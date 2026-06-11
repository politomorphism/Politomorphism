"""
Politomorphism Engine — MC Run pe Date Reale
=============================================
Citește CSV-urile din data/real/ și rulează calibrarea MC
pentru toți actorii definiti în config.

Rulare:
    python mc_run.py

Presupune că ai rulat deja:
    python data_collector.py
"""

import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import warnings
warnings.filterwarnings('ignore')

# Adaugă calea la components/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'components'))
from mc_component import MetapoliticalCalibration


# =============================================================================
# CONFIG
# =============================================================================

ACTORI = ['AUR', 'PSD', 'PNL', 'USR', 'Georgescu']

ACTOR_TYPE = {
    'AUR':       'populist',
    'Georgescu': 'populist',
    'PSD':       'institutional',
    'PNL':       'institutional',
    'USR':       'institutional',
}

ACTOR_COLOR = {
    'AUR':       '#e84393',
    'Georgescu': '#ff6b35',
    'PSD':       '#e63946',
    'PNL':       '#f4a261',
    'USR':       '#00b4d8',
}

MIN_PERIODS = 4   # minim de perioade pentru a include actorul


# =============================================================================
# LOAD DATE
# =============================================================================

def load_data():
    """
    Încarcă cele 3 CSV-uri și le aliniază temporal.
    """
    paths = {
        'it':   'data/real/sentiment_topics.csv',
        'srm':  'data/real/srm_scores.csv',
        'poll': 'data/real/polling.csv',
    }

    # Verificare existență
    missing = [p for p in paths.values() if not os.path.exists(p)]
    if missing:
        print(f"⚠ Fișiere lipsă: {missing}")
        print("  Rulează mai întâi: python data_collector.py")
        sys.exit(1)

    df_it   = pd.read_csv(paths['it'])
    df_srm  = pd.read_csv(paths['srm'])
    df_poll = pd.read_csv(paths['poll'])

    # Merge pe date + actor
    df = df_it.merge(df_srm,  on=['date', 'actor'], how='outer')
    df = df.merge(df_poll, on=['date', 'actor'], how='left')
    df = df.sort_values(['actor', 'date']).reset_index(drop=True)

    print(f"  ✓ Date încărcate: {len(df)} rânduri, "
          f"{df['date'].nunique()} perioade, "
          f"{df['actor'].nunique()} actori")
    return df


def prepare_actor_data(df, actor):
    """
    Pregătește seriile pentru un actor specific.
    Returnează S_obs, I_series, SRM_series sau None dacă date insuficiente.
    """
    sub = df[df['actor'] == actor].copy().sort_values('date').reset_index(drop=True)

    # Fill NaN cu medii
    for col in ['emotional_valence', 'narrative_dominance', 'geopolitical_signal',
                'srm_score', 'poll_pct']:
        if col in sub.columns:
            sub[col] = sub[col].fillna(sub[col].mean())

    if len(sub) < MIN_PERIODS:
        return None

    # I(t) — input noosfera [e, n, g]
    I_series = sub[['emotional_valence',
                    'narrative_dominance',
                    'geopolitical_signal']].values.astype(float)

    # SRM series
    SRM_series = sub['srm_score'].values.astype(float) \
        if 'srm_score' in sub.columns \
        else np.full(len(sub), 0.03)

    # S(t) — starea observată: [poll_pct normalizat, srm_score]
    # poll_pct normalizat la [0,1] pentru a fi comparabil cu srm
    if 'poll_pct' in sub.columns and not sub['poll_pct'].isna().all():
        poll_norm = sub['poll_pct'].values / 100.0
    else:
        poll_norm = np.full(len(sub), 0.3)

    srm_vals = SRM_series.copy()

    # S = [poll_norm, srm] — 2 dimensiuni
    S_obs = np.column_stack([poll_norm, srm_vals])

    # Adaugă un rând la început (S0) pentru a avea T+1 observații
    S0 = S_obs[0].copy()
    S_obs_full = np.vstack([S0, S_obs])

    return {
        'S_obs':      S_obs_full,    # [T+1 x 2]
        'I_series':   I_series,      # [T x 3]
        'SRM_series': SRM_series,    # [T]
        'dates':      sub['date'].values,
        'actor':      actor,
        'n_periods':  len(sub),
    }


