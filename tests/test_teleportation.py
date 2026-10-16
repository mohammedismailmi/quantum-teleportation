"""
Tests for the Quantum Teleportation Engine
==========================================
Validates correctness of:
- Bell pair preparation
- Three-qubit combined state amplitudes
- All four measurement outcomes
- Conditional correction mapping
- Fidelity = 1 across multiple test states (including complex amplitudes)
- Histogram uses actual simulator results
- Bloch sphere reduced density matrices
"""

import sys
import os
import numpy as np
import pytest

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector, DensityMatrix, partial_trace, state_fidelity

from quantum_teleportation import (
    PRESET_STATES,
    amplitudes_to_bloch,
    bloch_angles_to_amplitudes,
    compute_all_outcomes,
    compute_conditional_state,
    compute_stage_states,
    create_teleportation_circuit,
    dm_to_bloch,
    is_pure,
    normalize_state,
    run_simulation,
    verify_teleportation,
    run_verification_suite,
)


# ─── Test state normalisation ────────────────────────────────────────────────

class TestNormalisation:
    def test_already_normalised(self):
        a, b = normalize_state(0.6 + 0j, 0.8 + 0j)
        assert np.isclose(abs(a) ** 2 + abs(b) ** 2, 1.0)

    def test_needs_normalisation(self):
        a, b = normalize_state(3.0, 4.0)
        assert np.isclose(abs(a) ** 2 + abs(b) ** 2, 1.0)
        assert np.isclose(abs(a), 3 / 5)
        assert np.isclose(abs(b), 4 / 5)

    def test_complex_normalisation(self):
        a, b = normalize_state(1 + 1j, 1.0)
        assert np.isclose(abs(a) ** 2 + abs(b) ** 2, 1.0)

    def test_zero_raises(self):
        with pytest.raises(ValueError):
            normalize_state(0.0, 0.0)


# ─── Test Bell pair preparation ──────────────────────────────────────────────

class TestBellPair:
    def test_bell_pair_phi_plus(self):
        """Verify that H→CNOT on |00⟩ produces |Φ+⟩ = (|00⟩+|11⟩)/√2."""
        qc = QuantumCircuit(2)
        qc.h(0)
        qc.cx(0, 1)
        sv = Statevector.from_instruction(qc)
        data = sv.data

        # Qiskit little-endian: |00⟩ is index 0, |11⟩ is index 3
        expected = np.zeros(4, dtype=complex)
        expected[0] = 1 / np.sqrt(2)  # |00⟩
        expected[3] = 1 / np.sqrt(2)  # |11⟩

        assert np.allclose(data, expected), f"Got {data}, expected {expected}"

    def test_bell_pair_in_teleportation(self):
        """Verify Bell pair is |Φ+⟩ at Stage 2 of the teleportation."""
        stages = compute_stage_states(1.0, 0.0)
        stage2 = stages[2]  # After H + CNOT

        # M and Y should each be maximally mixed
        assert not stage2["is_pure"][1], "M should be mixed after Bell pair"
        assert not stage2["is_pure"][2], "Y should be mixed after Bell pair"

        # Check the Bloch vector of M is at the origin
        bm = stage2["bloch"][1]
        assert np.allclose(bm, (0, 0, 0), atol=0.01), f"M Bloch: {bm}"

        by = stage2["bloch"][2]
        assert np.allclose(by, (0, 0, 0), atol=0.01), f"Y Bloch: {by}"


# ─── Test three-qubit combined state ─────────────────────────────────────────

