"""
05_figures.py
Phase 7: the figures.

Builds the core figures with consistent per-episode colours, labelled axes
(vol in percent annualised, event time in trading days), titles, legends, a
source note, and 300-dpi PNG + PDF export.

  Figure 1  long-run GPRD and Brent price, 1990-2026, dual axis, episodes marked
  Figure 2  long-run Brent realized volatility, 1990-2026, episodes marked
  Figure 3  event-study panel: realized vol vs event time, all episodes
  Figure 4  the headline: 2025 (Twelve-Day War) vs 2026 (Strait closure)
  Figure 6  GARCH conditional volatility over the sample

Output: figures/figN_<name>.png and .pdf

Usage, from the project root:
    python code/05_figures.py   (run 01-03 first)
"""

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config

SOURCE_NOTE = "Source: EIA, Caldara and Iacoviello (2022), authors' calculations."

# One colour and short label per episode, used across every figure.
EPISODE_STYLE = {
    "gulf_war_1990":        ("#1f77b4", "Gulf War 1990"),
    "iran_sanctions_2018":  ("#2ca02c", "Iran sanctions 2018"),
    "russia_ukraine_2022":  ("#9467bd", "Russia–Ukraine 2022"),
    "twelve_day_war_2025":  ("#ff7f0e", "Twelve-Day War 2025"),
    "iran_2026_campaign":   ("#d62728", "2026 campaign"),
    "iran_2026_closure":    ("#8c564b", "2026 Strait closure"),
}
# Episodes marked on the long-run figures (one per event; 2026 = the closure).
MARK_EPISODES = ["gulf_war_1990", "iran_sanctions_2018", "russia_ukraine_2022",
                 "twelve_day_war_2025", "iran_2026_closure"]

plt.rcParams.update({
    "figure.dpi": 110,
    "savefig.dpi": 300,
    "font.size": 11,
    "font.family": "DejaVu Sans",
    "axes.grid": True,
    "grid.alpha": 0.3,
    "axes.axisbelow": True,
})


def load():
    p = config.DATA_PROCESSED
    panel = pd.read_csv(p / "processed_daily_panel.csv", parse_dates=["date"]).set_index("date")
    event = pd.read_csv(p / "processed_event_panel.csv", parse_dates=["date"])
    base = pd.read_csv(p / "processed_baselines.csv", parse_dates=["trigger_date", "day_zero"])
    cond = pd.read_csv(p / "processed_garch_condvol.csv", parse_dates=["date"]).set_index("date")
    return panel, event, base, cond


def save(fig, n: int, name: str) -> None:
    fig.text(0.01, 0.01, SOURCE_NOTE, fontsize=8, color="0.4", ha="left")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    for ext in ("png", "pdf"):
        fig.savefig(config.FIGURES / f"fig{n}_{name}.{ext}", bbox_inches="tight")
    plt.close(fig)
    print(f"  saved fig{n}_{name}.png / .pdf")


def _mark_episodes(ax, base: pd.DataFrame) -> None:
    """Vertical dashed lines at each marked episode's day zero, in episode colour."""
    bykey = base.set_index("episode")
    for key in MARK_EPISODES:
        if key in bykey.index:
            color, label = EPISODE_STYLE[key]
            ax.axvline(bykey.loc[key, "day_zero"], color=color, ls="--", lw=1.3,
                       alpha=0.9, label=label)


# ----------------------------------------------------------------------
def figure1(panel, base):
    """Long-run GPRD (63-day MA) and Brent price, dual axis, episodes marked."""
    df = panel.loc["1990":]
    brent = df["brent"].dropna()
    fig, ax1 = plt.subplots(figsize=(11, 5.5))
    ax1.plot(brent.index, brent, color="0.25", lw=1.0, label="Brent ($/bbl)")
    ax1.set_ylabel("Brent spot price ($/bbl)")
    ax1.set_xlabel("Year")

    ax2 = ax1.twinx()
    gprd_ma = df["gprd"].dropna().rolling(63).mean()
    ax2.plot(gprd_ma.index, gprd_ma, color="#c43e3e", lw=1.2,
             alpha=0.8, label="GPRD (63-day MA)")
    ax2.set_ylabel("Geopolitical Risk (GPRD, 63-day MA)", color="#c43e3e")
    ax2.tick_params(axis="y", labelcolor="#c43e3e")
    ax2.grid(False)

    _mark_episodes(ax1, base)
    ax1.set_title("Geopolitical risk and the Brent oil price, 1990–2026")
    h1, l1 = ax1.get_legend_handles_labels()
    ax1.legend(h1, l1, loc="upper left", fontsize=8, ncol=2)
    save(fig, 1, "gpr_and_brent")


