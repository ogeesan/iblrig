#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Author: Niccolò Bonacchi
# @Date: Friday, November 15th 2019, 12:05:29 pm
import logging
import sys
import time

import numpy as np
import usb
from ibllib.graphic import popup
from pybpodapi.protocol import Bpod, StateMachine

import iblrig.bonsai as bonsai
import iblrig.frame2TTL as frame2TTL
import iblrig.iotasks as iotasks
import iblrig.misc as misc
import iblrig.params as params
import task_settings
import user_settings
from iblrig.bpod_helper import BpodMessageCreator, bpod_lights
from iblrig.rotary_encoder import MyRotaryEncoder
from session_params import SessionParamHandler

log = logging.getLogger("iblrig")
log.setLevel(logging.INFO)

global sph
sph = SessionParamHandler(task_settings, user_settings)

PARAMS = params.load_params_file()

# get bpod
bpod = Bpod()
# Build messages
msg = BpodMessageCreator(bpod)
bpod = msg.return_bpod()


def opto_stim_on(bpod, stim_duration):
    sma = StateMachine(bpod)
    sma.add_state(
        state_name="opto_on",
        state_timer=stim_duration,
        output_actions=[("BNC2", 255)],  # To FPGA
        state_change_conditions={"Tup": "exit"},
    )
    bpod.send_state_machine(sma)
    bpod.run_state_machine(sma)  # Locks until state machine 'exit' is reached
    return


def opto_stim_off(bpod, interval_duration):
    sma = StateMachine(bpod)
    sma.add_state(
        state_name="opto_off",
        state_timer=interval_duration,
        output_actions=[("BNC2", 0)],  # To FPGA
        state_change_conditions={"Tup": "exit"},
    )
    bpod.send_state_machine(sma)
    bpod.run_state_machine(sma)  # Locks until state machine 'exit' is reached
    return


# Spontaneous activity
log.info("Starting %d minutes of spontaneous activity" % (sph.SPONTANEOUS_DURATION / 60))
time.sleep(sph.SPONTANEOUS_DURATION)

# start opto stim 
log.info("Starting optogenetic stimulation")
for i in range(sph.OPTO_TIMES):
    log.info("Stimulation %d of %d" % (i + 1, sph.OPTO_TIMES))
    opto_stim_on(bpod, sph.OPTO_DURATION)
    opto_stim_off(bpod, sph.OPTO_INTERVAL)
    
bpod.close()
# Turn bpod light's back on
bpod_lights(PARAMS["COM_BPOD"], 1)
# Close Bonsai stim
log.info("Protocol finished")

if __name__ == "__main__":
    pregenerated_session_num = "mock"
   
