#include <dlfcn.h>
#include <stdio.h>

typedef void(*vfunc_t)(int);
typedef int(*ifunc_t)(int);

int main() {
  void *handle = dlopen("increment.dylib", RTLD_NOW);
  if (!handle) {
    printf("%s\n", dlerror());
    return 1;
  }
  void *inc_v = dlsym(handle, "inc_value");
  void *read_v = dlsym(handle, "read_value");
  
  (*(vfunc_t)inc_v)(0);
  (*(vfunc_t)inc_v)(5);
  printf("glob[0]: %d, glob[1]: %d, glob[5]: %d\n", (*(ifunc_t)read_v)(0), (*(ifunc_t)read_v)(1), (*(ifunc_t)read_v)(5));
  return 0;
}
