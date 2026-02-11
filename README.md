# RISC-V Tutor
A minimalist, robust tutoring system designed for high-speed active recall of RISC-V instruction layouts and binary encoding.

## Project Purpose
### Description
`rvtutor` is a command-line interface (CLI) application that helps students quiz themselves on how to manually encode RISC-V instructions. It provides an interactive, fast-paced environment to practice identifying instruction fields, bit-widths, and full 32-bit hex encoding, as this is what will be tested.

### Motivation
- **Active Recall Integrity**: The system focuses on full active recall. It clears the screen between questions and enforces precise inputs, preventing visual hints from previous answers.
- **Speed & Efficiency**: Faster than traditional flashcards or manual pen-and-paper methods. By automating the validation and providing instant feedback, users can loop through dozens of instructions in minutes.
- **Superior to Chatbots**: Unlike AI tutoring cycles which often involve slow turn-based latency, `rvtutor` is a local, zero-latency tool designed specifically for this single repetitive task.

## Project Overview
The tutor supports six RISC-V instruction types: **R, I, S, B, U, J**.

### Features
- **Recall Mode**: Identify the exact order of fields (e.g., `opcode`, `rd`, `rs1`, etc.).
- **Bits Mode**: Memorize the bit-widths of every field in a specific instruction type.
- **Encoding Mode**: A rigorous 4-step pipeline:
  1. Identify Instruction Type
  2. Identify Field Names
  3. Convert Values to Binary Fields
  4. Final 32-bit Hex Synthesis
- **Partial Credit**: Get granular feedback on which specific fields you got right.
- **Global Stats**: Real-time accuracy tracking (`Points / Total Possible`).
- **Standardized Navigation**: Use `q` at any prompt to go back or quit.

### Example Sessions
#### 1. Recall Mode (Partial Correctness)
```text
Mode: Recall (Active Types: R, I)
--------------------
Instruction: ADD (R-Type)
Fields in order (q to quit): funct7 rs2 rs1 funct3 rd op
Incorrect. Points: 5/6
funct7: ✓ | rs2: ✓ | rs1: ✓ | funct3: ✓ | rd: ✓ | opcode: ✗

Global Accuracy: 5/6 (83%)
```

#### 2. Bits Mode (Field Widths)
```text
Mode: Bits (Active Types: I)
--------------------
Instruction: LW
Bit widths in order (space separated, q to quit): 12 5 3 5 7
Correct. (5/5)

Global Accuracy: 10/11 (90%)
```

#### 3. Encoding Mode (4-Step Pipeline)
```text
Mode: Encoding (Active Types: R)
--------------------
Encode: SUB
1. Identify Type (q to quit): R
Correct.

2. Enter Field Names (q to quit): funct7 rs2 rs1 funct3 rd opcode
Correct. (6/6)

Values: rs1=1, rs2=2, rd=3, imm=0
3. Binary for each field (q to quit): 0100000 00010 00001 000 00011 0110011
Correct. (6/6)

4. Full Hex (q to quit): 402081B3
Correct!

Global Accuracy: 24/25 (96%)
```

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

## AI Disclosure
100% of the code in this repository was written using **Google Antigravity**. However, the program design, feature requirements, and iterative refinements were made manually through numerous rounds of feedback.
