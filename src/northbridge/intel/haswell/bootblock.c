/* SPDX-License-Identifier: GPL-2.0-only */

#include <arch/bootblock.h>
#include <assert.h>
#include <device/pci_ops.h>
#include <types.h>

#include "haswell.h"

static uint32_t encode_pciexbar_length(void)
{
	switch (CONFIG_ECAM_MMCONF_BUS_NUMBER) {
		case 256: return 0 << 1;
		case 128: return 1 << 1;
		case  64: return 2 << 1;
		default:  return dead_code_t(uint32_t);
	}
}

static void haswell_ep_early_init(void)
{
	const uint32_t mmcfg_base = CONFIG_ECAM_MMCONF_BASE_ADDRESS;
	const uint32_t mmcfg_len = CONFIG_ECAM_MMCONF_BUS_NUMBER * 0x100000;
	const uint32_t mmcfg_limit = mmcfg_base + mmcfg_len;

	pci_io_write_config32(HASWELL_EP_SAD, 0x90, mmcfg_base);
	pci_io_write_config32(HASWELL_EP_SAD, 0x94, 0);
	pci_io_write_config32(HASWELL_EP_SAD, 0x98, mmcfg_limit);
	pci_io_write_config32(HASWELL_EP_SAD, 0x9c, 0);
}

void bootblock_early_northbridge_init(void)
{
	if (is_haswell_ep()) {
		haswell_ep_early_init();
		return;
	}

	/*
	 * The "io" variant of the config access is explicitly used to setup the
	 * PCIEXBAR because CONFIG(ECAM_MMCONF_SUPPORT) is set to true. That way, all
	 * subsequent non-explicit config accesses use MCFG. This code also assumes
	 * that bootblock_northbridge_init() is the first thing called in the non-asm
	 * boot block code. The final assumption is that no assembly code is using the
	 * CONFIG(ECAM_MMCONF_SUPPORT) option to do PCI config accesses.
	 *
	 * The PCIEXBAR is assumed to live in the memory mapped IO space under 4GiB.
	 */
	const uint32_t reg32 = CONFIG_ECAM_MMCONF_BASE_ADDRESS | encode_pciexbar_length() | 1;
	pci_io_write_config32(HOST_BRIDGE, PCIEXBAR + 4, 0);
	pci_io_write_config32(HOST_BRIDGE, PCIEXBAR, reg32);
}


