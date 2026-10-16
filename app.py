"""
Quantum Teleportation — From Alice to Bob
==========================================
Interactive educational web application for IBM Qiskit Fall Fest 2026.

Launch with:
    streamlit run app.py
"""

from __future__ import annotations

import numpy as np
import streamlit as st

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
from visualizations import (
    BG_DARK,
    BG_CARD,
    CYAN,
    VIOLET,
    PINK,
    GREEN,
    AMBER,
    TEXT,
    create_bloch_sphere,
    create_density_matrix_plot,
    create_histogram,
    create_noise_fidelity_plot,
    create_statevector_bar,
    draw_circuit_png,
    draw_stage_circuit_png,
    format_complex,
    format_statevector_table,
)

# ─── Page config ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Quantum Teleportation — From Alice to Bob",
    page_icon="⚛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ───────────────────────────────────────────────────────────────

st.markdown("""
<style>
    /* ── Global ── */
    .stApp {
        background: linear-gradient(135deg, #050816 0%, #0a0e1a 30%, #0d1224 70%, #080515 100%);
        color: #e2e8f0;
    }

    /* ── Sidebar ── */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0d1224 0%, #111827 100%);
        border-right: 1px solid rgba(168,85,247,0.15);
    }
    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] .stMarkdown li,
    section[data-testid="stSidebar"] label {
        color: #cbd5e1 !important;
    }

    /* ── Headers ── */
    h1, h2, h3 {
        background: linear-gradient(90deg, #00d4ff, #a855f7, #ec4899);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 700 !important;
    }
    h4, h5, h6 {
        color: #a855f7 !important;
    }

    /* ── Cards ── */
    .quantum-card {
        background: linear-gradient(135deg, rgba(17,24,39,0.9) 0%, rgba(30,41,59,0.6) 100%);
        border: 1px solid rgba(168,85,247,0.2);
        border-radius: 16px;
        padding: 1.5rem;
        margin: 0.75rem 0;
        backdrop-filter: blur(10px);
        box-shadow: 0 4px 24px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.05);
    }
    .quantum-card:hover {
        border-color: rgba(0,212,255,0.3);
        box-shadow: 0 4px 32px rgba(168,85,247,0.15), inset 0 1px 0 rgba(255,255,255,0.08);
    }

    /* ── Info card ── */
    .info-card {
        background: linear-gradient(135deg, rgba(0,212,255,0.08) 0%, rgba(168,85,247,0.08) 100%);
        border: 1px solid rgba(0,212,255,0.2);
        border-radius: 12px;
        padding: 1.2rem;
        margin: 0.5rem 0;
    }

    /* ── Success / error ── */
    .success-card {
        background: rgba(16,185,129,0.1);
        border: 1px solid rgba(16,185,129,0.3);
        border-radius: 12px;
        padding: 1rem;
    }
    .error-card {
        background: rgba(239,68,68,0.1);
        border: 1px solid rgba(239,68,68,0.3);
        border-radius: 12px;
        padding: 1rem;
    }

    /* ── Equations ── */
    .equation-box {
        background: rgba(168,85,247,0.06);
        border: 1px solid rgba(168,85,247,0.15);
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
        margin: 0.5rem 0;
        font-size: 1.1rem;
    }

    /* ── Step indicator ── */
    .step-badge {
        display: inline-block;
        background: linear-gradient(135deg, #a855f7, #6366f1);
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.85rem;
        margin-right: 0.5rem;
    }

    /* ── Tables ── */
    .stDataFrame {
        background: rgba(17,24,39,0.8) !important;
    }

    /* ── Buttons ── */
    .stButton > button {
        background: linear-gradient(135deg, rgba(168,85,247,0.2), rgba(0,212,255,0.2)) !important;
        border: 1px solid rgba(168,85,247,0.3) !important;
        color: #e2e8f0 !important;
        border-radius: 10px !important;
        transition: all 0.3s ease !important;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, rgba(168,85,247,0.4), rgba(0,212,255,0.4)) !important;
        border-color: rgba(0,212,255,0.5) !important;
        box-shadow: 0 0 20px rgba(168,85,247,0.3) !important;
    }

    /* ── Selectbox / slider / inputs ── */
    .stSelectbox label, .stSlider label, .stNumberInput label {
        color: #cbd5e1 !important;
    }

    /* ── Metrics ── */
    [data-testid="stMetricValue"] {
        color: #00d4ff !important;
        font-weight: 700 !important;
    }
    [data-testid="stMetricLabel"] {
        color: #94a3b8 !important;
    }

    /* ── Expander ── */
    .streamlit-expanderHeader {
        background: rgba(30,41,59,0.6) !important;
        border: 1px solid rgba(168,85,247,0.15) !important;
        border-radius: 8px !important;
        color: #e2e8f0 !important;
    }

    /* ── Tab styling ── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background: rgba(30,41,59,0.4);
        border-radius: 8px 8px 0 0;
        border: 1px solid rgba(168,85,247,0.1);
        color: #94a3b8;
        padding: 8px 20px;
    }
    .stTabs [aria-selected="true"] {
        background: rgba(168,85,247,0.15) !important;
        border-color: rgba(168,85,247,0.3) !important;
        color: #e2e8f0 !important;
    }

    /* ── Divider ── */
    .gradient-divider {
        height: 2px;
        background: linear-gradient(90deg, transparent, #a855f7, #00d4ff, #a855f7, transparent);
        margin: 2rem 0;
        border: none;
    }

    /* ── Glow text ── */
    .glow-text {
        text-shadow: 0 0 10px rgba(0,212,255,0.5), 0 0 20px rgba(168,85,247,0.3);
    }

    /* ── Hide Streamlit branding ── */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# ─── Helper functions ─────────────────────────────────────────────────────────

def card(content: str, extra_class: str = ""):
    """Render content inside a styled card."""
    st.markdown(f'<div class="quantum-card {extra_class}">{content}</div>', unsafe_allow_html=True)


def divider():
    st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)


def equation(tex: str):
    """Render a LaTeX equation in a styled box."""
    st.markdown(f'<div class="equation-box">', unsafe_allow_html=True)
    st.latex(tex)
    st.markdown('</div>', unsafe_allow_html=True)


def step_badge(n: int, label: str):
    st.markdown(
        f'<span class="step-badge">Stage {n}</span> <b style="color:#e2e8f0">{label}</b>',
        unsafe_allow_html=True,
    )


# ─── Sidebar: State preparation ──────────────────────────────────────────────

with st.sidebar:
    st.markdown("## ⚛️ Quantum Teleportation")
    st.markdown("### From Alice to Bob")
    st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)

    st.markdown("#### 📡 Message State Preparation")

    input_mode = st.radio(
        "Input mode",
        ["Preset states", "Bloch sphere angles", "Custom amplitudes"],
        index=0,
        help="Choose how to specify the message qubit state",
    )

    if input_mode == "Preset states":
        preset = st.selectbox(
            "Select a state",
            list(PRESET_STATES.keys()),
            index=0,
        )
        alpha, beta = PRESET_STATES[preset]
    elif input_mode == "Bloch sphere angles":
        theta = st.slider("θ (polar angle)", 0.0, np.pi, np.pi / 4, 0.01,
                          format="%.3f")
        phi = st.slider("φ (azimuthal angle)", 0.0, 2 * np.pi, 0.0, 0.01,
                        format="%.3f")
        alpha, beta = bloch_angles_to_amplitudes(theta, phi)
    else:
        st.markdown("**α (amplitude of |0⟩):**")
        col_ar, col_ai = st.columns(2)
        with col_ar:
            alpha_r = st.number_input("Re(α)", value=1.0, step=0.1, format="%.4f")
        with col_ai:
            alpha_i = st.number_input("Im(α)", value=0.0, step=0.1, format="%.4f")

        st.markdown("**β (amplitude of |1⟩):**")
        col_br, col_bi = st.columns(2)
        with col_br:
            beta_r = st.number_input("Re(β)", value=0.0, step=0.1, format="%.4f")
        with col_bi:
            beta_i = st.number_input("Im(β)", value=0.0, step=0.1, format="%.4f")

        alpha = complex(alpha_r, alpha_i)
        beta = complex(beta_r, beta_i)

    # Normalise
    try:
        alpha, beta = normalize_state(alpha, beta)
    except ValueError:
        st.error("Both amplitudes cannot be zero!")
        st.stop()

    # Display state info
    st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)
    st.markdown("#### 📊 Current State")

    st.latex(rf"|ψ\rangle = ({format_complex(alpha)})|0\rangle + ({format_complex(beta)})|1\rangle")

    prob_0 = abs(alpha) ** 2
    prob_1 = abs(beta) ** 2
    col1, col2 = st.columns(2)
    with col1:
        st.metric("|α|²", f"{prob_0:.4f}")
    with col2:
        st.metric("|β|²", f"{prob_1:.4f}")

    bx, by, bz = amplitudes_to_bloch(alpha, beta)
    st.markdown(f"**Bloch vector:** ({bx:.3f}, {by:.3f}, {bz:.3f})")

    # Display Bloch sphere in sidebar
    fig_sidebar = create_bloch_sphere(
        (bx, by, bz), title="Message Qubit Q", pure=True,
        width=280, height=300,
    )
    st.plotly_chart(fig_sidebar, use_container_width=True)

    st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)

    st.markdown("#### ⚙️ Simulation Settings")
    shots = st.select_slider(
        "Shots", options=[256, 512, 1024, 2048, 4096], value=1024,
        help="Number of measurement repetitions",
    )

    # Reset
    if st.button("🔄 Reset All", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

    st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)
    st.markdown(
        '<p style="color:#64748b;font-size:0.8rem;text-align:center">'
        'Built with Qiskit & Streamlit<br>'
        'IBM Qiskit Fall Fest 2026 · RV University'
        '</p>',
        unsafe_allow_html=True,
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MAIN CONTENT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# ─── Landing Section ──────────────────────────────────────────────────────────

st.markdown("""
<div style="text-align:center; padding:2rem 0 1rem 0;">
    <h1 style="font-size:2.8rem; margin-bottom:0.5rem;">
        ⚛️ Quantum Teleportation
    </h1>
    <p style="font-size:1.3rem; color:#94a3b8; margin-bottom:0.5rem;">
        From Alice to Bob — An Interactive Quantum Computing Lab
    </p>
    <p style="font-size:0.95rem; color:#64748b;">
        Explore the quantum teleportation protocol step by step.
        Prepare a quantum state, watch it travel through entanglement, and verify the result.
    </p>
</div>
""", unsafe_allow_html=True)

divider()

# ─── Qubit Convention ────────────────────────────────────────────────────────

with st.expander("📐 Qubit Convention & Protocol Overview", expanded=False):
    c1, c2 = st.columns([1, 1])
    with c1:
        st.markdown("""
        **Three Qubits:**

        | Qubit | Index | Role | Owner |
        |-------|-------|------|-------|
        | **Q** | 0 | Message qubit | Alice |
        | **M** | 1 | Bell pair half | Alice |
        | **Y** | 2 | Bell pair half | Bob |

        Combined state ordering: **Q ⊗ M ⊗ Y**
        """)
    with c2:
        st.markdown("""
        **Protocol Steps:**

        1. Alice prepares message state |ψ⟩ on Q
        2. Create Bell pair |Φ⁺⟩ shared by M and Y
        3. Alice performs Bell measurement on Q and M
        4. Alice sends 2 classical bits to Bob
        5. Bob applies correction gates to Y
        6. Bob's qubit Y now holds |ψ⟩
        """)

divider()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TABS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

tab_circuit, tab_outcomes, tab_histogram, tab_verify, tab_noise, tab_learn = st.tabs([
    "🔬 Circuit Walkthrough",
    "🎯 Measurement Outcomes",
    "📊 Histogram",
    "✅ Verification",
    "🌊 Noise Experiment",
    "📚 Learn",
])


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 1: Circuit Walkthrough
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

with tab_circuit:
    st.markdown("## 🔬 Gate-by-Gate Circuit Walkthrough")
    st.markdown("Step through the teleportation protocol and watch the quantum state evolve at each stage.")

    # Compute all stages
    stages = compute_stage_states(alpha, beta)

    # Step controls
    if "current_stage" not in st.session_state:
        st.session_state.current_stage = 0

    num_stages = len(stages)  # 0-4 (unitary stages)
    max_stage = num_stages - 1

    # Control buttons
    ctrl_cols = st.columns([1, 1, 1, 1, 3])
    with ctrl_cols[0]:
        if st.button("⏮ Reset", use_container_width=True):
            st.session_state.current_stage = 0
            st.rerun()
    with ctrl_cols[1]:
        if st.button("◀ Previous", use_container_width=True):
            st.session_state.current_stage = max(0, st.session_state.current_stage - 1)
            st.rerun()
    with ctrl_cols[2]:
        if st.button("Next ▶", use_container_width=True):
            st.session_state.current_stage = min(max_stage, st.session_state.current_stage + 1)
            st.rerun()
    with ctrl_cols[3]:
        if st.button("⏭ End", use_container_width=True):
            st.session_state.current_stage = max_stage
            st.rerun()

    stage_idx = st.session_state.current_stage

    # Progress bar
    progress = (stage_idx) / max_stage if max_stage > 0 else 1.0
    st.progress(progress)
    st.markdown(
        f'<p style="text-align:center;color:#94a3b8;">'
        f'Stage {stage_idx} of {max_stage} · <b style="color:#a855f7">{STAGE_LABELS[stage_idx]}</b>'
        f'</p>',
        unsafe_allow_html=True,
    )

    # Current stage data
    s = stages[stage_idx]

    # Stage description
    st.markdown(f"""
    <div class="info-card">
        <span class="step-badge">Stage {stage_idx}</span>
        <b style="color:#e2e8f0">{s['label']}</b>
        <p style="color:#cbd5e1;margin-top:0.75rem;line-height:1.6">{s['description']}</p>
    </div>
    """, unsafe_allow_html=True)

    # Circuit diagram
    st.markdown("#### 🔌 Circuit at this Stage")
    try:
        circuit_png = draw_stage_circuit_png(alpha, beta, stage_idx)
        st.image(circuit_png, use_container_width=True)
    except Exception as e:
        st.warning(f"Circuit rendering: {e}")

    # Bloch spheres for each qubit
    st.markdown("#### 🌐 Qubit States (Bloch Spheres)")

    qubit_names = ["Q (Message)", "M (Alice)", "Y (Bob)"]
    b_cols = st.columns(3)
    for qi, col in enumerate(b_cols):
        with col:
            bvec = s["bloch"][qi]
            pure = s["is_pure"][qi]
            fig = create_bloch_sphere(
                bvec,
                title=qubit_names[qi],
                pure=pure,
                width=300,
                height=340,
            )
            st.plotly_chart(fig, use_container_width=True)

            # State info
            vec_len = np.sqrt(sum(x**2 for x in bvec))
            if not pure:
                st.markdown(f'<p style="color:{AMBER};font-size:0.85rem;">⚠ Mixed state · |r| = {vec_len:.3f}</p>', unsafe_allow_html=True)
            else:
                st.markdown(f'<p style="color:{GREEN};font-size:0.85rem;">● Pure state · |r| = {vec_len:.3f}</p>', unsafe_allow_html=True)

    # Statevector details
    st.markdown("#### 📐 Full Three-Qubit State")

    sv_table = format_statevector_table(s["statevector"])
    if sv_table:
        import pandas as pd
        df = pd.DataFrame(sv_table)
        st.dataframe(df, use_container_width=True, hide_index=True)

    # Statevector amplitude chart
    fig_sv = create_statevector_bar(s["statevector"])
    st.plotly_chart(fig_sv, use_container_width=True)

    # Reduced density matrices
    with st.expander("🔬 Reduced Density Matrices"):
        dm_cols = st.columns(3)
        for qi, col in enumerate(dm_cols):
            with col:
                rdm = s["reduced_dm"][qi]
                fig_dm = create_density_matrix_plot(rdm, title=f"ρ_{qubit_names[qi]}")
                st.plotly_chart(fig_dm, use_container_width=True)

    # Post-measurement stages (5-8) - shown after stage 4
    if stage_idx == max_stage:
        divider()
        st.markdown("### 📡 Post-Measurement: Alice Measures Q and M")
        st.markdown("""
        After Stage 4, Alice measures her two qubits Q and M.
        The measurement outcome determines Bob's conditional state.

        **See the "Measurement Outcomes" tab** for the full analysis of each
        of the four possible results and Bob's correction procedure.
        """)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 2: Measurement Outcomes
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

with tab_outcomes:
    st.markdown("## 🎯 Interactive Measurement Outcomes")
    st.markdown("""
    Alice measures her two qubits Q and M, obtaining one of four equally-probable outcomes.
    Each outcome leaves Bob's qubit in a specific conditional state.
    After classical communication, Bob applies correction gates to recover the original state.
    """)

    st.info("💡 The measurement outcome is **probabilistic** — Alice cannot choose an outcome to force successful teleportation.")

    # Compute all outcomes
    all_outcomes = compute_all_outcomes(alpha, beta)

    # Let user pick an outcome or view all
    outcome_mode = st.radio(
        "View mode",
        ["All four outcomes", "Select specific outcome", "Random sample"],
        horizontal=True,
    )

    if outcome_mode == "Random sample":
        if st.button("🎲 Sample a random outcome"):
            st.session_state.sampled_outcome = np.random.randint(0, 4)
        idx = st.session_state.get("sampled_outcome", 0)
        selected_outcomes = [all_outcomes[idx]]
    elif outcome_mode == "Select specific outcome":
        sel = st.selectbox(
            "Select outcome",
            ["00 (Q=0, M=0)", "01 (Q=0, M=1)", "10 (Q=1, M=0)", "11 (Q=1, M=1)"],
        )
        idx = ["00", "01", "10", "11"].index(sel[:2])
        selected_outcomes = [all_outcomes[idx]]
    else:
        selected_outcomes = all_outcomes

    for oc in selected_outcomes:
        st.markdown(f"""
        <div class="quantum-card">
            <span class="step-badge">{oc['bits_str']}</span>
            <b style="color:#e2e8f0;">Outcome: Q={oc['q_meas']}, M={oc['m_meas']}</b>
            <span style="color:#94a3b8;margin-left:1rem;">Bell state: {oc['bell_label']}</span>
            <span style="color:#94a3b8;margin-left:1rem;">Prob: {oc['probability']:.4f}</span>
        </div>
        """, unsafe_allow_html=True)

        col_before, col_arrow, col_after = st.columns([2, 1, 2])

        with col_before:
            st.markdown("##### Bob's state BEFORE correction")
            st.latex(
                rf"|Y\rangle = {format_complex(oc['bob_before'][0])}|0\rangle + "
                rf"{format_complex(oc['bob_before'][1])}|1\rangle"
            )
            bvec_before = amplitudes_to_bloch(oc["bob_before"][0], oc["bob_before"][1])
            fig_before = create_bloch_sphere(bvec_before, "Before Correction", True, 260, 290)
            st.plotly_chart(fig_before, use_container_width=True)

        with col_arrow:
            st.markdown("")
            st.markdown("")
            st.markdown("")
            st.markdown(f"""
            <div style="text-align:center;padding-top:3rem;">
                <p style="color:#a855f7;font-size:1.5rem;">→</p>
                <p style="color:#e2e8f0;font-weight:600;">Apply</p>
                <p style="color:#00d4ff;font-size:1.2rem;font-weight:700;">{oc['correction']}</p>
            </div>
            """, unsafe_allow_html=True)

        with col_after:
            st.markdown("##### Bob's state AFTER correction")
            st.latex(
                rf"|Y\rangle = {format_complex(oc['bob_after'][0])}|0\rangle + "
                rf"{format_complex(oc['bob_after'][1])}|1\rangle"
            )
            bvec_after = amplitudes_to_bloch(oc["bob_after"][0], oc["bob_after"][1])
            fig_after = create_bloch_sphere(bvec_after, "After Correction", True, 260, 290)
            st.plotly_chart(fig_after, use_container_width=True)

        # Fidelity
        fid_color = GREEN if np.isclose(oc["fidelity"], 1.0, atol=1e-6) else AMBER
        st.markdown(f"""
        <div class="{'success-card' if np.isclose(oc['fidelity'], 1.0, atol=1e-6) else 'error-card'}">
            <b style="color:{fid_color};">
                {'✓ Perfect teleportation!' if np.isclose(oc['fidelity'], 1.0, atol=1e-6) else '⚠ Imperfect fidelity'}
            </b>
            <span style="color:#e2e8f0;margin-left:1rem;">
                Fidelity: F = {oc['fidelity']:.8f}
            </span>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("")  # Spacing

    # Correction summary table
    st.markdown("### 📋 Correction Gate Summary")
    st.markdown("""
    | Outcome (QM) | c₀ (Q) | c₁ (M) | Bell State | Correction | Bob's pre-correction state |
    |:---:|:---:|:---:|:---:|:---:|:---|
    | 00 | 0 | 0 | \|Φ⁺⟩ | I | α\|0⟩ + β\|1⟩ |
    | 01 | 0 | 1 | \|Ψ⁺⟩ | X | β\|0⟩ + α\|1⟩ |
    | 10 | 1 | 0 | \|Φ⁻⟩ | Z | α\|0⟩ − β\|1⟩ |
    | 11 | 1 | 1 | \|Ψ⁻⟩ | XZ | −β\|0⟩ + α\|1⟩ |
    """)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 3: Histogram
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

with tab_histogram:
    st.markdown("## 📊 Measurement Histogram")
    st.markdown(f"""
    Run the complete teleportation circuit on the Qiskit Aer simulator with **{shots} shots**
    and observe the distribution of Alice's measurement outcomes.
    """)

    if st.button("🚀 Run Simulation", use_container_width=True, key="run_sim"):
        with st.spinner("Running quantum simulation..."):
            sim_result = run_simulation(alpha, beta, shots=shots)
        st.session_state.sim_result = sim_result

    if "sim_result" in st.session_state:
        sim = st.session_state.sim_result
        counts = sim["counts"]

        # Histogram
        fig_hist = create_histogram(counts, sim["shots"])
        st.plotly_chart(fig_hist, use_container_width=True)

        # Detailed results
        st.markdown("### 📈 Detailed Results")

        total = sum(counts.values())
        expected = total / 4

        import pandas as pd
        rows = []
        for outcome in sorted(counts.keys()):
            count = counts[outcome]
            freq = count / total
            diff = freq - 0.25
            rows.append({
                "Outcome": outcome,
                "Count": count,
                "Frequency": f"{freq:.4f}",
                "Expected": f"{0.25:.4f}",
                "Deviation": f"{diff:+.4f}",
            })

        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)

        st.markdown(f"""
        <div class="info-card">
            <b style="color:#00d4ff;">Why do frequencies fluctuate?</b>
            <p style="color:#cbd5e1;margin-top:0.5rem;">
                With {shots} shots, each outcome has an expected probability of ¼ = 0.25.
                The observed frequencies deviate from this due to <b>shot noise</b> — the
                statistical fluctuation inherent in a finite number of measurements.
                Increasing the shot count reduces these fluctuations.
            </p>
        </div>
        """, unsafe_allow_html=True)

        # Full circuit
        with st.expander("🔌 Full Teleportation Circuit"):
            try:
                full_png = draw_circuit_png(sim["circuit"])
                st.image(full_png, use_container_width=True)
            except Exception as e:
                st.code(sim["circuit"].draw(output="text"))
    else:
        st.info("👆 Click 'Run Simulation' to execute the circuit and see results.")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 4: Verification
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

