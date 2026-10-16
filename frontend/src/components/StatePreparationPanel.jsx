import React from 'react';
import { Sliders, RefreshCw, Zap, Compass, CheckCircle } from 'lucide-react';
import KatexView from './KatexView';

const PRESETS = [
  { name: '|0⟩', label: '|0⟩ Ground', alpha: { real: 1, imag: 0 }, beta: { real: 0, imag: 0 }, theta: 0, phi: 0 },
  { name: '|1⟩', label: '|1⟩ Excited', alpha: { real: 0, imag: 0 }, beta: { real: 1, imag: 0 }, theta: Math.PI, phi: 0 },
  { name: '|+⟩', label: '|+⟩ Superpos.', alpha: { real: 1 / Math.SQRT2, imag: 0 }, beta: { real: 1 / Math.SQRT2, imag: 0 }, theta: Math.PI / 2, phi: 0 },
  { name: '|−⟩', label: '|−⟩ Phase', alpha: { real: 1 / Math.SQRT2, imag: 0 }, beta: { real: -1 / Math.SQRT2, imag: 0 }, theta: Math.PI / 2, phi: Math.PI },
  { name: '|i⟩', label: '|i+⟩ Circular', alpha: { real: 1 / Math.SQRT2, imag: 0 }, beta: { real: 0, imag: 1 / Math.SQRT2 }, theta: Math.PI / 2, phi: Math.PI / 2 },
  { name: '|-i⟩', label: '|i−⟩ Circular', alpha: { real: 1 / Math.SQRT2, imag: 0 }, beta: { real: 0, imag: -1 / Math.SQRT2 }, theta: Math.PI / 2, phi: 1.5 * Math.PI },
  { name: '0.6|0⟩+0.8|1⟩', label: 'Custom 3:4:5', alpha: { real: 0.6, imag: 0 }, beta: { real: 0.8, imag: 0 }, theta: 2 * Math.acos(0.6), phi: 0 },
];

