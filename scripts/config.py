import errno
import re
import sys
import logging
import json

from pgtt.mmu import *
from pgtt.table import *
from pgtt.codegen import *


class PgtConfig:
    def __init__(self, pgt):
        self.ttbr_str       = pgt["table_base_addr"]
        self.ttbr           = self.parse_addr(pgt["table_base_addr"])
        self.el             = pgt["excepiton_level"]
        self.tg_str         = pgt["granule"]
        self.tg             = {"4K": 4*1024, "16K": 16*1024, "64K": 64*1024}[self.tg_str]
        self.tsz            = pgt["table_region_size"]
        self.large_page     = pgt["large_page"]
        self.gen_code       = pgt["gen_table_runtime"]

        self.regions = []
        for idx, pgt_map in enumerate(pgt["maps"]):
            va = self.parse_addr(pgt_map["va"])
            pa = self.parse_addr(pgt_map["pa"])
            size = self.parse_size(pgt_map["size"])
            # alignment adjust
            down_alignment = va % self.tg
            up_alignment = (va + size) % self.tg
            up_alignment = 0 if not up_alignment else self.tg - up_alignment
            size += (down_alignment + up_alignment)

            mem_type = pgt_map["type"]
            mem_attr = self.parse_attr(pgt_map["attr"])
            label = pgt_map["description"]
            r = Region(0, label, va, pa, size, mem_type, mem_attr)
            self.regions.append(r)

    def parse_addr(self, s):
        s = s.upper()
        try:
            addr = int(s, base=(16 if s.startswith("0X") else 10))
        except ValueError:
            logging.error(f"invalid config address {s}")
        return addr

    def parse_size(self, s):
        s = s.upper()
        x = re.search(r"(\d+)([KMGT])", s)
        try:
            qty = x.group(1)
            logging.debug(f"got qty: {qty}")
            unit = x.group(2)
            logging.debug(f"got unit: {unit}")
        except AttributeError:
            logging.error(f"invalid config size {s}")
        return int(qty) * 1024 ** ("KMGT".find(unit) + 1)

    def parse_attr(self, s):
        if re.match(r"(?!!?w!?x!?s)", s):
            logging.error(f"bad memory attr {s}")
            sys.exit(errno.EINVAL)
        # force enable EL0 access
        ap = 0b11 if re.search(r"!w", s) else 0b01
        xn = 0b1  if re.search(r"!x", s) else 0b0
        ns = 0b1  if re.search(r"!s", s) else 0b0

        return MemAttr(ap, xn, ns)

class Config:
    def __init__(self, config_file_raw):
        self.config_str = self.remove_comments(config_file_raw)
        self.config = json.loads(self.config_str)

    def is_comment_line(self, line):
        if re.match(r"\s*//.*", line):
            return True
        return False

    def remove_comments(self, config_file_raw):
        lines = ""
        with open(config_file_raw, "r") as config_raw_handle:
            lines_raw = config_raw_handle.readlines()
            for line in lines_raw:
                if not self.is_comment_line(line):
                    lines += line

        return lines
    def pgt_configs(self):
        pgt_configs = []
        for pg in self.config["pagetables"]:
            pgt_configs.append(PgtConfig(pg))
        return pgt_configs


logging.basicConfig( level=logging.DEBUG)
conf = Config("config.json")
print(conf.pgt_configs())
for pgt_conf in conf.pgt_configs():
    mmu_conf = MmuConfig(pgt_conf)
    table = Table.gen(mmu_conf.start_level, mmu_conf)
    print(str(table))
    coder = CodeGen(table)
    print(coder.gen())
