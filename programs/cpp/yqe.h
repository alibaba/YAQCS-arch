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


/* MMIO address layout
  * Basic functionalities
    * ADDR_TRIGGER: Issue triggers with given number of repetitions for executing previously issued pulses
    * ADDR_PLAY: Issue pulse commands to specified control electronics
    * ADDR_WAIT: Increment global clock for pulse scheduling
    * ADDR_FMR: Retrieve measurement results from control electronics
    * ADDR_PARAMS: Specify detailed pulse parameters for upcoming pulse issuing
  * Upper PC IO
    * ADDR_PCIE: Output program results to upper PC
    * ADDR_SRAM: Receive program parameters from upper PC
  * Fetch-measurement-result (FMR) related
    * ADDR_FMR_IQ: Retrieve (demodulated) measurement IQ results from control electronics
    * ADDR_OFFSET: Specify return address offset relative to ADDR_FMR
  * Trigger related
    * ADDR_TRIGGER_INTERVAL: Specify time interval between two consecutive triggers
    * ADDR_TRIGGER_BITMASK: Specify which channels are activated for upcoming trigger
  * Pulse transmission
    * ADDR_ENVELOPE: Specify 14-bit resolution pulses
    * ADDR_WAVE_LEN: Specify length of waveform
    * ADDR_WAVE_CHANNEL: Specify to which control electronics is the envelope to be transmitted
    * ADDR_WAVE_INDEX: Specify to which pulse index of the given control electronics is the envelope to be transmitted
 */
volatile int *const ADDR_TRIGGER = (int *)0x40001000,
                    *const ADDR_WAIT = (int *)0x40002000,
                    *const ADDR_FMR = (int *)0x40003000,
                    *const ADDR_PCIE = (int *)0x40120000;
volatile unsigned char *const ADDR_FMR_READY = (unsigned char *)0x40002FFF,
                              *const ADDR_PLAY = (unsigned char *)0x40008000;
volatile double (*const ADDR_PARAMS)[4] = (double (*)[4])0x40010000;
volatile double (*const ADDR_FMR_IQ)[2] = (double (*)[2])0x40004000;
volatile double *const ADDR_SRAM = (double *)0x40100000;
volatile int *const ADDR_TRIGGER_INTERVAL = ADDR_TRIGGER + 1,
                    *const ADDR_TRIGGER_BITMASK = ADDR_TRIGGER + 2,
                    *const ADDR_OFFSET = ADDR_WAIT + 1;
volatile unsigned short *const ADDR_ENVELOPE = (unsigned short *)0x40002400;
volatile int *const ADDR_WAVE_LEN = (int *)0x400023F8;
volatile unsigned short *const ADDR_WAVE_CHANNEL = (unsigned short *)0x400023FC;
volatile unsigned char *const ADDR_WAVE_INDEX = (unsigned char *)0x400023FE;

/*
  Address mapping from MMIO to physical / logical channels
 */

static inline int CHANNEL_1Q(int k) { return k; }
static inline int CHANNEL_2Q(int k) { return 0x400 + k; }
static inline int CHANNEL_PHYS(int k) { return 0x2000 + k; }

/* Reserved pulse indices for 1Q and 2Q channels
  * WAVEFORM_PI: Sinusodial pulse for $\pi$-rotation along the X-axis
  * WAVEFORM_PI_2: Sinusodial pulse for $\pi/2$-rotation along the X-axis
  * WAVEFORM_SQUARE_UP: Rising edge for square pulse, on the XY line
  * WAVEFORM_SQAURE_DOWN: Falling edge for square pulse, on the XY line
  * WAVEFORM_Z_UP: Falling edge for square pulse, on the Z line
  * WAVEFORM_Z_DOWN: Falling edge for square pulse, on the Z line 
  * WAVEFORM_RESET: Reset a qubit to |0> state
  * WAVEFORM_MEAS: Measure a qubit
  * WAVEFORM_CZ: Placeholder for waveform performing a two-qubit CZ gate. Exact implementation depends on the platform.
  * WAVEFORM_IS: Placeholder for waveform performing a two-qubit iSWAP gate. Exact implementation depends on the platform.
 */

const unsigned char WAVEFORM_PI = 0, WAVEFORM_PI_2 = 1,
                    WAVEFORM_SQUARE_UP = 2, WAVEFORM_SQUARE_DOWN = 3,
                    WAVEFORM_Z_UP = 64, WAVEFORM_Z_DOWN = 65,
                    WAVEFORM_RESET = 127, WAVEFORM_MEAS = 128;
const unsigned char WAVEFORM_CZ = 0, WAVEFORM_IS = 1;

// TODO(fang.z): Don't know how to set or implement this
const int BITMASK = 0xffffffff;

static inline void trigger(int trigger_repeat) {
  *ADDR_TRIGGER = trigger_repeat;
  while (!*ADDR_FMR_READY) {
  }
}