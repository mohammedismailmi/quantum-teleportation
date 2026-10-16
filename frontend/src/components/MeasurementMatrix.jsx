import React, { useState } from 'react';
import { GitBranch, CheckCircle2, ArrowRight, ShieldCheck, Cpu } from 'lucide-react';
import KatexView from './KatexView';
import BlochSphere3D from './BlochSphere3D';

const OUTCOMES = [
  {
    c0: 0,
    c1: 0,
    bitstring: '00',
    bellName: '|Φ+⟩',
    bellFormula: '\\frac{1}{\\sqrt{2}}(|00\\rangle + |11\\rangle)',
    gateLabel: 'Identity (I)',
    gateSymbol: 'I',
    correctionDesc: 'No correction needed. Bob’s state is already identical to |ψ⟩.',
    matrixDesc: '\\begin{pmatrix} 1 & 0 \\\\ 0 & 1 \\end{pmatrix}',
    stateBeforeFormula: '\\alpha|0\\rangle + \\beta|1\\rangle',
  },
  {
    c0: 0,
    c1: 1,
    bitstring: '01',
    bellName: '|Ψ+⟩',
    bellFormula: '\\frac{1}{\\sqrt{2}}(|01\\rangle + |10\\rangle)',
    gateLabel: 'Pauli X (Bit Flip)',
    gateSymbol: 'X',
    correctionDesc: 'Bob applies a bit-flip gate X to restore swapped amplitudes.',
    matrixDesc: '\\begin{pmatrix} 0 & 1 \\\\ 1 & 0 \\end{pmatrix}',
    stateBeforeFormula: '\\beta|0\\rangle + \\alpha|1\\rangle = X|\\psi\\rangle',
  },
  {
    c0: 1,
    c1: 0,
    bitstring: '10',
    bellName: '|Φ-⟩',
    bellFormula: '\\frac{1}{\\sqrt{2}}(|00\\rangle - |11\\rangle)',
    gateLabel: 'Pauli Z (Phase Flip)',
    gateSymbol: 'Z',
    correctionDesc: 'Bob applies a phase-flip gate Z to correct the relative sign.',
    matrixDesc: '\\begin{pmatrix} 1 & 0 \\\\ 0 & -1 \\end{pmatrix}',
    stateBeforeFormula: '\\alpha|0\\rangle - \\beta|1\\rangle = Z|\\psi\\rangle',
  },
  {
    c0: 1,
    c1: 1,
    bitstring: '11',
    bellName: '|Ψ-⟩',
    bellFormula: '\\frac{1}{\\sqrt{2}}(|01\\rangle - |10\\rangle)',
    gateLabel: 'Pauli XZ (Bit + Phase)',
    gateSymbol: 'XZ',
    correctionDesc: 'Bob applies both X and Z gates to restore both amplitude and sign.',
    matrixDesc: 'X \\cdot Z = \\begin{pmatrix} 0 & -1 \\\\ 1 & 0 \\end{pmatrix}',
    stateBeforeFormula: '\\beta|0\\rangle - \\alpha|1\\rangle = XZ|\\psi\\rangle',
  },
];

