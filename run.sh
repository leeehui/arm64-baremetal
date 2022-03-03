#!/bin/sh

qemu-system-aarch64 -M virt -cpu cortex-a57 -nographic  -kernel build/test.elf