# =============================================================================
# CALIBRARE
# =============================================================================

def run_calibration(df, n_boot=200):
    """
    Rulează calibrarea MC pentru toți actorii cu date suficiente.
    """
    results = {}

    for actor in ACTORI:
        print(f"\n  [{actor}]")
        data = prepare_actor_data(df, actor)

        if data is None:
            print(f"    ⚠ Date insuficiente (< {MIN_PERIODS} perioade)")
            continue

        print(f"    {data['n_periods']} perioade disponibile")

        mc = MetapoliticalCalibration(dim_s=2, dim_i=3)

        try:
            res = mc.fit(data['S_obs'], data['I_series'], data['SRM_series'])
            mc.print_summary(actor)

            # Bootstrap
            print(f"    Bootstrap CI (n={n_boot})...")
            ci = mc.bootstrap_ci(data['S_obs'], data['I_series'],
                                 data['SRM_series'], n_boot=n_boot)

            results[actor] = {
                'data':   data,
                'res':    res,
                'ci':     ci,
                'mc':     mc,
                'type':   ACTOR_TYPE.get(actor, 'unknown'),
                'color':  ACTOR_COLOR.get(actor, '#888888'),
            }

        except Exception as e:
            print(f"    ✗ Eroare la calibrare: {e}")
            continue

    return results


# =============================================================================
# VIZUALIZARE
# =============================================================================

def plot_comparative_panel(results):
    """
    Panel comparativ: alpha, beta, R² pentru toți actorii calibrați.
    """
    if not results:
        print("  ⚠ Niciun actor calibrat.")
        return None

    actors = list(results.keys())
    n = len(actors)

    fig, axes = plt.subplots(1, 3, figsize=(14, 5))
    fig.patch.set_facecolor('#0d0d0d')

    metrics = [
        ('alpha', 'α — Learning Rate', 'alpha_ci'),
        ('beta',  'β — SRM Feedback',  'beta_ci'),
    ]

    # Plot 1 & 2: alpha e beta cu CI
    for ax_idx, (param, title, ci_key) in enumerate(metrics):
        ax = axes[ax_idx]
        ax.set_facecolor('#141414')

        vals   = [results[a]['res'][param] for a in actors]
        colors = [results[a]['color'] for a in actors]
        ci_lo  = [results[a]['ci'][ci_key][0] for a in actors]
        ci_hi  = [results[a]['ci'][ci_key][1] for a in actors]

        x = np.arange(n)
        bars = ax.bar(x, vals, color=colors, alpha=0.85, width=0.6)

        # Error bars
        ax.errorbar(x, vals,
                    yerr=[[v - lo for v, lo in zip(vals, ci_lo)],
                          [hi - v  for v, hi in zip(vals, ci_hi)]],
                    fmt='none', color='white', capsize=6, lw=1.5)

        ax.set_xticks(x)
        ax.set_xticklabels(actors, color='#cccccc', fontsize=9, rotation=20, ha='right')
        ax.set_title(title, color='white', fontsize=11, pad=8)
        ax.set_ylabel('Valoare estimată', color='#888888', fontsize=9)
        ax.tick_params(colors='#666666')
        for spine in ax.spines.values():
            spine.set_edgecolor('#333333')
        ax.grid(True, axis='y', alpha=0.15, color='#444444')

        # Annotate values
        for bar, v in zip(bars, vals):
            ax.text(bar.get_x() + bar.get_width()/2, v + 0.005,
                    f'{v:.3f}', ha='center', va='bottom',
                    color='white', fontsize=8, fontweight='bold')

        # Beta hypothesis line
        if param == 'beta':
            ax.axhline(0.10, color='#ffaa00', ls='--', lw=1.2, alpha=0.7)
            ax.text(n - 0.5, 0.105, 'prag populist', color='#ffaa00', fontsize=7)

    # Plot 3: R² per actor per dimensiune
    ax3 = axes[2]
    ax3.set_facecolor('#141414')

    x = np.arange(n)
    w = 0.35
    r2_dim0 = [np.mean(results[a]['res']['r2_per_dim'][0]) for a in actors]
    r2_dim1 = [np.mean(results[a]['res']['r2_per_dim'][1]) for a in actors]
    colors_list = [results[a]['color'] for a in actors]

    ax3.bar(x - w/2, r2_dim0, w, color=colors_list, alpha=0.85, label='S_dim0 (Poll)')
    ax3.bar(x + w/2, r2_dim1, w, color=colors_list, alpha=0.45, label='S_dim1 (SRM)',
            hatch='//')
    ax3.axhline(0.0, color='#888888', ls='-', lw=0.8)
    ax3.set_xticks(x)
    ax3.set_xticklabels(actors, color='#cccccc', fontsize=9, rotation=20, ha='right')
    ax3.set_title('R² per dimensiune S(t)', color='white', fontsize=11, pad=8)
    ax3.set_ylabel('R²', color='#888888', fontsize=9)
    ax3.legend(fontsize=8, framealpha=0.3, labelcolor='white', facecolor='#1a1a1a')
    ax3.tick_params(colors='#666666')
    for spine in ax3.spines.values():
        spine.set_edgecolor('#333333')
    ax3.grid(True, axis='y', alpha=0.15, color='#444444')

    fig.suptitle(
        'Politomorphism Engine — MC Component\nCalibration Results pe Date Reale',
        color='white', fontsize=13, fontweight='bold', y=1.02
    )

    # Legenda tip actor
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='#e84393', label='Populist'),
        Patch(facecolor='#00b4d8', label='Institutional'),
    ]
    fig.legend(handles=legend_elements, loc='lower center', ncol=2,
               framealpha=0.3, labelcolor='white', facecolor='#1a1a1a',
               fontsize=9, bbox_to_anchor=(0.5, -0.05))

    fig.text(0.5, -0.08,
             'ORCID: 0009-0000-2266-3356 | OSF: 10.17605/OSF.IO/HYDNZ | CC BY 4.0',
             ha='center', color='#444444', fontsize=8)

    plt.tight_layout()
    return fig


