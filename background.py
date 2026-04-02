import json
import random
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
from matplotlib.animation import FFMpegWriter
import matplotlib.gridspec as gridspec

# Dimensions TikTok 9:16
WIDTH_PX = 1080
HEIGHT_PX = 1920
DPI = 100
FIG_W = WIDTH_PX / DPI
FIG_H = HEIGHT_PX / DPI

DURATION_SEC = 60
FPS = 24
TOTAL_FRAMES = DURATION_SEC * FPS

# Palette dark trading
BG_COLOR      = "#0a0e1a"
GRID_COLOR    = "#1a2035"
CANDLE_UP     = "#00e676"
CANDLE_DOWN   = "#ff1744"
TEXT_COLOR    = "#e0e0e0"
ACCENT_COLOR  = "#00bcd4"
ACCENT2_COLOR = "#ff9800"
ACCENT3_COLOR = "#ab47bc"

# ─────────────────────────────────────────────
# DONNÉES SIMULÉES
# ─────────────────────────────────────────────

def generate_candles(n=80, base=100.0, volatility=0.02):
    candles, price = [], base
    for _ in range(n):
        o = price
        c = o * (1 + random.gauss(0, volatility))
        h = max(o, c) * (1 + abs(random.gauss(0, volatility * 0.4)))
        l = min(o, c) * (1 - abs(random.gauss(0, volatility * 0.4)))
        candles.append((o, h, l, c))
        price = c
    return candles

def candles_to_closes(candles):
    return [c[3] for c in candles]

def compute_rsi(closes, period=14):
    rsi = [50.0] * period
    for i in range(period, len(closes)):
        gains = [max(closes[j] - closes[j-1], 0) for j in range(i-period+1, i+1)]
        losses = [max(closes[j-1] - closes[j], 0) for j in range(i-period+1, i+1)]
        ag, al = np.mean(gains), np.mean(losses)
        rs = ag / al if al != 0 else 100
        rsi.append(100 - 100 / (1 + rs))
    return rsi

def compute_macd(closes, fast=12, slow=26, signal=9):
    def ema(data, n):
        k, result = 2/(n+1), [data[0]]
        for v in data[1:]:
            result.append(v * k + result[-1] * (1 - k))
        return result
    ema_fast = ema(closes, fast)
    ema_slow = ema(closes, slow)
    macd_line = [f - s for f, s in zip(ema_fast, ema_slow)]
    signal_line = ema(macd_line, signal)
    histogram = [m - s for m, s in zip(macd_line, signal_line)]
    return macd_line, signal_line, histogram

def compute_ma(closes, period):
    ma = [None] * (period - 1)
    for i in range(period - 1, len(closes)):
        ma.append(np.mean(closes[i-period+1:i+1]))
    return ma

# ─────────────────────────────────────────────
# HEADER COMMUN
# ─────────────────────────────────────────────

def draw_header(ax, actif, titre, niveau, fond_type):
    ax.clear()
    ax.set_facecolor(BG_COLOR)
    ax.axis('off')
    niveau_colors = {"débutant": "#4caf50", "intermédiaire": "#ff9800", "confirmé": "#f44336"}
    niv_color = niveau_colors.get(niveau, "#4caf50")
    ax.text(0.05, 0.80, actif, transform=ax.transAxes,
            color=ACCENT_COLOR, fontsize=22, fontweight='bold', va='top')
    ax.text(0.05, 0.30, titre.upper(), transform=ax.transAxes,
            color=TEXT_COLOR, fontsize=10, va='top', alpha=0.9)
    ax.text(0.95, 0.80, f"● {niveau.upper()}", transform=ax.transAxes,
            color=niv_color, fontsize=10, fontweight='bold', va='top', ha='right')
    ax.axhline(y=0.05, color=ACCENT_COLOR, linewidth=1, alpha=0.4)

# ─────────────────────────────────────────────
# SOUS-TITRES COMMUNS
# ─────────────────────────────────────────────

