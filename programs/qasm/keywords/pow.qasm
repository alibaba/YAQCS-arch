/* Test all keywords of OpenQASM 3 Live Spec https://openqasm.com/grammar/index.html#
*/

OPENQASM 3;

include "stdgates.inc";

gate x90 r { pow(1/2) @ x r; }