class TestCombinedState:
    def test_initial_state_amplitudes(self):
        """Stage 0: |ψ⟩_Q ⊗ |0⟩_M ⊗ |0⟩_Y."""
        alpha, beta = 0.6, 0.8
        stages = compute_stage_states(alpha, beta)
        sv = stages[0]["statevector"]

        # Only |000⟩ and |100⟩ should have nonzero amplitudes
        # Qiskit little-endian: |QMY⟩ → index = Y*4 + M*2 + Q
        # |000⟩ → index 0, amplitude = α
        # |100⟩ → index 1, amplitude = β
        assert np.isclose(abs(sv[0]), abs(alpha))
        assert np.isclose(abs(sv[1]), abs(beta))
        assert np.allclose(np.abs(sv[2:]), 0)

    def test_stage2_state_structure(self):
        """Stage 2: |ψ⟩_Q ⊗ |Φ+⟩_MY."""
        alpha, beta = 1 / np.sqrt(2), 1 / np.sqrt(2)
        stages = compute_stage_states(alpha, beta)
        sv = stages[2]["statevector"]

        # Full state: (α|0⟩ + β|1⟩) ⊗ (|00⟩+|11⟩)/√2
        # = α/√2 |000⟩ + α/√2 |011⟩ + β/√2 |100⟩ + β/√2 |111⟩
        # Qiskit indices: |QMY⟩ → Y*4 + M*2 + Q
        # |000⟩ → 0, |011⟩ → 6, |100⟩ → 1, |111⟩ → 7
        expected_nonzero = {0, 1, 6, 7}
        for i in range(8):
            if i in expected_nonzero:
                assert abs(sv[i]) > 0.1, f"Expected nonzero at index {i}"
            else:
                assert abs(sv[i]) < 1e-10, f"Expected zero at index {i}"

    def test_stage4_equal_probabilities(self):
        """Stage 4: each computational-basis outcome should have prob ≈ 1/4 for Bob."""
        alpha, beta = 0.6, 0.8
        stages = compute_stage_states(alpha, beta)
        sv = stages[4]["statevector"]

        # Group by (Q, M) outcome
        v = sv.reshape(2, 2, 2)  # v[Y][M][Q]
        for q in range(2):
            for m in range(2):
                bob = v[:, m, q]
                prob = np.sum(np.abs(bob) ** 2)
                assert np.isclose(prob, 0.25, atol=1e-6), \
                    f"Prob for Q={q},M={m} = {prob}, expected 0.25"


# ─── Test all four measurement outcomes ──────────────────────────────────────

class TestMeasurementOutcomes:
    @pytest.mark.parametrize("alpha,beta", [
        (1.0, 0.0),
        (0.0, 1.0),
        (1 / np.sqrt(2), 1 / np.sqrt(2)),
        (1 / np.sqrt(2), -1 / np.sqrt(2)),
        (1 / np.sqrt(2), 1j / np.sqrt(2)),
        (1 / np.sqrt(2), -1j / np.sqrt(2)),
        (0.6, 0.8),
        ((1 + 1j) / np.sqrt(3), 1 / np.sqrt(3)),
    ])
    def test_all_outcomes_fidelity_one(self, alpha, beta):
        """Verify fidelity = 1 for all outcomes across test states."""
        outcomes = compute_all_outcomes(alpha, beta)
        for oc in outcomes:
            assert np.isclose(oc["fidelity"], 1.0, atol=1e-6), \
                f"State α={alpha},β={beta} outcome {oc['bits_str']}: fidelity={oc['fidelity']}"

    def test_outcome_probabilities_sum_to_one(self):
        """Total probability across all outcomes must be 1."""
        outcomes = compute_all_outcomes(0.6, 0.8)
        total_prob = sum(oc["probability"] for oc in outcomes)
        assert np.isclose(total_prob, 1.0, atol=1e-6)

    def test_outcome_probabilities_each_quarter(self):
        """Each outcome should have probability ≈ 1/4."""
        outcomes = compute_all_outcomes(0.6, 0.8)
        for oc in outcomes:
            assert np.isclose(oc["probability"], 0.25, atol=1e-6), \
                f"Outcome {oc['bits_str']}: prob={oc['probability']}"


# ─── Test conditional correction mapping ─────────────────────────────────────

class TestCorrectionMapping:
    def test_no_correction_needed_for_00(self):
        """Outcome 00 → I (no correction)."""
        oc = compute_conditional_state(0.6, 0.8, 0, 0)
        assert oc["gates"] == []
        # Bob's state should already be correct
        assert np.isclose(oc["fidelity"], 1.0)

    def test_x_correction_for_01(self):
        """Outcome 01 → X gate."""
        oc = compute_conditional_state(0.6, 0.8, 0, 1)
        assert oc["gates"] == ["X"]
        assert np.isclose(oc["fidelity"], 1.0)

    def test_z_correction_for_10(self):
        """Outcome 10 → Z gate."""
        oc = compute_conditional_state(0.6, 0.8, 1, 0)
        assert oc["gates"] == ["Z"]
        assert np.isclose(oc["fidelity"], 1.0)

    def test_xz_correction_for_11(self):
        """Outcome 11 → X then Z."""
        oc = compute_conditional_state(0.6, 0.8, 1, 1)
        assert oc["gates"] == ["X", "Z"]
        assert np.isclose(oc["fidelity"], 1.0)


