/* Attempt to express basic calibration tasks using OpenQASM3 + OpenPulse.

The Rabi experiments scans qubit response to a 2D scan of the frequency
and the length of the drive pulse. Upon a correct drive frequency, the
qubit oscillates with maximum amplitude with respect to the drive length.
Such an experiment can be used to simultaneously determine the qubit 
frequency and a rough PI pulse driving qubit from |0> to |1>.

Find qubit frequency by looking for Rabi oscillations
*/

OPENQASM 3;
defcalgrammar "openpulse";

input float freq_start;
input float freq_step;
input int freq_num_steps;

input duration len_start;
input duration len_step;
input int len_num_steps;
input float amp;

input rabi_repeat;

defcal x_pulse(duration length) $0 {
    // drive_frame is supplied from some vendor-supplied 'cal' block
    play(drive_frame, constant(amp, length));
}

cal {
    // we divide by 100 to replicate rabi.cpp
    set_frequency(drive_frame, freq_start / 100);
}

for i in [1:freq_num_steps]{
    for j in [1:len_num_steps]{
        length = len_start + (j-1)*len_step;

        kernel_repeat(rabi_repeat){
            reset $0;
            x_pulse(length * 25) $0;
            measure $0;
        }

        cal {
            shift_frequency(drive_frame, freq_step / 100);
        }
    }
}


