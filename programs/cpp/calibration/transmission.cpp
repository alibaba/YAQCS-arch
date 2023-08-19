// Copyright 2023 Alibaba Group

// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at

//     http://www.apache.org/licenses/LICENSE-2.0

// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

/* Measure transmission
The experiment consists of playing a sinosodial wave on the readout line / XY
line for a period of time, and then collect result from the digitizer.
Sweepable parameters include (for example) readout power, freqency, length,
XY power, frequency, length, dc_bias etc.
 * **/

#include "../yqe.h"
const int DELAY_WAIT = 200, DELAY_X = 100, TRIGGER_INTERVAL = 1000;

int main() {
  int result;
  double ro_amp = ADDR_SRAM[0];
  double ro_freq = ADDR_SRAM[1];
  double z_amp = ADDR_SRAM[2];
  double xy_amp = ADDR_SRAM[3];
  double xy_freq = ADDR_SRAM[4];
  int repeat = int(ADDR_SRAM[5]);
  *ADDR_TRIGGER_BITMASK = BITMASK;
  *ADDR_TRIGGER_INTERVAL = TRIGGER_INTERVAL;
  *ADDR_OFFSET = 0;
  ADDR_PARAMS[CHANNEL_1Q(0)][2] = z_amp;
  ADDR_PLAY[CHANNEL_1Q(0)] = WAVEFORM_Z_UP;
  ADDR_PARAMS[CHANNEL_1Q(0)][0] = xy_freq;
  ADDR_PARAMS[CHANNEL_1Q(0)][2] = xy_amp;
  ADDR_PLAY[CHANNEL_1Q(0)] = WAVEFORM_PI;
  *ADDR_WAIT = DELAY_X;
  ADDR_PLAY[CHANNEL_1Q(0)] = WAVEFORM_Z_DOWN;
  *ADDR_WAIT = DELAY_X;
  ADDR_PARAMS[CHANNEL_1Q(0)][0] = ro_freq;
  ADDR_PARAMS[CHANNEL_1Q(0)][2] = ro_amp;
  ADDR_PLAY[CHANNEL_1Q(0)] = WAVEFORM_MEAS;
  *ADDR_WAIT = DELAY_WAIT;
  trigger(repeat);
  result = ADDR_FMR[0];
  *ADDR_PCIE = result;
  return 0;
}
