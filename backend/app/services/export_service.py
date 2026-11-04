"""Export service for truss models and analysis results.

Supports:
- PNG: High-resolution Matplotlib plot (200 DPI) with clean white background.
- JSON: Complete Schema 1.0 truss model (including units and schema version).
- CSV: Member forces and support reactions with units and tension/compression classifications.
"""

from __future__ import annotations

import csv
import io
import math
import os
from typing import Any, Dict

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon


class ExportError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


def extract_model_from_record(record) -> Dict[str, Any]:
    """Extract Schema 1.0 model from a SketchAnalysis record."""
    if record.human_geometry_json and isinstance(record.human_geometry_json, dict):
        return record.human_geometry_json

    if record.proposal_json and isinstance(record.proposal_json, dict):
        p = record.proposal_json
        if "model" in p and "nodes" in p["model"]:
            return p
        # Convert proposal joints/members into Schema 1.0
        nodes = [{"id": j.get("id"), "x": float(j.get("x", 0)) / 100.0, "y": float(j.get("y", 0)) / 100.0} for j in p.get("joints", [])]
        members = [{"id": m.get("id"), "node_i": m.get("joint_i"), "node_j": m.get("joint_j")} for m in p.get("members", [])]
        supports = []
        for s in p.get("supports", []):
            supports.append({
                "id": s.get("id", f"S{len(supports)+1}"),
                "node": s.get("joint") or s.get("node") or (nodes[0]["id"] if nodes else "J1"),
                "type": s.get("possible_type") or s.get("type", "pin"),
            })
        loads = []
        for l in p.get("loads", []):
            loads.append({
                "id": l.get("id", f"L{len(loads)+1}"),
                "node": l.get("joint") or l.get("node") or (nodes[-1]["id"] if nodes else "J1"),
                "fx": 0.0,
                "fy": -float(l.get("magnitude", 10.0)),
            })
        return {
            "schema_version": "1.0",
            "metadata": {
                "name": record.original_filename or "Truss Model",
                "units": {"length": "m", "force": "kN"},
            },
            "model": {
                "nodes": nodes,
                "members": members,
                "supports": supports,
                "loads": loads,
            },
        }

    raise ExportError("NO_MODEL_DATA", "Analysis has no valid truss geometry to export.", 404)


def export_truss_json(record) -> Dict[str, Any]:
    """Export the complete truss model using Schema 1.0."""
    model_data = extract_model_from_record(record)
    export_obj = {
        "schema_version": model_data.get("schema_version", "1.0"),
        "metadata": {
            **model_data.get("metadata", {}),
            "analysis_id": record.id,
            "exported_status": record.status,
            "units": model_data.get("metadata", {}).get("units", {"length": "m", "force": "kN"}),
        },
        "model": model_data.get("model", {}),
    }
    if record.status == "solved" and record.solver_results_json:
        export_obj["solver_results"] = record.solver_results_json
    return export_obj


def export_truss_csv(record) -> str:
    """Export member forces and support reactions as CSV.

    Requires fresh successful solver results.
    """
    if record.status != "solved" or not record.solver_results_json:
        raise ExportError(
            "RESULTS_REQUIRED",
            "Fresh successful solver results are required for CSV export. Solve the model before exporting CSV.",
            409,
        )

    model_data = extract_model_from_record(record)
    model = model_data.get("model", {})
    solver_results = record.solver_results_json

    force_unit = solver_results.get("force_unit") or model_data.get("metadata", {}).get("units", {}).get("force", "kN")
    length_unit = model_data.get("metadata", {}).get("units", {}).get("length", "m")

    output = io.StringIO()
    writer = csv.writer(output)

    # File Header
    writer.writerow(["# Sketch2Solve Structural Analysis Export"])
    writer.writerow(["# Analysis ID", record.id])
    writer.writerow(["# Model Name", record.original_filename or "Truss Analysis"])
    writer.writerow(["# Status", "SOLVED"])
    writer.writerow(["# Force Unit", force_unit])
    writer.writerow(["# Length Unit", length_unit])
    writer.writerow([])

    # Member Forces Section
    writer.writerow(["[MEMBER AXIAL FORCES]"])
    writer.writerow([
        "Member ID",
        "Joint I",
        "Joint J",
        f"Length ({length_unit})",
        f"Axial Force ({force_unit})",
        "State",
        "Classification",
    ])

    node_map = {n["id"]: n for n in model.get("nodes", [])}
    forces = solver_results.get("member_forces", {})
    states = solver_results.get("member_states", {})

    for m in model.get("members", []):
        m_id = m.get("id")
        ni = m.get("node_i")
        nj = m.get("node_j")
        n1 = node_map.get(ni, {})
        n2 = node_map.get(nj, {})
        length_str = "N/A"
        if "x" in n1 and "y" in n1 and "x" in n2 and "y" in n2:
            dx = float(n2["x"]) - float(n1["x"])
            dy = float(n2["y"]) - float(n1["y"])
            length_str = f"{math.hypot(dx, dy):.4f}"

        force_val = forces.get(m_id)
        if force_val is not None:
            formatted_force = f"{force_val:.4f}"
            state = states.get(m_id)
            if not state:
                if abs(force_val) < 1e-6:
                    state = "zero"
                elif force_val > 0:
                    state = "tension"
                else:
                    state = "compression"
            classification = state.capitalize()
        else:
            formatted_force = "N/A"
            state = "unsolved"
            classification = "N/A"

        writer.writerow([m_id, ni, nj, length_str, formatted_force, state, classification])

    writer.writerow([])

    # Support Reactions Section
    writer.writerow(["[SUPPORT REACTIONS]"])
    writer.writerow([
        "Support ID",
        "Joint ID",
        "Support Type",
        "Axis",
        f"Reaction Force ({force_unit})",
    ])

    reactions = solver_results.get("support_reactions", {})
    for s in model.get("supports", []):
        s_id = s.get("id")
        node_id = s.get("node")
        s_type = s.get("type", "pin")
        s_reactions = reactions.get(s_id, {})
        if not s_reactions and node_id in reactions:
            s_reactions = reactions[node_id]

        if isinstance(s_reactions, dict) and s_reactions:
            for axis, val in sorted(s_reactions.items()):
                writer.writerow([s_id, node_id, s_type, str(axis).upper(), f"{float(val):.4f}"])
        else:
            writer.writerow([s_id, node_id, s_type, "N/A", "0.0000"])

    return output.getvalue()


