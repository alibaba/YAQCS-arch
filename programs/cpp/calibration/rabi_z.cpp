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

/* Measure Z-line amplitude corresponding to qubit drive frequency using Rabi experiments.

The Rabi experiments scans qubit response to a 2D scan of the Z-line amplitude
and the length of the drive pulse. Upon a correct drive frequency, the
qubit oscillates with maximum amplitude with respect to the drive length.
Such an experiment can be used to simultaneously determine the Z-line amplitude
corresponding to a frequency, and a rough PI pulse driving qubit from |0>
to |1>. Additionally it can be used to determine the bias-to-Z relation,
and drive frequencies used for sideband reset.

This experiment only collects the Rabi experiment data and leave data 
processing to the Upper-level PC.

Args:
  * `z_range`(int): Range of Z-line amplitude to be scanned. The range
  of the Z-line amplitude to be scanned is set as `[-z_range/30.,z_range/30.]`,
  symmetric with respect to 0.
  * `z_step` (int): Step size of the frequency scan.
  * `len_range` (int): Range of pulse lengths to be scanned, with a unit of 25ns.
  * `len_step` (int): Step size of the pulse length scan.
 */

#include "../yqe.h"
const int DELAY_RESET = 100, DELAY_X = 100, TRIGGER_INTERVAL = 1000;

int main() {
  int t1_repeat = 1000, result;
  *ADDR_TRIGGER_BITMASK = BITMASK;
  *ADDR_TRIGGER_INTERVAL = TRIGGER_INTERVAL;
  *ADDR_OFFSET = 0;
  ADDR_PARAMS[CHANNEL_1Q(0)][0] = 0.0;
  ADDR_PARAMS[CHANNEL_1Q(0)][2] = 1.;

  // Read parameters
  int z_range = int(ADDR_SRAM[0]);
  int z_step = int(ADDR_SRAM[1]);
  int len_range = int(ADDR_SRAM[2]);
  int len_step = int(ADDR_SRAM[3]);

  for (int z = -z_range; z <= z_range; z += z_step) {
    for (int len = 1; len <= len_range; len += len_step) {
      ADDR_PLAY[CHANNEL_1Q(0)] = WAVEFORM_RESET;
      *ADDR_WAIT = DELAY_RESET;
      ADDR_PARAMS[CHANNEL_1Q(0)][2] = z / 30.;
      ADDR_PLAY[CHANNEL_1Q(0)] = WAVEFORM_Z_UP;
      ADDR_PARAMS[CHANNEL_1Q(0)][2] = 1;
      ADDR_PLAY[CHANNEL_1Q(0)] = WAVEFORM_SQUARE_UP;
      *ADDR_WAIT = len * 25;
      ADDR_PLAY[CHANNEL_1Q(0)] = WAVEFORM_Z_DOWN;
      ADDR_PLAY[CHANNEL_1Q(0)] = WAVEFORM_SQUARE_DOWN;
      *ADDR_WAIT = DELAY_X;
      ADDR_PLAY[CHANNEL_1Q(0)] = WAVEFORM_MEAS;
      trigger(t1_repeat);
      result = ADDR_FMR[0];
      *ADDR_PCIE = z;
      *ADDR_PCIE = len;
      *ADDR_PCIE = result;
    }
  }
  return 0;
}
