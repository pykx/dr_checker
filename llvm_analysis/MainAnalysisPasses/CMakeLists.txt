cmake_minimum_required(VERSION 3.1)

find_package(LLVM REQUIRED CONFIG)
add_definitions(${LLVM_DEFINITIONS})
include_directories(${LLVM_INCLUDE_DIRS})

link_directories(${LLVM_LIBRARY_DIRS})

# For gprof
SET(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -pg")
SET(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} -pg")
SET(CMAKE_SHARED_LINKER_FLAGS "${CMAKE_SHARED_LINKER_FLAGS} -pg")

add_subdirectory(Utils) # For utilities

add_subdirectory(RangeAnalysis) # For Range Analysis

add_subdirectory(Customizations) # General interface for customizations.

add_subdirectory(LinuxKernelCustomizations) # customizations for linux kernel.

add_subdirectory(SoundyAliasAnalysis) # Smart Alias Analysis

