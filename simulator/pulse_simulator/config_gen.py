# Copyright 2023 Alibaba Group

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""Generate pulse configuration file for the pulse simulator backend.

A pulse configuration file is a '.json' file and consists of the following:
- 'qubits': specifications for each qubit, including its noise model
- 'channels': specification of each channel, with the following keys:
    - 'type': '1Q' or '2Q', corresponding to single-qubit or two-qubit
    operations;
    - 'targets': to which qubit (or pairs of qubits) do the operations act upon;
    - 'waveforms': a dictionary of waveform informations indexed by pulse
    indices. A waveform is played on the corresponding channel upon indicating
    the corresponding waveform index.
"""

import argparse
import json
import numpy as np

parser = argparse.ArgumentParser(
    description='Generate pulse configuration file for the pulse simulator backend.')
parser.add_argument('topology_file', nargs='?', default='topology.json',
                    help='the json file describing the qubit topology')
parser.add_argument('pulse_file', nargs='?', default='pulse.json',
                    help='the output pulse configuration file')
args = parser.parse_args()

# Read topology file for qubit connectivity
with open(args.topology_file, 'r') as fin:
    data = json.load(fin)
    qubit_list = data['qubit_list']
    qubit_topology = data['qubit_topology']

# Generate qubit_config
qubit_config = {i: {"noise": {"t1": 4000, "t2": 4000}, "readout_center": {
    "0": [0, 1], "1": [1, 0]}} for i in qubit_list}

# Generate channel_config
channel_config = {}

# Generate sinusoidal waveforms as mock pulse envelopes
tlist = list(range(101))
pulse_null = [0] * 101
PULSE_FULL_AMP = 0x4000
pulse_full = list(
    int(i) for i in PULSE_FULL_AMP * (1 - np.cos(np.array(tlist) / 50 * np.pi)))
pulse_half = list(
    int(i) for i in (PULSE_FULL_AMP / 2 * (1 - np.cos(np.array(tlist) / 50 * np.pi))))

# Generate 1q waveforms played on sq_channels,
# pulse envelopes for 1Q gates X, X_half, and instructions for square pulses,
# reset and measure

sq_waveforms = {}
sq_waveforms[0] = ['xy_waveform', [pulse_full, pulse_null]]
sq_waveforms[1] = ['xy_waveform', [pulse_half, pulse_null]]
sq_waveforms[2] = ['xy_square_up']
sq_waveforms[3] = ['xy_square_down']
sq_waveforms[64] = ['z_square_up']
sq_waveforms[65] = ['z_square_down']
sq_waveforms[127] = ['reset']
sq_waveforms[128] = ['measure']

# Assign one sq_channel with a PI gate and a PI_Half gate for each qubit
index = 0
for i in qubit_list:
    sq_channel_config = {
        "type": "1Q",
        "waveforms": sq_waveforms,
        "target": i,
    }
    channel_config.update({index: sq_channel_config})
    index += 1

# Generate 2q waveforms played on tq_channels
# pulse envelopes for 2Q gates CZ, ISWAP (both are square pulses)
tq_waveforms = {}
tq_waveforms[0] = [[np.pi / 100] * 50 + [0] * 51]
tq_waveforms[1] = [[np.pi / 100] * 50 + [0] * 51]

# Assign one tq_channel with a CZ gate and an ISWAP gate for each tunable coupler
index = 0x400
for i in qubit_topology:
    tq_channel_config = {
        "type": "2Q",
        "waveforms": tq_waveforms,
        "target": i,
    }
    channel_config.update({index: tq_channel_config})
    index += 1

with open(args.pulse_file, 'w') as f:
    json.dump({"qubits": qubit_config, "channels": channel_config}, f)
