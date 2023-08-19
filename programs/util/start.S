# A wrapper for MMIO plugin test programs.
.section .text.init
.global _start
_start:

# Set mstatus[14:13] (floating-point context status) and mstatus[10:9]
# (vector context status) to 1 (Initial).
li t0, 0x00002200
csrs sstatus, t0

# Set the stack pointer and the global pointer.
la sp, _stack_top
.option push
.option norelax
1:auipc gp, %pcrel_hi(__global_pointer$)
  addi  gp, gp, %pcrel_lo(1b)
.option pop


# Call the main function defined in the test program.
call main

# Terminate the program via smarth MMIO
li s1, 0x10002000
sb zero, 0(s1)

# An infinite loop before the program is terminated
loop: 
j loop
