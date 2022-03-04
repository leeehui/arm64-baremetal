/* SPDX-License-Identifier: MIT */

#include "exception.h"
#include <asm_macros_common.S>

.globl exc_sync
.globl exc_irq
.globl exc_fiq
.globl exc_serr

.global sync_spx
.global irq_spx
.global fiq_spx
.global serror_spx

func sync_spx 
    sub sp, sp, #(SIZEOF_EXC_INFO - 32 * 8)
    str x30, [sp, #-16]!
    bl _exc_entry
    bl exc_sync

    b _exc_return
endfunc sync_spx

func irq_spx
    sub sp, sp, #(SIZEOF_EXC_INFO - 32 * 8)
    str x30, [sp, #-16]!
    bl _exc_entry
    bl exc_irq

    b _exc_return
endfunc irq_spx

func fiq_spx
    sub sp, sp, #(SIZEOF_EXC_INFO - 32 * 8)
    str x30, [sp, #-16]!
    bl _exc_entry
    bl exc_fiq

    b _exc_return
endfunc fiq_spx

func serror_spx
    sub sp, sp, #(SIZEOF_EXC_INFO - 32 * 8)
    str x30, [sp, #-16]!
    bl _exc_entry
    bl exc_serr

    b _exc_return
endfunc serror_spx

func _exc_entry
    stp x28, x29, [sp, #-16]!
    stp x26, x27, [sp, #-16]!
    stp x24, x25, [sp, #-16]!
    stp x22, x23, [sp, #-16]!
    stp x20, x21, [sp, #-16]!
    stp x18, x19, [sp, #-16]!
    stp x16, x17, [sp, #-16]!
    stp x14, x15, [sp, #-16]!
    stp x12, x13, [sp, #-16]!
    stp x10, x11, [sp, #-16]!
    stp x8, x9, [sp, #-16]!
    stp x6, x7, [sp, #-16]!
    stp x4, x5, [sp, #-16]!
    stp x2, x3, [sp, #-16]!
    stp x0, x1, [sp, #-16]!

    mov x0, sp
    ret
endfunc _exc_entry

func _exc_return
    ldp x0, x1, [sp], #16
    ldp x2, x3, [sp], #16
    ldp x4, x5, [sp], #16
    ldp x6, x7, [sp], #16
    ldp x8, x9, [sp], #16
    ldp x10, x11, [sp], #16
    ldp x12, x13, [sp], #16
    ldp x14, x15, [sp], #16
    ldp x16, x17, [sp], #16
    ldr x18, [sp], #8
    add sp, sp, #88
    ldr x30, [sp], #16

    add sp, sp, #(SIZEOF_EXC_INFO - 32 * 8)

    eret
endfunc _exc_return

