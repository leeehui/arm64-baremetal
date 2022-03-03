#include <utils.h>
#include <malloc.h>
#include <heapblock.h>
 
void main(void) {
    //void *addr = malloc(0x100);
    //printf("Hello world! addr: %p\n", addr);
    heapblock_init();
    printf("Hello world!\n");
}
