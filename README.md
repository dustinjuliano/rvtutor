# RISC-V Tutor
A minimalist, robust tutoring system designed for high-speed active recall of RISC-V instruction layouts and binary encoding.

## Project Purpose
### Description
`rvtutor` is a command-line interface (CLI) application that helps students quiz themselves on how to manually encode RISC-V instructions. It provides an interactive, fast-paced environment to practice identifying instruction fields, bit-widths, and full 32-bit hex encoding, as this is what will be tested.

I produced this project because we have to recall this information in one of our courses and I needed an efficient way to learn this as quickly as possible. This is shared with classmates to help us all out.

### Motivation
- **Active Recall Integrity**: The system focuses on full active recall. It clears the screen between questions and enforces precise inputs, preventing visual hints from previous answers.
- **Speed & Efficiency**: Faster than traditional flashcards or manual pen-and-paper methods. By automating the validation and providing instant feedback, users can loop through dozens of instructions in minutes.
- **Superior to Chatbots**: Unlike AI tutoring cycles which often involve slow turn-based latency, `rvtutor` is a local, zero-latency tool designed specifically for this single repetitive task.

## Project Overview
The tutor supports six RISC-V instruction types: **R, I, S, B, U, J**.

### Features
- **Recall Mode**: Identify the exact order of fields (e.g., `opcode`, `rd`, `rs1`, etc.).
- **Bits Mode**: Memorize the bit-widths of every field in a specific instruction type.
- **Encoding Mode**: A rigorous 4-step pipeline driven by assembly:
  1. Identify Instruction Type
  2. Identify Field Names
  3. Convert Assembly to Binary Fields
  4. Final 32-bit Hex Synthesis
- **Partial Credit**: Get granular feedback on which specific fields you got right with expected values shown on failure.
- **Visual Clarity**: Screen clears before every question to maintain "recall integrity".

### Example Sessions
#### 1. Recall Mode (Demo of Partial Grading)
```text
Mode: Recall (Active Types: R, I)
--------------------
Instruction: ADD (R-Type)
Fields in order (q to quit): funct7 rs2 rs1 funct3 rd op
Incorrect. Points: 5/6
funct7: ✓ | rs2: ✓ | rs1: ✓ | funct3: ✓ | rd: ✓ | opcode: ✗

Accuracy: 5/6 (83%)
```

#### 2. Bits Mode (Field Widths)
```text
Mode: Bits (Active Types: I)
--------------------
Instruction: LW
Bit widths in order (space separated, q to quit): 12 5 3 5 7
Correct. (5/5)

Accuracy: 10/11 (90%)
```

#### 3. Encoding Mode
```text
Mode: Encoding
--------------------

sub x3, x1, x2

Givens:
  Opcode: 51
  Funct3: 0
  Funct7: 32

--------------------
What instruction type is `sub`?
Type (q to quit): R
Correct. (1/1)

What are the field names for instruction `sub` in order?
Fields (space separated, q to quit): funct7 rs2 rs1 funct3 rd opcode
Correct. (6/6)

What are the binary values for each field in `sub`?
Binary (space separated, q to quit): 0100000 00010 00001 000 00011 0110011
Correct. (6/6)

What is the final 32-bit hex encoding for `sub`?
Hex (q to quit): 402081B3
Correct! (1/1)
```

## Pedagogy Methodology
The tool employs a **scaffolded learning approach** combined with **active recall**:

1.  **Isolation of Variables**: By separating "Recall" (fields), "Bits" (widths), and "Encoding" (values), users master each component of an instruction separately before having to combine them.
2.  **Immediate Feedback Loops**: Mistakes are caught instantly at the granular level (e.g., getting just the opcode wrong), allowing for rapid correction of mental models.
3.  **Cognitive Load Management**: 
    - Random immediate values are restricted to **double digits (e.g., -99 to 99)**. This mimics the "small constants" optimization often found in real code but, more importantly, reduces the mental arithmetic burden so students can focus on the *encoding structure* rather than performing complex binary arithmetic in their heads.
4.  **Interleaving**: The default mode mixes different instruction types (R, I, S, etc.), preventing rote memorization of a single pattern and forcing users to discriminate between formats actively.

## Grading Methodology
The system uses a **point-per-item** partial grading system across all modes to provide granular feedback.

### Recall & Bits Modes
- **Points per Field**: You earn 1 point for every field name (Recall) or bit-width (Bits) correctly placed in the sequence.
- **Order Matters**: The sequence must match the architectural layout (e.g., MSB to LSB).
- **Feedback**: Provides a field-by-field breakdown (✓/✗) so you can identify exactly where your mental model differs from the RISC-V specification.

### Encoding Mode
Grading is split across the 4-step pipeline:
1. **Instruction Type**: 1 point for identifying the correct format (R, I, S, B, U, or J).
2. **Field Names**: Points equal to the number of fields in that instruction's layout (e.g., 6 points for R-type).
3. **Binary Fields**: Points equal to the number of fields; requires exact binary string matching for each component (e.g., `rs1`, `rs2`, `imm`, etc.).
4. **Hex Synthesis**: 1 point for the final 32-bit hex value (0x-prefixed or raw).

## How to Use It
### Prerequisites
- Python 3.6+

### Execution
Run the main script from the root directory:
```bash
python3 main.py
```

### Navigation
- When prompted for **Types**, enter e.g., `R, I` or just press ENTER for `all`.
- Use `q` to return to the previous menu.
- Use `n` at the "Continue?" prompt to change modes.

## Testing Methodology
The project maintains an exhaustive test suite of **50 tests** covering 100% of the core logic and semantic edge cases.

### Test Breakdown
- **Unit Tests (`test_utils.py`)**: Verifies bit manipulation, sign-extension, and 32-bit hex truncation.
- **Registry Tests (`test_riscv.py`)**: Ensures every instruction in the set is correctly defined and that bit-swizzlers (S/B/J types) handle boundaries and negative offsets accurately.
- **Engine Tests (`test_engine.py`)**: Exhaustive ground-truth verification for all instruction types and validation logic.
- **Integration Tests (`test_main.py`)**: Simulates full user sessions, including multi-question pacing, stat persistence, and error handling for invalid or empty inputs.

### Running Tests
```bash
python3 -m unittest discover tests
```

## Project Layout
- `main.py`: Interactive CLI entry point and quiz loop orchestration.
- `engine.py`: The core logic engine managing state, randomization, and validation.
- `riscv.py`: Instruction registry and bit-layout specifications.
- `utils.py`: Low-level bitwise utilities and formatting helpers.
- `tests/`: Comprehensive directory containing all 50 test cases.

## Test Coverage
The project includes a comprehensive test suite with **58 tests** covering 100% of the core engine logic, instruction variations, and user interface workflows. This ensures reliable grading, accurate assembly formatting, and robust error handling across all modes.

## AI Disclosure
100% of the code in this repository was written using **Google Antigravity** and Gemini 3. However, the program design, feature requirements, and iterative refinements were made manually through quite a substantial number of rounds of my own feedback.
