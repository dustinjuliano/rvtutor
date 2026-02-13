"""
RISC-V Tutor - CLI Interface
Recall Integrity: Screen Clearing & Question Pacing
"""
import sys
import os
import re
import random
import time
from engine import QuizEngine
from riscv import LAYOUTS, Instruction
from typing import Dict, Tuple, List



def clear_screen():
    """Clears the console screen for active recall."""
    if os.name == 'nt':
        os.system('cls')
    else:
        # Cross-platform way to clear using ANSI or system command
        print("\033[H\033[J", end="")

def validate_asm_strict(user_input: str, target_ins: Instruction, target_vals: Dict) -> Tuple[bool, str]:
    """
    Validates assembly input using strict regex patterns.
    Returns (is_correct, feedback_message).
    """
    # Normalize input: trim and display single spaces (keep commas/parens)
    u = " ".join(user_input.split())
    
    # Define regex patterns
    patterns = {
        'R': r"^(\w+)\s+(x\d+),\s+(x\d+),\s+(x\d+)$",
        'I': r"^(\w+)\s+(x\d+),\s+(x\d+),\s+(-?\d+)$",
        'S': r"^(\w+)\s+(x\d+),\s+(-?\d+)\((x\d+)\)$",
        'B': r"^(\w+)\s+(x\d+),\s+(x\d+),\s+(-?\d+)$",
        'U': r"^(\w+)\s+(x\d+),\s+(-?\d+)$",
        'J': r"^(\w+)\s+(x\d+),\s+(-?\d+)$"
    }
    
    # I-Type Load variant (e.g., lw x1, 4(x2))
    if target_ins.type == 'I' and target_ins.name in ['lw', 'lb', 'lh', 'lbu', 'lhu']:
        pattern = r"^(\w+)\s+(x\d+),\s+(-?\d+)\((x\d+)\)$"
    else:
        pattern = patterns.get(target_ins.type)
        
    if not pattern:
        return False, "Internal Error: No pattern for type"

    match = re.match(pattern, u, re.IGNORECASE)
    if not match:
        # Construct expected format example
        ex = "???"
        if target_ins.type == 'R': ex = "add x1, x2, x3"
        elif target_ins.type == 'S': ex = "sw x1, 4(x2)"
        elif target_ins.type == 'B': ex = "beq x1, x2, -4"
        elif target_ins.type == 'U': ex = "lui x1, 10"
        elif target_ins.type == 'J': ex = "jal x1, 4"
        elif target_ins.type == 'I' and target_ins.name == 'lw': ex = "lw x1, 4(x2)"
        elif target_ins.type == 'I': ex = "addi x1, x2, 10"
        return False, f"Syntax Error. Expected format like: {ex}"

    groups = match.groups()
    mnemonic = groups[0].lower()
    
    # 1. Mnemonic Check
    if mnemonic != target_ins.name:
        return False, f"Incorrect Mnemonic. Expected: {target_ins.name}"

    # Extract parsed values
    regs = {}
    imm_val = None
    
    # Map regex groups to logical fields based on type
    try:
        if target_ins.type == 'R':
            # regex: (mnemonic), (rd), (rs1), (rs2) -> indices 0, 1, 2, 3
            regs['rd'] = int(groups[1][1:])
            regs['rs1'] = int(groups[2][1:])
            regs['rs2'] = int(groups[3][1:])
            
        elif target_ins.type == 'I':
            if target_ins.name in ['lw', 'lb', 'lh', 'lbu', 'lhu']:
                # lw rd, imm(rs1) -> groups: mnem, rd, imm, rs1
                regs['rd'] = int(groups[1][1:])
                imm_val = int(groups[2])
                regs['rs1'] = int(groups[3][1:])
            else:
                # addi rd, rs1, imm -> groups: mnem, rd, rs1, imm
                regs['rd'] = int(groups[1][1:])
                regs['rs1'] = int(groups[2][1:])
                imm_val = int(groups[3])
                
        elif target_ins.type == 'S':
            # sw rs2, imm(rs1) -> groups: mnem, rs2, imm, rs1
            regs['rs2'] = int(groups[1][1:])
            imm_val = int(groups[2])
            regs['rs1'] = int(groups[3][1:])
            
        elif target_ins.type == 'B':
            # beq rs1, rs2, imm -> groups: mnem, rs1, rs2, imm
            regs['rs1'] = int(groups[1][1:])
            regs['rs2'] = int(groups[2][1:])
            imm_val = int(groups[3])
            
        elif target_ins.type == 'U':
            # lui rd, imm -> groups: mnem, rd, imm
            regs['rd'] = int(groups[1][1:])
            imm_val = int(groups[2])
            
        elif target_ins.type == 'J':
            # jal rd, imm -> groups: mnem, rd, imm
            regs['rd'] = int(groups[1][1:])
            imm_val = int(groups[2])
            
    except ValueError:
        return False, "Error parsing integer values."

    # 2. Register Checks
    for r_name, r_val in regs.items():
        if r_val != target_vals[r_name]:
            return False, f"Incorrect register for {r_name}. Got x{r_val}, expected x{target_vals[r_name]}."

    # 3. Immediate Check
    if imm_val is not None:
        if imm_val != target_vals['imm']:
             return False, f"Incorrect Immediate. Got {imm_val}, expected {target_vals['imm']}. (Check un-swizzling!)"

    return True, "Correct."

