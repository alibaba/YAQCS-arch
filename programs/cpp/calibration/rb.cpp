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

/* Conduct single-qubit Clifford group Randomized Benchmarking (RB)
experiment.

RB is a standard way of extracting an overall figure of merit representing
average gate fidelity. An RB experiment generates random Clifford circuits
that multiplies to identity with given lengths. Due to noises in real
quantum devices, the probability that an input state gets recovered after
the circuit, called the survival rate, decreases exponentially with respect
to the circuit length, and can be extracted with curve fitting techniques.

This program generates random Clifford circuits of given lengths, and returns
the survival rates obtained from experiments. Curve fitting is left for the
Upper PC.

Args:
  * `rand_seed` (int): Random seed for random circuit generation. The current
  architecture relies on an auxiliary source for the random seed as it does
  not come with a built-in random number generator.
  * `num_lengths` (int): Number of Clifford circuit lengths used in experiments.
  * `num_circuit` (int): Number of random circuits to be sampled for each
  circuit length.
  * `lengths` (List[int]): the list of circuit lengths, containing `num_lengths`
  number of entries.
 */
#include <cmath>
#include <cstdlib>

#include "../yqe.h"
const int DELAY_RESET = 100, DELAY_X = 100,
          TRIGGER_INTERVAL = 1000;
#define MAX_NUM_LENGTHS 100
int lengths[MAX_NUM_LENGTHS];

// Basic gate pulses building Clifford gates
static inline void x() {
  ADDR_PARAMS[CHANNEL_1Q(0)][0] = 0;
  *ADDR_PLAY = WAVEFORM_PI;
  *ADDR_WAIT = DELAY_X;
}

static inline void y() {
  ADDR_PARAMS[CHANNEL_1Q(0)][0] = M_PI / 2;
  *ADDR_PLAY = WAVEFORM_PI;
  *ADDR_WAIT = DELAY_X;
}

static inline void x90() {
  ADDR_PARAMS[CHANNEL_1Q(0)][0] = 0;
  *ADDR_PLAY = WAVEFORM_PI_2;
  *ADDR_WAIT = DELAY_X;
}

static inline void xm90() {
  ADDR_PARAMS[CHANNEL_1Q(0)][0] = M_PI;
  *ADDR_PLAY = WAVEFORM_PI_2;
  *ADDR_WAIT = DELAY_X;
}

static inline void y90() {
  ADDR_PARAMS[CHANNEL_1Q(0)][0] = M_PI / 2;
  *ADDR_PLAY = WAVEFORM_PI_2;
  *ADDR_WAIT = DELAY_X;
}

static inline void ym90() {
  ADDR_PARAMS[CHANNEL_1Q(0)][0] = -M_PI / 2;
  *ADDR_PLAY = WAVEFORM_PI_2;
  *ADDR_WAIT = DELAY_X;
}

// Definition of Clifford gates with associated indices
static inline void apply_clifford(int clifford_index) {
  switch (clifford_index) {
    case 0:  // id_xy
      break;
    case 1:  // x90
      x90();
      break;
    case 2:  // x
      x();
      break;
    case 3:  // xm90
      xm90();
      break;
    case 4:  // y90
      y90();
      break;
    case 5:  // y
      y();
      break;
    case 6:  // ym90
      ym90();
      break;
    case 7:  // x90 * ym90 * xm90
      x90();
      ym90();
      xm90();
      break;
    case 8:  // y * x
      y();
      x();
      break;
    case 9:  // x90 * y90 * xm90
      x90();
      y90();
      xm90();
      break;
    case 10:  // x90 * y90 * x90
      x90();
      y90();
      x90();
      break;
    case 11:  // y90 * xm90 * y90
      y90();
      xm90();
      y90();
      break;
    case 12:  // y90 * x
      y90();
      x();
      break;
    case 13:  // ym90 * x
      ym90();
      x();
      break;
    case 14:  // xm90 * y
      xm90();
      y();
      break;
    case 15:  // y * xm90
      y();
      xm90();
      break;
    case 16:  // y90 * x90
      y90();
      x90();
      break;
    case 17:  // xm90 * ym90
      xm90();
      ym90();
      break;
    case 18:  // x90 * ym90
      x90();
      ym90();
      break;
    case 19:  // y90 * xm90
      y90();
      xm90();
      break;
    case 20:  // x90 * y90
      x90();
      y90();
      break;
    case 21:  // ym90 * xm90
      ym90();
      xm90();
      break;
    case 22:  // xm90 * y90
      xm90();
      y90();
      break;
    case 23:  // ym90 * x90
      ym90();
      x90();
  }
}

// Hardcoded multiplication table and inversion list, represented with
// the associated indices

