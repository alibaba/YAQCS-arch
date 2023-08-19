# Copyright 2023 Alibaba Group

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest
from contextlib import contextmanager
import subprocess as sp
import struct
import numpy as np
from scipy.stats import binomtest
import json

PROGRAMS_PATH = '/yaqcs-arch/programs'


class TestPrograms(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open('/yaqcs-arch/simulator/sim.json', 'r') as fin:
            cls.config = json.load(fin)

    @contextmanager
    def open_output_file(self, program, params=None, topology='default', backend=None):
        self.assertEqual(
            sp.call(['make', f'{topology}_topology'], cwd=PROGRAMS_PATH), 0)
        cmd = ['bash', 'test.sh']
        if params is not None:
            with open(PROGRAMS_PATH + '/params.txt', 'w') as f:
                f.write(str(len(params)) + '\n')
                f.write('\n'.join([str(i) for i in params]))
        if backend is not None:
            with open(PROGRAMS_PATH + '/config.json', 'w') as fout:
                json.dump({**self.config, 'quantum_backend': backend}, fout)
            cmd.extend(['-c', 'config.json'])
        cmd.append(program)
        print(cmd)
        self.assertEqual(sp.call(cmd, cwd=PROGRAMS_PATH), 0)
        self.fin = open(PROGRAMS_PATH + '/pcie.txt', 'r')
        try:
            yield self.fin
            # Assert that there are no extra lines in the output
            self.assertEqual(self.fin.read().strip(), '')
        finally:
            self.fin.close()

    def check_pcie(self, data_criterion=lambda data: True, addr=0, length=4):
        s = self.fin.readline()
        addr_fin = int(s.split()[0])
        length_fin = int(s.split()[1])
        if length_fin == 8:
            data_fin = float(s.split()[2])
        else:
            data_fin = int(s.split()[2])
        self.assertEqual(addr_fin, addr)
        self.assertEqual(length_fin, length)
        if isinstance(data_criterion, int):
            self.assertEqual(data_fin, data_criterion)
        else:
            self.assertTrue(data_criterion(data_fin))
        return data_fin

    def check_vector_pcie(self, data_criterion=lambda data: True, addr=0, length=4):
        s = bytes(self.check_pcie(addr=addr + i, length=1)
                  for i in range(length))
        data_fin, = struct.unpack('i', s)  # For now this forces length to be 4
        if isinstance(data_criterion, int):
            self.assertEqual(data_fin, data_criterion)
        else:
            self.assertTrue(data_criterion(data_fin))
        return data_fin

    def binom_criterion(self, n, p):
        def criterion(data):
            res = binomtest(data, n, p)
            print(res)
            # Be a little safe here to make sure the probability of a false positive is negligible
            return res.pvalue > 1e-15
        return criterion

    def normal_criterion(self, n, p):
        def criterion(data):
            print(data, p)
            return np.abs(data - p) < 3 / np.sqrt(n)
        return criterion

    # These values are also hardcoded in /simulator/pulse_simulator/config_gen.py
    t1_ground_truth = 4000
    tphi_ground_truth = 4000
    # Computed from t1 and tphi above: 1 / t2 = 1 / (2 * t1) + 1 / phi
    t2_ground_truth = 1 / (1 / (2 * t1_ground_truth) + 1 / tphi_ground_truth)

    # The below estimates of p are not completely accurate, but should be good enough for testing purposes

    def test_t1_demo(self):
        with self.open_output_file('t1_demo'):
            for t1_delay in range(0, 500, 50):
                self.check_pcie(t1_delay)
                p = np.exp(-(t1_delay + 50) / self.t1_ground_truth)
                self.check_pcie(self.binom_criterion(1000, p))

    def test_t1(self):
        with self.open_output_file('t1', params=[500, 100, 1000]):
            for t1_delay in range(0, 500, 100):
                self.check_pcie(t1_delay)
                p = np.exp(-(t1_delay + 50) / self.t1_ground_truth)
                self.check_pcie(self.binom_criterion(1000, p))

    def test_t1_iq(self):
        with self.open_output_file('t1_iq', params=[500, 100, 1000]):
            for t1_delay in range(0, 500, 100):
                self.check_pcie(t1_delay)
                p = np.exp(-(t1_delay + 50) / self.t1_ground_truth)
                self.check_pcie(self.normal_criterion(1000, p), length=8)

    def test_t1_simul(self):
        with self.open_output_file('t1_simul', params=[500, 100, 1000]):
            for t1_delay in range(0, 500, 100):
                self.check_pcie(t1_delay)
                p = np.exp(-(t1_delay + 50) / self.t1_ground_truth)
                self.check_pcie(self.binom_criterion(1000, p))
                self.check_pcie(self.binom_criterion(1000, p))

    def test_t2(self):
        fringe = 20
        with self.open_output_file('t2', params=[fringe, 500, 100, 1000]):
            for t2_delay in range(0, 500, 100):
                self.check_pcie(t2_delay)
                p = (1 + np.exp(-(t2_delay + 100) / self.t2_ground_truth)
                     * np.cos(t2_delay * fringe / 1000)) / 2
                self.check_pcie(self.binom_criterion(1000, p))

    def test_rb(self):
        with self.open_output_file('rb', params=[28495, 5, 1, 2, 4, 6, 8, 10]):
            for length in range(2, 11, 2):
                self.check_pcie(length)
                p = (1 + np.exp(-(length * 187.5 + 100) / self.tphi_ground_truth)) / 2
                self.check_pcie(self.binom_criterion(1000, p))

    def test_vector_t1(self):
        with self.open_output_file('vector_t1', params=[500, 50, 1000]):
            for t1_delay in range(0, 500, 50):
                self.check_pcie(t1_delay)
                p = np.exp(-(t1_delay + 50) / self.t1_ground_truth)
                for k in range(5):
                    self.check_vector_pcie(
                        self.binom_criterion(1000, p), addr=k * 4)

    def test_rabi_amp(self):
        with self.open_output_file('rabi_amp', params=[10, 5, 20, 5], backend='qutip_qip'):
            for freq in range(-10, 11, 5):
                for amp in range(1, 20, 5):
                    self.check_pcie(freq)
                    self.check_pcie(amp)
                    xangle = np.pi / 8 * amp
                    zangle = freq / 2
                    p = np.sin(np.sqrt(xangle ** 2 + zangle ** 2)) ** 2 * \
                        xangle ** 2 / (zangle ** 2 + xangle ** 2)
                    self.check_pcie(self.binom_criterion(1000, p))

    def test_rabi(self):
        with self.open_output_file('rabi', params=[10, 5, 20, 5], backend='qutip_qip'):
            for freq in range(-10, 11, 5):
                for length in range(1, 20, 5):
                    self.check_pcie(freq)
                    self.check_pcie(length)
                    xangle = np.pi / 2
                    zangle = freq / 2
                    p = np.sin(length / 4 * np.sqrt(xangle ** 2 + zangle ** 2)) ** 2 * \
                        xangle ** 2 / (zangle ** 2 + xangle ** 2)
                    self.check_pcie(self.binom_criterion(1000, p))

    def test_rabi_z(self):
        with self.open_output_file('rabi_z', params=[10, 5, 20, 5]):
            for z in range(-10, 11, 5):
                for length in range(1, 20, 5):
                    self.check_pcie(z)
                    self.check_pcie(length)
                    xangle = np.pi / 2
                    zangle = z ** 2 / 9
                    p = (1 / 2 + (np.sin(length / 4 * np.sqrt(xangle ** 2 + zangle ** 2)) ** 2 - 1 / 2) *
                         np.exp(-length * 25 / self.t2_ground_truth)) * \
                        xangle ** 2 / (zangle ** 2 + xangle ** 2)
                    self.check_pcie(self.binom_criterion(1000, p))

    def test_rabi_pulse(self):
        with self.open_output_file('rabi_pulse', params=[10, 5, 20, 5]):
            for length in range(1, 20, 5):
                for freq in range(-10, 11, 5):
                    self.check_pcie(freq)
                    self.check_pcie(length)
                    xangle = np.pi / 2
                    zangle = freq / 2
                    p = (1 / 2 + (np.sin(length / 4 * np.sqrt(xangle ** 2 + zangle ** 2)) ** 2 - 1 / 2) *
                         np.exp(-length * 25 / self.t2_ground_truth)) * \
                        xangle ** 2 / (zangle ** 2 + xangle ** 2)
                    self.check_pcie(self.binom_criterion(1000, p))

    def test_qmemory_experiment(self):
        with self.open_output_file('qmemory_experiment', topology='qec', backend='stim'):
            data = []
            for k in range(5):
                self.check_pcie(100)
                self.check_pcie(k)
                self.check_pcie(200)
                for i in range(4):
                    if k == 0:
                        data.append(self.check_pcie())
                    else:
                        self.check_pcie(0 if k % 2 else data[i])
                for i in range(4):
                    self.check_pcie(1 - k % 2)


if __name__ == '__main__':
    unittest.main()
