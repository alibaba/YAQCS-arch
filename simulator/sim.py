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

"""
RISC-V quantum program simulator for Yaqcs Architecture.

This module provides customizable interface for simulating runtime behavior
of RISC-V programs on a YAQCS architecture. It is to be incorporated
into the YAQCS toolchain as a mock backend for classical validation
and verification of quantum programs deployable on a real YAQCS
architecture.
"""

import argparse
import json
import subprocess
import os
import signal
import time

QUANTUM_COMMAND_DIR = '/yaqcs-arch/simulator/quantum_command.txt'
EXIT_CODE_DIR = '/yaqcs-arch/simulator/exit_code.txt'


def build_riscv_command(config, kernel, debug=False):
    """
    Build shell command initiating a RISC-V simulator, with the
    input program loaded as a kernel.
    Currently only supports `QEMU`.

    Args:
        config (dict): configurations containing specification of the
        RISC-V simulator.
        kernel (str): RISC-V kernel program to be simulated.

    Returns:
        List[str]: shell command initiating the RISC-V program simulation.

    Raises:
        ValueError: Unsupported RISC-V backend. Happens when 
        `config['classical_backend']!='qemu'`. 
        KeyError: Required configuration keyword missing.
    """
    try:
        classical_backend = config['classical_backend']
        SUPPORTED_CLASSICAL_BACKEND = ['qemu']
        if classical_backend not in SUPPORTED_CLASSICAL_BACKEND:
            raise ValueError("Classical backend {} not yet supported!\n Currently supported backend = {}".format(
                classical_backend, SUPPORTED_CLASSICAL_BACKEND))
        if classical_backend == 'qemu':
            command_strs = ["qemu-system-riscv64"]
            qemu_params = config['qemu_params']
            command_strs += ["-bios", qemu_params['bios']]
            command_strs += ["-machine", qemu_params['machine']]
            command_strs += ["-cpu", qemu_params['cpu']]
            command_strs += ["-nographic"] if qemu_params['nographic'] else []
            additional_params = qemu_params.get('additional', [])
            if debug:
                additional_params = list(set(additional_params + ['-s', '-S']))  # avoid repeated flags
            command_strs += additional_params
            command_strs += ["-kernel", kernel]
        return command_strs
    except KeyError as e:
        raise "Keyword missing in config file. Please revise." + e


def build_quantum_command(config):
    """
    Build a shell command invoking the pulse-level simulator for pulse-level
    quantum-device simulation.
    Args:
        config (dict): configurations containing specification of the
        pulse-level simulator.

    Returns:
        str: shell command invoking the pulse-level simulation.

    Raises:
        ValueError: Unsupported RISC-V backend. Happens when
        `config['quantum_backend']` not in `SUPPORTED_QUANTUM_BACKEND`.
        KeyError: Required configuration keyword missing.
    """
    try:
        SUPPORTED_QUANTUM_BACKEND = ['qutip', 'qutip-qip', 'qutip_qip', 'stim']
        quantum_backend = config['quantum_backend']
        if quantum_backend not in SUPPORTED_QUANTUM_BACKEND:
            raise ValueError("Quantum backend {} not yet supported!\n Currently supported backend = {}".format(
                quantum_backend, SUPPORTED_QUANTUM_BACKEND))
        command_str = "python3 " +\
            "/yaqcs-arch/simulator/pulse_simulator/pulse_simulator.py " +\
            "/yaqcs-arch/simulator/pulse_simulator/pulse.json " +\
            "pulses.txt output.txt {}; ".format(quantum_backend + " " + " ".join(config['quantum_backend_params'])) +\
            "echo $? > exit_code.txt"
        return command_str
    except KeyError as e:
        raise "Keyword missing in config file. Please revise." + e


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', help='config file for QCS simulator',
                        default='/yaqcs-arch/simulator/sim.json', action='store')
    parser.add_argument('-q', '--quantum-backend', dest='quantum_backend', help='quantum backend used in simulation',
                        default=None, action='store')
    parser.add_argument('-d', '--debug', action='store_true', help='enable debug mode for gdb to attach')
    parser.add_argument('kernel', action='store')

    args = parser.parse_args()
    config_file = args.config
    kernel = args.kernel
    with open(config_file, 'r') as f:
        config_json = json.load(f)

    # Build pulse-level simulation shell command
    # Quantum command is written to a file, ready to be called by the RISC-V
    # simulator through system call
    if args.quantum_backend is not None:
        config_json['quantum_backend'] = args.quantum_backend
    quantum_command = build_quantum_command(config_json)
    with open(QUANTUM_COMMAND_DIR, 'w') as f:
        f.write(quantum_command)

    # Build RISC-V simulation shell command
    riscv_commands = build_riscv_command(config_json, kernel, args.debug)

    p = subprocess.Popen(riscv_commands)
    if config_json['qemu_params']['machine'] != "smarth":
        # The simulator does not terminate automatically without an OS;
        # Need to have it killed upon the kernel program producing an
        # exit code
        while not os.path.exists(EXIT_CODE_DIR):
            time.sleep(1)
        with open(EXIT_CODE_DIR, 'r') as f:
            exit_code = int(f.readline().split(" ")[-1])
        subprocess.run(["rm", "-f", EXIT_CODE_DIR])
        os.kill(p.pid, signal.SIGTERM)
    else:
        exit_code = p.wait()
    print("RISC-V simulator completed with code {}".format(exit_code))