with tab_verify:
    st.markdown("## ✅ Teleportation Verification")
    st.markdown("""
    Verify that quantum teleportation produces the correct output state for every
    measurement outcome and across multiple test states.
    """)

    st.markdown("#### State Fidelity")
    st.latex(r"F(\rho, \sigma) = \left(\text{Tr}\sqrt{\sqrt{\rho}\,\sigma\,\sqrt{\rho}}\right)^2")
    st.markdown("For pure states, this reduces to the squared overlap: F = |⟨ψ|φ⟩|²")

    # Verify current state
    st.markdown("### 🔍 Current State Verification")

    v = verify_teleportation(alpha, beta)

    col_orig, col_result = st.columns(2)
    with col_orig:
        st.markdown("**Original state:**")
        st.latex(rf"|ψ\rangle = {format_complex(alpha)}|0\rangle + {format_complex(beta)}|1\rangle")
        fig_orig = create_bloch_sphere(
            amplitudes_to_bloch(alpha, beta),
            "Original |ψ⟩", True, 280, 320,
        )
        st.plotly_chart(fig_orig, use_container_width=True)

    with col_result:
        st.markdown("**Reconstructed state (outcome 00):**")
        oc00 = compute_conditional_state(alpha, beta, 0, 0)
        st.latex(
            rf"|ψ'\rangle = {format_complex(oc00['bob_after'][0])}|0\rangle + "
            rf"{format_complex(oc00['bob_after'][1])}|1\rangle"
        )
        fig_recon = create_bloch_sphere(
            amplitudes_to_bloch(oc00["bob_after"][0], oc00["bob_after"][1]),
            "Reconstructed |ψ'⟩", True, 280, 320,
        )
        st.plotly_chart(fig_recon, use_container_width=True)

    # Outcome-by-outcome table
    import pandas as pd
    v_rows = []
    for d in v["details"]:
        v_rows.append({
            "Outcome": d["outcome"],
            "Fidelity": f"{d['fidelity']:.8f}",
            "Status": "✓ Pass" if d["passed"] else "✗ Fail",
        })
    df_v = pd.DataFrame(v_rows)
    st.dataframe(df_v, use_container_width=True, hide_index=True)

    overall_status = "success-card" if v["all_passed"] else "error-card"
    overall_text = "✓ All outcomes produce perfect fidelity!" if v["all_passed"] else "✗ Some outcomes have imperfect fidelity"
    overall_color = GREEN if v["all_passed"] else "#ef4444"
    st.markdown(f"""
    <div class="{overall_status}">
        <b style="color:{overall_color};font-size:1.1rem;">{overall_text}</b>
        <p style="color:#cbd5e1;margin-top:0.3rem;">Tolerance: 1×10⁻⁶</p>
    </div>
    """, unsafe_allow_html=True)

    # Full verification suite
    divider()
    st.markdown("### 🧪 Full Verification Suite")
    st.markdown("Test teleportation across 8 diverse quantum states, including complex amplitudes.")

    if st.button("🔬 Run Full Suite", use_container_width=True):
        with st.spinner("Running verification across 8 test states..."):
            suite = run_verification_suite()
        st.session_state.suite = suite

    if "suite" in st.session_state:
        suite = st.session_state.suite
        all_pass = all(s["all_passed"] for s in suite)

        suite_rows = []
        for s in suite:
            for d in s["details"]:
                suite_rows.append({
                    "State": s["state_name"],
                    "Outcome": d["outcome"],
                    "Fidelity": f"{d['fidelity']:.8f}",
                    "Status": "✓" if d["passed"] else "✗",
                })

        df_suite = pd.DataFrame(suite_rows)
        st.dataframe(df_suite, use_container_width=True, hide_index=True)

        if all_pass:
            st.markdown(f"""
            <div class="success-card">
                <b style="color:{GREEN};font-size:1.2rem;">
                    ✓ ALL 32 TESTS PASSED
                </b>
                <p style="color:#cbd5e1;">
                    All 8 states × 4 outcomes = 32 verification checks completed successfully.
                </p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.error("Some tests failed. Check the table above.")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 5: Noise Experiment
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

with tab_noise:
    st.markdown("## 🌊 Noise Experiment")
    st.markdown("""
    Explore how noise degrades quantum teleportation fidelity.
    A **depolarising noise channel** is applied to all quantum gates, simulating realistic hardware imperfections.
    """)

    st.markdown("""
    <div class="info-card">
        <b style="color:#00d4ff;">What is depolarising noise?</b>
        <p style="color:#cbd5e1;margin-top:0.5rem;">
            A depolarising channel replaces a qubit's state with the maximally mixed state (I/2) with
            probability p, and leaves it unchanged with probability 1−p. For two-qubit gates, the
            channel acts on the joint two-qubit state. This models the dominant error mechanism in
            many quantum computing platforms.
        </p>
    </div>
    """, unsafe_allow_html=True)

    col_n1, col_n2 = st.columns(2)
    with col_n1:
        noise_shots = st.select_slider(
            "Shots per noise level",
            options=[1024, 2048, 4096],
            value=2048,
            key="noise_shots",
        )
    with col_n2:
        single_rate = st.slider(
            "Single noise rate (for individual run)",
            0.0, 0.3, 0.05, 0.005,
            key="single_noise_rate",
        )

    col_b1, col_b2 = st.columns(2)

    with col_b1:
        if st.button("🔬 Run Noise Sweep", use_container_width=True):
            with st.spinner("Running noise sweep (8 noise levels)..."):
                noise_results = compute_noisy_fidelities(alpha, beta, shots=noise_shots)
            st.session_state.noise_results = noise_results

    with col_b2:
        if st.button("📊 Run Single Noisy Simulation", use_container_width=True):
            with st.spinner(f"Running noisy simulation (p={single_rate:.3f})..."):
                noisy_sim = run_noisy_simulation(alpha, beta, shots=noise_shots,
                                                  depolarizing_rate=single_rate)
            st.session_state.noisy_sim = noisy_sim

    if "noise_results" in st.session_state:
        st.markdown("### 📉 Fidelity vs Noise Rate")
        fig_noise = create_noise_fidelity_plot(st.session_state.noise_results)
        st.plotly_chart(fig_noise, use_container_width=True)

        import pandas as pd
        noise_rows = [{
            "Noise Rate": f"{r['noise_rate']:.3f}",
            "Distribution Fidelity": f"{r['distribution_fidelity']:.4f}",
        } for r in st.session_state.noise_results]
        st.dataframe(pd.DataFrame(noise_rows), use_container_width=True, hide_index=True)

    if "noisy_sim" in st.session_state:
        ns = st.session_state.noisy_sim
        st.markdown(f"### 📊 Noisy Histogram (p = {ns['noise_rate']:.3f})")
        fig_noisy = create_histogram(ns["counts"], ns["shots"],
                                      title=f"Noisy Measurement (p={ns['noise_rate']:.3f})")
        st.plotly_chart(fig_noisy, use_container_width=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 6: Learn
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

with tab_learn:
    st.markdown("## 📚 Quantum Teleportation Theory")

    # Bell States
    st.markdown("### 🔔 The Four Bell States")
    st.markdown("""
    Bell states are maximally entangled two-qubit states that form the foundation
    of quantum teleportation.  They are created by applying a Hadamard gate followed
    by a CNOT gate.
    """)

    bell_cols = st.columns(4)
    bell_info = [
        ("|Φ⁺⟩", r"|\Phi^+\rangle = \frac{|00\rangle + |11\rangle}{\sqrt{2}}"),
        ("|Φ⁻⟩", r"|\Phi^-\rangle = \frac{|00\rangle - |11\rangle}{\sqrt{2}}"),
        ("|Ψ⁺⟩", r"|\Psi^+\rangle = \frac{|01\rangle + |10\rangle}{\sqrt{2}}"),
        ("|Ψ⁻⟩", r"|\Psi^-\rangle = \frac{|01\rangle - |10\rangle}{\sqrt{2}}"),
    ]

    for col, (name, tex) in zip(bell_cols, bell_info):
        with col:
            st.markdown(f"**{name}**")
            st.latex(tex)

    st.markdown("""
    The teleportation protocol uses **|Φ⁺⟩** as the default entangled resource
    shared between Alice and Bob.

    **Entanglement means** the two qubits are in a correlated state where measuring
    one instantly determines the other, regardless of distance. However, each
    individual qubit appears to be in the maximally mixed state ρ = I/2.
    The correlations exist only in the *joint* measurement statistics, not
    in either qubit alone.
    """)

    divider()

    # Mathematical derivation
    st.markdown("### 📐 Mathematical Derivation")

    st.markdown("**Step 1: Initial State**")
    st.latex(r"|\Psi_0\rangle = |\psi\rangle_Q \otimes |\Phi^+\rangle_{MY}")
    st.latex(r"= (\alpha|0\rangle + \beta|1\rangle) \otimes \frac{|00\rangle + |11\rangle}{\sqrt{2}}")

    st.markdown("**Step 2: Expand the tensor product**")
    st.latex(r"= \frac{1}{\sqrt{2}} \big[\alpha|000\rangle + \alpha|011\rangle + \beta|100\rangle + \beta|111\rangle\big]")

    st.markdown("**Step 3: Apply CNOT(Q→M) and H(Q)**")
    st.markdown("After the Bell measurement circuit, the state becomes:")
    st.latex(r"""
    |\Psi_4\rangle = \frac{1}{2}\big[
        |00\rangle_{QM}(\alpha|0\rangle + \beta|1\rangle)_Y
        + |01\rangle_{QM}(\beta|0\rangle + \alpha|1\rangle)_Y
        + |10\rangle_{QM}(\alpha|0\rangle - \beta|1\rangle)_Y
        + |11\rangle_{QM}(-\beta|0\rangle + \alpha|1\rangle)_Y
    \big]
    """)

    st.markdown("**Step 4: Measurement collapses the state**")
    st.markdown("""
    Each outcome has probability ¼. Bob applies the appropriate correction
    (I, X, Z, or XZ) to recover |ψ⟩.
    """)

    divider()

    # No-Cloning Theorem
    st.markdown("### 🚫 No-Cloning Theorem")

    st.markdown("""
    <div class="quantum-card">
        <h4 style="color:#ec4899 !important;">Why doesn't teleportation violate the No-Cloning Theorem?</h4>
        <p style="color:#cbd5e1;line-height:1.7;">
            The <b>no-cloning theorem</b> states that an arbitrary unknown quantum state cannot be
            perfectly copied. Quantum teleportation does <b>not</b> violate this theorem because:
        </p>
        <ol style="color:#cbd5e1;line-height:2;">
            <li><b>Alice's Bell measurement destroys the original state.</b>
                The measurement is irreversible — after measuring Q and M, Alice's message
                qubit no longer holds the state |ψ⟩.</li>
            <li><b>Bob reconstructs the state, he doesn't copy it.</b>
                The state is transferred (teleported), not duplicated. At no point do two
                perfect copies of |ψ⟩ coexist.</li>
            <li><b>Classical communication is required.</b>
                Bob cannot recover |ψ⟩ without Alice's two classical bits. The entanglement
                alone is not sufficient.</li>
            <li><b>The two classical bits do not encode the state.</b>
                The bits only specify which of four correction operations to apply.
                They do not reveal α or β. An eavesdropper who intercepts only the
                classical channel learns nothing about the original state.</li>
            <li><b>No matter or particles are transmitted.</b>
                Quantum teleportation transfers quantum information, not physical particles.
                It does not enable faster-than-light communication.</li>
        </ol>
    </div>
    """, unsafe_allow_html=True)

    divider()

    # Key quantum gates
    st.markdown("### 🔧 Key Quantum Gates")

    gate_cols = st.columns(3)
    with gate_cols[0]:
        st.markdown("**Hadamard (H)**")
        st.latex(r"H = \frac{1}{\sqrt{2}}\begin{pmatrix} 1 & 1 \\ 1 & -1 \end{pmatrix}")
        st.markdown("Creates equal superposition.")

    with gate_cols[1]:
        st.markdown("**CNOT (CX)**")
        st.latex(r"CX = \begin{pmatrix} 1&0&0&0 \\ 0&1&0&0 \\ 0&0&0&1 \\ 0&0&1&0 \end{pmatrix}")
        st.markdown("Flips target if control = |1⟩.")

    with gate_cols[2]:
        st.markdown("**Pauli X and Z**")
        st.latex(r"X = \begin{pmatrix} 0 & 1 \\ 1 & 0 \end{pmatrix}, \quad Z = \begin{pmatrix} 1 & 0 \\ 0 & -1 \end{pmatrix}")
        st.markdown("Bit-flip and phase-flip corrections.")

    divider()

    # References
    st.markdown("### 📖 References & Acknowledgements")
    st.markdown("""
    1. **Bennett et al.** (1993). "Teleporting an unknown quantum state via dual classical and
       Einstein-Podolsky-Rosen channels." *Physical Review Letters*, 70(13), 1895.

    2. **Nielsen & Chuang** (2010). *Quantum Computation and Quantum Information*.
       Cambridge University Press.

    3. **Qiskit Textbook** — Quantum Teleportation.
       [learning.quantum.ibm.com](https://learning.quantum.ibm.com/tutorial/quantum-teleportation)

    4. **Qiskit SDK Documentation**.
       [docs.quantum.ibm.com](https://docs.quantum.ibm.com/)

    ---

    *This project was built for the IBM Qiskit Fall Fest 2026 at RV University.*
    *Circuit construction and verification adapted from the official Qiskit teleportation tutorial.*
    """)
