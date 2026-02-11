"""
RISC-V Tutor Instruction Registry & Swizzlers
Defines layouts and bit-reordering logic with strict guards.
"""
from typing import List, Dict, Optional
from utils import to_bin

class Instruction:
    def __init__(self, name: str, type_char: str, op: int, f3: Optional[int] = None, f7: Optional[int] = None):
        if not isinstance(name, str) or not name:
            raise ValueError("name must be a non-empty string")
        if not isinstance(type_char, str) or type_char.upper() not in "RISBUJ":
            raise ValueError("type_char must be one of R, I, S, B, U, J")
        if not isinstance(op, int) or not (0 <= op < 128):
            raise ValueError("opcode must be a 7-bit integer")
        
        self.name = name.lower()
        self.type = type_char.upper()
        self.op = op
        self.f3 = f3
        self.f7 = f7
        
        # Guards for funct fields if provided
        if f3 is not None and (not isinstance(f3, int) or not (0 <= f3 < 8)):
            raise ValueError("funct3 must be a 3-bit integer")
        if f7 is not None and (not isinstance(f7, int) or not (0 <= f7 < 128)):
            raise ValueError("funct7 must be a 7-bit integer")

class Swizzler:
    @staticmethod
    def s_type(imm: int) -> List[str]:
        """S-Type: imm[11:5] (7b) | imm[4:0] (5b)"""
        if not isinstance(imm, int):
            raise TypeError("imm must be int")
        # Mask to 12 bits
        val = imm & 0xFFF
        high = (val >> 5) & 0x7F # bits 11:5
        low = val & 0x1F         # bits 4:0
        return [to_bin(high, 7), to_bin(low, 5)]

    @staticmethod
    def b_type(imm: int) -> List[str]:
        """B-Type: imm[12] | imm[10:5] | imm[4:1] | imm[11]"""
        if not isinstance(imm, int):
            raise TypeError("imm must be int")
        val = imm & 0x1FFE # 13 bits, bit 0 is always 0
        b12 = (val >> 12) & 0x1
        b11 = (val >> 11) & 0x1
        b10_5 = (val >> 5) & 0x3F
        b4_1 = (val >> 1) & 0xF
        return [to_bin(b12, 1), to_bin(b10_5, 6), to_bin(b4_1, 4), to_bin(b11, 1)]

    @staticmethod
    def j_type(imm: int) -> List[str]:
        """J-Type: imm[20] | imm[10:1] | imm[11] | imm[19:12]"""
        if not isinstance(imm, int):
            raise TypeError("imm must be int")
        val = imm & 0x1FFFFE # 21 bits, bit 0 is 0
        b20 = (val >> 20) & 0x1
        b19_12 = (val >> 12) & 0xFF
        b11 = (val >> 11) & 0x1
        b10_1 = (val >> 1) & 0x3FF
        return [to_bin(b20, 1), to_bin(b10_1, 10), to_bin(b11, 1), to_bin(b19_12, 8)]

LAYOUTS = {
    'R': [('funct7', 7), ('rs2', 5), ('rs1', 5), ('funct3', 3), ('rd', 5), ('opcode', 7)],
    'I': [('imm', 12), ('rs1', 5), ('funct3', 3), ('rd', 5), ('opcode', 7)],
    'S': [('imm', 7), ('rs2', 5), ('rs1', 5), ('funct3', 3), ('imm', 5), ('opcode', 7)],
    'B': [('imm', 1), ('imm', 6), ('rs2', 5), ('rs1', 5), ('funct3', 3), ('imm', 4), ('imm', 1), ('opcode', 7)],
    'U': [('imm', 20), ('rd', 5), ('opcode', 7)],
    'J': [('imm', 1), ('imm', 10), ('imm', 1), ('imm', 8), ('rd', 5), ('opcode', 7)],
}

REGISTRY = [
    Instruction("add",  "R", 0x33, 0x0, 0x00),
    Instruction("sub",  "R", 0x33, 0x0, 0x20),
    Instruction("sll",  "R", 0x33, 0x1, 0x00),
    Instruction("addi", "I", 0x13, 0x0),
    Instruction("lw",   "I", 0x03, 0x2),
    Instruction("sw",   "S", 0x23, 0x2),
    Instruction("beq",  "B", 0x63, 0x0),
    Instruction("lui",  "U", 0x37),
    Instruction("jal",  "J", 0x6F),
]
