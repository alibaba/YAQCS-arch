/* Testing basic GLI gates in compilation toolchain.
Apply CNOT followed by measurement of both qubits
*/

OPENQASM 3;

qreg q[2];
int[32] c0;
int[32] c1;

trigrepeat(1000) {
    reset q;
    gli_cnot q[0], q[1];
    meas q[0];
    meas q[1];
}
c0 = fetchresult q[0];
c1 = fetchresult q[1];