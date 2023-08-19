.PHONY: all clean
.PRECIOUS: %.ll

TARGETS = qasm_test/t1_demo qasm_test/x_sequence qasm_test/z_sequence qasm_test/h_sequence qasm_test/s_sequence qasm_test/t_sequence

CC = riscv64-unknown-elf-gcc
MARCH = rv64imafdc
CFLAGS = -L/build/qir-qrt/build -lqir-qrt -mno-relax -nostartfiles -static -mcmodel=medany -Wl,-T,../link.ld -march=$(MARCH)

all: $(TARGETS)

%: %.o ../start.S 
	$(CC) $^ $(CFLAGS) -o $@

LC = /opt/compiler/riscv-llvm/bin/clang
LMARCH = rv64gc
LFLAGS = -march=$(LMARCH) -O2 -c -mcmodel=medany
%.o: %.ll
	$(LC) $(LFLAGS) $^ -o $@

QC = qcor-mlir-tool
QEMIT = llvm
QFLAGS = -gli2hli_V2 -hli2pulse -no-entrypoint -internal-func-name=main -emit=$(QEMIT)
%.ll: %.qasm
	$(QC) $^ $(QFLAGS) 2> $@

clean: 
	rm *.ll