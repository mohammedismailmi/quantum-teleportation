"""
================================================================================
Quantum Teleportation Working using IBM Qiskit 1.x / Aer)
================================================================================
Reference:
    Bennett, Brassard, Crépeau, Jozsa, Peres, and Wootters,
    "Teleporting an Unknown Quantum State via Dual Classical and
    Einstein-Podolsky-Rosen Channels", Phys. Rev. Lett. 70, 1895 (1993).

Overview:
    Quantum teleportation transfers an arbitrary, unknown qubit state:
        |ψ⟩ = α|0⟩ + β|1⟩    where α, β ∈ ℂ and |α|² + |β|² = 1
    from Alice (the sender) to Bob (the receiver) without physically
    transporting the qubit carrying the state.

Fundamental Physical Principles:
    1. No-Cloning Theorem (Wootters & Zurek, 1982):
       An unknown quantum state cannot be replicated. Alice's projective
       Bell-basis measurement irrevocably collapses and destroys her original
       qubit's state, preventing cloning and preserving quantum uniqueness.
    2. Quantum Entanglement (EPR Channel):
       Alice and Bob pre-share an entangled Bell state |Φ+⟩ = (|00⟩ + |11⟩)/√2.
       This provides the non-local quantum correlation channel required for
       disentangling and reconstructing the state.
    3. Classical Communication & Relativistic Causality (No-Signaling):
       Alice must transmit 2 classical bits (c0, c1) to Bob over a conventional
       channel (light speed v ≤ c). Without these bits, Bob's reduced density
       matrix is maximally mixed (ρ = I/2), containing exactly zero information
       about |ψ⟩. Thus, instantaneous faster-than-light signaling is impossible.
    4. Unitary Feed-Forward Reconstruction:
       Upon receiving (c0, c1), Bob applies a deterministic Pauli correction:
           U(c0, c1) = Z^(c0) · X^(c1)
       which maps his qubit state into the exact original state |ψ⟩ with 100%
       fidelity in the absence of noise.

Qubit & Register Convention:
    • q[0] (Q) : Alice's unknown message qubit (|ψ⟩ = α|0⟩ + β|1⟩)
    • q[1] (M) : Alice's half of the pre-shared entangled Bell pair
    • q[2] (Y) : Bob's half of the pre-shared entangled Bell pair
    • c[0]     : Classical bit storing measurement of Alice's message qubit q[0]
                 (determines whether a phase-flip Pauli-Z correction is needed)
    • c[1]     : Classical bit storing measurement of Alice's Bell qubit q[1]
                 (determines whether a bit-flip Pauli-X correction is needed)
================================================================================
"""

from __future__ import annotations

from typing import Any
import numpy as np

# IBM Qiskit core circuit and quantum information modules
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit.quantum_info import (
    DensityMatrix,
    Statevector,
    partial_trace,
    state_fidelity,
)
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, depolarizing_error


# ─── Standard Basis & Bell State Presets ──────────────────────────────────────

# Canonical single-qubit basis states used for benchmarking and demonstration:
# |0⟩, |1⟩ : Computational Z-basis eigenstates
# |+⟩, |−⟩ : Hadamard X-basis eigenstates (|0⟩ ± |1⟩)/√2
# |i+⟩, |i−⟩: Circular Y-basis eigenstates (|0⟩ ± i|1⟩)/√2
PRESET_STATES: dict[str, tuple[complex, complex]] = {
    "|0⟩": (1.0 + 0j, 0.0 + 0j),
    "|1⟩": (0.0 + 0j, 1.0 + 0j),
    "|+⟩": (1 / np.sqrt(2) + 0j, 1 / np.sqrt(2) + 0j),
    "|−⟩": (1 / np.sqrt(2) + 0j, -1 / np.sqrt(2) + 0j),
    "|i+⟩": (1 / np.sqrt(2) + 0j, 1j / np.sqrt(2)),
    "|i−⟩": (1 / np.sqrt(2) + 0j, -1j / np.sqrt(2)),
}

# The four maximally entangled 2-qubit Bell states (EPR pairs):
# |Φ+⟩ = (|00⟩ + |11⟩)/√2
# |Φ−⟩ = (|00⟩ - |11⟩)/√2
# |Ψ+⟩ = (|01⟩ + |10⟩)/√2
# |Ψ−⟩ = (|01⟩ - |10⟩)/√2
BELL_STATES: dict[str, np.ndarray] = {
    "|Φ+⟩": np.array([1, 0, 0, 1]) / np.sqrt(2),
    "|Φ−⟩": np.array([1, 0, 0, -1]) / np.sqrt(2),
    "|Ψ+⟩": np.array([0, 1, 1, 0]) / np.sqrt(2),
    "|Ψ−⟩": np.array([0, 1, -1, 0]) / np.sqrt(2),
}

# Step-by-step sequential labels tracking the progression of the teleportation protocol
STAGE_LABELS = [
    "Initial State",
    "Hadamard on M",
    "CNOT (M → Y): Bell Pair Ready",
    "CNOT (Q → M): Alice Entangles",
    "Hadamard on Q: Bell Basis",
    "Alice Measures Q and M",
    "Classical Communication",
    "Bob's Correction",
    "Teleportation Complete",
]

