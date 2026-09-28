"""
signature.py - PART 5: educational QDS signature generation.

THE FOUR DIFFERENT THINGS (do not confuse them)
  1. classical hash      SHA-256 digest of the message (hashlib)
  2. quantum states      one qubit per 2 selected hash bits (quantum_encoding.py)
  3. teleportation data  Alice's Bell-measurement bits, Bob's reconstructed
                         Bloch vectors, fidelities (from the simulator)
  4. QDS signature       the structured record below that BUNDLES 1-3

GENERATION
  message -> SHA-256 -> first 16 bits -> 8 qubit states -> teleport each qubit
  -> record everything -> add a SHA-256 checksum of the record.

DESIGN LIMITATIONS (honest list)
  * No secret key and no public/private key pair: anyone can run this code on
    any message and produce a "valid" signature. It shows INTEGRITY checking,
    NOT authenticity or non-repudiation.
  * The verifier recomputes the states from the message, so the "quantum data"
    is reproducible classical information here, not a one-time quantum token.
  * The checksum only detects accidental/naive edits of the record; it is not
    a MAC or a signature.
  * Ideal noiseless simulator; real hardware would give fidelity < 1.
  * Not a formally proven or standardized QDS protocol.
"""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from teleportation.teleportation import get_backend

from .attacks import run_channel
from .config import (N_QUBITS, SCHEME_NAME, SIGN_SEED, FIDELITY_THRESHOLD)
from .logger import Logger
from .message import process_message
from .quantum_encoding import (encode_hash, format_encoding_report)

BLOCH_DECIMALS = 9


def compute_checksum(signature: dict) -> str:
    """SHA-256 over the canonical JSON of the record (excluding the checksum)."""
    payload = {k: v for k, v in signature.items() if k != "signature_checksum"}
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _versions():
    try:
        import qiskit, qiskit_aer
        return {"qiskit": qiskit.__version__, "qiskit_aer": qiskit_aer.__version__}
    except Exception:   # pragma: no cover
        return {}


def generate_signature(message, backend=None, seed=SIGN_SEED, log=None,
                       n_qubits=N_QUBITS) -> dict:
    log = log or Logger(verbose=False)
    backend = backend or get_backend()

    log.step(f"Message received: {message!r}")
    info = process_message(message)
    log.step(f"SHA-256 generated: {info['sha256_hex']}")

    bits, states = encode_hash(info["sha256_hex"], n_qubits)
    log.step(f"Hash bits selected: {bits} (first {len(bits)} of 256)")
    log.step("Quantum states prepared: " + " ".join(s["label"] for s in states))

    results = run_channel(states, "normal", seed, backend)
    log.step("Bell pairs created (one per qubit, inside each teleportation circuit)")
    log.step("Teleportation executed: Bell measurement + Bob's X/Z corrections")
    for r in results:
        log.detail(f"q{r['index']} {r['label']}: Alice bits (m1 m0) = "
                   f"{r['alice_m1']}{r['alice_m0']}")
    log.step("Bob states reconstructed")

    fids = [r["fidelity"] for r in results]
    log.step(f"Fidelity calculated: mean={np.mean(fids):.6f} min={min(fids):.6f}")

    records = [{
        "index": r["index"], "bits": r["bits"], "basis": r["basis"],
        "label": r["label"], "theta": r["theta"],
        "alice_m0": r["alice_m0"], "alice_m1": r["alice_m1"],
        "bob_bloch": [round(v, BLOCH_DECIMALS) for v in r["bob_bloch"]],
        "fidelity": round(r["fidelity"], 12),
    } for r in results]

    signature = {
        "scheme": SCHEME_NAME,
        "disclaimer": "Educational simulation. Not a standardized or formally proven QDS protocol.",
        "message_hash": info["sha256_hex"],
        "hash_algorithm": "SHA-256",
        "selected_hash_bits": bits,
        "encoding": {"n_qubits": n_qubits, "bits_per_qubit": 2,
                     "mapping": "00:|0>(0) 01:|1>(pi) 10:|+>(pi/2) 11:|->(-pi/2), state=Ry(theta)|0>"},
        "qubit_records": records,
        "quantum_measurements": {
            "alice_bell_measurements_m1m0": [f"{r['alice_m1']}{r['alice_m0']}" for r in records]},
        "teleportation_results": {
            "channel": "normal",
            "mean_fidelity": round(float(np.mean(fids)), 12),
            "min_fidelity": round(float(min(fids)), 12),
            "all_qubits_passed": bool(min(fids) >= FIDELITY_THRESHOLD)},
        "metadata": {"created_utc": datetime.now(timezone.utc).isoformat(),
                     "simulator": "qiskit_aer.AerSimulator", "seed": seed,
                     "versions": _versions()},
    }
    signature["signature_checksum"] = compute_checksum(signature)
    log.step(f"Signature generated (checksum {signature['signature_checksum'][:16]}...)")
    return signature


# ---------------------------------------------------------------------------
# Storage (PART 5 item "signature storage")
# ---------------------------------------------------------------------------
def save_signature(signature: dict, path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(signature, indent=2), encoding="utf-8")
    return path


def load_signature(path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def format_signature_summary(sig: dict) -> str:
    t = sig["teleportation_results"]
    L = ["QDS SIGNATURE (educational prototype output)",
         "-" * 60,
         f"Scheme            : {sig['scheme']}",
         f"[classical]  hash : {sig['message_hash']}",
         f"[classical]  bits : {sig['selected_hash_bits']}",
         "[quantum]    states: " + " ".join(r["label"] for r in sig["qubit_records"]),
         "[teleport]   Alice : " + " ".join(sig["quantum_measurements"]["alice_bell_measurements_m1m0"]),
         f"[teleport]   fidelity mean={t['mean_fidelity']:.6f} min={t['min_fidelity']:.6f}",
         f"[signature]  checksum: {sig['signature_checksum']}",
         "NOTE: no secret key - proves integrity of this simulation, not authorship."]
    return "\n".join(L)
