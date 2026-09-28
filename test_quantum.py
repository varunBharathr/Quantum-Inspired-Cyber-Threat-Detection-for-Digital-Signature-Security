"""
test_teleportation.py
Stage 1 of the QDS project: simulate ONLY quantum teleportation.

Qubit 0 = Alice's unknown state |psi>
Qubit 1 = Alice's half of the Bell pair
Qubit 2 = Bob's half of the Bell pair (the qubit that receives the state)

Written for Qiskit 2.5.2 and qiskit-aer 0.17.2.
"""

import numpy as np

from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister, transpile
from qiskit.quantum_info import Statevector, partial_trace, state_fidelity
from qiskit_aer import AerSimulator
from qiskit_aer.library import SaveStatevector

# ---------------------------------------------------------------------------
# The "unknown" state Alice wants to send:
#   |psi> = cos(theta/2)|0> + sin(theta/2)|1>
# theta = 2*pi/3 gives P(0) = 0.25 and P(1) = 0.75 (easy to check by eye).
# ---------------------------------------------------------------------------
THETA = 2 * np.pi / 3

# The original state as a mathematical object, used later for verification.
ORIGINAL_STATE = Statevector([np.cos(THETA / 2), np.sin(THETA / 2)])


def build_teleportation_circuit(theta, final="measure", corrections=True):
    """
    Build the teleportation circuit.

    final:
      "measure"     -> measure Bob's qubit in the Z basis (Requirement 7)
      "undo"        -> apply Ry(-theta) to Bob, then measure. If Bob holds
                       |psi>, this returns him to |0>, so he must read 0
                       every time. This tests the phase/sign too.
      "statevector" -> save the full final quantum state (for fidelity)
    corrections:
      True  -> apply Bob's X/Z corrections (the real protocol)
      False -> skip them (a "control" experiment showing they are needed)
    """
    q = QuantumRegister(3, "q")
    m0 = ClassicalRegister(1, "m0")    # Alice's bit from qubit 0 -> controls Z
    m1 = ClassicalRegister(1, "m1")    # Alice's bit from qubit 1 -> controls X
    bob = ClassicalRegister(1, "bob")  # Bob's final measurement
    qc = QuantumCircuit(q, m0, m1, bob)

    # STEP 1: Alice's unknown state. Ry(theta)|0> = cos(theta/2)|0> + sin(theta/2)|1>
    qc.ry(theta, q[0])
    qc.barrier()

    # STEP 2: Bell pair between qubit 1 (Alice) and qubit 2 (Bob).
    # H puts qubit 1 in superposition; CNOT entangles it with qubit 2,
    # giving (|00> + |11>)/sqrt(2).
    qc.h(q[1])
    qc.cx(q[1], q[2])
    qc.barrier()

    # STEP 3: Alice's Bell-state measurement.
    # CNOT (control = unknown state, target = her Bell qubit), then H on the
    # unknown-state qubit, converts the Bell basis into the Z basis.
    qc.cx(q[0], q[1])
    qc.h(q[0])
    qc.barrier()

    # STEP 4: Alice measures her two qubits -> two classical bits.
    qc.measure(q[0], m0[0])
    qc.measure(q[1], m1[0])
    qc.barrier()

    # STEP 5: Bob's corrections, controlled by Alice's classical bits
    # (this models Alice sending the 2 bits to Bob).
    # If m1 == 1 -> X;  if m0 == 1 -> Z.  Order: X first, then Z.
    if corrections:
        with qc.if_test((m1, 1)):
            qc.x(q[2])
        with qc.if_test((m0, 1)):
            qc.z(q[2])
        qc.barrier()

    # STEP 6: final action on Bob's qubit.
    if final == "measure":
        qc.measure(q[2], bob[0])
    elif final == "undo":
        qc.ry(-theta, q[2])
        qc.measure(q[2], bob[0])
    elif final == "statevector":
        qc.append(SaveStatevector(3, label="final_sv"), q)
    else:
        raise ValueError("final must be 'measure', 'undo' or 'statevector'")

    return qc


def run_counts(backend, qc, shots, seed):
    """Transpile for the simulator, run it, and return the counts dictionary."""
    tqc = transpile(qc, backend)
    return backend.run(tqc, shots=shots, seed_simulator=seed).result().get_counts()


def split_counts(counts):
    """
    Counts keys look like 'bob m1 m0' (last-added register on the left), e.g. '1 0 1'.
    Returns:
      alice[(m1, m0)] = number of times Alice got those bits
      bob_given[(m1, m0)][bob_bit] = Bob's results for each Alice outcome
      bob_total[bob_bit] = Bob's overall results
    """
    alice, bob_given, bob_total = {}, {}, {"0": 0, "1": 0}
    for key, n in counts.items():
        b, m1, m0 = key.split()
        alice[(m1, m0)] = alice.get((m1, m0), 0) + n
        bob_given.setdefault((m1, m0), {"0": 0, "1": 0})[b] += n
        bob_total[b] += n
    return alice, bob_given, bob_total


