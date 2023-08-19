/* Sequence of H gates. For even number we should get |0> and odd number we should get |+>. */

OPENQASM 3;
include "stdgates.inc";

qubit q;
int[32] c;

/* Apply twice */
trigrepeat(1000) {
    reset q;
    gli_h q;
    gli_h q;
    meas q;
}
c = fetchresult q;

/* Apply five times */
trigrepeat(1000) {
    reset q;
    gli_h q;
    gli_h q;
    gli_h q;
    gli_h q;
    gli_h q;
    meas q;
}
c = fetchresult q;