# Physical descriptions explaining the transformation occurring at each stage
STAGE_DESCRIPTIONS = [
    "Message qubit Q initialized to |ψ⟩ = α|0⟩ + β|1⟩. Qubits M and Y are in ground state |0⟩.",
    "Hadamard on M creates equal superposition H|0⟩ = (|0⟩ + |1⟩)/√2.",
    "CNOT from M to Y generates the maximally entangled Bell pair |Φ+⟩ = (|00⟩ + |11⟩)/√2.",
    "Alice performs CNOT from Q to M, correlating her message qubit with the Bell pair.",
    "Alice applies Hadamard to Q, rotating her joint system into the Bell measurement basis.",
    "Alice measures qubits Q and M, collapsing the system into one of 4 outcomes (c0, c1).",
    "Alice transmits 2 classical bits (c0, c1) to Bob over a classical channel (v ≤ c).",
    "Bob receives (c0, c1) and applies conditional Pauli corrections: X if c1=1, Z if c0=1.",
    "Teleportation complete! Bob's qubit Y is an exact replica of |ψ⟩ with fidelity = 1.0.",
]

# Four-branch Pauli decoding dictionary mapping classical measurement bit pairs (q_meas, m_meas)
# to their corresponding Bell state, required unitary gate operations, and descriptive labels:
#   (c0=0, c1=0) -> |Φ+⟩ -> Bob holds (α|0⟩ + β|1⟩)  -> Identity I (no gates)
#   (c0=0, c1=1) -> |Ψ+⟩ -> Bob holds (β|0⟩ + α|1⟩)  -> Pauli X (bit flip)
#   (c0=1, c1=0) -> |Φ-⟩ -> Bob holds (α|0⟩ - β|1⟩)  -> Pauli Z (phase flip)
#   (c0=1, c1=1) -> |Ψ-⟩ -> Bob holds (-β|0⟩ + α|1⟩) -> Pauli X then Pauli Z
OUTCOME_INFO = {
    (0, 0): {"bell_label": "|Φ⁺⟩", "correction": "I (no correction)", "gates": []},
    (0, 1): {"bell_label": "|Ψ⁺⟩", "correction": "X gate", "gates": ["X"]},
    (1, 0): {"bell_label": "|Φ⁻⟩", "correction": "Z gate", "gates": ["Z"]},
    (1, 1): {"bell_label": "|Ψ⁻⟩", "correction": "XZ (X then Z)", "gates": ["X", "Z"]},
}


# ─── 1. Core Quantum Circuit Builder ──────────────────────────────────────────

