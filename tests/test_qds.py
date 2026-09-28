"""
tests/test_qds.py - PART 14 automated tests.  Run:  python -m pytest -v

Every simulator run uses a fixed seed. Where physics makes an outcome random
(no-correction runs) the tests assert on many runs so they cannot flake.
"""

import copy
import hashlib

import numpy as np
import pytest

from qds.attacks import compare_normal_vs_attacked, tamper_message
from qds.config import FIDELITY_THRESHOLD
from qds.logger import Logger
from qds.message import hash_hex_to_bits, process_message, sha256_hex
from qds.quantum_encoding import encode_bits, encode_hash, select_hash_bits, expected_bloch
from qds.security_suite import run_security_suite
from qds.signature import (compute_checksum, generate_signature, load_signature,
                           save_signature)
from qds.threat_analysis import analyze_threat
from qds.verification import verify_signature
from teleportation.teleportation import get_backend, teleport_state

MSG = "HELLO CKCET"


@pytest.fixture(scope="module")
def backend():
    return get_backend()


@pytest.fixture(scope="module")
def signature(backend):
    return generate_signature(MSG, backend=backend)


# --- SHA-256 ---------------------------------------------------------------
def test_sha256_known_vector():
    assert sha256_hex("abc") == ("ba7816bf8f01cfea414140de5dae2223"
                                 "b00361a396177a9cb410ff61f20015ad")


def test_process_message_matches_hashlib():
    info = process_message(MSG)
    assert info["sha256_hex"] == hashlib.sha256(MSG.encode()).hexdigest()
    assert bytes(info["utf8_bytes"]).decode() == MSG
    assert len(info["sha256_bits"]) == 256
    assert int(info["sha256_bits"], 2) == int(info["sha256_hex"], 16)


def test_empty_message_rejected():
    with pytest.raises(ValueError):
        process_message("")


# --- hash-bit extraction & encoding ------------------------------------------
def test_hash_bit_extraction_is_deterministic():
    h = sha256_hex(MSG)
    assert select_hash_bits(h) == select_hash_bits(h)
    assert len(select_hash_bits(h)) == 16
    assert select_hash_bits(h) == hash_hex_to_bits(h)[:16]
    assert select_hash_bits(h) == "0101111000001010"      # known for "HELLO CKCET"


def test_encoding_table():
    s = encode_bits("00011011")
    assert [x["label"] for x in s] == ["|0>", "|1>", "|+>", "|->"]
    assert np.allclose([x["theta"] for x in s], [0, np.pi, np.pi / 2, -np.pi / 2])


def test_encoding_rejects_bad_input():
    for bad in ("", "101", "01x0"):
        with pytest.raises(ValueError):
            encode_bits(bad)


def test_message_hash_encodes_to_expected_states():
    _, states = encode_hash(sha256_hex(MSG))
    assert [s["label"] for s in states] == ["|1>", "|1>", "|->", "|+>", "|0>", "|0>", "|+>", "|+>"]


# --- teleportation & fidelity --------------------------------------------------
@pytest.mark.parametrize("theta", [0.0, np.pi / 3, np.pi / 2, 2 * np.pi / 3, np.pi, -np.pi / 2])
def test_teleportation_fidelity_is_one(theta, backend):
    r = teleport_state(theta, corrections=True, seed=5, backend=backend)
    assert r["fidelity"] > FIDELITY_THRESHOLD
    assert np.allclose(r["bob_bloch"], expected_bloch(theta), atol=1e-6)


def test_teleportation_without_corrections_fails_sometimes(backend):
    fids = [teleport_state(2 * np.pi / 3, corrections=False, seed=s, backend=backend)["fidelity"]
            for s in range(12)]
    assert min(fids) < 0.9          # wrong for any Alice outcome other than 00


def test_original_teleportation_program_still_works(backend):
    """Regression guard for the untouched test_quantum.py."""
    import test_quantum
    fids, _ = test_quantum.average_fidelity(backend, corrections=True, runs=4, base_seed=100)
    assert min(fids) > 0.999999
    assert test_quantum.build_teleportation_circuit(test_quantum.THETA).num_qubits == 3


