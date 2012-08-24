int ret1() {
  return 1;
}

int ret2() {
  return 1;
}

int ret3(int a, int b) {
  return a + b + ret2();
}

int fact(int v) {
  if (v<2) return 1;
  return v * fact(v-1);
}

int sum5(int a1, int a2, int a3, int a4, int a5) {
  int f = a1 * a4;
  int v = fact(ret3(ret1(), ret2()));
  return a1 * a2+ a3 * a4 + a5 * a1 + f + v; 
}