export default function StatePreparationPanel({
  alpha,
  beta,
  theta,
  phi,
  onStateChange,
}) {
  // Update state via angles (theta, phi)
  const handleAngleChange = (newTheta, newPhi) => {
    const a_r = Math.cos(newTheta / 2);
    const b_r = Math.sin(newTheta / 2) * Math.cos(newPhi);
    const b_i = Math.sin(newTheta / 2) * Math.sin(newPhi);

    onStateChange({
      alpha: { real: a_r, imag: 0 },
      beta: { real: b_r, imag: b_i },
      theta: newTheta,
      phi: newPhi,
    });
  };

  // Direct amplitude adjustment
  const handleAmplitudeChange = (field, part, value) => {
    const val = parseFloat(value) || 0;
    const newAlpha = { ...alpha };
    const newBeta = { ...beta };

    if (field === 'alpha') newAlpha[part] = val;
    if (field === 'beta') newBeta[part] = val;

    // Normalization
    const norm = Math.sqrt(
      newAlpha.real ** 2 + newAlpha.imag ** 2 + newBeta.real ** 2 + newBeta.imag ** 2
    );

    if (norm > 1e-9) {
      const normA = { real: newAlpha.real / norm, imag: newAlpha.imag / norm };
      const normB = { real: newBeta.real / norm, imag: newBeta.imag / norm };

      const th = 2 * Math.acos(Math.min(1, Math.max(0, Math.hypot(normA.real, normA.imag))));
      const phA = Math.atan2(normA.imag, normA.real);
      const phB = Math.atan2(normB.imag, normB.real);
      let ph = phB - phA;
      if (ph < 0) ph += 2 * Math.PI;

      onStateChange({
        alpha: normA,
        beta: normB,
        theta: th,
        phi: ph,
      });
    }
  };

  const setRandomState = () => {
    const rTheta = Math.random() * Math.PI;
    const rPhi = Math.random() * 2 * Math.PI;
    handleAngleChange(rTheta, rPhi);
  };

  // Formatted amplitude strings
  const formatComp = (c) => {
    const r = c.real;
    const i = c.imag;
    if (Math.abs(r) < 1e-4 && Math.abs(i) < 1e-4) return '0';
    if (Math.abs(i) < 1e-4) return r.toFixed(3);
    if (Math.abs(r) < 1e-4) return `${i >= 0 ? '' : '-'}${Math.abs(i).toFixed(3)}i`;
    const sign = i >= 0 ? '+' : '-';
    return `${r.toFixed(3)} ${sign} ${Math.abs(i).toFixed(3)}i`;
  };

  const prob0 = alpha.real ** 2 + alpha.imag ** 2;
  const prob1 = beta.real ** 2 + beta.imag ** 2;

  // LaTeX equation
  const latexFormula = `|\\psi\\rangle_Q = \\left(${formatComp(alpha)}\\right)|0\\rangle + \\left(${formatComp(beta)}\\right)|1\\rangle`;

  return (
    <div className="card formal-card">
      <div className="card-header">
        <div className="header-title-group">
          <Sliders className="icon-formal" size={18} />
          <div>
            <h3 className="section-title">Message Qubit State Preparation</h3>
            <p className="section-subtitle">
              Configure Alice's unknown message qubit <KatexView math="|\\psi\\rangle_Q" /> to be teleported to Bob
            </p>
          </div>
        </div>
        <button
          className="btn btn-secondary btn-sm"
          onClick={setRandomState}
          title="Generate random pure quantum state"
        >
          <RefreshCw size={13} />
          Random State
        </button>
      </div>

      <div className="card-body">
        {/* Preset Selector */}
        <div className="form-group mb-4">
          <label className="form-label">Standard Cardinal & Benchmark Presets</label>
          <div className="preset-grid">
            {PRESETS.map((p) => {
              const isSelected =
                Math.abs(theta - p.theta) < 0.05 &&
                (Math.abs(phi - p.phi) < 0.05 || p.theta < 0.01 || Math.abs(p.theta - Math.PI) < 0.01);
              return (
                <button
                  key={p.name}
                  className={`btn-preset ${isSelected ? 'active' : ''}`}
                  onClick={() =>
                    onStateChange({
                      alpha: p.alpha,
                      beta: p.beta,
                      theta: p.theta,
                      phi: p.phi,
                    })
                  }
                >
                  <span className="preset-name">{p.name}</span>
                  <span className="preset-sub">{p.label}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Sliders and Numerical Controls */}
        <div className="controls-grid">
          {/* Spherical Angle Sliders */}
          <div className="sub-panel">
            <h4 className="sub-panel-title">
              <Compass size={14} /> Bloch Sphere Coordinates
            </h4>

            <div className="slider-row">
              <div className="slider-label-group">
                <span className="slider-label">Polar Angle θ (Colatitude)</span>
                <span className="slider-val">
                  {(theta / Math.PI).toFixed(3)}π ({(theta * 180 / Math.PI).toFixed(1)}°)
                </span>
              </div>
              <input
                type="range"
                className="slider-input"
                min="0"
                max={Math.PI}
                step="0.01"
                value={theta}
                onChange={(e) => handleAngleChange(parseFloat(e.target.value), phi)}
              />
              <div className="slider-ticks">
                <span>0 (|0⟩)</span>
                <span>π/2 (Equator)</span>
                <span>π (|1⟩)</span>
              </div>
            </div>

            <div className="slider-row mt-3">
              <div className="slider-label-group">
                <span className="slider-label">Azimuthal Angle φ (Longitude)</span>
                <span className="slider-val">
                  {(phi / Math.PI).toFixed(3)}π ({(phi * 180 / Math.PI).toFixed(1)}°)
                </span>
              </div>
              <input
                type="range"
                className="slider-input"
                min="0"
                max={2 * Math.PI}
                step="0.01"
                value={phi}
                onChange={(e) => handleAngleChange(theta, parseFloat(e.target.value))}
              />
              <div className="slider-ticks">
                <span>0 (+X)</span>
                <span>π/2 (+Y)</span>
                <span>π (−X)</span>
                <span>2π</span>
              </div>
            </div>
          </div>

          {/* Complex Amplitudes Inputs */}
          <div className="sub-panel">
            <h4 className="sub-panel-title">
              <Zap size={14} /> Complex State Amplitudes
            </h4>

            <div className="amp-input-grid">
              <div className="amp-box">
                <span className="amp-tag">Re(α)</span>
                <input
                  type="number"
                  step="0.05"
                  className="amp-number-input"
                  value={alpha.real.toFixed(3)}
                  onChange={(e) => handleAmplitudeChange('alpha', 'real', e.target.value)}
                />
              </div>
              <div className="amp-box">
                <span className="amp-tag">Im(α)</span>
                <input
                  type="number"
                  step="0.05"
                  className="amp-number-input"
                  value={alpha.imag.toFixed(3)}
                  onChange={(e) => handleAmplitudeChange('alpha', 'imag', e.target.value)}
                />
              </div>
              <div className="amp-box">
                <span className="amp-tag">Re(β)</span>
                <input
                  type="number"
                  step="0.05"
                  className="amp-number-input"
                  value={beta.real.toFixed(3)}
                  onChange={(e) => handleAmplitudeChange('beta', 'real', e.target.value)}
                />
              </div>
              <div className="amp-box">
                <span className="amp-tag">Im(β)</span>
                <input
                  type="number"
                  step="0.05"
                  className="amp-number-input"
                  value={beta.imag.toFixed(3)}
                  onChange={(e) => handleAmplitudeChange('beta', 'imag', e.target.value)}
                />
              </div>
            </div>

            <div className="state-equation-box mt-3">
              <div className="eq-label">Statevector Dirac Expression:</div>
              <div className="eq-math">
                <KatexView math={latexFormula} block />
              </div>
            </div>
          </div>
        </div>

        {/* Measurement Probability Distribution Preview */}
        <div className="prob-bar-container mt-4">
          <div className="prob-header">
            <span className="prob-title">Computational Basis Measurement Probabilities</span>
            <span className="prob-sum">
              |α|² + |β|² = {(prob0 + prob1).toFixed(4)}
              <CheckCircle size={12} className="ml-1 text-success" />
            </span>
          </div>

          <div className="prob-bar-track">
            <div
              className="prob-bar-segment segment-0"
              style={{ width: `${prob0 * 100}%` }}
              title={`P(|0⟩) = ${(prob0 * 100).toFixed(1)}%`}
            >
              {prob0 > 0.12 && `P(|0⟩): ${(prob0 * 100).toFixed(1)}%`}
            </div>
            <div
              className="prob-bar-segment segment-1"
              style={{ width: `${prob1 * 100}%` }}
              title={`P(|1⟩) = ${(prob1 * 100).toFixed(1)}%`}
            >
              {prob1 > 0.12 && `P(|1⟩): ${(prob1 * 100).toFixed(1)}%`}
            </div>
          </div>

          <div className="prob-legend">
            <div className="legend-item">
              <span className="legend-dot dot-b2"></span>
              <span>Basis |0⟩: {(prob0 * 100).toFixed(2)}% (|α|² = {prob0.toFixed(4)})</span>
            </div>
            <div className="legend-item">
              <span className="legend-dot dot-b1"></span>
              <span>Basis |1⟩: {(prob1 * 100).toFixed(2)}% (|β|² = {prob1.toFixed(4)})</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
