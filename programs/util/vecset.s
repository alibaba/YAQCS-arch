    .text
    .balign 4
    .global vecset
    # void vecset(int* dest, int val, size_t n, size_t stride)
    # a0=dest, a1=val, a2=n, a3=stride
    #
  vecset:
      vsetvli t0, a2, e32, m8, ta, ma
      vxor.vv v0, v0, v0          # Zero out v0
      vor.vx v0, v0, a1           # Fill v0 with val
  loop:
      vsetvli t0, a2, e32, m8, ta, ma
      sub a2, a2, t0              # Decrement count
      vsse32.v v0, (a0), a3       # Store integers
      mul t0, t0, a3
      add a0, a0, t0              # Bump pointer
      bnez a2, loop               # Any more?
      ret                         # Return
