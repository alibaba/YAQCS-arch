import argparse
import json

parser = argparse.ArgumentParser(description='Generate the qubit topology for a rotated surface code')
parser.add_argument('n', metavar='N', type=int, help='size of the surface code (number of rows and columns of data qubits)')
parser.add_argument('topology_file', nargs='?', default='qec_topology.json', help='name of the output json file')
parser.add_argument('header_file', nargs='?', default='qec.h', help='name of the output header file containing constant macros (such as the number of qubits in each group)')
parser.add_argument('-v', '--visualize', action='store_true', help='visualize the layout of gates')

args = parser.parse_args()
n = args.n

# See https://arxiv.org/abs/1612.08208 for the surface code scheme used
# (including the meanings of these qubit group names)
qubit_group_name = {
    (0, 0): 'D1',
    (0, 2): 'D2',
    (2, 0): 'D3',
    (2, 2): 'D4',
    (1, 1): 'X1',
    (1, 3): 'Z1',
    (3, 1): 'Z2',
    (3, 3): 'X2',
    (-1, -1): 'dummy'
}

qubit_groups = {group: [] for group in qubit_group_name.values()}

# Generate a list of coordinates for qubits in the surface code.

# Data qubits are laid out in a square grid with unit distance 2 (so that
# ancilla qubits have integer coordinates), with even X and Y coordinates,
# starting from (0, 0).
data_qubit_coords = [(x * 2, y * 2) for x in range(n) for y in range(n)]

# Ancilla qubits have odd X and Y coordinates which may be -1 on the top/left
# boundaries. They are "staggered" between rows (hence the "y + x % 2"), and on
# the top and bottom boundaries only half of them exist.
ancilla_qubit_coords = [(x * 2 + 1, (y + x % 2) * 2 - 1)
                        for x in range(-1, n)
                        for y in (range(1, n, 2) if x in [-1, n - 1] else range(n))]
qubit_coords = data_qubit_coords + ancilla_qubit_coords

for x, y in qubit_coords:
    qubit_groups[qubit_group_name[x % 4, y % 4]].append((x, y))


def gen_CZ_gates(high_freq_group, low_freq_group):
    res = []
    for q1 in high_freq_group:
        for dx in -1, 1:
            for dy in -1, 1:
                q2 = q1[0] + dx, q1[1] + dy
                if q2 in low_freq_group:
                    res.append((q1, q2))
    return res


def visualize(gates=[]):
    gate_coords = [(min(x1, x2), min(y1, y2)) for (x1, y1), (x2, y2) in gates]
    for x in range(-1, n * 2):
        print('  '.join(f'{qubit_index[x, y]:2d}' if (x, y) in qubit_coords else '  ' for y in range(-1, n * 2)))
        print('  ' + '  '.join('**' if (x, y) in gate_coords else '  ' for y in range(-1, n * 2)))


macros = []
qubit_index = {}
n_qubits = 0
for group in 'D1', 'D2', 'D3', 'D4', 'X1', 'X2', 'Z1', 'Z2':
    macros.append((f'{group}_START', n_qubits))
    for qubit in qubit_groups[group]:
        qubit_index[qubit] = n_qubits
        n_qubits += 1
    macros.append((f'{group}_END', n_qubits))
    if group == 'D4':
        macros.append(('N_DATA_QUBITS', n_qubits))
macros.append(('N_QUBITS', n_qubits))

# In https://arxiv.org/abs/1612.08208, the two-qubit gates are implemented by
# flux pulsing qubits to detune their frequencies from their sweet spots so
# that they interact with neighboring qubits with nearby frequencies. Here in
# each tuple, the 1st qubit group is detuned to interact with the 2nd qubit
# group; the 3rd with the 4th. The 5th qubit group is also detuned to avoid
# unwanted interactions, which is currently irrelevant here, but it may affect
# the error model.
flux_dance_list = [
    ('D2', 'X1', 'X2', 'D3', 'D4'),
    ('D1', 'X1', 'X2', 'D4', 'D3'),
    ('D1', 'X2', 'X1', 'D4', 'D3'),
    ('D2', 'X2', 'X1', 'D3', 'D4'),
    ('D1', 'Z1', 'Z2', 'D4', 'D3'),
    ('D2', 'Z2', 'Z1', 'D3', 'D4'),
    ('D2', 'Z1', 'Z2', 'D3', 'D4'),
    ('D1', 'Z2', 'Z1', 'D4', 'D3')
]

qubit_topology = []
for i, flux_dance in enumerate(flux_dance_list):
    macros.append((f'SLOT_{i}_START', len(qubit_topology)))
    gates = []
    for g1, g2 in [flux_dance[0:2], flux_dance[2:4]]:
        gates += gen_CZ_gates(qubit_groups[g1], qubit_groups[g2])
    if args.visualize:
        print(flux_dance)
        print()
        visualize(gates)
    qubit_topology.extend([[qubit_index[q1], qubit_index[q2]] for q1, q2 in gates])
    macros.append((f'SLOT_{i}_END', len(qubit_topology)))

with open(args.topology_file, 'w') as fout:
    json.dump({'qubit_list': list(range(n_qubits)), 'qubit_topology': qubit_topology}, fout)

with open(args.header_file, 'w') as fout:
    fout.writelines(f'#define {k} {v}\n' for k, v in macros)
