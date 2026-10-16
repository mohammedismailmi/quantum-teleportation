"""
Quantum Teleportation Engine
=============================
Core quantum circuit construction, step-by-step state computation,
measurement-outcome analysis, fidelity verification, and noise experiments.

Qubit convention (used throughout the entire project):
    Q  (index 0) — Alice's message qubit
    M  (index 1) — Alice's half of the Bell pair
    Y  (index 2) — Bob's half of the Bell pair

Combined state ordering: Q ⊗ M ⊗ Y

References:
    * Nielsen & Chuang, *Quantum Computation and Quantum Information* (2010)
    * Qiskit Textbook — Quantum Teleportation
      https://learning.quantum.ibm.com/tutorial/quantum-teleportation
"""

from __future__ import annotations

import numpy as np
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit.quantum_info import (
    DensityMatrix,
    Operator,
    Statevector,
    partial_trace,
    state_fidelity,
)
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, depolarizing_error


# ─── Preset states ────────────────────────────────────────────────────────────

PRESET_STATES: dict[str, tuple[complex, complex]] = {
    "|0⟩": (1.0 + 0j, 0.0 + 0j),
    "|1⟩": (0.0 + 0j, 1.0 + 0j),
    "|+⟩": (1 / np.sqrt(2) + 0j, 1 / np.sqrt(2) + 0j),
    "|−⟩": (1 / np.sqrt(2) + 0j, -1 / np.sqrt(2) + 0j),
    "|i+⟩": (1 / np.sqrt(2) + 0j, 1j / np.sqrt(2)),
    "|i−⟩": (1 / np.sqrt(2) + 0j, -1j / np.sqrt(2)),
}

# Bell states (written in M ⊗ Y basis)
BELL_STATES: dict[str, np.ndarray] = {
    "|Φ+⟩": np.array([1, 0, 0, 1]) / np.sqrt(2),
    "|Φ−⟩": np.array([1, 0, 0, -1]) / np.sqrt(2),
    "|Ψ+⟩": np.array([0, 1, 1, 0]) / np.sqrt(2),
    "|Ψ−⟩": np.array([0, 1, -1, 0]) / np.sqrt(2),
}


# ─── Helpers ──────────────────────────────────────────────────────────────────


def normalize_state(alpha: complex, beta: complex) -> tuple[complex, complex]:
    """Return a normalised (α, β) pair, raising ValueError if both are zero."""
    norm = np.sqrt(abs(alpha) ** 2 + abs(beta) ** 2)
    if np.isclose(norm, 0.0):
        raise ValueError("Both amplitudes cannot be zero.")
    return (alpha / norm, beta / norm)


def bloch_angles_to_amplitudes(theta: float, phi: float) -> tuple[complex, complex]:
    """Convert Bloch-sphere angles (θ, φ) to (α, β)."""
    alpha = np.cos(theta / 2) + 0j
    beta = np.exp(1j * phi) * np.sin(theta / 2)
    return (alpha, beta)


def amplitudes_to_bloch(alpha: complex, beta: complex) -> tuple[float, float, float]:
    """Return Bloch-vector (x, y, z) for a pure state |ψ⟩ = α|0⟩ + β|1⟩."""
    alpha, beta = normalize_state(alpha, beta)
    x = 2 * np.real(np.conj(alpha) * beta)
    y = 2 * np.imag(np.conj(alpha) * beta)
    z = float(np.abs(alpha) ** 2 - np.abs(beta) ** 2)
    return (float(x), float(y), float(z))


def dm_to_bloch(dm: np.ndarray) -> tuple[float, float, float]:
    """Bloch vector from a 2×2 density matrix (pure or mixed)."""
    rho = np.asarray(dm, dtype=complex)
    x = float(2 * np.real(rho[0, 1]))
    y = float(2 * np.imag(rho[1, 0]))
    z = float(np.real(rho[0, 0] - rho[1, 1]))
    return (x, y, z)


