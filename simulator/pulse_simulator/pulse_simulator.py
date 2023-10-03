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

"""Pulse simulator backend for yaqcs architecture backend.

This module provides an interface for simulating quantum computation processes
described as pulse-level instructions. It is to be incorporated into the
YAQCS toolchain as a mock backend supporting validation and verification
of pulse-level instructions generated from upper levels.

Typical usage example (in command line):
    > python -m pulse_simulator.py config_file input_file output_file [backend]
"""

import sys
import warnings
import json

import numpy as np

with warnings.catch_warnings():
    warnings.filterwarnings('ignore',
                            message='matplotlib not found',
                            module='qutip')
    from qutip import ket2dm, Options, basis
    from qutip.operators import sigmay, sigmax, sigmaz, Qobj
    from qutip.tensor import tensor
    from qutip_qip.device import Processor
    from qutip_qip.pulse import Pulse
    from qutip_qip.qubits import qubit_states
    from qutip_qip.circuit import QubitCircuit
import stim

_ISWAP_HAM = (tensor(sigmax(), sigmax()) + tensor(sigmay(), sigmay())) / 2
_CPHASE_HAM = Qobj(np.diag([0, 0, 0, 1]))
_CPHASE_HAM.dims = [[2, 2], [2, 2]]
_DEFAULT_AMP = np.pi / 200
_DEFAULT_RANGE = 0x4000
_DEFAULT_LEN = 100


def single_qubit_gate(params):
    """
    Generate single qubit gates from pulse parameters. Used in gate-level
    simulation with `qutip_qip`.

    Args:
        params(List[double]): List of parameters specifying a 1q gate operation.

    Returns:
        numpy.array: Compiled single qubit gate as a 2x2 unitary matrix.
    """
    Paulis = [np.eye(2), 1j * np.diag([1, -1]), 1j *
              np.eye(2)[::-1], np.diag([-1, 1])[::-1]]
    xangle = np.pi / 2 * params[2]
    if params[-1] == 1:
        xangle /= 2
    zangle = _DEFAULT_LEN / 2 * params[1]
    freq = np.sqrt(zangle ** 2 + xangle ** 2)
    freq_angle = freq
    if params[-1] == 2:
        freq_angle *= params[3] / _DEFAULT_LEN
    coeffs = [
        np.cos(freq_angle),
        -np.sin(freq_angle) * zangle / freq,
        np.sin(freq_angle) * xangle / freq *
        np.cos(params[0] + _DEFAULT_LEN * params[1]),
        np.sin(freq_angle) * xangle / freq *
        np.sin(params[0] + _DEFAULT_LEN * params[1]),
    ]
    res = Qobj(np.sum([coeffs[i] * Paulis[i]
               for i in range(4)], axis=0), dims=[[2], [2]])
    return res


def two_qubit_gate(params):
    """
    Generate two qubit gates from pulse parameters. Used in gate-level
    simulation with `qutip_qip`.

    Args:
        params(List[double]): List of parameters specifying a 2q gate operation.

    Returns:
        numpy.array: Compiled two qubit gate as a 4x4 unitary matrix.
    """
    if params[0] == 0:
        res = np.diag([1, 1, 1, np.exp(1j * params[1])])
    else:
        res = np.array([[1, 0, 0, 0], [0, np.cos(params[1]/2), 1j * np.sin(params[1]  / 2), 0],
                        [0, 1j * np.sin(params[1]  / 2), np.cos(params[1]  / 2), 0], [0, 0, 0, 1]])
    return Qobj(res, dims=[[2,2],[2,2]])


def z_to_f(z):
    """
    Map Z line pulse to sigma-Z Hamiltonian strength in the rotating frame,
    indicated by the sweet-spot frequency.
    Assuming that Z=0 set the qubit to sweet spot, the resulting energy difference
    is mocked by a quadratic change with respect to the Z-line offset.

    Args:
        z(double): Z-line offset strength.

    Returns:
        double: Effective strength of Sigma-Z Hamiltonian under rotating frame.
    """
    return z ** 2


