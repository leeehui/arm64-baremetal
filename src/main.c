#include <utils.h>
#include <malloc.h>
#include <heapblock.h>
 
extern char runtime_exceptions[0];
extern void *sync_sp_el0;

void main(void) {
    msr(sctlr_el3, ((1<<4)|(1<<5)|(1<<11)|(1<<16)|(1<<18)|(1<<22)|(1<<23)|(1<<28)|(1<<29))& (~((1<<25)|(1<<19)|(1<<1)|(1<<3)|(1ULL<<44))));
    printf("Hello world! runtime_exceptions: %lx\n", (u64)runtime_exceptions);
    printf("Hello world! sync_sp_el0: %lx\n", (u64)sync_sp_el0);
    printf("Running in EL%ld\n", (mrs(CurrentEL) >> 2) & 0x3);
    msr(vbar_el3, (u64)runtime_exceptions);
    sysop("isb sy");
    printf("Hello world! vbar_el3:0x%lx\n", mrs(vbar_el3));
    void *addr = malloc(0x100);
    printf("Hello world! addr: %p\n", addr);
    printf("Hello world! addr0: %x\n", read32(0x1000000000) );
    while(1);
}
