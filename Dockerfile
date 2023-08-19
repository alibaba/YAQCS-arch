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


# Use 'docker build --target yaqcs_arch -t yaqcs_arch:latest .' to build the image of qcs simulator

FROM debian:bookworm as yaqcs_arch

SHELL ["/bin/bash", "-c"]

# Install required Debian packages.
RUN dpkg --add-architecture riscv64 && apt-get update \
 && apt-get install --yes --no-install-recommends \
      ca-certificates git autoconf automake autotools-dev curl python3 \
      libmpc-dev libmpfr-dev libgmp-dev \
      gawk \
      build-essential \
      cargo \
      device-tree-compiler \
      bison \
      flex \
      texinfo \
      gperf \
      libtool \
      patchutils \
      bc \
      procps \
      zlib1g-dev \
      libexpat-dev \
      rustc \
      python3-full \
      python3-pip \
      python3-venv \
      nano \
      gcc g++ gfortran  libcurl4-openssl-dev libssl-dev liblapack-dev libblas-dev ninja-build lsb-release \
      libglib2.0-dev libfdt-dev libpixman-1-dev zlib1g-dev \
 && rm -rf /var/lib/apt/lists/*

# Install RISC-V GNU toolchain.
# This happens before everything else since it's really slow...
RUN git clone https://github.com/riscv/riscv-gnu-toolchain \
&& cd riscv-gnu-toolchain/ \
&& export PATH=${PATH}:/opt/riscv/bin \
&& ./configure --prefix=/opt/riscv --enable-multilib --with-cmodel=medany \
&& make -j$(( $(nproc) + 1 ))\
&& cd ../ \
&& rm -rf riscv-gnu-toolchain

# Create virtual environment to meet the requirement of PEP668, which has been adopted in the base system, Debian Bookworm.
RUN mkdir -p ${HOME}/.env && python3 -m venv ${HOME}/.env/yaqcs

# Set the environment variable $PATH
# Please be aware that we use ~ instead of $HOME when setting the variable $PATH due to an unsolved issue of Docker
# https://github.com/moby/moby/issues/28971
ENV PATH "~/.env/yaqcs/bin:${PATH}:/opt/riscv/bin:/opt/qemu/bin"

# Install needed python packages.
#RUN mkdir -p $HOME/.env && python3 -m venv $HOME/.env/yaqcs \
RUN source $HOME/.env/yaqcs/bin/activate && python -m pip install numpy qutip qutip-qip stim cmake

# Install QEMU ISA simulator.
COPY ./simulator/qemu /yaqcs-arch/simulator/qemu
WORKDIR /yaqcs-arch/simulator/qemu
RUN mkdir build \
    && cd build \
    && ../configure --prefix=/opt/qemu --target-list="riscv32-softmmu riscv64-softmmu" --with-git-submodules=ignore  \
    && make -j$(( $(nproc) + 1 )) \
    && make install  \
    && cd ../ \
    && rm -rf qemu

# Generate the pulse configuration file.
COPY ./simulator/pulse_simulator /yaqcs-arch/simulator/pulse_simulator
COPY ./simulator/sim.py /yaqcs-arch/simulator/sim.py
COPY ./simulator/sim.json /yaqcs-arch/simulator/sim.json
WORKDIR /yaqcs-arch/simulator/pulse_simulator
RUN source $HOME/.env/yaqcs/bin/activate && python config_gen.py

# Compile example programs that use the YQE plugin.
COPY ./programs /yaqcs-arch/programs
WORKDIR /yaqcs-arch/programs
RUN source $HOME/.env/yaqcs/bin/activate && make

# Copy the tests into the container.
COPY ./tests /yaqcs-arch/tests
WORKDIR /yaqcs-arch/tests

CMD ["/bin/bash"]
