O ?= .
ARCH ?= x86_64

IMAGE_x86_64 = arch/x86/boot/bzImage
IMAGE_i386 = arch/x86/boot/bzImage
IMAGE_arm64 = arch/arm64/boot/Image.gz
IMAGE_arm = arch/arm/boot/zImage
IMAGE_riscv = arch/riscv/boot/Image.gz
IMAGE_powerpc = arch/powerpc/boot/zImage

IMAGE = $(IMAGE_$(ARCH))

.PHONY: all defconfig mrproper menuconfig

all:
	test -f "$(O)/.config"
	test "$(FAKE_SLOW)" != "1" || sleep 6
	mkdir -p "$(O)/$(dir $(IMAGE))"
	touch "$(O)/$(IMAGE)"

defconfig:
	test "$(O)" = "." || test ! -f .config
	mkdir -p "$(O)"
	printf '%s\n' '# CONFIG_FAKE_KERNEL is not set' > "$(O)/.config"

mrproper:
	rm -rf "$(O)/.config" "$(O)/arch"

menuconfig:
	sleep 6