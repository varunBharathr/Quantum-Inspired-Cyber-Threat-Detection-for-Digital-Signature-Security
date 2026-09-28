"""
attacks.py - PARTS 7 and 8: attack / fault simulations.

Contains NO Qiskit code (that lives in teleportation/). Channel modes:
    "normal"         honest teleportation with Bob's X/Z corrections
    "no_correction"  Bob skips the corrections (protocol failure / control)
    "intercept"      EDUCATIONAL intercept/measure attack (see teleportation/intercept.py)
"""

import numpy as np

from teleportation.teleportation import teleport_state, get_backend
from teleportation.intercept import intercept_state

from .config import (ATTACK_SEED, FIDELITY_THRESHOLD, NO_CORRECTION_REPEATS)
from .logger import Logger
from .message import sha256_hex
from .quantum_encoding import encode_hash

MODES = ("normal", "no_correction", "intercept")


# ---------------------------------------------------------------------------
# Part 7: message tampering
# ---------------------------------------------------------------------------
def tamper_message(message: str, suffix: str = " 123") -> str:
    """The attacker's modification: append `suffix` to the message."""
    return message + suffix


# ---------------------------------------------------------------------------
# Channel runner used by verification and by the attack comparison
# ---------------------------------------------------------------------------
def run_channel(states, mode="normal", seed=ATTACK_SEED, backend=None) -> list:
    """Teleport every qubit state in `states` under the chosen channel mode."""
    if mode not in MODES:
        raise ValueError(f"mode must be one of {MODES}")
    backend = backend or get_backend()
    results = []
    for i, s in enumerate(states):
        sd = seed + 10 * i
        if mode == "normal":
            r = teleport_state(s["theta"], True, sd, backend)
        elif mode == "intercept":
            r = intercept_state(s["theta"], sd, backend)
        else:  # no_correction: keep the worst of several runs
            runs = [teleport_state(s["theta"], False, sd + k, backend)
                    for k in range(NO_CORRECTION_REPEATS)]
            r = min(runs, key=lambda x: x["fidelity"])
        r.update({"index": s["index"], "bits": s["bits"],
                  "label": s["label"], "basis": s["basis"]})
        results.append(r)
    return results


# ---------------------------------------------------------------------------
# Part 8: normal vs attacked teleportation
# ---------------------------------------------------------------------------
def compare_normal_vs_attacked(message, backend=None, seed=ATTACK_SEED, log=None):
    """
    Educational intercept/measurement attack simulation.
    Returns per-qubit results for both runs plus a detection decision.
    """
    log = log or Logger(verbose=False)
    backend = backend or get_backend()
    bits, states = encode_hash(sha256_hex(message))
    log.tag("ATTACK", "Eve intercepts Bob's Bell-pair half and measures it (Z basis)")

    normal = run_channel(states, "normal", seed, backend)
    attacked = run_channel(states, "intercept", seed, backend)

    rows = []
    for n, a in zip(normal, attacked):
        shift = float(np.linalg.norm(np.array(n["bob_bloch"]) - np.array(a["bob_bloch"])))
        rows.append({"index": n["index"], "label": n["label"], "basis": n["basis"],
                     "fidelity_normal": n["fidelity"],
                     "fidelity_attacked": a["fidelity"],
                     "eve_bit": a["eve_bit"],
                     "alice_bits_normal": f"{n['alice_m1']}{n['alice_m0']}",
                     "alice_bits_attacked": f"{a['alice_m1']}{a['alice_m0']}",
                     "bob_bloch_normal": n["bob_bloch"],
                     "bob_bloch_attacked": a["bob_bloch"],
                     "bloch_shift": shift,
                     "disturbed": a["fidelity"] < FIDELITY_THRESHOLD})
    detected = any(r["disturbed"] for r in rows)
    result = {
        "message": message,
        "attack_name": "Educational intercept/measurement attack simulation",
        "rows": rows,
        "mean_fidelity_normal": float(np.mean([r["fidelity_normal"] for r in rows])),
        "mean_fidelity_attacked": float(np.mean([r["fidelity_attacked"] for r in rows])),
        "min_fidelity_attacked": float(min(r["fidelity_attacked"] for r in rows)),
        "disturbed_qubits": sum(r["disturbed"] for r in rows),
        "sensitive_qubits": sum(r["basis"] == "X" for r in rows),
        "detected": detected,
    }
    if detected:
        log.tag("DETECTION", f"Fidelity drop on {result['disturbed_qubits']} of "
                             f"{len(rows)} qubits (min {result['min_fidelity_attacked']:.4f})")
    else:
        log.tag("DETECTION", "No disturbance seen (no X-basis qubits in the selected bits)")
    return result


def format_attack_comparison(res: dict) -> str:
    L = ["EDUCATIONAL INTERCEPT/MEASUREMENT ATTACK SIMULATION",
         "(one simplified strategy - NOT every possible quantum attack)",
         "-" * 74,
         "Qubit State  F(normal)  F(attacked)  Eve bit  Bloch shift  Disturbed"]
    for r in res["rows"]:
        L.append(f"  q{r['index']}   {r['label']:>4}   {r['fidelity_normal']:.4f}     "
                 f"{r['fidelity_attacked']:.4f}       {r['eve_bit']}       "
                 f"{r['bloch_shift']:.3f}      {'YES' if r['disturbed'] else 'no'}")
    L += ["-" * 74,
          f"NORMAL TELEPORTATION   mean fidelity: {res['mean_fidelity_normal']:.4f}",
          f"ATTACKED TELEPORTATION mean fidelity: {res['mean_fidelity_attacked']:.4f} "
          f"(min {res['min_fidelity_attacked']:.4f})",
          f"Disturbed qubits: {res['disturbed_qubits']} / {len(res['rows'])} "
          f"(X-basis qubits in this message: {res['sensitive_qubits']})",
          "Disturbance detected: " + ("YES" if res["detected"] else "NO")]
    return "\n".join(L)


def format_tamper_report(analysis: dict) -> str:
    return "\n".join([
        f"ATTACK TYPE:\n{analysis['attack_type']}", "",
        f"STATUS:\n{'DETECTED' if analysis['attack_detected'] else 'NOT DETECTED'}", "",
        f"INTEGRITY:\n{'COMPROMISED' if not analysis['message_integrity'] else 'INTACT'}",
    ])
