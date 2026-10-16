import React from 'react';
import { BookOpen, AlertTriangle, ShieldCheck, Zap, Lock } from 'lucide-react';
import KatexView from './KatexView';

export default function TheoryMathView() {
  return (
    <div className="card formal-card">
      <div className="card-header">
        <div className="header-title-group">
          <BookOpen className="icon-formal" size={18} />
          <div>
            <h3 className="section-title">Formal Quantum Mechanical Derivations & Principles</h3>
            <p className="section-subtitle">
              Mathematical proofs, conservation laws, no-cloning theorem, and relativistic communication constraints
            </p>
          </div>
        </div>
      </div>

      <div className="card-body">
        <div className="theory-sections">
          {/* Section 1: Algebraic Tensor Expansion */}
          <div className="theory-section">
            <h4 className="theory-heading">
              1. Full Tripartite State Expansion in the Bell Basis
            </h4>
            <p className="theory-p">
              Let Alice possess an arbitrary pure single-qubit quantum state <KatexView math="|\psi\rangle_Q = \alpha|0\rangle + \beta|1\rangle" /> with <KatexView math="|\alpha|^2 + |\beta|^2 = 1" />. Alice and Bob share an entangled EPR Bell pair in state <KatexView math="|\Phi^+\rangle_{MY} = \frac{1}{\sqrt{2}}(|00\rangle + |11\rangle)_{MY}" />.
            </p>
            <p className="theory-p">
              The combined 3-qubit statevector before Alice’s local operations is the tensor product:
            </p>
            <div className="math-display-card">
              <KatexView
                math="|\psi_0\rangle = |\psi\rangle_Q \otimes |\Phi^+\rangle_{MY} = (\alpha|0\rangle + \beta|1\rangle) \otimes \frac{1}{\sqrt{2}}(|00\rangle + |11\rangle) = \frac{1}{\sqrt{2}}\Big[\alpha|000\rangle + \alpha|011\rangle + \beta|100\rangle + \beta|111\rangle\Big]"
                block
              />
            </div>
            <p className="theory-p mt-3">
              Alice applies a CNOT gate with <KatexView math="Q" /> controlling <KatexView math="M" />, followed by a Hadamard gate on <KatexView math="Q" />. Expressing Alice’s two qubits <KatexView math="(Q, M)" /> in the standard computational basis gives:
            </p>
            <div className="math-display-card">
              <KatexView
                math="|\psi_{\text{final}}\rangle = \frac{1}{2} \Big[ |00\rangle_A (\alpha|0\rangle + \beta|1\rangle)_B + |01\rangle_A (\beta|0\rangle + \alpha|1\rangle)_B + |10\rangle_A (\alpha|0\rangle - \beta|1\rangle)_B + |11\rangle_A (-\beta|0\rangle + \alpha|1\rangle)_B \Big]"
                block
              />
            </div>
          </div>

          {/* Section 2: Bob's Unitary Decoding */}
          <div className="theory-section mt-4">
            <h4 className="theory-heading">
              2. The Feed-Forward Pauli Correction Table
            </h4>
            <p className="theory-p">
              When Alice measures her two qubits in the computational basis, she receives two classical bits <KatexView math="(c_0, c_1)" />. Each outcome occurs with uniform probability <KatexView math="P = 1/4 = 25\%" />:
            </p>
            <div className="formal-table-container mt-2">
              <table className="formal-table">
                <thead>
                  <tr>
                    <th>Classical Bits (c₀, c₁)</th>
                    <th>Alice’s Bell Projection</th>
                    <th>Bob’s Subsystem State</th>
                    <th>Required Unitary U</th>
                    <th>Reconstructed State</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td>(0, 0)</td>
                    <td><KatexView math="|\Phi^+\rangle = \frac{|00\rangle + |11\rangle}{\sqrt{2}}" /></td>
                    <td><KatexView math="\alpha|0\rangle + \beta|1\rangle" /></td>
                    <td><KatexView math="I = \begin{pmatrix} 1 & 0 \\ 0 & 1 \end{pmatrix}" /></td>
                    <td><KatexView math="|\psi\rangle" /></td>
                  </tr>
                  <tr>
                    <td>(0, 1)</td>
                    <td><KatexView math="|\Psi^+\rangle = \frac{|01\rangle + |10\rangle}{\sqrt{2}}" /></td>
                    <td><KatexView math="\beta|0\rangle + \alpha|1\rangle" /></td>
                    <td><KatexView math="X = \begin{pmatrix} 0 & 1 \\ 1 & 0 \end{pmatrix}" /></td>
                    <td><KatexView math="|\psi\rangle" /></td>
                  </tr>
                  <tr>
                    <td>(1, 0)</td>
                    <td><KatexView math="|\Phi^-\rangle = \frac{|00\rangle - |11\rangle}{\sqrt{2}}" /></td>
                    <td><KatexView math="\alpha|0\rangle - \beta|1\rangle" /></td>
                    <td><KatexView math="Z = \begin{pmatrix} 1 & 0 \\ 0 & -1 \end{pmatrix}" /></td>
                    <td><KatexView math="|\psi\rangle" /></td>
                  </tr>
                  <tr>
                    <td>(1, 1)</td>
                    <td><KatexView math="|\Psi^-\rangle = \frac{|01\rangle - |10\rangle}{\sqrt{2}}" /></td>
                    <td><KatexView math="\beta|0\rangle - \alpha|1\rangle" /></td>
                    <td><KatexView math="XZ = \begin{pmatrix} 0 & -1 \\ 1 & 0 \end{pmatrix}" /></td>
                    <td><KatexView math="|\psi\rangle" /></td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          {/* Section 3: No-Cloning & No-Signaling Theorems */}
          <div className="theory-grid-two mt-4">
            <div className="principle-card">
              <div className="principle-header">
                <Lock size={16} className="text-b1" />
                <h5>The No-Cloning Theorem</h5>
              </div>
              <p className="principle-body">
                The No-Cloning Theorem (Wootters & Zurek, 1982) states that an unknown quantum state cannot be copied without destroying the original.
              </p>
              <div className="math-mini-card">
                <KatexView math="U_{\text{clone}} |\psi\rangle |0\rangle \ne |\psi\rangle |\psi\rangle" />
              </div>
              <p className="principle-note">
                Quantum teleportation fully obeys this law: Alice's projective measurement irreversibly collapses and destroys her original message qubit state <KatexView math="|\psi\rangle_Q" />. Information is <em>teleported</em>, never cloned.
              </p>
            </div>

            <div className="principle-card">
              <div className="principle-header">
                <AlertTriangle size={16} className="text-b1" />
                <h5>No-Signaling & Relativistic Causality</h5>
              </div>
              <p className="principle-body">
                Quantum teleportation cannot transmit information faster than light (<KatexView math="v \le c" />). Prior to receiving Alice's classical bits, Bob's reduced density matrix is obtained by the partial trace:
              </p>
              <div className="math-mini-card">
                <KatexView math="\rho_Y = \text{Tr}_{QM}(|\psi\rangle\langle\psi|) = \frac{1}{2} |0\rangle\langle 0| + \frac{1}{2} |1\rangle\langle 1| = \frac{1}{2} \mathbb{I}_2" />
              </div>
              <p className="principle-note">
                Bob's state is completely mixed and possesses zero information about <KatexView math="\alpha" /> or <KatexView math="\beta" />. Without the two classical bits, Bob cannot perform the correction.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
