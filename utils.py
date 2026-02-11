"""
RISC-V Tutor Utilities
Provides bit manipulation and formatting with strict contract guards.
"""

def to_bin(val: int, bits: int) -> str:
    """Converts an integer to a zero-padded binary string of fixed width."""
    if not isinstance(val, int):
        raise TypeError(f"val must be int, got {type(val)}")
    if not isinstance(bits, int):
        raise TypeError(f"bits must be int, got {type(bits)}")
    if bits <= 0:
        raise ValueError(f"bits must be positive, got {bits}")
    
    # Mask to ensure it fits in bits (unsigned behavior)
    mask = (1 << bits) - 1
    sanitized_val = val & mask
    return format(sanitized_val, f'0{bits}b')

def to_hex(val: int) -> str:
    """Converts an integer to an 8-character zero-padded hex string."""
    if not isinstance(val, int):
        raise TypeError(f"val must be int, got {type(val)}")
    
    # RISC-V 32-bit hex usually
    mask = 0xFFFFFFFF
    sanitized_val = val & mask
    return format(sanitized_val, '08x')

def sign_extend(val: int, bits: int) -> int:
    """Sign-extends a value from a given bit-width to 32-bit integer."""
    if not isinstance(val, int):
        raise TypeError(f"val must be int, got {type(val)}")
    if not isinstance(bits, int):
        raise TypeError(f"bits must be int, got {type(bits)}")
    if bits <= 0 or bits > 32:
        raise ValueError(f"bits must be in range [1, 32], got {bits}")

    sign_bit = 1 << (bits - 1)
    # Mask to the specified bits
    masked = val & ((1 << bits) - 1)
    if masked & sign_bit:
        return masked - (1 << bits)
    return masked
