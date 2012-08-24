#include <stdio.h>
void inc_value(int index);

extern
void callback() {
  printf("HI!\n");
}

int main() {
  inc_value(5);
  callback();
  return 0;
}
