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
        # Flow: Types (ALL), Mode (1), 
        # Step 1: Type (R), 
        # Step 2: Fields (funct7 rs2 rs1 funct3 rd opcode), 
        # Continue (n), Types Exit (q)
        # Note: Enter for ALL = ""
        mock_input.side_effect = ["", "1", "R", "funct7 rs2 rs1 funct3 rd opcode", "n", "q"]
        
        with patch('engine.random.choice') as mock_choice:
            ins = Instruction("add", "R", 0x33, 0x0, 0x0)
            mock_choice.return_value = ins
            
            with self.assertRaises(SystemExit):
                main()
            
            output = mock_stdout.getvalue()
            self.assertIn("Welcome to rvtutor", output)

    @patch('builtins.input')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_main_bits_flow(self, mock_stdout, mock_input):
        # Flow: Types (I), Mode (2), Step 1: Type (I), Step 2: Bits (12 5 3 5 7), Continue (n), Types Exit (q)
        mock_input.side_effect = ["I", "2", "I", "12 5 3 5 7", "n", "q"]
        
        with patch('engine.random.choice') as mock_choice:
            ins = Instruction("addi", "I", 0x13, 0x0)
            mock_choice.return_value = ins
            
            with self.assertRaises(SystemExit):
                main()
            
            output = mock_stdout.getvalue()
            self.assertIn("Mode: Bits", output)

    @patch('builtins.input')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_main_bits_invalid_then_q(self, mock_stdout, mock_input):
        # Flow: Types (I), Mode (2), Step 1: Type (I), Step 2: Bad Answer, Continue (n), Types Exit (q)
        mock_input.side_effect = ["I", "2", "I", "not numbers", "n", "q", "q", "q"]
        
        with patch('engine.random.choice') as mock_choice:
            ins = Instruction("addi", "I", 0x13, 0x0)
            mock_choice.return_value = ins
            
            with self.assertRaises(SystemExit):
                main()
            
            output = mock_stdout.getvalue()
            self.assertIn("Expected:", output)

    @patch('builtins.input')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_encoding_pipeline(self, mock_stdout, mock_input):
        engine = QuizEngine()
        ins = Instruction("addi", "I", 0x13, 0x0)
        q = {"instruction": ins, "rs1": 1, "rs2": 0, "rd": 2, "imm": 10, "asm": "addi x2, x1, 10"}
        engine.current_q = q
        
        # Encoding Steps (single-attempt)
        mock_input.side_effect = [
            "I", 
            "imm[11:0] rs1 funct3 rd opcode",
            "000000001010 00001 000 00010 0010011",
            "00a08113"
        ]
        
        run_encoding_pipeline(engine, q)
        output = mock_stdout.getvalue()
        self.assertIn("Mode: Encoding", output)

    @patch('builtins.input')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_main_multi_question_stats(self, mock_stdout, mock_input):
        # Flow: Types (ALL), Mode (2), 
        # Q1: Type (I), Bits (OK), Continue (y)
        # Q2: Type (I), Bits (Fail), Continue (n), Quit
        mock_input.side_effect = ["all", "2", "I", "12 5 3 5 7", "y", "I", "0 0 0 0 0", "n", "q", "q", "q"]
        
        with patch('engine.random.choice') as mock_choice:
            ins = Instruction("addi", "I", 0x13, 0x0)
            mock_choice.return_value = ins
            
            with self.assertRaises(SystemExit):
                main()
            
            output = mock_stdout.getvalue()
            # Accuracy check: 1/1+5/5 from first, 1/1+0/5 from second = 7/12 (58%)
            self.assertIn("Accuracy: 7.00/12.00 (58.0%)", output)

    @patch('builtins.input')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_main_case_insensitivity(self, mock_stdout, mock_input):
        # Flow: Types (r,i), Mode (1), Answer Type (r), Mixed-Case Fields, Continue (n), Types Exit (q)
        mock_input.side_effect = ["R,i", "1", "r", "FUNCT7 rs2 RS1 funct3 rd OPCODE", "n", "q"]
        
        with patch('engine.random.choice') as mock_choice:
            ins = Instruction("add", "R", 0x33, 0x0, 0x0)
            mock_choice.return_value = ins
            
            with self.assertRaises(SystemExit):
                main()
            
            output = mock_stdout.getvalue()
            self.assertIn("Mode: Recall", output)

    @patch('builtins.input')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_main_mode_switch(self, mock_stdout, mock_input):
        # Flow: Types (all), Mode (1), Type(R), Fields(OK), Continue (n) -> Mode (2), Type(I), Bits(OK), Continue (n) -> Mode Exit (q) -> Types Exit (q)
        mock_input.side_effect = ["all", "1", "R", "funct7 rs2 rs1 funct3 rd opcode", "n", "2", "I", "12 5 3 5 7", "n", "q", "q"]
        
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

    @patch('builtins.input')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_encoding_flow_consistency(self, mock_stdout, mock_input):
        # Verify full flow for SW x2, 8(x1)
        # S-type, fields: imm[11:5] rs2 rs1 funct3 imm[4:0] opcode
        # rs1=1, rs2=2, imm=8 -> 0x0020A423
        engine = QuizEngine()
        ins = Instruction("sw", "S", 0x23, 0x2)
        q = {
            "instruction": ins, 
            "rs1": 1, "rs2": 2, "rd": 0, "imm": 8,
            "asm": "sw x2, 8(x1)"
        }
        engine.current_q = q
        
        # Inputs:
        # 1. Type: S
        # 2. Fields: imm rs2 rs1 funct3 imm opcode
        # 3. Binary: imm[11:5] rs2 rs1 funct3 imm[4:0] opcode
        #    8 = 000...001000
        #    imm[11:5]=0000000, rs2=00010, rs1=00001, f3=010, imm[4:0]=01000, op=0100011
        #    0000000 00010 00001 010 01000 0100011
        # 4. Hex: 0020A423
        
        mock_input.side_effect = [
            "S",
            "imm[11:5] rs2 rs1 funct3 imm[4:0] opcode",
            "0000000 00010 00001 010 01000 0100011",
            "0020a423"
        ]
        
        run_encoding_pipeline(engine, q)
        output = mock_stdout.getvalue()
        
        self.assertIn("Mode: Encoding", output)
        self.assertIn("sw x2, 8(x1)", output)

    @patch('builtins.input')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_encoding_feedback_persistence(self, mock_stdout, mock_input):
        # Verify that screen does NOT clear after incorrect input in Encoding mode
        engine = QuizEngine()
        ins = Instruction("add", "R", 0x33, 0x0, 0x0)
        q = {"instruction": ins, "rs1":1, "rs2":2, "rd":3, "imm":0, "asm":"add x3, x1, x2"}
        engine.current_q = q
        
        # Single-attempt: bad input -> feedback shown, then moves to Step 3
        mock_input.side_effect = [
            "R", # Step 1: OK
            "bad input", # Step 2: Fail (single-attempt, feedback shown)
            "q" # Quit at Step 3
        ]
        
        try:
            run_encoding_pipeline(engine, q)
        except SystemExit:
            pass
            
        output = mock_stdout.getvalue()
        
        # Verify feedback is shown for bad input
        self.assertIn("bad: ✗ (Expected: funct7)", output)

    @patch('builtins.input')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_recall_extra_fields(self, mock_stdout, mock_input):
        # User enters more fields than expected for sw (S-type)
        # S-Type has 6 fields. User enters 7.
        mock_input.side_effect = ["S", "1", "S", "imm[11:5] rs2 rs1 funct3 rs imm[4:0] opcode", "n", "q", "q", "q"]
        
        with patch('engine.random.choice') as mock_choice:
            ins = Instruction("sw", "S", 0x23, 0x2)
            mock_choice.return_value = ins
            
            with self.assertRaises(SystemExit):
                main()
            
            output = mock_stdout.getvalue()
            self.assertIn("opcode: ✗ (Extra)", output)

if __name__ == '__main__':
    unittest.main()
