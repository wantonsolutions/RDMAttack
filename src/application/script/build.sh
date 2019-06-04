#!/bin/bash

mkdir -p build
cd build
rm -r *

cmake -DCMAKE_BUILD_TYPE=Release ../src
make

