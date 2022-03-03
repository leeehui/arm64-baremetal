#include <asm_macros_common.S>

    .global startup
func startup
    bl plat_set_my_stack
    bl main
endfunc startup

