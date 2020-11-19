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

// 25 Hz stimulation with 10 ms pulses
uint16_t pulse_width_us = 10000;
uint16_t pulse_interval_us = 30000;
uint16_t pulse_intensity = 4095;
int opto_on = 0;
uint16_t pulse_time;
uint16_t opto_start_time;

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
    if (digitalRead(TRIG0) && opto_on == 0 && pulse_time > 100) {
      opto_on = 1;
      pulse_time = millis();
      opto_start_time = millis();
    }
    else if (digitalRead(TRIG0) && opto_on == 1 && pulse_time > 100) {
      opto_on = 0;
      pulse_time = millis();
    }

    // Pulse train
    if (opto_on == 1 && opto_start_time < 60000) {
      cyclops0.dac_load_voltage(pulse_intensity);
      delayMicroseconds(pulse_width_us);
      cyclops0.dac_load_voltage(0);
      delayMicroseconds(pulse_interval_us);  
    }
}
