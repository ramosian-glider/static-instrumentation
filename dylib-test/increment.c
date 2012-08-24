int glob[5] = {0, 0, 0, 0, 0};

#ifdef CALLBACK
extern
void callback(void *mem);
#endif

void inc_value(int index) {
#ifdef CALLBACK
  callback(&(glob[index]));
#endif
  glob[index]++;
}

int read_value(int index) {
  return glob[index];
}
