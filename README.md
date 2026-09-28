QDS-SAFE — Quantum Digital Signature Security Assessment & Threat Detection Framework

SIH 2026 Problem Statement: SIH26141
Title: Quantum-Inspired Cyber Threat Detection for Digital Signature Security
Type: Simulation-based cybersecurity software prototype

1. Overview

QDS-SAFE is a simulation-based framework for experimentally assessing the security and verification behaviour of a quantum-digital-signature-like workflow.

The current prototype combines:

SHA-256 message processing

deterministic quantum-state encoding

Bell-state entanglement

quantum teleportation

Pauli correction

projective measurement

structured signature records

deterministic verification

controlled attack/fault simulations

rule-based threat analysis

reproducible experiment logging

Important: This is an educational simulation, not a formally proven or standardized QDS protocol. Teleportation does not by itself create a secure digital signature.

2. SIH Alignment

The intended SIH workflow is:

Message
  ↓
Quantum-state preparation
  ↓
Bell-state / entanglement
  ↓
Teleportation + Pauli correction
  ↓
Measurement / verification
  ↓
Legitimate baseline
  ↓
Controlled attack / noise injection
  ↓
Feature extraction
  ↓
Statistical / threshold analysis
  ↓
Security decision
  ↓
Failure localization
  ↓
Detection-boundary analysis
  ↓
Improved verification
  ↓
Re-test

The current codebase implements the quantum simulation, signature-like record, verification checks and basic attack/fault experiments. The baseline-calibrated statistical layer, broader attack matrix and detection-boundary experiments are the next development layer.

3. Scope and Terminology

The project does not claim to implement a standardized production QDS protocol.

The current model:

hashes a message with SHA-256;

selects 16 hash bits;

converts each 2-bit pair into one of |0>, |1>, |+>, |->;

teleports the resulting 8 qubits;

records teleportation information;

verifies the message and quantum reconstruction;

runs controlled attack/fault experiments.

A SHA-256 hash is not called a quantum signature. The structured JSON record is a simulation artefact, not a standardized QDS signature format.

4. Quantum Model

Encoding

Bits

State

00

`

0>`

01

`

1>`

10

`

+>`

11

`

->`

The states are prepared using the corresponding Ry(theta)|0> representation.

Teleportation

Input qubit
    ↓
Shared Bell pair
    ↓
Bell measurement
    ↓
Two classical bits
    ↓
Pauli correction
    ↓
Bob's qubit
    ↓
Measurement

The simulator records Bell-measurement bits, Bob's reconstructed Bloch vector and teleportation fidelity.

5. Signature Record

The record contains:

Layer

Meaning

Classical hash

SHA-256 digest

Quantum states

8 states derived from selected hash bits

Teleportation data

measurement bits, Bloch vectors, fidelity

Record integrity

SHA-256 checksum

This record demonstrates an experimental signature-like workflow; it does not provide production cryptographic authentication.

6. Verification

The current verifier performs six checks:

Record checksum

SHA-256 message match

Selected hash-bit match

State encoding match

Teleportation re-run fidelity

Bob's reconstructed Bloch-vector comparison

ALL CHECKS PASS → VALID

ANY CHECK FAILS → VERIFICATION FAILURE

Teleportation fidelity alone is not treated as proof of message integrity.

7. Threat Model

QDS-SAFE separates adversarial attacks from ordinary degradation.

Adversarial scenarios

Forgery

Impersonation

Replay

Unauthorized verification

Quantum-channel manipulation

Repudiation-related scenarios

Non-adversarial degradation

Channel loss

Measurement error

Gate noise

Depolarizing noise

Bit-flip noise

Phase-flip noise

Ordinary noise is not automatically labelled as an attack.

8. Current Attack Experiments

Message tampering

Changing the message causes SHA-256 and encoding mismatches. Teleporting the tampered message can still have high fidelity, demonstrating why one quantum metric cannot be the only verification signal.

Educational intercept/measurement attack

The current experiment measures Bob's half of the Bell pair in the Z basis. This is a simplified attack model, not a complete model of quantum attacks. X-basis states can show reduced fidelity under this disturbance.

