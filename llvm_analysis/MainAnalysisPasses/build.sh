#!/bin/bash
LLVM_DIR=$LLVM_ROOT/../cmake
echo "[*] Trying to Run Cmake"
mkdir build_dir
cd build_dir
cmake -DCMAKE_CXX_FLAGS=-pg -DCMAKE_EXE_LINKER_FLAGS=-pg -DCMAKE_SHARED_LINKER_FLAGS=-pg ..
echo "[*] Trying to make"
make -j8
