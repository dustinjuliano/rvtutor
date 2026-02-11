import unittest
from unittest.mock import patch, MagicMock
import io
import sys
from main import main, run_encoding_pipeline
from engine import QuizEngine
from riscv import Instruction

class TestMain(unittest.TestCase):
    @patch('builtins.input')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_main_recall_flow(self, mock_stdout, mock_input):
        # Flow: Types (ALL), Mode (1), Answer, Continue (n), Types Exit (q)
        # Note: Enter for ALL = ""
        mock_input.side_effect = ["", "1", "funct7 rs2 rs1 funct3 rd opcode", "n", "q"]
        
        with patch('engine.random.choice') as mock_choice:
            ins = Instruction("add", "R", 0x33, 0x0, 0x0)
            mock_choice.return_value = ins
            
            with self.assertRaises(SystemExit):
                main()
            
            output = mock_stdout.getvalue()
            self.assertIn("Welcome to rvtutor", output)
            self.assertIn("Correct.", output)

    @patch('builtins.input')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_main_bits_flow(self, mock_stdout, mock_input):
        # Flow: Types (I), Mode (2), Answer, Continue (n), Types Exit (q)
        mock_input.side_effect = ["I", "2", "12 5 3 5 7", "n", "q"]
        
        with patch('engine.random.choice') as mock_choice:
            ins = Instruction("addi", "I", 0x13, 0x0)
            mock_choice.return_value = ins
            
            with self.assertRaises(SystemExit):
                main()
            
            output = mock_stdout.getvalue()
            self.assertIn("Correct.", output)

    @patch('builtins.input')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_main_bits_invalid_then_q(self, mock_stdout, mock_input):
        # Flow: Types (I), Mode (2), Empty (repeat), Bad Answer, Continue (n), Types Exit (q)
        mock_input.side_effect = ["I", "2", "", "not numbers", "n", "q"]
        
        with patch('engine.random.choice') as mock_choice:
            ins = Instruction("addi", "I", 0x13, 0x0)
            mock_choice.return_value = ins
            
            with self.assertRaises(SystemExit):
                main()
            
            output = mock_stdout.getvalue()
            self.assertIn("Incorrect.", output)

    @patch('builtins.input')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_encoding_pipeline(self, mock_stdout, mock_input):
        engine = QuizEngine()
        ins = Instruction("addi", "I", 0x13, 0x0)
        q = {"instruction": ins, "rs1": 1, "rs2": 0, "rd": 2, "imm": 10}
        engine.current_q = q
        
        # Encoding Steps with one empty input for Step 1
        mock_input.side_effect = [
            "", "I", 
            "imm rs1 funct3 rd opcode",
            "000000001010 00001 000 00010 0010011",
            "00A08113"
        ]
        
        run_encoding_pipeline(engine, q)
        output = mock_stdout.getvalue()
        self.assertIn("Correct", output)

    @patch('builtins.input')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_main_multi_question_stats(self, mock_stdout, mock_input):
        # Flow: Types (ALL), Mode (2), Ans1 (OK), Continue (y), Ans2 (Fail), Continue (n), Quit
        mock_input.side_effect = ["all", "2", "12 5 3 5 7", "y", "0 0 0 0 0", "n", "q"]
        
        with patch('engine.random.choice') as mock_choice:
            ins = Instruction("addi", "I", 0x13, 0x0)
            mock_choice.return_value = ins
            
            with self.assertRaises(SystemExit):
                main()
            
            output = mock_stdout.getvalue()
            # Accuracy check: 5/5 from first, 0/5 from second = 5/10 (50%)
            self.assertIn("Accuracy: 5/10 (50%)", output)

    @patch('builtins.input')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_main_case_insensitivity(self, mock_stdout, mock_input):
        # Flow: Types (r,i), Mode (1), Mixed-Case Answer, Continue (n), Types Exit (q)
        mock_input.side_effect = ["R,i", "1", "FUNCT7 rs2 RS1 funct3 rd OPCODE", "n", "q"]
        
        with patch('engine.random.choice') as mock_choice:
            ins = Instruction("add", "R", 0x33, 0x0, 0x0)
            mock_choice.return_value = ins
            
            with self.assertRaises(SystemExit):
                main()
            
            output = mock_stdout.getvalue()
            self.assertIn("Correct.", output)

    @patch('builtins.input')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_main_mode_switch(self, mock_stdout, mock_input):
        # Flow: Types (all), Mode (1), Ans, Continue (n) -> Mode (2), Ans, Continue (n) -> Mode Exit (q) -> Types Exit (q)
        mock_input.side_effect = ["all", "1", "funct7 rs2 rs1 funct3 rd opcode", "n", "2", "12 5 3 5 7", "n", "q", "q"]
        
        with patch('engine.random.choice') as mock_choice:
            ins_r = Instruction("add", "R", 0x33, 0x0, 0x0)
            ins_i = Instruction("addi", "I", 0x13, 0x0)
            mock_choice.side_effect = [ins_r, ins_i]
            
            with self.assertRaises(SystemExit):
                main()
            
            output = mock_stdout.getvalue()
            self.assertIn("Mode: Recall", output)
            self.assertIn("Mode: Bits", output)

    @patch('builtins.input')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_main_encoding_quit_midway(self, mock_stdout, mock_input):
        # Flow: Types (all), Mode (3), Step 1 (q), Mode Exit (q), Types Exit (q)
        mock_input.side_effect = ["all", "3", "q", "q", "q"]
        with patch('engine.random.choice') as mock_choice:
            mock_choice.return_value = Instruction("add", "R", 0x33, 0x0, 0x0)
            with self.assertRaises(SystemExit):
                main()
            self.assertIn("Mode: Encoding", mock_stdout.getvalue())

    @patch('builtins.input')
    def test_config_errors(self, mock_input):
        mock_input.side_effect = ["UNK", "q"]
        with patch('sys.stdout', new_callable=io.StringIO):
            with self.assertRaises(SystemExit):
                main()

if __name__ == '__main__':
    unittest.main()
