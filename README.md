HEAD
# Educational Quantum Digital Signature (QDS) Simulator

> **This is an educational simulation, not a formally proven or standardized QDS protocol.**
> It demonstrates how quantum-teleportation concepts can be wired into a
> signature-*like* workflow. It must not be used to protect real data.

## 1. What the project does
Takes a message, hashes it with SHA-256, turns selected hash bits into qubit states,
teleports those qubits with a simulated circuit, stores the results as a structured
"signature" record, and later verifies a message against it. It also simulates
message tampering, an intercept/measure attack, and a protocol fault (no Bob correction),
and reports the outcome with a rule-based threat analysis.

## 2. Why teleportation?
Teleportation moves an unknown qubit state using a shared Bell pair plus two classical
bits. It is a compact, testable way to show *entanglement*, *measurement*, *classical
communication* and *fidelity*. Teleportation does **not** by itself create a secure
digital signature - it is the quantum building block this prototype experiments with.

## 3. What "QDS" means here
The signature is a record bundling four different things:
| Layer | Meaning |
|---|---|
| classical hash | SHA-256 of the message (`hashlib`) |
| quantum states | 8 qubits encoded from the first 16 hash bits |
| teleportation data | Alice's Bell-measurement bits, Bob's Bloch vectors, fidelities |
| QDS signature | the JSON record combining the above plus a SHA-256 checksum |

A bare SHA-256 hash is **not** called a quantum signature anywhere in this project.

## 4. Architecture
```
Quantum_Digital_Signature/
├── test_quantum.py            ORIGINAL working teleportation program (UNTOUCHED)
├── teleportation/
│   ├── teleportation.py       adapter: imports test_quantum, teleport_state(theta)
│   └── intercept.py           intercept/measure attack circuit (Qiskit)
├── qds/                       (no Qiskit imports in here)
│   ├── config.py              constants, thresholds, seeds
│   ├── message.py             message -> bytes -> SHA-256 -> bits
│   ├── quantum_encoding.py    hash bits -> qubit states
│   ├── signature.py           signature generation / save / load
│   ├── verification.py        6-check verifier
│   ├── attacks.py             tampering, channel modes, normal-vs-attacked
│   ├── threat_analysis.py     rule-based PASS/FAIL analysis
│   ├── security_suite.py      the 4 required tests + summary table
│   └── logger.py              [01].. / [ATTACK] logs
├── tests/test_qds.py          pytest suite
├── signatures/                saved signature JSON files
├── main.py                    CLI menu
├── requirements.txt  pytest.ini  README.md
```

## 5. Installation (Windows PowerShell, inside the project folder)
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```
(If activation is blocked: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`.)

## 6. Running
```powershell
python main.py              # the QDS simulator menu
python test_quantum.py      # your original teleportation demo, unchanged
python -m pytest -v         # automated tests
```

## 7. Signature-generation flow
1. Message received -> UTF-8 bytes -> SHA-256.
2. First 16 hash bits selected (deterministic).
3. Each 2-bit pair -> one qubit: `00:|0>  01:|1>  10:|+>  11:|->`, prepared as `Ry(theta)|0>`.
4. Each qubit is teleported with the original circuit (Bell pair, Bell measurement, X/Z correction).
5. Alice's bits, Bob's reconstructed Bloch vector and the fidelity are recorded per qubit.
6. The record gets a SHA-256 checksum and is saved to `signatures/last_signature.json`.

## 8. Verification flow (six independent checks)
Record checksum · SHA-256 match · selected bits match · state encoding match ·
teleportation re-run fidelity >= 0.999999 · Bob's re-run Bloch vectors equal the recorded ones.
The signature is valid only if **all six** pass. Alice's random measurement bits are *not*
compared (they differ every run by design); the deterministic reconstructed state is.

## 9. Attack simulation
* **Message tampering** - `HELLO CKCET` -> `HELLO CKCET 123`: SHA-256 mismatch, Bloch/encoding mismatch.
  Note that teleporting the tampered message's states still has fidelity ~1: teleportation is
  working fine, so the hash/record checks are what catch this. That is why one check is never enough.
* **Educational intercept/measurement attack simulation** - Eve measures Bob's half of the Bell pair in
  the Z basis. This breaks the entanglement. |0>/|1> survive (fidelity 1.0); |+>/|-> drop to 0.5.
  For `HELLO CKCET` four of the eight qubits are X-basis, so the attack is detected.
  It is one simplified strategy, **not** every possible quantum attack.
* **No Bob correction** - protocol fault control: fidelity drops, verification fails.

## 10. Limitations
* No secret/public key: anyone can generate a "valid" signature for any message. This shows
  integrity checking, **not authenticity or non-repudiation**.
* The verifier recomputes states from the message, so the "quantum data" is reproducible, not a
  one-time quantum token; real QDS schemes (e.g. Gottesman-Chuang) use quantum public keys.
* Intercept detection needs at least one X-basis qubit; a message whose 16 selected bits are all
  Z-basis (probability 1/256) would pass the interception test. The hash check still works.
* Ideal, noiseless simulator; only one attack model; no formal security proof; 16 of 256 hash bits
  feed the quantum part (the full hash is still compared classically).

## 11. Future improvements
Add a secret key (e.g. HMAC or a real signature scheme) for authenticity; noise models
(`qiskit_aer.noise`); multiple attack bases (random-basis interception); more hash bits / qubits;
swap-test based state comparison; Flask/React front-end.

# Quantum-Inspired-Cyber-Threat-Detection-for-Digital-Signature-Security
A simulation-based QDS security assessment framework that detects threats, discovers verification failure boundaries, and experimentally measures improvements in security verification.
 a42883a13d0a9aa187d63ec01353d474890bdbb5