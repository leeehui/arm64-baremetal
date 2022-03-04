/* SPDX-License-Identifier: MIT */

#ifndef __EXCEPTION_H__
#define __EXCEPTION_H__

#define SIZEOF_EXC_INFO (64 * 8)

#ifndef __ASSEMBLER__

#include <assert.h>
#include <stdint.h>

#include "types.h"

struct exc_info {
    u64 regs[32];
    u64 spsr;
    u64 elr;
    u64 esr;
    u64 far;
    u64 afsr1;
    u64 sp[3];
    u64 cpu_id;
    u64 mpidr;
    u64 elr_phys;
    u64 far_phys;
    u64 sp_phys;
    void *extra;
};
static_assert(sizeof(struct exc_info) <= SIZEOF_EXC_INFO, "Please increase SIZEOF_EXC_INFO");
static_assert((sizeof(struct exc_info) & 15) == 0, "SIZEOF_EXC_INFO must be a multiple of 16");

void exception_initialize(void);
void exception_shutdown(void);

void print_regs(u64 *regs);

#endif

#endif
