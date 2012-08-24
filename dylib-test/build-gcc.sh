#!/bin/bash

gcc main.c -o main
gcc increment.c -dynamiclib -o increment.dylib

gcc increment.c -dynamiclib -DCALLBACK -undefined dynamic_lookup -o increment-cb.dylib
gcc increment.c -dynamiclib -UCALLBACK -undefined dynamic_lookup -o increment-nocb.dylib
