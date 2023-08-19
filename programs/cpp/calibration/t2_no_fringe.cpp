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

// Measure system T2 by measuring the state purity via a pair of complementary bases
#include "../yqe.h"
#include <cmath>
const int DELAY_RESET = 100, DELAY_X = 100, TRIGGER_INTERVAL = 1000;

int main() {
  // Fringe frequency for T2 Ramsey experiment
  int t2_delay_max = int(ADDR_SRAM[0]);
  int t2_delay_step = int(ADDR_SRAM[1]);
  int t2_repeat = int(ADDR_SRAM[2]);
  int resultx, resulty;
  double result;
  double fx, fy;
  *ADDR_TRIGGER_BITMASK = BITMASK;
  *ADDR_TRIGGER_INTERVAL = TRIGGER_INTERVAL;
  *ADDR_OFFSET = 0;
  ADDR_PARAMS[CHANNEL_1Q(0)][2] = 1.0;
  for (int t2_delay = 0; t2_delay < t2_delay_max; t2_delay += t2_delay_step) {
    // Measure under the X-basis
    ADDR_PLAY[CHANNEL_1Q(0)] = WAVEFORM_RESET;
    *ADDR_WAIT = DELAY_RESET;
    ADDR_PARAMS[CHANNEL_1Q(0)][0] = 0.0;
    ADDR_PLAY[CHANNEL_1Q(0)] = WAVEFORM_ZXZ_90;
    *ADDR_WAIT = DELAY_X;
    *ADDR_WAIT = t2_delay;
    ADDR_PLAY[CHANNEL_1Q(0)] = WAVEFORM_ZXZ_90;
    *ADDR_WAIT = DELAY_X;
    ADDR_PLAY[CHANNEL_1Q(0)] = WAVEFORM_MEAS;
    trigger(t2_repeat);
    resultx = ADDR_FMR[0];

    /* 
      Measure under the Y-basis. The two bases do not have to be X and Y; 
      as long as the phases differ by PI/2 this should work.
      */
    ADDR_PLAY[CHANNEL_1Q(0)] = WAVEFORM_RESET;
    *ADDR_WAIT = DELAY_RESET;
    ADDR_PLAY[CHANNEL_1Q(0)] = WAVEFORM_ZXZ_90;
    *ADDR_WAIT = DELAY_X;
    *ADDR_WAIT = t2_delay;
    ADDR_PARAMS[CHANNEL_1Q(0)][0] = M_PI_2;
    ADDR_PLAY[CHANNEL_1Q(0)] = WAVEFORM_ZXZ_90;
    *ADDR_WAIT = DELAY_X;
    ADDR_PLAY[CHANNEL_1Q(0)] = WAVEFORM_MEAS;
    trigger(t2_repeat);
    resulty = ADDR_FMR[0];

    fx = resultx / (t2_repeat + 0.) - 0.5;
    fy = resulty / (t2_repeat + 0.) - 0.5;
    result = sqrt(fx * fx + fy * fy);
    *ADDR_PCIE = t2_delay;
    *(double *)ADDR_PCIE = result;
  }
  return 0;
}
