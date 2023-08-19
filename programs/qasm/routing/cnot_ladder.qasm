/*Test example for qubit routing feature. A ladder of CNOTs going from qubit 0 to qubit 1 and from qubit 1 to qubit 2. However, qubit 1 and qubit 2 are not connected. 
I inserted a SWAP between qubit 0 and qubit 1 after the first CNOT and it worked.
*/

OPENQASM 3;

qreg q[3];
int[32] c0;
int[32] c1;
int[32] c2;

trigrepeat(1000){
    reset q;
    gli_cnot q[0],q[1];
    gli_cnot q[1],q[2];
    meas q[0];
    meas q[1];
    meas q[2];
}

c0 = fetchresult q[0];
c1 = fetchresult q[1];
c2 = fetchresult q[2];