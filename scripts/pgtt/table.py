"""
Copyright (c) 2019 Ash Wilding. All rights reserved.

SPDX-License-Identifier: MIT
"""

# Standard Python deps
from dataclasses import dataclass
from typing import List
import logging

# Internal deps


class Table:
    """
    Class representing a translation table.
    """
    _allocated = []


    def __init__( self, level, mmu_conf, va_base=0 ):
        """
        Constructor.

        args
        ====

            level
                        level of translation

            va_base
                        base virtual address mapped by entry [0] in this table

        """
        self.pgt_conf = mmu_conf.pgt_conf
        self.mmu_conf = mmu_conf
        self.addr = self.pgt_conf.ttbr + len(Table._allocated) * self.pgt_conf.tg
        self.level = level
        self.chunk = self.pgt_conf.tg << ((3 - self.level) * self.mmu_conf.table_idx_bits)
        self.va_base = va_base
        self.entries = {}
        Table._allocated.append(self)


    def prepare_next( self, idx:int, va_base:int=None ) -> None:
        """
        Allocate next-level table at entry [idx] if it does not already point
        to a next-level table.

        Leave va_base=None to default to self.va_base + idx * self.chunk.
        """
        if not idx in self.entries:
            self.entries[idx] = Table(
                self.level + 1,
                self.mmu_conf,
                va_base if not va_base is None else (self.va_base + idx * self.chunk)
            )


    def map( self, region) -> None:
        """
        Map a region of memory in this translation table.
        """
        margin = " " * (self.level - self.mmu_conf.start_level + 1) * 8

        logging.debug(margin + f"mapping region {hex(region.va)} in level {self.level} table")
        assert(region.va >= self.va_base)
        assert(region.va + region.size <= self.va_base + self.mmu_conf.entries_per_table * self.chunk)

        """
        Calculate number of chunks required to map this region.
        A chunk is the area mapped by each individual entry in this table.
        start_idx is the first entry in this table mapping part of the region.
        """
        num_chunks = region.size // self.chunk
        entry_idx_shift = (3 - self.level) * self.mmu_conf.table_idx_bits + self.mmu_conf.block_offset_bits
        start_idx = (region.va >> entry_idx_shift) & self.mmu_conf.table_idx_mask

        end_va = region.va + region.size
        end_pa = region.pa + region.size

        """
        Check whether the region is "floating".
        If so, dispatch to next-level table and we're finished.

                    +--------------------+
                 // |                    |
            Chunk - |####################| <-- Floating region
                 \\ |                    |
                    +--------------------+
        """
        if num_chunks == 0:
            logging.debug(margin + f"floating region, dispatching to next-level table")
            self.prepare_next(start_idx)
            self.entries[start_idx].map(region)
            return

        """
        Check for any "underflow".
        If so, dispatch the underflow to next-level table and proceed.

                    +--------------------+
                 // |####################|
            Chunk - |####################|
                 \\ |####################|
                    +--------------------+
                 // |####################| <-- Underflow
            Chunk - |                    |
                 \\ |                    |
                    +--------------------+
        """
        underflow = region.va % self.chunk
        if underflow:
            logging.debug(margin + f"{underflow=}, dispatching to next-level table")
            delta = self.chunk - underflow
            self.prepare_next(start_idx)
            self.entries[start_idx].map(region.copy(size = delta))
            start_idx += 1
            region.va += delta
            region.pa += delta
            region.size -= delta

        """
        Check for any "overflow".
        If so, dispatch the overflow to next-level table and proceed.

                    +--------------------+
                 // |                    |
            Chunk - |                    |
                 \\ |####################| <-- Overflow
                    +--------------------+
                 // |####################|
            Chunk - |####################|
                 \\ |####################|
                    +--------------------+
        """
        overflow = end_va % self.chunk
        if overflow:
            logging.debug(margin + f"{overflow=}, dispatching to next-level table")
            final_idx = (end_va >> entry_idx_shift) & self.mmu_conf.table_idx_mask
            va_base = (end_va // self.chunk) * self.chunk
            pa_base = end_pa - (end_va - va_base)
            self.prepare_next(final_idx, va_base)
            self.entries[final_idx].map(region.copy(va=va_base, pa=pa_base, size=overflow))
            region.size -= (self.chunk - overflow)

        num_chunks = region.size // self.chunk
        """
        Handle any remaining complete chunks.
        """
        region.size = self.chunk
        can_split_level_min = (1 if self.pgt_conf.tg_str == "4K" else 2)
        can_split = ((self.level >= can_split_level_min) and self.level < 3) and (not self.pgt_conf.large_page)
        num_contiguous_blocks = 0
        for i in range(start_idx, start_idx + num_chunks):
            logging.debug(margin + f"mapping complete chunk at index {i}")
            va_base = self.va_base + i * self.chunk
            pa_base = region.pa + (i - start_idx) * self.chunk
            r = region.copy(va=va_base, pa=pa_base)
            if can_split:
                self.prepare_next(i)
                self.entries[i].map(r)
            else:
                self.entries[i] = r
            num_contiguous_blocks += 1
        if num_contiguous_blocks > 0:
            self.entries[start_idx].num_contig = num_contiguous_blocks


    def __str__( self ) -> str:
        """
        Recursively crawl this table to generate a pretty-printable string.
        """
        margin = " " * (self.level - self.mmu_conf.start_level + 1) * 8
        string = f"{margin}level {self.level} table @ {hex(self.addr)}\n"
        for k in sorted(list(self.entries.keys())):
            entry = self.entries[k]
            if type(entry) is Table:
                header = "{}[#{:>4}]".format(margin, k)
                nested_table = str(entry)
                hyphens = "-" * (len(nested_table.splitlines()[0]) - len(header))
                string += f"{header}" + hyphens + f"\\\n{nested_table}"
            else:
                string += "{}[#{:>4}] 0x{:>012x}-0x{:>012x}, 0x{:>012x}-0x{:>012x}, {}, {}\n".format(
                    margin,
                    k,
                    entry.va,
                    entry.va + entry.size - 1,
                    entry.pa,
                    entry.pa + entry.size - 1,
                    entry.mem_type,
                    entry.label
                )
        return string


    #@classmethod
    #def usage( cls ) -> str:
    #    """
    #    Generate memory allocation usage information for the user.
    #    """
    #    string  = f"This memory map requires a total of {len(cls._allocated)} translation tables.\n"
    #    string += f"Each table occupies {args.tg_str} of memory ({hex(args.tg)} bytes).\n"
    #    string += f"The buffer pointed to by {hex(args.ttb)} must therefore be {len(cls._allocated)}x {args.tg_str} = {hex(args.tg * len(cls._allocated))} bytes long."
    #    return string

    @classmethod
    def gen(cls, level, mmu_conf):
        root = Table(level, mmu_conf)
        [root.map(r) for r in mmu_conf.pgt_conf.regions]
        return root

