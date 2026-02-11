import unittest
from utils import to_bin, to_hex, sign_extend

class TestUtils(unittest.TestCase):
    def test_to_bin_valid(self):
        self.assertEqual(to_bin(5, 4), "0101")
        self.assertEqual(to_bin(0, 1), "0")
        self.assertEqual(to_bin(255, 8), "11111111")
        # Over-wide value should be masked
        self.assertEqual(to_bin(0xFF, 4), "1111")

    def test_to_bin_guards(self):
        with self.assertRaises(TypeError):
            to_bin("5", 4)
        with self.assertRaises(TypeError):
            to_bin(5, "4")
        with self.assertRaises(ValueError):
            to_bin(5, 0)
        with self.assertRaises(ValueError):
            to_bin(5, -1)

    def test_to_bin_zero_width(self):
        with self.assertRaises(ValueError):
            to_bin(5, 0)

    def test_to_bin_large_mask(self):
        # Masking 0xFF to 1 bit
        self.assertEqual(to_bin(0xFF, 1), "1")
        # Masking 0xFE to 1 bit
        self.assertEqual(to_bin(0xFE, 1), "0")

    def test_to_hex_valid(self):
        self.assertEqual(to_hex(0), "00000000")
        self.assertEqual(to_hex(0xABCDEF), "00abcdef")
        self.assertEqual(to_hex(0xFFFFFFFF), "ffffffff")
        # Should mask to 32-bit
        self.assertEqual(to_hex(0x1FFFFFFFF), "ffffffff")

    def test_to_hex_guards(self):
        with self.assertRaises(TypeError):
            to_hex("0x5")

    def test_sign_extend_valid(self):
        # 8-bit to 32-bit
        self.assertEqual(sign_extend(0x7F, 8), 127)
        self.assertEqual(sign_extend(0x80, 8), -128)
        self.assertEqual(sign_extend(0xFF, 8), -1)
        # 12-bit (I-type imm)
        self.assertEqual(sign_extend(0x7FF, 12), 2047)
        self.assertEqual(sign_extend(0x800, 12), -2048)

    def test_sign_extend_guards(self):
        with self.assertRaises(TypeError):
            sign_extend("127", 8)
        with self.assertRaises(TypeError):
            sign_extend(127, "8")
        with self.assertRaises(ValueError):
            sign_extend(127, 0)
        with self.assertRaises(ValueError):
            sign_extend(127, 33)

    def test_to_bin_negatives(self):
        # 2's complement masking for -1
        self.assertEqual(to_bin(-1, 8), "11111111")
        self.assertEqual(to_bin(-1, 1), "1")

    def test_sign_extend_max_bits(self):
        # 32-bit to 32-bit (identity)
        self.assertEqual(sign_extend(0xFFFFFFFF, 32), -1)
        self.assertEqual(sign_extend(0x7FFFFFFF, 32), 2147483647)

    def test_sign_extend_boundaries(self):
        # 1-bit extension (edge case)
        self.assertEqual(sign_extend(0, 1), 0)
        self.assertEqual(sign_extend(1, 1), -1)
        # 31-bit to 32-bit (nearly full)
        self.assertEqual(sign_extend(0x40000000, 31), -0x40000000)

    def test_to_bin_masking_complex(self):
        # Large value, many bits
        self.assertEqual(to_bin(0xFFFFFFFF, 32), "1" * 32)
        # Large value, few bits (masking check)
        self.assertEqual(to_bin(0b10101010, 4), "1010")

    def test_to_hex_large_values(self):
        # 64-bit value should be truncated to 32-bit
        self.assertEqual(to_hex(0xFFFFFFFFF), "ffffffff")
        # Exact 32-bit max
        self.assertEqual(to_hex(0xFFFFFFFF), "ffffffff")
        # Zero
        self.assertEqual(to_hex(0), "00000000")

if __name__ == '__main__':
    unittest.main()
