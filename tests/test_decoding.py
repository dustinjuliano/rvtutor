import unittest
from unittest.mock import patch, MagicMock
import io
import sys
import main
from engine import QuizEngine
from riscv import Instruction

class TestDecoding(unittest.TestCase):
    def setUp(self):
        self.engine = QuizEngine()
        # Populate pool for distractors
        self.engine.filter_pool(['R', 'I', 'S', 'B', 'U', 'J'])

    def test_validate_asm_strict_R(self):
        ins = Instruction("add", "R", 0x33, 0x0, 0x0)
        # Target vals
        t_vals = {"rd": 1, "rs1": 2, "rs2": 3, "imm": 0}
        
        # Correct
        ok, msg = main.validate_asm_strict("add x1, x2, x3", ins, t_vals)
        self.assertTrue(ok, msg)
        
        # Syntax Errors
        ok, msg = main.validate_asm_strict("add x1 x2 x3", ins, t_vals) # Missing commas
        self.assertFalse(ok)
        self.assertIn("Syntax Error", msg)
        
        # Wrong Mnemonic
        ok, msg = main.validate_asm_strict("sub x1, x2, x3", ins, t_vals)
        self.assertFalse(ok)
        self.assertIn("Mnemonic", msg)
        
        # Wrong Register
        ok, msg = main.validate_asm_strict("add x1, x2, x4", ins, t_vals)
        self.assertFalse(ok)
        self.assertIn("Incorrect register", msg)

    def test_validate_asm_strict_I_Load(self):
        ins = Instruction("lw", "I", 0x03, 0x2)
        t_vals = {"rd": 1, "rs1": 2, "imm": 4, "rs2": 0}
        
        # Correct
        ok, msg = main.validate_asm_strict("lw x1, 4(x2)", ins, t_vals)
        self.assertTrue(ok, msg)
        
        # Wrong Syntax (Store like)
        ok, msg = main.validate_asm_strict("lw x2, 4(x1)", ins, t_vals) # swapped regs?
        # lw rd, imm(rs1). User: lw x2, 4(x1). rd=2, rs1=1. Target: rd=1, rs1=2.
        self.assertFalse(ok)
        self.assertIn("Incorrect register", msg)

    def test_validate_asm_strict_S(self):
        ins = Instruction("sw", "S", 0x23, 0x2)
        t_vals = {"rs1": 1, "rs2": 2, "imm": 8, "rd": 0}
        
        # Correct
        ok, msg = main.validate_asm_strict("sw x2, 8(x1)", ins, t_vals)
        self.assertTrue(ok, msg)
        
        # Bad Syntax
        ok, msg = main.validate_asm_strict("sw x2, x1, 8", ins, t_vals)
        self.assertFalse(ok)

    def test_validate_asm_strict_B(self):
        ins = Instruction("beq", "B", 0x63, 0x0)
        t_vals = {"rs1": 1, "rs2": 2, "imm": -4, "rd": 0}
        
        # Correct
        ok, msg = main.validate_asm_strict("beq x1, x2, -4", ins, t_vals)
        self.assertTrue(ok, msg)
        
        # Wrong Immediate
        ok, msg = main.validate_asm_strict("beq x1, x2, 4", ins, t_vals)
        self.assertFalse(ok)
        self.assertIn("Incorrect Immediate", msg)

    @patch('builtins.input')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_decoding_flow_success(self, mock_stdout, mock_input):
        # 6-step single-attempt pipeline:
        # Step 1: Hex->Binary, Step 2: Opcode, Step 3: Type,
        # Step 4: Field Names, Step 5: Field Values (single input), Step 6: Assembly
        
        ins = Instruction("addi", "I", 0x13, 0x0)
        q = {"instruction": ins, "rs1": 2, "rs2": 0, "rd": 1, "imm": 10, "asm": "addi x1, x2, 10"}
        
        mock_truth = {
            "hex": "00a10093",
            "binary": "00000000101000010000000010010011",
            "fields": [("imm[11:0]", "000000001010"), ("rs1", "00010"), ("funct3", "000"), ("rd", "00001"), ("opcode", "0010011")] 
        }
        
        self.engine.get_ground_truth = MagicMock(return_value=mock_truth)
        
        inputs = [
            mock_truth['binary'],                      # Step 1: Binary
            "19",                                      # Step 2: Opcode
            "I",                                       # Step 3: Type
            "imm[11:0] rs1 funct3 rd opcode",          # Step 4: Field Names
            "10 2 0 1 19",                             # Step 5: Field Values (MSB to LSB)
            "addi x1, x2, 10",                         # Step 6: Assembly
        ]
        
        mock_input.side_effect = inputs
        
        res = main.run_decoding_pipeline(self.engine, q)
        self.assertTrue(res)
        
        output = mock_stdout.getvalue()
        self.assertIn("Step 1: Hex to Binary", output)
        self.assertIn("Step 6: Final Assembly", output)
        self.assertIn("imm[11:0]", output)
        self.assertIn("rs1", output)
        self.assertIn("funct3", output)
        self.assertIn("rd", output)
        self.assertIn("opcode", output)

    @patch('builtins.input')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_decoding_malformed_inputs(self, mock_stdout, mock_input):
        # Single-attempt: wrong answers are immediately revealed
        ins = Instruction("addi", "I", 0x13, 0x0)
        q = {"instruction": ins, "rs1": 2, "rs2": 0, "rd": 1, "imm": 10, "asm": "addi x1, x2, 10"}
        
        mock_truth = {
            "hex": "00a10093",
            "binary": "00000000101000010000000010010011",
            "fields": [("imm[11:0]", "000000001010"), ("rs1", "00010"), ("funct3", "000"), ("rd", "00001"), ("opcode", "0010011")],
            "asm": "addi x1, x2, 10"
        }
        self.engine.get_ground_truth = MagicMock(return_value=mock_truth)
        
        inputs = [
            "0" * 31,                   # Step 1: Wrong length -> 0 pts, answer revealed
            "WRONG_OP",                 # Step 2: Fail (revealed)
            "X",                        # Step 3: Fail (revealed)
            "bad",                      # Step 4: Fail (revealed)
            "bad bad bad bad bad",       # Step 5: Fail (revealed)
            "bad asm",                  # Step 6: Fail (revealed)
        ]
        mock_input.side_effect = inputs
        
        res = main.run_decoding_pipeline(self.engine, q)
        self.assertTrue(res)

    def test_reference_table_uniqueness(self):
        ins_add = Instruction("add", "R", 51, 0, 0)
        ins_sub = Instruction("sub", "R", 51, 0, 32)
        ins_sll = Instruction("sll", "R", 51, 1, 0)
        ins_addi = Instruction("addi", "I", 19, 0)
        ins_lw = Instruction("lw", "I", 3, 2)
        
        self.engine.pool = [ins_add, ins_sub, ins_sll, ins_addi, ins_lw]
        q = {"instruction": ins_add, "asm": "add x1, x2, x3", "hex": "...", "binary": "...", "rs1": 0, "rs2": 0, "rd": 0, "imm": 0}
        self.engine.current_q = q
        
        with patch('builtins.input', side_effect=['q']):
            with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
                main.run_decoding_pipeline(self.engine, q)
                
                output = mock_stdout.getvalue()
                self.assertIn("add", output)
                self.assertNotIn("sub", output)
                self.assertNotIn("sll", output)
                self.assertIn("addi", output)
                self.assertIn("lw", output)

    def test_decoding_progressive_feedback(self):
        q = self.engine.generate_question()
        truth = self.engine.get_ground_truth()
        correct_bin = truth['binary']
        
        # Single-attempt: wrong-length binary gets 0 pts, answer revealed, moves on
        inputs = [
            "101",       # Wrong length -> 0 pts, answer revealed immediately
            "q"          # Quit at Step 2
        ]
        
        self.engine.stats = {"success": 0, "attempts": 0, "points": 0.0, "total_points": 0}
        
        with patch('builtins.input', side_effect=inputs):
            with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
                main.run_decoding_pipeline(self.engine, q)
                
                # After wrong binary, correct answer is revealed in the worksheet
                output = mock_stdout.getvalue()
                self.assertIn("Step 1: Hex to Binary", output)
                # Should have recorded 0 points for failed binary
                self.assertAlmostEqual(self.engine.stats['points'], 0.0)

    def test_decoding_partial_grading(self):
        ins = Instruction("addi", "I", 0x13, 0x0)
        q = {"instruction": ins, "rs1": 2, "rs2": 0, "rd": 1, "imm": 10, "asm": "addi x1, x2, 10"}
        
        mock_truth = {
            "hex": "00a10093",
            "binary": "00000000101000010000000010010011",
            "fields": [("imm[11:0]", "000000001010"), ("rs1", "00010"), ("funct3", "000"), ("rd", "00001"), ("opcode", "0010011")]
        }
        self.engine.get_ground_truth = MagicMock(return_value=mock_truth)
        
        # Change 4 bits (1 nibble) to make it 7/8 correct
        wrong_bin = "1111" + mock_truth['binary'][4:]
            
        inputs = [
            wrong_bin,                                 # Step 1: 7/8 correct (0.875), single-attempt
            "19",                                      # Step 2: Correct (1.0)
            "I",                                       # Step 3: Correct (1.0)
            "imm[11:0] rs1 funct3 rd opcode",          # Step 4: All correct (1.0)
            "10 2 0 1 19",                             # Step 5: All correct (1.0)
            "addi x1, x2, 10",                         # Step 6: Correct (1.0)
        ]
        
        self.engine.stats = {"success": 0, "attempts": 0, "points": 0.0, "total_points": 0}
        
        with patch('builtins.input', side_effect=inputs):
             res = main.run_decoding_pipeline(self.engine, q)
             self.assertTrue(res)
             
             # Step 1: 0.875 / 1.0
             # Step 2: 1.0 / 1.0
             # Step 3: 1.0 / 1.0
             # Step 4: 1.0 / 1.0
             # Step 5: 1.0 / 1.0
             # Step 6: 1.0 / 1.0
             # Total points: 5.875
             # Total potential: 6.0
             self.assertAlmostEqual(self.engine.stats["points"], 5.875, places=3)
             self.assertAlmostEqual(self.engine.stats["total_points"], 6.0, places=1)

    def test_strict_grading_step2_3_failure(self):
        ins = Instruction("addi", "I", 0x13, 0x0)
        q = {"instruction": ins, "rs1": 2, "rs2": 0, "rd": 1, "imm": 10}
        mock_truth = {
            "hex": "00a10093",
            "binary": "00000000101000010000000010010011",
            "fields": [("imm[11:0]", "0"), ("rs1", "0"), ("funct3", "0"), ("rd", "0"), ("opcode", "0")]
        }
        self.engine.get_ground_truth = MagicMock(return_value=mock_truth)

        inputs = [
            mock_truth['binary'], # Step 1: Correct (1.0)
            "99",                 # Step 2: Fail (0.0), answer revealed
            "R",                  # Step 3: Fail (0.0), answer revealed
            "q"                   # Step 4: Quit
        ]
        self.engine.stats = {"success": 0, "attempts": 0, "points": 0.0, "total_points": 0}
        
        with patch('builtins.input', side_effect=inputs):
             try:
                 main.run_decoding_pipeline(self.engine, q)
             except:
                 pass
             
             # points: 1.0 (S1) + 0.0 (S2) + 0.0 (S3) = 1.0
             self.assertEqual(self.engine.stats["points"], 1.0)
             self.assertEqual(self.engine.stats["total_points"], 3)

    def test_decoding_table_filtering(self):
        # Setup specific pool to test filtering
        ins_addi = Instruction("addi", "I", 19, 0)
        ins_lw = Instruction("lw", "I", 3, 2)
        ins_add = Instruction("add", "R", 51, 0, 0)
        
        self.engine.pool = [ins_addi, ins_lw, ins_add]
        # target is addi
        q = {"instruction": ins_addi, "asm": "addi x1, x2, 10", "rd": 1, "rs1": 2, "rs2": 0, "imm": 10}
        
        mock_truth = {
            "hex": "00a10093",
            "binary": "00000000101000010000000010010011",
            "fields": [("opcode", "0010011"), ("rd", "00001"), ("funct3", "000"), ("rs1", "00010"), ("imm[11:0]", "000000001010")],
            "asm": "addi x1, x2, 10"
        }
        self.engine.get_ground_truth = MagicMock(return_value=mock_truth)
        
        inputs = [
            mock_truth['binary'], # Step 1: Binary
            "19",                 # Step 2: Opcode
            "q"                   # Step 3: Type (Quit)
        ]
        
        with patch('builtins.input', side_effect=inputs):
            with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
                main.run_decoding_pipeline(self.engine, q)
                output = mock_stdout.getvalue()
                
                # Split output to inspect Stage 3 specifically
                parts = output.split("Step 3: Instruction Type")
                self.assertEqual(len(parts), 2, "Should have reached Step 3")
                step3_view = parts[1]
                
                # Use regex to check for instructions at the start of rows
                import re
                self.assertTrue(re.search(r'^addi\s+\|', step3_view, re.MULTILINE), "addi should be in table")
                self.assertFalse(re.search(r'^add\s+\|', step3_view, re.MULTILINE), "add should be filtered out")
                self.assertFalse(re.search(r'^lw\s+\|', step3_view, re.MULTILINE), "lw should be filtered out")

if __name__ == '__main__':
    unittest.main()
