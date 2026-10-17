"""
FastAPI Backend for Quantum Teleportation Simulator
===================================================
Provides REST API endpoints for state computation, Qiskit Aer simulation,
noisy hardware simulation, step-by-step protocol states, and verification suites.
"""

from __future__ import annotations

import ctypes
import os
import sys

# Safeguard against glibc static TLS allocation errors with OpenMP/qiskit-aer
import glob
for _lib in glob.glob("/usr/local/lib/python*/site-packages/qiskit_aer.libs/libgomp*.so*"):
    try:
        ctypes.CDLL(_lib, mode=ctypes.RTLD_GLOBAL)
    except Exception:
        pass
try:
    ctypes.CDLL("libgomp.so.1", mode=ctypes.RTLD_GLOBAL)
except Exception:
    pass

import io
import math
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import numpy as np

from quantum_teleportation import (
    BELL_STATES,
    OUTCOME_INFO,
    PRESET_STATES,
    STAGE_DESCRIPTIONS,
    STAGE_LABELS,
    amplitudes_to_bloch,
    bloch_angles_to_amplitudes,
    compute_all_outcomes,
    compute_conditional_state,
    compute_noisy_fidelities,
    compute_stage_states,
    create_teleportation_circuit,
    dm_to_bloch,
    is_pure,
    normalize_state,
    run_noisy_simulation,
    run_simulation,
    verify_teleportation,
    run_verification_suite,
)