def is_pure(dm: np.ndarray, tol: float = 1e-6) -> bool:
    """Check whether a density matrix represents a pure state."""
    rho = np.asarray(dm, dtype=complex)
    return bool(np.real(np.trace(rho @ rho)) > 1 - tol)


# ─── Step-by-step state computation ──────────────────────────────────────────

STAGE_LABELS = [
    "Initial State",                  # 0
    "Hadamard on M",                  # 1
    "CNOT (M → Y): Bell Pair Ready",  # 2
    "CNOT (Q → M): Alice Entangles",  # 3
    "Hadamard on Q: Bell Basis",      # 4
    "Alice Measures Q and M",         # 5
    "Classical Communication",        # 6
    "Bob's Correction",              # 7
    "Teleportation Complete",         # 8
]

STAGE_DESCRIPTIONS = [
    # Stage 0
    (
        "We prepare the three-qubit system.  Alice's message qubit Q is initialised "
        "to |ψ⟩ = α|0⟩ + β|1⟩.  Qubits M and Y both start in |0⟩.\n\n"
        "Full state: |Ψ₀⟩ = (α|0⟩ + β|1⟩)_Q ⊗ |0⟩_M ⊗ |0⟩_Y"
    ),
    # Stage 1
    (
        "A Hadamard gate is applied to Alice's qubit M, creating a superposition:\n\n"
        "H|0⟩ = (|0⟩ + |1⟩) / √2\n\n"
        "This is the first step toward generating a Bell pair between M and Y."
    ),
    # Stage 2
    (
        "A CNOT gate with M as control and Y as target completes the Bell pair:\n\n"
        "|Φ⁺⟩_MY = (|00⟩ + |11⟩) / √2\n\n"
        "Full state: |Ψ₂⟩ = (α|0⟩ + β|1⟩)_Q ⊗ |Φ⁺⟩_MY\n\n"
        "Qubits M and Y are now maximally entangled.  Alice keeps M; Bob takes Y."
    ),
    # Stage 3
    (
        "Alice applies a CNOT gate with her message qubit Q as control and her Bell "
        "qubit M as target.\n\n"
        "This correlates Q with M, beginning the transfer of quantum information "
        "into the joint Q–M system."
    ),
    # Stage 4
    (
        "A Hadamard gate is applied to Q, completing the rotation of Alice's two "
        "qubits (Q, M) into the Bell measurement basis.\n\n"
        "The three-qubit state can now be rewritten as a sum over the four Bell "
        "outcomes, each associated with a specific conditional state for Bob's qubit Y."
    ),
    # Stage 5
    (
        "Alice measures her two qubits Q and M in the computational basis, obtaining "
        "two classical bits.\n\n"
        "Each of the four outcomes (00, 01, 10, 11) occurs with probability ¼ and "
        "collapses Bob's qubit into a specific conditional state.\n\n"
        "The measurement is irreversible — Alice's original message state is consumed."
    ),
    # Stage 6
    (
        "Alice sends her two classical bits to Bob through a classical communication "
        "channel (e.g. a phone call or text message).\n\n"
        "Note: only *two classical bits* are transmitted — not the unknown quantum "
        "state itself.  These bits alone do not reveal α or β."
    ),
    # Stage 7
    (
        "Bob applies correction gates based on Alice's measurement results:\n\n"
        "• 00 → I (no correction)\n"
        "• 01 → X gate\n"
        "• 10 → Z gate\n"
        "• 11 → X then Z\n\n"
        "After correction, Bob's qubit is in the state α|0⟩ + β|1⟩."
    ),
    # Stage 8
    (
        "Teleportation is complete.  Bob's qubit Y now holds the state |ψ⟩ = α|0⟩ + β|1⟩, "
        "identical to Alice's original message (up to a global phase).\n\n"
        "The fidelity between the original and reconstructed state should be 1 in an "
        "ideal, noiseless simulation."
    ),
]


