"""
message.py - PART 2: message processing (classical side only).

message (str) -> UTF-8 bytes -> SHA-256 digest (hashlib) -> 256-bit string
No custom cryptography: hashing is Python's standard hashlib.
"""

import hashlib


def sha256_hex(message: str) -> str:
    """SHA-256 of the UTF-8 encoding of `message`, as 64 hex characters."""
    return hashlib.sha256(message.encode("utf-8")).hexdigest()


def hash_hex_to_bits(hash_hex: str) -> str:
    """64 hex chars -> 256-character string of '0'/'1' (big-endian, zero padded)."""
    return f"{int(hash_hex, 16):0{len(hash_hex) * 4}b}"


def process_message(message: str) -> dict:
    """Return everything Part 2 asks for, in one dictionary."""
    if not isinstance(message, str) or message == "":
        raise ValueError("Message must be a non-empty string.")
    data = message.encode("utf-8")
    digest_hex = hashlib.sha256(data).hexdigest()
    return {
        "message": message,
        "utf8_bytes": list(data),
        "utf8_hex": data.hex(),
        "sha256_hex": digest_hex,
        "sha256_bits": hash_hex_to_bits(digest_hex),
    }


def format_message_report(info: dict) -> str:
    bits = info["sha256_bits"]
    rows = [bits[i:i + 32] for i in range(0, len(bits), 32)]
    lines = [
        "MESSAGE PROCESSING",
        "-" * 60,
        f"Original message : {info['message']}",
        f"UTF-8 bytes      : {info['utf8_bytes']}",
        f"UTF-8 (hex)      : {info['utf8_hex']}",
        f"SHA-256 (hex)    : {info['sha256_hex']}",
        "SHA-256 (binary, 256 bits, 32 per row):",
    ]
    lines += [f"   {r}" for r in rows]
    return "\n".join(lines)
