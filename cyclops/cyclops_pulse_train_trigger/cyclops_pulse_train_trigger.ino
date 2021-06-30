/*
Copyright (c) Jon Newman (jpnewman ~at~ mit <dot> edu)
All right reserved.

This file is part of the Cyclops Library (CL) for Arduino.

CL is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

CL is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with CL.  If not, see <http://www.gnu.org/licenses/>.
*/

#include <Cyclops.h>

Cyclops cyclops0(CH0);

// Stop laser if no stop pulse is detected after 1 second
uint16_t stop_time_ms = 1000;

// 25 Hz stimulation with 10 ms pulses
uint16_t pulse_width_us = 10000;
uint16_t pulse_interval_us = 30000;
uint16_t pulse_intensity = 4095;
int opto_on = 0;
int timed_out = 0;
unsigned long pulse_time;
unsigned long opto_start_time;

void setup()
{
    // Set pin mode of trigger to input
    pinMode(TRIG0, INPUT); 
    
    // Start the device
    Cyclops::begin();

    // Zero out the DAC
    cyclops0.dac_load_voltage(0);

    // Initialize timer
    pulse_time = millis();
    opto_start_time = millis();
}

void loop()
{
    // Start pulse train when input is detected
    if (digitalRead(TRIG0) && opto_on == 0 && millis() - pulse_time > 200) {
      opto_on = 1;
      pulse_time = millis();
      opto_start_time = millis();
    }
    // Stop the pulse train
    else if (digitalRead(TRIG0) && opto_on == 1 && millis() - pulse_time > 200) {
      opto_on = 0;
      pulse_time = millis();
    }
    // If this is the first pulse after a time-out, ignore it
    //else if (digitalRead(TRIG0) && timed_out == 1 && millis() - pulse_time > 200) {
    //  timed_out = 0;
    //  pulse_time = millis();
    //}

    // Pulse train
    if (opto_on == 1) {
      cyclops0.dac_load_voltage(pulse_intensity);
      delayMicroseconds(pulse_width_us);
      cyclops0.dac_load_voltage(0);
      delayMicroseconds(pulse_interval_us);  
    }

    // Stop opto stim if stop pulse has not been received after stop_time_ms
    //if (opto_on == 1 && millis() - opto_start_time > stop_time_ms) {
    //  opto_on = 0;
    //  timed_out = 1;
    //}
}