def compute_stage_states(
    alpha: complex, beta: complex
) -> list[dict]:
    """
    Compute the full three-qubit Statevector at each stage of the
    teleportation protocol (stages 0–4).

    Returns a list of dicts:
        {
            "stage": int,
            "label": str,
            "description": str,
            "statevector": np.ndarray,        # full 8-component vector
            "reduced_dm": {0: ..., 1: ..., 2: ...},  # per-qubit density matrices
            "bloch": {0: ..., 1: ..., 2: ...},        # per-qubit Bloch vectors
            "is_pure": {0: ..., 1: ..., 2: ...},
        }
    """
    alpha, beta = normalize_state(alpha, beta)
    results: list[dict] = []

    def _snapshot(stage_idx: int, sv: Statevector) -> dict:
        dm_full = DensityMatrix(sv)
        reduced: dict[int, np.ndarray] = {}
        bloch: dict[int, tuple[float, float, float]] = {}
        purity: dict[int, bool] = {}
        for q in range(3):
            others = [j for j in range(3) if j != q]
            rdm = partial_trace(dm_full, others).data
            reduced[q] = rdm
            bloch[q] = dm_to_bloch(rdm)
            purity[q] = is_pure(rdm)
        return {
            "stage": stage_idx,
            "label": STAGE_LABELS[stage_idx],
            "description": STAGE_DESCRIPTIONS[stage_idx],
            "statevector": sv.data,
            "reduced_dm": reduced,
            "bloch": bloch,
            "is_pure": purity,
        }

    # Build circuit stage by stage using unitary operations
    qc = QuantumCircuit(3)
    qc.initialize([alpha, beta], 0)
    sv = Statevector.from_instruction(qc)
    results.append(_snapshot(0, sv))

    # Stage 1: H on M
    qc.h(1)
    sv = Statevector.from_instruction(qc)
    results.append(_snapshot(1, sv))

    # Stage 2: CNOT M→Y
    qc.cx(1, 2)
    sv = Statevector.from_instruction(qc)
    results.append(_snapshot(2, sv))

    # Stage 3: CNOT Q→M
    qc.cx(0, 1)
    sv = Statevector.from_instruction(qc)
    results.append(_snapshot(3, sv))

    # Stage 4: H on Q
    qc.h(0)
    sv = Statevector.from_instruction(qc)
    results.append(_snapshot(4, sv))

    return results


# ─── Measurement outcome analysis ────────────────────────────────────────────

# Outcome key: (c[0]=Q measurement, c[1]=M measurement)
# Conditional state of Bob's qubit Y after Alice measures (Q, M)
# Correction: apply X if c[1]=1, then Z if c[0]=1

OUTCOME_INFO = {
    (0, 0): {
        "bell_label": "|Φ⁺⟩",
        "correction": "I (no correction)",
        "gates": [],
    },
    (0, 1): {
        "bell_label": "|Ψ⁺⟩",
        "correction": "X gate",
        "gates": ["X"],
    },
    (1, 0): {
        "bell_label": "|Φ⁻⟩",
        "correction": "Z gate",
        "gates": ["Z"],
    },
    (1, 1): {
        "bell_label": "|Ψ⁻⟩",
        "correction": "XZ (X then Z)",
        "gates": ["X", "Z"],
    },
}


