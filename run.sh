#!/bin/sh

# use CTRL-a x  force exit emulator
qemu-system-aarch64 -machine virt,secure=on -cpu cortex-a57 -nographic  -kernel build/test.elf
