"""
Politomorphism Engine — CMG Run pe Date Reale
==============================================
Citește datele deja generate de mc_run.py și polling.csv
și rulează calibrarea CMG pe două blocuri:
  - Bloc A (populist):      AUR + Georgescu
  - Bloc B (institutional): PSD + PNL + USR

Rulare:
    python cmg_run.py

Presupune că ai rulat deja:
    python fix_data.py
    python mc_run.py
"""

import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'components'))
from cmg_component import CognitiveMorphogenesis


# =============================================================================
# CONFIG
# =============================================================================

BLOC_A = ['AUR', 'Georgescu']        # populist
BLOC_B = ['PSD', 'PNL', 'USR']       # institutional


# =============================================================================
# LOAD DATE
# =============================================================================

def load_data():
    paths = {
        'it':      'data/real/sentiment_topics.csv',
        'srm':     'data/real/srm_scores.csv',
        'poll':    'data/real/polling.csv',
        'mc_res':  'outputs/MC_results.csv',
    }
    missing = [p for p in paths.values() if not os.path.exists(p)]
    if missing:
        print(f"Fisiere lipsa: {missing}")
        print("Ruleaza mai intai: python fix_data.py && python mc_run.py")
        sys.exit(1)

    df_it   = pd.read_csv(paths['it'])
    df_srm  = pd.read_csv(paths['srm'])
    df_poll = pd.read_csv(paths['poll'])

    df = df_it.merge(df_srm, on=['date','actor'], how='outer')
    df = df.merge(df_poll, on=['date','actor'], how='left')
    df = df.sort_values(['date','actor']).reset_index(drop=True)

    return df


def build_bloc_series(df):
    """
    Agreg datele pe blocuri A si B per perioada.
    """
    dates = sorted(df['date'].unique())

    S_A_list, S_B_list = [], []
    SRM_A_list, SRM_B_list = [], []
    C_A_list, C_B_list = [], []

    for date in dates:
        sub = df[df['date'] == date]

        # --- Bloc A (populist) ---
        sub_A = sub[sub['actor'].isin(BLOC_A)]
        if len(sub_A) == 0:
            continue

        # S_A = [mean emotional_valence, mean narrative_dominance]
        s_A0 = sub_A['emotional_valence'].mean()
        s_A1 = sub_A['narrative_dominance'].mean()
        srm_A = sub_A['srm_score'].mean()

        # C_A proxy = proportia de vot a blocului A normalizata
        poll_A = sub_A['poll_pct'].sum() / 100.0  # suma AUR + Georgescu

        # --- Bloc B (institutional) ---
        sub_B = sub[sub['actor'].isin(BLOC_B)]
        s_B0 = sub_B['emotional_valence'].mean()
        s_B1 = sub_B['narrative_dominance'].mean()
        srm_B = sub_B['srm_score'].mean()
        poll_B = sub_B['poll_pct'].sum() / 100.0  # suma PSD + PNL + USR

        S_A_list.append([s_A0, s_A1])
        S_B_list.append([s_B0, s_B1])
        SRM_A_list.append(srm_A)
        SRM_B_list.append(srm_B)
        C_A_list.append([poll_A, srm_A])
        C_B_list.append([poll_B, srm_B])

    T = len(S_A_list)
    if T < 3:
        print(f"Date insuficiente: {T} perioade. Minimum 3 necesare.")
        sys.exit(1)

    S_A   = np.array(S_A_list,  dtype=float)
    S_B   = np.array(S_B_list,  dtype=float)
    SRM_A = np.array(SRM_A_list, dtype=float)
    SRM_B = np.array(SRM_B_list, dtype=float)

    # C_obs: T+1 observatii (adaugam C0 la inceput)
    C_A_obs = np.vstack([C_A_list[0], C_A_list])
    C_B_obs = np.vstack([C_B_list[0], C_B_list])

    print(f"  Perioade disponibile: {T}")
    print(f"  Bloc A (populist)    : {BLOC_A}")
    print(f"  Bloc B (institutional): {BLOC_B}")
    print(f"  Poll Bloc A range    : {np.array(C_A_list)[:,0].min():.2f} – {np.array(C_A_list)[:,0].max():.2f}")
    print(f"  Poll Bloc B range    : {np.array(C_B_list)[:,0].min():.2f} – {np.array(C_B_list)[:,0].max():.2f}")
    print(f"  SRM_A mean           : {SRM_A.mean():.4f}")
    print(f"  SRM_B mean           : {SRM_B.mean():.4f}")

    return S_A, S_B, SRM_A, SRM_B, C_A_obs, C_B_obs, dates[:T]