# --- signature generation ------------------------------------------------------
def test_signature_structure(signature):
    for key in ("message_hash", "selected_hash_bits", "qubit_records",
                "quantum_measurements", "teleportation_results",
                "metadata", "signature_checksum"):
        assert key in signature
    assert signature["message_hash"] == sha256_hex(MSG)
    assert isinstance(signature, dict) and signature["signature_checksum"] != signature["message_hash"]
    assert len(signature["qubit_records"]) == 8
    assert signature["teleportation_results"]["all_qubits_passed"]
    assert compute_checksum(signature) == signature["signature_checksum"]


def test_signature_json_round_trip(signature, tmp_path, backend):
    path = save_signature(signature, tmp_path / "sig.json")
    loaded = load_signature(path)
    assert loaded == signature
    assert verify_signature(MSG, loaded, backend=backend)["signature_valid"]


# --- verification --------------------------------------------------------------
def test_valid_signature_verifies(signature, backend):
    v = verify_signature(MSG, signature, backend=backend)
    assert v["signature_valid"]
    assert all(c["passed"] for c in v["checks"].values())
    assert v["fidelity_min"] > FIDELITY_THRESHOLD
    a = analyze_threat(v)
    assert a["final_status"] == "SECURE FOR THIS SIMULATION" and not a["attack_detected"]


def test_tampered_message_detected(signature, backend):
    v = verify_signature(tamper_message(MSG), signature, backend=backend)
    assert not v["signature_valid"]
    assert not v["checks"]["sha256_match"]["passed"]
    a = analyze_threat(v)
    assert a["attack_type"] == "Message Tampering"
    assert not a["message_integrity"] and a["final_status"] == "COMPROMISED"


def test_modified_signature_record_detected(signature, backend):
    forged = copy.deepcopy(signature)
    forged["message_hash"] = sha256_hex("SOMETHING ELSE")
    v = verify_signature(MSG, forged, backend=backend)
    assert not v["signature_valid"]
    assert not v["checks"]["signature_record_checksum"]["passed"]
    assert not v["checks"]["sha256_match"]["passed"]


def test_verification_rejects_malformed_signature():
    with pytest.raises(ValueError):
        verify_signature(MSG, {"nonsense": 1})


def test_verification_without_corrections_fails(signature, backend):
    v = verify_signature(MSG, signature, backend=backend, mode="no_correction")
    assert v["checks"]["sha256_match"]["passed"]           # message itself is fine
    assert not v["checks"]["teleportation_fidelity"]["passed"]
    assert not v["signature_valid"]


# --- attack simulation -----------------------------------------------------------
def test_intercept_attack_disturbs_x_basis_states(backend):
    res = compare_normal_vs_attacked(MSG, backend=backend)
    assert res["sensitive_qubits"] == 4                    # |->, |+>, |+>, |+>
    assert res["mean_fidelity_normal"] > FIDELITY_THRESHOLD
    assert res["detected"]
    for r in res["rows"]:
        if r["basis"] == "X":
            assert r["fidelity_attacked"] == pytest.approx(0.5, abs=1e-6)
        else:                                              # Z-basis states survive a Z measurement
            assert r["fidelity_attacked"] > FIDELITY_THRESHOLD


def test_intercept_attack_rejected_by_verifier(signature, backend):
    v = verify_signature(MSG, signature, backend=backend, mode="intercept")
    a = analyze_threat(v)
    assert v["checks"]["sha256_match"]["passed"] and not v["signature_valid"]
    assert a["attack_detected"] and not a["quantum_state_integrity"]
    assert a["message_integrity"]


def test_security_suite_matches_expectations(backend):
    rows = run_security_suite(MSG, backend=backend)
    assert [r["result"] for r in rows] == ["PASS", "FAIL", "FAIL", "FAIL"]
    assert all(r["as_expected"] for r in rows)


# --- logging ---------------------------------------------------------------------
def test_logger_numbering():
    log = Logger(verbose=False)
    log.step("a"); log.step("b"); log.tag("ATTACK", "c")
    assert log.lines == ["[01] a", "[02] b", "[ATTACK] c"]
