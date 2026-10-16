"""
Quantum Teleportation — Visualisation Module
=============================================
Plotly-based Bloch spheres, measurement histograms, statevector displays,
circuit diagrams, and noise-fidelity plots.

All plots use a premium dark quantum-computing aesthetic.
"""

from __future__ import annotations

import io
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from quantum_teleportation import dm_to_bloch, is_pure


# ─── Colour palette ──────────────────────────────────────────────────────────

BG_DARK = "#0a0e1a"
BG_CARD = "#111827"
CYAN = "#00d4ff"
VIOLET = "#a855f7"
PINK = "#ec4899"
GREEN = "#10b981"
AMBER = "#f59e0b"
TEXT = "#e2e8f0"
GRID = "rgba(148,163,184,0.08)"
SURFACE_ALPHA = 0.06


# ─── Bloch sphere ────────────────────────────────────────────────────────────

def _sphere_mesh(n: int = 30):
    """Generate wireframe sphere coordinates."""
    u = np.linspace(0, 2 * np.pi, n)
    v = np.linspace(0, np.pi, n)
    x = np.outer(np.cos(u), np.sin(v))
    y = np.outer(np.sin(u), np.sin(v))
    z = np.outer(np.ones_like(u), np.cos(v))
    return x, y, z


def create_bloch_sphere(
    bloch_vec: tuple[float, float, float],
    title: str = "Bloch Sphere",
    pure: bool = True,
    width: int = 350,
    height: int = 380,
    show_title: bool = True,
) -> go.Figure:
    """
    Create a 3D Plotly Bloch-sphere figure.

    Parameters
    ----------
    bloch_vec : (x, y, z)
        Bloch vector components.
    title : str
        Display title.
    pure : bool
        Whether the state is pure (vector reaches the surface).
    """
    bx, by, bz = bloch_vec
    vec_len = np.sqrt(bx**2 + by**2 + bz**2)

    fig = go.Figure()

    # Wireframe sphere
    for angle in np.linspace(0, np.pi, 7):
        theta = np.linspace(0, 2 * np.pi, 60)
        fig.add_trace(go.Scatter3d(
            x=np.sin(angle) * np.cos(theta),
            y=np.sin(angle) * np.sin(theta),
            z=np.full_like(theta, np.cos(angle)),
            mode="lines",
            line=dict(color="rgba(148,163,184,0.15)", width=1),
            showlegend=False, hoverinfo="skip",
        ))
    for angle in np.linspace(0, 2 * np.pi, 13):
        phi = np.linspace(0, np.pi, 40)
        fig.add_trace(go.Scatter3d(
            x=np.sin(phi) * np.cos(angle),
            y=np.sin(phi) * np.sin(angle),
            z=np.cos(phi),
            mode="lines",
            line=dict(color="rgba(148,163,184,0.1)", width=1),
            showlegend=False, hoverinfo="skip",
        ))

    # Axes
    axis_len = 1.15
    for ax_vec, label, color in [
        ((axis_len, 0, 0), "X", CYAN),
        ((0, axis_len, 0), "Y", VIOLET),
        ((0, 0, axis_len), "Z", GREEN),
    ]:
        fig.add_trace(go.Scatter3d(
            x=[0, ax_vec[0]], y=[0, ax_vec[1]], z=[0, ax_vec[2]],
            mode="lines+text",
            line=dict(color=color, width=2),
            text=["", label],
            textfont=dict(color=color, size=12),
            textposition="top center",
            showlegend=False, hoverinfo="skip",
        ))
        fig.add_trace(go.Scatter3d(
            x=[0, -ax_vec[0]], y=[0, -ax_vec[1]], z=[0, -ax_vec[2]],
            mode="lines",
            line=dict(color=color, width=1, dash="dot"),
            showlegend=False, hoverinfo="skip",
        ))

    # Basis labels
    for pos, label in [
        ((0, 0, 1.25), "|0⟩"), ((0, 0, -1.25), "|1⟩"),
        ((1.25, 0, 0), "|+⟩"), ((-1.25, 0, 0), "|−⟩"),
        ((0, 1.25, 0), "|i+⟩"), ((0, -1.25, 0), "|i−⟩"),
    ]:
        fig.add_trace(go.Scatter3d(
            x=[pos[0]], y=[pos[1]], z=[pos[2]],
            mode="text",
            text=[label],
            textfont=dict(color=TEXT, size=10),
            showlegend=False, hoverinfo="skip",
        ))

    # State vector arrow
    vec_color = CYAN if pure else AMBER
    if vec_len > 0.01:
        fig.add_trace(go.Scatter3d(
            x=[0, bx], y=[0, by], z=[0, bz],
            mode="lines",
            line=dict(color=vec_color, width=5),
            showlegend=False,
            hoverinfo="text",
            hovertext=f"({bx:.3f}, {by:.3f}, {bz:.3f})",
        ))
        # Arrow head as a cone
        fig.add_trace(go.Cone(
            x=[bx], y=[by], z=[bz],
            u=[bx * 0.15], v=[by * 0.15], w=[bz * 0.15],
            colorscale=[[0, vec_color], [1, vec_color]],
            showscale=False,
            sizemode="absolute",
            sizeref=0.12,
            hoverinfo="skip",
        ))
    else:
        # Mixed state at origin
        fig.add_trace(go.Scatter3d(
            x=[0], y=[0], z=[0],
            mode="markers",
            marker=dict(color=AMBER, size=8, symbol="circle"),
            showlegend=False,
            hoverinfo="text",
            hovertext="Maximally mixed (origin)",
        ))

    # State info annotation
    state_info = f"|r| = {vec_len:.3f}"
    if vec_len < 0.01:
        state_info += "  (maximally mixed)"
    elif not pure:
        state_info += "  (mixed)"

    camera = dict(eye=dict(x=1.5, y=1.5, z=1.0))

    fig.update_layout(
        scene=dict(
            xaxis=dict(visible=False, range=[-1.4, 1.4]),
            yaxis=dict(visible=False, range=[-1.4, 1.4]),
            zaxis=dict(visible=False, range=[-1.4, 1.4]),
            aspectmode="cube",
            bgcolor=BG_DARK,
            camera=camera,
        ),
        paper_bgcolor=BG_DARK,
        plot_bgcolor=BG_DARK,
        margin=dict(l=0, r=0, t=35 if show_title else 5, b=25),
        width=width,
        height=height,
        title=dict(
            text=f"<b>{title}</b><br><span style='font-size:11px;color:{TEXT}'>{state_info}</span>" if show_title else "",
            font=dict(color=TEXT, size=14),
            x=0.5,
        ),
    )

    return fig