def create_teleportation_circuit(
    alpha: complex | float = 0.6,
    beta: complex | float = 0.8,
) -> QuantumCircuit:
    """
    Construct the full 3-qubit, 2-classical-bit quantum teleportation circuit.

    Protocol Architecture & Mathematical Derivation:
        Let Alice's unknown input state on qubit q[0] (Q) be:
            |ψ⟩_Q = α|0⟩ + β|1⟩
        Alice and Bob share an entangled Bell pair on qubits q[1] (M) and q[2] (Y):
            |Φ+⟩_MY = (|00⟩ + |11⟩)/√2

        The combined 3-qubit state |Ψ₀⟩ = |ψ⟩_Q ⊗ |Φ+⟩_MY expands to:
            |Ψ₀⟩ = (α|0⟩ + β|1⟩) ⊗ (|00⟩ + |11⟩)/√2
                 = 1/√2 [ α|000⟩ + α|011⟩ + β|100⟩ + β|111⟩ ]

        Alice applies CNOT(Q → M), flipping qubit M if Q is |1⟩:
            |Ψ₁⟩ = 1/√2 [ α|000⟩ + α|011⟩ + β|110⟩ + β|101⟩ ]

        Alice applies Hadamard H(Q), rotating |0⟩ → (|0⟩+|1⟩)/√2 and |1⟩ → (|0⟩-|1⟩)/√2:
            |Ψ₂⟩ = 1/2 [ α(|0⟩+|1⟩)|00⟩ + α(|0⟩+|1⟩)|11⟩ + β(|0⟩-|1⟩)|10⟩ + β(|0⟩-|1⟩)|01⟩ ]
            Regrouping terms by Alice's measured basis states |q₀ q₁⟩:
                 = 1/2 [ |00⟩_QM ⊗ ( α|0⟩ + β|1⟩)_Y    (c0=0, c1=0 → Bob has |ψ⟩)
                       + |01⟩_QM ⊗ ( α|1⟩ + β|0⟩)_Y    (c0=0, c1=1 → Bob has X|ψ⟩)
                       + |10⟩_QM ⊗ ( α|0⟩ - β|1⟩)_Y    (c0=1, c1=0 → Bob has Z|ψ⟩)
                       + |11⟩_QM ⊗ (-β|0⟩ + α|1⟩)_Y ]  (c0=1, c1=1 → Bob has ZX|ψ⟩)

        When Alice measures q[0] into c[0] and q[1] into c[1], the state collapses
        into one of the 4 branches with equal probability P = 1/4 = 25%.
        Bob then applies conditional feed-forward operations Z^(c0) · X^(c1)
        to recover |ψ⟩ exactly.

    Parameters:
        alpha (complex | float): Complex probability amplitude of ground state |0⟩.
        beta  (complex | float): Complex probability amplitude of excited state |1⟩.

    Returns:
        QuantumCircuit: Complete 3-qubit, 2-classical-bit teleportation circuit.
    """
    # -------------------------------------------------------------------------
    # Step 0: Validate and Normalize State Amplitudes
    # Enforces the fundamental Born probability conservation rule: |α|² + |β|² = 1.
    # -------------------------------------------------------------------------
    alpha_c = complex(alpha)
    beta_c = complex(beta)
    norm = np.sqrt(abs(alpha_c) ** 2 + abs(beta_c) ** 2)

    if np.isclose(norm, 0.0):
        raise ValueError("Both state amplitudes cannot be zero.")

    # Rescale amplitudes so that the state vector has exact unit Euclidean norm
    alpha_norm = alpha_c / norm
    beta_norm = beta_c / norm

    # -------------------------------------------------------------------------
    # Step 1: Allocate Quantum and Classical Registers
    # 3 quantum qubits:
    #   q[0]: Alice's message qubit (Q)
    #   q[1]: Alice's half of the Bell pair (M)
    #   q[2]: Bob's half of the Bell pair (Y)
    # 2 classical bits:
    #   c[0]: Alice's measurement result for message qubit q[0] (phase-flip bit)
    #   c[1]: Alice's measurement result for Bell qubit q[1] (bit-flip bit)
    # -------------------------------------------------------------------------
    q = QuantumRegister(3, name="q")
    c = ClassicalRegister(2, name="c")
    qc = QuantumCircuit(q, c, name="Quantum_Teleportation")

    # -------------------------------------------------------------------------
    # Step 2: Message State Preparation (Alice's Qubit Q)
    # Sets q[0] to the state |ψ⟩_Q = α|0⟩ + β|1⟩ via Qiskit's state initialization
    # -------------------------------------------------------------------------
    qc.initialize([alpha_norm, beta_norm], q[0])
    qc.barrier(label="Message")

    # -------------------------------------------------------------------------
    # Step 3: Shared EPR Bell Pair Creation (Alice's M & Bob's Y)
    # - Hadamard on q[1] puts it into equal superposition: (|0⟩ + |1⟩)/√2
    # - CNOT with control q[1] and target q[2] creates the entangled state:
    #       |Φ+⟩_MY = (|00⟩ + |11⟩)/√2
    # Spatial Separation: Alice retains qubit q[1]; qubit q[2] is sent to Bob.
    # -------------------------------------------------------------------------
    qc.h(q[1])
    qc.cx(q[1], q[2])
    qc.barrier(label="Entanglement")

    # -------------------------------------------------------------------------
    # Step 4: Alice's Entangling Operations (Bell-Basis Rotation)
    # - CNOT (q[0] -> q[1]): Correlates the message state with Alice's Bell qubit.
    # - Hadamard on q[0]: Rotates Alice's two qubits into the Bell measurement basis.
    # -------------------------------------------------------------------------
    qc.cx(q[0], q[1])
    qc.h(q[0])
    qc.barrier(label="Bell measurement")

    # -------------------------------------------------------------------------
    # Step 5: Alice's Projective Measurements
    # Alice measures her two qubits in the standard computational basis:
    #   c[0] ← measurement of q[0] (tells Bob if a sign flip occurred)
    #   c[1] ← measurement of q[1] (tells Bob if a bit flip occurred)
    #
    # Physical consequence: This measurement collapses Alice's original state,
    # destroying the qubit |ψ⟩ at Alice's station (respecting No-Cloning).
    # -------------------------------------------------------------------------
    qc.measure(q[0], c[0])
    qc.measure(q[1], c[1])

    # -------------------------------------------------------------------------
    # Step 6: Bob's Feed-Forward Conditional Unitary Corrections
    # Alice sends classical bits (c0, c1) to Bob over a classical channel (v ≤ c).
    # Bob applies conditional Pauli corrections to his qubit q[2]:
    #   • If c[1] == 1: Apply Pauli-X to undo the bit-flip (swap amplitudes)
    #   • If c[0] == 1: Apply Pauli-Z to undo the phase-flip (correct relative sign)
    #
    # In Qiskit, this dynamic feed-forward logic is expressed via `qc.if_test`:
    # -------------------------------------------------------------------------
    with qc.if_test((c[1], 1)):
        qc.x(q[2])

    with qc.if_test((c[0], 1)):
        qc.z(q[2])

    return qc


# ─── 2. Local Quantum Circuit Simulation ──────────────────────────────────────

