"""
RISC-V Tutor - CLI Interface
Recall Integrity: Screen Clearing & Question Pacing
"""
import sys
import os
from engine import QuizEngine
from riscv import LAYOUTS

def clear_screen():
    """Clears the console screen for active recall."""
    if os.name == 'nt':
        os.system('cls')
    else:
        # Cross-platform way to clear using ANSI or system command
        print("\033[H\033[J", end="")

def main():
    clear_screen()
    print("Welcome to rvtutor")
    print("-" * 20)
    
    engine = QuizEngine()
    
    while True: # 1. Types Configuration Loop
        print("\nEnter instruction types (R I S B U J) [Space or Comma separated, Enter for ALL]")
        types_raw = input("Types (or 'q' to quit): ").strip().lower()
        
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
            # Calculate accuracy for display
            p = engine.stats['points']
            t = engine.stats['total_points']
            acc = (p * 100 // t) if t > 0 else 0
            
            print(f"\nMode Selection (Active Instruction Types: {', '.join(active_types)})")
            print(f"Accuracy: {p}/{t} ({acc}%)")
            print("-" * 20)
            print("1: Recall (Field names)")
            print("2: Bits (Field bit-widths)")
            print("3: Encoding (Full 32-bit practice)")
            print("m: Instruction Type selection")
            print("q: Quit")
            
            mode_choice = input("Choice: ").strip().lower()
            if mode_choice == 'm':
                break
            if mode_choice == 'q':
                sys.exit(0)
            if mode_choice not in ["1", "2", "3"]:
                print("Invalid choice.")
                continue

            mode = mode_choice
            
            # Mode header will be printed inside the loop
            mode_header = f"Mode: {['Recall', 'Bits', 'Encoding'][int(mode)-1]} (Active Types: {', '.join(active_types)})"

            while True: # 3. Quiz Inner Loop
                try:
                    q = engine.generate_question()
                    ins = q["instruction"]
                    
                    clear_screen()
                    print(mode_header)
                    print("-" * 20)
                    print("Type 'q' to return to the mode menu.\n")
                    
                    if mode == "1": # Recall
                        # Step 1: Instruction Type
                        clear_screen()
                        print(mode_header)
                        print("-" * 20)
                        print("Type 'q' to return to the mode menu.\n")
                        print(f"Instruction: {ins.name.lower()}")
                        
                        step1_correct = False
                        return_to_menu = False
                        while True:
                            ans_type = input("What instruction type is this? (q to quit): ").strip().upper()
                            if ans_type.lower() in ['q', 'quit']: 
                                return_to_menu = True
                                break
                            if not ans_type: continue
                            
                            if ans_type == ins.type:
                                print(f"Correct. (1/1) (Type: {ins.type})")
                                engine.record_stats(1, 1)
                                step1_correct = True
                                break
                            else:
                                print(f"Incorrect. (0/1) Expected: {ins.type}")
                                engine.record_stats(0, 1)
                                # Reveal type on failure too, to help recall
                                break
                        
                        if return_to_menu: break

                        # Step 2: Fields
                        print(f"\nInstruction: {ins.name.lower()} ({ins.type}-Type)")
                        while True:
                            ans_raw = input("Fields in order (q to quit): ").strip()
                            if ans_raw.lower() in ['q', 'quit']: return_to_menu = True; break
                            if not ans_raw: continue
                            return_to_menu = False
                            break
                        
                        if return_to_menu: break
                        
                        ans = ans_raw.split()
                        all_ok, mask, correct_list = engine.validate_layout(ans)
                        points = sum(mask)
                        total = len(correct_list)
                        engine.record_stats(points, total)
                        
                        if all_ok:
                            print(f"Correct. ({points}/{total})")
                        else:
                            print(f"Incorrect. Points: {points}/{total}")
                            feedback = []
                            for i, name in enumerate(ans):
                                if i < len(correct_list):
                                    # mask has same length as correct_list
                                    msg = "✓" if mask[i] else f"✗ (Expected: {correct_list[i]})"
                                    feedback.append(f"{name}: {msg}")
                                else:
                                    feedback.append(f"{name}: ✗ (Extra)")
                            # If answer was shorter, append missing expected fields
                            if len(ans) < len(correct_list):
                                feedback.extend([f"Missing (Expected: {correct_list[i]})" for i in range(len(ans), len(correct_list))])
                            print(" | ".join(feedback))
                            
                    elif mode == "2": # Bits
                        # Step 1: Instruction Type
                        clear_screen()
                        print(mode_header)
                        print("-" * 20)
                        print("Type 'q' to return to the mode menu.\n")
                        print(f"Instruction: {ins.name.lower()}")
                        
                        return_to_menu = False
                        while True:
                            ans_type = input("What instruction type is this? (q to quit): ").strip().upper()
                            if ans_type.lower() in ['q', 'quit']: 
                                return_to_menu = True
                                break
                            if not ans_type: continue
                            
                            if ans_type == ins.type:
                                print(f"Correct. (1/1) (Type: {ins.type})")
                                engine.record_stats(1, 1)
                                break
                            else:
                                print(f"Incorrect. (0/1) Expected: {ins.type}")
                                engine.record_stats(0, 1)
                                break
                        
                        if return_to_menu: break

                        # Step 2: Bits
                        print(f"\nInstruction: {ins.name.lower()} ({ins.type}-Type)")
                        while True:
                            ans_raw = input("Bit widths in order (space separated, q to quit): ").strip()
                            if ans_raw.lower() in ['q', 'quit']: return_to_menu = True; break
                            if not ans_raw: continue
                            return_to_menu = False
                            break
                            
                        if return_to_menu: break
                        
                        ans = ans_raw.split()
                        all_ok, mask, correct_list = engine.validate_bits(ans)
                        points = sum(mask)
                        total = len(correct_list)
                        engine.record_stats(points, total)
                        
                        if all_ok:
                            print(f"Correct. ({points}/{total})")
                        else:
                            print(f"Incorrect. Points: {points}/{total}")
                            feedback = []
                            for i, val in enumerate(ans):
                                if i < len(correct_list):
                                    msg = "✓" if mask[i] else f"✗ (Expected: {correct_list[i]})"
                                    feedback.append(msg)
                                else:
                                    feedback.append("✗ (Extra)")
                            
                            # Append missing expected fields if any
                            if len(ans) < len(correct_list):
                                feedback.extend([f"✗ (Expected: {correct_list[i]})" for i in range(len(ans), len(correct_list))])
                            
                            print(" ".join(feedback))
                            
                    elif mode == "3": # Encoding
                        if not run_encoding_pipeline(engine, q):
                            break
                    
                    p = engine.stats['points']
                    t = engine.stats['total_points']
                    acc = (p * 100 // t) if t > 0 else 0
                    p = engine.stats['points']
                    t = engine.stats['total_points']
                    acc = (p * 100 // t) if t > 0 else 0
                    print(f"\nAccuracy: {p}/{t} ({acc}%)")
                    
                    cont = input("\nContinue? [Y/n]: ").strip().lower()
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
        print("-" * 20)
        print(f"\n{q['asm']}\n")
        
        if show_givens:
            print("Givens:")
            print(f"  Opcode: {ins.op}")
            if ins.f3 is not None:
                print(f"  Funct3: {ins.f3}")
            if ins.f7 is not None:
                print(f"  Funct7: {ins.f7}")
            print()

        print("-" * 20)
    
    def check_exit(text):
        return text.lower() in ['q', 'quit']

    # Step 1: Type
    display_context(show_givens=False)
    while True:
        print(f"What instruction type is `{ins.name.lower()}`?")
        raw = input("Type (q to quit): ").strip()
        if not raw: continue
        if check_exit(raw): return False
        if raw.upper() == ins.type: 
            print("Correct. (1/1)")
            engine.record_stats(1, 1)
            break
        print(f"Incorrect. (0/1) Expected: {ins.type}")
        engine.record_stats(0, 1)

    # Step 2: Fields
    display_context(show_givens=False)
    while True:
        print(f"What are the field names for instruction `{ins.name.lower()}` in order?")
        raw = input("Fields (space separated, q to quit): ").strip()
        if not raw: continue
        if check_exit(raw): return False
        ans = raw.split()
        ok, mask, correct = engine.validate_layout(ans)
        points = sum(mask)
        total = len(correct)
        engine.record_stats(points, total)
        
        if ok: 
            print(f"Correct. ({points}/{total})")
            break
        print(f"Incorrect. ({points}/{total})")
        feedback = []
        for i, name in enumerate(ans):
            if i < len(correct):
                # mask matches correct length
                msg = "✓" if mask[i] else f"✗ (Expected: {correct[i]})"
                feedback.append(f"{name}: {msg}")
            else:
                feedback.append(f"{name}: ✗ (Extra)")
        # If answer was shorter, append missing expected fields
        if len(ans) < len(correct):
            feedback.extend([f"Missing (Expected: {correct[i]})" for i in range(len(ans), len(correct))])
        print(" | ".join(feedback))

    # Step 3: Binary per field
    display_context(show_givens=True)
    while True:
        print(f"What are the binary values for each field in `{ins.name.lower()}`?")
        raw = input("Binary (space separated, q to quit): ").strip()
        if not raw: continue
        if check_exit(raw): return False
        ans = raw.split()
        truth_parts = [p[1] for p in truth["fields"]]
        
        mask = [False] * len(truth_parts)
        for i in range(min(len(ans), len(truth_parts))):
            if ans[i] == truth_parts[i]:
                mask[i] = True
        
        points = sum(mask)
        total = len(truth_parts)
        engine.record_stats(points, total)
        
        if points == total and len(ans) == total:
            print(f"Correct. ({points}/{total})")
            break
        
        print(f"Incorrect. ({points}/{total})")
        field_names = [p[0] for p in truth["fields"]]
        feedback = []
        for i, val in enumerate(ans):
            if i < len(truth_parts):
                msg = "✓" if mask[i] else f"✗ (Expected: {truth_parts[i]})"
                feedback.append(f"{field_names[i]}: {msg}")
            else:
                feedback.append(f"✗ (Extra)")
        
        # Append missing
        if len(ans) < len(truth_parts):
             feedback.extend([f"{field_names[i]}: ✗ (Expected: {truth_parts[i]})" for i in range(len(ans), len(truth_parts))])

        print(" | ".join(feedback))

    # Step 4: Final Hex
    display_context(show_givens=True)
    while True:
        print(f"What is the final 32-bit hex encoding for `{ins.name.lower()}`?")
        raw = input("Hex (q to quit): ").strip()
        if not raw: continue
        if check_exit(raw): return False
        h = raw.lower()
        expected = truth["hex"]
        if h == expected or h == "0x" + expected:
            print("Correct! (1/1)")
            engine.record_stats(1, 1)
            break
        print(f"Incorrect. (0/1) Expected: {expected}")
        engine.record_stats(0, 1)
        
    return True

if __name__ == "__main__":
    main()
