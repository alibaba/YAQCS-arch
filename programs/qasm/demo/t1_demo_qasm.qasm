/* Measure T1 relaxation time of a qubit by observing exponential decay of the
survival rate after excitation of the qubit. A qubit is measured after a certain
amount of time after being applied an X gate. The decay rate of the observed
frequency of measuring 1 with respect to the waiting time is called the T1 relaxation
time.
*/
OPENQASM 3;
//include "stdgates.inc";


qubit q0;
int[32] c0;

for t1_delay in [0: 50: 500] {
    trigrepeat(1000) {
        // start of a basic block
        reset q0;
        // excite qubits
        gli_x q0;
        // wait for a fixed time indicated by loop counter
        delay[t1_delay];
        //delay[100];
        meas q0;
    }
    // read out qubit states
    c0 = fetchresult q0;
}

