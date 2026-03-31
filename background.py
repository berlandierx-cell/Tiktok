import json
import random
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.animation import FFMpegWriter
import matplotlib.gridspec as gridspec

# Dimensions TikTok 9:16
WIDTH_PX = 1080
HEIGHT_PX = 1920
DPI = 100
FIG_W = WIDTH_PX / DPI
FIG_H = HEIGHT_PX / DPI

DURATION_SEC = 60
FPS = 30
TOTAL_FRAMES = DURATION_SEC * FPS

# Palette dark trading
BG_COLOR = "#0a0e1a"
GRID_COLOR = "#1a2035"
CANDLE_UP = "#00e676"
CANDLE_DOWN = "#ff1744"
TEXT_COLOR = "#e0e0e0"
ACCENT_COLOR = "#00bcd4"
SUBTITLE_BG = "#000000cc"


def generate_candles(n=60, base=100.0, volatility=0.02):
    """Génère des bougies OHLC simulées réalistes."""
    candles = []
    price = base
    for _ in range(n):
        open_ = price
        change = random.gauss(0, volatility)
        close = open_ * (1 + change)
        high = max(open_, close) * (1 + abs(random.gauss(0, volatility * 0.5)))
        low = min(open_, close) * (1 - abs(random.gauss(0, volatility * 0.5)))
        candles.append((open_, high, low, close))
        price = close
    return candles


def draw_candles(ax, candles, highlight_last=5):
    """Dessine les chandeliers sur l'axe."""
    ax.clear()
    ax.set_facecolor(BG_COLOR)

    for i, (o, h, l, c) in enumerate(candles):
        color = CANDLE_UP if c >= o else CANDLE_DOWN
        alpha = 1.0 if i >= len(candles) - highlight_last else 0.7

        # Corps
        body_bottom = min(o, c)
        body_height = abs(c - o) if abs(c - o) > 0.001 else 0.001
        rect = mpatches.Rectangle(
            (i - 0.35, body_bottom), 0.7, body_height,
            color=color, alpha=alpha, zorder=3
        )
        ax.add_patch(rect)

        # Mèches
        ax.plot([i, i], [l, h], color=color, linewidth=1, alpha=alpha, zorder=2)

    # Style axes
    prices = [c[3] for c in candles]
    price_min = min(c[2] for c in candles)
    price_max = max(c[1] for c in candles)
    margin = (price_max - price_min) * 0.1
    ax.set_xlim(-1, len(candles) + 1)
    ax.set_ylim(price_min - margin, price_max + margin)
    ax.set_facecolor(BG_COLOR)
    ax.tick_params(colors=TEXT_COLOR, labelsize=8)
    ax.yaxis.set_tick_params(labelcolor=ACCENT_COLOR)
    ax.xaxis.set_visible(False)

    # Grille
    ax.grid(True, color=GRID_COLOR, linewidth=0.5, alpha=0.8)
    ax.spines['bottom'].set_color(GRID_COLOR)
    ax.spines['top'].set_color(GRID_COLOR)
    ax.spines['left'].set_color(GRID_COLOR)
    ax.spines['right'].set_color(GRID_COLOR)

    # Prix courant
    last_price = prices[-1]
    ax.axhline(y=last_price, color=ACCENT_COLOR, linewidth=0.8,
               linestyle='--', alpha=0.6, zorder=1)
    ax.text(len(candles) + 0.3, last_price, f"{last_price:.4f}",
            color=ACCENT_COLOR, fontsize=8, va='center', fontweight='bold')


def get_subtitle_for_frame(frame, sous_titres, total_frames):
    """Retourne le sous-titre correspondant au frame actuel."""
    if not sous_titres:
        return ""
    idx = int((frame / total_frames) * len(sous_titres))
    idx = min(idx, len(sous_titres) - 1)
    return sous_titres[idx]


