#!/bin/bash

for to_test in instruction.py table_generator.py disassembler.py
do
python $to_test || exit 1
done