Missing Bob correction

Removing Bob's Pauli correction is used as a protocol-fault control experiment and should reduce reconstruction fidelity.

9. Security-Assessment Layer

The intended SIH extension is:

             LEGITIMATE QDS
                    ↓
            BASELINE CALIBRATION
                    ↓
        ┌───────────┴───────────┐
        ↓                       ↓
    ATTACK LAB              NOISE LAB
        └───────────┬───────────┘
                    ↓
           MEASUREMENT ENGINE
                    ↓
           STATISTICAL ENGINE
                    ↓
           SECURITY DECISION
                    ↓
            FAILURE ANALYZER
                    ↓
           DETECTION BOUNDARY
                    ↓
           IMPROVED PROFILE
                    ↓
                 RE-TEST

10. Features to Measure

Teleportation fidelity

Measurement error rate

Bell-state correlation

X/Y/Z measurement statistics

Verification outcome

Attack/no-attack ground truth

Runtime

Sample size

Measurement/test-round cost

Suggested experiment record:

experiment_id
seed
attack_type
attack_strength
noise_type
noise_strength
measurement_basis
sample_size
fidelity
error_rate
correlation
x_stat
y_stat
z_stat
decision
ground_truth

11. Statistical Detection

Do not use arbitrary rules such as error > 10% = attack.

Instead:

H0: observed behaviour is consistent with legitimate QDS behaviour.

H1: observed behaviour significantly deviates from legitimate QDS behaviour.

Candidate methods include:

confidence intervals

binomial confidence intervals

chi-square goodness-of-fit where appropriate

bootstrap confidence intervals

baseline-relative distribution comparisons

Thresholds must be calibrated from legitimate baseline experiments.

12. Detection Boundary

The main experimental question is:

At what attack/disturbance level does malicious behaviour become statistically distinguishable from legitimate system variation?

The final graph must use measured data. No numerical detection curve is claimed until the attack sweep has been executed.

13. False-Negative Analysis

Attack occurs
    ↓
Detector says legitimate
    ↓
FALSE NEGATIVE
    ↓
Analyse why
    ↓
Change verification configuration
    ↓
Re-test
    ↓
Measure FNR change

This is a core part of the security assessment.

14. Verification Profiles

Profiles are experimental operating points, not universal security rankings.

Fast

Lower measurement/test volume and faster verification.

Balanced

Moderate measurement coverage.

High-Assurance

Higher measurement coverage and stricter statistical evidence.

Compare:

detection rate

false-positive rate

false-negative rate

runtime

sample/measurement cost

15. Experiment Matrix

Profile

Clean

Noisy

Attack

Fast

✓

✓

✓

Balanced

✓

✓

✓

High-Assurance

✓

✓

✓

Vary:

attack strength

noise strength

sample size

measurement basis

verification profile

16. Quantitative Evaluation

Detection Rate

DR = detected attacks / total attacks

False Positive Rate

FPR = false alarms / legitimate trials

False Negative Rate

FNR = missed attacks / attack trials

Also measure:

teleportation fidelity

verification error rate

legitimate rejection/abort probability

runtime

computational cost

measurement/sample cost

Do not publish values until they have been experimentally measured.

17. Confusion Matrix

                         PREDICTED
                    Legitimate   Attack

ACTUAL
Legitimate              TN          FP
Attack                  FN          TP

The FN case is particularly important because it represents an attack that escaped detection.

18. Failure Report

The final dashboard/report should answer:

Test ID: QDS-XXXX
Profile: Balanced
Scenario: [INSERT EXPERIMENT]

Fidelity:          [INSERT]
Error Rate:        [INSERT]
Correlation:       [INSERT]
X/Y/Z deviation:   [INSERT]

Statistical Result:[INSERT]

Decision:          [Healthy / Degraded / Suspicious / Attack]

Failure Location:  [Protocol / Channel / Measurement / Verification]

Contributing Condition:
[INSERT EXPERIMENTAL EXPLANATION]

Next Experiment:
[INSERT]

