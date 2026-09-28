"""
verification.py - PART 6: signature verification.

Six independent checks (verification never relies on one comparison):

  1 signature_record_checksum  the signature record was not edited
  2 sha256_match               SHA-256(received message) == signed hash
  3 selected_bits_match        bits re-selected from the received hash == signed bits
  4 state_encoding_match       qubit angles re-derived from the message == signed angles
  5 teleportation_fidelity     states rebuilt from the RECEIVED message are teleported
                               again; every fidelity must be >= threshold
  6 bob_state_matches_record   Bob's re-run Bloch vectors == Bloch vectors in the signature

`mode` lets the same verifier run over a normal channel or an attacked/faulty one
("intercept", "no_correction") for the security tests.
"""

import numpy as np

from teleportation.teleportation import get_backend

from .attacks import run_channel
from .config import BLOCH_TOLERANCE, FIDELITY_THRESHOLD, VERIFY_SEED
from .logger import Logger
from .message import process_message
from .quantum_encoding import encode_bits, select_hash_bits
from .signature import compute_checksum

REQUIRED_KEYS = ("message_hash", "selected_hash_bits", "encoding",
                 "qubit_records", "signature_checksum")

CHECK_TITLES = {
    "signature_record_checksum": "Signature record checksum",
    "sha256_match": "SHA-256 hash match",
    "selected_bits_match": "Selected hash bits match",
    "state_encoding_match": "Quantum state encoding match",
    "teleportation_fidelity": "Teleportation fidelity >= threshold",
    "bob_state_matches_record": "Bob state matches signature record",
}


def verify_signature(message, signature, backend=None, seed=VERIFY_SEED,
                     mode="normal", log=None) -> dict:
    log = log or Logger(verbose=False)
    backend = backend or get_backend()
    missing = [k for k in REQUIRED_KEYS if k not in signature]
    if missing:
        raise ValueError(f"Malformed signature, missing keys: {missing}")

    checks = {}

    def record(name, passed, detail):
        checks[name] = {"passed": bool(passed), "detail": detail}

    log.step(f"Message received for verification: {message!r}")

    # 1 - the record itself
    record("signature_record_checksum",
           compute_checksum(signature) == signature["signature_checksum"],
           "checksum recomputed over the signature record")

    # 2 - classical hash
    info = process_message(message)
    signed_hash = signature["message_hash"]
    log.step(f"SHA-256 recalculated: {info['sha256_hex']}")
    record("sha256_match", info["sha256_hex"] == signed_hash,
           f"received={info['sha256_hex'][:16]}...  signed={signed_hash[:16]}...")
    if not checks["sha256_match"]["passed"]:
        log.tag("DETECTION", "SHA-256 mismatch")

    # 3 - selected bits
    n_qubits = int(signature["encoding"]["n_qubits"])
    bits = select_hash_bits(info["sha256_hex"], n_qubits)
    record("selected_bits_match", bits == signature["selected_hash_bits"],
           f"received={bits}  signed={signature['selected_hash_bits']}")

    # 4 - state encoding
    states = encode_bits(bits)
    signed_thetas = [r["theta"] for r in signature["qubit_records"]]
    thetas = [s["theta"] for s in states]
    record("state_encoding_match",
           len(thetas) == len(signed_thetas) and np.allclose(thetas, signed_thetas, atol=1e-9),
           "qubit angles re-derived from the received message")
    log.step("Expected quantum states reconstructed from the received message")

    # 5 + 6 - teleportation re-run
    results = run_channel(states, mode, seed, backend)
    log.step(f"Teleportation re-run (channel mode: {mode})")
    fids = [r["fidelity"] for r in results]
    f_mean, f_min = float(np.mean(fids)), float(min(fids))
    log.step(f"Fidelity calculated: mean={f_mean:.6f} min={f_min:.6f}")
    record("teleportation_fidelity", f_min >= FIDELITY_THRESHOLD,
           f"mean={f_mean:.6f} min={f_min:.6f} threshold={FIDELITY_THRESHOLD}")

    dists = []
    for r, rec in zip(results, signature["qubit_records"]):
        dists.append(float(np.linalg.norm(np.array(r["bob_bloch"]) - np.array(rec["bob_bloch"]))))
    same_len = len(results) == len(signature["qubit_records"])
    max_d = max(dists) if dists else float("inf")
    record("bob_state_matches_record", same_len and max_d <= BLOCH_TOLERANCE,
           f"max Bloch-vector distance = {max_d:.2e} (tolerance {BLOCH_TOLERANCE:.0e})")

    valid = all(c["passed"] for c in checks.values())
    log.step("Verification completed")
    if not valid:
        log.tag("RESULT", "Signature verification failed")

    return {
        "mode": mode,
        "message": message,
        "message_hash_received": info["sha256_hex"],
        "message_hash_signed": signed_hash,
        "checks": checks,
        "per_qubit": results,
        "fidelity_mean": f_mean,
        "fidelity_min": f_min,
        "signature_valid": valid,
    }


def format_verification_report(v: dict) -> str:
    L = ["SIGNATURE VERIFICATION", "-" * 60,
         f"Message  : {v['message']}",
         f"Hash     : {v['message_hash_received']}",
         f"Signed   : {v['message_hash_signed']}",
         f"Channel  : {v['mode']}",
         f"Fidelity : mean {v['fidelity_mean']:.4f} (min {v['fidelity_min']:.4f})", ""]
    for name, c in v["checks"].items():
        L.append(f"  [{'PASS' if c['passed'] else 'FAIL'}] {CHECK_TITLES[name]}")
        L.append(f"         {c['detail']}")
    L.append("")
    if v["signature_valid"]:
        L += ["✓ SIGNATURE VALID", "✓ MESSAGE INTEGRITY VERIFIED"]
    else:
        L += ["✗ SIGNATURE INVALID"]
        if not v["checks"]["sha256_match"]["passed"]:
            L.append("⚠ MESSAGE TAMPERING DETECTED")
        elif not v["checks"]["teleportation_fidelity"]["passed"]:
            L.append("⚠ QUANTUM STATE DISTURBANCE DETECTED")
        else:
            L.append("⚠ SIGNATURE RECORD INCONSISTENCY DETECTED")
    return "\n".join(L)
