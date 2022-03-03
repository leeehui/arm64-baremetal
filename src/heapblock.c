/* SPDX-License-Identifier: MIT */

#include "assert.h"
#include "heapblock.h"
#include "platform.h"
#include "types.h"
#include "utils.h"

/*
 * This is a non-freeing allocator, used as a backend for malloc and for uncompressing data.
 *
 * Allocating 0 bytes is allowed, and guarantees "infinite" (until the end of RAM) space is
 * available at the returned pointer as long as no other malloc/heapblock calls occur, which is
 * useful as a buffer for unknown-length uncompressed data. A subsequent call with a size will then
 * actually reserve the block.
 */

static char heap_pool[PLATFORM_HEAP_SIZE] __attribute__((section("heap")));
static void *heap_base = heap_pool;

void heapblock_init(void)
{

    heapblock_alloc(0); // align base

    printf("Heap base: %p\n", heap_base);
}

void *heapblock_alloc(size_t size)
{
    return heapblock_alloc_aligned(size, 64);
}

void *heapblock_alloc_aligned(size_t size, size_t align)
{
    assert((align & (align - 1)) == 0);
    assert((uintptr_t)heap_base < ((uintptr_t)heap_pool + PLATFORM_HEAP_SIZE));

    uintptr_t block = (((uintptr_t)heap_base) + align - 1) & ~(align - 1);
    heap_base = (void *)(block + size);

    return (void *)block;
}