Re-test Result:
[INSERT EXPERIMENTAL RESULT]

19. Architecture

Quantum_Digital_Signature/
├── test_quantum.py
├── teleportation/
│   ├── teleportation.py
│   └── intercept.py
├── qds/
│   ├── config.py
│   ├── message.py
│   ├── quantum_encoding.py
│   ├── signature.py
│   ├── verification.py
│   ├── attacks.py
│   ├── threat_analysis.py
│   ├── security_suite.py
│   └── logger.py
├── tests/
│   └── test_qds.py
├── signatures/
├── main.py
├── requirements.txt
├── pytest.ini
└── README.md

20. Technology Stack

Python
├── Qiskit       → quantum-circuit simulation
├── NumPy/SciPy  → numerical/statistical analysis
├── Pandas       → experiment datasets
├── Matplotlib/
│   Plotly       → experiment visualization
└── Streamlit    → security dashboard

21. Reproducibility

Experiments should record:

seed

experiment ID

attack/noise configuration

measurement basis

sample size

verification profile

measured outputs

ground truth

QDS-SAFE generates a controlled experimental dataset. It does not claim to use a real-world QDS attack dataset unless one is explicitly added and documented.

22. Installation

Windows PowerShell

python -m venv venv
.env\Scripts\Activate.ps1
pip install -r requirements.txt

If activation is blocked:

Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

23. Running

python main.py
python test_quantum.py
python -m pytest -v

24. Recommended SIH Demo

1. CLEAN QDS
   → VERIFIED

2. MESSAGE / REPLAY TAMPERING
   → DETECTED

3. CHANNEL MANIPULATION
   → STATISTICAL DEVIATION

4. LOWER ATTACK STRENGTH
   → FALSE NEGATIVE

5. CHANGE VERIFICATION PROFILE
   → RE-TEST

6. ATTACK STRENGTH SWEEP
   → DETECTION BOUNDARY + FNR CHANGE

25. Security-Property Mapping

Requirement

QDS-SAFE treatment

Unforgeability

Forgery experiments + verification mismatch

Repudiation resistance

Repudiation-oriented experiments; protocol-specific implementation required

Transferability

Future protocol-specific extension

Replay resistance

Replay scenario and protocol-state checks

Impersonation resistance

Participant/authentication scenario

Unauthorized verification

Verification/access scenario

Quantum-channel integrity

Channel manipulation experiments

26. Proposed Contribution

The project does not claim that quantum teleportation or QDS itself is novel.

The proposed software contribution is the integrated assessment workflow:

controlled attack + noise stress testing

legitimate-baseline calibration

statistical threat detection

detection-boundary discovery

false-negative analysis

failure localization

verification-profile comparison

improvement → re-test

reproducible experiment generation

This should be presented as a proposed software assessment workflow, not as a claim that no prior research performs similar activities.

27. Limitations

Simulation-based evaluation

Depends on the selected QDS-like model

Simulator noise does not reproduce every hardware effect

Statistical thresholds depend on baseline calibration

Current core verifier is deterministic/rule-based

The current educational intercept attack is only one attack strategy

No secret/public key in the current model

No formal security proof

Real-device validation is future work

Experimental performance values must be generated before being claimed

28. Roadmap

Phase 1 — Foundation

Quantum encoding, teleportation, verification and basic attack experiments.

Phase 2 — SIH Security Layer

Baseline generation, noise models, expanded attack library, statistical detection and experiment matrix.

Phase 3 — Security Analysis

Detection-boundary sweep, false-negative search, confusion matrix and failure localization.

Phase 4 — Hardware Validation

Compare simulator results with selected real quantum-hardware experiments.

Phase 5 — Broader QDS Evaluation

Support additional QDS constructions and protocol-specific benchmarking.

29. Final Project Statement

QDS-SAFE is a reproducible simulation framework for experimentally evaluating the security behaviour of a quantum-digital-signature-like workflow. It combines quantum teleportation, controlled attack/noise injection, baseline-calibrated statistical analysis, failure localization and verification re-testing to study where and under what conditions QDS verification becomes unreliable.

