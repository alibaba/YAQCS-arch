/* Attempt to express basic calibration tasks using OpenQASM3 + OpenPulse.

The Rabi experiments scans qubit response to a 2D scan of the frequency
and the length of the drive pulse. Upon a correct drive frequency, the
qubit oscillates with maximum amplitude with respect to the drive length.
Such an experiment can be used to simultaneously determine the qubit 
frequency and a rough PI pulse driving qubit from |0> to |1>.

Find qubit frequency by looking for Rabi oscillations. Instead of tuning the drive frequency we tune the z amplitude.
*/

OPENQASM 3;
defcalgrammar "openpulse";

input float z_start;
input float z_step;
input int z_num_steps;

input duration len_start;
input duration len_step;
input int len_num_steps;
input float x_amp;

input rabi_z_repeat;

// simultaneous drive line and flux line pulse
defcal xz_pulse(float z_amp, duration length) $0 {
    // flux_frame is supplied from some vendor-supplied 'cal' block
    play(flux_frame, constant(z_amp, length));
    // drive_frame is supplied from some vendor-supplied 'cal' block
    play(drive_frame, constant(x_amp, length));
}

for i in [1:z_num_steps]{
    z_amp = z_start + (i-1) * z_step;
    for j in [1:len_num_steps]{
        length = len_start + (j-1)*len_step;

        kernel_repeat(rabi_z_repeat){
            reset $0;
            xz_pulse(z_amp / 30, length * 25) $0;
            measure $0;
        }
    }
}


