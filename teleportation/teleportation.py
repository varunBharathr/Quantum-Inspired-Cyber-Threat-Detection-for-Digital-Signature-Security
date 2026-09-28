"""
teleportation/teleportation.py - ADAPTER around your existing, working program.

Your original file (test_quantum.py) is NOT modified. This module imports it
and re-uses:
    build_teleportation_circuit(theta, final=..., corrections=...)
    average_fidelity(...), main()  (your original demo, kept available)

Why an adapter?  Your `average_fidelity()` is hard-wired to the global THETA,
so the QDS needs a version that takes theta as a parameter. `teleport_state()`
below does the SAME steps as `average_fidelity()` (1 shot, save statevector,
partial_trace onto Bob's qubit, state_fidelity) for any theta.

ALL Qiskit calls of the QDS live in this package (this file and intercept.py).
"""

import sys
from functools import lru_cache
from pathlib import Path

# Make the project root importable so `import test_quantum` works no matter
# where Python is launched from.
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import numpy as np
from qiskit import transpile
from qiskit.quantum_info import Statevector, partial_trace, state_fidelity
from qiskit_aer import AerSimulator

# ---- re-used from the original, untouched program -------------------------
from test_quantum import (                                  # noqa: E402
    build_teleportation_circuit,
    average_fidelity as original_average_fidelity,
    main as run_original_demo,
    THETA as ORIGINAL_THETA,
)


@lru_cache(maxsize=1)
def get_backend():
    """One shared local simulator (no real quantum hardware)."""
    return AerSimulator()


def _bloch_from_density(rho) -> list:
    """rho = (I + xX + yY + zZ)/2  ->  [x, y, z]."""
    m = np.asarray(rho.data)
    return [float(2 * m[0, 1].real), float(-2 * m[0, 1].imag),
            float((m[0, 0] - m[1, 1]).real)]


def _alice_bits(qc, counts) -> dict:
    """
    Read classical registers out of a 1-shot counts key.
    Qiskit prints the LAST register on the LEFT ('bob m1 m0'), so we reverse
    the register list before zipping.
    """
    key = next(iter(counts))
    names = [cr.name for cr in qc.cregs]
    parts = dict(zip(reversed(names), key.split()))
    return parts


def run_statevector_circuit(qc, theta, seed=None, backend=None) -> dict:
    """
    Run a circuit that ends with SaveStatevector(label='final_sv') for ONE shot
    and compare Bob's qubit (qubit 2) with the ideal state Ry(theta)|0>.
    """
    backend = backend or get_backend()
    tqc = transpile(qc, backend)
    kwargs = {} if seed is None else {"seed_simulator": int(seed)}
    result = backend.run(tqc, shots=1, **kwargs).result()

    full_state = Statevector(result.data(0)["final_sv"])          # 3 qubits
    bob_rho = partial_trace(full_state, [0, 1])                   # keep qubit 2
    expected = Statevector([np.cos(theta / 2), np.sin(theta / 2)])
    fidelity = float(state_fidelity(bob_rho, expected))

    regs = _alice_bits(qc, result.get_counts())
    return {
        "theta": float(theta),
        "alice_m0": int(regs["m0"]),
        "alice_m1": int(regs["m1"]),
        "eve_bit": int(regs["eve"]) if "eve" in regs else None,
        "bob_bloch": _bloch_from_density(bob_rho),
        "fidelity": fidelity,
    }


def teleport_state(theta, corrections=True, seed=None, backend=None) -> dict:
    """
    Teleport Ry(theta)|0> with the ORIGINAL circuit builder.
    corrections=False reproduces your 'control' experiment (no X/Z fix).
    """
    qc = build_teleportation_circuit(theta, final="statevector",
                                     corrections=corrections)
    out = run_statevector_circuit(qc, theta, seed=seed, backend=backend)
    out["corrections"] = bool(corrections)
    return out
