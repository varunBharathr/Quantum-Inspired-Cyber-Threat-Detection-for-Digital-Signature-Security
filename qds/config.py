"""
config.py - every tunable constant of the QDS prototype lives here.
"""

SCHEME_NAME = "EDU-QDS-TELEPORT-v1"     # NOT a standardized protocol
DEFAULT_MESSAGE = "HELLO CKCET"

# --- Quantum encoding ------------------------------------------------------
BITS_PER_QUBIT = 2      # 1 bit chooses the basis (Z or X), 1 bit chooses the value
N_QUBITS = 8            # 8 qubits x 2 bits = the first 16 bits of the SHA-256 hash

# --- Verification thresholds ----------------------------------------------
FIDELITY_THRESHOLD = 0.999999   # ideal simulator teleportation gives ~1.0
BLOCH_TOLERANCE = 1e-5          # max distance between Bloch vectors (record vs rerun)

# --- Reproducibility (simulator seeds) -------------------------------------
SIGN_SEED = 1000
VERIFY_SEED = 2000
ATTACK_SEED = 3000

# Without Bob's correction each Alice outcome is random, so a single run can
# look "fine" by luck. We take the worst of a few runs per qubit.
NO_CORRECTION_REPEATS = 4
