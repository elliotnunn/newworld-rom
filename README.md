The NewWorld ROM
================

This repo is part of the *CDG5* project. It builds version 9.6.1 of the *parcels*-based Mac OS ROM file, starting from a 4 MB Power Mac ROM (`rom`) and other PEF binaries (`pef/`). Use https://github.com/elliotnunn/powermac-rom to build your own ROM. A few bytes are different from the original file because (I think) the original Apple build tool failed to zero-initialize a buffer. The build result does not contain the *System Enabler* found in later Mac OS ROM versions.

Building
--------

A basic Unix toolchain is required.

	make tbxi.hqx

Instead of using the included 4 MB ROM, you can uncomment some code in the makefile to trigger a build from https://github.com/elliotnunn/powermac-rom

The makefile also helps you to test your build:

	make test-qemu
	make test-fw

Patching
--------

Some useful patches to the Open Firmware boot script can be enabled at the top of `bootmake.py`.

The parcel build script will preferentially load files with `.patch` appended to the name. This is helpful when using https://github.com/elliotnunn/patchpef to edit the PowerPC binaries under `pef/`. For example, to prevent the Power Manager from crashing while trying to load a PMU plugin on the Mac mini:

	patchpef.py pef/nlib/NativePowerMgrLib{,.patch} Initialize+0x94 " li r3,0"
