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
            print(f"\nMode Selection (Active Instruction Types: {', '.join(active_types)})")
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
                        print(f"Instruction: {ins.name.upper()} ({ins.type}-Type)")
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
                            feedback = [f"{name}: {'✓' if i < len(mask) and mask[i] else '✗'}" 
                                       for i, name in enumerate(correct_list)]
                            print(" | ".join(feedback))
                            
                    elif mode == "2": # Bits
                        print(f"Instruction: {ins.name.upper()}")
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
                            feedback = ["✓" if i < len(mask) and mask[i] else f"✗ (Exp: {bits})" 
                                       for i, bits in enumerate(correct_list)]
                            print(" ".join(feedback))
                            
                    elif mode == "3": # Encoding
                        if not run_encoding_pipeline(engine, q):
                            break
                    
                    p = engine.stats['points']
                    t = engine.stats['total_points']
                    acc = (p * 100 // t) if t > 0 else 0
                    print(f"\nGlobal Accuracy: {p}/{t} ({acc}%)")
                    
                    cont = input("\nContinue? [Y/n]: ").strip().lower()
                    if cont == 'n':
                        break
                        
                except (KeyboardInterrupt, EOFError):
                    break

def run_encoding_pipeline(engine, q):
    """4-step interactive encoding process with exit paths."""
    ins = q["instruction"]
    truth = engine.get_ground_truth()
    
    def display_context():
        clear_screen()
        print(f"Mode: Encoding (Instruction: {ins.name.upper()} - {ins.type}-Type)")
        print("-" * 20)
    
    def check_exit(text):
        return text.lower() in ['q', 'quit']

    # Step 1: Type
    while True:
        display_context()
        raw = input("1. Identify Type (q to quit): ").strip()
        if not raw: continue
        if check_exit(raw): return False
        if raw.upper() == ins.type: 
            print("Correct.")
            engine.record_stats(1, 1)
            break
        print(f"Incorrect. Expected: {ins.type}")
        engine.record_stats(0, 1)

    # Step 2: Fields
    while True:
        display_context()
        raw = input("2. Enter Field Names (q to quit): ").strip()
        if not raw: continue
        if check_exit(raw): return False
        ans = raw.split()
        ok, mask, correct = engine.validate_layout(ans)
        points = sum(mask)
        total = len(correct)
        engine.record_stats(points, total)
        ok, mask, correct = engine.validate_layout(ans)
        points = sum(mask)
        total = len(correct)
        engine.record_stats(points, total)
        if ok: 
            print(f"Correct. ({points}/{total})")
            break
        print(f"Incorrect. Expected: {' '.join(correct)}")

    # Step 3: Binary per field
    while True:
        display_context()
        print(f"Values: rs1={q['rs1']}, rs2={q['rs2']}, rd={q['rd']}, imm={q['imm']}")
        raw = input("3. Binary for each field (q to quit): ").strip()
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
        print(f"Incorrect. Expected: {' '.join(truth_parts)}")

    # Step 4: Final Hex
    while True:
        display_context()
        raw = input("4. Full Hex (q to quit): ").strip()
        if not raw: continue
        if check_exit(raw): return False
        h = raw.upper()
        expected = truth["hex"]
        if h == expected or h == "0X" + expected:
            print("Correct!")
            engine.record_stats(1, 1)
            break
        print(f"Incorrect. Expected: {expected}")
        engine.record_stats(0, 1)
        
    return True

if __name__ == "__main__":
    main()