def create_bloch_comparison(
    bloch_vecs: list[tuple[tuple[float, float, float], str, bool]],
    overall_title: str = "",
) -> list[go.Figure]:
    """Create a list of Bloch-sphere figures for side-by-side display."""
    figs = []
    for vec, label, pure in bloch_vecs:
        fig = create_bloch_sphere(vec, title=label, pure=pure, width=280, height=320)
        figs.append(fig)
    return figs


# ─── Measurement histogram ───────────────────────────────────────────────────

def create_histogram(
    counts: dict[str, int],
    shots: int,
    title: str = "Measurement Results",
) -> go.Figure:
    """Create a measurement histogram with expected vs observed comparison."""
    # Sort outcomes
    outcomes = sorted(counts.keys())
    observed = [counts.get(k, 0) for k in outcomes]
    probs = [c / shots for c in observed]
    expected_prob = 0.25  # Each Bell outcome has p = 1/4

    colors = [CYAN, VIOLET, PINK, GREEN]

    fig = go.Figure()

    # Expected bars (background)
    fig.add_trace(go.Bar(
        x=outcomes,
        y=[expected_prob] * len(outcomes),
        name="Expected (1/4)",
        marker_color="rgba(148,163,184,0.15)",
        marker_line=dict(color="rgba(148,163,184,0.3)", width=1),
        width=0.5,
    ))

    # Observed bars
    fig.add_trace(go.Bar(
        x=outcomes,
        y=probs,
        name="Observed",
        marker_color=colors[:len(outcomes)],
        marker_line=dict(color="rgba(255,255,255,0.2)", width=1),
        text=[f"{p:.3f}<br>({c})" for p, c in zip(probs, observed)],
        textposition="outside",
        textfont=dict(color=TEXT, size=11),
        width=0.35,
    ))

    fig.update_layout(
        title=dict(text=f"<b>{title}</b>", font=dict(color=TEXT, size=16), x=0.5),
        xaxis=dict(
            title="Measurement Outcome (c₁c₀)",
            titlefont=dict(color=TEXT),
            tickfont=dict(color=TEXT, size=13),
            gridcolor=GRID,
        ),
        yaxis=dict(
            title="Probability",
            titlefont=dict(color=TEXT),
            tickfont=dict(color=TEXT),
            gridcolor=GRID,
            range=[0, max(probs + [expected_prob]) * 1.25],
        ),
        barmode="overlay",
        paper_bgcolor=BG_DARK,
        plot_bgcolor=BG_DARK,
        legend=dict(font=dict(color=TEXT), bgcolor="rgba(0,0,0,0.3)"),
        margin=dict(l=60, r=20, t=50, b=60),
        height=400,
    )

    return fig