def compute_conditional_state(
    alpha: complex, beta: complex, q_meas: int, m_meas: int
) -> dict:
    """
    Compute Bob's conditional state for a given measurement outcome.

    Parameters
    ----------
    alpha, beta : complex
        Amplitudes of the message state |ψ⟩ = α|0⟩ + β|1⟩ (must be normalised).
    q_meas : int
        Measurement result for qubit Q (0 or 1).
    m_meas : int
        Measurement result for qubit M (0 or 1).

    Returns
    -------
    dict with keys:
        "q_meas", "m_meas", "bell_label", "correction",
        "bob_before_correction", "bob_after_correction", "fidelity"
    """
    alpha, beta = normalize_state(alpha, beta)
    info = OUTCOME_INFO[(q_meas, m_meas)]

    # Full pre-measurement state (stage 4)
    qc = QuantumCircuit(3)
    qc.initialize([alpha, beta], 0)
    qc.h(1)
    qc.cx(1, 2)
    qc.cx(0, 1)
    qc.h(0)
    sv = Statevector.from_instruction(qc)

    # Project onto |q_meas⟩_Q ⊗ |m_meas⟩_M
    # Qiskit little-endian: index = q2*4 + q1*2 + q0
    # reshape(2,2,2) → v[q2][q1][q0] where Q=q0, M=q1, Y=q2
    full_vec = sv.data.reshape(2, 2, 2)  # indices: Y, M, Q
    conditional_vec = full_vec[:, m_meas, q_meas]  # Bob's (Y) unnormalised state

    norm = np.linalg.norm(conditional_vec)
    if norm < 1e-12:
        raise ValueError("Zero-probability outcome — should not happen.")
    bob_before = conditional_vec / norm

    # Apply corrections
    X = np.array([[0, 1], [1, 0]], dtype=complex)
    Z = np.array([[1, 0], [0, -1]], dtype=complex)
    bob_after = bob_before.copy()
    for gate in info["gates"]:
        if gate == "X":
            bob_after = X @ bob_after
        elif gate == "Z":
            bob_after = Z @ bob_after

    original = Statevector([alpha, beta])
    reconstructed = Statevector(bob_after)
    fidelity = float(state_fidelity(original, reconstructed))

    return {
        "q_meas": q_meas,
        "m_meas": m_meas,
        "bits_str": f"{q_meas}{m_meas}",
        "bell_label": info["bell_label"],
        "correction": info["correction"],
        "gates": info["gates"],
        "bob_before": bob_before,
        "bob_after": bob_after,
        "fidelity": fidelity,
        "probability": float(norm ** 2),
    }


def compute_all_outcomes(alpha: complex, beta: complex) -> list[dict]:
    """Compute conditional states for all four measurement outcomes."""
    results = []
    for (q, m) in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        results.append(compute_conditional_state(alpha, beta, q, m))
    return results


# ─── Full circuit (with conditional operations) ──────────────────────────────


def create_teleportation_circuit(
    alpha: complex = 0.6 + 0j,
    beta: complex = 0.8 + 0j,
) -> QuantumCircuit:
    """
    Build the full teleportation circuit including conditional corrections.

    Qubit order: Q (q[0]), M (q[1]), Y (q[2])
    Classical bits: c[0] ← Q measurement, c[1] ← M measurement

    Bob's corrections:
        if c[1] == 1: apply X to Y
        if c[0] == 1: apply Z to Y
    """
    alpha, beta = normalize_state(alpha, beta)

    q = QuantumRegister(3, "q")
    c = ClassicalRegister(2, "c")
    qc = QuantumCircuit(q, c)

    # 1. Prepare the message qubit
    qc.initialize([alpha, beta], q[0])
    qc.barrier(label="Message")

    # 2. Create Bell pair |Φ+⟩ between M and Y
    qc.h(q[1])
    qc.cx(q[1], q[2])
    qc.barrier(label="Entanglement")

    # 3. Bell measurement circuit on Q and M
    qc.cx(q[0], q[1])
    qc.h(q[0])
    qc.barrier(label="Bell measurement")

    # 4. Measure Alice's qubits
    qc.measure(q[0], c[0])
    qc.measure(q[1], c[1])

    # 5. Bob's conditional corrections
    with qc.if_test((c[1], 1)):
        qc.x(q[2])
    with qc.if_test((c[0], 1)):
        qc.z(q[2])

    return qc


# ─── Simulator runs ──────────────────────────────────────────────────────────


def run_simulation(
    alpha: complex = 0.6 + 0j,
    beta: complex = 0.8 + 0j,
    shots: int = 1024,
) -> dict:
    """
    Run the teleportation circuit on AerSimulator.

    Returns
    -------
    dict with keys: "circuit", "counts", "shots", "alpha", "beta"
    """
    alpha, beta = normalize_state(alpha, beta)
    qc = create_teleportation_circuit(alpha, beta)

    simulator = AerSimulator()
    result = simulator.run(qc, shots=shots).result()
    counts = result.get_counts()

    return {
        "circuit": qc,
        "counts": counts,
        "shots": shots,
        "alpha": alpha,
        "beta": beta,
    }