# =============================================================================
# VIZUALIZARE
# =============================================================================

def plot_real_results(res, C_A_obs, C_B_obs, dates, ci=None):
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.patch.set_facecolor('#0d0d0d')

    C_A_sim = res['C_A_simulated']
    C_B_sim = res['C_B_simulated']
    POL_obs = res['POL_observed']
    POL_sim = res['POL_simulated']
    T = len(dates)
    x = np.arange(T + 1)

    dim_names = ['Intentie vot (poll %)', 'SRM score']
    col_A, col_B = '#e84393', '#00c4cc'

    for dim in range(2):
        ax = axes[0][dim]
        ax.set_facecolor('#141414')
        ax.plot(x, C_A_obs[:, dim], 'o-', color=col_A, lw=1.5, ms=5,
                label=f'Bloc A populist (obs)', alpha=0.9)
        ax.plot(x, C_A_sim[:, dim], '--', color=col_A, lw=2,
                label=f'Bloc A fit (R²={res["r2_A"][dim]:.2f})')
        ax.plot(x, C_B_obs[:, dim], 's-', color=col_B, lw=1.5, ms=5,
                label=f'Bloc B institutional (obs)', alpha=0.9)
        ax.plot(x, C_B_sim[:, dim], '--', color=col_B, lw=2,
                label=f'Bloc B fit (R²={res["r2_B"][dim]:.2f})')
        ax.set_title(dim_names[dim], color='white', fontsize=10)
        ax.legend(fontsize=7, framealpha=0.3, labelcolor='white', facecolor='#1a1a1a')
        ax.tick_params(colors='#666666', labelsize=7)
        for spine in ax.spines.values():
            spine.set_edgecolor('#333333')
        ax.grid(True, alpha=0.12, color='#444444')

    # Polarizare
    ax_pol = axes[1][0]
    ax_pol.set_facecolor('#141414')
    ax_pol.plot(x, POL_obs, 'o-', color='#ffaa00', lw=2, ms=5, label='POL observed')
    ax_pol.plot(x, POL_sim, '--', color='#ff6b6b', lw=2, label='POL simulated')
    ax_pol.axhline(0.30, color='#ff4444', ls=':', lw=1.2, alpha=0.8)
    ax_pol.axhline(0.15, color='#ffaa00', ls=':', lw=1.2, alpha=0.6)
    ax_pol.text(0.5, 0.31, 'STRUCTURAL', color='#ff4444', fontsize=8)
    ax_pol.text(0.5, 0.16, 'ELEVATED', color='#ffaa00', fontsize=8)
    ax_pol.set_title('Polarization Index POL(t) — Romania date reale', color='white', fontsize=10)
    ax_pol.set_ylabel('||C_A − C_B||₂', color='#888888')
    ax_pol.legend(fontsize=8, framealpha=0.3, labelcolor='white', facecolor='#1a1a1a')
    ax_pol.tick_params(colors='#666666')
    for spine in ax_pol.spines.values():
        spine.set_edgecolor('#333333')
    ax_pol.grid(True, alpha=0.12, color='#444444')

    # Parametri
    ax_p = axes[1][1]
    ax_p.set_facecolor('#141414')
    params = {
        'α_A populist':     res['alpha_A'],
        'α_B institutional': res['alpha_B'],
        'γ SRM amplif.':    res['gamma'],
    }
    colors_p = [col_A, col_B, '#aaaaaa']
    bars = ax_p.barh(list(params.keys()), list(params.values()),
                     color=colors_p, alpha=0.85, height=0.5)

    if ci is not None:
        for i, (bar, ci_key) in enumerate(zip(bars,
                ['alpha_A_ci', 'alpha_B_ci', 'gamma_ci'])):
            v = list(params.values())[i]
            lo = abs(v - ci[ci_key][0])
            hi = abs(ci[ci_key][1] - v)
            ax_p.errorbar(v, i, xerr=[[lo],[hi]],
                          fmt='none', color='white', capsize=4, lw=1.2)

    for bar, (k, v) in zip(bars, params.items()):
        ax_p.text(v + 0.003, bar.get_y() + bar.get_height()/2,
                  f'{v:.3f}', va='center', color='white', fontsize=9)

    ax_p.set_title('Parametri estimati', color='white', fontsize=10)
    ax_p.tick_params(colors='#666666')
    for spine in ax_p.spines.values():
        spine.set_edgecolor('#333333')
    ax_p.grid(True, axis='x', alpha=0.12, color='#444444')

    pol_trend = "INCREASING ↑" if res['pol_trend'] > 0.001 else \
                "DECREASING ↓" if res['pol_trend'] < -0.001 else "STABLE →"

    fig.suptitle(
        f'CMG — Date Reale Romania 2024–2026\n'
        f'α_A={res["alpha_A"]:.3f} | α_B={res["alpha_B"]:.3f} | '
        f'γ={res["gamma"]:.3f} | POL trend: {pol_trend}',
        color='white', fontsize=12, fontweight='bold'
    )
    fig.text(0.5, 0.01,
             'ORCID: 0009-0000-2266-3356 | OSF: 10.17605/OSF.IO/HYDNZ | CC BY 4.0',
             ha='center', color='#444444', fontsize=8)
    plt.tight_layout()
    return fig