class PulseSimulator():
    """Simulator backend class.

    The `PulseSimulator` class incorporates several simulator softwares for
    quantum computation, including `qutip` for pulse-level simulation, `qutip_qip`
    for gate-level simulation and `stim` for polynomial-time Clifford circuit simulation
    for large-scale quantum circuits.

    Args:
        config_file (str): A '.json' file containing the descriptions of the
        quantum device.
        input_file (str): A '.qsim' file specifying the instructions to be
        executed on the simulator.
        output_file (str): Output file name for the simulation result.
        backend (str, optional): Backend software used in simulation. Currently
        supports 'qutip', 'stim' and 'qutip_qip', planning to add 'acqdp'. Specifying
        'backend' to other values will not immediately but will raise a
        'ValueError' when '.execute()' is called. Defaults to 'qutip'.
    """

    def __init__(self, config_file, input_file, output_file, backend='qutip'):
        with open(config_file, 'r') as f:
            self.pulse_config = json.load(f)
        self.num_qubits = len(self.pulse_config['qubits'])

        def get_noise(dic, key):
            try:
                return dic['noise'][key]
            except KeyError:
                return None

        self.t1_list = [
            get_noise(self.pulse_config['qubits'][i], 't1')
            for i in self.pulse_config['qubits']
        ]
        self.t2_list = [
            get_noise(self.pulse_config['qubits'][i], 't2')
            for i in self.pulse_config['qubits']
        ]
        self.center_list = [self.pulse_config['qubits'][i]
                            ['readout_center'] for i in self.pulse_config['qubits']]
        self.input_file = input_file
        self.output_file = output_file
        self.backend = backend
        with open(self.input_file, 'r') as f:
            self.instr_list = f.read().split("\n")
        self.num_cycles = int(self.instr_list[0])

    class PulseInstruction():
        """Class indicating pulse informations for one operation.

        A 'PulseInstruction' is generated upon parsing one line of '.qsim'
        instruction from 'PulseSimulator._parse_instr()'.

        Attributes:
            pulse_type (str) : type of the operation, from 'gate_1q', 'gate_2q',
            'measure' or 'reset'.
            targets (List[int]) : target qubits where the operation is acted upon.
            index (int) : waveform index of the operation. Index 128 is reserved
            for measurement.
            tlist (Optional[List[double], None]]): Lists of timesteps of the
            pulse coefficients. Only present when 'index' != 128.
            coefs (Optional[List[List[double]], List[double], None]): Waveform
            envelopes. For 1q gates the waveform contains two quadrants; for 2q
            gates the waveform contains one envelope. For measurements the
            waveform is 'None'.
            params (Optional[List[double], None]): Other parameters in the
            instruction. For 1q gates 'params' contains a relative phase
            parameter, an intermediate frequency, and an amplitude multiplier.
            delay (Optional[double, None]): Time delay of the operation.
        """

        def __init__(self,
                     pulse_type,
                     targets,
                     index,
                     tlist=None,
                     coefs=None,
                     params=None,
                     delay=None):
            self.pulse_type = pulse_type
            self.targets = targets
            self.index = index
            self.tlist = tlist
            self.coefs = coefs
            self.params = params
            self.delay = delay

    def execute(self):
        """Execution entrance for simulation.

        Raises:
            ValueError: Unsupported backend, when 'self.backend' is not in
            '['qutip', 'stim', 'qutip_qip', 'qutip-qip' 'acqdp']'.
            'qutip-qip' and 'qutip_qip' can be used interchangeably.
        """
        # Parse `.qsim` files to PulseInstructions
        self._parse_instr(self.instr_list)

        # Execute PulseInstructions with given backend
        if self.backend == "qutip":
            res = self._execute_qutip()
        elif self.backend == "stim":
            res = self._execute_stim()
        elif self.backend == "acqdp":
            res = self._execute_acqdp()
        elif self.backend == "qutip_qip" or self.backend == "qutip-qip":
            res = self._execute_qutip_qip()
        else:
            raise ValueError(f"Unsupported backend: {self.backend}")
        with open(self.output_file, 'w') as f:
            f.write("\n".join([" ".join(i) for i in res[0]]) + "\n")
            f.write("\n".join(
                ["\n".join([str(j[0]) + " " + str(j[1]) for j in i]) for i in res[1]]) + "\n")

    def _parse_instr(self, instr_list):
        """Parse a list of '.qsim' instruction into a list of 'PulseInstruction'.

        Args:
            instr_list (List[str]): A list of '.qsim' instructions

        Returns:
            List['PulseInstruction'] : Compiled 'PulseInstruction' obejcts for further
            incorporation into backends.
        """
        res = []
        square_dic_xy = {}
        square_dic_z = {}
        for instr in instr_list[1:]:
            if len(instr) == 0:
                continue
            params = instr.split(" ")
            delay = int(params[0])
            channel = params[1]
            channel_config = self.pulse_config["channels"][channel]
            channel_type = channel_config["type"]
            targets = channel_config["target"]
            index = params[2]
            if channel_type == '1Q':
                inst_type = channel_config['waveforms'][index][0]
                if inst_type == 'xy_waveform':  # 1 qubit drive line gates specified by pulse
                    coefs = channel_config['waveforms'][index][1]
                    coefs_x, coefs_y = coefs
                    tlist = np.linspace(0, len(coefs_x) - 1, len(coefs_x))
                    coefs = [list(np.array(coefs_x) * _DEFAULT_AMP / _DEFAULT_RANGE),
                             list(np.array(coefs_y) * _DEFAULT_AMP / _DEFAULT_RANGE)]
                    res.append(PulseSimulator.PulseInstruction('gate_1q', targets,
                                                               index, tlist, coefs,
                                                               params, delay=delay))
                elif inst_type == 'xy_square_up':  # 1 qubit drive line square pulse raising edge
                    if targets in square_dic_xy:
                        raise IndexError(
                            "Raising edge applied on already raised qubit")
                    square_dic_xy[targets] = [index, params, delay]
                elif inst_type == 'xy_square_down':  # 1 qubit drive line square pulse falling edge
                    if targets in square_dic_xy:
                        index_last, params, delay_last = square_dic_xy.pop(
                            targets)
                        params[6] = delay - delay_last
                        tlist = np.linspace(
                            0, delay - delay_last, delay - delay_last + 1)
                        coeff_x = [
                            0] + [_DEFAULT_AMP * (len(tlist) - 1) / (len(tlist) - 2)] * (len(tlist) - 2) + [0]
                        coeff_y = [0] * len(tlist)
                        res.append(PulseSimulator.PulseInstruction('gate_1q', targets,
                                                                   index_last, tlist, [
                                                                       coeff_x, coeff_y],
                                                                   params, delay=delay_last))
                    else:
                        raise IndexError(
                            "Square pulse falling edge before raising edge")
                elif inst_type == 'z_square_up':  # 1 qubit drive line square pulse raising edge
                    if targets in square_dic_z:
                        raise IndexError(
                            "Raising edge applied on already raised qubit")
                    # 1 qubit drive line square pulse falling edge
                    square_dic_z[targets] = [index, params, delay]
                elif inst_type == 'z_square_down':
                    if targets in square_dic_z:
                        index_last, params, delay_last = square_dic_z.pop(
                            targets)
                        params[6] = delay - delay_last
                        tlist = np.linspace(
                            0, delay - delay_last, delay - delay_last + 1)
                        coeff = [
                            0] + [1] * (len(tlist) - 2) + [0]
                        res.append(PulseSimulator.PulseInstruction('gate_1q_z', targets,
                                                                   index_last, tlist, coeff,
                                                                   params, delay=delay_last))
                    else:
                        raise IndexError(
                            "Square pulse falling edge before raising edge")
                elif inst_type == 'reset':  # special index reserved for state preparation
                    res.append(PulseSimulator.PulseInstruction('reset', targets,
                                                               index))
                elif inst_type == 'measure':  # special index reserved for measurements
                    res.append(PulseSimulator.PulseInstruction('measure',
                                                               targets,
                                                               index,
                                                               delay=delay))
            elif channel_type == '2Q':  # 2 qubit gates
                coefs = channel_config['waveforms'][index][0]
                tlist = np.linspace(0, len(coefs) - 1, len(coefs))
                res.append(PulseSimulator.PulseInstruction('gate_2q', targets, index,
                                                           tlist, coefs, params, delay=delay))

        self.pulse_instrs = res
        return res

    def _execute_qutip(self):
        """Pulse-level simulation using 'qutip' backend.

        Returns:
            List[str]: Result bitstrings. The number of bitstrings is
            determined by 'self.num_cycles', and the number of bits in each
            bitstring is determined by the number of qubits being measured.
        """
        # Compile instructions into pulses
        processor = Processor(num_qubits=self.num_qubits,
                              t1=self.t1_list,
                              t2=self.t2_list)
        tlist, measure_qubits = self._process_pulses(
            processor, self.pulse_instrs)

        # Pulse simulation
        state = ket2dm(qubit_states(self.num_qubits))
        solver_result = processor.run_state(init_state=state,
                                            tlist=np.linspace(
                                                0, max(tlist),
                                                int(max(tlist)) + 1),
                                            options=Options(max_step=1))

        # Sample bistrings from the final probability distribution
        res_prob = np.diag(np.real(solver_result.states[-1].full()))
        res_bitstrings = self._sample_bitstrings(res_prob, measure_qubits)
        res_iq = self._sample_readout_iq(res_bitstrings, measure_qubits)
        return res_bitstrings, res_iq

    def _process_pulses(self, processor, pulse_instrs):
        """Compile PulseInstruction instructions into pulse objects in qutip.

        Args:
            processor (qutip_qip.device.Processor): 'Processor' object
            incorporating all pulses and the noise model.
            pulse_instrs (List[PulseSimulator.PulseInstruction]): List of PulseInstructions
            parsed from input `.qsim` file.

        Returns:
            List[double], List[int]: List of timesteps for qutip ODE solver, and
            list of measured qubits for sampling.
        """
        full_tlist = []
        measure_qubits = []
        for pulse_instr in pulse_instrs:
            if pulse_instr.pulse_type == 'gate_1q':  # 1Q drive line gates
                theta = float(pulse_instr.params[3])
                freq = float(pulse_instr.params[4])
                amp = float(pulse_instr.params[5])
                tlist = np.array(pulse_instr.tlist) + pulse_instr.delay
                coeff_x, coeff_y = pulse_instr.coefs
                waveform_comp = amp * np.exp(1j * (theta + freq * tlist)) \
                                    * (np.array(coeff_x) + 1j * np.array(coeff_y))
                waveform_x = np.real(waveform_comp)
                waveform_y = np.imag(waveform_comp)
                pulsex = Pulse(sigmax(), pulse_instr.targets, tlist,
                               waveform_x)
                pulsey = Pulse(sigmay(), pulse_instr.targets, tlist,
                               waveform_y)
                processor.add_pulse(pulsex)
                processor.add_pulse(pulsey)
                full_tlist += list(tlist)
            elif pulse_instr.pulse_type == 'gate_1q_z':  # 1Q Z line gates
                amp = float(pulse_instr.params[5])
                tlist = np.array(pulse_instr.tlist) + pulse_instr.delay
                coeff = pulse_instr.coefs
                waveform = np.array(coeff) * z_to_f(amp)
                pulse = Pulse(sigmaz(), pulse_instr.targets, tlist,
                              waveform)
                processor.add_pulse(pulse)
                full_tlist += list(tlist)
            elif pulse_instr.pulse_type == 'measure':  # 1Q measurement
                full_tlist += [pulse_instr.delay]
                measure_qubits.append(pulse_instr.targets)
            elif pulse_instr.pulse_type == 'reset':
                pass
            elif pulse_instr.pulse_type == 'gate_2q':  # 2Q gates
                ham = _CPHASE_HAM if pulse_instr.index == "0" else _ISWAP_HAM
                tlist = np.array(pulse_instr.tlist) + pulse_instr.delay
                pulse = Pulse(ham, pulse_instr.targets, list(tlist),
                              np.array(pulse_instr.coefs))
                processor.add_pulse(pulse)
                full_tlist += list(tlist)
        return full_tlist, measure_qubits

    def _execute_qutip_qip(self):
        """Gate-level simulation with the 'qutip_qip' backend.

        Each pulse instruction is translated to a unitary gate and simulated
        using the 'qutip_qip' backend.

        Currently not supporting noise models.

        Returns:
            List[str]: Result bitstrings. The number of bitstrings is
            determined by 'self.num_cycles', and the number of bits in each
            bitstring is determined by the number of qubits being measured.
        """
        qc = QubitCircuit(N=self.num_qubits)
        measure_qubits = self._process_gates(qc, self.pulse_instrs)
        res = np.array(
            qc.run(state=tensor(*[basis(2, 0)] * self.num_qubits))).flatten()
        res_bitstrings = self._sample_bitstrings(
            np.real(res * np.conj(res)), measure_qubits)
        res_iq = self._sample_readout_iq(res_bitstrings, measure_qubits)
        return res_bitstrings, res_iq

    def _process_gates(self, qc, pulse_instrs):
        """Compile PulseInstructions into gate objects in qutip_qip.

        Args:
            qc (qutip_qip.circuit.QubitCircuit): 'QubitCircuit' object
            incorporating all gates.
            pulse_instrs (List[PulseSimulator.PulseInstruction]): List of PulseInstructions
            parsed from input `.qsim` file.

        Returns:
            List[int]: List of measured qubits for sampling.
        """
        measure_qubits = []
        qc.user_gates = {"gate_1q": single_qubit_gate,
                         "gate_2q": two_qubit_gate}
        for pulse_instr in pulse_instrs:
            if pulse_instr.pulse_type == 'gate_1q':  # 1Q gates
                params = [float(i) for i in pulse_instr.params[3:]
                          ] + [int(pulse_instr.index)]
                qc.add_gate("gate_1q", targets=pulse_instr.targets,
                            arg_value=params)
            elif pulse_instr.pulse_type == 'measure':  # 1Q measurement
                measure_qubits.append(pulse_instr.targets)
            elif pulse_instr.pulse_type == 'gate_2q':  # 2Q gates
                qc.add_gate("gate_2q", targets=pulse_instr.targets, arg_value=(
                    int(pulse_instr.index), float(pulse_instr.params[5])))
        return measure_qubits

    def _execute_stim(self):
        """Clifford-level simulation with the 'stim' backend.

        Each pulse instruction is translated to a Clifford gate and simulated
        using the 'stim' backend.

        Currently not supporting IQ readout.

        Returns:
            List[str]: Result bitstrings. The number of bitstrings is
            determined by 'self.num_cycles', and the number of bits in each
            bitstring is determined by the number of qubits being measured.
        """
        circuit = stim.Circuit()
        self._process_stim_cliffords(circuit, self.pulse_instrs)
        sampler = circuit.compile_sampler()
        res = sampler.sample(shots=self.num_cycles)
        return ["".join(str(int(i)) for i in j) for j in res], [[[0., 0.]] * len(j) for j in res]

    def _process_stim_cliffords(self, circuit, pulse_instrs):
        """Compile PulseInstructions into Clifford gates in Stim.

        Args:
            circuit (stim.Circuit): `Clifford circuit` incorporating all Clifford gates.
            pulse_instrs (List[PulseSimulator.PulseInstruction]): List of PulseInstructions
            parsed from input `.qsim` file.
        """
        for pulse_instr in pulse_instrs:
            if pulse_instr.pulse_type == "gate_1q":
                op_dic = {
                    "0": {
                        0: 'X',
                        2: 'X',
                        1: 'Y',
                        3: 'Y',
                    },
                    "1": {
                        0: 'SQRT_X',
                        2: 'SQRT_X_DAG',
                        1: 'SQRT_Y',
                        3: 'SQRT_Y_DAG',
                    }
                }
                theta = np.mod(int(float(pulse_instr.params[3]) / (np.pi/2)), 4)
                index = "1" if pulse_instr.index == '0' and float(pulse_instr.params[5]) == 0.5 else pulse_instr.index
                try:
                    operation = op_dic[index][theta]
                    circuit.append_operation(operation,
                                             [int(pulse_instr.targets)])
                except KeyError as e:
                    raise ValueError(
                        'Non-clifford operation not supported') from e
            elif pulse_instr.pulse_type == 'measure':
                circuit.append_operation("M", [int(pulse_instr.targets)])
            elif pulse_instr.pulse_type == "gate_2q":
                operation = "CZ" if pulse_instr.index == "0" else "ISWAP"
                circuit.append_operation(operation, pulse_instr.targets)

    def _sample_bitstrings(self, res_prob, measure_qubits):
        """Sample bistrings given underlying probability distribution.

        Args:
            res_prob (List[double]): Probability distribution
            measure_qubits (List[int]): Qubit list where the measurement is
            taking place. The final measurement result would only be on those
            qubits.

        Returns:
            List[str]: Sampled bistrings on the given qubits.
        """

        # generate all binary bitstrings of length self.num_qubits
        bitstring_list = [
            format(i, '0' + str(self.num_qubits) + 'b')
            for i in range(2**self.num_qubits)
        ]

        # sample all bitstrings
        bitstring_samples = np.random.choice(bitstring_list,
                                             self.num_cycles,
                                             p=res_prob)
        # project onto the actual measured qubits
        res = [[s[i] for i in measure_qubits] for s in bitstring_samples]
        return res

    def _sample_readout_iq(self, bitstrings, measure_qubits):
        """Sample IQ quadruples given underlying probability distribution.

        This is a mock sampling scheme of IQ quadruples. IQ quadrature data is generated
        from Gaussian distributions indicated by previously sampled binary results.

        Args:
            bitstrings (List[str]): Sampled bitstrings
            measure_qubits (List[int]): Qubit list where the measurement is
            taking place. The final measurement result would only be on those
            qubits.

        Returns:
            List[str]: Sampled IQ quadruples on the given qubits.
        """
        return [[[np.random.normal(self.center_list[measure_qubits[i]][bitstring[i]][0]), np.random.normal(
            self.center_list[measure_qubits[i]][bitstring[i]][1])] for i in range(len(measure_qubits))] for bitstring in bitstrings]


if __name__ == "__main__":
    argv = sys.argv
    PulseSimulator(*argv[1:]).execute()