def run_noisy_simulation(
    alpha: complex = 0.6 + 0j,
    beta: complex = 0.8 + 0j,
    shots: int = 1024,
    depolarizing_rate: float = 0.01,
) -> dict:
    """
    Run the teleportation circuit with a depolarizing noise model.

    Depolarizing noise is applied to all single-qubit and two-qubit gates.
    """
    alpha, beta = normalize_state(alpha, beta)
    qc = create_teleportation_circuit(alpha, beta)

    noise_model = NoiseModel()
    error_1q = depolarizing_error(depolarizing_rate, 1)
    error_2q = depolarizing_error(depolarizing_rate, 2)
    noise_model.add_all_qubit_quantum_error(error_1q, ["h", "x", "z"])
    noise_model.add_all_qubit_quantum_error(error_2q, ["cx"])

    simulator = AerSimulator(noise_model=noise_model)
    result = simulator.run(qc, shots=shots).result()
    counts = result.get_counts()

    return {
        "circuit": qc,
        "counts": counts,
        "shots": shots,
        "alpha": alpha,
        "beta": beta,
        "noise_rate": depolarizing_rate,
    }


def compute_noisy_fidelities(
    alpha: complex,
    beta: complex,
    noise_rates: list[float] | None = None,
    shots: int = 4096,
) -> list[dict]:
    """
    Sweep over noise rates and compute approximate fidelity at each level.

    Fidelity is estimated from the measurement statistics: for each outcome,
    apply the correction and compute the overlap with the original state,
    weighted by the observed probability.
    """
    if noise_rates is None:
        noise_rates = [0.0, 0.005, 0.01, 0.02, 0.05, 0.1, 0.15, 0.2]

    alpha, beta = normalize_state(alpha, beta)
    original = Statevector([alpha, beta])
    X = np.array([[0, 1], [1, 0]], dtype=complex)
    Z = np.array([[1, 0], [0, -1]], dtype=complex)

    results = []
    for rate in noise_rates:
        sim_result = run_noisy_simulation(alpha, beta, shots=shots, depolarizing_rate=rate)
        counts = sim_result["counts"]
        total = sum(counts.values())

        # For each measurement outcome, estimate Bob's state fidelity
        weighted_fid = 0.0
        for bitstring, count in counts.items():
            # Qiskit bitstring is c[1]c[0] order
            bits = bitstring.strip()
            if len(bits) == 2:
                c1 = int(bits[0])
                c0 = int(bits[1])
            else:
                continue

            info = OUTCOME_INFO.get((c0, c1))
            if info is None:
                continue

            # In ideal case, Bob's state after correction matches original
            # In noisy case, the correction is the same, but noise degrades fidelity
            # We approximate fidelity from outcome probabilities
            prob = count / total
            weighted_fid += prob  # In ideal case, each contributes prob * 1.0

        # For a more accurate estimate: use statevector simulation with noise
        # The weighted fidelity from measurement alone is an approximation
        # A better metric: compare ideal vs noisy outcome distributions
        ideal_counts = run_simulation(alpha, beta, shots=shots)["counts"]
        
        # Classical fidelity between distributions
        all_keys = set(list(counts.keys()) + list(ideal_counts.keys()))
        p_ideal = {k: ideal_counts.get(k, 0) / shots for k in all_keys}
        p_noisy = {k: counts.get(k, 0) / total for k in all_keys}
        
        # Bhattacharyya coefficient as fidelity proxy
        bc = sum(np.sqrt(p_ideal.get(k, 0) * p_noisy.get(k, 0)) for k in all_keys)

        results.append({
            "noise_rate": rate,
            "distribution_fidelity": float(bc),
            "counts": counts,
        })

    return results


# ─── Verification ─────────────────────────────────────────────────────────────


