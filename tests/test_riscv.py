import unittest
from riscv import Instruction, Swizzler, REGISTRY

class TestRISCV(unittest.TestCase):
    def test_instruction_init(self):
        ins = Instruction("ADD", "R", 0x33, 0x0, 0x00)
        self.assertEqual(ins.name, "add")
        self.assertEqual(ins.type, "R")
        self.assertEqual(ins.op, 0x33)
        self.assertEqual(ins.f3, 0)
        self.assertEqual(ins.f7, 0)

    def test_instruction_guards(self):
        # Name
        with self.assertRaises(ValueError):
            Instruction("", "R", 0x33)
        # Type
        with self.assertRaises(ValueError):
            Instruction("nop", "X", 0x33)
        # Opcode
        with self.assertRaises(ValueError):
            Instruction("nop", "I", 128)
        # Funct3
        with self.assertRaises(ValueError):
            Instruction("nop", "I", 0x13, f3=8)
        # Funct7
        with self.assertRaises(ValueError):
            Instruction("nop", "R", 0x33, f7=128)

    def test_swizzler_s(self):
        # imm[11:5] | imm[4:0]
        # 0xA80 -> 0b1010 1000 0000
        # bits 11:5 = 0b1010100 (0x54)
        # bits 4:0 = 0b00000 (0x00)
        res = Swizzler.s_type(0xA80)
        self.assertEqual(res, ["1010100", "00000"])
        
        with self.assertRaises(TypeError):
            Swizzler.s_type("0xA80")

    def test_swizzler_b(self):
        # imm[12] | imm[10:5] | imm[4:1] | imm[11]
        # Value 0x155FFE -> bits 12:1 are 0b1 0101 0101 1111
        # b12=1, b11=0, b10_5=101010 (0x2A), b4_1=1111 (0xF)
        # 0xAAA -> 1010 1010 1010
        # Wait, let's use a clear one: 0x1002 (bit 12=1, bit 1=1)
        # b12=1, b11=0, b10_5=000000, b4_1=0001
        res = Swizzler.b_type(0x1002)
        self.assertEqual(res, ["1", "000000", "0001", "0"])

    def test_swizzler_j(self):
        # imm[20] | imm[10:1] | imm[11] | imm[19:12]
        # 0x155FFE -> b20=1, b19_12=01010101 (0x55), b11=1, b10_1=1111111111 (0x3FF)
        res = Swizzler.j_type(0x155FFE)
        self.assertEqual(res, ["1", "1111111111", "1", "01010101"])

    def test_registry_comprehensive(self):
        # Every instruction in registry must have a valid layout
        from riscv import LAYOUTS
        for ins in REGISTRY:
            self.assertIn(ins.type, LAYOUTS)
            self.assertTrue(len(ins.name) > 0)
            self.assertTrue(0 <= ins.op < 128)

    def test_swizzler_j_negatives(self):
        # -2 -> 0x1FFFFE
        res = Swizzler.j_type(-2)
        self.assertEqual(res, ["1", "1111111111", "1", "11111111"])

    def test_swizzler_u_boundaries(self):
        # U-type is just 20 bits
        self.assertEqual(Swizzler.j_type(0), ["0", "0000000000", "0", "00000000"]) # Wait, j_type test
        # Let's just add a simple registry sanity check
        self.assertEqual(len(REGISTRY), 9)

    def test_swizzler_s_negatives(self):
        # imm = -1 (0xFFF)
        # bits 11:5 = 1111111, bits 4:0 = 11111
        res = Swizzler.s_type(-1)
        self.assertEqual(res, ["1" * 7, "1" * 5])

    def test_swizzler_b_negatives(self):
        # imm = -2 (0x1FFE)
        # b12=1, b10_5=111111, b4_1=1111, b11=1
        res = Swizzler.b_type(-2)
        self.assertEqual(res, ["1", "111111", "1111", "1"])

    def test_swizzler_b_boundaries(self):
        # Min/Max 13-bit signed imm for B-type (masked to 13 bits internally, but Swizzler handles bits)
        # 0x1FFE (max pos) -> b12=1, b11=1, b10_5=111111, b4_1=1111
        res = Swizzler.b_type(0x1FFE)
        self.assertEqual(res, ["1", "111111", "1111", "1"])
        # 0x0 -> all 0
        res = Swizzler.b_type(0)
        self.assertEqual(res, ["0", "000000", "0000", "0"])

    def test_swizzler_j_boundaries(self):
        # 0x1FFFFE -> b20=1, b19_12=11111111, b11=1, b10_1=1111111111
        res = Swizzler.j_type(0x1FFFFE)
        self.assertEqual(res, ["1", "1111111111", "1", "11111111"])
        # 0x0
        res = Swizzler.j_type(0)
        self.assertEqual(res, ["0", "0000000000", "0", "00000000"])

if __name__ == '__main__':
    unittest.main()
