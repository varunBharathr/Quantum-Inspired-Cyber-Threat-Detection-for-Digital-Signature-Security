"""
threat_analysis.py - PART 10: rule-based threat analysis.

Every output is a direct function of the verification checks (measurable
simulation results). No machine learning, no guessing.
"""


def analyze_threat(v: dict) -> dict:
    c = {k: x["passed"] for k, x in v["checks"].items()}
    message_integrity = c["sha256_match"] and c["selected_bits_match"]
    quantum_integrity = (c["teleportation_fidelity"] and c["bob_state_matches_record"]
                         and c["state_encoding_match"])
    signature_ok = bool(v["signature_valid"])
    attack_detected = not signature_ok

    if signature_ok:
        attack_type = "None"
    elif not message_integrity:
        attack_type = "Message Tampering"
    elif not c["signature_record_checksum"]:
        attack_type = "Signature Record Modification"
    elif not quantum_integrity:
        attack_type = "Quantum State Disturbance (interception / protocol failure)"
    else:
        attack_type = "Unknown inconsistency"

    return {
        "message_integrity": message_integrity,
        "quantum_state_integrity": quantum_integrity,
        "signature_verification": signature_ok,
        "attack_detected": attack_detected,
        "attack_type": attack_type,
        "final_status": "SECURE FOR THIS SIMULATION" if signature_ok else "COMPROMISED",
    }


def format_threat_report(a: dict) -> str:
    pf = lambda b: "PASS" if b else "FAIL"
    return "\n".join([
        "THREAT ANALYSIS", "-" * 60,
        f"Message Integrity        : {pf(a['message_integrity'])}",
        f"Quantum State Integrity  : {pf(a['quantum_state_integrity'])}",
        f"Signature Verification   : {pf(a['signature_verification'])}",
        f"Attack Detected          : {'YES' if a['attack_detected'] else 'NO'}",
        f"Attack Type              : {a['attack_type']}",
        f"Final Security Status    : {a['final_status']}",
    ])