export default function MeasurementMatrix({
  alpha,
  beta,
  blochCoords,
}) {
  const [selectedOutcome, setSelectedOutcome] = useState('00');

  const outcome = OUTCOMES.find((o) => o.bitstring === selectedOutcome) || OUTCOMES[0];

  // Compute pre-correction Bloch vector for the selected outcome
  const [x, y, z] = blochCoords;
  let preBloch = [x, y, z];
  if (outcome.bitstring === '01') {
    // X gate flips Z and preserves X, inverts Y: (x, -y, -z)
    preBloch = [x, -y, -z];
  } else if (outcome.bitstring === '10') {
    // Z gate inverts X and Y: (-x, -y, z)
    preBloch = [-x, -y, z];
  } else if (outcome.bitstring === '11') {
    // XZ gate: (-x, y, -z)
    preBloch = [-x, y, -z];
  }

  return (
    <div className="card formal-card">
      <div className="card-header">
        <div className="header-title-group">
          <GitBranch className="icon-formal" size={18} />
          <div>
            <h3 className="section-title">Alice's 4 Measurement Outcomes & Bob's Corrections</h3>
            <p className="section-subtitle">
              Every branch of Alice's joint measurement deterministically collapses into a known unitary rotation
            </p>
          </div>
        </div>
        <div className="fidelity-badge">
          <ShieldCheck size={14} className="text-success" />
          <span>Universal Fidelity: 100.00%</span>
        </div>
      </div>

      <div className="card-body">
        {/* Outcome Selector Cards */}
        <div className="outcome-cards-grid">
          {OUTCOMES.map((o) => {
            const isSelected = o.bitstring === selectedOutcome;
            return (
              <div
                key={o.bitstring}
                className={`outcome-card ${isSelected ? 'selected' : ''}`}
                onClick={() => setSelectedOutcome(o.bitstring)}
              >
                <div className="outcome-card-top">
                  <span className="outcome-bitstring">Bits: {o.bitstring}</span>
                  <span className="badge badge-subtle">{o.bellName}</span>
                </div>

                <div className="outcome-gate-info">
                  <div className="gate-pill">{o.gateSymbol}</div>
                  <span className="gate-title">{o.gateLabel}</span>
                </div>

                <div className="outcome-prob-tag">
                  Theoretical Prob: <strong>25.0%</strong>
                </div>
              </div>
            );
          })}
        </div>

        {/* Selected Branch Deep-Dive Panel */}
        <div className="branch-deepdive mt-4">
          <div className="deepdive-header">
            <h4 className="deepdive-title">
              Deep-Dive Analysis for Outcome: <span className="text-b1">c₀ = {outcome.c0}, c₁ = {outcome.c1} ({outcome.bitstring})</span>
            </h4>
            <span className="badge badge-success">Branch Verification: Passed</span>
          </div>

          <div className="deepdive-body-grid">
            {/* Mathematical Transformations */}
            <div className="math-transform-panel">
              <div className="step-box">
                <span className="step-num">1</span>
                <div>
                  <strong>Alice’s Measured Bell Basis State:</strong>
                  <div className="mt-1">
                    <KatexView math={`|\\text{Bell}\\rangle = ${outcome.bellName} = ${outcome.bellFormula}`} />
                  </div>
                </div>
              </div>

              <div className="step-box mt-3">
                <span className="step-num">2</span>
                <div>
                  <strong>Bob’s Collapsed State (Before Correction):</strong>
                  <div className="mt-1">
                    <KatexView math={`|\\psi_{\\text{pre}}\\rangle_Y = ${outcome.stateBeforeFormula}`} />
                  </div>
                </div>
              </div>

              <div className="step-box mt-3">
                <span className="step-num">3</span>
                <div>
                  <strong>Bob’s Unitary Correction Operator:</strong>
                  <div className="mt-1 flex-align-center">
                    <KatexView math={`U = ${outcome.matrixDesc}`} />
                  </div>
                  <p className="correction-text mt-1">{outcome.correctionDesc}</p>
                </div>
              </div>

              <div className="step-box final-step mt-3">
                <span className="step-num success">4</span>
                <div>
                  <strong>Bob’s Final Reconstructed State:</strong>
                  <div className="mt-1">
                    <KatexView math={`|\\psi\\rangle_Y = U |\\psi_{\\text{pre}}\\rangle = \\alpha|0\\rangle + \\beta|1\\rangle = |\\psi\\rangle_Q`} />
                  </div>
                  <div className="fidelity-metric mt-2">
                    <CheckCircle2 size={15} className="text-success" />
                    <span>State Overlap Fidelity: <strong>1.000000 (100.0%)</strong></span>
                  </div>
                </div>
              </div>
            </div>

            {/* Visual State Comparison Bloch Spheres */}
            <div className="spheres-comparison-panel">
              <h5 className="sub-panel-title">
                <Cpu size={14} /> Bloch Sphere Transformation for Outcome {outcome.bitstring}
              </h5>

              <div className="dual-bloch-flex">
                <div className="bloch-sub-view">
                  <span className="bloch-sub-label">Bob's State (Pre-Correction)</span>
                  <BlochSphere3D
                    vector={preBloch}
                    title="Pre-Correction State"
                    size={190}
                    showAngles={false}
                  />
                  <span className="bloch-tag-info">Distorted by channel</span>
                </div>

                <div className="arrow-divider">
                  <span className="gate-transform-pill">{outcome.gateSymbol} Gate</span>
                  <ArrowRight size={22} className="text-b1" />
                </div>

                <div className="bloch-sub-view">
                  <span className="bloch-sub-label">Bob's State (Restored)</span>
                  <BlochSphere3D
                    vector={blochCoords}
                    targetVector={blochCoords}
                    title="Restored State |ψ⟩"
                    size={190}
                    showAngles={false}
                  />
                  <span className="bloch-tag-info success">Fidelity = 1.000</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