def figure2(panel, base):
    """Long-run Brent realized volatility with episodes marked."""
    vol = panel.loc["1990":, "brent_vol"].dropna()
    fig, ax = plt.subplots(figsize=(11, 5.5))
    ax.plot(vol.index, vol, color="0.2", lw=0.9)
    _mark_episodes(ax, base)
    ax.set_ylabel("21-day realized volatility (%, annualised)")
    ax.set_xlabel("Year")
    ax.set_title("Brent realized volatility, 1990–2026")
    ax.legend(loc="upper left", fontsize=8, ncol=2)
    save(fig, 2, "realized_vol_long_run")


def figure3(event, base):
    """Event-study panel: realized vol vs event time for all episodes."""
    fig, ax = plt.subplots(figsize=(10, 6))
    for key, g in event.groupby("episode", sort=False):
        color, label = EPISODE_STYLE[key]
        ax.plot(g["event_day"], g["brent_vol"], color=color, lw=1.6, label=label)
    ax.axvline(0, color="0.4", lw=1.0, ls=":")
    ax.set_xlabel("Event time (trading days; 0 = trigger)")
    ax.set_ylabel("21-day realized volatility (%, annualised)")
    ax.set_title("Realized volatility around each geopolitical trigger "
                 f"({config.WINDOW_PRE} before to {config.WINDOW_POST} after)")
    ax.legend(loc="upper left", fontsize=9)
    save(fig, 3, "event_study_panel")


def figure4(event):
    """Headline: 2025 vs 2026, realized vol (left) and GPRD (right), event time."""
    pair = {"twelve_day_war_2025": EPISODE_STYLE["twelve_day_war_2025"],
            "iran_2026_closure": EPISODE_STYLE["iran_2026_closure"]}
    fig, ax1 = plt.subplots(figsize=(10, 6))
    ax2 = ax1.twinx()
    ax2.grid(False)
    for key, (color, label) in pair.items():
        g = event[event["episode"] == key]
        ax1.plot(g["event_day"], g["brent_vol"], color=color, lw=2.0,
                 label=f"{label} — realized vol")
        ax2.plot(g["event_day"], g["gprd"], color=color, lw=1.4, ls="--",
                 label=f"{label} — GPRD")
    ax1.axvline(0, color="0.4", lw=1.0, ls=":")
    ax1.set_xlabel("Event time (trading days; 0 = trigger)")
    ax1.set_ylabel("21-day realized volatility (%, annualised)")
    ax2.set_ylabel("Daily geopolitical risk (GPRD)")
    ax1.set_title("Headlines vs disruption: 2025 Twelve-Day War vs 2026 Strait closure")
    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(h1 + h2, l1 + l2, loc="upper left", fontsize=8.5)
    save(fig, 4, "2025_vs_2026")


def figure5(event):
    """Small multiples: GPRD vs realized vol within each episode's window."""
    keys = list(EPISODE_STYLE.keys())
    fig, axes = plt.subplots(2, 3, figsize=(13, 7.5), sharex=True)
    for ax, key in zip(axes.ravel(), keys):
        color, label = EPISODE_STYLE[key]
        g = event[event["episode"] == key]
        ax.plot(g["event_day"], g["brent_vol"], color=color, lw=1.6)
        ax.set_title(label, fontsize=10)
        ax.axvline(0, color="0.5", lw=0.8, ls=":")
        ax2 = ax.twinx()
        ax2.plot(g["event_day"], g["gprd"], color="0.45", lw=1.0, ls="--")
        ax2.grid(False)
        ax2.tick_params(labelsize=8)
        ax.tick_params(labelsize=8)
    fig.supxlabel("Event time (trading days; 0 = trigger)")
    fig.supylabel("Realized vol (%, annualised) — solid")
    fig.suptitle("Realized volatility (coloured) and GPRD (grey dashed) by episode", y=0.99)
    save(fig, 5, "small_multiples_vol_gprd")


def figure6(panel, cond, base):
    """GARCH(1,1) conditional volatility over the sample, vs realized vol."""
    vol = panel.loc["1990":, "brent_vol"].dropna()
    c = cond.loc["1990":, "garch_condvol_ann_pct"].dropna()
    fig, ax = plt.subplots(figsize=(11, 5.5))
    ax.plot(vol.index, vol, color="0.7", lw=0.7, label="21-day realized vol")
    ax.plot(c.index, c, color="#1b5e9b", lw=0.9, label="GARCH(1,1) conditional vol")
    _mark_episodes(ax, base)
    ax.set_ylabel("Volatility (%, annualised)")
    ax.set_xlabel("Year")
    ax.set_title("GARCH(1,1) conditional volatility for Brent, 1990–2026")
    ax.legend(loc="upper left", fontsize=8, ncol=2)
    save(fig, 6, "garch_conditional_vol")


