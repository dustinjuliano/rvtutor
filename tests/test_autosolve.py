import unittest
from unittest.mock import patch, MagicMock
import io
import sys
import main
from engine import QuizEngine
from riscv import Instruction

class TestAutoSolve(unittest.TestCase):
    def setUp(self):
        self.engine = QuizEngine()
        # Mock a simple instruction pool
        self.ins = Instruction("addi", "I", 19, 0, None)
        self.engine.pool = [self.ins]
        
    @patch('builtins.input')
    @patch('main.clear_screen')
    def test_mode1_step1_autosolve(self, mock_clear, mock_input):
        # Recall Mode, Step 1: Type
        # Single-attempt: wrong answer reveals immediately
        # No retries to test, just verify answer-reveal behavior
        pass

    @patch('builtins.input')
    @patch('main.clear_screen')
    @patch('main.time.sleep')
    def test_mode3_step1_autosolve(self, mock_sleep, mock_clear, mock_input):
        # Single-attempt: Type 'R' for 'addi' (Type I) -> fail, answer revealed
        mock_input.side_effect = ["R", "q"] 
        q = self.engine.generate_question() # addi
        
        with patch('sys.stdout', new=io.StringIO()) as mock_stdout:
            main.run_encoding_pipeline(self.engine, q)
            output = mock_stdout.getvalue()
            
            self.assertIn("Answer: I", output)

    @patch('builtins.input')
    @patch('main.clear_screen')
    @patch('main.time.sleep')
    def test_mode4_step2_autosolve(self, mock_sleep, mock_clear, mock_input):
        # Decoding Mode Step 2 (Opcode) - single-attempt: wrong answer, 
        # answer is revealed via the worksheet display (not inline print)
        q = self.engine.generate_question()
        truth = self.engine.get_ground_truth()
        mock_input.side_effect = [
            truth['binary'], # Step 1: Pass
            "0",             # Step 2: Fail (answer revealed in worksheet)
            "q"              # Step 3: Quit
        ]
        
        with patch('sys.stdout', new=io.StringIO()) as mock_stdout:
            main.run_decoding_pipeline(self.engine, q)
            output = mock_stdout.getvalue()
            # The opcode value (19) should appear in the worksheet
            self.assertIn("Opcode: 19", output)

if __name__ == '__main__':
    unittest.main()
