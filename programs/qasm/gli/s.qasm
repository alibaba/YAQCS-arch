/* Testing basic GLI gates in compilation toolchain.
Apply S followed by measurement of qubit
*/
OPENQASM 3;

qubit q;
int[32] c;

trigrepeat(1000) {
    reset q;
    gli_s q;
    meas q;
}
c = fetchresult q;