"""
teleportation/intercept.py - EDUCATIONAL intercept/measure attack circuit.

WHAT IS MODELLED
In teleportation the state itself never travels. What Alice and Bob share is
the Bell pair, and Bob's half must reach him. Here an eavesdropper (Eve)
intercepts Bob's half of the Bell pair on its way to Bob and MEASURES it in the
Z basis, then the protocol continues normally (Alice measures, Bob corrects).

Measuring Bob's half collapses the Bell pair to |00> or |11>, so the
entanglement is destroyed. Bob then ends up with a Z-basis state |x> instead of
psi:
    * psi = |0> or |1>   -> Bob still gets the right state (fidelity 1.0)
    * psi = |+> or |->   -> fidelity 0.5  (disturbance is visible)

WHY A SEPARATE BUILDER?  The original build_teleportation_circuit() has no place
to insert Eve, and it must stay untouched. This circuit is gate-for-gate the
same as the original, with ONE extra measurement (marked EVE).

This is a simplified single-strategy model, NOT every possible quantum attack.
"""

from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit_aer.library import SaveStatevector

from .teleportation import run_statevector_circuit


def build_intercepted_circuit(theta):
    q = QuantumRegister(3, "q")
    m0 = ClassicalRegister(1, "m0")
    m1 = ClassicalRegister(1, "m1")
    bob = ClassicalRegister(1, "bob")
    eve = ClassicalRegister(1, "eve")          # Eve's measurement result
    qc = QuantumCircuit(q, m0, m1, bob, eve)

    qc.ry(theta, q[0])                          # Alice's state
    qc.h(q[1])                                  # Bell pair (same as original)
    qc.cx(q[1], q[2])
    qc.barrier()

    qc.measure(q[2], eve[0])                    # EVE: intercept + measure Bob's half
    qc.barrier()

    qc.cx(q[0], q[1])                           # Alice's Bell measurement
    qc.h(q[0])
    qc.measure(q[0], m0[0])
    qc.measure(q[1], m1[0])
    qc.barrier()

    with qc.if_test((m1, 1)):                   # Bob's normal corrections
        qc.x(q[2])
    with qc.if_test((m0, 1)):
        qc.z(q[2])
    qc.append(SaveStatevector(3, label="final_sv"), q)
    return qc


def intercept_state(theta, seed=None, backend=None) -> dict:
    """Teleport Ry(theta)|0> while Eve measures Bob's Bell-pair half."""
    out = run_statevector_circuit(build_intercepted_circuit(theta), theta,
                                  seed=seed, backend=backend)
    out["corrections"] = True
    return out