def draw_subtitle(ax, frame, sous_titres, tags):
    ax.clear()
    ax.set_facecolor(BG_COLOR)
    ax.axis('off')
    if sous_titres:
        idx = min(int((frame / TOTAL_FRAMES) * len(sous_titres)), len(sous_titres) - 1)
        subtitle = sous_titres[idx]
        ax.text(0.5, 0.60, subtitle, transform=ax.transAxes,
                color='white', fontsize=17, fontweight='bold',
                ha='center', va='center', wrap=True,
                bbox=dict(boxstyle='round,pad=0.4', facecolor='#000000',
                          alpha=0.75, edgecolor=ACCENT_COLOR, linewidth=1.2))
    ax.text(0.5, 0.10, tags, transform=ax.transAxes,
            color=ACCENT_COLOR, fontsize=9, ha='center', va='bottom', alpha=0.7)

# ─────────────────────────────────────────────
# TYPE 1 : CHANDELIERS
# ─────────────────────────────────────────────

def render_chandeliers(ax, candles_full, frame):
    # Ticker continu : scroll de 1 bougie toutes les 7 frames
    window = 25
    scroll_speed = 7  # frames par bougie
    max_start = len(candles_full) - window
    start = min(frame // scroll_speed, max_start)
    visible = candles_full[start:start + window]

    ax.clear()
    ax.set_facecolor(BG_COLOR)

    for i, (o, h, l, c) in enumerate(visible):
        color = CANDLE_UP if c >= o else CANDLE_DOWN
        body_h = max(abs(c - o), 0.0001)
        rect = mpatches.Rectangle((i - 0.35, min(o, c)), 0.7, body_h,
                                   color=color, alpha=0.85, zorder=3)
        ax.add_patch(rect)
        ax.plot([i, i], [l, h], color=color, linewidth=1.2, alpha=0.85, zorder=2)

    prices = [c[3] for c in visible]
    p_min = min(c[2] for c in visible)
    p_max = max(c[1] for c in visible)
    margin = (p_max - p_min) * 0.12
    ax.set_xlim(-1, window + 1)
    ax.set_ylim(p_min - margin, p_max + margin)
    ax.set_facecolor(BG_COLOR)
    ax.tick_params(colors=TEXT_COLOR, labelsize=7)
    ax.xaxis.set_visible(False)
    ax.yaxis.tick_right()
    ax.grid(True, color=GRID_COLOR, linewidth=0.4, alpha=0.8)
    for spine in ax.spines.values():
        spine.set_color(GRID_COLOR)

    last = prices[-1]
    ax.axhline(y=last, color=ACCENT_COLOR, linewidth=0.8, linestyle='--', alpha=0.6)
    ax.text(window + 0.5, last, f"{last:.4f}", color=ACCENT_COLOR,
            fontsize=7, va='center', fontweight='bold')

# ─────────────────────────────────────────────
# TYPE 2 : RSI
# ─────────────────────────────────────────────

def render_rsi(ax_price, ax_rsi, candles_full, frame):
    window = 40
    scroll_speed = 5
    max_start = len(candles_full) - window
    start = min(frame // scroll_speed, max_start)
    visible = candles_full[start:start + window]
    closes = candles_to_closes(candles_full)
    rsi_full = compute_rsi(closes)
    rsi_visible = rsi_full[start:start + window]
    x = list(range(len(visible)))

    # Prix (mini chandeliers)
    ax_price.clear()
    ax_price.set_facecolor(BG_COLOR)
    for i, (o, h, l, c) in enumerate(visible):
        color = CANDLE_UP if c >= o else CANDLE_DOWN
        ax_price.plot([i, i], [l, h], color=color, linewidth=1.5, alpha=0.7)
        ax_price.plot([i], [c], 'o', color=color, markersize=2.5, alpha=0.9)
    ax_price.set_xlim(-1, window + 1)
    ax_price.set_facecolor(BG_COLOR)
    ax_price.xaxis.set_visible(False)
    ax_price.tick_params(colors=TEXT_COLOR, labelsize=7)
    ax_price.yaxis.tick_right()
    ax_price.grid(True, color=GRID_COLOR, linewidth=0.4)
    for spine in ax_price.spines.values():
        spine.set_color(GRID_COLOR)

    # RSI
    ax_rsi.clear()
    ax_rsi.set_facecolor(BG_COLOR)
    ax_rsi.plot(x, rsi_visible, color=ACCENT2_COLOR, linewidth=2, zorder=3)
    ax_rsi.axhline(70, color=CANDLE_DOWN, linewidth=1, linestyle='--', alpha=0.7)
    ax_rsi.axhline(30, color=CANDLE_UP, linewidth=1, linestyle='--', alpha=0.7)
    ax_rsi.axhline(50, color=TEXT_COLOR, linewidth=0.5, linestyle=':', alpha=0.4)
    ax_rsi.fill_between(x, rsi_visible, 70, where=[r > 70 for r in rsi_visible],
                        color=CANDLE_DOWN, alpha=0.2)
    ax_rsi.fill_between(x, rsi_visible, 30, where=[r < 30 for r in rsi_visible],
                        color=CANDLE_UP, alpha=0.2)
    ax_rsi.set_xlim(-1, window + 1)
    ax_rsi.set_ylim(0, 100)
    ax_rsi.set_yticks([30, 50, 70])
    ax_rsi.tick_params(colors=TEXT_COLOR, labelsize=7)
    ax_rsi.yaxis.tick_right()
    ax_rsi.grid(True, color=GRID_COLOR, linewidth=0.4)
    ax_rsi.text(-0.5, 72, 'Suracheté', color=CANDLE_DOWN, fontsize=7, alpha=0.8)
    ax_rsi.text(-0.5, 22, 'Survendu', color=CANDLE_UP, fontsize=7, alpha=0.8)
    ax_rsi.text(window - 5, rsi_visible[-1] + 3, f"RSI: {rsi_visible[-1]:.0f}",
                color=ACCENT2_COLOR, fontsize=8, fontweight='bold')
    for spine in ax_rsi.spines.values():
        spine.set_color(GRID_COLOR)

# ─────────────────────────────────────────────
# TYPE 3 : MACD
# ─────────────────────────────────────────────

def render_macd(ax_price, ax_macd, candles_full, frame):
    window = 40
    scroll_speed = 5
    max_start = len(candles_full) - window
    start = min(frame // scroll_speed, max_start)
    visible = candles_full[start:start + window]
    closes = candles_to_closes(candles_full)
    macd_line, signal_line, histogram = compute_macd(closes)
    m_vis = macd_line[start:start + window]
    s_vis = signal_line[start:start + window]
    h_vis = histogram[start:start + window]
    x = list(range(len(visible)))

    # Prix
    ax_price.clear()
    ax_price.set_facecolor(BG_COLOR)
    for i, (o, h, l, c) in enumerate(visible):
        color = CANDLE_UP if c >= o else CANDLE_DOWN
        ax_price.plot([i, i], [l, h], color=color, linewidth=1.5, alpha=0.7)
        ax_price.plot([i], [c], 'o', color=color, markersize=2.5)
    ax_price.set_xlim(-1, window + 1)
    ax_price.set_facecolor(BG_COLOR)
    ax_price.xaxis.set_visible(False)
    ax_price.tick_params(colors=TEXT_COLOR, labelsize=7)
    ax_price.yaxis.tick_right()
    ax_price.grid(True, color=GRID_COLOR, linewidth=0.4)
    for spine in ax_price.spines.values():
        spine.set_color(GRID_COLOR)

    # MACD
    ax_macd.clear()
    ax_macd.set_facecolor(BG_COLOR)
    colors_hist = [CANDLE_UP if v >= 0 else CANDLE_DOWN for v in h_vis]
    ax_macd.bar(x, h_vis, color=colors_hist, alpha=0.6, zorder=2)
    ax_macd.plot(x, m_vis, color=ACCENT_COLOR, linewidth=1.8, label='MACD', zorder=3)
    ax_macd.plot(x, s_vis, color=ACCENT2_COLOR, linewidth=1.5, linestyle='--',
                 label='Signal', zorder=3)
    ax_macd.axhline(0, color=TEXT_COLOR, linewidth=0.5, alpha=0.4)
    ax_macd.set_xlim(-1, window + 1)
    ax_macd.tick_params(colors=TEXT_COLOR, labelsize=7)
    ax_macd.yaxis.tick_right()
    ax_macd.grid(True, color=GRID_COLOR, linewidth=0.4)
    ax_macd.legend(loc='upper left', fontsize=7, facecolor=BG_COLOR,
                   labelcolor=TEXT_COLOR, framealpha=0.7)
    for spine in ax_macd.spines.values():
        spine.set_color(GRID_COLOR)

# ─────────────────────────────────────────────
# TYPE 4 : MOYENNES MOBILES
# ─────────────────────────────────────────────

def render_moyenne_mobile(ax, candles_full, frame):
    window = 40
    scroll_speed = 5
    max_start = len(candles_full) - window
    start = min(frame // scroll_speed, max_start)
    visible = candles_full[start:start + window]
    closes_full = candles_to_closes(candles_full)
    ma20_full = compute_ma(closes_full, 20)
    ma50_full = compute_ma(closes_full, 50)

    closes_v = closes_full[start:start + window]
    ma20_v = ma20_full[start:start + window]
    ma50_v = ma50_full[start:start + window]
    x = list(range(window))

    ax.clear()
    ax.set_facecolor(BG_COLOR)

    # Chandeliers
    for i, (o, h, l, c) in enumerate(visible):
        color = CANDLE_UP if c >= o else CANDLE_DOWN
        body_h = max(abs(c - o), 0.0001)
        rect = mpatches.Rectangle((i - 0.3, min(o, c)), 0.6, body_h,
                                   color=color, alpha=0.6, zorder=2)
        ax.add_patch(rect)
        ax.plot([i, i], [l, h], color=color, linewidth=1, alpha=0.6)

    # MA20
    ma20_x = [i for i, v in enumerate(ma20_v) if v is not None]
    ma20_y = [v for v in ma20_v if v is not None]
    if ma20_x:
        ax.plot(ma20_x, ma20_y, color=ACCENT_COLOR, linewidth=2,
                label='MA20', zorder=4)

    # MA50
    ma50_x = [i for i, v in enumerate(ma50_v) if v is not None]
    ma50_y = [v for v in ma50_v if v is not None]
    if ma50_x:
        ax.plot(ma50_x, ma50_y, color=ACCENT2_COLOR, linewidth=2,
                linestyle='--', label='MA50', zorder=4)

    # Zone entre MA
    if ma20_x and ma50_x:
        common_x = [i for i in ma20_x if i in ma50_x]
        if common_x:
            cy20 = [ma20_v[i] for i in common_x]
            cy50 = [ma50_v[i] for i in common_x]
            ax.fill_between(common_x, cy20, cy50, alpha=0.08, color=ACCENT_COLOR)

    p_min = min(c[2] for c in visible)
    p_max = max(c[1] for c in visible)
    margin = (p_max - p_min) * 0.12
    ax.set_xlim(-1, window + 1)
    ax.set_ylim(p_min - margin, p_max + margin)
    ax.set_facecolor(BG_COLOR)
    ax.xaxis.set_visible(False)
    ax.tick_params(colors=TEXT_COLOR, labelsize=7)
    ax.yaxis.tick_right()
    ax.grid(True, color=GRID_COLOR, linewidth=0.4)
    ax.legend(loc='upper left', fontsize=8, facecolor=BG_COLOR,
              labelcolor=TEXT_COLOR, framealpha=0.7)
    for spine in ax.spines.values():
        spine.set_color(GRID_COLOR)

# ─────────────────────────────────────────────
# TYPE 5 : TEXTE CLÉS
# ─────────────────────────────────────────────

def render_texte_cles(ax, frame, concepts):
    ax.clear()
    ax.set_facecolor(BG_COLOR)
    ax.axis('off')
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    progress = frame / TOTAL_FRAMES
    n_visible = max(1, int(progress * len(concepts)) + 1)

    positions_y = np.linspace(0.85, 0.15, len(concepts))
    colors_cycle = [ACCENT_COLOR, ACCENT2_COLOR, CANDLE_UP, ACCENT3_COLOR,
                    TEXT_COLOR, CANDLE_DOWN]

    for i, (concept, y) in enumerate(zip(concepts[:n_visible], positions_y[:n_visible])):
        color = colors_cycle[i % len(colors_cycle)]
        alpha = 1.0 if i == n_visible - 1 else 0.6 + 0.4 * (i / max(n_visible - 1, 1))
        size = 20 if i == n_visible - 1 else 15

        # Puce
        ax.text(0.05, y, "▶", transform=ax.transAxes,
                color=color, fontsize=size * 0.7, va='center', alpha=alpha)
        # Texte
        ax.text(0.12, y, concept, transform=ax.transAxes,
                color=color, fontsize=size, fontweight='bold',
                va='center', alpha=alpha)

        # Ligne séparatrice légère
        if i < n_visible - 1:
            ax.axhline(y=y - 0.05, xmin=0.05, xmax=0.95,
                      color=GRID_COLOR, linewidth=0.5, alpha=0.5)

# ─────────────────────────────────────────────
# TYPE 6 : SCHÉMA RISK/REWARD
# ─────────────────────────────────────────────

def render_schema_risk_reward(ax, frame):
    ax.clear()
    ax.set_facecolor(BG_COLOR)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis('off')

    progress = frame / TOTAL_FRAMES

    # Prix d'entrée
    entry_y = 4.5
    tp_y = 7.5
    sl_y = 3.0

    reward = tp_y - entry_y
    risk = entry_y - sl_y
    rr = reward / risk if risk > 0 else 0

    # Animation : les zones apparaissent progressivement
    alpha_entry = min(1.0, progress * 4)
    alpha_tp = min(1.0, max(0, (progress - 0.25) * 4))
    alpha_sl = min(1.0, max(0, (progress - 0.5) * 4))
    alpha_rr = min(1.0, max(0, (progress - 0.75) * 4))

    # Zone TP (gain)
    if alpha_tp > 0:
        tp_rect = mpatches.Rectangle((1, entry_y), 7, tp_y - entry_y,
                                     color=CANDLE_UP, alpha=0.15 * alpha_tp)
        ax.add_patch(tp_rect)
        ax.axhline(tp_y, xmin=0.1, xmax=0.9, color=CANDLE_UP,
                   linewidth=2, alpha=alpha_tp)
        ax.text(8.5, tp_y, f"TP", color=CANDLE_UP, fontsize=11,
                fontweight='bold', va='center', alpha=alpha_tp)
        ax.text(5, (entry_y + tp_y) / 2, f"+{reward:.1f}R",
                color=CANDLE_UP, fontsize=13, fontweight='bold',
                ha='center', va='center', alpha=alpha_tp)

    # Zone SL (perte)
    if alpha_sl > 0:
        sl_rect = mpatches.Rectangle((1, sl_y), 7, entry_y - sl_y,
                                     color=CANDLE_DOWN, alpha=0.15 * alpha_sl)
        ax.add_patch(sl_rect)
        ax.axhline(sl_y, xmin=0.1, xmax=0.9, color=CANDLE_DOWN,
                   linewidth=2, alpha=alpha_sl)
        ax.text(8.5, sl_y, f"SL", color=CANDLE_DOWN, fontsize=11,
                fontweight='bold', va='center', alpha=alpha_sl)
        ax.text(5, (entry_y + sl_y) / 2, f"-{risk:.1f}R",
                color=CANDLE_DOWN, fontsize=13, fontweight='bold',
                ha='center', va='center', alpha=alpha_sl)

    # Ligne d'entrée
    if alpha_entry > 0:
        ax.axhline(entry_y, xmin=0.1, xmax=0.9, color=ACCENT_COLOR,
                   linewidth=2.5, alpha=alpha_entry)
        ax.text(8.5, entry_y, "ENTRÉE", color=ACCENT_COLOR, fontsize=9,
                fontweight='bold', va='center', alpha=alpha_entry)

    # Ratio R/R
    if alpha_rr > 0:
        ax.text(5, 1.5, f"Ratio Risk/Reward : 1 : {rr:.1f}",
                color=ACCENT2_COLOR, fontsize=14, fontweight='bold',
                ha='center', va='center', alpha=alpha_rr,
                bbox=dict(boxstyle='round,pad=0.5', facecolor='#000000',
                          alpha=0.7, edgecolor=ACCENT2_COLOR, linewidth=1.5))

    # Légende cours
    ax.text(5, 9.2, "SCHÉMA RISK / REWARD", color=TEXT_COLOR,
            fontsize=13, fontweight='bold', ha='center', va='center', alpha=0.9)

# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def generate_background(metadata_path="video_metadata.json", output_path="background.mp4"):
    with open(metadata_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    actif      = data.get("actif", "BTC/USDT")
    titre      = data.get("titre", "Trading")
    niveau     = data.get("niveau", "débutant")
    fond_type  = data.get("fond_type", "chandeliers")
    sous_titres = data.get("sous_titres", [])
    tags        = data.get("tags", "#trading")
    concepts    = data.get("concepts_cles", ["Discipline", "Patience", "Gestion du risque"])

    print(f"🎨 Fond : {fond_type} | Actif : {actif} | Niveau : {niveau}")

    # Paramètres selon l'actif
    volatility = 0.008 if "USD" in actif and "USDT" not in actif else 0.022
    base_map = {"BTC": 65000, "ETH": 3500, "SOL": 180, "BNB": 600,
                "XRP": 0.55, "EUR": 1.08, "GBP": 1.27, "AUD": 0.65}
    base = next((v for k, v in base_map.items() if k in actif), 100.0)
    candles_full = generate_candles(n=300, base=base, volatility=volatility)

    # Setup figure selon le type
    fig = plt.figure(figsize=(FIG_W, FIG_H), dpi=DPI, facecolor=BG_COLOR)

    if fond_type in ["indicateur_rsi", "indicateur_macd"]:
        gs = gridspec.GridSpec(4, 1, figure=fig,
                               height_ratios=[0.10, 0.25, 0.23, 0.42], hspace=0.03)
        ax_header   = fig.add_subplot(gs[0])
        ax_price    = fig.add_subplot(gs[1])
        ax_indicator = fig.add_subplot(gs[2])
        ax_subtitle = fig.add_subplot(gs[3])
    elif fond_type in ["chandeliers", "moyenne_mobile"]:
        gs = gridspec.GridSpec(3, 1, figure=fig,
                               height_ratios=[0.10, 0.48, 0.42], hspace=0.03)
        ax_header   = fig.add_subplot(gs[0])
        ax_chart    = fig.add_subplot(gs[1])
        ax_subtitle = fig.add_subplot(gs[2])
    else:  # texte_cles, schema_risk_reward
        gs = gridspec.GridSpec(3, 1, figure=fig,
                               height_ratios=[0.10, 0.48, 0.42], hspace=0.03)
        ax_header   = fig.add_subplot(gs[0])
        ax_main     = fig.add_subplot(gs[1])
        ax_subtitle = fig.add_subplot(gs[2])

    writer = FFMpegWriter(fps=FPS, metadata=dict(title=titre),
                          extra_args=['-vcodec', 'libx264', '-pix_fmt', 'yuv420p',
                                      '-crf', '23', '-preset', 'fast'])

    print(f"🎬 Rendu {TOTAL_FRAMES} frames...")

    with writer.saving(fig, output_path, dpi=DPI):
        for frame in range(TOTAL_FRAMES):

            draw_header(ax_header, actif, titre, niveau, fond_type)

            if fond_type == "chandeliers":
                render_chandeliers(ax_chart, candles_full, frame)

            elif fond_type == "indicateur_rsi":
                render_rsi(ax_price, ax_indicator, candles_full, frame)

            elif fond_type == "indicateur_macd":
                render_macd(ax_price, ax_indicator, candles_full, frame)

            elif fond_type == "moyenne_mobile":
                render_moyenne_mobile(ax_chart, candles_full, frame)

            elif fond_type == "texte_cles":
                render_texte_cles(ax_main, frame, concepts)

            elif fond_type == "schema_risk_reward":
                render_schema_risk_reward(ax_main, frame)

            draw_subtitle(ax_subtitle, frame, sous_titres, tags)

            writer.grab_frame()

            if frame % (FPS * 10) == 0:
                print(f"   {int(frame / TOTAL_FRAMES * 100)}%...")

    plt.close(fig)
    print(f"✅ Fond généré : {output_path}")
    return output_path


if __name__ == "__main__":
    generate_background()
