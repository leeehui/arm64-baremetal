#include <asm_macros_common.S>

    .global startup
    .global sync_sp_el0
    .global runtime_exceptions
func startup
    bl plat_set_my_stack
    bl main
endfunc startup

vector_base runtime_exceptions
	/* ---------------------------------------------------------------------
	 * Current EL with SP_EL0 : 0x0 - 0x200
	 * ---------------------------------------------------------------------
	 */
vector_entry        sync_sp_el0
    b .
end_vector_entry    sync_sp_el0

vector_entry        irq_sp_el0
    b .
end_vector_entry    irq_sp_el0

vector_entry        fiq_sp_el0
    b .
end_vector_entry    fiq_sp_el0

vector_entry        serror_sp_el0
    b .
end_vector_entry    serror_sp_el0

	/* ---------------------------------------------------------------------
	 * Current EL with SP_ELx : 0x200 - 0x400
	 * ---------------------------------------------------------------------
	 */
vector_entry        sync_sp_elx
    b sync_spx
end_vector_entry    sync_sp_elx

vector_entry        irq_sp_elx
    b irq_spx
end_vector_entry    irq_sp_elx

vector_entry        fiq_sp_elx
    b fiq_spx
end_vector_entry    fiq_sp_elx

vector_entry        serror_sp_elx
    b serror_spx
end_vector_entry    serror_sp_elx

	/* ---------------------------------------------------------------------
	 * Lower EL using AArch64 : 0x400 - 0x600
	 * ---------------------------------------------------------------------
	 */
vector_entry        sync_aarch64
    b sync_spx
end_vector_entry    sync_aarch64

vector_entry        irq_aarch64
    b irq_spx
end_vector_entry    irq_aarch64

vector_entry        fiq_aarch64
    b fiq_spx
end_vector_entry    fiq_aarch64

vector_entry        serror_aarch64
    b serror_spx
end_vector_entry    serror_aarch64

	/* ---------------------------------------------------------------------
	 * Lower EL using AArch32 : 0x600 - 0x800
	 * ---------------------------------------------------------------------
	 */
vector_entry        sync_aarch32
    b .
end_vector_entry    sync_aarch32

vector_entry        irq_aarch32
    b .
end_vector_entry    irq_aarch32

vector_entry        fiq_aarch32
    b .
end_vector_entry    fiq_aarch32

vector_entry        serror_aarch32
    b .
end_vector_entry    serror_aarch32