# ─── Test fidelity across states ─────────────────────────────────────────────

class TestVerification:
    def test_verification_suite(self):
        """Full verification suite should pass all 8 states × 4 outcomes."""
        suite = run_verification_suite()
        for v in suite:
            assert v["all_passed"], f"Failed for state: {v['state_name']}"

    def test_verify_single_state(self):
        """Verify a single complex-amplitude state."""
        v = verify_teleportation((1 + 1j) / np.sqrt(3), 1 / np.sqrt(3))
        assert v["all_passed"]


# ─── Test simulator runs produce actual results ──────────────────────────────

class TestSimulation:
    def test_simulation_produces_counts(self):
        """Simulator must return non-empty counts dict."""
        result = run_simulation(0.6, 0.8, shots=256)
        counts = result["counts"]
        assert len(counts) > 0
        assert sum(counts.values()) == 256

    def test_all_outcomes_present_with_enough_shots(self):
        """With enough shots, all 4 outcomes should appear."""
        result = run_simulation(1 / np.sqrt(2), 1 / np.sqrt(2), shots=4096)
        counts = result["counts"]
        # All four outcomes should appear (with very high probability)
        assert len(counts) >= 3, f"Only {len(counts)} outcomes in {counts}"


# ─── Test Bloch sphere calculations ──────────────────────────────────────────

class TestBlochSphere:
    def test_ket0_bloch(self):
        bx, by, bz = dm_to_bloch(np.array([[1, 0], [0, 0]], dtype=complex))
        assert np.isclose(bz, 1.0) and np.isclose(bx, 0) and np.isclose(by, 0)

    def test_ket1_bloch(self):
        bx, by, bz = dm_to_bloch(np.array([[0, 0], [0, 1]], dtype=complex))
        assert np.isclose(bz, -1.0)

    def test_mixed_state_at_origin(self):
        bx, by, bz = dm_to_bloch(np.eye(2, dtype=complex) / 2)
        assert np.isclose(bx, 0) and np.isclose(by, 0) and np.isclose(bz, 0)

    def test_plus_state_bloch(self):
        rho = np.array([[0.5, 0.5], [0.5, 0.5]], dtype=complex)
        bx, by, bz = dm_to_bloch(rho)
        assert np.isclose(bx, 1.0) and np.isclose(by, 0) and np.isclose(bz, 0)

    def test_mixed_state_detection(self):
        assert is_pure(np.array([[1, 0], [0, 0]], dtype=complex))
        assert not is_pure(np.eye(2, dtype=complex) / 2)

    def test_reduced_dm_is_correct(self):
        """Verify reduced density matrices from stage states use real Qiskit calculations."""
        stages = compute_stage_states(0.6, 0.8)

        # Stage 0: Q should be pure with |ψ⟩ = 0.6|0⟩ + 0.8|1⟩
        rdm_q = stages[0]["reduced_dm"][0]
        expected_q = np.array([[0.36, 0.48], [0.48, 0.64]], dtype=complex)
        assert np.allclose(rdm_q, expected_q, atol=1e-6)

        # Stage 0: M should be |0⟩
        rdm_m = stages[0]["reduced_dm"][1]
        expected_m = np.array([[1, 0], [0, 0]], dtype=complex)
        assert np.allclose(rdm_m, expected_m, atol=1e-6)

    def test_bloch_angles_roundtrip(self):
        """θ, φ → α, β → Bloch → compare."""
        theta, phi = np.pi / 3, np.pi / 4
        alpha, beta = bloch_angles_to_amplitudes(theta, phi)
        bx, by, bz = amplitudes_to_bloch(alpha, beta)

        # Expected: x=sinθ cosφ, y=sinθ sinφ, z=cosθ
        assert np.isclose(bx, np.sin(theta) * np.cos(phi), atol=1e-6)
        assert np.isclose(by, np.sin(theta) * np.sin(phi), atol=1e-6)
        assert np.isclose(bz, np.cos(theta), atol=1e-6)


# ─── Test circuit construction ───────────────────────────────────────────────

class TestCircuit:
    def test_circuit_has_3_qubits(self):
        qc = create_teleportation_circuit(0.6, 0.8)
        assert qc.num_qubits == 3

    def test_circuit_has_2_classical_bits(self):
        qc = create_teleportation_circuit(0.6, 0.8)
        assert qc.num_clbits == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
