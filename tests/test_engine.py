import unittest
from engine import QuizEngine
from riscv import Instruction

class TestEngine(unittest.TestCase):
    def setUp(self):
        self.engine = QuizEngine()

    def test_filter_pool_valid(self):
        self.engine.filter_pool(['R', 'I'])
        # Registry has add, sub, sll (R) and addi, lw (I)
        self.assertEqual(len(self.engine.pool), 5)

    def test_filter_pool_guards(self):
        with self.assertRaises(TypeError):
            self.engine.filter_pool("R")
        with self.assertRaises(ValueError):
            self.engine.filter_pool(['X']) # None matching

    def test_filter_pool_all_literal(self):
        # Test the list with 'all' inside (though main.py handles it, engine should be robust)
        self.engine.filter_pool(['R', 'I', 'S', 'B', 'U', 'J'])
        self.assertEqual(len(self.engine.pool), 10)

    def test_filter_pool_redundant(self):
        self.engine.filter_pool(['R', 'R', 'R'])
        self.assertEqual(len(self.engine.pool), 3) # add, sub, sll

    def test_generate_question_guards(self):
        # Empty pool
        with self.assertRaises(RuntimeError):
            self.engine.generate_question()

    def test_generate_question_types(self):
        # Test immediate constraints for different types
        # B-type
        self.engine.filter_pool(['B'])
        q = self.engine.generate_question()
        self.assertEqual(q["imm"] % 2, 0)
        self.assertTrue(-4096 <= q["imm"] < 4096)
        
        # J-type
        self.engine.filter_pool(['J'])
        q = self.engine.generate_question()
        self.assertTrue(-1048576 <= q["imm"] < 1048576)

    def test_ground_truth_logic_i(self):
        # Already tested addi in base, but let's keep it structured
        ins = Instruction("addi", "I", 0x13, 0x0)
        self.engine.pool = [ins]
        self.engine.current_q = {"instruction": ins, "rs1": 1, "rs2": 0, "rd": 2, "imm": 10}
        truth = self.engine.get_ground_truth()
        self.assertEqual(truth["hex"], "00a08113")

    def test_ground_truth_logic_r(self):
        # add x3, x1, x2 -> funct7=0, rs2=2, rs1=1, f3=0, rd=3, op=0x33
        # 0000000 | 00010 | 00001 | 000 | 00011 | 0110011
        # bin: 00000000001000001000000110110011 -> 0x002081B3
        ins = Instruction("add", "R", 0x33, 0x0, 0x0)
        self.engine.pool = [ins]
        self.engine.current_q = {"instruction": ins, "rs1": 1, "rs2": 2, "rd": 3, "imm": 0}
        truth = self.engine.get_ground_truth()
        self.assertEqual(truth["hex"], "002081b3")

    def test_ground_truth_logic_s(self):
        # sw x2, 8(x1) -> imm=8 (0000000 01000)
        # imm[11:5]=0000000 | rs2=2 | rs1=1 | f3=2 | imm[4:0]=01000 | op=0x23
        # 0000000 | 00010 | 00001 | 010 | 01000 | 0100011
        # bin: 00000000001000001010010000100011 -> 0x0020A423
        ins = Instruction("sw", "S", 0x23, 0x2)
        self.engine.pool = [ins]
        self.engine.current_q = {"instruction": ins, "rs1": 1, "rs2": 2, "rd": 0, "imm": 8}
        truth = self.engine.get_ground_truth()
        self.assertEqual(truth["hex"], "0020a423")

    def test_ground_truth_logic_b(self):
        # beq x1, x2, 4 -> imm=4 (offset +4)
        # imm[12]=0, imm[10:5]=000000, imm[4:1]=0010, imm[11]=0
        # 0 | 000000 | 00010 | 00001 | 000 | 0010 | 0 | 1100011
        # bin: 00000000001000001000001001100011 -> 0x00208263
        ins = Instruction("beq", "B", 0x63, 0x0)
        self.engine.pool = [ins]
        self.engine.current_q = {"instruction": ins, "rs1": 1, "rs2": 2, "rd": 0, "imm": 4}
        truth = self.engine.get_ground_truth()
        self.assertEqual(truth["hex"], "00208263")

    def test_ground_truth_logic_u(self):
        # lui x1, 0x1 -> imm=1
        # imm[31:12]=00000000000000000001 | rd=1 | op=0x37
        # 00000000000000000001 | 00001 | 0110111
        # bin: 00000000000000000001000010110111 -> 0x000010B7
        ins = Instruction("lui", "U", 0x37)
        self.engine.pool = [ins]
        self.engine.current_q = {"instruction": ins, "rs1": 0, "rs2": 0, "rd": 1, "imm": 1}
        truth = self.engine.get_ground_truth()
        self.assertEqual(truth["hex"], "000010b7")

    def test_ground_truth_logic_j(self):
        # jal x1, 2 -> imm=2
        # imm[20]=0, imm[10:1]=0000000001, imm[11]=0, imm[19:12]=00000000
        # 0 | 0000000001 | 0 | 00000000 | 00001 | 1101111
        # bin: 0000000001000000000000011101111 -> 0x002000EF
        ins = Instruction("jal", "J", 0x6F)
        self.engine.pool = [ins]
        self.engine.current_q = {"instruction": ins, "rs1": 0, "rs2": 0, "rd": 1, "imm": 2}
        truth = self.engine.get_ground_truth()
        self.assertEqual(truth["hex"], "002000ef")

    def test_validation_layout(self):
        # R-type
        ins = Instruction("add", "R", 0x33, 0x0, 0x0)
        self.engine.pool = [ins]
        self.engine.generate_question()
        input_correct = ["funct7", "rs2", "rs1", "funct3", "rd", "opcode"]
        ok, mask, correct = self.engine.validate_layout(input_correct)
        self.assertTrue(ok)
        self.assertEqual(len(mask), len(correct))
        
        ok, _, _ = self.engine.validate_layout(["bad", "rs2", "rs1", "funct3", "rd", "opcode"])
        self.assertFalse(ok)
        
        with self.assertRaises(TypeError):
            self.engine.validate_layout("string")

    def test_validation_bits(self):
        self.engine.filter_pool(['U']) # imm[31:12](20), rd(5), op(7)
        self.engine.generate_question()
        ok, mask, correct = self.engine.validate_bits([20, 5, 7])
        self.assertTrue(ok)
        
        ok, _, _ = self.engine.validate_bits([20, 5, "7"]) # Handles string if it converts
        self.assertTrue(ok)
        
        ok, _, _ = self.engine.validate_bits([20, 5, "bad"])
        self.assertFalse(ok)

    def test_validation_bits_edge_cases(self):
        # Mismatched length
        self.engine.filter_pool(['U'])
        self.engine.generate_question()
        ok, _, _ = self.engine.validate_bits([20, 5]) # Too short
        self.assertFalse(ok)
        
        # Mixed invalid inputs
        ok, mask, _ = self.engine.validate_bits(["20", None, 7.0])
        self.assertFalse(ok)
        self.assertTrue(mask[0]) # 20 works
        self.assertFalse(mask[1]) # None fails

    def test_stats_success_logic(self):
        # 2 correct, 1 partial (fail)
        self.engine.stats = {"success": 0, "attempts": 0, "points": 0, "total_points": 0}
        self.engine.record_stats(5, 5) # Success
        self.engine.record_stats(5, 5) # Success
        self.engine.record_stats(3, 5) # Fail
        self.assertEqual(self.engine.stats["success"], 2)
        self.assertEqual(self.engine.stats["attempts"], 3)

    def test_format_asm_R(self):
        ins = Instruction("add", "R", 0x33, 0x0, 0x0)
        q = {"instruction": ins, "rs1": 1, "rs2": 2, "rd": 3, "imm": 0}
        self.assertEqual(self.engine.format_asm(q), "add x3, x1, x2")

    def test_format_asm_I(self):
        ins_addi = Instruction("addi", "I", 0x13, 0x0)
        q_addi = {"instruction": ins_addi, "rs1": 1, "rs2": 0, "rd": 2, "imm": -10}
        self.assertEqual(self.engine.format_asm(q_addi), "addi x2, x1, -10")
        
        ins_lw = Instruction("lw", "I", 0x03, 0x2)
        q_lw = {"instruction": ins_lw, "rs1": 5, "rs2": 0, "rd": 6, "imm": 4}
        self.assertEqual(self.engine.format_asm(q_lw), "lw x6, 4(x5)")

    def test_format_asm_S(self):
        ins = Instruction("sw", "S", 0x23, 0x2)
        q = {"instruction": ins, "rs1": 5, "rs2": 6, "rd": 0, "imm": 8}
        self.assertEqual(self.engine.format_asm(q), "sw x6, 8(x5)")

    def test_format_asm_B(self):
        ins = Instruction("beq", "B", 0x63, 0x0)
        q = {"instruction": ins, "rs1": 1, "rs2": 2, "rd": 0, "imm": 4}
        self.assertEqual(self.engine.format_asm(q), "beq x1, x2, 4")

    def test_format_asm_U(self):
        ins = Instruction("lui", "U", 0x37)
        q = {"instruction": ins, "rs1": 0, "rs2": 0, "rd": 5, "imm": 1}
        self.assertEqual(self.engine.format_asm(q), "lui x5, 1")

    def test_format_asm_J(self):
        ins = Instruction("jal", "J", 0x6F)
        q = {"instruction": ins, "rs1": 0, "rs2": 0, "rd": 1, "imm": 4}
        self.assertEqual(self.engine.format_asm(q), "jal x1, 4")

    def test_semantic_validity_comprehensive(self):
        """
        Cryptographically verify that generated instructions:
        1. Never write to x0 (rd != 0 for R, I, U, J types).
        2. Have valid 2-byte aligned immediates for B, J types.
        3. Keep register indices within [0, 31].
        """
        self.engine.filter_pool(['R', 'I', 'S', 'B', 'U', 'J'])
        
        # Run enough iterations to hit edge cases
        for _ in range(1000):
            q = self.engine.generate_question()
            ins = q["instruction"]
            
            # 1. Register Range Checks
            self.assertTrue(0 <= q['rs1'] <= 31, f"rs1 out of range: {q['rs1']}")
            self.assertTrue(0 <= q['rs2'] <= 31, f"rs2 out of range: {q['rs2']}")
            self.assertTrue(0 <= q['rd'] <= 31, f"rd out of range: {q['rd']}")
            
            # 2. Destination semantics (x0 is read-only)
            # R, I, U, J types write to rd
            if ins.type in ['R', 'I', 'U', 'J']:
                self.assertNotEqual(q['rd'], 0, f"Generated write to x0 for {ins.name} ({ins.type})")
                
            # 3. Immediate semantics (Alignment)
            # B, J types must be 2-byte aligned
            if ins.type in ['B', 'J']:
                self.assertEqual(q['imm'] % 2, 0, f"Misaligned immediate for {ins.name}: {q['imm']}")

if __name__ == '__main__':
    unittest.main()