def run_teleportation(
    alpha: complex | float = 0.6,
    beta: complex | float = 0.8,
    shots: int = 2048,
) -> tuple[QuantumCircuit, dict[str, int]]:
    """
    Execute the quantum teleportation circuit on a local Aer simulator.

    Runs repeated shot-based statistical sampling of Alice's measurement outcomes
    to verify that all four branches occur with equal ~25% probability.

    Parameters:
        alpha (complex | float): Message ground amplitude α.
        beta  (complex | float): Message excited amplitude β.
        shots (int)            : Number of statistical measurement samples.

    Returns:
        tuple[QuantumCircuit, dict[str, int]]:
            - circuit: The executed Qiskit QuantumCircuit.
            - counts: Dictionary mapping measured bitstrings (c1c0) to observed counts.
    """
    # 1. Build the full circuit including dynamic feed-forward Pauli corrections
    qc = create_teleportation_circuit(alpha, beta)

    # 2. Instantiate Qiskit Aer's high-performance C++ simulator
    simulator = AerSimulator()

    # 3. Execute the circuit across the specified shot count
    result = simulator.run(qc, shots=shots).result()

    # 4. Extract statistical outcome counts (bitstrings '00', '01', '10', '11')
    counts = result.get_counts()

    return qc, counts


# ─── 3. Mathematical State Helpers & Analysis ─────────────────────────────────

def normalize_state(alpha: complex, beta: complex) -> tuple[complex, complex]:
    """
    Normalize arbitrary complex amplitudes (α, β) to satisfy the Born rule.

    Calculates norm = √(|α|² + |β|²) and returns (α/norm, β/norm).
    Raises ValueError if both amplitudes are zero (an unphysical null state).
    """
    # Compute the Euclidean vector norm of the state
    norm = np.sqrt(abs(alpha) ** 2 + abs(beta) ** 2)
    if np.isclose(norm, 0.0):
        raise ValueError("Both amplitudes cannot be zero.")
    return (alpha / norm, beta / norm)


def bloch_angles_to_amplitudes(theta: float, phi: float) -> tuple[complex, complex]:
    """
    Convert spherical Bloch sphere coordinates (θ, φ) to statevector amplitudes (α, β).

    The standard single-qubit Bloch sphere parameterization is:
        |ψ(θ, φ)⟩ = cos(θ/2)|0⟩ + e^(iφ) sin(θ/2)|1⟩
    where:
        θ ∈ [0, π]   is the polar angle (colatitude)
        φ ∈ [0, 2π)  is the azimuthal angle (longitude / phase)
    """
    alpha = np.cos(theta / 2) + 0j
    beta = np.exp(1j * phi) * np.sin(theta / 2)
    return (alpha, beta)


def amplitudes_to_bloch(alpha: complex, beta: complex) -> tuple[float, float, float]:
    """
    Calculate Cartesian Bloch sphere coordinates (x, y, z) for pure state α|0⟩ + β|1⟩.

    The Bloch vector components correspond to Pauli expectation values:
        x = ⟨σ_x⟩ = 2 Re(α* · β)
        y = ⟨σ_y⟩ = 2 Im(α* · β)
        z = ⟨σ_z⟩ = |α|² - |β|²
    For any pure quantum state, the Bloch vector lies on the surface: x² + y² + z² = 1.
    """
    alpha, beta = normalize_state(alpha, beta)
    x = 2 * np.real(np.conj(alpha) * beta)
    y = 2 * np.imag(np.conj(alpha) * beta)
    z = float(np.abs(alpha) ** 2 - np.abs(beta) ** 2)
    return (float(x), float(y), float(z))


def dm_to_bloch(dm: np.ndarray) -> tuple[float, float, float]:
    """
    Extract Cartesian Bloch vector coordinates (x, y, z) from a 2×2 reduced density matrix ρ.

    Any single-qubit density matrix can be decomposed in the Pauli basis:
        ρ = 1/2 [ I + r_x σ_x + r_y σ_y + r_z σ_z ]
    where the coordinates are given by:
        r_x = 2 Re(ρ₀₁)
        r_y = 2 Im(ρ₁₀)
        r_z = ρ₀₀ - ρ₁₁
    For mixed states (such as an entangled subsystem), |r| < 1 (inside the sphere).
    For maximally mixed states (e.g. half of a Bell pair), r = (0, 0, 0) (sphere center).
    """
    rho = np.asarray(dm, dtype=complex)
    x = float(2 * np.real(rho[0, 1]))
    y = float(2 * np.imag(rho[1, 0]))
    z = float(np.real(rho[0, 0] - rho[1, 1]))
    return (x, y, z)


def is_pure(dm: np.ndarray, tol: float = 1e-6) -> bool:
    """
    Verify quantum state purity using the trace of the squared density matrix:
        Purity γ = Tr(ρ²)
    - Pure states satisfy γ = 1 (idempotent: ρ² = ρ).
    - Mixed states satisfy γ < 1 (for a single qubit, maximally mixed γ = 0.5).
    """
    rho = np.asarray(dm, dtype=complex)
    # Tr(ρ²) is mathematically strictly real and bounded in [1/d, 1]
    return bool(np.real(np.trace(rho @ rho)) > 1 - tol)


