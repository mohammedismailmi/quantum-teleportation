import React, { useState, useEffect } from 'react';
import {
  ChevronLeft,
  ChevronRight,
  Play,
  Pause,
  RotateCcw,
  Layers,
  Activity,
  CheckCircle2,
  Share2,
  Lock,
  ArrowRight,
  Sparkles,
} from 'lucide-react';
import KatexView from './KatexView';
import BlochSphere3D from './BlochSphere3D';

const STAGES = [
  {
    id: 0,
    title: 'Stage 0: State Preparation',
    tag: 'Initialization',
    desc: "Alice prepares the unknown quantum message |ψ⟩ on qubit Q (q0). Qubits M (q1) and Y (q2) are initialized in the ground state |0⟩.",
    math: '|\\psi_0\\rangle = |\\psi\\rangle_Q \\otimes |0\\rangle_M \\otimes |0\\rangle_Y = (\\alpha|0\\rangle + \\beta|1\\rangle) \\otimes |00\\rangle_{MY}',
    aliceStatus: 'Holds pure state |ψ⟩ (Q)',
    bobStatus: 'Holds ground state |0⟩ (Y)',
    entanglementStatus: 'No entanglement (Separable product state)',
  },
  {
    id: 1,
    title: 'Stage 1: Bell Pair Creation',
    tag: 'EPR Entanglement',
    desc: 'A Bell state |Φ+⟩ is generated between qubits M (q1) and Y (q2) using a Hadamard gate followed by a CNOT gate. Bob takes qubit Y, Alice takes qubit M.',
    math: '|\\Phi^+\\rangle_{MY} = \\frac{1}{\\sqrt{2}}(|00\\rangle + |11\\rangle)_{MY} \\implies |\\psi_1\\rangle = |\\psi\\rangle_Q \\otimes |\\Phi^+\\rangle_{MY}',
    aliceStatus: 'Holds Q and entangled half M',
    bobStatus: 'Holds entangled half Y',
    entanglementStatus: 'M and Y maximally entangled (EPR Pair)',
  },
  {
    id: 2,
    title: "Stage 2: Alice's Entangling CNOT & Hadamard",
    tag: 'Bell Basis Transform',
    desc: "Alice applies a CNOT gate from her message qubit Q to her Bell qubit M, followed by a Hadamard gate on Q. This rotates Alice's two qubits into the Bell basis.",
    math: '|\\psi_2\\rangle = \\frac{1}{2}\\Big[|00\\rangle(\\alpha|0\\rangle + \\beta|1\\rangle) + |01\\rangle(\\alpha|1\\rangle + \\beta|0\\rangle) + |10\\rangle(\\alpha|0\\rangle - \\beta|1\\rangle) + |11\\rangle(\\alpha|1\\rangle - \\beta|0\\rangle)\\Big]_{QMY}',
    aliceStatus: 'Qubits Q and M now entangled with Y',
    bobStatus: 'Y state is correlated with Alice’s joint measurement',
    entanglementStatus: 'Tripartite 3-qubit entangled state',
  },
  {
    id: 3,
    title: "Stage 3: Alice's Bell Measurement",
    tag: 'Quantum Collapse',
    desc: 'Alice measures qubits Q and M in the computational Z-basis. The quantum state collapses into one of 4 classical outcomes (00, 01, 10, 11) with equal 25% probability.',
    math: 'P(c_0, c_1) = \\frac{1}{4} = 25\\% \\quad \\text{for } (c_0, c_1) \\in \\{00, 01, 10, 11\\}',
    aliceStatus: 'Message state destroyed upon measurement (No-Cloning respected)',
    bobStatus: 'Y collapsed into one of 4 rotated variants of |ψ⟩',
    entanglementStatus: 'Entanglement broken by projective measurement',
  },
  {
    id: 4,
    title: 'Stage 4: Classical Transmission',
    tag: 'Classical Channel',
    desc: 'Alice sends the two classical measurement bits (c0, c1) to Bob over an ordinary classical channel. Quantum state teleportation cannot exceed the speed of light.',
    math: '\\text{Alice } \\xrightarrow{\\quad c_0, c_1 \\in \\{0,1\\}^2 \\quad} \\text{ Bob } \\quad (v \\le c)',
    aliceStatus: 'Bits c0, c1 transmitted over classical link',
    bobStatus: 'Awaiting classical bits to determine correction',
    entanglementStatus: 'Classical information exchange in progress',
  },
  {
    id: 5,
    title: "Stage 5: Bob's Conditional Unitary Correction",
    tag: 'Feed-forward Pauli Correction',
    desc: 'Bob receives bits (c0, c1) and applies the unitary correction Z^{c0} X^{c1} to his qubit Y: if c1=1, apply X; if c0=1, apply Z.',
    math: 'U_{\\text{Bob}} = Z^{c_0} X^{c_1} \\quad \\implies U_{\\text{Bob}} |\\psi_Y^{\\text{collapsed}}\\rangle = \\alpha|0\\rangle + \\beta|1\\rangle',
    aliceStatus: 'Alice has only the classical measurement logs',
    bobStatus: 'Bob corrects qubit Y to reconstruct |ψ⟩',
    entanglementStatus: 'Protocol target achieved',
  },
  {
    id: 6,
    title: 'Stage 6: Teleportation Verification',
    tag: 'State Reconstructed',
    desc: 'Teleportation is complete! Bob’s qubit Y is an exact replica of Alice’s initial message qubit Q. The state fidelity is identically 100%.',
    math: '|\\psi\\rangle_Y = \\alpha|0\\rangle + \\beta|1\\rangle \\quad \\implies \\mathcal{F}(\\psi_{\\text{in}}, \\psi_Y) = |\\langle\\psi_{\\text{in}}|\\psi_Y\\rangle|^2 = 1.000000',
    aliceStatus: 'Original state successfully transferred',
    bobStatus: 'Possesses identical quantum state |ψ⟩_Y',
    entanglementStatus: 'State Fidelity: 100.00% (Lossless)',
  },
];