def generate_background(metadata_path="video_metadata.json", output_path="background.mp4"):
    with open(metadata_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    actif = data.get("actif", "BTC/USDT")
    titre = data.get("titre", "Trading")
    niveau = data.get("niveau", "débutant")
    categorie = data.get("categorie", "crypto")
    sous_titres = data.get("sous_titres", [])

    print(f"🎨 Génération du fond : {actif} | {len(sous_titres)} sous-titres")

    # Volatilité selon l'actif
    volatility = 0.008 if "USD" in actif and "/" in actif and "USDT" not in actif else 0.025
    base_price = 65000 if "BTC" in actif else (3500 if "ETH" in actif else 1.08 if "EUR" in actif else 100)

    # Générer les données de marché
    candles_full = generate_candles(n=80, base=base_price, volatility=volatility)

    # Setup figure
    fig = plt.figure(figsize=(FIG_W, FIG_H), dpi=DPI, facecolor=BG_COLOR)
    gs = gridspec.GridSpec(3, 1, figure=fig,
                           height_ratios=[0.12, 0.55, 0.33],
                           hspace=0.02)

    ax_header = fig.add_subplot(gs[0])
    ax_chart = fig.add_subplot(gs[1])
    ax_subtitle = fig.add_subplot(gs[2])

    for ax in [ax_header, ax_subtitle]:
        ax.set_facecolor(BG_COLOR)
        ax.axis('off')

    # Writer FFmpeg
    writer = FFMpegWriter(fps=FPS, metadata=dict(title=titre),
                          extra_args=['-vcodec', 'libx264', '-pix_fmt', 'yuv420p',
                                      '-crf', '23', '-preset', 'fast'])

    print(f"🎬 Rendu {TOTAL_FRAMES} frames à {FPS}fps...")

    with writer.saving(fig, output_path, dpi=DPI):
        for frame in range(TOTAL_FRAMES):
            progress = frame / TOTAL_FRAMES

            # Fenêtre glissante de chandeliers (40 visibles)
            window = 40
            start_idx = min(int(progress * (len(candles_full) - window)), len(candles_full) - window)
            visible_candles = candles_full[start_idx:start_idx + window]

            # --- HEADER ---
            ax_header.clear()
            ax_header.set_facecolor(BG_COLOR)
            ax_header.axis('off')

            # Badge niveau
            niveau_colors = {"débutant": "#4caf50", "intermédiaire": "#ff9800", "confirmé": "#f44336"}
            niv_color = niveau_colors.get(niveau, "#4caf50")

            ax_header.text(0.05, 0.75, actif, transform=ax_header.transAxes,
                          color=ACCENT_COLOR, fontsize=22, fontweight='bold', va='top')
            ax_header.text(0.05, 0.25, titre.upper(), transform=ax_header.transAxes,
                          color=TEXT_COLOR, fontsize=11, va='top', alpha=0.9)
            ax_header.text(0.95, 0.75, f"● {niveau.upper()}", transform=ax_header.transAxes,
                          color=niv_color, fontsize=10, fontweight='bold', va='top', ha='right')

            # Ligne séparatrice
            ax_header.axhline(y=0.05, color=ACCENT_COLOR, linewidth=1, alpha=0.4)

            # --- GRAPHIQUE ---
            draw_candles(ax_chart, visible_candles, highlight_last=5)

            # Indicateur de progression (barre en bas du graphique)
            ax_chart.axvline(x=int(progress * window), color=ACCENT_COLOR,
                            linewidth=1, alpha=0.3, linestyle=':')

            # --- SOUS-TITRES ---
            ax_subtitle.clear()
            ax_subtitle.set_facecolor(BG_COLOR)
            ax_subtitle.axis('off')

            subtitle = get_subtitle_for_frame(frame, sous_titres, TOTAL_FRAMES)
            if subtitle:
                # Fond semi-transparent pour le texte
                ax_subtitle.text(0.5, 0.6, subtitle,
                                transform=ax_subtitle.transAxes,
                                color='white', fontsize=18, fontweight='bold',
                                ha='center', va='center',
                                wrap=True,
                                bbox=dict(boxstyle='round,pad=0.4',
                                         facecolor='#000000',
                                         alpha=0.7,
                                         edgecolor=ACCENT_COLOR,
                                         linewidth=1))

            # Tags en bas
            tags = data.get("tags", "#trading")
            ax_subtitle.text(0.5, 0.1, tags,
                           transform=ax_subtitle.transAxes,
                           color=ACCENT_COLOR, fontsize=9,
                           ha='center', va='bottom', alpha=0.7)

            writer.grab_frame()

            if frame % 150 == 0:
                print(f"   {int(progress * 100)}%...")

    plt.close(fig)
    print(f"✅ Fond généré : {output_path}")
    return output_path


if __name__ == "__main__":
    generate_background()
