"""
quantum_encoding.py - PART 3: SHA-256 hash bits -> single-qubit states.

PIPELINE (fully deterministic)
    SHA-256 digest (256 bits)
        |  take the FIRST 2*N_QUBITS bits            (select_hash_bits)
    classical bit string, e.g. 0101111000001010
        |  split into 2-bit pairs, one pair per qubit (encode_bits)
    one BB84-style state per pair
        |  Ry(theta)|0>  (prepared by the teleportation circuit)
    quantum state to teleport

ENCODING TABLE  (pair = basis bit, value bit)
    bits  basis  state  theta (Ry angle)
    "00"    Z     |0>      0
    "01"    Z     |1>      pi
    "10"    X     |+>      pi/2
    "11"    X     |->     -pi/2

Ry(theta)|0> = cos(theta/2)|0> + sin(theta/2)|1>, which is exactly the state
form used by the existing teleportation circuit. Ry(-pi/2)|0> = (|0>-|1>)/sqrt2 = |->.

WHY THIS ENCODING?  Z-basis states (|0>,|1>) are NOT disturbed by a Z-basis
measurement, but X-basis states (|+>,|->) ARE. That is what lets the
interception demo (attacks.py) show a measurable disturbance.
"""

import numpy as np

from .config import N_QUBITS, BITS_PER_QUBIT
from .message import hash_hex_to_bits

ENCODING_TABLE = {
    "00": ("Z", 0, "|0>", 0.0),
    "01": ("Z", 1, "|1>", float(np.pi)),
    "10": ("X", 0, "|+>", float(np.pi / 2)),
    "11": ("X", 1, "|->", float(-np.pi / 2)),
}


def select_hash_bits(hash_hex: str, n_qubits: int = N_QUBITS) -> str:
    """The first n_qubits*2 bits of the SHA-256 digest (deterministic)."""
    return hash_hex_to_bits(hash_hex)[: n_qubits * BITS_PER_QUBIT]


def encode_bits(bits: str) -> list:
    """Bit string (even length) -> list of per-qubit state descriptions."""
    if len(bits) == 0 or len(bits) % BITS_PER_QUBIT != 0 or set(bits) - {"0", "1"}:
        raise ValueError("bits must be a non-empty 0/1 string of even length")
    states = []
    for i in range(0, len(bits), BITS_PER_QUBIT):
        pair = bits[i:i + BITS_PER_QUBIT]
        basis, value, label, theta = ENCODING_TABLE[pair]
        states.append({"index": i // BITS_PER_QUBIT, "bits": pair,
                       "basis": basis, "value": value,
                       "label": label, "theta": theta})
    return states


def encode_hash(hash_hex: str, n_qubits: int = N_QUBITS):
    """Convenience: returns (selected_bits, states)."""
    bits = select_hash_bits(hash_hex, n_qubits)
    return bits, encode_bits(bits)


def expected_bloch(theta: float) -> list:
    """Bloch vector [x, y, z] of Ry(theta)|0> (no Qiskit needed)."""
    return [float(np.sin(theta)), 0.0, float(np.cos(theta))]


def format_encoding_report(bits: str, states: list) -> str:
    lines = ["QUANTUM ENCODING (SHA-256 -> selected bits -> qubit states)",
             "-" * 60,
             f"Selected hash bits ({len(bits)}): {bits}",
             "Qubit  bits  basis  state   theta (rad)"]
    for s in states:
        lines.append(f"  q{s['index']}    {s['bits']}     {s['basis']}    "
                     f"{s['label']:>4}   {s['theta']:+.4f}")
    return "\n".join(lines)
