#!/bin/bash

set -x

name="${1::-3}"

python3 py2cxx.py $1 | tee $name.cc

gcc $name.cc -std=c++17 -lstdc++ -o $name

./$name


