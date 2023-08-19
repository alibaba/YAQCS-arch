import unittest
from contextlib import contextmanager
import subprocess as sp
import struct
import numpy as np
from scipy.stats import binomtest
import json

num_repeat = 1000
PROGRAMS_PATH = '/yaqcs-arch/programs/qasm/tests'

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
        #print('s: ', s)
        addr_fin = int(s.split()[0])
        length_fin = int(s.split()[1])
        if length_fin == 8:
            data_fin = float(s.split()[2])
        else:
            data_fin = int(s.split()[2])
        self.assertEqual(addr_fin, addr)
        self.assertEqual(length_fin, length)
        #print('data_fin: ', data_fin)
        #print('data_criterion: ', data_criterion)
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
        print('Running t1_demo test')
        with self.open_output_file('t1_demo', backend = 'qutip'):
            for t1_delay in range(0, 500, 50):
                #print('t1_delay: ', t1_delay)
                #self.check_pcie(t1_delay)
                p = np.exp(-(t1_delay + 50) / self.t1_ground_truth)
                self.check_pcie(self.binom_criterion(num_repeat, p))
    
    def test_x_sequence(self):
        print('Running x_sequence test')
        with self.open_output_file('x_sequence', backend = 'qutip_qip'):
            self.check_pcie(0)
            self.check_pcie(num_repeat)

    def test_z_sequence(self):
        print('Running z_sequence test')
        with self.open_output_file('z_sequence', backend = 'qutip_qip'):
            self.check_pcie(0)
            self.check_pcie(num_repeat)

    def test_h_sequence(self):
        print('Running h_sequence test')
        with self.open_output_file('h_sequence', backend = 'qutip_qip'):
            self.check_pcie(0)
            self.check_pcie(self.binom_criterion(num_repeat, 0.5))

    def test_s_sequence(self):
        print('Running s_sequence test')
        with self.open_output_file('s_sequence', backend = 'qutip_qip'):
            self.check_pcie(0)
            self.check_pcie(num_repeat)

    def test_t_sequence(self):
        print('Running t_sequence test')
        with self.open_output_file('t_sequence', backend = 'qutip_qip'):
            self.check_pcie(0)
            self.check_pcie(num_repeat)

if __name__ == '__main__':
    unittest.main()