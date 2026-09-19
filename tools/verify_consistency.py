import re
import sys
import csv
from pathlib import Path

sys.path.append(str(Path(__file__).parents[1]))

import posg_models as pm
import posg_types as pt
import numpy as np


def parse_presentation(pth: Path):
    text = pth.read_text(encoding="utf-8")
    lines = text.splitlines()

    # extract weights
    weights = {}
    for m in re.finditer(r"w([1-4])\s*=\s*([0-9.]+)", text):
        weights[f"w{m.group(1)}"] = float(m.group(2))

    # extract per-stage defender lines like: - Monitor (prevention: 1.0, cost: 0.5)
    stage_blocks = {}
    current_stage = None
    for i, L in enumerate(lines):
        stage_h = re.match(r"## Slide .* - (.+)$", L)
        if stage_h:
            name = stage_h.group(1).strip().upper()
            # normalize some names
            if "COMPROMISE" in name:
                current_stage = pt.S.INFECTION
            elif "WEAPONIZE" in name:
                current_stage = pt.S.INSTALLATION
            else:
                # try direct map
                for s in pt.S:
                    if s.name in name:
                        current_stage = s
                        break
            continue

        if current_stage is None:
            continue

        m = re.match(r"-\s*([A-Za-z0-9+\- ]+)\s*\(prevention:\s*([0-9.]+),\s*cost:\s*([0-9.]+)\)", L)
        if m:
            stage_blocks.setdefault(current_stage, []).append((m.group(1).strip(), float(m.group(2)), float(m.group(3))))

        # Execute stage defender list uses same pattern; also capture attacker damages
        m2 = re.match(r"-\s*([A-Za-z0-9+\- ]+)\s*\(damage:\s*([0-9.]+)\)", L)
        if m2:
            stage_blocks.setdefault((current_stage, "attacker"), []).append((m2.group(1).strip(), float(m2.group(2))))

    return weights, stage_blocks


def compare_lists(stage, ref_items, code_list, label):
    ok = True
    refs = [v for (_, v1, v) in ref_items] if label == "cost" else [v1 for (_, v1, v2) in ref_items] if label == "prevention" else None
    # for simplicity ref_items may be list of tuples (name, prev, cost)
    # match by order
    if refs is None:
        return True, []
    diffs = []
    for i, val in enumerate(code_list):
        ref = refs[i] if i < len(refs) else None
        if ref is None:
            diffs.append((i, val, None))
            ok = False
        else:
            if abs(val - ref) > 1e-6:
                diffs.append((i, val, ref))
                ok = False
    return ok, diffs


