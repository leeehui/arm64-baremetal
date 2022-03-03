/*
 * Copyright (c) 2014-2020, ARM Limited and Contributors. All rights reserved.
 *
 * SPDX-License-Identifier: BSD-3-Clause
 */

#include <platform.h>
#include <asm_macros_common.S>


	.local	platform_normal_stacks
	.weak	plat_get_my_stack
	.weak	plat_set_my_stack

    

func plat_my_core_pos
	mrs	x0, mpidr_el1
	and	x0, x0, #0xFF
	ret
endfunc plat_my_core_pos

    /*
	 * This macro calculates the base address of the current CPU's MP stack
	 * using the plat_my_core_pos() index, the name of the stack storage
	 * and the size of each stack
	 * Out: X0 = physical address of stack base
	 * Clobber: X30, X1, X2
	 */
	.macro get_my_mp_stack _name, _size
	bl	plat_my_core_pos
	adrp	x2, (\_name + \_size)
	add	x2, x2, :lo12:(\_name + \_size)
	mov x1, #\_size
	madd x0, x0, x1, x2
	.endm


	/* ---------------------------------------------------------------------
	 * When the compatibility layer is disabled, the platform APIs
	 * plat_get_my_stack() and plat_set_my_stack() are supported by the
	 * platform and the previous APIs platform_get_stack() and
	 * platform_set_stack() are defined in terms of new APIs making use of
	 * the fact that they are only ever invoked for the current CPU.  This
	 * is to enable components of Trusted Firmware like SPDs using the old
	 * platform APIs to continue to work.
	 * --------------------------------------------------------------------
	 */

	/* -----------------------------------------------------
	 * uintptr_t plat_get_my_stack ()
	 *
	 * For the current CPU, this function returns the stack
	 * pointer for a stack allocated in device memory.
	 * -----------------------------------------------------
	 */
func plat_get_my_stack
	mov	x10, x30
	get_my_mp_stack platform_normal_stacks, PLATFORM_STACK_SIZE
	ret	x10
endfunc plat_get_my_stack

	/* -----------------------------------------------------
	 * void plat_set_my_stack ()
	 *
	 * For the current CPU, this function sets the stack
	 * pointer to a stack allocated in normal memory.
	 * -----------------------------------------------------
	 */
func plat_set_my_stack
	mov	x9, x30
	bl 	plat_get_my_stack
	mov	sp, x0
	ret	x9
endfunc plat_set_my_stack

	/* -----------------------------------------------------
	 * Per-CPU stacks in normal memory. Each CPU gets a
	 * stack of PLATFORM_STACK_SIZE bytes.
	 * -----------------------------------------------------
	 */
declare_stack platform_normal_stacks, tzfw_normal_stacks, \
		PLATFORM_STACK_SIZE, PLATFORM_CORE_COUNT