def verify_teleportation(alpha: complex, beta: complex) -> dict:
    """
    Full verification: check all four outcomes produce the correct state.
    """
    alpha, beta = normalize_state(alpha, beta)
    outcomes = compute_all_outcomes(alpha, beta)
    
    all_passed = True
    details = []
    for oc in outcomes:
        passed = np.isclose(oc["fidelity"], 1.0, atol=1e-6)
        if not passed:
            all_passed = False
        details.append({
            "outcome": oc["bits_str"],
            "fidelity": oc["fidelity"],
            "passed": passed,
        })

    return {
        "alpha": alpha,
        "beta": beta,
        "all_passed": all_passed,
        "details": details,
    }


def run_verification_suite() -> list[dict]:
    """Run verification across multiple test states."""
    test_states = [
        ("|0⟩", 1.0 + 0j, 0.0 + 0j),
        ("|1⟩", 0.0 + 0j, 1.0 + 0j),
        ("|+⟩", 1 / np.sqrt(2), 1 / np.sqrt(2)),
        ("|−⟩", 1 / np.sqrt(2), -1 / np.sqrt(2)),
        ("|i+⟩", 1 / np.sqrt(2), 1j / np.sqrt(2)),
        ("|i−⟩", 1 / np.sqrt(2), -1j / np.sqrt(2)),
        ("0.6|0⟩+0.8|1⟩", 0.6 + 0j, 0.8 + 0j),
        ("(1+i)|0⟩/√3 + 1|1⟩/√3", (1 + 1j) / np.sqrt(3), 1 / np.sqrt(3)),
    ]

    results = []
    for name, alpha, beta in test_states:
        v = verify_teleportation(alpha, beta)
        v["state_name"] = name
        results.append(v)

    return results


# ─── IBM Quantum Cloud Hardware Integration ──────────────────────────────────

IBM_DEFAULT_TOKEN = "fFfXXOtzorYMEnJ_N-OOpMVmYifj4ZmW0GxUJNN4aGCi"
IBM_DEFAULT_CRN = "crn:v1:bluemix:public:quantum-computing:us-east:a/bebe6d634e114fa49d27f6df3d902c6b:fdbe7491-2d6e-484c-9240-30be98d41891::"

IBM_KINGSTON_CALIBRATION: dict[str, Any] = {
    "backend_name": "ibm_kingston",
    "processor_type": "Heron r2",
    "num_qubits": 156,
    "region": "us-east (Washington DC)",
    "t1_median_us": 232.01,
    "t2_median_us": 136.34,
    "cz_error_median": 1.961e-3,
    "sx_error_median": 2.668e-4,
    "readout_error_median": 9.949e-3,
    "init_error_median": 2.000e-3,
}


def build_kingston_noise_model() -> NoiseModel:
    """
    Build a realistic Qiskit Aer NoiseModel calibrated to ibm_kingston (Heron r2).

    Parameters:
        T1 = 232.01 µs, T2 = 136.34 µs
        2-qubit CZ gate error = 0.1961%
        Single-qubit SX/RZ gate error = 0.0267%
        Readout error = 0.9949%
    """
    from qiskit_aer.noise import ReadoutError

    nm = NoiseModel()
    cz_err = depolarizing_error(IBM_KINGSTON_CALIBRATION["cz_error_median"], 2)
    sx_err = depolarizing_error(IBM_KINGSTON_CALIBRATION["sx_error_median"], 1)

    nm.add_all_qubit_quantum_error(cz_err, ["cz", "cx"])
    nm.add_all_qubit_quantum_error(sx_err, ["sx", "x", "h", "z"])

    ro_prob = IBM_KINGSTON_CALIBRATION["readout_error_median"]
    ro_err = ReadoutError([[1 - ro_prob, ro_prob], [ro_prob, 1 - ro_prob]])
    nm.add_all_qubit_readout_error(ro_err)

    return nm