app = FastAPI(
    title="Quantum Teleportation Engine API",
    description="Formal computational backend for quantum teleportation protocol simulation using Qiskit.",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def serialize_complex(c: complex | float | int) -> dict[str, float]:
    c_val = complex(c)
    return {"real": float(c_val.real), "imag": float(c_val.imag)}


def format_complex_str(c: complex | float | int, precision: int = 4) -> str:
    c_val = complex(c)
    r, i = c_val.real, c_val.imag
    if abs(r) < 1e-7 and abs(i) < 1e-7:
        return "0"
    if abs(i) < 1e-7:
        return f"{r:.{precision}f}".rstrip("0").rstrip(".")
    if abs(r) < 1e-7:
        sign = "" if i >= 0 else "-"
        mag = abs(i)
        if abs(mag - 1.0) < 1e-7:
            return f"{sign}i"
        return f"{sign}{mag:.{precision}f}i".rstrip("0").rstrip(".")
    sign = "+" if i >= 0 else "-"
    mag = abs(i)
    if abs(mag - 1.0) < 1e-7:
        return f"{r:.{precision}f} {sign} i"
    return f"{r:.{precision}f} {sign} {mag:.{precision}f}i"


# ─── Pydantic Request Models ──────────────────────────────────────────────────

class StateInput(BaseModel):
    alpha_real: float = 0.6
    alpha_imag: float = 0.0
    beta_real: float = 0.8
    beta_imag: float = 0.0


class SimulationInput(BaseModel):
    alpha_real: float = 0.6
    alpha_imag: float = 0.0
    beta_real: float = 0.8
    beta_imag: float = 0.0
    shots: int = Field(default=1024, ge=1, le=65536)


class NoisySimulationInput(BaseModel):
    alpha_real: float = 0.6
    alpha_imag: float = 0.0
    beta_real: float = 0.8
    beta_imag: float = 0.0
    shots: int = Field(default=2048, ge=100, le=32768)
    noise_rates: list[float] | None = None


# ─── API Endpoints ────────────────────────────────────────────────────────────

@app.get("/api/health")
def health_check():
    return {"status": "ok", "engine": "Qiskit / Qiskit Aer", "version": "2.0.0"}


@app.get("/api/presets")
def get_presets():
    """Return available preset quantum states."""
    presets = []
    for key, (alpha, beta) in PRESET_STATES.items():
        bloch = amplitudes_to_bloch(alpha, beta)
        presets.append({
            "name": key,
            "alpha": serialize_complex(alpha),
            "beta": serialize_complex(beta),
            "alpha_str": format_complex_str(alpha),
            "beta_str": format_complex_str(beta),
            "bloch": [float(b) for b in bloch],
        })
    return {"presets": presets}


@app.post("/api/state/normalize")
def normalize_endpoint(state: StateInput):
    alpha = complex(state.alpha_real, state.alpha_imag)
    beta = complex(state.beta_real, state.beta_imag)
    norm_alpha, norm_beta = normalize_state(alpha, beta)
    bloch = amplitudes_to_bloch(norm_alpha, norm_beta)
    theta = float(2.0 * math.acos(min(1.0, max(0.0, abs(norm_alpha)))))
    phi = float(math.atan2(norm_beta.imag, norm_beta.real) - math.atan2(norm_alpha.imag, norm_alpha.real))
    if phi < 0:
        phi += 2 * math.pi

    prob0 = float(abs(norm_alpha) ** 2)
    prob1 = float(abs(norm_beta) ** 2)

    return {
        "alpha": serialize_complex(norm_alpha),
        "beta": serialize_complex(norm_beta),
        "alpha_str": format_complex_str(norm_alpha),
        "beta_str": format_complex_str(norm_beta),
        "prob0": prob0,
        "prob1": prob1,
        "bloch": [float(b) for b in bloch],
        "theta": theta,
        "phi": phi,
    }


@app.post("/api/protocol/stages")
def get_stages(state: StateInput):
    """Compute step-by-step 3-qubit statevectors and reduced density matrices."""
    alpha = complex(state.alpha_real, state.alpha_imag)
    beta = complex(state.beta_real, state.beta_imag)
    alpha, beta = normalize_state(alpha, beta)

    raw_stages = compute_stage_states(alpha, beta)
    stages = []

    for s in raw_stages:
        idx = s["stage"]
        sv = s["statevector"]
        # sv is numpy array of length 8
        sv_list = []
        for i, val in enumerate(sv):
            bin_str = format(i, "03b")  # q2, q1, q0
            prob = float(abs(val) ** 2)
            sv_list.append({
                "basis": f"|{bin_str}⟩",
                "binary": bin_str,
                "amplitude": serialize_complex(val),
                "amplitude_str": format_complex_str(val),
                "probability": prob,
            })

        bloch_by_qubit = {}
        for q in [0, 1, 2]:
            b_coords = s["bloch"][q]
            bloch_by_qubit[str(q)] = [float(c) for c in b_coords]

        density_by_qubit = {}
        for q in [0, 1, 2]:
            dm_raw = s["reduced_dm"][q]
            density_by_qubit[str(q)] = [
                [serialize_complex(dm_raw[r, c]) for c in range(2)]
                for r in range(2)
            ]

        stages.append({
            "stage": idx,
            "label": s["label"],
            "description": s["description"],
            "statevector": sv_list,
            "bloch": bloch_by_qubit,
            "purity": {str(q): bool(s["is_pure"][q]) for q in [0, 1, 2]},
            "reduced_dm": density_by_qubit,
        })

    return {"stages": stages, "alpha": serialize_complex(alpha), "beta": serialize_complex(beta)}


@app.post("/api/protocol/outcomes")
def get_outcomes(state: StateInput):
    """Compute Bob's conditional states for each of the four possible Bell measurement results."""
    alpha = complex(state.alpha_real, state.alpha_imag)
    beta = complex(state.beta_real, state.beta_imag)
    alpha, beta = normalize_state(alpha, beta)

    raw_outcomes = compute_all_outcomes(alpha, beta)
    outcomes = []

    for oc in raw_outcomes:
        bob_before = oc["bob_before_correction"]
        bob_after = oc["bob_after_correction"]

        b_before_bloch = amplitudes_to_bloch(bob_before[0], bob_before[1])
        b_after_bloch = amplitudes_to_bloch(bob_after[0], bob_after[1])

        outcomes.append({
            "q_meas": oc["q_meas"],
            "m_meas": oc["m_meas"],
            "bits_str": oc["bits_str"],
            "bell_label": oc["bell_label"],
            "bell_name": oc["bell_name"],
            "correction_label": oc["correction_label"],
            "bob_before": [serialize_complex(bob_before[0]), serialize_complex(bob_before[1])],
            "bob_before_str": f"{format_complex_str(bob_before[0])}|0⟩ + {format_complex_str(bob_before[1])}|1⟩",
            "bob_before_bloch": [float(c) for c in b_before_bloch],
            "bob_after": [serialize_complex(bob_after[0]), serialize_complex(bob_after[1])],
            "bob_after_str": f"{format_complex_str(bob_after[0])}|0⟩ + {format_complex_str(bob_after[1])}|1⟩",
            "bob_after_bloch": [float(c) for c in b_after_bloch],
            "fidelity": float(oc["fidelity"]),
            "theoretical_prob": 0.25,
        })

    return {"outcomes": outcomes}


@app.post("/api/simulation/run")
def run_teleportation_simulation(sim_input: SimulationInput):
    """Execute the full teleportation circuit on the Qiskit Aer simulator."""
    alpha = complex(sim_input.alpha_real, sim_input.alpha_imag)
    beta = complex(sim_input.beta_real, sim_input.beta_imag)
    alpha, beta = normalize_state(alpha, beta)

    res = run_simulation(alpha, beta, shots=sim_input.shots)
    counts = res["counts"]
    shots = res["shots"]

    # Qiskit outcome keys are bitstrings "c1 c0" or "c1c0"
    standard_counts = {"00": 0, "01": 1, "10": 0, "11": 0}
    for k, v in counts.items():
        clean_k = k.replace(" ", "")
        if clean_k in standard_counts:
            standard_counts[clean_k] = v

    # Theoretical probabilities (ideal teleportation distributes uniformly over the 4 Bell outcomes)
    expected_prob = 0.25
    breakdown = []
    chi_square = 0.0
    expected_count = shots * expected_prob

    for bitstring in ["00", "01", "10", "11"]:
        c = standard_counts.get(bitstring, 0)
        p = c / shots
        chi_square += ((c - expected_count) ** 2) / expected_count
        breakdown.append({
            "outcome": bitstring,
            "measured_count": c,
            "measured_probability": round(p, 4),
            "theoretical_probability": 0.25,
            "bell_state": {
                "00": "|Φ+⟩",
                "01": "|Ψ+⟩",
                "10": "|Φ-⟩",
                "11": "|Ψ-⟩"
            }[bitstring],
            "correction": {
                "00": "Identity (I)",
                "01": "Bit Flip (X)",
                "10": "Phase Flip (Z)",
                "11": "Bit & Phase (XZ)"
            }[bitstring],
        })

    # Circuit text representation
    qc = res["circuit"]
    circuit_text = str(qc.draw(output="text"))
    qasm_str = qc.qasm() if hasattr(qc, "qasm") else ""

    return {
        "shots": shots,
        "counts": standard_counts,
        "breakdown": breakdown,
        "chi_square_stat": round(chi_square, 3),
        "fidelity": 1.0,
        "circuit_text": circuit_text,
        "qasm": qasm_str,
    }


@app.post("/api/simulation/noisy")
def run_noisy_sweep(noisy_input: NoisySimulationInput):
    """Sweep noise rates using Qiskit Aer depolarizing noise model."""
    alpha = complex(noisy_input.alpha_real, noisy_input.alpha_imag)
    beta = complex(noisy_input.beta_real, noisy_input.beta_imag)
    alpha, beta = normalize_state(alpha, beta)

    rates = noisy_input.noise_rates or [0.0, 0.01, 0.02, 0.04, 0.08, 0.12, 0.16, 0.20]
    sweep_results = compute_noisy_fidelities(alpha, beta, noise_rates=rates, shots=noisy_input.shots)

    data = []
    for item in sweep_results:
        data.append({
            "noise_rate": item["noise_rate"],
            "noise_percent": round(item["noise_rate"] * 100, 1),
            "fidelity": round(item["distribution_fidelity"], 4),
            "counts": item["counts"],
        })

    return {"results": data, "shots": noisy_input.shots}


@app.get("/api/verification/suite")
def verification_suite():
    """Run full automated verification suite across benchmark states."""
    suite = run_verification_suite()
    formatted = []
    total_passed = 0

    for item in suite:
        all_passed = bool(item["all_passed"])
        if all_passed:
            total_passed += 1
        clean_details = [
            {
                "outcome": str(d["outcome"]),
                "fidelity": float(d["fidelity"]),
                "passed": bool(d["passed"]),
            }
            for d in item.get("details", [])
        ]
        formatted.append({
            "state_name": str(item["state_name"]),
            "alpha": serialize_complex(item["alpha"]),
            "beta": serialize_complex(item["beta"]),
            "all_passed": all_passed,
            "details": clean_details,
        })

    return {
        "total_tests": len(suite),
        "total_passed": total_passed,
        "passed": bool(total_passed == len(suite)),
        "tests": formatted,
    }


# ─── IBM Quantum Cloud Runtime Live Endpoints ────────────────────────────────
from qiskit import transpile
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2

def get_ibm_service() -> QiskitRuntimeService:
    try:
        return QiskitRuntimeService(name="default-cloud")
    except Exception:
        return QiskitRuntimeService(
            channel="ibm_cloud",
            token="fFfXXOtzorYMEnJ_N-OOpMVmYifj4ZmW0GxUJNN4aGCi",
            instance="crn:v1:bluemix:public:quantum-computing:us-east:a/bebe6d634e114fa49d27f6df3d902c6b:fdbe7491-2d6e-484c-9240-30be98d41891::",
        )


@app.get("/api/ibm/backends")
def list_ibm_backends():
    """Fetch live operational status and queue depth from IBM Quantum Cloud."""
    try:
        service = get_ibm_service()
        backends_data = []
        for b in service.backends():
            status = b.status()
            backends_data.append({
                "name": b.name,
                "num_qubits": b.num_qubits,
                "operational": bool(status.operational),
                "pending_jobs": int(status.pending_jobs),
                "status_msg": str(status.status_msg),
                "processor_type": "Heron r2" if "kingston" in b.name or "marrakesh" in b.name else "Eagle",
            })
        return {"status": "ok", "backends": backends_data}
    except Exception as e:
        return {"status": "error", "message": str(e), "backends": []}


@app.get("/api/ibm/jobs")
def list_ibm_jobs(limit: int = 5):
    """Retrieve user's recent quantum cloud jobs."""
    try:
        service = get_ibm_service()
        jobs_list = []
        for j in service.jobs(limit=limit):
            b_name = j.backend().name if j.backend() else "unknown"
            jobs_list.append({
                "job_id": j.job_id(),
                "status": str(j.status()),
                "backend": b_name,
                "created": str(j.creation_date),
            })
        return {"status": "ok", "jobs": jobs_list}
    except Exception as e:
        return {"status": "error", "message": str(e), "jobs": []}


class CloudJobInput(BaseModel):
    alpha_real: float = 0.6
    alpha_imag: float = 0.0
    beta_real: float = 0.8
    beta_imag: float = 0.0
    shots: int = 1024
    backend_name: str = "ibm_kingston"


@app.post("/api/ibm/submit")
def submit_cloud_job(req: CloudJobInput):
    """Transpile and submit real quantum teleportation job to IBM Quantum cloud hardware."""
    try:
        service = get_ibm_service()
        backend = service.backend(req.backend_name)
        alpha = complex(req.alpha_real, req.alpha_imag)
        beta = complex(req.beta_real, req.beta_imag)
        alpha, beta = normalize_state(alpha, beta)

        qc = create_teleportation_circuit(alpha, beta)
        isa_circuit = transpile(qc, backend=backend, optimization_level=1)

        sampler = SamplerV2(mode=backend)
        job = sampler.run([isa_circuit], shots=req.shots)

        return {
            "status": "submitted",
            "job_id": job.job_id(),
            "backend": req.backend_name,
            "cloud_status": str(job.status()),
            "shots": req.shots,
            "message": f"Job successfully queued on physical QPU {req.backend_name}. Track status in IBM dashboard or here.",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/ibm/job/{job_id}")
def check_cloud_job(job_id: str):
    """Check live status of an IBM Cloud quantum job."""
    try:
        service = get_ibm_service()
        job = service.job(job_id)
        job_status = str(job.status())
        b_name = job.backend().name if job.backend() else "unknown"

        result_data = None
        if job_status == "DONE":
            try:
                res = job.result()
                pub_result = res[0]
                counts_dict = pub_result.data.meas.get_counts() if hasattr(pub_result.data, "meas") else {}
                result_data = {"counts": counts_dict}
            except Exception:
                result_data = {"counts": {}}

        return {
            "job_id": job_id,
            "status": job_status,
            "backend": b_name,
            "created": str(job.creation_date),
            "result": result_data,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── Static Files & SPA Frontend Serving ─────────────────────────────────────
import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

frontend_dist = os.path.join(os.path.dirname(__file__), "frontend", "dist")
if os.path.exists(frontend_dist):
    assets_dir = os.path.join(frontend_dist, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}")
    def serve_frontend_spa(full_path: str):
        # Don't intercept API calls
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="API endpoint not found")
        file_path = os.path.join(frontend_dist, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        index_file = os.path.join(frontend_dist, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        return {"error": "Frontend not built"}