# ─── Statevector display ─────────────────────────────────────────────────────

def format_complex(z: complex, precision: int = 4) -> str:
    """Format a complex number nicely."""
    r = np.real(z)
    i = np.imag(z)
    if abs(i) < 10**(-precision):
        return f"{r:.{precision}f}"
    if abs(r) < 10**(-precision):
        if abs(i - 1) < 10**(-precision):
            return "i"
        if abs(i + 1) < 10**(-precision):
            return "−i"
        return f"{i:.{precision}f}i"
    sign = "+" if i >= 0 else "−"
    return f"{r:.{precision}f} {sign} {abs(i):.{precision}f}i"


def format_statevector_table(sv: np.ndarray, n_qubits: int = 3) -> list[dict]:
    """
    Create a table of statevector amplitudes.

    Returns list of dicts with keys:
        basis, amplitude, probability, phase_deg
    """
    rows = []
    for idx in range(len(sv)):
        amp = sv[idx]
        prob = abs(amp) ** 2
        if prob < 1e-10:
            continue
        # Qiskit little-endian: bit string is reversed
        bits = format(idx, f"0{n_qubits}b")[::-1]  # Q M Y order
        phase = np.angle(amp, deg=True)
        rows.append({
            "basis": f"|{bits[0]}{bits[1]}{bits[2]}⟩",
            "qmy_label": f"Q={bits[0]} M={bits[1]} Y={bits[2]}",
            "amplitude": format_complex(amp),
            "probability": f"{prob:.6f}",
            "phase_deg": f"{phase:.1f}°",
        })
    return rows


def create_statevector_bar(sv: np.ndarray, n_qubits: int = 3) -> go.Figure:
    """Create a bar chart of statevector amplitudes (real and imaginary)."""
    n = len(sv)
    labels = []
    for idx in range(n):
        bits = format(idx, f"0{n_qubits}b")[::-1]
        labels.append(f"|{bits}⟩")

    real_parts = np.real(sv)
    imag_parts = np.imag(sv)

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=labels, y=real_parts,
        name="Real",
        marker_color=CYAN,
        marker_line=dict(color="rgba(255,255,255,0.2)", width=1),
    ))
    fig.add_trace(go.Bar(
        x=labels, y=imag_parts,
        name="Imaginary",
        marker_color=VIOLET,
        marker_line=dict(color="rgba(255,255,255,0.2)", width=1),
    ))

    fig.update_layout(
        title=dict(text="<b>Statevector Amplitudes</b>", font=dict(color=TEXT, size=14), x=0.5),
        xaxis=dict(
            title="Basis State (Q M Y)",
            tickfont=dict(color=TEXT, size=11),
            titlefont=dict(color=TEXT),
            gridcolor=GRID,
        ),
        yaxis=dict(
            title="Amplitude",
            tickfont=dict(color=TEXT),
            titlefont=dict(color=TEXT),
            gridcolor=GRID,
        ),
        barmode="group",
        paper_bgcolor=BG_DARK,
        plot_bgcolor=BG_DARK,
        legend=dict(font=dict(color=TEXT), bgcolor="rgba(0,0,0,0.3)"),
        margin=dict(l=60, r=20, t=50, b=60),
        height=350,
    )

    return fig


# ─── Circuit diagram (matplotlib → PNG bytes) ────────────────────────────────

def draw_circuit_png(qc, stage: int | None = None) -> bytes:
    """
    Draw a Qiskit circuit as a PNG image.

    Parameters
    ----------
    qc : QuantumCircuit
        The circuit to draw.
    stage : int, optional
        If provided, only draw gates up to this stage (unused for now).

    Returns
    -------
    bytes : PNG image data.
    """
    fig, ax = plt.subplots(1, 1, figsize=(14, 4))
    fig.patch.set_facecolor("#0a0e1a")
    ax.set_facecolor("#0a0e1a")

    qc.draw(
        output="mpl",
        ax=ax,
        style={
            "backgroundcolor": "#0a0e1a",
            "textcolor": "#e2e8f0",
            "linecolor": "#475569",
            "gatefacecolor": "#1e293b",
            "gatetextcolor": "#e2e8f0",
            "barrierfacecolor": "#334155",
            "fontsize": 12,
        },
    )

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                facecolor="#0a0e1a", edgecolor="none")
    plt.close(fig)
    buf.seek(0)
    return buf.read()


