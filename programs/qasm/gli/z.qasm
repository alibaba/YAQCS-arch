/* Testing basic GLI gates in compilation toolchain.
Apply Z followed by measurement of qubit
*/
OPENQASM 3;

qubit q;
int[32] c;

trigrepeat(1000) {
    reset q;
    gli_z q;
    meas q;
}
c = fetchresult q;