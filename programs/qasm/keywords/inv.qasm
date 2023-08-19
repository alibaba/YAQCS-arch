/* Test all keywords of OpenQASM 3 Live Spec https://openqasm.com/grammar/index.html#
*/

OPENQASM 3;

include "stdgates.inc";

gate sdg r { inv @ s r; }