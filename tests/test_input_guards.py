
import unittest
from unittest.mock import patch
import io
import sys
import main
from main import main as main_func, run_encoding_pipeline
from engine import QuizEngine
from riscv import Instruction

class TestInputGuards(unittest.TestCase):
    
    @patch('builtins.input')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_mode_1_recall_extra_fields(self, mock_stdout, mock_input):
        """Mode 1 (Recall): Verify extra fields are handled gracefully."""
        # Single-attempt: extra field -> feedback shown immediately, no retry
        mock_input.side_effect = ["R", "1", "R", "funct7 rs2 rs1 funct3 rd opcode extra", "n", "q", "q"]
        
        with patch('engine.random.choice') as mock_choice:
            ins = Instruction("add", "R", 0x33, 0x0, 0x0)
            mock_choice.return_value = ins
            
            with self.assertRaises(SystemExit):
                main_func()
            
            output = mock_stdout.getvalue()
            self.assertIn("extra: ✗ (Extra)", output)
            self.assertNotIn("IndexError", output)

    @patch('builtins.input')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_mode_2_bits_extra_fields(self, mock_stdout, mock_input):
        """Mode 2 (Bits): Verify extra fields are handled gracefully."""
        # Single-attempt: extra bit -> feedback shown immediately, no retry
        mock_input.side_effect = ["I", "2", "I", "12 5 3 5 7 99", "n", "q", "q"]
        
        with patch('engine.random.choice') as mock_choice:
            ins = Instruction("addi", "I", 0x13, 0x0)
            mock_choice.return_value = ins
            
            with self.assertRaises(SystemExit):
                main_func()
            
            output = mock_stdout.getvalue()
            self.assertIn("(Extra)", output)

    @patch('builtins.input')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_mode_3_step_2_fields_extra(self, mock_stdout, mock_input):
        """Mode 3 (Encoding) Step 2: Verify extra fields are handled gracefully."""
        engine = QuizEngine()
        ins = Instruction("sub", "R", 0x33, 0x0, 0x20)
        q = {"instruction": ins, "rs1": 1, "rs2": 2, "rd": 3, "imm": 0, "asm": "sub x3, x1, x2"}
        engine.current_q = q
        
        mock_input.side_effect = [
            "R", # Step 1: Type
            "funct7 rs2 rs1 funct3 rd opcode extra", # Step 2: Extra (single-attempt)
            "q", # Step 3: Quit
        ]
        
        with patch('sys.exit'):
             run_encoding_pipeline(engine, q)
             
        output = mock_stdout.getvalue()
        self.assertIn("extra: ✗ (Extra)", output)

    @patch('builtins.input')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_mode_3_step_3_binary_extra(self, mock_stdout, mock_input):
        """Mode 3 (Encoding) Step 3: Verify extra binary fields are handled gracefully."""
        engine = QuizEngine()
        ins = Instruction("jal", "J", 0x6F)
        q = {"instruction": ins, "rd": 1, "imm": 4, "rs1":0, "rs2":0, "asm": "jal x1, 4"}
        engine.current_q = q
        
        mock_input.side_effect = [
            "J", # Step 1
            "imm[20] imm[10:1] imm[11] imm[19:12] rd opcode", # Step 2
            "0 0000000000 0 00000000 00000 0000000 111", # Step 3: Extra (single-attempt)
            "q", # Step 4: Quit
        ]
        
        with patch('sys.exit'):
             run_encoding_pipeline(engine, q)
             
        output = mock_stdout.getvalue()
        self.assertIn("(Extra)", output)

if __name__ == '__main__':
    unittest.main()
