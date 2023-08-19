/* Attempt to express basic calibration tasks using OpenQASM3 + OpenPulse.

The Rabi experiments scans qubit response to a 2D scan of the frequency
and the length of the drive pulse. Upon a correct drive frequency, the
qubit oscillates with maximum amplitude with respect to the drive length.
Such an experiment can be used to simultaneously determine the qubit 
frequency and a rough PI pulse driving qubit from |0> to |1>.

Find qubit frequency by looking for Rabi oscillations. Amplitude is tuned instead of gate duration.
*/

OPENQASM 3;
defcalgrammar "openpulse";

input float freq_start;
input float freq_step;
input int freq_num_steps;

input float amp_start;
input float amp_step;
input int amp_num_steps;

input rabi_amp_repeat;

defcal x_pulse(float amp) $0 {
    // drive_frame is supplied from some vendor-supplied 'cal' block
    // x_pulse is the stored waveform to an x rotation and takes an amplitude as an argument
    play(drive_frame, x_pulse(amp));
}

cal {
    // we divide by 100 to replicate rabi_amp.cpp
    set_frequency(drive_frame, freq_start / 100);
}

for i in [1:freq_num_steps]{
    for j in [1:amp_num_steps]{
        amp = amp_start + (j-1)*amp_step;

        kernel_repeat(rabi_amp_repeat){
            reset $0;
            x_pulse(amp / 4) $0;
            measure $0;
        }

        cal {
            shift_frequency(drive_frame, freq_step / 100);
        }
    }
}


