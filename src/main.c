#include <utils.h>
#include <malloc.h>
#include <heapblock.h>
 
extern void *runtime_excetions;
void main(void) {
    printf("Hello world!\n");
    msr(vbar_el3, (u64)runtime_excetions);
    printf("Hello world!\n");
    void *addr = malloc(0x100);
    printf("Hello world! addr: %p\n", addr);
    while(1);
}
