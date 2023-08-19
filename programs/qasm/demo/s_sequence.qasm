/* Sequence of S gates sandwiched by Hadamards. For 0 mod 4 we should get |0> and 2 mod 4 we should get |1>. */

OPENQASM 3;
include "stdgates.inc";

qubit q;
int[32] c;

trigrepeat(1000) {
    reset q;
    gli_h q;
    // 100 times s
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_h q;
    meas q;
}
c = fetchresult q;

trigrepeat(1000) {
    reset q;
    gli_h q;
    // 98 times s
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_s q;
    gli_h q;
    meas q;
}
c = fetchresult q;