#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only

import argparse
import os
import struct
import subprocess
import sys


def get_symbol_address(elf_path, symbol_name):
	out = subprocess.check_output(["nm", "-n", elf_path]).decode()
	for line in out.splitlines():
		parts = line.strip().split()
		if len(parts) >= 3 and parts[2] == symbol_name:
			return int(parts[0], 16)
	raise ValueError(f"Symbol '{symbol_name}' not found in {elf_path}")


def get_romstage_rom_base(cbfstool_path, cb_rom_path):
	out = subprocess.check_output([cbfstool_path, cb_rom_path, "print"]).decode()
	for line in out.splitlines():
		parts = line.split()
		if len(parts) >= 2 and parts[0] == "fallback/romstage":
			cbfs_offset = int(parts[1], 16)
			return 0xff831000 + cbfs_offset + 0x60
	raise ValueError("Could not find 'fallback/romstage' in CBFS")


def main():
	parser = argparse.ArgumentParser(
		description="Stitch Coreboot CBFS with factory Descriptor, ME, and SEC for Machinist X99-MR9A PRO"
	)
	parser.add_argument("--stock", required=True, help="Path to stock 16MB BIOS dump")
	parser.add_argument("--coreboot", default="build/coreboot.rom", help="Path to built coreboot.rom")
	parser.add_argument("--romstage", default="build/cbfs/fallback/romstage.elf", help="Path to romstage.elf")
	parser.add_argument("--cbfstool", default="build/cbfstool", help="Path to cbfstool")
	parser.add_argument("-o", "--output", default="machinist_x99_mr9a_pro.bin", help="Output 16MB image path")
	args = parser.parse_args()

	if not os.path.exists(args.stock):
		sys.exit(f"Stock dump not found: {args.stock}")
	if not os.path.exists(args.coreboot):
		sys.exit(f"Coreboot ROM not found: {args.coreboot}")

	cbfstool = args.cbfstool
	if not os.path.exists(cbfstool):
		cbfstool = "util/cbfstool/cbfstool"
		if not os.path.exists(cbfstool):
			sys.exit(f"cbfstool not found at {args.cbfstool} or {cbfstool}")

	with open(args.stock, "rb") as f:
		stock = bytearray(f.read())
	with open(args.coreboot, "rb") as f:
		cb = f.read()

	if len(stock) != 16 * 1024 * 1024 or len(cb) != 16 * 1024 * 1024:
		sys.exit("Input files must be exactly 16MB (16777216 bytes)")

	car_stack_top = get_symbol_address(args.romstage, "_ecar_stack")
	car_entry_vma = get_symbol_address(args.romstage, "car_stage_entry")
	gdtptr_vma = get_symbol_address(args.romstage, "gdtptr")
	bss_start = get_symbol_address(args.romstage, "_bss")
	bss_end = get_symbol_address(args.romstage, "_ebss")
	data_start = get_symbol_address(args.romstage, "_data")
	data_end = get_symbol_address(args.romstage, "_edata")
	data_load_vma = get_symbol_address(args.romstage, "_data_load")
	fmap_cache = get_symbol_address(args.romstage, "_fmap_cache")

	romstage_rom_base = get_romstage_rom_base(cbfstool, args.coreboot)
	car_entry = romstage_rom_base + (car_entry_vma - 0x02000000)
	gdtptr = romstage_rom_base + (gdtptr_vma - 0x02000000)
	data_load = romstage_rom_base + (data_load_vma - 0x02000000)

	image = bytearray(stock)
	image[0x800000:0xda0000] = cb[0x800000:0xda0000]

	console_start = 0x810000
	console_size = 0x020000
	image[console_start : console_start + console_size] = b"\xff" * console_size

	fmap_rom_addr = 0xff830000

	trampoline = bytearray([
		0xb0, 0x77,
		0xe6, 0x80,
		0x2e, 0x0f, 0x01, 0x15,
	])
	trampoline += struct.pack("<I", gdtptr)
	trampoline += bytearray([
		0x66, 0xb8, 0x10, 0x00,
		0x8e, 0xd8,
		0x8e, 0xc0,
		0x8e, 0xd0,
		0xbc,
	])
	trampoline += struct.pack("<I", car_stack_top)
	trampoline += bytearray([
		0xfc,
		0x31, 0xc0,
		0xb9,
	])
	trampoline += struct.pack("<I", bss_end)
	trampoline += bytearray([0xbf])
	trampoline += struct.pack("<I", bss_start)
	trampoline += bytearray([
		0x29, 0xf9,
		0xc1, 0xe9, 0x02,
		0xf3, 0xab,
		0xb9,
	])
	trampoline += struct.pack("<I", data_end)
	trampoline += bytearray([0xbf])
	trampoline += struct.pack("<I", data_start)
	trampoline += bytearray([
		0x29, 0xf9,
		0xc1, 0xe9, 0x02,
		0xbe,
	])
	trampoline += struct.pack("<I", data_load)
	trampoline += bytearray([
		0xf3, 0xa5,
		0x83, 0xe4, 0xf0,
		0xb0, 0x78,
		0xe6, 0x80,
		0xba, 0xf8, 0x0c, 0x00, 0x00,
		0xb8, 0x90, 0x28, 0x00, 0x80,
		0xef,
		0xba, 0xfc, 0x0c, 0x00, 0x00,
		0xb8, 0x01, 0x00, 0x00, 0x80,
		0xef,
		0xba, 0xf8, 0x0c, 0x00, 0x00,
		0xb8, 0x94, 0x28, 0x00, 0x80,
		0xef,
		0xba, 0xfc, 0x0c, 0x00, 0x00,
		0x31, 0xc0,
		0xef,
		0xba, 0xf8, 0x0c, 0x00, 0x00,
		0xb8, 0x98, 0x28, 0x00, 0x80,
		0xef,
		0xba, 0xfc, 0x0c, 0x00, 0x00,
		0xb8, 0x01, 0x00, 0x00, 0x8c,
		0xef,
		0xba, 0xf8, 0x0c, 0x00, 0x00,
		0xb8, 0x9c, 0x28, 0x00, 0x80,
		0xef,
		0xba, 0xfc, 0x0c, 0x00, 0x00,
		0x31, 0xc0,
		0xef,
		0xb0, 0x79,
		0xe6, 0x80,
		0xc7, 0x05, 0xf0, 0x80, 0x0f, 0x80,
		0x01, 0xc0, 0xd1, 0xfe,
		0xb0, 0x7a,
		0xe6, 0x80,
		0xbe,
	])
	trampoline += struct.pack("<I", fmap_rom_addr)
	trampoline += bytearray([0xbf])
	trampoline += struct.pack("<I", fmap_cache)
	trampoline += bytearray([
		0xb9, 0x80, 0x00, 0x00, 0x00,
		0xf3, 0xa5,
		0xb0, 0x7b,
		0xe6, 0x80,
		0xb8,
	])
	trampoline += struct.pack("<I", car_entry)
	trampoline += bytearray([
		0xff, 0xd0,
		0xb0, 0xee,
		0xe6, 0x80,
		0xf4,
		0xeb, 0xfd,
	])

	# DxeIpl entry point (0xffda9b68) executed after PEI memory training completes
	hook_offset = 0xda9b68
	image[hook_offset : hook_offset + len(trampoline)] = trampoline

	with open(args.output, "wb") as f_out:
		f_out.write(image)

	print(f"Image successfully created: {args.output}")


if __name__ == "__main__":
	main()
