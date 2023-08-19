#include <stddef.h>

void memset(volatile void* dest, int val, size_t n) {
  while (n--) *((volatile char*)dest++) = val;
}

void memcpy(volatile void* dest, volatile void* src, size_t n) {
  while (n--) *((volatile char*)dest++) = *((volatile char*)src++);
}
