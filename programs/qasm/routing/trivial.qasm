/* Test example for qubit routing feature. Trivial example with two qubits and one single-qubit gate on each. Tried to insert a swap after the two single-qubit gates and it worked.
*/

OPENQASM 3;

qreg q[2];
int[32] c0;
int[32] c1;

trigrepeat(1000){
    reset q;
    gli_x q[0];
    gli_z q[1];
    gli_cnot q[0], q[1];
    meas q[0];
    meas q[1];
}

c0 = fetchresult q[0];
c1 = fetchresult q[1];