const int clifford_multiplication_table[24][24] = {
    {0,  1,  2,  3,  4,  5,  6,  7,  8,  9,  10, 11,
     12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23},
    {1,  2,  3, 0, 20, 15, 18, 16, 14, 23, 21, 19,
     17, 22, 5, 8, 10, 6,  12, 9,  13, 7,  4,  11},
    {2, 3, 0,  1,  13, 8,  12, 10, 5,  11, 7,  9,
     6, 4, 15, 14, 21, 18, 17, 23, 22, 16, 20, 19},
    {3,  0,  1, 2, 22, 14, 17, 21, 15, 19, 16, 23,
     18, 20, 8, 5, 7,  12, 6,  11, 4,  10, 13, 9},
    {4, 16, 12, 19, 5,  6, 0, 22, 13, 20, 17, 18,
     8, 2,  23, 21, 14, 9, 7, 15, 10, 3,  11, 1},
    {5,  14, 8, 15, 6,  0,  4,  11, 2,  10, 9,  7,
     13, 12, 1, 3,  23, 20, 22, 21, 17, 19, 18, 16},
    {6, 23, 13, 21, 0, 4,  5,  18, 12, 17, 20, 22,
     2, 8,  16, 19, 1, 10, 11, 3,  9,  15, 7,  14},
    {7,  18, 11, 22, 16, 10, 21, 8, 9, 0,  2,  5,
     19, 23, 17, 20, 12, 3,  15, 4, 1, 13, 14, 6},
    {8, 15, 5, 14, 12, 2,  13, 9,  0,  7,  11, 10,
     4, 6,  3, 1,  19, 22, 20, 16, 18, 23, 17, 21},
    {9,  20, 10, 17, 19, 11, 23, 0,  7,  8, 5, 2,
     16, 21, 22, 18, 4,  14, 1,  12, 15, 6, 3, 13},
    {10, 17, 9,  20, 21, 7, 16, 5,  11, 2, 0,  8,
     23, 19, 18, 22, 6,  1, 14, 13, 3,  4, 15, 12},
    {11, 22, 7,  18, 23, 9,  19, 2, 10, 5,  8, 0,
     21, 16, 20, 17, 13, 15, 3,  6, 14, 12, 1, 4},
    {12, 19, 4,  16, 2, 13, 8, 17, 6,  18, 22, 20,
     0,  5,  21, 23, 3, 7,  9, 1,  11, 14, 10, 15},
    {13, 21, 6,  23, 8,  12, 2,  20, 4, 22, 18, 17,
     5,  0,  19, 16, 15, 11, 10, 14, 7, 1,  9,  3},
    {14, 8,  15, 5, 17, 3, 22, 23, 1,  16, 19, 21,
     20, 18, 0,  2, 9,  4, 13, 10, 12, 11, 6,  7},
    {15, 5,  14, 8, 18, 1,  20, 19, 3, 21, 23, 16,
     22, 17, 2,  0, 11, 13, 4,  7,  6, 9,  12, 10},
    {16, 12, 19, 4,  10, 21, 7, 14, 23, 1,  3, 15,
     9,  11, 6,  13, 17, 0,  8, 20, 2,  22, 5, 18},
    {17, 9,  20, 10, 3, 22, 14, 6, 18, 12, 4,  13,
     1,  15, 7,  11, 0, 16, 23, 2, 19, 5,  21, 8},
    {18, 11, 22, 7, 1, 20, 15, 12, 17, 6, 13, 4,
     3,  14, 10, 9, 2, 21, 19, 0,  23, 8, 16, 5},
    {19, 4,  16, 12, 11, 23, 9, 3,  21, 15, 14, 1,
     7,  10, 13, 6,  22, 8,  0, 18, 5,  17, 2,  20},
    {20, 10, 17, 9, 15, 18, 1,  4, 22, 13, 6,  12,
     14, 3,  11, 7, 5,  23, 16, 8, 21, 0,  19, 2},
    {21, 6, 23, 13, 7,  16, 10, 15, 19, 3,  1, 14,
     11, 9, 12, 4,  18, 2,  5,  22, 0,  20, 8, 17},
    {22, 7, 18, 11, 14, 17, 3,  13, 20, 4, 12, 6,
     15, 1, 9,  10, 8,  19, 21, 5,  16, 2, 23, 0},
    {23, 13, 21, 6,  9,  19, 11, 1,  16, 14, 15, 3,
     10, 7,  4,  12, 20, 5,  2,  17, 8,  18, 0,  22}};

const int clifford_inversion_list[24] = {0,  3,  2,  1,  6,  5,  4,  9,
                                       8,  7,  10, 11, 12, 13, 14, 15,
                                       17, 16, 19, 18, 21, 20, 23, 22};

static inline int get_int() {
  static int offset = 0;
  return (int)(ADDR_SRAM[offset++] + 0.5);
}

int main() {
  int rb_repeat = 1000, result;
  *ADDR_TRIGGER_BITMASK = BITMASK;
  *ADDR_TRIGGER_INTERVAL = TRIGGER_INTERVAL;
  *ADDR_OFFSET = 0;
  ADDR_PARAMS[CHANNEL_1Q(0)][2] = 1.00;

  // Read parameters
  int rand_seed = get_int();
  int num_lengths = get_int();
  int num_circuit = get_int();
  for (int i = 0; i < num_lengths; i++) lengths[i] = get_int();

  srand(rand_seed);
  for (int i = 0; i < num_lengths; i++) {
    int fid_sum = 0;
    for (int cnt = 0; cnt < num_circuit; cnt++) {
      int total = 0;
      double phase = 0.0;
      ADDR_PLAY[CHANNEL_1Q(0)] = WAVEFORM_RESET;
      *ADDR_WAIT = DELAY_RESET;
      // Apply the first `lengths[i] - 1` gates i.i.d. uniformly at random
      for (int j = 0; j < lengths[i] - 1; j++) {
        int r = rand() % 24;
        apply_clifford(r);
        total = clifford_multiplication_table[total][r];
      }
      // Apply the inversion gate
      apply_clifford(clifford_inversion_list[total]);
      ADDR_PLAY[CHANNEL_1Q(0)] = WAVEFORM_MEAS;
      trigger(rb_repeat);
      result = ADDR_FMR[0];
      // Accumulate number of 1's detected
      fid_sum += result;
    }
    *ADDR_PCIE = lengths[i];
    *ADDR_PCIE = rb_repeat * num_circuit - fid_sum;
  }

  return 0;
}

#undef MAX_NUM_LENGTHS