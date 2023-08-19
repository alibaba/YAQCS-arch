/* Attempt to express basic calibration tasks using OpenQASM3 + OpenPulse.

Measure T1 relaxation time of a qubit by observing exponential decay of the
survival rate after excitation of the qubit. A qubit is measured after a certain
amount of time after being applied an X gate. The decay rate of the observed
frequency of measuring 1 with respect to the waiting time is called the T1 relaxation
time.
*/
OPENQASM 3;
//include "stdgates.inc";

// These parameters will be provided at run-time
input duration t1_delay_step;
input int t1_delay_num_steps;
input int t1_repeat;

qubit q0;
bit c0;

for int i in [1:t1_delay_num_steps] {
    duration t1_delay = (i-1)* t1_delay_step;
    kernel_repeat(t1_repeat) {
        // start of a basic block
        reset q0;
        // excite qubits
        x q0;
        // wait for a fixed time indicated by loop counter
        delay[t1_delay];
    }
    // read out qubit states
    c0 = measure q0;
}
