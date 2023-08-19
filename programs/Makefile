.PRECIOUS: %.ll

TARGETS_CCC = t1 t1_demo t1_iq t2 rb rabi rabi_amp rabi_z rabi_pulse transmission t1_simul vector_t1
TARGETS_QEC = qmemory_experiment qmemory_experiment_scalar
TARGETS_QASM_DEMO = x_sequence z_sequence h_sequence s_sequence t_sequence t1_demo_qasm
TARGETS_QASM_ROUT = trivial cnot_ladder misc_circuit

CCC_DIR = cpp/calibration
QEC_DIR = cpp/qec
QASM_DEMO_DIR = qasm/demo
QASM_ROUT_DIR = qasm/routing

# Compile for smarth by default
# Switch to $(MACHINE) if MACHINE parameter is passed
MACHINE ?=
LINK = $(if $(MACHINE),_$(MACHINE))

CC = riscv64-unknown-elf-g++
MARCH = rv64imafdc
CFLAGS = -nostartfiles -static -mcmodel=medany -Wl,-T,util/link$(LINK).ld -march=$(MARCH) -DSIMULATOR
CFLAGS_QASM = -L/build/qir-qrt/build -lqir-qrt -mno-relax -nostartfiles -static -mcmodel=medany -Wl,-T,util/link$(LINK).ld -march=$(MARCH)

all: qec ccc

ccc: $(TARGETS_CCC) default_topology
qasm: $(TARGETS_QASM_ROUT) #$(TARGETS_QASM_DEMO) 

$(TARGETS_CCC) $(TARGETS_QEC): %: util/start$(LINK).S
	$(CC) $(CFLAGS) $^ -o $@

$(TARGETS_QASM_DEMO) $(TARGETS_QASM_ROUT): %: %.oqasm util/start$(LINK).S
	$(CC) $^ $(CFLAGS_QASM) -o $@

$(TARGETS_CCC): %: $(CCC_DIR)/%.cpp
$(filter %_scalar,$(TARGETS_QEC)): %_scalar: $(QEC_DIR)/%.cpp
$(filter-out %_scalar,$(TARGETS_QEC)): %: $(QEC_DIR)/%.cpp

LC = /opt/compiler/riscv-llvm/bin/clang
LMARCH = rv64gc
LFLAGS = -march=$(LMARCH) -O2 -c -mcmodel=medany
%.oqasm: %.ll
	$(LC) $(LFLAGS) $^ -o $@

QC = qcor-mlir-tool
QEMIT = llvm
QFLAGS = -gli2hli_V2 -hli2pulse -no-entrypoint -internal-func-name=main -emit=$(QEMIT)
#%.ll: $(QASM_DEMO_DIR)/%.qasm
#	$(QC) $^ $(QFLAGS) 2> $@

ROUTE_OPT = R3
%.ll: $(QASM_ROUT_DIR)/%.qasm
	$(QC) $^ $(QFLAGS) -topology=$(basename $^)_top.json -route=$(ROUTE_OPT) 2> $@

# Some targets have extra dependencies, or different -march= values.
vector_test: util/memcpy.s
vector_test: MARCH=rv64imafdcv

vector_t1: util/memset.s util/memcpy.s
vector_t1: MARCH=rv64imafdcv

qmemory_experiment: qec.h util/memset.s util/memcpy.s
qmemory_experiment: MARCH=rv64imafdcv

qmemory_experiment_scalar: qec.h util/scalar_mem_funcs.c

# Different topologies have different source files, but follow the same recipe.
TOPOLOGIES = qec_topology default_topology

$(TOPOLOGIES):
	python3 /yaqcs-arch/simulator/pulse_simulator/config_gen.py $^ /yaqcs-arch/simulator/pulse_simulator/pulse.json

qec_topology: qec_topology.json
default_topology: /yaqcs-arch/simulator/pulse_simulator/topology.json

# Make two files at once with qec_gen.py.
QEC_SIZE = 3
qec.h qec_topology.json &:
	python3 util/qec_gen.py $(QEC_SIZE)

# Shortcut to remake all QEC-related targets (useful when QEC_SIZE is changed).
qec: qec_topology qmemory_experiment qmemory_experiment_scalar

.PHONY: clean all $(TOPOLOGIES) qec
clean:
	@rm -f $(TARGETS) qec.h qec_topology.json
	@rm *.ll *.oqasm