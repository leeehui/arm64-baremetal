# target macros
CROSS_COMPILE := aarch64-none-linux-gnu-
TARGET := test# FILL: target filename
BUILD_DIR := build
LD_FILE := $(BUILD_DIR)/$(TARGET).ld
DEP_DIR := $(BUILD_DIR)/.deps
SRC_DIRS := src 

# from atf log
CFLAGS	:= -nostdinc -Werror -Wall -Wmissing-include-dirs -Wunused -Wdisabled-optimization -Wvla -Wshadow \
		   -Wno-unused-parameter -Wredundant-decls -Wunused-but-set-variable -Wmaybe-uninitialized \
		   -Wpacked-bitfield-compat -Wshift-overflow=2 -Wlogical-op -Wno-error=deprecated-declarations \
		   -Wno-error=cpp -march=armv8-a -mgeneral-regs-only -mstrict-align \
		   -ffunction-sections -fdata-sections -ffreestanding -fno-builtin -fno-common -Os -std=gnu99 -fno-stack-protector 

LDFLAGS	:= -T ${LD_FILE} --fatal-warnings --gc-sections

CC := $(CROSS_COMPILE)gcc
AS := $(CROSS_COMPILE)gcc
LD := $(CROSS_COMPILE)ld
OBJCOPY := $(CROSS_COMPILE)objcopy

# recursive wildcard
rwildcard=$(foreach d,$(wildcard $(addsuffix *,$(1))),$(call rwildcard,$(d)/,$(2))$(filter $(subst *,%,$(2)),$(d)))

INC_DIRS := include
#INC_DIRS += `find . -type f -name '*.h' | sed -r 's|/[^/]+$||' |sort |uniq`
CFLAGS += $(patsubst %, -I%, $(INC_DIRS))

ALL_C_SRCS += $(call rwildcard,$(SRC_DIRS),*.c)
ALL_S_SRCS += $(call rwildcard,$(SRC_DIRS),*.S)
ALL_OBJS += $(patsubst %.c, %.o, ${ALL_C_SRCS})
ALL_OBJS += $(patsubst %.S, %.o, ${ALL_S_SRCS})
BUILD_OBJS := $(patsubst %, $(BUILD_DIR)/%, ${ALL_OBJS})

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

$(LD_FILE): $(TARGET).ld.S
	@echo "  PP    $@"
	@$(CC) -E $(CFLAGS) -x c $< | grep -v '^#' > $@

# phony targets
.PHONY: all
all: $(BUILD_DIR)/$(TARGET).elf

.PHONY: clean
clean: 
	rm -rf $(BUILD_DIR)/*