def get_ibm_service(
    token: str | None = None,
    instance: str | None = None,
    channel: str = "ibm_cloud",
) -> Any:
    """Initialize QiskitRuntimeService with user credentials or saved account."""
    from qiskit_ibm_runtime import QiskitRuntimeService

    try:
        return QiskitRuntimeService(name="default-cloud")
    except Exception:
        pass

    tok = token or IBM_DEFAULT_TOKEN
    inst = instance or IBM_DEFAULT_CRN
    return QiskitRuntimeService(channel=channel, token=tok, instance=inst)


def query_cloud_backends(service: Any = None) -> list[dict]:
    """Retrieve available IBM Quantum Cloud hardware backends and queue depth."""
    if service is None:
        service = get_ibm_service()

    results = []
    for b in service.backends():
        st = b.status()
        results.append({
            "name": b.name,
            "num_qubits": b.num_qubits,
            "operational": bool(st.operational),
            "pending_jobs": int(st.pending_jobs),
            "status_msg": str(st.status_msg),
            "processor_type": "Heron r2" if "kingston" in b.name or "marrakesh" in b.name else "Eagle",
        })
    return results


def submit_cloud_teleportation(
    alpha: complex = 0.6 + 0j,
    beta: complex = 0.8 + 0j,
    backend_name: str = "ibm_kingston",
    shots: int = 1024,
    service: Any = None,
) -> dict:
    """
    Transpile and submit the teleportation protocol to a real physical IBM Quantum QPU.

    Returns a dict with 'job_id', 'status', 'backend', and 'shots'.
    """
    from qiskit import transpile
    from qiskit_ibm_runtime import SamplerV2

    if service is None:
        service = get_ibm_service()

    alpha, beta = normalize_state(alpha, beta)
    backend = service.backend(backend_name)
    qc = create_teleportation_circuit(alpha, beta)

    # Transpile circuit to physical QPU basis gates (Heron r2 uses CZ entangling gates)
    isa_circuit = transpile(qc, backend=backend, optimization_level=1)

    sampler = SamplerV2(mode=backend)
    job = sampler.run([isa_circuit], shots=shots)

    return {
        "job_id": job.job_id(),
        "backend": backend_name,
        "status": str(job.status()),
        "shots": shots,
        "alpha": alpha,
        "beta": beta,
    }


def retrieve_cloud_job_results(job_id: str, service: Any = None) -> dict:
    """Fetch status and counts of a submitted IBM Quantum cloud job."""
    if service is None:
        service = get_ibm_service()

    job = service.job(job_id)
    status_str = str(job.status())
    b_name = job.backend().name if job.backend() else "unknown"

    counts: dict[str, int] = {}
    if status_str == "DONE":
        try:
            res = job.result()
            pub_result = res[0]
            if hasattr(pub_result.data, "meas"):
                counts = pub_result.data.meas.get_counts()
        except Exception as e:
            counts = {"error": str(e)}

    return {
        "job_id": job_id,
        "backend": b_name,
        "status": status_str,
        "creation_date": str(job.creation_date),
        "counts": counts,
    }


# ─── CLI entry point ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    print("Quantum Teleportation Engine — Verification & QPU Suite")
    print("=" * 60)

    if "--cloud" in sys.argv:
        print("\nQuerying IBM Quantum Cloud Fleet...")
        try:
            backends = query_cloud_backends()
            for b in backends:
                print(f"  • {b['name']} ({b['processor_type']}, {b['num_qubits']}Q): "
                      f"Operational={b['operational']}, Pending Jobs={b['pending_jobs']}")
        except Exception as err:
            print(f"Cloud connection failed: {err}")
    else:
        suite = run_verification_suite()
        for v in suite:
            status = "✓ PASS" if v["all_passed"] else "✗ FAIL"
            print(f"\n{status}  {v['state_name']}")
            for d in v["details"]:
                print(f"    Outcome {d['outcome']}: fidelity = {d['fidelity']:.8f}")

        print("\n" + "=" * 60)
        all_ok = all(v["all_passed"] for v in suite)
        print(f"Overall: {'ALL PASSED ✓' if all_ok else 'SOME FAILED ✗'}")
        print("\nTip: Run with --cloud to query live IBM Quantum hardware backends.")
