#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: Niccolò Bonacchi
# @Date:   2018-02-02 17:19:09
import logging
import os
import tkinter as tk
from pathlib import Path
from sys import platform
from tkinter import messagebox

from pythonosc import udp_client

import iblrig.adaptive as adaptive
import iblrig.ambient_sensor as ambient_sensor
import iblrig.bonsai as bonsai
import iblrig.frame2TTL as frame2TTL
import iblrig.iotasks as iotasks
import iblrig.misc as misc
import iblrig.sound as sound
import iblrig.user_input as user_input
from iblrig.path_helper import SessionPathCreator
from iblrig.rotary_encoder import MyRotaryEncoder

log = logging.getLogger("iblrig")


class SessionParamHandler(object):
    """Session object imports user_settings and task_settings
    will and calculates other secondary session parameters,
    runs Bonsai and saves all params in a settings file.json"""

    def __init__(self, task_settings, user_settings, debug=False, fmake=True):
        self.DEBUG = debug
        make = True
        self.IBLRIG_FOLDER = "C:\\iblrig"
        self.IBLRIG_DATA_FOLDER = None  # ..\\iblrig_data if None
        # =====================================================================
        # IMPORT task_settings, user_settings, and SessionPathCreator params
        # =====================================================================
        ts = {
            i: task_settings.__dict__[i]
            for i in [x for x in dir(task_settings) if "__" not in x]
        }
        self.__dict__.update(ts)
        us = {
            i: user_settings.__dict__[i]
            for i in [x for x in dir(user_settings) if "__" not in x]
        }
        self.__dict__.update(us)
        self = iotasks.deserialize_pybpod_user_settings(self)
        spc = SessionPathCreator(
            self.PYBPOD_SUBJECTS[0], protocol=self.PYBPOD_PROTOCOL, make=make
        )
        self.__dict__.update(spc.__dict__)
        # =====================================================================
        # SETTINGS
        # =====================================================================
        self.RECORD_SOUND = False
        self.RECORD_AMBIENT_SENSOR_DATA = True
        self.RECORD_VIDEO = False
        self.OPEN_CAMERA_VIEW = False  # Always True if RECORD_VIDEO is True

        self.SPONTANEOUS_DURATION = 6 * 60
        self.OPTO_TIMES = 30
        self.OPTO_DURATION = 1
        self.OPTO_INTERVAL = 3

        # =====================================================================
        # SUBJECT
        # =====================================================================
        # self.SUBJECT_WEIGHT = self.ask_subject_weight()
        self.POOP_COUNT = False
        # =====================================================================
        # OSC CLIENT
        # =====================================================================
        self.OSC_CLIENT_PORT = 7110
        self.OSC_CLIENT_IP = "127.0.0.1"
        self.OSC_CLIENT = udp_client.SimpleUDPClient(
            self.OSC_CLIENT_IP, self.OSC_CLIENT_PORT
        )
        # =====================================================================
        # SAVE SETTINGS FILE AND TASK CODE
        # =====================================================================
        if not self.DEBUG:
            iotasks.save_session_settings(self)
            iotasks.copy_task_code(self)
            iotasks.save_task_code(self)
            self.bpod_lights(0)

    # =========================================================================
    # METHODS
    # =========================================================================
    def patch_settings_file(self, patch):
        self.__dict__.update(patch)
        misc.patch_settings_file(self.SETTINGS_FILE_PATH, patch)

    def save_ambient_sensor_reading(self, bpod_instance):
        return ambient_sensor.get_reading(
            bpod_instance, save_to=self.SESSION_RAW_DATA_FOLDER
        )

    def bpod_lights(self, command: int):
        fpath = Path(self.IBLRIG_FOLDER) / "scripts" / "bpod_lights.py"
        os.system(f"python {fpath} {command}")

    def get_port_events(self, events, name=""):
        return misc.get_port_events(events, name=name)

    # =========================================================================
    # JSON ENCODER PATCHES
    # =========================================================================
    def reprJSON(self):
        def remove_from_dict(sx):
            if "weighings" in sx.keys():
                sx["weighings"] = None
            if "water_administration" in sx.keys():
                sx["water_administration"] = None
            return sx

        d = self.__dict__.copy()
        d["OSC_CLIENT"] = str(d["OSC_CLIENT"])
        if isinstance(d["PYBPOD_SUBJECT_EXTRA"], list):
            sub = []
            for sx in d["PYBPOD_SUBJECT_EXTRA"]:
                sub.append(remove_from_dict(sx))
            d["PYBPOD_SUBJECT_EXTRA"] = sub
        elif isinstance(d["PYBPOD_SUBJECT_EXTRA"], dict):
            d["PYBPOD_SUBJECT_EXTRA"] = remove_from_dict(d["PYBPOD_SUBJECT_EXTRA"])
        
        return d

    

if __name__ == "__main__":
    """
    SessionParamHandler fmake flag=False disables:
        making folders/files;
    SessionParamHandler debug flag disables:
        running auto calib;
        calling bonsai
        turning off lights of bpod board
    """
    import task_settings as _task_settings
    import iblrig.fake_user_settings as _user_settings
    import datetime

    dt = datetime.datetime.now()
    dt = [
        str(dt.year),
        str(dt.month),
        str(dt.day),
        str(dt.hour),
        str(dt.minute),
        str(dt.second),
    ]
    dt = [x if int(x) >= 10 else "0" + x for x in dt]
    dt.insert(3, "-")
    _user_settings.PYBPOD_SESSION = "".join(dt)
    _user_settings.PYBPOD_SETUP = "ephysChoiceWorld"
    _user_settings.PYBPOD_PROTOCOL = "_iblrig_tasks_passive_opto"
    if platform == "linux":
        _task_settings.AUTOMATIC_CALIBRATION = False
        _task_settings.USE_VISUAL_STIMULUS = False

    sph = SessionParamHandler(_task_settings, _user_settings, debug=False, fmake=True)
    for k in sph.__dict__:
        if sph.__dict__[k] is None:
            print(f"{k}: {sph.__dict__[k]}")
    self = sph
    print("Done!")
