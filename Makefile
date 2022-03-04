# target macros
CROSS_COMPILE := aarch64-none-linux-gnu-
TARGET := test# FILL: target filename
BUILD_DIR := build
LD_FILE := $(BUILD_DIR)/$(TARGET).ld
DEP_DIR := $(BUILD_DIR)/.deps
SRC_DIRS := src 
DEBUG	:= 1

# from atf log
# -Wredundant-decls -Wshadow 
CFLAGS	:= -nostdinc -Werror -Wall -Wmissing-include-dirs -Wunused -Wdisabled-optimization -Wvla \
		   -Wno-unused-parameter -Wunused-but-set-variable -Wmaybe-uninitialized \
		   -Wpacked-bitfield-compat -Wshift-overflow=2 -Wlogical-op -Wno-error=deprecated-declarations \
		   -Wno-error=cpp -march=armv8-a -mgeneral-regs-only -mstrict-align \
		   -ffunction-sections -fdata-sections -ffreestanding -fno-builtin -fno-common -Os -std=gnu99 -fno-stack-protector 

LDFLAGS	:= -T ${LD_FILE} --fatal-warnings --gc-sections

CC := $(CROSS_COMPILE)gcc
AS := $(CROSS_COMPILE)gcc
LD := $(CROSS_COMPILE)ld
OBJCOPY := $(CROSS_COMPILE)objcopy
OBJDUMP := $(CROSS_COMPILE)objdump
READELF := $(CROSS_COMPILE)readelf

# recursive wildcard
rwildcard=$(foreach d,$(wildcard $(addsuffix *,$(1))),$(call rwildcard,$(d)/,$(2))$(filter $(subst *,%,$(2)),$(d)))

USER_INC_DIRS := include src
#INC_DIRS += `find . -type f -name '*.h' | sed -r 's|/[^/]+$||' |sort |uniq`
CFLAGS += $(patsubst %, -I%, $(USER_INC_DIRS))

# specify path of std headers we override(only contains essential implementations)
STDLIBC_INC_DIRS := sysinc
CFLAGS += $(patsubst %, -isystem %, $(STDLIBC_INC_DIRS))

# we do not use standard library which usually means the standard libc
# but still we need compiler level headers, e.g. stddef.h stdargs.h stdint.h ...
# as previous cflag "-nostdinc" tells gcc ONLY search dirs specified by -I -isystem -iqoute
# the following shell command print full path of a library call "include" which contains
# the compiler level headers 
COMPILER_INC_DIRS := $(shell $(CC) -print-file-name=include)
CFLAGS += $(patsubst %, -isystem %, $(COMPILER_INC_DIRS))

ifeq ($(DEBUG), 1)
CFLAGS += -g
endif


ALL_C_SRCS += $(call rwildcard,$(SRC_DIRS),*.c)
ALL_S_SRCS += $(call rwildcard,$(SRC_DIRS),*.S)
ALL_OBJS += $(patsubst %.c, %.o, ${ALL_C_SRCS})
ALL_OBJS += $(patsubst %.S, %.o, ${ALL_S_SRCS})
BUILD_OBJS := $(patsubst %, $(BUILD_DIR)/%, ${ALL_OBJS})

# phony targets
.PHONY: all
all: $(BUILD_DIR)/$(TARGET).asm

${BUILD_DIR}/%.o: %.S
	@echo "  AS    $@"
	@mkdir -p $(DEP_DIR)
	@mkdir -p "$(dir $@)"
	@$(AS) -c $(CFLAGS) -MMD -MF $(DEP_DIR)/$(*F).d -MQ "$@" -MP -o $@ $<

${BUILD_DIR}/%.o: %.c
	@echo "  CC    $@"
	@mkdir -p $(DEP_DIR)
	@mkdir -p "$(dir $@)"
	@$(CC) -c $(CFLAGS) -MMD -MF $(DEP_DIR)/$(*F).d -MQ "$@" -MP -o $@ $<

$(BUILD_DIR)/$(TARGET).elf: $(BUILD_OBJS) $(LD_FILE)
	@echo "  LD    $@"
	@$(LD) $(LDFLAGS) -o $@ $(BUILD_OBJS)

$(BUILD_DIR)/$(TARGET).asm: $(BUILD_DIR)/$(TARGET).elf
	@echo "  CP    $@"
	@$(OBJDUMP) -D $< > $@

$(LD_FILE): $(TARGET).ld.S
	@echo "  PP    $@"
	@$(CC) -E $(CFLAGS) -x c $< | grep -v '^#' > $@

.PHONY: clean
clean: 
	rm -rf $(BUILD_DIR)/*