def plot_trajectories(results):
    """
    Trajectories observed vs fitted pentru fiecare actor.
    """
    n = len(results)
    if n == 0:
        return None

    fig, axes = plt.subplots(n, 2, figsize=(14, 3.5 * n))
    fig.patch.set_facecolor('#0d0d0d')

    if n == 1:
        axes = [axes]

    dim_names = ['Intenție vot (poll %)', 'SRM score']

    for row_idx, (actor, r) in enumerate(results.items()):
        data  = r['data']
        res   = r['res']
        color = r['color']
        T     = data['n_periods']
        dates = data['dates']
        S_obs = data['S_obs']
        S_sim = res['S_simulated']
        x     = np.arange(T + 1)

        for dim in range(2):
            ax = axes[row_idx][dim]
            ax.set_facecolor('#141414')

            obs_vals = S_obs[:, dim]
            sim_vals = S_sim[:, dim]

            ax.plot(x, obs_vals, 'o-', color='#cccccc', lw=1.5, ms=5,
                    label='Observat', zorder=3)
            ax.plot(x, sim_vals, '-', color=color, lw=2.5,
                    label=f'MC fit (R²={res["r2_per_dim"][dim]:.3f})', zorder=2)
            ax.fill_between(x, sim_vals * 0.95, sim_vals * 1.05,
                            alpha=0.15, color=color)

            # Date pe axa X (subsample dacă sunt multe)
            step = max(1, T // 6)
            tick_x = list(range(0, T + 1, step))
            tick_labels = [dates[min(i, T-1)] if i < T else dates[-1] for i in tick_x]
            ax.set_xticks(tick_x)
            ax.set_xticklabels(tick_labels, rotation=30, ha='right',
                               color='#888888', fontsize=7)

            if dim == 0:
                ax.set_ylabel(f'{actor}', color=color, fontsize=10, fontweight='bold')
            ax.set_title(dim_names[dim], color='#cccccc', fontsize=9, pad=4)
            ax.legend(fontsize=7, framealpha=0.3, labelcolor='white',
                      facecolor='#1a1a1a')
            ax.tick_params(colors='#666666', labelsize=7)
            for spine in ax.spines.values():
                spine.set_edgecolor('#333333')
            ax.grid(True, alpha=0.12, color='#444444')

            # Parametri în colțul graficului
            ax.text(0.98, 0.05,
                    f'α={res["alpha"]:.3f}  β={res["beta"]:.3f}',
                    transform=ax.transAxes, ha='right', va='bottom',
                    color=color, fontsize=8, alpha=0.8)

    fig.suptitle('MC — Trajectories: Observed vs Fitted | Date Reale',
                 color='white', fontsize=12, fontweight='bold')
    plt.tight_layout()
    return fig


# =============================================================================
# MAIN
# =============================================================================

def main():
    os.makedirs('outputs', exist_ok=True)

    print("=" * 60)
    print("Politomorphism Engine — MC Calibration pe Date Reale")
    print("=" * 60)

    # 1. Load date
    print("\n[1] Încărcare date...")
    df = load_data()

    # 2. Calibrare
    print("\n[2] Calibrare MC per actor...")
    results = run_calibration(df, n_boot=300)

    if not results:
        print("\n⚠ Niciun actor nu a putut fi calibrat. Verifică data_collector.py")
        return

    # 3. Beta hypothesis summary
    print("\n" + "=" * 60)
    print("BETA HYPOTHESIS TEST")
    print("=" * 60)
    pop_betas  = [r['res']['beta'] for a, r in results.items()
                  if r['type'] == 'populist']
    inst_betas = [r['res']['beta'] for a, r in results.items()
                  if r['type'] == 'institutional']

    if pop_betas and inst_betas:
        mean_pop  = np.mean(pop_betas)
        mean_inst = np.mean(inst_betas)
        print(f"  β mediu populiști:      {mean_pop:.4f}")
        print(f"  β mediu instituționali: {mean_inst:.4f}")
        print(f"  Diferență:              {mean_pop - mean_inst:.4f}")
        if mean_pop > mean_inst:
            print("  ✓ Ipoteză SUSȚINUTĂ: populiștii au feedback SRM mai mare")
        else:
            print("  ✗ Ipoteză NESUSȚINUTĂ pe aceste date")

    # 4. Vizualizări
    print("\n[3] Generare grafice...")

    fig1 = plot_comparative_panel(results)
    if fig1:
        fig1.savefig('outputs/MC_real_comparative.png',
                     dpi=150, bbox_inches='tight', facecolor='#0d0d0d')
        print("  ✓ Salvat: outputs/MC_real_comparative.png")

    fig2 = plot_trajectories(results)
    if fig2:
        fig2.savefig('outputs/MC_real_trajectories.png',
                     dpi=150, bbox_inches='tight', facecolor='#0d0d0d')
        print("  ✓ Salvat: outputs/MC_real_trajectories.png")

    plt.close('all')

    # 5. Export rezultate CSV
    rows = []
    for actor, r in results.items():
        ci = r['ci']
        rows.append({
            'actor':       actor,
            'type':        r['type'],
            'alpha':       round(r['res']['alpha'], 4),
            'beta':        round(r['res']['beta'],  4),
            'alpha_ci_lo': round(ci['alpha_ci'][0], 4),
            'alpha_ci_hi': round(ci['alpha_ci'][1], 4),
            'beta_ci_lo':  round(ci['beta_ci'][0],  4),
            'beta_ci_hi':  round(ci['beta_ci'][1],  4),
            'rmse':        round(r['res']['rmse'],   4),
            'r2_dim0':     round(r['res']['r2_per_dim'][0], 3),
            'r2_dim1':     round(r['res']['r2_per_dim'][1], 3),
            'n_periods':   r['data']['n_periods'],
        })

    df_out = pd.DataFrame(rows)
    df_out.to_csv('outputs/MC_results.csv', index=False)
    print("  ✓ Salvat: outputs/MC_results.csv")
    print("\n" + df_out.to_string(index=False))

    print("\n" + "=" * 60)
    print("GATA. Pasul următor: python cmg_run.py")
    print("=" * 60)


if __name__ == '__main__':
    main()