def run_decoding_pipeline(engine, q):
    """Refined 7-Step Decoding Workflow with Horizontal UI and Strict Grading."""
    engine.current_q = q
    ins = q["instruction"]
    truth = engine.get_ground_truth()
    
    # Track stats for THIS instruction to show session accuracy
    session_points = 0.0
    session_total = 0.0
    
    def record_session(pts, tot):
        nonlocal session_points, session_total
        session_points = round(session_points + pts, 4)
        session_total = round(session_total + tot, 4)
        engine.record_stats(pts, tot)

    # --- Reference Table Generation ---
    distractors_by_op = {}
    for d in engine.pool:
        if d.op != ins.op:
            if d.op not in distractors_by_op: distractors_by_op[d.op] = []
            distractors_by_op[d.op].append(d)
    
    available_ops = list(distractors_by_op.keys())
    num_distractors = min(5, len(available_ops))
    selected_ops = random.sample(available_ops, num_distractors)
    selected_distractors = [random.choice(distractors_by_op[op]) for op in selected_ops]
    
    def fmt_row(i):
        f3 = str(i.f3) if i.f3 is not None else "-"
        f7 = str(i.f7) if i.f7 is not None else "-"
        return (i.name, i.op, f3, f7, i.type)
    
    table_rows = [fmt_row(ins)] + [fmt_row(d) for d in selected_distractors]
    random.shuffle(table_rows)
    
    def print_ref_table(filter_type=None, filter_op=None):
        print("Reference Table:")
        print(f"{'Instruction':<12} | {'opcode':<8} | {'funct3':<8} | {'funct7':<8}")
        print("-" * 46)
        for row in table_rows:
            if filter_type and row[4] != filter_type: continue
            if filter_op is not None and row[1] != filter_op: continue
            print(f"{row[0]:<12} | {row[1]:<8} | {row[2]:<8} | {row[3]:<8}")

    def check_quit(s):
        if s.lower() in ['q', 'quit']: return True
        return False

    nibble_status = ["?"] * 8
    nibble_bins = ["????"] * 8

    # Solving State for Worksheet
    field_layouts = LAYOUTS[ins.type] # MSB to LSB
    num_fields = len(field_layouts)
    # State per field slot
    solved_names = ["?"] * num_fields
    solved_vals = ["-"] * num_fields
    status_icons = ["?"] * num_fields

    # Persistent status log (survives screen clears)
    status_log = []

    user_bin = "0" * 32

    def display_worksheet(step_name, show_bin=False, show_op=False, show_type=False, show_fields=False, show_vals=False, show_nibbles=False, show_asm=False):
        clear_screen()
        print(f"Mode: Decoding - {step_name}")
        # Successively build ref table focus
        ref_filter_type = ins.type if show_type else None
        ref_filter_op = ins.op if show_op else None
        print_ref_table(filter_type=ref_filter_type, filter_op=ref_filter_op)
        print()
        
        # Hex alignment
        h_row = "Hex:    "
        for h in truth['hex']: h_row += f"{h:<5}"
        print(h_row)
        
        if show_nibbles:
            s_row = "Status: "
            b_row = "Binary: "
            for i in range(8):
                s_row += f"{nibble_status[i]:<5}"
                b_row += f"{nibble_bins[i]:<5}"
            print(b_row)
            print(s_row)
        elif show_bin: 
            # Show formatted binary (nibbles)
            b_str = "Binary: "
            for i in range(8): b_str += f"{user_bin[i*4:(i+1)*4]} "
            print(b_str)

        if show_op:    print(f"Opcode: {ins.op}")
        if show_type:  print(f"Type:   {ins.type}")

        if show_fields:
            print("\nProgress:")
            # Calculate column widths
            widths = []
            for i in range(num_fields):
                name_len = len(solved_names[i])
                val_len = len(solved_vals[i]) if show_vals else 1
                widths.append(max(name_len, val_len, 5) + 2)
            
            s_row = "Status: "
            f_row = "Field:  "
            v_row = "Value:  "
            for i in range(num_fields):
                s_row += f"{status_icons[i]:^{widths[i]}}"
                f_row += f"{solved_names[i]:^{widths[i]}}"
                v_row += f"{solved_vals[i]:^{widths[i]}}"
            
            print(f_row)
            if show_vals: print(v_row)
            print(s_row)
        
        # Persistent log: show last 3 entries
        if status_log:
            print("\nLog (recent):")
            for entry in status_log[-3:]:
                print(f"  {entry}")

        if show_asm:
            print(f"\nAssembly: {q['asm']}")

    # --- Step 1: Hex to Binary ---
    display_worksheet("Step 1: Hex to Binary", show_nibbles=True)
    raw_inp = input("\nConvert Hex to Binary (32 bits):\nPress 'q' to quit to main menu.\n> ").strip()
    if check_quit(raw_inp): return False

    inp = re.sub(r'[^01]', '', raw_inp)
    if len(inp) == 32:
        for i in range(8):
            u_nib = inp[i*4:(i+1)*4]
            t_nib = truth['binary'][i*4:(i+1)*4]
            nibble_bins[i] = u_nib
            if u_nib == t_nib:
                nibble_status[i] = "✓"
            else:
                nibble_status[i] = "✗"
        correct_nibbles = sum(1 for s in nibble_status if s == "✓")
        record_session(correct_nibbles / 8.0, 1)
        if correct_nibbles == 8:
            user_bin = inp
            status_log.append("Step 1: ✓ Binary correct")
        else:
            for i in range(8):
                nibble_bins[i] = truth['binary'][i*4:(i+1)*4]
                nibble_status[i] = "✓" if nibble_status[i] == "✓" else "✗"
            user_bin = truth['binary']
            status_log.append(f"Step 1: ✗ Binary {correct_nibbles}/8 nibbles correct")
    else:
        # Wrong length → 0 points, reveal all correct nibbles
        record_session(0, 1)
        for i in range(8):
            nibble_bins[i] = truth['binary'][i*4:(i+1)*4]
            nibble_status[i] = "✗"
        user_bin = truth['binary']
        status_log.append("Step 1: ✗ Invalid input (need exactly 32 binary digits)")

    display_worksheet("Step 1: Hex to Binary", show_nibbles=True)

    # --- Step 2: Opcode ---
    display_worksheet("Step 2: Opcode", show_bin=True)
    inp = input("\nWhat is the opcode in decimal?\nPress 'q' to quit to main menu.\n> ").strip()
    if check_quit(inp): return False

    try:
        if int(inp) == ins.op:
            record_session(1, 1)
            status_log.append("Step 2: ✓ Opcode correct")
        else:
            record_session(0, 1)
            status_log.append(f"Step 2: ✗ Opcode was {ins.op}, got {inp}")
    except:
        record_session(0, 1)
        status_log.append(f"Step 2: ✗ Opcode was {ins.op}, got '{inp}'")

    # --- Step 3: Type ---
    display_worksheet("Step 3: Instruction Type", show_bin=True, show_op=True)
    inp = input("\nIdentify the Type (R, I, S, B, U, J):\nPress 'q' to quit to main menu.\n> ").strip().upper()
    if check_quit(inp): return False

    if inp == ins.type:
        record_session(1, 1)
        status_log.append("Step 3: ✓ Type correct")
    else:
        record_session(0, 1)
        status_log.append(f"Step 3: ✗ Type was {ins.type}, got {inp}")

    # --- Step 4: Field Names ---
    display_worksheet("Step 4: Field Names", show_bin=True, show_op=True, show_type=True, show_fields=True)
    inp_raw = input("\nEnter field names (space separated, MSB to LSB):\nPress 'q' to quit to main menu.\n> ").strip()
    if check_quit(inp_raw): return False

    ans = inp_raw.split()
    all_ok, mask, correct_list = engine.validate_layout(ans)

    for i in range(num_fields):
        solved_names[i] = correct_list[i]
        if i < len(ans) and mask[i]:
            status_icons[i] = "✓"
        else:
            status_icons[i] = "✗"

    if all_ok:
        record_session(1.0, 1.0)
        status_log.append("Step 4: ✓ Field names correct")
    else:
        record_session(0.0, 1.0)
        correct_count = sum(mask)
        status_log.append(f"Step 4: ✗ Fields {correct_count}/{num_fields} correct")

    display_worksheet("Step 4: Field Names", show_bin=True, show_op=True, show_type=True, show_fields=True)

    # --- Step 5: Field Values (all at once, MSB to LSB) ---
    for i in range(num_fields): status_icons[i] = "?"

    display_worksheet("Step 5: Field Values", show_bin=True, show_op=True, show_type=True, show_fields=True, show_vals=True)
    inp_raw = input("\nEnter decimal values (space separated, MSB to LSB):\nPress 'q' to quit to main menu.\n> ").strip()
    if check_quit(inp_raw): return False

    user_vals = inp_raw.split()
    field_vals_map = {}
    correct_val_count = 0

    for i in range(num_fields):
        field_name, width = field_layouts[i]
        bin_str = next((f[1] for f in truth['fields'] if f[0] == field_name), "0")
        expected_val = int(bin_str, 2)

        if i < len(user_vals):
            try:
                user_val = int(user_vals[i])
                bitmask = (1 << width) - 1
                if (user_val & bitmask) == expected_val:
                    solved_vals[i] = user_vals[i]
                    status_icons[i] = "✓"
                    field_vals_map[field_name] = user_val
                    record_session(1.0 / num_fields, 1.0 / num_fields)
                    correct_val_count += 1
                    continue
            except ValueError:
                pass

        # Wrong or missing
        record_session(0.0, 1.0 / num_fields)
        solved_vals[i] = str(expected_val)
        status_icons[i] = "✗"
        field_vals_map[field_name] = expected_val

    if correct_val_count == num_fields:
        status_log.append("Step 5: ✓ Field values correct")
    else:
        status_log.append(f"Step 5: ✗ Values {correct_val_count}/{num_fields} correct")

    display_worksheet("Step 5: Field Values", show_bin=True, show_op=True, show_type=True, show_fields=True, show_vals=True)

    # --- Step 6: Final Assembly ---
    target_vals = {"opcode": ins.op, "rd": q['rd'], "rs1": q['rs1'], "rs2": q['rs2'], "imm": q['imm']}

    display_worksheet("Step 6: Final Assembly", show_bin=True, show_op=True, show_type=True, show_fields=True, show_vals=True)
    inp = input("\nWrite the final assembly (e.g. add x1, x2, x3):\nPress 'q' to quit to main menu.\n> ").strip()
    if check_quit(inp): return False

    ok, msg = validate_asm_strict(inp, ins, target_vals)
    if ok:
        record_session(1, 1)
        status_log.append("Step 6: ✓ Assembly correct")
    else:
        record_session(0, 1)
        status_log.append(f"Step 6: ✗ {msg}")

    # Show final state with assembly revealed
    display_worksheet("Step 6: Final Assembly", show_bin=True, show_op=True, show_type=True, show_fields=True, show_vals=True, show_asm=True)

    return True

