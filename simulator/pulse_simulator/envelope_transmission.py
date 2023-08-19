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

"""Register input pulse sequences to an existing pulse configuration file,
used in the pulse simulator backend. Pulse transmission is typically used in
qubit calibration where pulses are to be modified delicately to enhance gate
fidelity. Given limited computational resource allocated to the control
electronics, our design delegates the computation of pulse sequences to the
master FPGA, but allows the master FPGA to transmit such pulse information to
control electronics where the pulse sequences are to be played.

This module is to be incorporated as a subroutine in the QEMU simulator (see
`qemu/hw/misc/yqe_plugin.c`) to simulate an MMIO routine transmitting a pulse
waveform to control electronics at run time.

- `input_file` contains necessary information of a pulse sequence and
its storage destination. The first line contains `channel`, `index` and `length`
of the pulse sequence, and the following lines each contains an integer, describing
the pulse sequence.
    * `channel` is a physical channel index indicating the index of the destination
    control eletronic device.
    * `index` is the index to which the pulse sequence is to be stored. Any
    non-reserved index can be used. Storing a pulse sequence to a reserved index
    will raise exit code 1, whereas storing a pulse sequence to a non-reserved
    index overwrites the previous pulse information stored at this index.

Currently only supports 1Q gate pulse transmissions.
    * In the case the channel is an `xy_channel`, the pulse sequence is complex,
    with real and imaginary components written on lines `[1 : length // 2 + 1]`
    and `[length // 2 + 1 : length // 2]`.
"""

import json
import sys

# Reserved indices; overwriting such indices will cause error
RESERVED_INDICES = [0, 1, 2, 3, 64, 65] + list(range(127, 256))


def envelope_transmission(input_file, output_file):
    with open(input_file, "r") as f:
        k = f.readlines()
        info = k[0].split(' ')
        channel = info[0]
        index = info[1]
        length = int(info[2])
        envelope = [int(i) for i in k[1:] if len(i) > 0]
    with open(output_file, "r") as f:
        pulse_json = json.load(f)
    if channel not in pulse_json['channels']:
        print("Channel non-existent")
        exit(1)
    elif pulse_json['channels'][channel]["type"] != "1Q":
        print("Multi-qubit channel envelope transmission not yet supported")
        exit(1)
    else:
        if int(index) in RESERVED_INDICES:
            print("Pulse index reserved and cannot be modified")
            exit(1)
        elif int(index) < 64:  # xy pulse
            xy_len = length // 2
            pulse_json["channels"][channel]["waveforms"][index] = [
                "xy_waveform", [envelope[:xy_len], envelope[xy_len:]]]
        else:  # z pulse
            pulse_json['channels'][channel]["waveforms"][index] = [
                "z_waveform", envelope]
    with open(output_file, "w") as f:
        json.dump(pulse_json, f)


if __name__ == "__main__":
    argv = sys.argv
    envelope_transmission(*argv[1:])
