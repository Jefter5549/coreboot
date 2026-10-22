/* SPDX-License-Identifier: GPL-2.0-only */

#include <bootblock_common.h>
#include <device/pci_ops.h>
#include <southbridge/intel/lynxpoint/pch.h>
#include <southbridge/intel/common/gpio.h>

void bootblock_mainboard_early_init(void)
{
	/* Configure PCH LPC generic decode ranges for Nuvoton Super I/O */
	/* GEN1_DEC: 0x003c0a01 -> Window 0x0a00-0x0a3f enabled (for HWM at 0x0a20) */
	pci_write_config32(PCI_DEV(0, 0x1f, 0), LPC_GEN1_DEC, 0x003c0a01);

	/* GEN4_DEC: 0x001c0601 -> Window 0x0600-0x061f enabled (for PM/ACPI) */
	pci_write_config32(PCI_DEV(0, 0x1f, 0), LPC_GEN4_DEC, 0x001c0601);

	/* Initialize PCH GPIOs early */
	setup_pch_gpios(&mainboard_gpio_map);
}
