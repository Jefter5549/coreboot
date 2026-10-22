/* SPDX-License-Identifier: GPL-2.0-only */

#include <device/azalia_device.h>

const u32 cim_verb_data[] = {
	0x10ec0897,	/* Realtek ALC897 */
	0x10ec0897,	/* Subsystem ID */
	13,		/* Number of entries */

	AZALIA_PIN_CFG(0, 0x11, 0x40000000),
	AZALIA_PIN_CFG(0, 0x12, 0x411111f0),
	AZALIA_PIN_CFG(0, 0x14, 0x01014410), /* Line Out (Green) */
	AZALIA_PIN_CFG(0, 0x15, 0x411111f0),
	AZALIA_PIN_CFG(0, 0x16, 0x411111f0),
	AZALIA_PIN_CFG(0, 0x17, 0x411111f0),
	AZALIA_PIN_CFG(0, 0x18, 0x01a19c40), /* Mic In Rear (Pink) */
	AZALIA_PIN_CFG(0, 0x19, 0x02a19c50), /* Mic In Front */
	AZALIA_PIN_CFG(0, 0x1a, 0x0181344f), /* Line In Rear (Blue) */
	AZALIA_PIN_CFG(0, 0x1b, 0x02214420), /* HP Out Front */
	AZALIA_PIN_CFG(0, 0x1c, 0x411111f0),
	AZALIA_PIN_CFG(0, 0x1d, 0x4024c601),
	AZALIA_PIN_CFG(0, 0x1e, 0x411111f0),
};

const u32 pc_beep_verbs[0] = {};

AZALIA_ARRAY_SIZES;
