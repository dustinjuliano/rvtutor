"""
RISC-V Tutor Quiz Engine
Manages instruction pools, randomization, and ground truth generation.
"""
import random
from typing import List, Dict, Optional, Tuple
from riscv import REGISTRY, LAYOUTS, Instruction, Swizzler
from utils import to_bin, to_hex

class QuizEngine:
    def __init__(self):
        self.pool: List[Instruction] = []
        self.stats = {"success": 0, "attempts": 0, "points": 0, "total_points": 0}
        self.current_q: Optional[Dict] = None

    def record_stats(self, points: int, total: int):
        """Updates stats with points achieved and total possible."""
        self.stats["points"] += points
        self.stats["total_points"] += total
        self.stats["attempts"] += 1
        if points == total:
            self.stats["success"] += 1

    def filter_pool(self, types: List[str]) -> None:
        """Filters instructions into the active pool based on types (e.g., ['R', 'I'])."""
        if not isinstance(types, list):
            raise TypeError("types must be a list of strings")
        
        valid_types = [t.upper() for t in types if isinstance(t, str)]
        self.pool = [i for i in REGISTRY if i.type in valid_types]
        
        if not self.pool:
            raise ValueError("No instructions found for the given types")

    def generate_question(self) -> Dict:
        """Picks a random instruction and generates values for fields."""
        if not self.pool:
            raise RuntimeError("Pool is empty. Call filter_pool first.")
            
        ins = random.choice(self.pool)
        q = {
            "instruction": ins,
            "rs1": random.randint(0, 31),
            "rs2": random.randint(0, 31),
            "rd": random.randint(1, 31), # Enforce semantic validity: rd != x0
            "imm": 0
        }
        
        # Immediate range handling
        if ins.type == 'I': q["imm"] = random.randint(-99, 99)
        elif ins.type == 'S': q["imm"] = random.randint(-99, 99)
        elif ins.type == 'B': q["imm"] = random.choice(range(-98, 98, 2))
        elif ins.type == 'U': q["imm"] = random.randint(0, 99)
        elif ins.type == 'J': q["imm"] = random.choice(range(-98, 98, 2))
        
        self.current_q = q
        q["asm"] = self.format_asm(q)
        return q

    def format_asm(self, q: Dict) -> str:
        """Generates a standard assembly string for the given question."""
        ins = q["instruction"]
        name = ins.name.lower()
        rd, rs1, rs2, imm = q["rd"], q["rs1"], q["rs2"], q["imm"]
        
        if ins.type == 'R':
            return f"{name} x{rd}, x{rs1}, x{rs2}"
        elif ins.type == 'I':
            if name == 'lw':
                return f"{name} x{rd}, {imm}(x{rs1})"
            return f"{name} x{rd}, x{rs1}, {imm}"
        elif ins.type == 'S':
            return f"{name} x{rs2}, {imm}(x{rs1})"
        elif ins.type == 'B':
            return f"{name} x{rs1}, x{rs2}, {imm}"
        elif ins.type == 'U':
            return f"{name} x{rd}, {imm}"
        elif ins.type == 'J':
            return f"{name} x{rd}, {imm}"
        return f"{name} ???"

    def get_ground_truth(self) -> Dict:
        """Generates the 32-bit binary structure for the current question."""
        if not self.current_q:
            raise RuntimeError("No current question")
            
        q = self.current_q
        ins = q["instruction"]
        fields = {}
        
        # Standard opcode/funct fields
        fields["opcode"] = to_bin(ins.op, 7)
        if ins.f3 is not None: fields["funct3"] = to_bin(ins.f3, 3)
        if ins.f7 is not None: fields["funct7"] = to_bin(ins.f7, 7)
        
        # Dynamic register fields
        if "rs1" in [f[0] for f in LAYOUTS[ins.type]]: fields["rs1"] = to_bin(q["rs1"], 5)
        if "rs2" in [f[0] for f in LAYOUTS[ins.type]]: fields["rs2"] = to_bin(q["rs2"], 5)
        if "rd" in [f[0] for f in LAYOUTS[ins.type]]: fields["rd"] = to_bin(q["rd"], 5)
        
        # Immediate swizzling
        imm_val = q["imm"]
        imm_parts = []
        if ins.type == 'I': 
            imm_parts = [to_bin(imm_val, 12)]
        elif ins.type == 'S': 
            imm_parts = Swizzler.s_type(imm_val)
        elif ins.type == 'B': 
            imm_parts = Swizzler.b_type(imm_val)
        elif ins.type == 'U': 
            imm_parts = [to_bin(imm_val, 20)]
        elif ins.type == 'J': 
            imm_parts = Swizzler.j_type(imm_val)
            
        # Compile full binary
        layout = LAYOUTS[ins.type]
        binary_str = ""
        imm_ptr = 0
        ordered_fields = []
        
        for name, bits in layout:
            if name == 'imm':
                val = imm_parts[imm_ptr]
                imm_ptr += 1
            else:
                val = fields[name]
            binary_str += val
            ordered_fields.append((name, val))
            
        return {
            "binary": binary_str,
            "hex": to_hex(int(binary_str, 2)),
            "fields": ordered_fields
        }

    def validate_layout(self, user_input: List[str]) -> Tuple[bool, List[bool], List[str]]:
        """Verifies field names; returns (all_ok, mask_list, correct_list)."""
        if not self.current_q: raise RuntimeError("No question")
        if not isinstance(user_input, list): raise TypeError("input must be a list")
        
        correct = [f[0].lower() for f in LAYOUTS[self.current_q["instruction"].type]]
        sanit_input = [v.strip().lower() for v in user_input]
        
        # Compare padding with None to match lengths
        mask = [False] * len(correct)
        for i in range(min(len(sanit_input), len(correct))):
            if sanit_input[i] == correct[i]:
                mask[i] = True
        
        all_correct = len(user_input) == len(correct) and all(mask)
        return all_correct, mask, correct

    def validate_bits(self, user_input: List[int]) -> Tuple[bool, List[bool], List[int]]:
        """Verifies bit-widths; returns (all_ok, mask_list, correct_list)."""
        if not self.current_q: raise RuntimeError("No question")
        if not isinstance(user_input, list): raise TypeError("input must be a list")
        
        correct = [f[1] for f in LAYOUTS[self.current_q["instruction"].type]]
        mask = [False] * len(correct)
        
        for i in range(min(len(user_input), len(correct))):
            try:
                if int(user_input[i]) == correct[i]:
                    mask[i] = True
            except (ValueError, TypeError):
                continue
            
        all_correct = len(user_input) == len(correct) and all(mask)
        return all_correct, mask, correct