export default function ProtocolWalkthrough({
  alpha,
  beta,
  blochCoords,
  stagesData = null,
}) {
  const [currentStage, setCurrentStage] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [playSpeed, setPlaySpeed] = useState(2500);

  // Auto-play timer
  useEffect(() => {
    let timer;
    if (isPlaying) {
      timer = setInterval(() => {
        setCurrentStage((prev) => {
          if (prev >= STAGES.length - 1) {
            setIsPlaying(false);
            return prev;
          }
          return prev + 1;
        });
      }, playSpeed);
    }
    return () => clearInterval(timer);
  }, [isPlaying, playSpeed]);

  const stageInfo = STAGES[currentStage];

  // Derive per-qubit Bloch vectors for display
  const getQubitBloch = (qubitIdx) => {
    if (currentStage === 0) {
      if (qubitIdx === 0) return blochCoords;
      return [0, 0, 1]; // |0⟩
    }
    if (currentStage === 1) {
      if (qubitIdx === 0) return blochCoords;
      // Entangled qubits M and Y have zero local Bloch vector (completely mixed state ρ = I/2)
      return [0, 0, 0];
    }
    if (currentStage === 2) {
      return [0, 0, 0]; // all 3 entangled
    }
    if (currentStage === 3 || currentStage === 4) {
      // Measured
      if (qubitIdx === 0) return [0, 0, 1];
      if (qubitIdx === 1) return [0, 0, 1];
      return blochCoords; // Bob's state
    }
    if (currentStage >= 5) {
      if (qubitIdx === 2) return blochCoords; // Teleported state!
      return [0, 0, 1];
    }
    return [0, 0, 1];
  };

  return (
    <div className="card formal-card">
      {/* Header & Controls */}
      <div className="card-header">
        <div className="header-title-group">
          <Layers className="icon-formal" size={18} />
          <div>
            <h3 className="section-title">Protocol Walkthrough: Stage-by-Stage Visualizer</h3>
            <p className="section-subtitle">
              Follow the quantum state evolution from Alice’s initial preparation to Bob’s final reconstructed state
            </p>
          </div>
        </div>

        <div className="stage-controls">
          <button
            className="btn btn-secondary btn-sm"
            onClick={() => setCurrentStage(0)}
            title="Reset to Stage 0"
          >
            <RotateCcw size={13} />
          </button>
          <button
            className="btn btn-secondary btn-sm"
            onClick={() => setCurrentStage((p) => Math.max(0, p - 1))}
            disabled={currentStage === 0}
          >
            <ChevronLeft size={15} /> Prev
          </button>
          <button
            className="btn btn-primary btn-sm"
            onClick={() => setIsPlaying(!isPlaying)}
          >
            {isPlaying ? <Pause size={13} /> : <Play size={13} />}
            {isPlaying ? 'Pause' : 'Auto Play'}
          </button>
          <button
            className="btn btn-secondary btn-sm"
            onClick={() => setCurrentStage((p) => Math.min(STAGES.length - 1, p + 1))}
            disabled={currentStage === STAGES.length - 1}
          >
            Next <ChevronRight size={15} />
          </button>
        </div>
      </div>

      <div className="card-body">
        {/* Stepper Progress Bar */}
        <div className="stepper-container">
          <div className="stepper-line">
            <div
              className="stepper-line-fill"
              style={{ width: `${(currentStage / (STAGES.length - 1)) * 100}%` }}
            />
          </div>
          <div className="stepper-nodes">
            {STAGES.map((s, idx) => {
              const isPast = idx < currentStage;
              const isCurrent = idx === currentStage;
              return (
                <button
                  key={s.id}
                  className={`stepper-node ${isCurrent ? 'active' : ''} ${isPast ? 'completed' : ''}`}
                  onClick={() => setCurrentStage(idx)}
                >
                  <div className="node-circle">
                    {isPast ? <CheckCircle2 size={13} /> : idx}
                  </div>
                  <span className="node-label">Stage {idx}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Active Stage Detail Panel */}
        <div className="stage-detail-card mt-4">
          <div className="stage-detail-header">
            <div className="stage-badge-group">
              <span className="badge badge-primary">{stageInfo.tag}</span>
              <h4 className="stage-detail-title">{stageInfo.title}</h4>
            </div>
            <span className="stage-counter">Stage {currentStage + 1} of {STAGES.length}</span>
          </div>

          <p className="stage-description-text">{stageInfo.desc}</p>

          <div className="stage-math-box">
            <div className="math-label">Statevector Equation:</div>
            <div className="math-content">
              <KatexView math={stageInfo.math} block />
            </div>
          </div>

          {/* Qubit Location & Entanglement Badges */}
          <div className="status-grid mt-3">
            <div className="status-card">
              <span className="status-label">Alice's System (Q, M)</span>
              <span className="status-value">{stageInfo.aliceStatus}</span>
            </div>
            <div className="status-card">
              <span className="status-label">Bob's System (Y)</span>
              <span className="status-value">{stageInfo.bobStatus}</span>
            </div>
            <div className="status-card highlight-status">
              <span className="status-label">Global Entanglement & Fidelity</span>
              <span className="status-value">{stageInfo.entanglementStatus}</span>
            </div>
          </div>
        </div>

        {/* 3-Qubit Bloch Sphere Visualizer at Current Stage */}
        <div className="qubit-spheres-section mt-4">
          <h4 className="sub-panel-title mb-3">
            <Activity size={15} /> Physical Bloch Vectors Across the 3 Qubits at Stage {currentStage}
          </h4>

          <div className="qubit-spheres-grid">
            {/* Qubit Q (Alice) */}
            <div className="qubit-card">
              <div className="qubit-card-badge">
                <span className="badge badge-outline">Qubit Q (q0)</span>
                <span className="qubit-owner">Alice's Message</span>
              </div>
              <BlochSphere3D
                vector={getQubitBloch(0)}
                title="Qubit Q (Message)"
                size={230}
                showAngles={true}
              />
              <div className="qubit-status-note">
                {currentStage === 0 && 'Contains original state |ψ⟩'}
                {currentStage >= 1 && currentStage <= 2 && 'Undergoing entangling unitary'}
                {currentStage >= 3 && 'Measured: collapsed to classical bit'}
              </div>
            </div>

            {/* Qubit M (Bell Pair Alice) */}
            <div className="qubit-card">
              <div className="qubit-card-badge">
                <span className="badge badge-outline">Qubit M (q1)</span>
                <span className="qubit-owner">Alice's Bell Half</span>
              </div>
              <BlochSphere3D
                vector={getQubitBloch(1)}
                title="Qubit M (Alice)"
                size={230}
                showAngles={true}
              />
              <div className="qubit-status-note">
                {currentStage === 0 && 'Initial ground state |0⟩'}
                {currentStage >= 1 && currentStage <= 2 && 'Maximally entangled (ρ = I/2)'}
                {currentStage >= 3 && 'Measured: collapsed to classical bit'}
              </div>
            </div>

            {/* Qubit Y (Bob) */}
            <div className={`qubit-card ${currentStage === 6 ? 'qubit-card-winner' : ''}`}>
              <div className="qubit-card-badge">
                <span className="badge badge-primary">Qubit Y (q2)</span>
                <span className="qubit-owner">Bob's Target</span>
              </div>
              <BlochSphere3D
                vector={getQubitBloch(2)}
                targetVector={currentStage >= 5 ? blochCoords : null}
                title="Qubit Y (Bob)"
                size={230}
                showAngles={true}
              />
              <div className="qubit-status-note">
                {currentStage === 0 && 'Initial ground state |0⟩'}
                {currentStage === 1 && 'Entangled with M (Bell state)'}
                {currentStage >= 3 && currentStage <= 4 && 'Pre-correction: correlated with (c0, c1)'}
                {currentStage === 5 && 'Corrected via Pauli gates: state restored!'}
                {currentStage === 6 && 'Teleportation Complete! Fidelity = 1.000'}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