def main():
    clear_screen()
    print("Welcome to rvtutor")
    print("-" * 20)
    
    engine = QuizEngine()
    
    while True: # 1. Types Configuration Loop
        print("\nEnter instruction types (R I S B U J) [Space or Comma separated, Enter for ALL]")
        types_raw = input("\nTypes (or 'q' to quit):\n> ").strip().lower()
        
        if types_raw in ['q', 'quit']:
            sys.exit(0)
            
        if not types_raw or types_raw == 'all':
            types = ["R", "I", "S", "B", "U", "J"]
        else:
            types = [t.strip().upper() for t in types_raw.replace(',', ' ').split()]
        
        try:
            engine.filter_pool(types)
            active_types = sorted(set(t.type for t in engine.pool))
            print(f"Selected Instruction Types: {', '.join(active_types)}")
        except Exception as e:
            print(f"Error: {e}. Please try again.")
            continue

        while True: # 2. Mode Selection Loop
            clear_screen()
            # Calculate accuracy for display
            p = engine.stats['points']
            t = engine.stats['total_points']
            acc = (p * 100 // t) if t > 0 else 0
            
            print(f"\nMode Selection (Active Instruction Types: {', '.join(active_types)})")
            print(f"Accuracy: {p:.2f}/{t:.2f} ({acc:.1f}%)")
            print("-" * 20)
            print("1: Recall (Field names)")
            print("2: Bits (Field bit-widths)")
            print("3: Encoding (Full 32-bit practice)")
            print("4: Decoding (Hex to Assembly)")
            print("m: Instruction Type selection")
            print("q: Quit")
            
            mode_choice = input("\nChoice:\n> ").strip().lower()
            if mode_choice == 'm':
                break
            if mode_choice == 'q':
                sys.exit(0)
            if mode_choice not in ["1", "2", "3", "4"]:
                print("Invalid choice.")
                continue

            mode = mode_choice
            
            # Mode header will be printed inside the loop
            mode_header = f"Mode: {['Recall', 'Bits', 'Encoding', 'Decoding'][int(mode)-1]} (Active Types: {', '.join(active_types)})"

            while True: # 3. Quiz Inner Loop
                try:
                    q = engine.generate_question()
                    ins = q["instruction"]
                    
                    if mode == "4":
                        if not run_decoding_pipeline(engine, q):
                            break
                    elif mode == "1": # Recall
                        # Step 1: Instruction Type
                        clear_screen()
                        print(mode_header)
                        print(f"Instruction: {ins.name.lower()}")
                        
                        return_to_menu = False
                        ans_type = input("\nWhat instruction type is this? (q to quit):\n> ").strip().upper()
                        if ans_type.lower() in ['q', 'quit']: 
                            return_to_menu = True
                        elif ans_type == ins.type:
                            engine.record_stats(1, 1)
                        else:
                            engine.record_stats(0, 1)
                            print(f"Answer: {ins.type}")
                        
                        if return_to_menu: break

                        # Step 2: Fields
                        print(f"\nInstruction: {ins.name.lower()} ({ins.type}-Type)")
                        ans_raw = input("\nFields in order (use imm[hi:lo], q to quit):\n> ").strip()
                        if ans_raw.lower() in ['q', 'quit']: break
                        if not ans_raw: pass
                        else:
                            ans = ans_raw.split()
                            all_ok, mask, correct_list = engine.validate_layout(ans)
                            points = sum(mask)
                            total = len(correct_list)
                            
                            if all_ok:
                                engine.record_stats(points, total)
                            else:
                                engine.record_stats(points, total)
                                # Show feedback
                                feedback_parts = []
                                for i, name in enumerate(ans):
                                    if i < len(correct_list):
                                        msg = "✓" if mask[i] else f"✗ (Expected: {correct_list[i]})"
                                        feedback_parts.append(f"{name}: {msg}")
                                    else:
                                        feedback_parts.append(f"{name}: ✗ (Extra)")
                                if len(ans) < len(correct_list):
                                    feedback_parts.extend([f"Missing (Expected: {correct_list[i]})" for i in range(len(ans), len(correct_list))])
                                print(" | ".join(feedback_parts))
                            
                    elif mode == "2": # Bits
                        # Step 1: Instruction Type
                        clear_screen()
                        print(mode_header)
                        print(f"Instruction: {ins.name.lower()}")
                        
                        return_to_menu = False
                        ans_type = input("\nWhat instruction type is this? (q to quit):\n> ").strip().upper()
                        if ans_type.lower() in ['q', 'quit']: 
                            return_to_menu = True
                        elif ans_type == ins.type:
                            engine.record_stats(1, 1)
                        else:
                            engine.record_stats(0, 1)
                            print(f"Answer: {ins.type}")
                        
                        if return_to_menu: break

                        # Step 2: Bits
                        print(f"\nInstruction: {ins.name.lower()} ({ins.type}-Type)")
                        ans_raw = input("\nBit widths in order for fields/imm[hi:lo] (space separated, q to quit):\n> ").strip()
                        if ans_raw.lower() in ['q', 'quit']: break
                        if not ans_raw: pass
                        else:
                            ans = ans_raw.split()
                            all_ok, mask, correct_list = engine.validate_bits(ans)
                            points = sum(mask)
                            total = len(correct_list)
                            
                            if all_ok:
                                engine.record_stats(points, total)
                            else:
                                engine.record_stats(points, total)
                                # Show feedback
                                feedback_parts = []
                                field_names = [f[0] for f in LAYOUTS[ins.type]]
                                for i, b in enumerate(ans):
                                    if i < len(correct_list):
                                        msg = "✓" if mask[i] else f"✗ (Expected: {correct_list[i]})"
                                        feedback_parts.append(f"{field_names[i]}: {msg}")
                                    else:
                                        feedback_parts.append(f"✗ (Extra)")
                                if len(ans) < len(correct_list):
                                    feedback_parts.extend([f"{field_names[i]}: ✗ (Expected: {correct_list[i]})" for i in range(len(ans), len(correct_list))])
                                print(" | ".join(feedback_parts))
                            
                    elif mode == "3": # Encoding
                        if not run_encoding_pipeline(engine, q):
                            break
                    
                    p = engine.stats['points']
                    t = engine.stats['total_points']
                    acc = (p * 100 // t) if t > 0 else 0
                    print(f"\nAccuracy: {p:.2f}/{t:.2f} ({acc:.1f}%)")
                    
                    cont = input("Continue? [Y/n]: ").strip().lower()
                    if cont == 'n':
                        break
                        
                except (KeyboardInterrupt, EOFError):
                    break

def run_encoding_pipeline(engine, q):
    """4-step interactive encoding process with exit paths."""
    ins = q["instruction"]
    truth = engine.get_ground_truth()
    
    def display_context(show_givens=False):
        clear_screen()
        print(f"Mode: Encoding")
        print(f"\n{q['asm']}\n")
        
        if show_givens:
            if ins.f3 is not None:
                print(f"  Funct3: {ins.f3}")
            if ins.f7 is not None:
                print(f"  Funct7: {ins.f7}")
            print()
    
    def check_exit(text):
        return text.lower() in ['q', 'quit']

    # Step 1: Type
    display_context(show_givens=False)
    print(f"What instruction type is {ins.name.lower()}?")
    raw = input("\nType (q to quit):\n> ").strip()
    if not raw or check_exit(raw): return False
    
    if raw.upper() == ins.type: 
        engine.record_stats(1, 1)
    else:
        engine.record_stats(0, 1)
        print(f"Answer: {ins.type}")

    # Step 2: Fields
    display_context(show_givens=False)
    print(f"What are the field names for instruction {ins.name.lower()} in order?")
    raw = input("\nFields (space separated, use imm[hi:lo], q to quit):\n> ").strip()
    if not raw or check_exit(raw): return False
    ans = raw.split()
    ok, mask, correct = engine.validate_layout(ans)
    points = sum(mask)
    total = len(correct)
    
    engine.record_stats(points, total)
    if not ok:
        # Detailed feedback
        feedback_parts = []
        for i, name in enumerate(ans):
            if i < len(correct):
                msg = "✓" if mask[i] else f"✗ (Expected: {correct[i]})"
                feedback_parts.append(f"{name}: {msg}")
            else:
                feedback_parts.append(f"{name}: ✗ (Extra)")
        if len(ans) < len(correct):
            feedback_parts.extend([f"Missing (Expected: {correct[i]})" for i in range(len(ans), len(correct))])
        print(" | ".join(feedback_parts))

    # Step 3: Binary per field
    display_context(show_givens=True)
    print(f"What are the binary values for each field in {ins.name.lower()}?")
    raw = input("\nBinary (space separated, q to quit):\n> ").strip()
    if not raw or check_exit(raw): return False
    ans = raw.split()
    truth_parts = [p[1] for p in truth["fields"]]
    
    mask = [False] * len(truth_parts)
    for i in range(min(len(ans), len(truth_parts))):
        if ans[i] == truth_parts[i]:
            mask[i] = True
    
    points = sum(mask)
    total = len(truth_parts)
    
    engine.record_stats(points, total)
    if not (points == total and len(ans) == total):
        # Feedback
        field_names = [p[0] for p in truth["fields"]]
        feedback_parts = []
        for i, val in enumerate(ans):
            if i < len(truth_parts):
                msg = "✓" if mask[i] else f"✗ (Expected: {truth_parts[i]})"
                feedback_parts.append(f"{field_names[i]}: {msg}")
            else:
                feedback_parts.append(f"✗ (Extra)")
        if len(ans) < len(truth_parts):
             feedback_parts.extend([f"{field_names[i]}: ✗ (Expected: {truth_parts[i]})" for i in range(len(ans), len(truth_parts))])
        print(" | ".join(feedback_parts))

    # Step 4: Final Hex
    display_context(show_givens=True)
    print(f"What is the final 32-bit hex encoding for {ins.name.lower()}?")
    raw = input("\nHex (q to quit):\n> ").strip()
    if not raw or check_exit(raw): return False
    h = raw.lower()
    expected = truth["hex"]
    if h == expected or h == "0x" + expected:
        engine.record_stats(1, 1)
    else:
        engine.record_stats(0, 1)
        print(f"Answer: {expected}")
        
    return True

if __name__ == "__main__":
    main()