def draw_stage_circuit_png(alpha: complex, beta: complex, stage: int) -> bytes:
    """
    Build a circuit up to the specified stage and render as PNG.
    """
    from qiskit import QuantumCircuit

    qc = QuantumCircuit(3)
    qubit_labels = ["Q (msg)", "M (Alice)", "Y (Bob)"]

    # Apply gates stage by stage
    if stage >= 0:
        qc.initialize([alpha, beta], 0)
    if stage >= 1:
        qc.barrier()
        qc.h(1)
    if stage >= 2:
        qc.cx(1, 2)
    if stage >= 3:
        qc.barrier()
        qc.cx(0, 1)
    if stage >= 4:
        qc.h(0)

    fig, ax = plt.subplots(1, 1, figsize=(max(6, 2 + stage * 2), 3.5))
    fig.patch.set_facecolor(BG_DARK)
    ax.set_facecolor(BG_DARK)

    qc.draw(
        output="mpl",
        ax=ax,
        style={
            "backgroundcolor": BG_DARK,
            "textcolor": TEXT,
            "linecolor": "#475569",
            "gatefacecolor": "#1e293b",
            "gatetextcolor": TEXT,
            "barrierfacecolor": "#334155",
            "fontsize": 12,
        },
    )

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                facecolor=BG_DARK, edgecolor="none")
    plt.close(fig)
    buf.seek(0)
    return buf.read()


# ─── Noise fidelity plot ─────────────────────────────────────────────────────

def create_noise_fidelity_plot(results: list[dict]) -> go.Figure:
    """Plot distribution fidelity vs noise rate."""
    rates = [r["noise_rate"] for r in results]
    fids = [r["distribution_fidelity"] for r in results]

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=rates, y=fids,
        mode="lines+markers",
        line=dict(color=CYAN, width=3),
        marker=dict(color=CYAN, size=10, line=dict(color="white", width=1)),
        name="Fidelity",
        hovertemplate="Noise: %{x:.3f}<br>Fidelity: %{y:.4f}<extra></extra>",
    ))

    # Ideal line
    fig.add_hline(y=1.0, line_dash="dash", line_color=GREEN,
                  annotation_text="Ideal (F=1)",
                  annotation_font_color=GREEN)

    fig.update_layout(
        title=dict(
            text="<b>Fidelity vs Depolarising Noise</b>",
            font=dict(color=TEXT, size=16),
            x=0.5,
        ),
        xaxis=dict(
            title="Depolarising Error Rate",
            titlefont=dict(color=TEXT),
            tickfont=dict(color=TEXT),
            gridcolor=GRID,
        ),
        yaxis=dict(
            title="Distribution Fidelity",
            titlefont=dict(color=TEXT),
            tickfont=dict(color=TEXT),
            gridcolor=GRID,
            range=[0, 1.05],
        ),
        paper_bgcolor=BG_DARK,
        plot_bgcolor=BG_DARK,
        legend=dict(font=dict(color=TEXT)),
        margin=dict(l=60, r=20, t=50, b=60),
        height=400,
    )

    return fig


# ─── Density matrix heatmap ──────────────────────────────────────────────────

def create_density_matrix_plot(dm: np.ndarray, title: str = "Density Matrix") -> go.Figure:
    """Create a heatmap of a density matrix (magnitude and phase)."""
    n = dm.shape[0]
    labels = [f"|{i}⟩" for i in range(n)]

    mag = np.abs(dm)
    phase = np.angle(dm, deg=True)

    text = [[f"{mag[i,j]:.3f}\n∠{phase[i,j]:.0f}°" for j in range(n)] for i in range(n)]

    fig = go.Figure(data=go.Heatmap(
        z=mag,
        x=labels,
        y=labels,
        text=text,
        texttemplate="%{text}",
        textfont=dict(size=11, color="white"),
        colorscale=[[0, BG_DARK], [0.5, VIOLET], [1, CYAN]],
        showscale=True,
        colorbar=dict(
            title="Magnitude",
            titlefont=dict(color=TEXT),
            tickfont=dict(color=TEXT),
        ),
    ))

    fig.update_layout(
        title=dict(text=f"<b>{title}</b>", font=dict(color=TEXT, size=14), x=0.5),
        xaxis=dict(tickfont=dict(color=TEXT), side="bottom"),
        yaxis=dict(tickfont=dict(color=TEXT), autorange="reversed"),
        paper_bgcolor=BG_DARK,
        plot_bgcolor=BG_DARK,
        margin=dict(l=40, r=20, t=50, b=40),
        width=320,
        height=320,
    )

    return fig
