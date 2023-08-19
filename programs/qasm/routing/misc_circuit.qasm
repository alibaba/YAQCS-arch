/*Test example for qubit routing feature. Miscellaneous quantum circuit with assortment of gates. Two qubit gates go between 0 and 1 and 0 and 2. Topology only has [0,1] and [1,2]. 
Tried to insert SWAP after the X gates on qubit 1 and 2 and it worked.
*/

OPENQASM 3.0;
qreg q[3];
int[32] c0;
int[32] c1;
int[32] c2;

trigrepeat(1000) {
    reset q;
    gli_x q[0];
    gli_s q[0];
    gli_z q[0];
    gli_x q[2];
    gli_cnot q[0],q[1];
    gli_x q[1];
    gli_cnot q[0],q[2];
    gli_x q[2];
    gli_z q[2];
    gli_h q[1];
    meas q[0];
    meas q[1];
    meas q[2];
}

c0 = fetchresult q[0];
c1 = fetchresult q[1];
c2 = fetchresult q[2];