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

/* Measure T1 relaxation time of a qubit by observing exponential decay of the
survival rate after excitation of the qubit. A qubit is measured after a certain
amount of time after being applied an X gate. The decay rate of the observed
frequency of measuring 1 with respect to the waiting time is called the T1 relaxation
time.

Args:
  * `t1_delay_max` (int): The maximum delay time between the X gate and final
  measurement.
  * `t1_delay_step` (int): Step length of delay increment. Experiments
  are done for each multiple of `t1_delay_step` t where 0 < t < `t1_delay_max`
  * `t1_repeat` (int): Number of repeated experiments for each delay. For each delay
  t, the experiment is repeated `t1_repeat` times to get an estimate of the current
  survival rate.
 */

#include "../yqe.h"
const int DELAY_RESET = 100, DELAY_X = 100, TRIGGER_INTERVAL = 1000;

int main() {
  // Initialization
  int result;
  *ADDR_TRIGGER_BITMASK = BITMASK;
  *ADDR_TRIGGER_INTERVAL = TRIGGER_INTERVAL;
  *ADDR_OFFSET = 0;
  ADDR_PARAMS[CHANNEL_1Q(0)][0] = 0.0;
  ADDR_PARAMS[CHANNEL_1Q(0)][2] = 1.0;

  // Read parameters
  int t1_delay_max = int(ADDR_SRAM[0]);
  int t1_delay_step = int(ADDR_SRAM[1]);
  int t1_repeat = int(ADDR_SRAM[2]);

  // Measure the survival rate after a certain time after excitation
  for (int t1_delay = 0; t1_delay < t1_delay_max; t1_delay += t1_delay_step) {
    ADDR_PLAY[CHANNEL_1Q(0)] = WAVEFORM_RESET;
    *ADDR_WAIT = DELAY_RESET;
    ADDR_PLAY[CHANNEL_1Q(0)] = WAVEFORM_PI;
    *ADDR_WAIT = DELAY_X;
    *ADDR_WAIT = t1_delay;
    ADDR_PLAY[CHANNEL_1Q(0)] = WAVEFORM_MEAS;
    trigger(t1_repeat);
    result = ADDR_FMR[0];

    // Output delay time and survival count
    *ADDR_PCIE = t1_delay;
    *ADDR_PCIE = result;
  }
  return 0;
}
