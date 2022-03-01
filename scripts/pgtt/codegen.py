"""
Copyright (c) 2019 Ash Wilding. All rights reserved.

SPDX-License-Identifier: MIT
"""
from struct import *

# Internal deps
from .mmu import *
from .table import *



class CodeGen:
    def __init__(self, table):
        self.table = table
        self.pgt_conf = table.pgt_conf
        self.mmu_conf = table.mmu_conf

    def _mk_table(self, table_idx, table) -> str:
        """
        Generate assembly to begin programming a translation table.

        args
        ====

            n
                        table number in sequential order from ttbr0_eln

            t
                        translation table being programmed
        """
        return f"""
    program_table_{table_idx}:

        LDR     x8, ={hex(table.addr)}          // base address of this table
        LDR     x9, ={hex(table.chunk)}         // chunk size"""



    def _mk_blocks(self, table_idx, table, entry_idx_start, region) -> str:
        """
        Generate assembly to program a range of contiguous block/page entries.

        args
        ====

            n
                        table number in sequential order from ttbr0_eln

            t
                        translation table being programmed

            idx
                        index of the first block/page in the contiguous range

            r
                        the memory region
        """
        return f"""

    program_table_{table_idx}_entry_{entry_idx_start}{f'_to_{entry_idx_start + region.num_contig - 1}' if region.num_contig > 1 else ''}:

        LDR     x10, ={entry_idx_start}                 // idx
        LDR     x11, ={region.num_contig}        // number of contiguous entries
        LDR     x12, ={hex(region.pa)}         // output address of entry[idx]
        LDR     x13, ={self.mmu_conf.entry_template(region.mem_type, region.mem_attr, region.is_page)}
    1:
        ORR     x12, x12, x13    // merge output address with template
        STR     X12, [x8, x10, lsl #3]      // write entry into table
        ADD     x10, x10, #1                // prepare for next entry idx+1
        ADD     x12, x12, x9                // add chunk to address
        SUBS    x11, x11, #1                // loop as required
        B.NE    1b"""



    def _mk_next_level_table(self,  parent_table_idx, entry_idx, table) -> str:
        """
        Generate assembly to program a pointer to a next level table.

        args
        ====

            n
                        parent table number in sequential order from ttbr0_eln

            idx
                        index of the next level table pointer

            next_t
                        the next level translation table
        """
        return f"""

    program_table_{parent_table_idx}_entry_{entry_idx}:

        LDR     x10, ={entry_idx}                 // idx
        LDR     x11, ={hex(table.addr)}    // next-level table address
        ORR     x11, x11, #0x3              // next-level table descriptor
        STR     x11, [x8, x10, lsl #3]      // write entry into table"""



    def _mk_asm(self) -> str:
        """
        Generate assembly to program all allocated translation tables.
        """
        string = ""
        for n,t in enumerate(self.table._allocated):
            string += self._mk_table(n, t)
            keys = sorted(list(t.entries.keys()))
            while keys:
                idx = keys[0]
                entry = t.entries[idx]
                if type(entry) is Region:
                    string += self._mk_blocks(n, t, idx, entry)
                    for k in range(idx, idx+entry.num_contig):
                        keys.remove(k)
                else:
                    string += self._mk_next_level_table(n, idx, entry)
                    keys.remove(idx)
        return string

    def _fill_entry(self, table, entry_idx, entry, page_mem_fd):
        entry_offset = table.addr - self.pgt_conf.ttbr + entry_idx * 8
        page_mem_fd.seek(entry_offset)
        if type(entry) is Region:
            for idx in range(entry_idx, entry_idx + entry.num_contig):
                addr = entry.pa + (idx - entry_idx) * table.chunk + int(self.mmu_conf.entry_template(entry.mem_type, entry.mem_attr, entry.is_page), base=16)
                data = pack("<Q", addr)
                page_mem_fd.write(data)

        else:
            addr = (entry.addr | 0x3)
            data = pack("<Q", addr )
            page_mem_fd.write(data)



    def _mk_mem(self, page_mem_file) :
        """
        Generate assembly to program all allocated translation tables.
        """
        #page_data = bytearray()
        with open(page_mem_file, "wb") as page_mem_fd:

            page_mem_fd.write(b'\x00' * self.pgt_conf.tg * len(self.table._allocated))

            for n,t in enumerate(self.table._allocated):
                keys = sorted(list(t.entries.keys()))
                while keys:
                    idx = keys[0]
                    entry = t.entries[idx]
                    if type(entry) is Region:
                        self._fill_entry(t, idx, entry, page_mem_fd)
                        for k in range(idx, idx+entry.num_contig):
                            keys.remove(k)
                    else:
                        self._fill_entry(t, idx, entry, page_mem_fd)
                        keys.remove(idx)

        page_mem_fd.close()

    def gen(self):
        _newline = "\n"
        _tmp = f"""
    /*
     * This file was automatically generated using arm64-pgtable-tool.
     * See: https://github.com/ashwio/arm64-pgtable-tool
     *
     * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
     * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
     * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
     * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
     * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
     * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
     * SOFTWARE.
     *
     * The programmer must also ensure that the virtual memory region containing the
     * translation tables is itself marked as NORMAL in the memory map file.
     */

        .section .data.mmu
        .balign 2

        mmu_lock: .4byte 0                  // lock to ensure only 1 CPU runs init
        #define LOCKED 1

        mmu_init: .4byte 0                  // whether init has been run
        #define INITIALISED 1

        .section .text.mmu_on
        .balign 2
        .global mmu_on
        .type mmu_on, @function

    mmu_on:

        ADRP    x0, mmu_lock                // get 4KB page containing mmu_lock
        ADD     x0, x0, :lo12:mmu_lock      // restore low 12 bits lost by ADRP
        MOV     w1, #LOCKED
        SEVL                                // first pass won't sleep
    1:
        WFE                                 // sleep on retry
        LDAXR   w2, [x0]                    // read mmu_lock
        CBNZ    w2, 1b                      // not available, go back to sleep
        STXR    w3, w1, [x0]                // try to acquire mmu_lock
        CBNZ    w3, 1b                      // failed, go back to sleep

    check_already_initialised:

        ADRP    x1, mmu_init                // get 4KB page containing mmu_init
        ADD     x1, x1, :lo12:mmu_init      // restore low 12 bits lost by ADRP
        LDR     w2, [x1]                    // read mmu_init
        CBNZ    w2, end                     // init already done, skip to the end

    zero_out_tables:

        LDR     x2, ={hex(self.pgt_conf.ttbr)}        // address of first table
        LDR     x3, ={hex(self.pgt_conf.tg * len(self.table._allocated))}   // combined length of all tables
        LSR     x3, x3, #5                  // number of required STP instructions
        FMOV    d0, xzr                     // clear q0
    1:
        STP     q0, q0, [x2], #32           // zero out 4 table entries at a time
        SUBS    x3, x3, #1
        B.NE    1b

    {self._mk_asm() if self.pgt_conf.gen_code else ""}

    init_done:

        MOV     w2, #INITIALISED
        STR     w2, [x1]

    end:

        LDR     x1, ={self.pgt_conf.ttbr}             // program ttbr0 on this CPU
        MSR     ttbr0_el{self.pgt_conf.el}, x1
        LDR     x1, ={self.mmu_conf.mair}             // program mair on this CPU
        MSR     mair_el{self.pgt_conf.el}, x1
        LDR     x1, ={self.mmu_conf.tcr}              // program tcr on this CPU
        MSR     tcr_el{self.pgt_conf.el}, x1
        ISB
        MRS     x2, tcr_el{self.pgt_conf.el}         // verify CPU supports desired config
        CMP     x2, x1
        B.NE    .
        LDR     x1, ={self.mmu_conf.sctlr}            // program sctlr on this CPU
        MSR     sctlr_el{self.pgt_conf.el}, x1
        ISB                                 // synchronize context on this CPU
        STLR    wzr, [x0]                   // release mmu_lock
        RET                                 // done!
    """



        output = ""
        for line in _tmp.splitlines():
            if "//" in line and not " * " in line:
                idx = line.index("//")
                code = line[:idx].rstrip()
                comment = line[idx:]
                line = f"{code}{' ' * (41 - len(code))}{comment}"
            output += f"{line}\n"

        self._mk_mem("/home/lh/page")

        return output

