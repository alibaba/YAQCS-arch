/* Attempt to express basic calibration tasks using OpenQASM3 + OpenPulse.

Measure T2 relaxation time of a qubit through a T2 Ramsey experiment.
A qubit is measured after an X/2 gate followed by an X/2 gate interleaved
by a certain delay time. Depolarization of the qubit within the delay time
makes the qubit fail to return to the original 0 state at the end, resulting
in an observable change of final survival rate with respect to the delay time.
*/
OPENQASM 3;
defcalgrammar "openpulse";

input float fringe;

input duration t2_delay_step;
input int t2_delay_num_steps;

input float qubit_freq;

input int t2_repeat;

cal {
    extern port d0;
    frame frd0 = newframe(d0, qubit_freq, 0.);
}

defcal x90 $0 {
    // x90_pulse is the stored waveform calibrated for the x90 gate
    play(frd0, x90_pulse); 
}

defcal single_qubit_delay(duration length) $0 {
    delay[length] frd0;
}

for i in [1:t2_delay_num_steps] {
    t2_delay = (i-1) * t2_delay_step;
    kernel_repeat(t2_repeat) {
        reset $0;
        x90 $0;
        single_qubit_delay(t2_delay) $0;
        cal {
            // we divide by 1000 to replicate t2.cpp
            shift_phase(frd0, 2 * pi * (fringe / 1000) * t2_delay); 
        }
        x90 $0;
        measure $0;
    }
}