########################################################################################
# Adapted from memcpy.s
########################################################################################
    .text
    .balign 4
    .global memset
    # void *memset(void* dest, int val, size_t n)
    # a0=dest, a1=val, a2=n
    #
  memset:
      mv a3, a0 # Copy destination
      vsetvli t0, a2, e8, m8, ta, ma
      vxor.vv v0, v0, v0          # Zero out v0
      vor.vx v0, v0, a1           # Fill v0 with val
  loop:
      vsetvli t0, a2, e8, m8, ta, ma
      sub a2, a2, t0              # Decrement count
      vse8.v v0, (a3)             # Store bytes
      add a3, a3, t0              # Bump pointer
      bnez a2, loop               # Any more?
      ret                         # Return
