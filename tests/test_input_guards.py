
import unittest
from unittest.mock import patch
import io
import sys
from main import main, run_encoding_pipeline
from engine import QuizEngine
from riscv import Instruction

class TestInputGuards(unittest.TestCase):
    
    @patch('builtins.input')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_mode_1_recall_extra_fields(self, mock_stdout, mock_input):
        """Mode 1 (Recall): Verify extra fields are handled gracefully."""
        # Instruction: add (R-Type) -> funct7 rs2 rs1 funct3 rd opcode (6 fields)
        # Input: 7 fields (1 extra)
        # Flow: Types (R), Mode (1), Step 1 Type (R), Step 2 Fields (R + extra), Continue (n), Quit
        mock_input.side_effect = ["R", "1", "R", "funct7 rs2 rs1 funct3 rd opcode extra", "n", "q"]
        
        with patch('engine.random.choice') as mock_choice:
            ins = Instruction("add", "R", 0x33, 0x0, 0x0)
            mock_choice.return_value = ins
            
            with self.assertRaises(SystemExit):
                main()
            
            output = mock_stdout.getvalue()
            self.assertIn("extra: ✗ (Extra)", output)
            self.assertNotIn("IndexError", output)
            # Verify accuracy reporting
            # Recall mode uses "Incorrect. Points: X/Y"
            self.assertRegex(output, r"Incorrect\. Points: \d+/\d+")

    @patch('builtins.input')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_mode_2_bits_extra_fields(self, mock_stdout, mock_input):
        """Mode 2 (Bits): Verify extra fields are handled gracefully."""
        # Instruction: addi (I-Type) -> 12 5 3 5 7 (5 fields)
        # Input: 6 fields (1 extra)
        # Flow: Types (I), Mode (2), Step 1 Type (I), Step 2 Bits (Extra), Continue (n), Quit
        mock_input.side_effect = ["I", "2", "I", "12 5 3 5 7 99", "n", "q"]
        
        with patch('engine.random.choice') as mock_choice:
            ins = Instruction("addi", "I", 0x13, 0x0)
            mock_choice.return_value = ins
            
            with self.assertRaises(SystemExit):
                main()
            
            output = mock_stdout.getvalue()
            # Expecting handling for extra fields
            self.assertIn("(Extra)", output)
            # Verify accuracy reporting
            # Bits mode uses "Incorrect. Points: X/Y"
            self.assertRegex(output, r"Incorrect\. Points: \d+/\d+")

    @patch('builtins.input')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_mode_3_step_2_fields_extra(self, mock_stdout, mock_input):
        """Mode 3 (Encoding) Step 2: Verify extra fields are handled gracefully."""
        # Instruction: sub (R-Type)
        # Step 1: Type (R) -> OK
        # Step 2: Fields -> Extra field
        engine = QuizEngine()
        ins = Instruction("sub", "R", 0x33, 0x0, 0x20)
        q = {"instruction": ins, "rs1": 1, "rs2": 2, "rd": 3, "imm": 0, "asm": "sub x3, x1, x2"}
        engine.current_q = q
        
        mock_input.side_effect = [
            "R", # Step 1
            "funct7 rs2 rs1 funct3 rd opcode extra", # Step 2: Extra field
            "q", # Quit
            "q"  # Quit main
        ]
        
        with patch('sys.exit'): # Prevent actual exit if it bubbles up
             run_encoding_pipeline(engine, q)
             
        output = mock_stdout.getvalue()
        self.assertIn("extra: ✗ (Extra)", output)
        # Encoding mode uses "Incorrect. (X/Y)"
        self.assertRegex(output, r"Incorrect\. \(\d+/\d+\)")

    @patch('builtins.input')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_mode_3_step_3_binary_extra(self, mock_stdout, mock_input):
        """Mode 3 (Encoding) Step 3: Verify extra binary fields are handled gracefully."""
        # Instruction: jal (J-Type) -> imm[20] imm[10:1] imm[11] imm[19:12] rd opcode
        # 6 parts
        engine = QuizEngine()
        ins = Instruction("jal", "J", 0x6F)
        q = {"instruction": ins, "rd": 1, "imm": 4, "rs1":0, "rs2":0, "asm": "jal x1, 4"}
        engine.current_q = q
        
        # Mock correct binary strings partially to pass logic if needed, but we focus on length
        # J-Type parts: 1 10 1 8 5 7 bits
        
        mock_input.side_effect = [
            "J", # Step 1
            "imm imm imm imm rd opcode", # Step 2
            "0 0000000000 0 00000000 00000 0000000 111", # Step 3: 7 parts (1 extra '111')
            "q", # Quit
            "q"
        ]
        
        with patch('sys.exit'):
             run_encoding_pipeline(engine, q)
             
        output = mock_stdout.getvalue()
        self.assertIn("(Extra)", output)
        # Encoding mode uses "Incorrect. (X/Y)"
        self.assertRegex(output, r"Incorrect\. \(\d+/\d+\)")

if __name__ == '__main__':
    unittest.main()
