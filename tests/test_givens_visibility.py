import unittest
from unittest.mock import patch, MagicMock
import io
import sys
from main import run_encoding_pipeline
from engine import QuizEngine
from riscv import Instruction

class TestGivensVisibility(unittest.TestCase):
    @patch('builtins.input')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_givens_visibility(self, mock_stdout, mock_input):
        engine = QuizEngine()
        ins = Instruction("add", "R", 0x33, 0x0, 0x0)
        q = {
            "instruction": ins, 
            "rs1": 1, "rs2": 2, "rd": 3, "imm": 0, 
            "asm": "add x3, x1, x2"
        }
        engine.current_q = q
        
        # Inputs for the 4 steps:
        # 1. Type: R
        # 2. Field Names: funct7 rs2 rs1 funct3 rd opcode
        # 3. Binary: 0000000 00010 00001 000 00011 0110011
        # 4. Hex: 002081b3
        
        mock_input.side_effect = [
            "R",
            "funct7 rs2 rs1 funct3 rd opcode",
            "0000000 00010 00001 000 00011 0110011",
            "002081b3"
        ]
        
        run_encoding_pipeline(engine, q)
        output = mock_stdout.getvalue()
        
        # Check that funct3/funct7 context appears for Steps 3 and 4,
        # but NOT for Steps 1 and 2.
        # display_context(show_givens=True) prints "Funct3:" and "Funct7:" 
        # for R-type which has both funct3 and funct7.
        
        idx_step1 = output.find("What instruction type is")
        idx_step2 = output.find("What are the field names for instruction")
        idx_step3 = output.find("What are the binary values for each field")
        idx_step4 = output.find("What is the final 32-bit hex encoding")
        
        self.assertNotEqual(idx_step1, -1)
        self.assertNotEqual(idx_step2, -1)
        self.assertNotEqual(idx_step3, -1)
        self.assertNotEqual(idx_step4, -1)
        
        # Funct3/Funct7 context should appear 2 times (Steps 3 and 4).
        funct3_count = output.count("Funct3:")
        self.assertEqual(funct3_count, 2, f"Expected 2 Funct3 occurrences, got {funct3_count}")
        
        # Verify location: first Funct3 must appear after Step 2 prompt
        first_funct3 = output.find("Funct3:")
        second_funct3 = output.find("Funct3:", first_funct3 + 1)
        
        self.assertGreater(first_funct3, idx_step2)
        self.assertGreater(second_funct3, idx_step3)

if __name__ == '__main__':
    unittest.main()
