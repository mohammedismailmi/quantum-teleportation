# Quantum Teleportation — From Alice to Bob

Formal interactive educational quantum teleportation application built with **React**, **FastAPI**, and **IBM Qiskit / Qiskit Aer**.

Designed with a formal publication-grade blue and white theme:
- Primary Navy Blue `b1`: `rgb(27, 70, 140)` (`#1B468C`)
- Deep Imperial Navy Blue `b2`: `rgb(0, 0, 93)` (`#00005D`)
- Pure Crisp White: `#FFFFFF`
- Pure academic typography with zero logos.

## Quickstart

### 1. Run the Full-Stack Application
```bash
# Start the FastAPI computational backend (serves both API & React SPA on port 8000)
.venv/bin/uvicorn server:app --host 127.0.0.1 --port 8000 --reload
```
Open **`http://localhost:8000`** in your browser.

### 2. Optional: Run Vite Frontend in Development Mode
```bash
cd frontend
npm run dev
```
Open **`http://localhost:5173`** with hot module replacement (HMR).

## The Quantum Teleportation Protocol

Quantum teleportation transfers an unknown quantum state |ψ⟩ = α|0⟩ + β|1⟩ from Alice to Bob without directly sending the qubit. The protocol uses:

1. **A shared Bell pair** |Φ⁺⟩ = (|00⟩ + |11⟩)/√2 between Alice and Bob
2. **A Bell measurement** by Alice on her two qubits
3. **Two classical bits** communicated from Alice to Bob
4. **Correction gates** applied by Bob based on Alice's measurement

### Three Qubits

| Qubit | Index | Role | Owner |
|-------|-------|------|-------|
| **Q** | 0 | Message qubit | Alice |
| **M** | 1 | Bell pair half | Alice |
| **Y** | 2 | Bell pair half | Bob |

### Correction Mapping

| Outcome (Q, M) | Bob's Conditional State | Correction |
|:---:|:---|:---:|
| 00 | α\|0⟩ + β\|1⟩ | I |
| 01 | β\|0⟩ + α\|1⟩ | X |
| 10 | α\|0⟩ − β\|1⟩ | Z |
| 11 | −β\|0⟩ + α\|1⟩ | XZ |

## Features

### 🔬 Gate-by-Gate Circuit Walkthrough
Step through all 5 unitary stages of the protocol (initialisation, Hadamard, CNOT, Bell measurement circuit) with:
- Interactive step controls (Previous / Next / Reset)
- Live circuit diagrams
- 3D Plotly Bloch spheres for every qubit
- Full statevector amplitude tables
- Reduced density matrices

### 🎯 Interactive Measurement Outcomes
Explore all four Bell measurement outcomes:
- View Bob's state before and after correction
- Compare Bloch spheres side by side
- Verify fidelity = 1 for every outcome

### 📊 Measurement Histogram
Run the full circuit on the Aer simulator with configurable shots (256–4096):
- Observed vs expected frequency comparison
- Statistical analysis and shot noise explanation

### ✅ Verification Suite
Quantitative verification across 8 test states × 4 outcomes = 32 checks:
- State fidelity F(ρ, σ) calculation
- Complex-amplitude test states included

### 🌊 Noise Experiment
Explore how depolarising noise degrades teleportation:
- Fidelity vs noise rate sweep
- Individual noisy simulation runs
- Real noise model (not hardcoded)

### 📚 Learning Section
Educational content covering:
- Bell states and entanglement
- Full mathematical derivation
- No-cloning theorem explanation
- Key quantum gates

## Installation

### Prerequisites
- Python 3.10+
- macOS (or any platform supporting Qiskit)

### Setup

```bash
# Clone the repository
git clone https://github.com/mohammedismailmi/quantum-teleportation.git
cd quantum-teleportation

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Running the Application

```bash
# Activate the virtual environment (if not already active)
source .venv/bin/activate

# Launch the Streamlit app
streamlit run app.py
```

The app opens at `http://localhost:8501` in your browser.

## Running Tests

```bash
# Run the full test suite
python -m pytest tests/test_teleportation.py -v

# Run the quantum engine verification
python quantum_teleportation.py
```

## Project Structure

```
quantum-teleportation/
├── app.py                          # Streamlit web application
├── quantum_teleportation.py        # Core quantum engine
├── visualizations.py               # Plotly visualisations
├── requirements.txt                # Python dependencies
├── requirements-lock.txt           # Pinned dependency versions
├── README.md                       # This file
├── .gitignore                      # Git ignore rules
└── tests/
    ├── __init__.py
    └── test_teleportation.py       # Automated test suite (36 tests)
```

## Screenshots

*Launch the app with `streamlit run app.py` to see the interactive interface.*

## Limitations

- The simulator runs locally using Qiskit Aer — no real quantum hardware is used by default
- The noise experiment uses a simplified depolarising model
- Circuit rendering uses matplotlib (static images) rather than interactive SVG
- Post-measurement stages (5–8) are shown in the Measurement Outcomes tab rather than as statevector snapshots, since measurement collapses the quantum state

## References & Acknowledgements

1. **Bennett et al.** (1993). "Teleporting an unknown quantum state via dual classical and Einstein-Podolsky-Rosen channels." *Physical Review Letters*, 70(13), 1895.

2. **Nielsen & Chuang** (2010). *Quantum Computation and Quantum Information*. Cambridge University Press.

3. **Qiskit Textbook** — Quantum Teleportation tutorial. The circuit structure and verification approach are adapted from the official [Qiskit learning resources](https://learning.quantum.ibm.com/tutorial/quantum-teleportation).

4. **Qiskit SDK Documentation** — [docs.quantum.ibm.com](https://docs.quantum.ibm.com/)

---

*Built for IBM Qiskit Fall Fest 2026 at RV University.*
