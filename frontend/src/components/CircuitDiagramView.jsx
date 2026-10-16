import React, { useState } from 'react';
import { Network, Copy, Check, Code, FileText, Download } from 'lucide-react';
import KatexView from './KatexView';

export default function CircuitDiagramView({
  alpha,
  beta,
  circuitText = null,
}) {
  const [copiedType, setCopiedType] = useState(null);
  const [activeTab, setActiveTab] = useState('svg');
  const [hoverGate, setHoverGate] = useState(null);

  // Generate python Qiskit code
  const qiskitCode = `from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit_aer import AerSimulator
import numpy as np

# 1. Initialize Quantum and Classical Registers
q = QuantumRegister(3, name="q")
c = ClassicalRegister(2, name="c")
qc = QuantumCircuit(q, c)

# 2. State Preparation on Alice's message qubit q[0]
alpha = complex(${alpha.real.toFixed(4)}, ${alpha.imag.toFixed(4)})
beta = complex(${beta.real.toFixed(4)}, ${beta.imag.toFixed(4)})
qc.initialize([alpha, beta], q[0])
qc.barrier(label="Prep")

# 3. Create EPR Bell pair |Phi+> between Alice (q[1]) and Bob (q[2])
qc.h(q[1])
qc.cx(q[1], q[2])
qc.barrier(label="Bell Pair")

# 4. Alice's Entangling Operations (Bell Basis Measurement)
qc.cx(q[0], q[1])
qc.h(q[0])
qc.barrier(label="Bell Meas")

# 5. Measure Alice's qubits into classical bits
qc.measure(q[0], c[0])
qc.measure(q[1], c[1])

# 6. Bob's Conditional Feed-Forward Unitary Corrections
with qc.if_test((c[1], 1)):
    qc.x(q[2])
with qc.if_test((c[0], 1)):
    qc.z(q[2])

# Execute on Aer Simulator
simulator = AerSimulator()
job = simulator.run(qc, shots=1024)
counts = job.result().get_counts()
print("Measurement counts (c1c0):", counts)
`;

  const qasmCode = `OPENQASM 3.0;
include "stdgates.inc";

qubit[3] q;
bit[2] c;

// Prepare State |psi>
// initialize([${alpha.real.toFixed(4)}, ${beta.real.toFixed(4)}], q[0]);
h q[1];
cx q[1], q[2];
barrier q;

// Bell Measurement
cx q[0], q[1];
h q[0];
barrier q;

c[0] = measure q[0];
c[1] = measure q[1];

// Conditional Corrections
if (c[1] == 1) {
    x q[2];
}
if (c[0] == 1) {
    z q[2];
}
`;

  const copyToClipboard = (text, type) => {
    navigator.clipboard.writeText(text);
    setCopiedType(type);
    setTimeout(() => setCopiedType(null), 2000);
  };

  return (
    <div className="card formal-card">
      <div className="card-header">
        <div className="header-title-group">
          <Network className="icon-formal" size={18} />
          <div>
            <h3 className="section-title">Interactive Quantum Circuit & Program Export</h3>
            <p className="section-subtitle">
              Formal 3-qubit circuit architecture with classical feed-forward control and unitary correction gates
            </p>
          </div>
        </div>

        <div className="view-switch-tabs">
          <button
            className={`tab-btn ${activeTab === 'svg' ? 'active' : ''}`}
            onClick={() => setActiveTab('svg')}
          >
            Circuit Schematic
          </button>
          <button
            className={`tab-btn ${activeTab === 'code' ? 'active' : ''}`}
            onClick={() => setActiveTab('code')}
          >
            Python (Qiskit)
          </button>
          <button
            className={`tab-btn ${activeTab === 'qasm' ? 'active' : ''}`}
            onClick={() => setActiveTab('qasm')}
          >
            OpenQASM 3.0
          </button>
          <button
            className={`tab-btn ${activeTab === 'ascii' ? 'active' : ''}`}
            onClick={() => setActiveTab('ascii')}
          >
            ASCII Diagram
          </button>
        </div>
      </div>

      <div className="card-body">
        {activeTab === 'svg' && (
          <div className="circuit-schematic-wrapper">
            <div className="circuit-diagram-container">
              <svg viewBox="0 0 980 340" className="circuit-svg">
                <defs>
                  {/* Gate shadow */}
                  <filter id="gateShadow" x="-10%" y="-10%" width="120%" height="120%">
                    <feDropShadow dx="0" dy="1.5" stdDeviation="1" floodColor="#00005d" floodOpacity="0.12" />
                  </filter>
                </defs>

                {/* Background grid / Stage regions */}
                <rect x="130" y="20" width="130" height="295" fill="rgba(27, 70, 140, 0.02)" rx="6" />
                <rect x="270" y="20" width="170" height="295" fill="rgba(27, 70, 140, 0.04)" rx="6" />
                <rect x="450" y="20" width="230" height="295" fill="rgba(27, 70, 140, 0.02)" rx="6" />
                <rect x="690" y="20" width="250" height="295" fill="rgba(27, 70, 140, 0.05)" rx="6" />

                {/* Stage Titles */}
                <text x="195" y="40" textAnchor="middle" fill="#1b468c" fontSize="11" fontWeight="600">
                  1. State Prep
                </text>
                <text x="355" y="40" textAnchor="middle" fill="#1b468c" fontSize="11" fontWeight="600">
                  2. Bell Entanglement
                </text>
                <text x="565" y="40" textAnchor="middle" fill="#1b468c" fontSize="11" fontWeight="600">
                  3. Alice's Bell Measurement
                </text>
                <text x="815" y="40" textAnchor="middle" fill="#00005d" fontSize="11" fontWeight="600">
                  4. Bob's Unitary Corrections
                </text>

                {/* Quantum Wires */}
                {/* Wire 0: Alice Q */}
                <text x="30" y="85" fill="#00005d" fontSize="13" fontWeight="600">
                  q₀ (Q)
                </text>
                <text x="75" y="85" fill="#64748b" fontSize="11">
                  |ψ⟩
                </text>
                <line x1="110" y1="80" x2="650" y2="80" stroke="#00005d" strokeWidth="1.5" />

                {/* Wire 1: Alice M */}
                <text x="30" y="155" fill="#00005d" fontSize="13" fontWeight="600">
                  q₁ (M)
                </text>
                <text x="75" y="155" fill="#64748b" fontSize="11">
                  |0⟩
                </text>
                <line x1="110" y1="150" x2="650" y2="150" stroke="#00005d" strokeWidth="1.5" />

                {/* Wire 2: Bob Y */}
                <text x="30" y="225" fill="#00005d" fontSize="13" fontWeight="600">
                  q₂ (Y)
                </text>
                <text x="75" y="225" fill="#64748b" fontSize="11">
                  |0⟩
                </text>
                <line x1="110" y1="220" x2="940" y2="220" stroke="#00005d" strokeWidth="1.5" />

                {/* Classical Register Wires (Double line) */}
                <text x="30" y="295" fill="#64748b" fontSize="13" fontWeight="600">
                  c [2]
                </text>
                <line x1="110" y1="288" x2="940" y2="288" stroke="#94a3b8" strokeWidth="1.2" />
                <line x1="110" y1="292" x2="940" y2="292" stroke="#94a3b8" strokeWidth="1.2" />

                {/* State Prep Box on q0 */}
                <g
                  onMouseEnter={() => setHoverGate('StatePrep')}
                  onMouseLeave={() => setHoverGate(null)}
                  style={{ cursor: 'pointer' }}
                >
                  <rect x="150" y="60" width="70" height="40" rx="4" fill="#1b468c" filter="url(#gateShadow)" />
                  <text x="185" y="85" textAnchor="middle" fill="#ffffff" fontSize="11" fontWeight="600">
                    Init |ψ⟩
                  </text>
                </g>

                {/* Bell Pair Creation: H on q1, CNOT q1->q2 */}
                <g
                  onMouseEnter={() => setHoverGate('H')}
                  onMouseLeave={() => setHoverGate(null)}
                  style={{ cursor: 'pointer' }}
                >
                  <rect x="295" y="130" width="38" height="40" rx="4" fill="#00005d" filter="url(#gateShadow)" />
                  <text x="314" y="155" textAnchor="middle" fill="#ffffff" fontSize="14" fontWeight="600">
                    H
                  </text>
                </g>

                {/* CNOT between q1 and q2 */}
                <line x1="380" y1="150" x2="380" y2="220" stroke="#00005d" strokeWidth="2" />
                <circle cx="380" cy="150" r="5" fill="#00005d" />
                <circle cx="380" cy="220" r="11" fill="#ffffff" stroke="#00005d" strokeWidth="2" />
                <line x1="369" y1="220" x2="391" y2="220" stroke="#00005d" strokeWidth="2" />
                <line x1="380" y1="209" x2="380" y2="231" stroke="#00005d" strokeWidth="2" />

                {/* Alice's Bell Measurement: CNOT q0->q1, H on q0 */}
                <line x1="475" y1="80" x2="475" y2="150" stroke="#1b468c" strokeWidth="2" />
                <circle cx="475" cy="80" r="5" fill="#1b468c" />
                <circle cx="475" cy="150" r="11" fill="#ffffff" stroke="#1b468c" strokeWidth="2" />
                <line x1="464" y1="150" x2="486" y2="150" stroke="#1b468c" strokeWidth="2" />
                <line x1="475" y1="139" x2="475" y2="161" stroke="#1b468c" strokeWidth="2" />

                {/* H on q0 */}
                <g
                  onMouseEnter={() => setHoverGate('H')}
                  onMouseLeave={() => setHoverGate(null)}
                  style={{ cursor: 'pointer' }}
                >
                  <rect x="525" y="60" width="38" height="40" rx="4" fill="#00005d" filter="url(#gateShadow)" />
                  <text x="544" y="85" textAnchor="middle" fill="#ffffff" fontSize="14" fontWeight="600">
                    H
                  </text>
                </g>

                {/* Measurement Gate on q0 */}
                <g>
                  <rect x="590" y="60" width="42" height="40" rx="4" fill="#f1f5f9" stroke="#00005d" strokeWidth="1.5" />
                  <path d="M 600 84 A 11 11 0 0 1 622 84" fill="none" stroke="#00005d" strokeWidth="1.5" />
                  <line x1="611" y1="84" x2="618" y2="72" stroke="#00005d" strokeWidth="1.5" />
                  {/* Classical feed line down to register c0 */}
                  <line x1="611" y1="100" x2="611" y2="288" stroke="#94a3b8" strokeWidth="1.2" strokeDasharray="3,3" />
                  <text x="618" y="280" fill="#64748b" fontSize="9">c₀</text>
                </g>

                {/* Measurement Gate on q1 */}
                <g>
                  <rect x="590" y="130" width="42" height="40" rx="4" fill="#f1f5f9" stroke="#00005d" strokeWidth="1.5" />
                  <path d="M 600 154 A 11 11 0 0 1 622 154" fill="none" stroke="#00005d" strokeWidth="1.5" />
                  <line x1="611" y1="154" x2="618" y2="142" stroke="#00005d" strokeWidth="1.5" />
                  {/* Classical feed line down to register c1 */}
                  <line x1="611" y1="170" x2="611" y2="292" stroke="#94a3b8" strokeWidth="1.2" strokeDasharray="3,3" />
                  <text x="618" y="260" fill="#64748b" fontSize="9">c₁</text>
                </g>

                {/* Classical Control Wires to Bob's gates */}
                {/* Control to X gate from c1 */}
                <line x1="745" y1="292" x2="745" y2="240" stroke="#00005d" strokeWidth="1.5" strokeDasharray="2,2" />
                <circle cx="745" cy="292" r="3.5" fill="#00005d" />

                {/* Bob's conditional X gate */}
                <g
                  onMouseEnter={() => setHoverGate('X')}
                  onMouseLeave={() => setHoverGate(null)}
                  style={{ cursor: 'pointer' }}
                >
                  <rect x="725" y="200" width="40" height="40" rx="4" fill="#1b468c" filter="url(#gateShadow)" />
                  <text x="745" y="225" textAnchor="middle" fill="#ffffff" fontSize="14" fontWeight="600">
                    X
                  </text>
                  <text x="745" y="255" textAnchor="middle" fill="#1b468c" fontSize="9" fontWeight="600">
                    if c₁=1
                  </text>
                </g>

                {/* Control to Z gate from c0 */}
                <line x1="835" y1="288" x2="835" y2="240" stroke="#00005d" strokeWidth="1.5" strokeDasharray="2,2" />
                <circle cx="835" cy="288" r="3.5" fill="#00005d" />

                {/* Bob's conditional Z gate */}
                <g
                  onMouseEnter={() => setHoverGate('Z')}
                  onMouseLeave={() => setHoverGate(null)}
                  style={{ cursor: 'pointer' }}
                >
                  <rect x="815" y="200" width="40" height="40" rx="4" fill="#00005d" filter="url(#gateShadow)" />
                  <text x="835" y="225" textAnchor="middle" fill="#ffffff" fontSize="14" fontWeight="600">
                    Z
                  </text>
                  <text x="835" y="255" textAnchor="middle" fill="#00005d" fontSize="9" fontWeight="600">
                    if c₀=1
                  </text>
                </g>

                {/* Output indicator */}
                <g>
                  <rect x="895" y="202" width="65" height="36" rx="4" fill="#ecfdf5" stroke="#059669" strokeWidth="1.5" />
                  <text x="927" y="225" textAnchor="middle" fill="#059669" fontSize="12" fontWeight="700">
                    |ψ⟩ Replic.
                  </text>
                </g>
              </svg>
            </div>

            {/* Hover Gate Info Inspector */}
            <div className="gate-tooltip-bar mt-3">
              {hoverGate === 'H' && (
                <div className="tooltip-content">
                  <strong>Hadamard Gate (H):</strong> Creates an equal superposition.
                  <span className="tooltip-matrix">
                    <KatexView math="H = \frac{1}{\sqrt{2}}\begin{pmatrix} 1 & 1 \\ 1 & -1 \end{pmatrix}" />
                  </span>
                </div>
              )}
              {hoverGate === 'X' && (
                <div className="tooltip-content">
                  <strong>Pauli-X Gate:</strong> Quantum NOT / Bit-flip operator.
                  <span className="tooltip-matrix">
                    <KatexView math="X = \begin{pmatrix} 0 & 1 \\ 1 & 0 \end{pmatrix}" />
                  </span>
                </div>
              )}
              {hoverGate === 'Z' && (
                <div className="tooltip-content">
                  <strong>Pauli-Z Gate:</strong> Phase-flip operator.
                  <span className="tooltip-matrix">
                    <KatexView math="Z = \begin{pmatrix} 1 & 0 \\ 0 & -1 \end{pmatrix}" />
                  </span>
                </div>
              )}
              {hoverGate === 'StatePrep' && (
                <div className="tooltip-content">
                  <strong>State Initialization:</strong> Prepares Alice's message qubit into state <KatexView math="|\psi\rangle = \alpha|0\rangle + \beta|1\rangle" />.
                </div>
              )}
              {!hoverGate && (
                <div className="tooltip-placeholder">
                  Hover over any quantum gate (H, X, Z, Init) in the circuit diagram above to inspect its unitary operator matrix
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'code' && (
          <div className="code-export-panel">
            <div className="code-panel-top">
              <span className="code-lang-label">
                <Code size={14} /> Python (Qiskit 1.x / Aer)
              </span>
              <button
                className="btn btn-secondary btn-sm"
                onClick={() => copyToClipboard(qiskitCode, 'python')}
              >
                {copiedType === 'python' ? <Check size={13} className="text-success" /> : <Copy size={13} />}
                {copiedType === 'python' ? 'Copied!' : 'Copy Code'}
              </button>
            </div>
            <pre className="code-block">
              <code>{qiskitCode}</code>
            </pre>
          </div>
        )}

        {activeTab === 'qasm' && (
          <div className="code-export-panel">
            <div className="code-panel-top">
              <span className="code-lang-label">
                <FileText size={14} /> OpenQASM 3.0 Program
              </span>
              <button
                className="btn btn-secondary btn-sm"
                onClick={() => copyToClipboard(qasmCode, 'qasm')}
              >
                {copiedType === 'qasm' ? <Check size={13} className="text-success" /> : <Copy size={13} />}
                {copiedType === 'qasm' ? 'Copied!' : 'Copy QASM'}
              </button>
            </div>
            <pre className="code-block">
              <code>{qasmCode}</code>
            </pre>
          </div>
        )}

        {activeTab === 'ascii' && (
          <div className="code-export-panel">
            <div className="code-panel-top">
              <span className="code-lang-label">
                <FileText size={14} /> Qiskit ASCII Text Drawing
              </span>
              <button
                className="btn btn-secondary btn-sm"
                onClick={() => copyToClipboard(circuitText || 'Loading...', 'ascii')}
              >
                {copiedType === 'ascii' ? <Check size={13} className="text-success" /> : <Copy size={13} />}
                {copiedType === 'ascii' ? 'Copied!' : 'Copy ASCII'}
              </button>
            </div>
            <pre className="code-block ascii-block">
              <code>{circuitText || 'Run simulation to inspect live circuit ASCII rendering.'}</code>
            </pre>
          </div>
        )}
      </div>
    </div>
  );
}
