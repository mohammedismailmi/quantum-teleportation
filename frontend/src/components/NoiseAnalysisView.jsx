import React, { useState } from 'react';
import { Activity, ShieldAlert, TrendingDown, RefreshCw, Info, CheckCircle } from 'lucide-react';
import KatexView from './KatexView';

const DEFAULT_NOISE_DATA = [
  { noise_rate: 0.0, noise_percent: 0.0, fidelity: 1.0000 },
  { noise_rate: 0.01, noise_percent: 1.0, fidelity: 0.9854 },
  { noise_rate: 0.02, noise_percent: 2.0, fidelity: 0.9712 },
  { noise_rate: 0.04, noise_percent: 4.0, fidelity: 0.9429 },
  { noise_rate: 0.08, noise_percent: 8.0, fidelity: 0.8876 },
  { noise_rate: 0.12, noise_percent: 12.0, fidelity: 0.8351 },
  { noise_rate: 0.16, noise_percent: 16.0, fidelity: 0.7840 },
  { noise_rate: 0.20, noise_percent: 20.0, fidelity: 0.7355 },
];

export default function NoiseAnalysisView({
  alpha,
  beta,
  onRunNoiseSweep,
  noiseResults = null,
  isLoading = false,
}) {
  const [selectedRate, setSelectedRate] = useState(0.02);

  const data = noiseResults || DEFAULT_NOISE_DATA;

  // Chart dimensions for SVG
  const width = 560;
  const height = 260;
  const padding = { top: 30, right: 30, bottom: 45, left: 55 };

  const plotWidth = width - padding.left - padding.right;
  const plotHeight = height - padding.top - padding.bottom;

  // Min and max
  const minFid = 0.65;
  const maxFid = 1.02;

  const getX = (rate) => padding.left + (rate / 0.20) * plotWidth;
  const getY = (fid) => padding.top + plotHeight - ((fid - minFid) / (maxFid - minFid)) * plotHeight;

  // Generate SVG path for data curve
  const points = data.map((d) => ({
    x: getX(d.noise_rate),
    y: getY(d.fidelity),
    ...d,
  }));

  const pathD = points.reduce((acc, p, idx) => {
    return idx === 0 ? `M ${p.x} ${p.y}` : `${acc} L ${p.x} ${p.y}`;
  }, '');

  // Find data point closest to selected rate
  const activePoint = points.reduce((prev, curr) =>
    Math.abs(curr.noise_rate - selectedRate) < Math.abs(prev.noise_rate - selectedRate) ? curr : prev
  );

  return (
    <div className="card formal-card">
      <div className="card-header">
        <div className="header-title-group">
          <Activity className="icon-formal" size={18} />
          <div>
            <h3 className="section-title">Quantum Noise & Realistic Hardware Fidelity Analysis</h3>
            <p className="section-subtitle">
              Simulate teleportation on noisy intermediate-scale quantum (NISQ) processors subject to depolarizing error channels
            </p>
          </div>
        </div>

        <button
          className="btn btn-secondary btn-sm"
          onClick={() => onRunNoiseSweep()}
          disabled={isLoading}
        >
          {isLoading ? <RefreshCw size={13} className="spin" /> : <RefreshCw size={13} />}
          {isLoading ? 'Sweeping Noise...' : 'Re-run Noise Sweep'}
        </button>
      </div>

      <div className="card-body">
        <div className="noise-grid">
          {/* Interactive Plot */}
          <div className="noise-plot-panel">
            <div className="plot-header-sub">
              <h4 className="sub-panel-title">
                <TrendingDown size={15} /> Distribution Fidelity vs Gate Depolarizing Error Rate <KatexView math="p" />
              </h4>
              <span className="badge badge-outline">Depolarizing Channel Model</span>
            </div>

            <div className="svg-plot-container">
              <svg viewBox={`0 0 ${width} ${height}`} className="formal-plot-svg">
                {/* Grid horizontal lines */}
                {[0.7, 0.8, 0.9, 1.0].map((val) => {
                  const yPos = getY(val);
                  return (
                    <g key={val}>
                      <line
                        x1={padding.left}
                        y1={yPos}
                        x2={width - padding.right}
                        y2={yPos}
                        stroke="#e2e8f0"
                        strokeDasharray="4,4"
                      />
                      <text
                        x={padding.left - 8}
                        y={yPos + 4}
                        textAnchor="end"
                        fontSize="10"
                        fill="#64748b"
                        fontFamily="JetBrains Mono"
                      >
                        {(val * 100).toFixed(0)}%
                      </text>
                    </g>
                  );
                })}

                {/* Grid vertical lines */}
                {[0.0, 0.05, 0.10, 0.15, 0.20].map((rate) => {
                  const xPos = getX(rate);
                  return (
                    <g key={rate}>
                      <line
                        x1={xPos}
                        y1={padding.top}
                        x2={xPos}
                        y2={height - padding.bottom}
                        stroke="#e2e8f0"
                        strokeDasharray="4,4"
                      />
                      <text
                        x={xPos}
                        y={height - padding.bottom + 16}
                        textAnchor="middle"
                        fontSize="10"
                        fill="#64748b"
                        fontFamily="JetBrains Mono"
                      >
                        {(rate * 100).toFixed(0)}%
                      </text>
                    </g>
                  );
                })}

                {/* X and Y Axis titles */}
                <text
                  x={width / 2}
                  y={height - 8}
                  textAnchor="middle"
                  fontSize="11"
                  fill="#00005d"
                  fontWeight="600"
                >
                  Depolarizing Error Rate per Gate (p)
                </text>
                <text
                  x={15}
                  y={height / 2}
                  textAnchor="middle"
                  transform={`rotate(-90 15 ${height / 2})`}
                  fontSize="11"
                  fill="#00005d"
                  fontWeight="600"
                >
                  Quantum Fidelity 𝓕
                </text>

                {/* Area under curve fill */}
                <path
                  d={`${pathD} L ${getX(0.20)} ${getY(minFid)} L ${getX(0.0)} ${getY(minFid)} Z`}
                  fill="rgba(27, 70, 140, 0.08)"
                />

                {/* Curve line */}
                <path
                  d={pathD}
                  fill="none"
                  stroke="#1b468c"
                  strokeWidth="2.5"
                  strokeLinecap="round"
                />

                {/* Data points */}
                {points.map((p) => {
                  const isActive = p.noise_rate === activePoint.noise_rate;
                  return (
                    <circle
                      key={p.noise_rate}
                      cx={p.x}
                      cy={p.y}
                      r={isActive ? 6 : 4}
                      fill={isActive ? '#00005d' : '#ffffff'}
                      stroke={isActive ? '#1b468c' : '#1b468c'}
                      strokeWidth={isActive ? 3 : 2}
                      style={{ cursor: 'pointer' }}
                      onClick={() => setSelectedRate(p.noise_rate)}
                    />
                  );
                })}

                {/* Active point indicator badge */}
                <g transform={`translate(${activePoint.x}, ${activePoint.y - 12})`}>
                  <rect
                    x="-45"
                    y="-20"
                    width="90"
                    height="18"
                    rx="4"
                    fill="#00005d"
                  />
                  <text
                    x="0"
                    y="-8"
                    textAnchor="middle"
                    fill="#ffffff"
                    fontSize="10"
                    fontWeight="600"
                    fontFamily="JetBrains Mono"
                  >
                    F = {(activePoint.fidelity * 100).toFixed(2)}%
                  </text>
                </g>
              </svg>
            </div>

            {/* Slider to interactively test error rate */}
            <div className="slider-row mt-3">
              <div className="slider-label-group">
                <span className="slider-label">Test Hardware Gate Error Rate (p):</span>
                <span className="slider-val">
                  {(selectedRate * 100).toFixed(1)}% depolarizing error
                </span>
              </div>
              <input
                type="range"
                className="slider-input"
                min="0.0"
                max="0.20"
                step="0.01"
                value={selectedRate}
                onChange={(e) => setSelectedRate(parseFloat(e.target.value))}
              />
            </div>
          </div>

          {/* Theory and Analysis Details */}
          <div className="noise-info-panel">
            <h4 className="sub-panel-title mb-3">
              <Info size={15} /> Physical Decoherence in Real Quantum Hardware
            </h4>

            <div className="info-callout mb-3">
              <div className="callout-header">
                <ShieldAlert size={15} className="text-b1" />
                <strong>Depolarizing Quantum Channel:</strong>
              </div>
              <div className="callout-math mt-1">
                <KatexView
                  math={String.raw`\mathcal{E}_p(\rho) = (1 - p)\rho + \frac{p}{3}\left(X\rho X + Y\rho Y + Z\rho Z\right)`}
                  block
                />
              </div>
              <p className="callout-desc mt-2">
                Every single-qubit gate (H, X, Z) and two-qubit entangling gate (CNOT) subjects the qubits to stochastic Pauli noise, transforming pure quantum superpositions into mixed classical statistical ensembles.
              </p>
            </div>

            <div className="hardware-specs-table">
              <div className="spec-row">
                <span className="spec-name">Ideal Simulation (Local Qiskit Aer):</span>
                <span className="spec-val text-success">Fidelity = 1.0000 (100.0%)</span>
              </div>
              <div className="spec-row" style={{ backgroundColor: 'rgba(27, 70, 140, 0.05)', borderRadius: '4px' }}>
                <span className="spec-name">
                  <strong>ibm_kingston (Heron r2):</strong><br />
                  <small className="text-muted">2Q CZ: 1.961E-3 | SX: 2.668E-4 | Readout: 0.995%</small>
                </span>
                <span className="spec-val text-b1">Fidelity ≈ 99.41%</span>
              </div>
              <div className="spec-row">
                <span className="spec-name">
                  T₁ Relaxation (ibm_kingston):<br />
                  <small className="text-muted">Median qubit lifetime</small>
                </span>
                <span className="spec-val">232.01 µs</span>
              </div>
              <div className="spec-row">
                <span className="spec-name">
                  T₂ Dephasing (ibm_kingston):<br />
                  <small className="text-muted">Phase coherence time</small>
                </span>
                <span className="spec-val">136.34 µs</span>
              </div>
              <div className="spec-row">
                <span className="spec-name">Classical Simulation Limit:</span>
                <span className="spec-val text-muted">F = 2/3 (66.7%)</span>
              </div>
            </div>

            <div className="takeaway-box mt-3">
              <CheckCircle size={14} className="text-b1" />
              <span>
                <strong>Quantum Advantage Principle:</strong> Any teleportation protocol achieving fidelity <KatexView math={String.raw`\mathcal{F} > \frac{2}{3} \approx 66.7\%`} /> fundamentally proves non-classical entanglement, exceeding the maximum bound achievable by any classical measurement-and-resynthesis strategy.
              </span>
            </div>

            <div className="info-callout mt-3" style={{ backgroundColor: '#ffffff', borderColor: '#cbd5e1' }}>
              <div className="callout-header">
                <Info size={14} className="text-b1" />
                <strong>Local Aer Simulation vs. Cloud Hardware Queues:</strong>
              </div>
              <p className="callout-desc mt-1">
                This simulator runs locally using <strong>Qiskit Aer</strong> on your machine, computing exact quantum states in milliseconds. Physical cloud QPUs (like <code>ibm_kingston</code>) queue jobs remotely (e.g. 5 pending jobs) where they must await physical hardware access.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