def compute_stage_states(alpha: complex, beta: complex) -> list[dict]:
    """
    Compute step-by-step 3-qubit Statevectors and reduced density matrices across stages 0–4.

    Stages tracked:
        Stage 0: |ψ⟩_Q ⊗ |00⟩_MY (Alice's message initialized, Bell pair ground)
        Stage 1: |ψ⟩_Q ⊗ |+0⟩_MY (Hadamard applied to Alice's Bell qubit M)
        Stage 2: |ψ⟩_Q ⊗ |Φ+⟩_MY (CNOT M→Y: EPR pair formed, M and Y become mixed)
        Stage 3: CNOT(Q → M) applied (Alice entangles message with her Bell qubit)
        Stage 4: H(Q) applied (Alice rotates her joint qubits into the Bell basis)

    For each stage, this function computes:
        - Full 3-qubit statevector (dimension 8)
        - Partial trace over complementary qubits to get each individual qubit's
          reduced density matrix ρ_Q, ρ_M, ρ_Y
        - Corresponding Bloch sphere coordinates (x, y, z)
        - Purity boolean (pure vs entangled/mixed)

    Returns:
        list[dict]: List of stage dictionaries containing statevectors and Bloch metrics.
    """
    alpha, beta = normalize_state(alpha, beta)
    results: list[dict] = []

    def _snapshot(stage_idx: int, sv: Statevector) -> dict:
        # Convert statevector into full 8×8 density matrix
        dm_full = DensityMatrix(sv)
        reduced: dict[int, np.ndarray] = {}
        bloch: dict[int, tuple[float, float, float]] = {}
        purity: dict[int, bool] = {}

        # Compute partial trace for each individual qubit: ρ_i = Tr_{j ≠ i}(ρ)
        for q_idx in range(3):
            others = [j for j in range(3) if j != q_idx]
            rdm = partial_trace(dm_full, others).data
            reduced[q_idx] = rdm
            bloch[q_idx] = dm_to_bloch(rdm)
            purity[q_idx] = is_pure(rdm)

        return {
            "stage": stage_idx,
            "label": STAGE_LABELS[stage_idx],
            "description": STAGE_DESCRIPTIONS[stage_idx],
            "statevector": sv.data,
            "reduced_dm": reduced,
            "bloch": bloch,
            "is_pure": purity,
        }

    # Stage 0: Alice initializes her message qubit Q
    qc = QuantumCircuit(3)
    qc.initialize([alpha, beta], 0)
    results.append(_snapshot(0, Statevector.from_instruction(qc)))

    # Stage 1: Hadamard on M creates equal superposition (|0⟩+|1⟩)/√2
    qc.h(1)
    results.append(_snapshot(1, Statevector.from_instruction(qc)))

    # Stage 2: CNOT(M → Y) entangles M and Y into Bell state |Φ+⟩
    qc.cx(1, 2)
    results.append(_snapshot(2, Statevector.from_instruction(qc)))

    # Stage 3: CNOT(Q → M) correlates Alice's message with her Bell qubit
    qc.cx(0, 1)
    results.append(_snapshot(3, Statevector.from_instruction(qc)))

    # Stage 4: Hadamard on Q rotates Alice's joint qubits into the Bell basis
    qc.h(0)
    results.append(_snapshot(4, Statevector.from_instruction(qc)))

    return results


def compute_conditional_state(alpha: complex, beta: complex, q_meas: int, m_meas: int) -> dict:
    """
    Compute Bob's conditional quantum state and verify reconstruction fidelity
    for a specific measurement outcome branch (q_meas, m_meas).

    Mathematical Process:
        1. Evolve the 3-qubit state through the Bell-basis rotation.
        2. Project onto Alice's measurement subspace |q_meas, m_meas⟩_QM.
        3. Extract Bob's post-measurement conditional statevector on qubit Y.
        4. Apply Bob's corresponding feed-forward Pauli correction:
           - Outcome (0, 0): Identity I
           - Outcome (0, 1): Pauli X (flips amplitudes back)
           - Outcome (1, 0): Pauli Z (flips relative sign back)
           - Outcome (1, 1): Pauli X followed by Pauli Z
        5. Compute the quantum state fidelity F = |⟨ψ_original | ψ_bob⟩|² to prove
           exact reconstruction (F = 1.0).

    Parameters:
        alpha (complex): Ground state amplitude α.
        beta  (complex): Excited state amplitude β.
        q_meas (int)   : Alice's measurement result for message qubit q[0] (0 or 1).
        m_meas (int)   : Alice's measurement result for Bell qubit q[1] (0 or 1).

    Returns:
        dict: Breakdown containing pre-correction state, post-correction state,
              Pauli gates applied, branch probability, and state fidelity.
    """
    alpha, beta = normalize_state(alpha, beta)
    info = OUTCOME_INFO[(q_meas, m_meas)]

    # 1. Build circuit up to Alice's measurement
    qc = QuantumCircuit(3)
    qc.initialize([alpha, beta], 0)
    qc.h(1)
    qc.cx(1, 2)
    qc.cx(0, 1)
    qc.h(0)
    sv = Statevector.from_instruction(qc)

    # 2. Reshape into 3D tensor: dimensions correspond to (q2=Y, q1=M, q0=Q) in Qiskit ordering
    full_vec = sv.data.reshape(2, 2, 2)
    conditional_vec = full_vec[:, m_meas, q_meas]

    # 3. Normalize Bob's conditional statevector (norm² gives branch probability = 0.25)
    norm = np.linalg.norm(conditional_vec)
    if norm < 1e-12:
        raise ValueError("Zero-probability outcome.")
    bob_before = conditional_vec / norm

    # 4. Define Pauli correction operators
    X = np.array([[0, 1], [1, 0]], dtype=complex)
    Z = np.array([[1, 0], [0, -1]], dtype=complex)
    bob_after = bob_before.copy()

    # Apply conditional Pauli gates according to Alice's classical bits
    for gate in info["gates"]:
        if gate == "X":
            bob_after = X @ bob_after
        elif gate == "Z":
            bob_after = Z @ bob_after

    # 5. Calculate fidelity between Alice's input state and Bob's reconstructed state
    original = Statevector([alpha, beta])
    reconstructed = Statevector(bob_after)
    fidelity = float(state_fidelity(original, reconstructed))

    return {
        "q_meas": q_meas,
        "m_meas": m_meas,
        "bits_str": f"{q_meas}{m_meas}",
        "bell_label": info["bell_label"],
        "bell_name": info["bell_label"],
        "correction": info["correction"],
        "correction_label": info["correction"],
        "gates": info["gates"],
        "bob_before_correction": bob_before,
        "bob_after_correction": bob_after,
        "fidelity": fidelity,
        "probability": float(norm ** 2),
    }