def export_truss_png(record) -> io.BytesIO:
    """Generate high-resolution PNG using Matplotlib (200 DPI, clean white background)."""
    model_data = extract_model_from_record(record)
    model = model_data.get("model", {})
    units = model_data.get("metadata", {}).get("units", {})
    length_unit = units.get("length", "m")
    force_unit = units.get("force", "kN")
    title_name = model_data.get("metadata", {}).get("name") or record.original_filename or "Truss Model"

    nodes = model.get("nodes", [])
    members = model.get("members", [])
    supports = model.get("supports", [])
    loads = model.get("loads", [])

    is_solved = record.status == "solved" and bool(record.solver_results_json)
    solver_results = record.solver_results_json or {}
    member_forces = solver_results.get("member_forces", {})
    support_reactions = solver_results.get("support_reactions", {})

    node_map = {n["id"]: n for n in nodes}
    xs = [float(n["x"]) for n in nodes] if nodes else [0.0]
    ys = [float(n["y"]) for n in nodes] if nodes else [0.0]

    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    span = max_x - min_x if max_x > min_x else 1.0
    height = max_y - min_y if max_y > min_y else 1.0
    scale = max(span, height, 1.0)

    fig, ax = plt.subplots(figsize=(10, 6.5), dpi=200)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    ax.grid(True, linestyle=":", alpha=0.4, color="#cbd5e1")

    # Draw members
    has_tension = False
    has_compression = False
    has_zero = False

    for m in members:
        n1 = node_map.get(m["node_i"])
        n2 = node_map.get(m["node_j"])
        if not n1 or not n2:
            continue
        x1, y1 = float(n1["x"]), float(n1["y"])
        x2, y2 = float(n2["x"]), float(n2["y"])

        if is_solved and m["id"] in member_forces:
            force_val = member_forces[m["id"]]
            if abs(force_val) < 1e-6:
                color = "#475569"
                tag = f"{m['id']}: 0.00 {force_unit}"
                has_zero = True
            elif force_val > 0:
                color = "#0284c7"
                tag = f"{m['id']}: +{force_val:.2f} {force_unit} (T)"
                has_tension = True
            else:
                color = "#dc2626"
                tag = f"{m['id']}: {force_val:.2f} {force_unit} (C)"
                has_compression = True
            linewidth = 2.4
        else:
            color = "#334155"
            tag = str(m["id"])
            linewidth = 2.0

        ax.plot([x1, x2], [y1, y2], color=color, linewidth=linewidth, zorder=2)

        # Midpoint text label
        mx, my = (x1 + x2) / 2.0, (y1 + y2) / 2.0
        # Normal vector offset
        dx = x2 - x1
        dy = y2 - y1
        L = math.hypot(dx, dy)
        offset_dist = scale * 0.035
        if L > 1e-6:
            nx = -dy / L * offset_dist
            ny = dx / L * offset_dist
        else:
            nx, ny = 0.0, offset_dist

        ax.text(
            mx + nx,
            my + ny,
            tag,
            fontsize=8,
            fontweight="bold",
            color=color,
            ha="center",
            va="center",
            bbox=dict(boxstyle="round,pad=0.2", facecolor="white", edgecolor="#e2e8f0", alpha=0.92),
            zorder=3,
        )

    # Draw supports
    sup_w = scale * 0.04
    sup_h = scale * 0.05
    for s in supports:
        n = node_map.get(s.get("node"))
        if not n:
            continue
        sx, sy = float(n["x"]), float(n["y"])
        stype = s.get("type", "pin")

        # Triangle
        tri = Polygon([[sx, sy], [sx - sup_w, sy - sup_h], [sx + sup_w, sy - sup_h]], closed=True, facecolor="#94a3b8", edgecolor="#334155", linewidth=1.2, zorder=3)
        ax.add_patch(tri)
        # Ground line
        ax.plot([sx - sup_w * 1.3, sx + sup_w * 1.3], [sy - sup_h, sy - sup_h], color="#1e293b", linewidth=1.5, zorder=3)

        if stype == "roller":
            # Roller circle
            ax.plot([sx - sup_w * 0.45, sx + sup_w * 0.45], [sy - sup_h * 1.15, sy - sup_h * 1.15], "o", color="#475569", markersize=3, zorder=3)
            ax.plot([sx - sup_w * 1.3, sx + sup_w * 1.3], [sy - sup_h * 1.25, sy - sup_h * 1.25], color="#1e293b", linewidth=1.2, zorder=3)

        # Support Reaction labels if solved
        if is_solved:
            s_reactions = support_reactions.get(s["id"]) or support_reactions.get(s.get("node")) or {}
            rx = s_reactions.get("x", 0.0)
            ry = s_reactions.get("y", 0.0)
            react_labels = []
            if abs(rx) > 1e-6:
                react_labels.append(f"Rx={rx:.2f} {force_unit}")
            if abs(ry) > 1e-6:
                react_labels.append(f"Ry={ry:.2f} {force_unit}")
            if react_labels:
                ax.text(
                    sx,
                    sy - sup_h * 1.8,
                    "\n".join(react_labels),
                    fontsize=8,
                    fontweight="bold",
                    color="#047857",
                    ha="center",
                    va="top",
                    bbox=dict(boxstyle="round,pad=0.2", facecolor="#ecfdf5", edgecolor="#a7f3d0", alpha=0.9),
                    zorder=4,
                )

    # Draw loads
    arrow_len = scale * 0.12
    for l in loads:
        n = node_map.get(l.get("node"))
        if not n:
            continue
        lx, ly = float(n["x"]), float(n["y"])
        fx = float(l.get("fx", 0.0))
        fy = float(l.get("fy", -10.0 if not l.get("fx") else 0.0))
        f_mag = math.hypot(fx, fy)

        if f_mag > 1e-6:
            # Direction vector pointing TO node (lx, ly)
            dir_x = fx / f_mag
            dir_y = fy / f_mag
            start_x = lx - dir_x * arrow_len
            start_y = ly - dir_y * arrow_len

            ax.annotate(
                "",
                xy=(lx, ly),
                xytext=(start_x, start_y),
                arrowprops=dict(facecolor="#d97706", edgecolor="#b45309", width=1.5, headwidth=6, headlength=7),
                zorder=4,
            )
            ax.text(
                start_x,
                start_y,
                f"{f_mag:.1f} {force_unit}",
                fontsize=8,
                fontweight="bold",
                color="#b45309",
                ha="center",
                va="bottom" if dir_y < 0 else "top",
                bbox=dict(boxstyle="round,pad=0.15", facecolor="#fffbeb", edgecolor="#fde68a", alpha=0.9),
                zorder=5,
            )

    # Draw joints (nodes)
    for n in nodes:
        x, y = float(n["x"]), float(n["y"])
        ax.plot(x, y, "o", color="#1e293b", markersize=7, zorder=4)
        ax.text(x, y + scale * 0.035, str(n["id"]), fontsize=9, fontweight="bold", color="#0f172a", ha="center", va="bottom", zorder=5)

    # Title & Subtitle
    status_str = "SOLVED" if is_solved else "UNSOLVED DRAFT"
    ax.set_title(f"{title_name} — Structural Analysis Diagram [{status_str}]", fontsize=11, fontweight="bold", pad=12, color="#0f172a")
    ax.set_xlabel(f"X ({length_unit})", fontsize=9, color="#475569")
    ax.set_ylabel(f"Y ({length_unit})", fontsize=9, color="#475569")

    # Legend when solved
    if is_solved:
        legend_lines = []
        legend_labels = []
        if has_tension:
            legend_lines.append(plt.Line2D([0], [0], color="#0284c7", lw=2.5))
            legend_labels.append("Tension (T)")
        if has_compression:
            legend_lines.append(plt.Line2D([0], [0], color="#dc2626", lw=2.5))
            legend_labels.append("Compression (C)")
        if has_zero:
            legend_lines.append(plt.Line2D([0], [0], color="#475569", lw=2.5))
            legend_labels.append("Zero Force")
        if legend_lines:
            ax.legend(legend_lines, legend_labels, loc="upper right", framealpha=0.9, fontsize=8)

    ax.set_aspect("equal", adjustable="datalim")
    ax.margins(0.2)

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    buf.seek(0)
    return buf

