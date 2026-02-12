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
            self.assertIn("Correct. (1/1) (Type: R)", output) # Step 1 verification
            self.assertIn("Correct.", output) # Step 2 verification

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
            self.assertIn("Correct. (1/1) (Type: I)", output)
            self.assertIn("Correct.", output)

    @patch('builtins.input')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_main_bits_invalid_then_q(self, mock_stdout, mock_input):
        # Flow: Types (I), Mode (2), Step 1: Type (I), Step 2: Empty (repeat), Bad Answer, Continue (n), Types Exit (q)
        mock_input.side_effect = ["I", "2", "I", "", "not numbers", "n", "q"]
        
        with patch('engine.random.choice') as mock_choice:
            ins = Instruction("addi", "I", 0x13, 0x0)
            mock_choice.return_value = ins
            
            with self.assertRaises(SystemExit):
                main()
            
            output = mock_stdout.getvalue()
            self.assertIn("Incorrect.", output)
            self.assertIn("Expected:", output)

    @patch('builtins.input')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_encoding_pipeline(self, mock_stdout, mock_input):
        engine = QuizEngine()
        ins = Instruction("addi", "I", 0x13, 0x0)
        q = {"instruction": ins, "rs1": 1, "rs2": 0, "rd": 2, "imm": 10, "asm": "addi x2, x1, 10"}
        engine.current_q = q
        
        # Encoding Steps with one empty input for Step 1
        mock_input.side_effect = [
            "", "I", 
            "imm rs1 funct3 rd opcode",
            "000000001010 00001 000 00010 0010011",
            "00a08113"
        ]
        
        run_encoding_pipeline(engine, q)
        output = mock_stdout.getvalue()
        self.assertIn("Correct", output)

    @patch('builtins.input')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_main_multi_question_stats(self, mock_stdout, mock_input):
        # Flow: Types (ALL), Mode (2), 
        # Q1: Type (I), Bits (OK), Continue (y)
        # Q2: Type (I), Bits (Fail), Continue (n), Quit
        mock_input.side_effect = ["all", "2", "I", "12 5 3 5 7", "y", "I", "0 0 0 0 0", "n", "q"]
        
        with patch('engine.random.choice') as mock_choice:
            ins = Instruction("addi", "I", 0x13, 0x0)
            mock_choice.return_value = ins
            
            with self.assertRaises(SystemExit):
                main()
            
            output = mock_stdout.getvalue()
            # Accuracy check: 1/1+5/5 from first, 1/1+0/5 from second = 7/12 (58%)
            # Wait, points: 1+5 + 1+0 = 7. Total: 1+5 + 1+5 = 12.
            # 7/12 = 58.33% -> 58%
            self.assertIn("Accuracy: 7/12 (58%)", output)

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
            self.assertIn("Correct.", output)

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
        # S-type, fields: imm rs2 rs1 funct3 imm opcode
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
            "imm rs2 rs1 funct3 imm opcode",
            "0000000 00010 00001 010 01000 0100011",
            "0020a423"
        ]
        
        run_encoding_pipeline(engine, q)
        output = mock_stdout.getvalue()
        
        self.assertIn("Mode: Encoding", output)
        self.assertIn("sw x2, 8(x1)", output)
        self.assertIn("Correct. (1/1)", output) # Type
        self.assertIn("Correct. (6/6)", output) # Fields
        self.assertIn("Correct. (6/6)", output) # Binary
        self.assertIn("Correct! (1/1)", output) # Hex

    @patch('builtins.input')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_encoding_feedback_persistence(self, mock_stdout, mock_input):
        # Verify that screen does NOT clear after incorrect input in Encoding mode
        engine = QuizEngine()
        ins = Instruction("add", "R", 0x33, 0x0, 0x0)
        q = {"instruction": ins, "rs1":1, "rs2":2, "rd":3, "imm":0, "asm":"add x3, x1, x2"}
        engine.current_q = q
        
        # Step 2: Input 'bad' (fail) -> 'funct7 rs2 rs1 funct3 rd opcode' (pass)
        # We start at Step 1 inputs (Type) just to get to Step 2
        mock_input.side_effect = [
            "R", # Step 1: OK
            "bad input", # Step 2: Fail
            "funct7 rs2 rs1 funct3 rd opcode", # Step 2: Pass
            "q" # Quit at Step 3
        ]
        
        try:
            run_encoding_pipeline(engine, q)
        except SystemExit:
            pass
            
        output = mock_stdout.getvalue()
        
        # We expect "Incorrect." to appear
        self.assertIn("Incorrect.", output)
        
        # We expect the feedback to be visible
 
        
        # Count clear codes. 
        # 1 for Step 1 entry
        # 1 for Step 2 entry
        # 1 for Step 3 entry
        # Should be 3. If it cleared on error, it would be 4.
        # Note: clear_screen prints "\033[H\033[J" on non-Windows
        # assertCount might be tricky if we don't mock os.name, but test environment is likely POSIX-like
        # Better: check that "Incorrect" is followed by Prompt, NOT by "Mode: Encoding" (which implies header reprint)
        
        fail_idx = output.find("Incorrect.")
        header_idx = output.find("Mode: Encoding", fail_idx)
        
        # If header_idx is -1, it means header wasn't reprinted after failure (Good).
        # Or if it IS printed, it must be for the NEXT step.
        # But we pass Step 2 immediately after. So Step 3 header appears.
        # But between "Incorrect" and "What are the field names", there should NOT be a header.
        
        # Search for pattern: Incorrect -> Feedback -> What are the field names
        # VS Incorrect -> Clear -> Header -> What are the field names
        
        # We can simply count the number of times the Header appears.
        # It should appear exactly 3 times (Step 1, Step 2, Step 3).
        # If the screen cleared on the retry in Step 2, it would appear 4 times.
        self.assertEqual(output.count("Mode: Encoding"), 3)
        
        # Also verify the feedback text is present
        # With extended partial grading, "bad input" maps to field[0]="bad" -> "bad: ✗ (Expected: funct7)"
        self.assertIn("bad: ✗ (Expected: funct7)", output)

    @patch('builtins.input')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_recall_extra_fields(self, mock_stdout, mock_input):
        # User enters more fields than expected for sw (S-type)
        # S-Type has 6 fields. User enters 7.
        # Flow:
        # 1. Types (S)
        # 2. Mode (1)
        # 3. Step 1 (Type): S
        # 4. Step 2 (Fields): imm rs2 rs1 funct3 rs imm opcode (Extra)
        # 5. Continue? (n)
        # 6. Types: (q) -- wait, main loop breaks on 'n', so it goes back to Types input
        
        # main() structure:
        # while True (Types):
        #   input Types -> "S"
        #   while True (Mode):
        #     input Mode -> "1"
        #     while True (Quiz):
        #       Step 1: input Type -> "S"
        #       Step 2: input Fields -> "..."
        #       input Continue? -> "n" (breaks Quiz loop)
        #     (back in Mode loop)
        #     input Mode -> "q" (exit sys)
        
        # So inputs should be: "S", "1", "S", "fields...", "n", "q"
        mock_input.side_effect = ["S", "1", "S", "imm rs2 rs1 funct3 rs imm opcode", "n", "q", "q", "q"]
        
        with patch('engine.random.choice') as mock_choice:
            ins = Instruction("sw", "S", 0x23, 0x2)
            mock_choice.return_value = ins
            
            with self.assertRaises(SystemExit):
                main()
            
            output = mock_stdout.getvalue()
            # Verify no crash and expected error message for extra field
            # The 5th item (index 4) 'rs' is extra relative to standard S-type?
            # Wait, S-type: imm(0), rs2(1), rs1(2), funct3(3), imm(4), opcode(5).
            # User Input: imm(0), rs2(1), rs1(2), funct3(3), rs(4), imm(5), opcode(6).
            # index 4 is 'rs'. expected 'imm'.
            # index 5 is 'imm'. expected 'opcode'.
            # index 6 is 'opcode'. Unexpected (Extra).
            
            # The code prints "✗ (Extra)" for i >= len(correct_list) aka i >= 6.
            # So 'opcode' (index 6) should be marked as Extra.
            self.assertIn("opcode: ✗ (Extra)", output)

if __name__ == '__main__':
    unittest.main()