def compute_all_outcomes(alpha: complex, beta: complex) -> list[dict]:
    """
    Calculate Bob's post-measurement and reconstructed states across all four
    possible measurement branches: (0,0), (0,1), (1,0), and (1,1).

    Demonstrates that regardless of which random outcome Alice observes, Bob's
    feed-forward correction deterministically recovers |ψ⟩ with unit fidelity.
    """
    results = []
    for (q, m) in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        results.append(compute_conditional_state(alpha, beta, q, m))
    return results


def run_simulation(alpha: complex = 0.6 + 0j, beta: complex = 0.8 + 0j, shots: int = 1024) -> dict:
    """
    Simulate the teleportation circuit on a noiseless local AerSimulator.

    Returns the assembled QuantumCircuit, observed measurement histogram counts,
    and simulation parameters.
    """
    alpha, beta = normalize_state(alpha, beta)
    qc = create_teleportation_circuit(alpha, beta)
    simulator = AerSimulator()
    result = simulator.run(qc, shots=shots).result()
    return {
        "circuit": qc,
        "counts": result.get_counts(),
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
    Simulate the teleportation circuit under a parameterized depolarizing noise model.

    Quantum Noise Physics:
        A depolarizing channel on d dimensions contracts the density matrix towards
        the maximally mixed state I/d:
            E(ρ) = (1 - p)ρ + p/d · I
        - Single-qubit errors (p = depolarizing_rate) applied to 1Q gates (H, X, Z)
        - Two-qubit errors applied to 2Q entangling gates (CX, CZ)
    This accurately models quantum decoherence and gate infidelity on real quantum processors.

    Parameters:
        alpha, beta        : Message state amplitudes.
        shots              : Number of measurement samples.
        depolarizing_rate  : Depolarizing error probability p per gate.

    Returns:
        dict: Noisy measurement histogram and noise metadata.
    """
    alpha, beta = normalize_state(alpha, beta)
    qc = create_teleportation_circuit(alpha, beta)

    # Construct quantum noise model
    noise_model = NoiseModel()
    error_1q = depolarizing_error(depolarizing_rate, 1)
    error_2q = depolarizing_error(depolarizing_rate, 2)
    noise_model.add_all_qubit_quantum_error(error_1q, ["h", "x", "z"])
    noise_model.add_all_qubit_quantum_error(error_2q, ["cx", "cz"])

    # Execute simulation with noise model attached
    simulator = AerSimulator(noise_model=noise_model)
    result = simulator.run(qc, shots=shots).result()
    return {
        "circuit": qc,
        "counts": result.get_counts(),
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
    Sweep across depolarizing noise rates and evaluate statistical distribution fidelity.

    Metric:
        Uses the classical Bhattacharyya coefficient (distribution fidelity) between
        the ideal noiseless probability distribution P(x) and noisy distribution Q(x):
            BC(P, Q) = ∑_{x} √(P(x) · Q(x))
        - In the noiseless limit (p = 0): BC = 1.0.
        - As noise increases (p → 0.2): Gate errors distort outcome statistics, causing
          the Bhattacharyya coefficient to decrease monotonically.

    Parameters:
        alpha, beta : Message state amplitudes.
        noise_rates : List of depolarizing error probabilities to test.
        shots       : Samples per noise rate.

    Returns:
        list[dict]: Array of noise rates and corresponding distribution fidelities.
    """
    if noise_rates is None:
        noise_rates = [0.0, 0.01, 0.02, 0.04, 0.08, 0.12, 0.16, 0.2]

    alpha, beta = normalize_state(alpha, beta)
    # Obtain ideal baseline counts
    ideal_counts = run_simulation(alpha, beta, shots=shots)["counts"]

    results = []
    for rate in noise_rates:
        noisy_res = run_noisy_simulation(alpha, beta, shots=shots, depolarizing_rate=rate)
        counts = noisy_res["counts"]
        total = sum(counts.values())

        # Normalize counts into discrete probability distributions
        all_keys = set(list(counts.keys()) + list(ideal_counts.keys()))
        p_ideal = {k: ideal_counts.get(k, 0) / shots for k in all_keys}
        p_noisy = {k: counts.get(k, 0) / total for k in all_keys}

        # Calculate Bhattacharyya overlap coefficient
        bc = sum(np.sqrt(p_ideal.get(k, 0) * p_noisy.get(k, 0)) for k in all_keys)
        results.append({
            "noise_rate": rate,
            "distribution_fidelity": float(bc),
            "counts": counts,
        })
    return results


def verify_teleportation(alpha: complex, beta: complex) -> dict:
    """
    Perform rigorous mathematical verification that all 4 measurement branches
    reconstruct the input state with unit fidelity (F = 1.0 ± 10⁻⁶).

    Checks each branch (00, 01, 10, 11) individually and flags an overall pass/fail.
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
            "fidelity": float(oc["fidelity"]),
            "passed": bool(passed),
        })

    return {
        "alpha": alpha,
        "beta": beta,
        "all_passed": bool(all_passed),
        "details": details,
    }


def run_verification_suite() -> list[dict]:
    """
    Execute quantitative fidelity verification across 8 fundamental benchmark states:
        1. |0⟩ ground state
        2. |1⟩ excited state
        3. |+⟩ equal superposition on X-axis
        4. |−⟩ anti-symmetric superposition on X-axis
        5. |i+⟩ imaginary superposition on Y-axis
        6. |i−⟩ negative imaginary superposition on Y-axis
        7. 0.6|0⟩ + 0.8|1⟩ arbitrary real state
        8. (1+i)/√3 |0⟩ + 1/√3 |1⟩ complex state with non-zero relative phase

    Returns:
        list[dict]: Array of verification results verifying that all states achieve 100% fidelity.
    """
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
    for name, a, b in test_states:
        v = verify_teleportation(a, b)
        v["state_name"] = name
        results.append(v)
    return results


# ─── 4. IBM Quantum Cloud Integration & Calibration ───────────────────────────

from qiskit_ibm_runtime import QiskitRuntimeService

# Save your API key and crn and have access to the quantum computers
your_api_key = "fFfXXOtzorYMEnJ_N-OOpMVmYifj4ZmW0GxUJNN4aGCi"
your_crn = "crn:v1:bluemix:public:quantum-computing:us-east:a/bebe6d634e114fa49d27f6df3d902c6b:fdbe7491-2d6e-484c-9240-30be98d41891::"

try:
    QiskitRuntimeService.save_account(
        channel="ibm_cloud",
        token=your_api_key,
        instance=your_crn,
        overwrite=True,
    )
except Exception:
    pass

IBM_DEFAULT_TOKEN = your_api_key
IBM_DEFAULT_CRN = your_crn

# Calibration telemetry snapshot for ibm_kingston (156-qubit Heron r2 processor in us-east)
# Used to display physical hardware specs and contextualize hardware error rates
IBM_KINGSTON_CALIBRATION: dict[str, Any] = {
    "backend_name": "ibm_kingston",
    "processor_type": "Heron r2",
    "num_qubits": 156,
    "region": "us-east (Washington DC)",
    "t1_median_us": 232.01,          # Median longitudinal energy relaxation time T1
    "t2_median_us": 136.34,          # Median transverse dephasing coherence time T2
    "cz_error_median": 1.961e-3,      # Median 2-qubit CZ entangling gate error rate (0.196%)
    "sx_error_median": 2.668e-4,      # Median 1-qubit SX (√X) gate error rate (0.027%)
    "readout_error_median": 9.949e-3, # Median measurement readout error rate (0.995%)
    "init_error_median": 2.000e-3,    # State preparation / initialization error rate
}


def build_kingston_noise_model() -> NoiseModel:
    """
    Construct a realistic Qiskit Aer NoiseModel calibrated to ibm_kingston (Heron r2).

    Physical Calibration Parameters:
        - T1 relaxation: 232.01 µs
        - T2 dephasing: 136.34 µs
        - Two-qubit CZ entangling error: 0.1961%
        - Single-qubit SX / RZ gate error: 0.0267%
        - Measurement readout error: 0.9949%
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
    """
    Initialize an authenticated QiskitRuntimeService connection to IBM Quantum Cloud.

    Authentication Strategy:
        1. Attempt to load existing saved account 'default-cloud' from ~/.qiskit/qiskit-ibm.json.
        2. If unavailable, instantiate directly using the project API token and CRN instance.
    """
    from qiskit_ibm_runtime import QiskitRuntimeService

    try:
        # Load from local stored configuration if already initialized
        return QiskitRuntimeService(name="default-cloud")
    except Exception:
        pass

    # Fallback to direct credentials
    tok = token or IBM_DEFAULT_TOKEN
    inst = instance or IBM_DEFAULT_CRN
    return QiskitRuntimeService(channel=channel, token=tok, instance=inst)


def query_cloud_backends(service: Any = None) -> list[dict]:
    """
    Query IBM Quantum Cloud to retrieve operational status, qubit counts, and queue depth
    for all accessible physical QPUs (e.g., ibm_kingston, ibm_marrakesh, ibm_fez).

    Returns:
        list[dict]: Array of backend status dictionaries.
    """
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
    Transpile and submit the quantum teleportation circuit to a physical IBM Quantum QPU.

    Execution Workflow:
        1. Build the high-level quantum teleportation circuit.
        2. Transpile the circuit into Instruction Set Architecture (ISA) native gates
           compatible with the physical backend (e.g. CZ, SX, RZ gates on Heron r2).
        3. Submit the job using the Qiskit Runtime SamplerV2 primitive.
        4. Return the unique Job ID for asynchronous queue tracking.

    Parameters:
        alpha, beta  : Message state amplitudes.
        backend_name : Target physical backend (default: 'ibm_kingston').
        shots        : Number of measurement shots.
        service      : Optional authenticated QiskitRuntimeService.

    Returns:
        dict: Submission metadata containing job_id and status.
    """
    from qiskit import transpile
    from qiskit_ibm_runtime import SamplerV2

    if service is None:
        service = get_ibm_service()

    alpha, beta = normalize_state(alpha, beta)
    backend = service.backend(backend_name)
    qc = create_teleportation_circuit(alpha, beta)

    # Transpile circuit to match the physical processor's coupling map and native basis gates
    isa_circuit = transpile(qc, backend=backend, optimization_level=1)

    # Dispatch job to IBM Quantum cloud scheduler via SamplerV2
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
    """
    Fetch the execution status and measurement counts of an IBM Quantum Cloud job.

    Status Progression:
        - QUEUED: The job is waiting in the IBM Quantum physical queue in Washington DC.
        - RUNNING: The job is currently actively executing on the dilution refrigerator QPU.
        - DONE: Execution completed; measurement bitstrings are parsed and returned.
    """
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
            # Extract measurement counts from the SamplerV2 result data structure
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


# ─── 5. CLI Demonstration Entry Point ─────────────────────────────────────────

if __name__ == "__main__":
    import sys

    # If --cloud flag is passed, query real IBM Quantum backends
    if "--cloud" in sys.argv:
        print("Quantum Teleportation Engine — Live IBM Cloud Fleet")
        print("=" * 60)
        try:
            backends = query_cloud_backends()
            for b in backends:
                print(f"  • {b['name']} ({b['processor_type']}, {b['num_qubits']}Q): "
                      f"Operational={b['operational']}, Pending Jobs={b['pending_jobs']}")
        except Exception as err:
            print(f"Cloud connection failed: {err}")

    # If --jobs flag is passed, list recent jobs in IBM Quantum Cloud
    elif "--jobs" in sys.argv:
        print("Quantum Teleportation Engine — Recent IBM Cloud Jobs")
        print("=" * 60)
        try:
            service = get_ibm_service()
            recent_jobs = service.jobs(limit=5)
            if not recent_jobs:
                print("No jobs found in your IBM Quantum account.")
            for j in recent_jobs:
                bname = j.backend().name if j.backend() else "unknown"
                print(f"  • Job ID: {j.job_id()} | Backend: {bname} | Status: {j.status()} | Created: {j.creation_date}")
        except Exception as err:
            print(f"Failed to fetch jobs: {err}")

    # If --submit flag is passed, actually transpile and submit to real IBM Quantum hardware
    elif "--submit" in sys.argv:
        backend = "ibm_kingston"
        for arg in sys.argv:
            if arg.startswith("--backend="):
                backend = arg.split("=")[1]
        print(f"Quantum Teleportation Engine — Submitting to Physical IBM QPU ({backend})")
        print("=" * 60)
        print("Transpiling circuit to ISA basis gates and dispatching via SamplerV2...")
        try:
            res = submit_cloud_teleportation(0.6, 0.8, backend_name=backend, shots=1024)
            print("\n✓ Job Submitted Successfully to IBM Quantum Cloud!")
            print(f"  • Job ID   : {res['job_id']}")
            print(f"  • Backend  : {res['backend']}")
            print(f"  • Status   : {res['status']}")
            print(f"  • Shots    : {res['shots']}")
            print(f"\nTrack live on IBM Quantum Dashboard:")
            print(f"  https://quantum.cloud.ibm.com/jobs/{res['job_id']}")
        except Exception as err:
            print(f"Submission failed: {err}")

    else:
        # Default local run: Teleport test state |ψ⟩ = 0.6|0⟩ + 0.8|1⟩ on local AerSimulator
        alpha = 0.6
        beta = 0.8

        circuit, counts = run_teleportation(alpha, beta)

        print("Quantum Teleportation")
        print("---------------------")
        print("Input state: 0.6|0> + 0.8|1>")
        print("\nMeasurement counts (Local AerSimulator):")
        print(counts)

        print("\nCircuit:")
        print(circuit.draw(output="text"))

        print("\n" + "=" * 60)
        print("Note: The above executed on your local CPU (AerSimulator in ~5ms).")
        print("To submit to real physical IBM Quantum hardware, run:")
        print("    python3 -m quantum_teleportation --submit")
        print("To view your recent IBM Cloud jobs, run:")
        print("    python3 -m quantum_teleportation --jobs")
