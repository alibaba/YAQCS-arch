# YAQCS Project
Driven by the recognition of the increasingly pivotal role of quantum computing, the <strong>YAQCS (Yet Another Quantum Computing Suite)</strong> project endeavours to provide a foundational infrastructure. Our modest goal is to support the creation and continuous refinement of digital quantum computers. We strive to offer a platform that nurtures creativity and subtly contributes to the onward journey of quantum computing technology advancement.

## Yaqcs Architecture
As a keystone initiative within the YAQCS project, our inaugural module, titled the <em>yaqcs-arch</em> repository, houses an intricate array of specifications and implementations of the system. Currently, our proposed architecture is based on the <em>YAQCS-electronics</em> driver instructions described in [this document](https://arxiv.org/abs/2305.14304), which are sent at runtime from a RISC-V CPU to the YAQCS-electronics driver (a driver controlling the underlying YAQCS-electronics) through MMIO.

Current yaqcs-arch repository contains the following components:
* `programs/`, a collection of test programs written in C++, demonstrating the use of YAQCS-electronics driver instructions.
* `simulator/`, a [QEMU](https://www.qemu.org)-based simulator that emulates YAQCS-electronics driver instructions and interfaces with a backend simulator, for an end-to-end simulation of quantum computation.

Another salient component of the YAQCS project is the Yaqcs Electronics. It manifests our commitment to building a robust control and measurement system, aimed at addressing the complexities of large-scale system synchronization, low-latency execution, and noise mitigation. This system is centered around a real-time digital signal processing core, embedded within a Field Programmable Gate Array (FPGA). This design enables precise timing control, arbitrary waveform generation, qubit state discrimination, and the generation of real-time, qubit state-dependent trigger signals for efficient feedback mechanisms. For an in-depth understanding of the system, we direct you to our publication linked [here](https://doi.org/10.1063/5.0085467).

The Yaqcs Electronics is presently undergoing testing at the Quantum Laboratory, [DAMO Academy](https://damo.alibaba.com/). It seamlessly integrates a RISC-V softcore with our bespoke electronic control and measurement system. We're in the process of updating from the T-head [E906](https://img.102.alibaba.com/1626084219353/73250d17edd7f07517dc23392807c346.pdf) to T-head [C908](https://img.102.alibaba.com/1686197152629/cc9eb98f11e41a47bb298ead4915e0c6.pdf), aiming to optimize our system specifically for superconducting quantum processors.

We are diligently striving towards the launch of the YAQCS-electronics module, anticipated in early 2024.
## Installation

This project is based on [docker](https://www.docker.com/get-started). Use the command below to build the core of this project:
```bash
docker build . --target yaqcs_arch -t yaqcs-arch:latest
```

Please note that building the docker image for the first time is a resource-intensive operation **that may take many hours to finish and may need about 10GB of memory**. Please adjust the docker settings as necessary.

The automated tests can be done by running `python3 -m unittest` in the docker image build above:
```bash
docker run --rm yaqcs-arch:latest bash -c "source ~/.env/yaqcs/bin/activate && python3 -m unittest"
```

To manually test this project, run the docker image in interactive mode:
```bash
docker run -it --rm yaqcs-arch:latest
```

This will open an interactive docker shell. All shell commands in the "usage" sections below are supposed to be run in this shell.

## Simulator usage

In the interactive docker shell, run
```bash
# Activate the python venv
source ~/.env/yaqcs/bin/activate

# First change to the programs directory
cd ../programs/

# Run a program
./test.sh t1_demo

```

Note that the programs are build for the machine `smarth` on `qemu`. To rebuild them for `virt`, go to the `programs` folder and run
```bash
make clean
make MACHINE=virt
```

In addition to the console outputs, the values that would be output to the upper PC are also stored in the text file `pcie.txt` for further automated processing. See `tests/test.py` for an example on how to read this text file. For more advanced usage of this simulator, please refer to a more detailed tutorial in `tutorial.md`.

### Backends

Currently the simulator supports three different backends:
* [`qutip`](https://github.com/qutip/qutip) (default), a pulse-level simulator with a simple error model.
* [`qutip_qip`](https://github.com/qutip/qutip-qip), a gate-level simulator, currently with no error model.
* [`stim`](https://github.com/quantumlib/Stim), a more efficient gate-level simulator, but only for Clifford gates (and also with no error model currently).

To use a backend other than `qutip`, use the option `--backend=<BACKEND>` with `test.sh`:
```bash
# Note: Since there is no error model, all measurement results would be 1000
./test.sh -q stim t1_demo
```

### Topologies

The `qmemory_experiment` test program cannot be directly run, because it requires a different qubit topology than the rest of the test programs. In order to run `qmemory_experiment`:
```bash
# Change the qubit topology the backend simulator uses
make qec

./test.sh -q stim qmemory_experiment
```

The test program itself uses some constant macros which depend on the size of the QEC. In order to try a different QEC size, you need to rebuild both the qubit topology file and the test program, which can be done by:
```bash
# The "-B" option forces a rebuild
make -B qec QEC_SIZE=7

./test.sh -q stim qmemory_experiment
```

Afterwards, to run non-QEC test programs, you need to switch back to the default qubit topology:
```bash
make default_topology
```

See `simulator/programs/Makefile` for a full list of test programs.

## For developers

The `qmemory_experiment` test program includes the header file `qec.h`, which is generated by running `make qec` in the docker shell. If you need this file outside of the docker image for any reason, you can run:
```bash
# Note the ".h" extension
make qec.h
```
This will also generate `qec_topology.json`, but will not change the qubit topology used by the pulse simulator. Both files generated by `make qec.h` are in `.gitignore`.

## Contributing
Contributions, issues, and feature requests are warmly welcomed. Should you wish to contribute, please feel free to check our issues page.

## License
The primary project is licensed under the Apache License, Version 2.0. For more details, please refer to the [LICENSE](LICENSE) file. The software in `programs/` directory is optimized for a dedicated system built on yaqcs-electronics.

The simulator in `simulator/` directory, on the other hand, is covered under the [GPL 3.0 license](COPYING).
