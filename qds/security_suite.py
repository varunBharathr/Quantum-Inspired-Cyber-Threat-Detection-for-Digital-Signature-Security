"""
security_suite.py - PART 9: runs the four required tests and prints the table.
"""

from teleportation.teleportation import get_backend

from .attacks import tamper_message
from .config import DEFAULT_MESSAGE
from .logger import Logger
from .signature import generate_signature
from .threat_analysis import analyze_threat
from .verification import verify_signature


def run_security_suite(message=DEFAULT_MESSAGE, backend=None, log=None) -> list:
    log = log or Logger(verbose=False)
    backend = backend or get_backend()

    log.tag("SUITE", f"Signing {message!r}")
    sig = generate_signature(message, backend=backend, log=log)

    cases = [
        ("1 Valid message + valid signature", "None", message, "normal", "PASS"),
        ("2 Modified message + original sig", "Message Tampering",
         tamper_message(message), "normal", "FAIL"),
        ("3 Intercept/measure attack", "Intercept/Measure (edu)",
         message, "intercept", "FAIL"),
        ("4 Teleportation w/o Bob correction", "No X/Z correction",
         message, "no_correction", "FAIL"),
    ]
    rows = []
    for name, attack, msg, mode, expected in cases:
        log.tag("TEST", name)
        v = verify_signature(msg, sig, backend=backend, mode=mode)
        a = analyze_threat(v)
        result = "PASS" if v["signature_valid"] else "FAIL"
        rows.append({"test": name, "attack": attack, "expected": expected,
                     "fidelity_mean": v["fidelity_mean"], "fidelity_min": v["fidelity_min"],
                     "hash_match": v["checks"]["sha256_match"]["passed"],
                     "result": result, "as_expected": result == expected,
                     "attack_detected": a["attack_detected"], "final_status": a["final_status"]})
    return rows


def format_summary_table(rows: list) -> str:
    head = (f"{'Test':<36} {'Attack':<24} {'Fidelity mean (min)':<21} "
            f"{'Hash':<6} {'Result':<7} {'Expected':<9} OK?")
    L = [head, "-" * len(head)]
    for r in rows:
        fid = f"{r['fidelity_mean']:.4f} ({r['fidelity_min']:.4f})"
        L.append(f"{r['test']:<36} {r['attack']:<24} {fid:<21} "
                 f"{'YES' if r['hash_match'] else 'NO':<6} {r['result']:<7} "
                 f"{r['expected']:<9} {'✓' if r['as_expected'] else '✗'}")
    ok = all(r["as_expected"] for r in rows)
    L.append("-" * len(head))
    L.append("ALL TESTS BEHAVED AS EXPECTED" if ok else "SOME TESTS DID NOT BEHAVE AS EXPECTED")
    return "\n".join(L)
