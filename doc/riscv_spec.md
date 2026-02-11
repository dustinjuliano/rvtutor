# RISC-V RV32I Specification Summary

This document serves as a reference for the core RISC-V instruction layouts and encoding rules.

## Instruction Formats

| Type | 31 30--25 | 24--21 20 | 19--15 | 14--12 | 11--8 7 | 6--0 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **R** | funct7 | rs2 | rs1 | funct3 | rd | opcode |
| **I** | imm[11:0] | rs1 | funct3 | rd | opcode |
| **S** | imm[11:5] | rs2 | rs1 | funct3 | imm[4:0] | opcode |
| **B** | imm[12] imm[10:5] | rs2 | rs1 | funct3 | imm[4:1] imm[11] | opcode |
| **U** | imm[31:12] | rd | opcode |
| **J** | imm[20] imm[10:1] imm[11] imm[19:12] | rd | opcode |

## Detailed Scrambling for B and J Types

### B-Type (Conditional Branches)
- Layout (MSB to LSB):
  - `inst[31]` (1 bit): `imm[12]` (Sign bit)
  - `inst[30:25]` (6 bits): `imm[10:5]`
  - `inst[24:20]` (5 bits): `rs2`
  - `inst[19:15]` (5 bits): `rs1`
  - `inst[14:12]` (3 bits): `funct3`
  - `inst[11:8]` (4 bits): `imm[4:1]`
  - `inst[7]` (1 bit): `imm[11]`
  - `inst[6:0]` (7 bits): `opcode`
- **Total Immediate**: 13 bits (imm[12:0]), LSB (imm[0]) is always 0.

### J-Type (Unconditional Jumps)
- Layout (MSB to LSB):
  - `inst[31]` (1 bit): `imm[20]` (Sign bit)
  - `inst[30:21]` (10 bits): `imm[10:1]`
  - `inst[20]` (1 bit): `imm[11]`
  - `inst[19:12]` (8 bits): `imm[19:12]`
  - `inst[11:7]` (5 bits): `rd`
  - `inst[6:0]` (7 bits): `opcode`
- **Total Immediate**: 21 bits (imm[20:0]), LSB (imm[0]) is always 0.

## Rationale
Scrambling avoids requiring multiple multiplexers for different bit-positions in hardware. Bit 31 is always the sign bit for all formats, enabling parallel sign extension.
