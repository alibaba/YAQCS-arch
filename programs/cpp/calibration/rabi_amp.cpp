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


/* Measure qubit drive frequency using Rabi experiments.

The Rabi experiments scans qubit response to a 2D scan of the frequency
and the amplitude of the drive pulse. Upon a correct drive frequency, the
qubit oscillates with maximum amplitude with respect to the drive amplitude.
Such an experiment can be used to simultaneously determine the qubit 
drive amplitude and a rough PI pulse driving qubit from |0> to |1>.

This experiment only collects the Rabi experiment data and leave data 
processing to the Upper-level PC.

Amplitude-based Rabi experiment can be performed where XY line is not
equipped with square-pulse functionalities but only a amplitude modification;
however the pattern observed might deviate from ordianry Chevron pattern
typical for Rabi experiments.

Args:
  * `freq_range`(int): Range of frequency to be scanned. Assuming the
  IQ mixer frequency is close to the qubit drive frequency, the range
  of the IF frequency to be scanned is set as 
  `[-freq_range/100.,freq_range/100.]`, symmetric with respect to 0.
  * `freq_step` (int): Step size of the frequency scan.
  * `amp_range` (int): Range of pulse amplitudes to be scanned, with a
  unit of .25 to the PI pulse amplitude.
  * `amp_step` (int): Step size of the pulse length scan.
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
  int freq_range = int(ADDR_SRAM[0]);
  int freq_step = int(ADDR_SRAM[1]);
  int amp_range = int(ADDR_SRAM[2]);
  int amp_step = int(ADDR_SRAM[3]);


  for (int freq = -freq_range; freq <= freq_range; freq += freq_step) {
    ADDR_PARAMS[CHANNEL_1Q(0)][1] = freq / 100.;
    for (int amp = 1; amp <= amp_range; amp += amp_step) {
      ADDR_PLAY[CHANNEL_1Q(0)] = WAVEFORM_RESET;
      *ADDR_WAIT = DELAY_RESET;
      ADDR_PARAMS[CHANNEL_1Q(0)][2] = amp / 4.;
      ADDR_PLAY[CHANNEL_1Q(0)] = WAVEFORM_PI;
      *ADDR_WAIT = DELAY_X;
      ADDR_PLAY[CHANNEL_1Q(0)] = WAVEFORM_MEAS;
      trigger(t1_repeat);
      result = ADDR_FMR[0];
      *ADDR_PCIE = freq;
      *ADDR_PCIE = amp;
      *ADDR_PCIE = result;
    }
  }
  return 0;
}