def average_fidelity(backend, corrections, runs, base_seed):
    """
    Run the circuit `runs` times with ONE shot each (each run collapses to one
    random Alice outcome), save the final statevector, extract Bob's qubit,
    and compare it with the original state.
    Returns (list of fidelities, list of Alice outcomes as 'm1m0' strings).
    """
    qc = build_teleportation_circuit(THETA, final="statevector", corrections=corrections)
    tqc = transpile(qc, backend)
    fids, outcomes = [], []
    for i in range(runs):
        result = backend.run(tqc, shots=1, seed_simulator=base_seed + i).result()
        full_state = Statevector(result.data(0)["final_sv"])   # 3-qubit state
        bob_state = partial_trace(full_state, [0, 1])          # keep only qubit 2
        fids.append(state_fidelity(bob_state, ORIGINAL_STATE))
        # Alice's classical bits for this run: the key is 'bob m1 m0'
        _, m1, m0 = next(iter(result.get_counts())).split()
        outcomes.append(m1 + m0)
    return fids, outcomes


def main():
    backend = AerSimulator()   # local simulator; no real quantum computer needed
    shots = 4000

    # ------------------------------------------------------------------
    print("=" * 70)
    print("QUANTUM TELEPORTATION SIMULATION (Qiskit 2.5.2 / Aer 0.17.2)")
    print("=" * 70)
    print(f"Unknown state: cos(theta/2)|0> + sin(theta/2)|1>, theta = {THETA:.4f} rad")
    print(f"Expected P(0) = {np.cos(THETA/2)**2:.4f}, expected P(1) = {np.sin(THETA/2)**2:.4f}\n")

    # ------------------------------------------------------------------
    # Print the circuit
    qc = build_teleportation_circuit(THETA, final="measure")
    print("QUANTUM CIRCUIT:")
    print(qc.draw(output="text"))
    print()

    # ------------------------------------------------------------------
    # Run and print Alice's and Bob's measurement results
    counts = run_counts(backend, qc, shots, seed=42)
    alice, bob_given, bob_total = split_counts(counts)

    print(f"ALICE'S MEASUREMENT RESULTS ({shots} shots), shown as (m1 m0):")
    for k in sorted(alice):
        print(f"  Alice bits {k[0]}{k[1]} : {alice[k]:5d}  ({alice[k]/shots:.3f})")
    print("  (All four outcomes should appear, each about 25%.)\n")

    print("BOB'S MEASUREMENT RESULTS (after X/Z corrections):")
    print(f"  Overall: 0 -> {bob_total['0']}, 1 -> {bob_total['1']}")
    print(f"  Measured P(1) = {bob_total['1']/shots:.4f}  (expected {np.sin(THETA/2)**2:.4f})")
    print("  Bob's results for each Alice outcome (should look the same every time):")
    for k in sorted(bob_given):
        tot = sum(bob_given[k].values())
        print(f"    Alice {k[0]}{k[1]}: P(Bob=1) = {bob_given[k]['1']/tot:.3f}")
    print()

    # ------------------------------------------------------------------
    # VERIFICATION 1: undo test.
    # If Bob really holds |psi>, then Ry(-theta) maps it back to |0>.
    undo_counts = run_counts(backend, build_teleportation_circuit(THETA, final="undo"), shots, seed=7)
    _, _, undo_total = split_counts(undo_counts)
    p_zero = undo_total["0"] / shots
    print("VERIFICATION 1 - inverse-rotation test:")
    print(f"  After Ry(-theta) on Bob, P(0) = {p_zero:.4f} (ideal = 1.0000)\n")

    # ------------------------------------------------------------------
    # VERIFICATION 2: exact statevector fidelity, Bob's state vs original.
    runs = 40
    fids, outcomes = average_fidelity(backend, corrections=True, runs=runs, base_seed=100)
    print("VERIFICATION 2 - statevector fidelity |<psi_original|psi_Bob>|^2:")
    print(f"  Runs: {runs} | Alice outcomes seen: {sorted(set(outcomes))}")
    print(f"  Minimum fidelity: {min(fids):.10f}")
    print(f"  Average fidelity: {np.mean(fids):.10f}  (ideal = 1.0)\n")

    # CONTROL: same experiment WITHOUT corrections, to show the check is real.
    ctrl, _ = average_fidelity(backend, corrections=False, runs=runs, base_seed=100)
    print("CONTROL - same experiment WITHOUT Bob's X/Z corrections:")
    print(f"  Average fidelity: {np.mean(ctrl):.4f}  (much lower, so corrections matter)\n")

    # ------------------------------------------------------------------
    # Final verdict
    success = (
        min(fids) > 0.999999
        and p_zero > 0.999
        and abs(bob_total["1"] / shots - np.sin(THETA / 2) ** 2) < 0.03
    )
    print("=" * 70)
    if success:
        print("Quantum teleportation simulation successful.")
    else:
        print("Teleportation verification FAILED - check the circuit.")
    print("=" * 70)


if __name__ == "__main__":
    main()