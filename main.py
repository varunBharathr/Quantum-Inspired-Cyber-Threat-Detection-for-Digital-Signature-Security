"""
main.py - PART 13: command-line interface for the educational QDS simulator.

Run:  python main.py
"""

import sys

if hasattr(sys.stdout, "reconfigure"):          # keep ✓ ✗ ⚠ printable on Windows
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from pathlib import Path

from qds.attacks import (compare_normal_vs_attacked, format_attack_comparison,
                         format_tamper_report, tamper_message)
from qds.config import DEFAULT_MESSAGE
from qds.logger import Logger
from qds.message import format_message_report, process_message
from qds.quantum_encoding import encode_hash, format_encoding_report
from qds.security_suite import format_summary_table, run_security_suite
from qds.signature import (format_signature_summary, generate_signature,
                           load_signature, save_signature)
from qds.threat_analysis import analyze_threat, format_threat_report
from qds.verification import format_verification_report, verify_signature

SIG_FILE = Path(__file__).resolve().parent / "signatures" / "last_signature.json"
STATE = {"signature": None, "message": None}

BANNER = """
========================================
 QUANTUM DIGITAL SIGNATURE SIMULATOR
 (educational prototype - not a formally
  proven or standardized QDS protocol)
========================================
1. Generate Signature
2. Verify Signature
3. Simulate Message Tampering
4. Simulate Quantum Interception Attack
5. Run Complete Security Test
6. Exit
"""


def ask(prompt, default=None):
    text = input(f"{prompt}" + (f" [{default}]" if default else "") + ": ").strip()
    return text or default


def ensure_signature():
    """Use the signature from this session, else the saved file, else make one."""
    if STATE["signature"] is None and SIG_FILE.exists():
        STATE["signature"] = load_signature(SIG_FILE)
        print(f"(loaded saved signature from {SIG_FILE.name})")
    if STATE["signature"] is None:
        print(f"No signature yet - generating one for {DEFAULT_MESSAGE!r} first.\n")
        do_generate(DEFAULT_MESSAGE)
    return STATE["signature"]


def do_generate(message=None):
    message = message or ask("Enter message to sign", DEFAULT_MESSAGE)
    info = process_message(message)
    print("\n" + format_message_report(info) + "\n")
    bits, states = encode_hash(info["sha256_hex"])
    print(format_encoding_report(bits, states) + "\n")
    sig = generate_signature(message, log=Logger(verbose=True))
    save_signature(sig, SIG_FILE)
    STATE["signature"], STATE["message"] = sig, message
    print("\n" + format_signature_summary(sig))
    print(f"\nSaved to {SIG_FILE}")


def do_verify():
    sig = ensure_signature()
    default = STATE["message"] or DEFAULT_MESSAGE
    message = ask("Enter the message to verify", default)
    v = verify_signature(message, sig, log=Logger(verbose=True))
    print("\n" + format_verification_report(v))
    print("\n" + format_threat_report(analyze_threat(v)))


def do_tamper():
    sig = ensure_signature()
    original = STATE["message"] or DEFAULT_MESSAGE
    print(f"\nOriginal message : {original}")
    tampered = ask("Attacker's modified message", tamper_message(original))
    log = Logger(verbose=True)
    log.tag("ATTACK", f"Message modified: {original!r} -> {tampered!r}")
    v = verify_signature(tampered, sig, log=log)
    a = analyze_threat(v)
    print("\n" + format_verification_report(v))
    print("\n" + format_threat_report(a))
    print("\n" + format_tamper_report(a))


def do_intercept():
    original = STATE["message"] or ask("Message", DEFAULT_MESSAGE)
    res = compare_normal_vs_attacked(original, log=Logger(verbose=True))
    print("\n" + format_attack_comparison(res))


def do_suite():
    message = ask("Message for the security test", DEFAULT_MESSAGE)
    rows = run_security_suite(message, log=Logger(verbose=True))
    print("\n" + format_summary_table(rows))


ACTIONS = {"1": do_generate, "2": do_verify, "3": do_tamper,
           "4": do_intercept, "5": do_suite}


def main():
    while True:
        print(BANNER)
        choice = ask("Choose")
        if choice == "6":
            print("Goodbye.")
            return
        action = ACTIONS.get(choice)
        if action is None:
            print("Please enter a number from 1 to 6.")
            continue
        try:
            print()
            action()
        except (KeyboardInterrupt, EOFError):
            print("\nCancelled.")
            return
        except Exception as exc:                   # keep the menu alive
            print(f"\nERROR: {type(exc).__name__}: {exc}")


if __name__ == "__main__":
    main()
