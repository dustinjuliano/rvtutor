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
        
        # We need to capture output at each step.
        # Since run_encoding_pipeline runs all steps in a loop, we can provide all inputs
        # and then analyze the full output to see when "Givens:" appears.
        
        mock_input.side_effect = [
            "R",
            "funct7 rs2 rs1 funct3 rd opcode",
            "0000000 00010 00001 000 00011 0110011",
            "002081b3"
        ]
        
        run_encoding_pipeline(engine, q)
        output = mock_stdout.getvalue()
        
        # Split output by the interaction steps to analyze context for each step
        # Step 1 prompt: "What instruction type is"
        # Step 2 prompt: "What are the field names for instruction"
        # Step 3 prompt: "What are the binary values for each field"
        # Step 4 prompt: "What is the final 32-bit hex encoding"
        
        # We can locate these prompts and check the text immediately preceding them in the same "screen clearing" block.
        # Note: clear_screen() is called before each step.
        
        # Let's find the indices of the prompts
        idx_step1 = output.find("What instruction type is")
        idx_step2 = output.find("What are the field names for instruction")
        idx_step3 = output.find("What are the binary values for each field")
        idx_step4 = output.find("What is the final 32-bit hex encoding")
        
        self.assertNotEqual(idx_step1, -1)
        self.assertNotEqual(idx_step2, -1)
        self.assertNotEqual(idx_step3, -1)
        self.assertNotEqual(idx_step4, -1)
        
        # Extract the content for each step (approximate context check)
        # Content for Step 1 is from start to Step 1 prompt
        # Content for Step 2 is from Step 1 prompt to Step 2 prompt
        # ...
        
        # Actually, "Givens:" is printed inside display_context(), which clears screen first.
        # So "Givens:" should appear in the text block associated with Step 3 and Step 4, 
        # but NOT in the text block associated with Step 1 and Step 2.
        
        # Let's slice the output
        segment1 = output[:idx_step1]
        segment2 = output[idx_step1:idx_step2]
        segment3 = output[idx_step2:idx_step3]
        segment4 = output[idx_step3:idx_step4]
        
        # Verify absence in Step 1 & 2
        self.assertNotIn("Givens:", segment1, "Givens should not be in Step 1 context")
        self.assertNotIn("Givens:", segment2, "Givens should not be in Step 2 context")
        
        # Verify presence in Step 3 & 4
        # Note: segment3 ends at the PROMPT of step 3. But display_context is called BEFORE the prompt.
        # So the context for Step 3 lies in the segment between Step 2's completion and Step 3's prompt.
        # Wait, the segments above correspond to:
        # segment1: Header + Context for Step 1
        # segment2: Interaction of Step 1 + Header + Context for Step 2
        # segment3: Interaction of Step 2 + Header + Context for Step 3
        # segment4: Interaction of Step 3 + Header + Context for Step 4
        
        # So:
        # segment1 should NOT have Givens
        # segment2 should NOT have Givens (it validates Step 1, then prints context for Step 2)
        # segment3 SHOULD have Givens (it validates Step 2, then prints context for Step 3)
        # segment4 SHOULD have Givens (it validates Step 3, then prints context for Step 4)
        
        self.assertNotIn("Givens:", segment1)
        
        # segment2 contains the validation of Step 1 ("Correct."), then Clear Screen, then Context for Step 2.
        # We need to be careful. The "Givens:" string might appear if we are not strict about where.
        # But we know it shouldn't appear AT ALL in Step 2's context.
        # However, check if it appeared in Step 1's validation? No.
        
        # Let's verify strict absence in the text block for Step 2 context.
        # We can count occurrences?
        # Total "Givens:" count should be 2 (one for Step 3, one for Step 4).
        self.assertEqual(output.count("Givens:"), 2)
        
        # Let's verify location.
        first_givens = output.find("Givens:")
        second_givens = output.find("Givens:", first_givens + 1)
        
        # First "Givens:" must be AFTER Step 2 prompt (context for Step 3 is printed after Step 2 prompt is answered)
        self.assertGreater(first_givens, idx_step2)
        
        # Second "Givens:" must be AFTER Step 3 prompt
        self.assertGreater(second_givens, idx_step3)

if __name__ == '__main__':
    unittest.main()