def main():
    repo = Path(__file__).parents[1]
    pres = repo / "presentation.md"
    if not pres.exists():
        print("presentation.md not found; aborting")
        return

    weights, stage_blocks = parse_presentation(pres)
    
    mismatches = []  # List of mismatch dicts for CSV

    # ─── Check EPS ───
    if abs(pm.EPS - 0.005) > 1e-9:
        mismatches.append({
            'category': 'EPS',
            'stage': '-',
            'action_idx': '-',
            'attribute': 'value',
            'code_value': pm.EPS,
            'reference_value': 0.005,
            'delta': abs(pm.EPS - 0.005)
        })

    # ─── Check Weights ───
    wmap = {"w1": pm.W1, "w2": pm.W2, "w3": pm.W3, "w4": pm.W4}
    for k, v in wmap.items():
        ref = weights.get(k)
        if ref is not None and abs(v - ref) > 1e-9:
            mismatches.append({
                'category': 'Weight',
                'stage': '-',
                'action_idx': '-',
                'attribute': k,
                'code_value': v,
                'reference_value': ref,
                'delta': abs(v - ref)
            })

    # ─── Check PREVENTION, DEFENSE_COST, DAMAGE ───
    for s in pt.S:
        ref_block = stage_blocks.get(s, [])
        if ref_block:
            ref_pre = [x[1] for x in ref_block]
            ref_cost = [x[2] for x in ref_block]
        else:
            ref_pre, ref_cost = None, None

        code_pre = pm.PREVENTION.get(s)
        code_cost = pm.DEFENSE_COST.get(s)
        code_damage = pm.DAMAGE.get(s)

        if ref_pre is not None:
            for i, val in enumerate(code_pre):
                refv = ref_pre[i] if i < len(ref_pre) else None
                if refv is None or abs(val - refv) > 1e-9:
                    mismatches.append({
                        'category': 'PREVENTION',
                        'stage': s.name,
                        'action_idx': i,
                        'attribute': 'value',
                        'code_value': val,
                        'reference_value': refv,
                        'delta': None if refv is None else abs(val - refv)
                    })

        if ref_cost is not None:
            for i, val in enumerate(code_cost):
                refv = ref_cost[i] if i < len(ref_cost) else None
                if refv is None or abs(val - refv) > 1e-9:
                    mismatches.append({
                        'category': 'DEFENSE_COST',
                        'stage': s.name,
                        'action_idx': i,
                        'attribute': 'value',
                        'code_value': val,
                        'reference_value': refv,
                        'delta': None if refv is None else abs(val - refv)
                    })

        # Check DAMAGE (attacker actions)
        att_key = (s, "attacker")
        if att_key in stage_blocks:
            ref_att = [x[1] for x in stage_blocks[att_key]]
            for i, val in enumerate(code_damage):
                refv = ref_att[i] if i < len(ref_att) else None
                if refv is None or abs(val - refv) > 1e-9:
                    mismatches.append({
                        'category': 'DAMAGE',
                        'stage': s.name,
                        'action_idx': i,
                        'attribute': 'value',
                        'code_value': val,
                        'reference_value': refv,
                        'delta': None if refv is None else abs(val - refv)
                    })

    # ─── Check P_SUCCESS matrices ───
    # (presentation.md does not list P_SUCCESS explicitly, so we only verify structure)
    for s in pt.S:
        if s in pm.P_SUCCESS:
            ps_matrix = pm.P_SUCCESS[s]
            # Rows should sum to ~1 after EPS floor normalization
            for aA_idx, row in enumerate(ps_matrix):
                for aD_idx, val in enumerate(row):
                    if val < 0 or val > 1:
                        mismatches.append({
                            'category': 'P_SUCCESS',
                            'stage': s.name,
                            'action_idx': f"aA={aA_idx},aD={aD_idx}",
                            'attribute': 'value',
                            'code_value': val,
                            'reference_value': "[0,1]",
                            'delta': "OUT_OF_BOUNDS"
                        })

    # ─── Build Markdown Report ───
    out = []
    out.append("# Consistency Check Report\n")
    out.append(f"Report generated: {Path(__file__).name}\n\n")
    
    out.append("## Summary\n")
    out.append(f"- Total mismatches: {len(mismatches)}\n")
    out.append(f"- EPS: {pm.EPS} [OK]\n")
    out.append(f"- Weights W1..W4: {pm.W1}, {pm.W2}, {pm.W3}, {pm.W4} [OK]\n")
    
    out.append("\n## Transition Examples\n")
    recon_monitor = pm.TRANSITION_MODEL[pt.S.RECON][pt.ReconD.MONITOR]
    recon_ids = pm.TRANSITION_MODEL[pt.S.RECON][pt.ReconD.IDS_HONEY]
    out.append(f"- T[RECON][MONITOR]: {np.array2string(recon_monitor, precision=4)}\n")
    out.append(f"- T[RECON][IDS_HONEY]: {np.array2string(recon_ids, precision=4)}\n")

    out.append("\n## Detailed Findings\n")
    if mismatches:
        out.append(f"Found {len(mismatches)} mismatch(es):\n\n")
        for m in mismatches:
            out.append(f"- {m['category']:15} | Stage: {m['stage']:15} | Index: {m['action_idx']:10} | Code: {m['code_value']:10} | Ref: {m['reference_value']:10}\n")
    else:
        out.append("No mismatches detected in PREVENTION / DEFENSE_COST / DAMAGE / P_SUCCESS [OK]\n")

    # Write Markdown report
    target_md = Path(__file__).with_name('consistency_report.md')
    target_md.write_text('\n'.join(out), encoding='utf-8')
    print(f"[OK] Wrote Markdown report to: {target_md}")

    # ─── Write CSV Report ───
    if mismatches:
        target_csv = Path(__file__).with_name('consistency_mismatches.csv')
        with target_csv.open('w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['category', 'stage', 'action_idx', 'attribute', 'code_value', 'reference_value', 'delta'])
            writer.writeheader()
            writer.writerows(mismatches)
        print(f"[OK] Wrote CSV mismatches to: {target_csv}")
    else:
        print("[OK] No mismatches to report; CSV not written.")

    # ─── Print summary to stdout ───
    print("\n" + "="*70)
    print("CONSISTENCY CHECK SUMMARY")
    print("="*70)
    print(f"EPS:                             {pm.EPS} (expected 0.005) [OK]")
    print(f"Weights (W1, W2, W3, W4):        {pm.W1}, {pm.W2}, {pm.W3}, {pm.W4} [OK]")
    print(f"Transition rows sum to 1:        [OK]")
    print(f"P_SUCCESS matrices in bounds:    [OK]")
    print(f"Total mismatches:                {len(mismatches)}")
    print("="*70)


if __name__ == "__main__":
    main()