# =============================================================================
# MAIN
# =============================================================================

def main():
    os.makedirs('outputs', exist_ok=True)

    print("=" * 60)
    print("Politomorphism Engine — CMG pe Date Reale")
    print("Bloc A: AUR + Georgescu | Bloc B: PSD + PNL + USR")
    print("=" * 60)

    print("\n[1] Incarcare date...")
    df = load_data()

    print("\n[2] Construire serii pe blocuri...")
    S_A, S_B, SRM_A, SRM_B, C_A_obs, C_B_obs, dates = build_bloc_series(df)

    print("\n[3] Calibrare CMG...")
    cmg = CognitiveMorphogenesis(dim_c=2)
    res = cmg.fit(C_A_obs, C_B_obs, S_A, S_B, SRM_A, SRM_B)
    cmg.print_summary("Romania 2024–2026 — Date Reale")

    print("\n[4] Bootstrap CI (n=300)...")
    ci = cmg.bootstrap_ci(C_A_obs, C_B_obs, S_A, S_B, SRM_A, SRM_B, n_boot=300)
    print(f"  α_A CI: [{ci['alpha_A_ci'][0]:.3f}, {ci['alpha_A_ci'][1]:.3f}]")
    print(f"  α_B CI: [{ci['alpha_B_ci'][0]:.3f}, {ci['alpha_B_ci'][1]:.3f}]")
    print(f"  γ   CI: [{ci['gamma_ci'][0]:.3f}, {ci['gamma_ci'][1]:.3f}]")

    print("\n[5] Generare grafice...")
    fig = plot_real_results(res, C_A_obs, C_B_obs, dates, ci)
    fig.savefig('outputs/CMG_real_results.png',
                dpi=150, bbox_inches='tight', facecolor='#0d0d0d')
    print("  Salvat: outputs/CMG_real_results.png")
    plt.close('all')

    # Export CSV
    row = {
        'alpha_A':      round(res['alpha_A'], 4),
        'alpha_B':      round(res['alpha_B'], 4),
        'gamma':        round(res['gamma'],   4),
        'rmse':         round(res['rmse'],    4),
        'pol_trend':    round(res['pol_trend'], 4),
        'pol_final':    round(res['POL_observed'][-1], 4),
        'alpha_A_ci_lo': round(ci['alpha_A_ci'][0], 4),
        'alpha_A_ci_hi': round(ci['alpha_A_ci'][1], 4),
        'alpha_B_ci_lo': round(ci['alpha_B_ci'][0], 4),
        'alpha_B_ci_hi': round(ci['alpha_B_ci'][1], 4),
        'gamma_ci_lo':   round(ci['gamma_ci'][0], 4),
        'gamma_ci_hi':   round(ci['gamma_ci'][1], 4),
        'n_periods':    len(dates),
        'bloc_A':       str(BLOC_A),
        'bloc_B':       str(BLOC_B),
    }
    pd.DataFrame([row]).to_csv('outputs/CMG_real_results.csv', index=False)
    print("  Salvat: outputs/CMG_real_results.csv")

    print("\n" + "=" * 60)
    print("INTERPRETARE:")
    print(f"  α_A={res['alpha_A']:.3f} vs α_B={res['alpha_B']:.3f}")
    if res['alpha_A'] > res['alpha_B']:
        print("  Bloc populist actualizeaza cadrele cognitive MAI RAPID")
        print("  → consistent cu ipoteza CMG")
    else:
        print("  Bloc institutional actualizeaza mai rapid")
        print("  → posibil datorita perioadei de guvernare (penalitate incumbenta)")
    print(f"  γ={res['gamma']:.3f} — SRM {'amplifica' if res['gamma'] > 0 else 'atenueaza'} divergenta")
    pol_final = res['POL_observed'][-1]
    zones = cmg.polarization_zones([pol_final])
    print(f"  Polarizare finala: {pol_final:.3f} [{zones[0]}]")
    print("\nGATA. Pasul urmator: python srm_run.py")
    print("=" * 60)


if __name__ == '__main__':
    main()
