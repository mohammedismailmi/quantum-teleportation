import React from 'react';
import {
  Compass,
  Layers,
  GitBranch,
  Cpu,
  Activity,
  Network,
  ShieldCheck,
  BookOpen,
  Cloud,
} from 'lucide-react';

export default function Header({
  activeTab,
  setActiveTab,
  engineStatus = 'online',
}) {
  const tabs = [
    { id: 'prep', label: '1. State Preparation', icon: Compass },
    { id: 'protocol', label: '2. Protocol Walkthrough', icon: Layers },
    { id: 'outcomes', label: '3. Measurement Branches', icon: GitBranch },
    { id: 'simulation', label: '4. Aer Simulator', icon: Cpu },
    { id: 'noise', label: '5. Noise Analysis', icon: Activity },
    { id: 'circuit', label: '6. Circuit & Code', icon: Network },
    { id: 'verification', label: '7. Verification Suite', icon: ShieldCheck },
    { id: 'theory', label: '8. Theory & Proofs', icon: BookOpen },
    { id: 'cloud', label: '9. IBM Cloud QPUs', icon: Cloud },
  ];

  return (
    <header className="formal-header">
      {/* Top Banner */}
      <div className="header-top-bar">
        <div className="header-brand-group">
          {/* Strict rule: NO LOGO */}
          <div className="formal-title-container">
            <h1 className="formal-main-title">QUANTUM TELEPORTATION SIMULATOR</h1>
            <span className="formal-sub-title">
              From Alice to Bob • Interactive Quantum Simulator & Verification Engine
            </span>
          </div>
        </div>

        <div className="header-meta-group">
          <div className="engine-status-badge">
            <span className={`status-indicator ${engineStatus === 'online' ? 'online' : 'connecting'}`} />
            <span>Qiskit Aer 1.x Backend: {engineStatus === 'online' ? 'Connected' : 'Local Engine'}</span>
          </div>
          <div className="protocol-fidelity-tag">
            <span>Universal Target Fidelity:</span>
            <strong>1.0000 (100%)</strong>
          </div>
        </div>
      </div>

      {/* Main Navigation Bar */}
      <nav className="header-nav">
        <div className="nav-tabs-scroll">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                className={`nav-tab-item ${isActive ? 'active' : ''}`}
                onClick={() => setActiveTab(tab.id)}
              >
                <Icon size={14} className="nav-icon" />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>
      </nav>
    </header>
  );
}
