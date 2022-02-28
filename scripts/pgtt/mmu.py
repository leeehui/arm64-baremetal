"""
Copyright (c) 2019 Ash Wilding. All rights reserved.

SPDX-License-Identifier: MIT
"""

# Standard Python deps
import math
from dataclasses import dataclass
from typing import List
from enum import IntEnum

# Internal deps
from .register import Register

class MairEncode(IntEnum):
    DEVICE_nGnRnE   = 0x00
    DEVICE_nGnRE    = 0x04
    DEVICE_GRE      = 0x0c
    NORMAL_NC       = 0x44
    NORMAL_WT       = 0xbb
    NORMAL          = 0xff

class MemType(IntEnum):
    DEVICE_nGnRnE   = 0
    DEVICE_nGnRE    = 1
    DEVICE_GRE      = 2
    NORMAL_NC       = 3
    NORMAL_WT       = 4
    NORMAL          = 5

@dataclass
class MemAttr:
    ap:int
    xn:int
    ns:int

@dataclass
class Region:
    """
    Class representing a single region in the memory map.
    """

    lineno: int                    # line number in source memory map file
    label: str                     # name/label e.g. DRAM, GIC, UART, ...
    va: int                      # base address
    pa: int                      # base address
    size: int                    # length in bytes
    mem_type: MemType         # True for Device-nGnRnE, False for Normal WB RAWA
    mem_attr: MemAttr
    is_page = True             # whether this region is page or not
    num_contig = 1


    def copy( self, **kwargs ):
        """
        Create a duplicate of this Region.
        Use kwargs to override this region's corresponding properties.
        """
        region = Region(self.lineno, self.label, self.va, self.pa, self.size, self.mem_type, self.mem_attr)
        for kw,arg in kwargs.items():
            region.__dict__[kw] = arg
        return region


    def __str__( self ):
        """
        Override default __str__ to print addr and length in hex format.
        """
        return "Region(lineno={}, label='{}', va={}, pa={}, size={}, mem_type={}".format(
            self.lineno, self.label, hex(self.va), hex(self.pa), hex(self.size), self.mem_type
        )


class MmuConfig:

    def __init__(self, pgt_conf):

        self.pgt_conf = pgt_conf
        """
        Tables occupy one granule and each entry is a 64-bit descriptor.
        """
        self.entries_per_table = pgt_conf.tg // 8
        #log.debug(f"{entries_per_table=}")


        """
        Number of bits required to index each byte in a granule sized page.
        """
        self.block_offset_bits = int(math.log(pgt_conf.tg, 2))
        #log.debug(f"{block_offset_bits=}")


        """
        Number of bits required to index each entry in a complete table.
        """
        self.table_idx_bits = int(math.log(self.entries_per_table, 2))
        self.table_idx_mask = (1 << self.table_idx_bits) - 1
        #log.debug(f"{table_idx_bits=}")


        """
        Starting level of translation.
        """
        self.start_level = 3 - (pgt_conf.tsz - self.block_offset_bits) // self.table_idx_bits
        if (pgt_conf.tsz - self.block_offset_bits) % self.table_idx_bits == 0:
            self.start_level += 1
            #log.debug(f"start_level corrected as {args.tsz=} exactly fits in first table")
        #log.debug(f"{start_level=}")

        self.tcr = self._tcr()
        self.sctlr = self._sctlr()

        self.mem_types = {i.name: i.value for i in MemType}
        self.mair_encodes = {i.name: i.value for i in MairEncode}

        self.mair = self._mair()
        self.ttbr = pgt_conf.ttbr

    def _mair(self):
        mair = 0
        for k in self.mair_encodes.keys():
            mair |= (self.mair_encodes[k] << (self.mem_types[k] * 8))
        return hex(mair)

    def _tcr(self) -> str:
        """
        Generate required value for TCR_ELn.
        """
        reg = Register(f"tcr_el{self.pgt_conf.el}")

        """
        Configurable bitfields present at all exception levels.
        """
        reg.field( 5,  0, "t0sz", 64-self.pgt_conf.tsz)
        reg.field( 9,  8, "irgn0", 1)  # Normal WB RAWA
        reg.field(11, 10, "orgn0", 1)  # Normal WB RAWA
        reg.field(13, 12, "sh0", 3)    # Inner Shareable
        reg.field(15, 14, "tg0", {"4K":0, "16K":2, "64K":1}[self.pgt_conf.tg_str])

        """
        Bits that are RES1 at all exception levels.
        """
        reg.res1(23) # technically epd1 at EL1 but we'll want =1 then anyway

        """
        Exception level specific differences.
        """
        ps_val = {32:0, 36:1, 40:2, 48:5}[self.pgt_conf.tsz]
        if self.pgt_conf.el == 1:
            reg.field(34, 32, "ps", ps_val)
        else:
            reg.field(18, 16, "ps", ps_val)
            reg.res1(31)

        return hex(reg.value())


    def _sctlr(self) -> str:
        """
        Generate required value for SCTLR_ELn.
        """
        reg = Register(f"sctlr_el{self.pgt_conf.el}")

        """
        Configurable bitfields present at all exception levels.
        """
        reg.field( 0,  0, "m", 1)    # MMU enabled
        reg.field( 2,  2, "c", 1)    # D-side access cacheability controlled by pgtables
        reg.field(12, 12, "i", 1),   # I-side access cacheability controlled by pgtables


        return hex(reg.value())


    def entry_template(self, mem_type, mem_attr, is_page:bool ):
        """
        Translation table entry fields common across all exception levels.
        """
        pte = Register("pte")
        pte.field( 0,  0, "valid", 1)
        pte.field( 1,  1, "[1]", int(is_page))
        pte.field( 4,  2, "attrindx", self.mem_types[mem_type])
        pte.field( 5,  5, "ns", mem_attr.ns)
        pte.field( 7,  6, "AP", mem_attr.ap)
        pte.field( 9,  8, "sh", 3)  # Inner Shareable, ignored by Device memory
        pte.field(10, 10, "af", 1)  # Disable Access Flag faults
        pte.field(53, 53, "pxn", mem_attr.ns)
        pte.field(54, 54, "xn", mem_attr.ns)

        return hex(pte.value())

