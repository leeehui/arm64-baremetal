#include <platform.h>

OUTPUT_FORMAT("elf64-littleaarch64")
OUTPUT_ARCH(aarch64)
ENTRY(startup)

MEMORY {
    RAM(rwx): ORIGIN = RAM_BASE, LENGTH = RAM_SIZE
#define NOBITS RAM
}

SECTIONS {
   . = RAM_BASE;

   . = ALIGN(0x1000);
    __START__ = .;
    __RO_START__ = .;
    .text . : {
        __TEXT_START__ = .;
        *start.o(.text*)
        *(SORT_BY_ALIGNMENT(SORT(.text*)))
        *(.vectors)
        __TEXT_END__ = .;
    } >RAM

   . = ALIGN(0x1000);
    .rodata . : {
        __RODATA_START__ = .;
        *(SORT_BY_ALIGNMENT(.rodata*))
        __RODATA_END__ = .;
    } >RAM
    __RO_END__ = .;

   . = ALIGN(0x1000);
    __RW_START__ = .;
	.data . : {
		__DATA_START__ = .;	
		*(SORT_BY_ALIGNMENT(.data*))
		__DATA_END__ = .;	
    } >RAM

   . = ALIGN(0x1000);
	.rela.dyn : {
		__RELA_START__ = .;	
		*(.rela*)
		__RELA_END__ = .;
	} >RAM
    __RW_END__ = .;
    
   . = ALIGN(0x1000);
    __NOBITS_START__ = .;
	stacks (NOLOAD) : {	
		__STACKS_START__ = .;
		*(tzfw_normal_stacks)
		__STACKS_END__ = .;	
	} >NOBITS
    . = ALIGN(0x1000);
	.bss (NOLOAD) : {
		__BSS_START__ = .;
		*(SORT_BY_ALIGNMENT(.bss*))
		*(COMMON)
		__BSS_END__ = .;
	} >NOBITS
    __NOBITS_END__ = .;

    __END__ = .;

    /DISCARD/ : {
        *(.dynsym .dynstr .hash .gnu.hash)
    }
}
