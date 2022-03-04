/* SPDX-License-Identifier: MIT */

#include "exception.h"
#include "uart.h"
#include "utils.h"

static char *m_table[0x10] = {
    [0x00] = "EL0t", //
    [0x04] = "EL1t", //
    [0x05] = "EL1h", //
    [0x08] = "EL2t", //
    [0x09] = "EL2h", //
};

static char *ec_table[0x40] = {
    [0x00] = "unknown",
    [0x01] = "wf*",
    [0x03] = "c15 mcr/mrc",
    [0x04] = "c15 mcrr/mrrc",
    [0x05] = "c14 mcr/mrc",
    [0x06] = "ldc/stc",
    [0x07] = "FP off",
    [0x08] = "VMRS access",
    [0x09] = "PAC off",
    [0x0a] = "ld/st64b",
    [0x0c] = "c14 mrrc",
    [0x0d] = "branch target",
    [0x0e] = "illegal state",
    [0x11] = "svc in a32",
    [0x12] = "hvc in a32",
    [0x13] = "smc in a32",
    [0x15] = "svc in a64",
    [0x16] = "hvc in a64",
    [0x17] = "smc in a64",
    [0x18] = "other mcr/mrc/sys",
    [0x19] = "SVE off",
    [0x1a] = "eret",
    [0x1c] = "PAC failure",
    [0x20] = "instruction abort (lower)",
    [0x21] = "instruction abort (current)",
    [0x22] = "pc misaligned",
    [0x24] = "data abort (lower)",
    [0x25] = "data abort (current)",
    [0x26] = "sp misaligned",
    [0x28] = "FP exception (a32)",
    [0x2c] = "FP exception (a64)",
    [0x2f] = "SError",
    [0x30] = "BP (lower)",
    [0x31] = "BP (current)",
    [0x32] = "step (lower)",
    [0x33] = "step (current)",
    [0x34] = "watchpoint (lower)",
    [0x35] = "watchpoint (current)",
    [0x38] = "bkpt (a32)",
    [0x3a] = "vector catch (a32)",
    [0x3c] = "brk (a64)",
};

static const char *get_exception_source(void)
{
    u64 spsr = mrs(SPSR_EL3);
    const char *m_desc = NULL;

    m_desc = m_table[spsr & 0xf];

    if (!m_desc)
        m_desc = "?";

    return m_desc;
}

static const unsigned int get_exception_level(void)
{
    u64 lvl = mrs(CurrentEL);

    return (lvl >> 2) & 0x3;
}

void exception_initialize(void)
{
    //msr(VBAR_EL1, _vectors_start);

    //if (is_primary_core())
    //    msr(DAIF, 0 << 6); // Enable SError, IRQ and FIQ

    //if (in_el2()) {
    //    // Set up a sane HCR_EL2
    //    msr(HCR_EL2, (BIT(41) | // API
    //                  BIT(40) | // APK
    //                  BIT(37) | // TEA
    //                  BIT(34) | // E2H
    //                  BIT(31) | // RW
    //                  BIT(27) /*| // TGE
    //                  BIT(5) |  // AMO
    //                  BIT(4) |  // IMO
    //                  BIT(3)*/);  // FMO
    //    );
    //    // Set up exception forwarding from EL1
    //    msr(VBAR_EL12, _el1_vectors_start);
    //    sysop("isb");
    //}
}

void exception_shutdown(void)
{
    msr(DAIF, 7 << 6); // Disable SError, IRQ and FIQ
}

void print_regs(u64 *regs)
{
    u64 sp = ((u64)(regs)) + 256;


    printf("Exception taken from %s\n", get_exception_source());
    printf("Running in EL%d\n", get_exception_level());
    printf("MPIDR: 0x%lx\n", mrs(MPIDR_EL1));
    printf("Registers: (@%p)\n", regs);
    printf("  x0-x3: %016lx %016lx %016lx %016lx\n", regs[0], regs[1], regs[2], regs[3]);
    printf("  x4-x7: %016lx %016lx %016lx %016lx\n", regs[4], regs[5], regs[6], regs[7]);
    printf(" x8-x11: %016lx %016lx %016lx %016lx\n", regs[8], regs[9], regs[10], regs[11]);
    printf("x12-x15: %016lx %016lx %016lx %016lx\n", regs[12], regs[13], regs[14], regs[15]);
    printf("x16-x19: %016lx %016lx %016lx %016lx\n", regs[16], regs[17], regs[18], regs[19]);
    printf("x20-x23: %016lx %016lx %016lx %016lx\n", regs[20], regs[21], regs[22], regs[23]);
    printf("x24-x27: %016lx %016lx %016lx %016lx\n", regs[24], regs[25], regs[26], regs[27]);
    printf("x28-x30: %016lx %016lx %016lx\n", regs[28], regs[29], regs[30]);

    u64 elr = mrs(ELR_EL3);
    u64 esr = mrs(ESR_EL3);
    u64 spsr = mrs(SPSR_EL3);
    u64 far = mrs(FAR_EL3);

    printf("SP:       0x%lx\n", sp);
    printf("ELR_EL3:  0x%lx\n", elr);
    printf("SPSR_EL3: 0x%lx\n", spsr);
    printf("FAR_EL3:  0x%lx\n", far);
    const char *ec_desc = ec_table[(esr >> 26) & 0x3f];
    printf("ESR_EL3:  0x%lx (%s)\n", esr, ec_desc ? ec_desc : "?");
}

void exc_sync(u64 *regs)
{
    printf("Exception: SYNC\n");
    print_regs(regs);
    while(1);
}

void exc_irq(u64 *regs)
{
    printf("Exception: IRQ\n");
    print_regs(regs);
    while(1);
}

void exc_fiq(u64 *regs)
{
    printf("Exception: FIQ\n");
    print_regs(regs);
    while(1);
}

void exc_serr(u64 *regs)
{
    printf("Exception: SError\n");
    print_regs(regs);
    while(1);
}
