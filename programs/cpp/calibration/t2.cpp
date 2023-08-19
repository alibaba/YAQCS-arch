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

/* Measure T2 relaxation time of a qubit through a T2 Ramsey experiment.
A qubit is measured after an X/2 gate followed by an X/2 gate interleaved
by a certain delay time. Depolarization of the qubit within the delay time
makes the qubit fail to return to the original 0 state at the end, resulting
in an observable change of final survival rate with respect to the delay time.

Args:
  * `FRINGE`(double): fringe frequency. The final inverse gate is to be conjugated
  by a phase calculated from the fringe frequency in order to enhance the observed
  signal. Can also be used to measure the qubit frequency.
  * `t2_delay_max` (int): The maximum delay time between the X gate and final
  measurement.
  * `t2_delay_step` (int): Step length of delay increment. Experiments
  are done for each multiple of `t1_delay_step` t where 0 < t < `t1_delay_max`
  * `t2_repeat` (int): Number of repeated experiments for each delay. For each delay
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
  ADDR_PARAMS[CHANNEL_1Q(0)][2] = 1.0;

  // Read parameters
  double FRINGE = ADDR_SRAM[0];
  int t2_delay_max = int(ADDR_SRAM[1]);
  int t2_delay_step = int(ADDR_SRAM[2]);
  int t2_repeat = int(ADDR_SRAM[3]);

  for (int t2_delay = 0; t2_delay < t2_delay_max; t2_delay += t2_delay_step) {
    ADDR_PLAY[CHANNEL_1Q(0)] = WAVEFORM_RESET;
    *ADDR_WAIT = DELAY_RESET;
    ADDR_PARAMS[CHANNEL_1Q(0)][0] = 0.0;
    ADDR_PLAY[CHANNEL_1Q(0)] = WAVEFORM_PI_2;
    *ADDR_WAIT = DELAY_X;
    *ADDR_WAIT = t2_delay;
    ADDR_PARAMS[CHANNEL_1Q(0)][0] = t2_delay * FRINGE / 1000.;
    ADDR_PLAY[CHANNEL_1Q(0)] = WAVEFORM_PI_2;
    *ADDR_WAIT = DELAY_X;
    ADDR_PLAY[CHANNEL_1Q(0)] = WAVEFORM_MEAS;
    trigger(t2_repeat);
    result = ADDR_FMR[0];

    // Output delay time and survival count
    *ADDR_PCIE = t2_delay;
    *ADDR_PCIE = result;
  }
  return 0;
}