def figure7():
    """Local-projection impulse response of realized vol to a 1-SD GPRD shock."""
    lp_path = config.TABLES / "table4_local_projection.csv"
    if not lp_path.exists():
        print("  fig7 skipped (run 04_regressions.py first)")
        return
    lp = pd.read_csv(lp_path)
    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax.fill_between(lp["horizon"], lp["ci_low"], lp["ci_high"],
                    color="#1b5e9b", alpha=0.2, label="95% CI")
    ax.plot(lp["horizon"], lp["beta"], color="#1b5e9b", lw=1.8, label="Response")
    ax.axhline(0, color="0.4", lw=0.9, ls=":")
    ax.set_xlabel("Horizon (trading days after the GPRD shock)")
    ax.set_ylabel("Response of realized vol (pp, per 1-SD GPRD shock)")
    ax.set_title("Local-projection impulse response of Brent volatility to geopolitical risk")
    ax.legend(loc="upper right", fontsize=9)
    save(fig, 7, "local_projection_irf")


def figure12(event):
    """OVX (implied) vs realized vol for the post-2007 episodes OVX covers."""
    post2007 = [k for k in EPISODE_STYLE
                if event.loc[event.episode == k, "ovx"].notna().any()]
    if not post2007:
        print("  fig12 skipped (no OVX coverage)")
        return
    n = len(post2007)
    fig, axes = plt.subplots(1, n, figsize=(3.4 * n, 4.5), sharey=True)
    axes = np.atleast_1d(axes)
    for ax, key in zip(axes, post2007):
        color, label = EPISODE_STYLE[key]
        g = event[event.episode == key]
        ax.plot(g["event_day"], g["brent_vol"], color=color, lw=1.8, label="Realized vol")
        ax.plot(g["event_day"], g["ovx"], color="0.35", lw=1.4, ls="--", label="OVX (implied)")
        ax.axvline(0, color="0.6", lw=0.8, ls=":")
        ax.set_title(label, fontsize=10)
        ax.set_xlabel("Event day")
    axes[0].set_ylabel("Volatility (%, annualised)")
    axes[0].legend(loc="upper left", fontsize=8)
    fig.suptitle("Implied (OVX) vs realized volatility around the post-2007 episodes", y=1.02)
    save(fig, 12, "ovx_vs_realized")


def figure8():
    """Days-to-revert by episode, coloured by supply disruption (the mechanism)."""
    dr_path = config.TABLES / "table2_days_to_revert.csv"
    if not dr_path.exists():
        print("  fig8 skipped (run 03_persistence.py first)")
        return
    dr = pd.read_csv(dr_path).set_index("episode")
    dcolor = {"yes": "#c43e3e", "partial": "#e8a33d", "no": "#3a7d44"}
    keys = [k for k in EPISODE_STYLE if k in dr.index]
    vals = [dr.loc[k, "days_to_revert"] for k in keys]
    disrupt = [config.TRIGGERS[k]["supply_disruption"] for k in keys]
    colors = [dcolor.get(d, "0.6") for d in disrupt]
    labels = [EPISODE_STYLE[k][1] for k in keys]

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(range(len(keys)), vals, color=colors,
                  hatch=["//" if dr.loc[k, "censored"] else "" for k in keys])
    ax.set_xticks(range(len(keys)))
    ax.set_xticklabels(labels, rotation=20, ha="right", fontsize=9)
    ax.set_ylabel("Days to revert (trading days)")
    ax.set_title("Volatility persistence by episode, coloured by supply disruption")
    for b, k in zip(bars, keys):
        tag = f"≥{int(dr.loc[k,'days_to_revert'])}" if dr.loc[k, "censored"] else int(dr.loc[k, "days_to_revert"])
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 2, str(tag),
                ha="center", fontsize=9)
    handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in dcolor.values()]
    leg1 = ax.legend(handles, [f"supply disruption: {k}" for k in dcolor],
                     loc="upper right", fontsize=9)
    ax.add_artist(leg1)
    ax.bar(0, 0, color="white", edgecolor="0.4", hatch="//", label="still elevated at cutoff")
    ax.legend(loc="upper center", fontsize=8, frameon=True,
              handles=[plt.Rectangle((0, 0), 1, 1, facecolor="white", edgecolor="0.4", hatch="//")],
              labels=["still elevated at cutoff (hatched)"])
    save(fig, 8, "days_to_revert_by_disruption")


def main():
    config.FIGURES.mkdir(parents=True, exist_ok=True)
    panel, event, base, cond = load()
    print("Phase 7: figures")
    figure1(panel, base)
    figure2(panel, base)
    figure3(event, base)
    figure4(event)
    figure5(event)
    figure6(panel, cond, base)
    figure7()
    figure8()
    figure12(event)
    print(f"Done. Figures in {config.FIGURES.relative_to(config.PROJECT_ROOT)}/")


if __name__ == "__main__":
    main()
