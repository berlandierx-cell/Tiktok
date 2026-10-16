"""TikTok-first preview from a pre-recorded French voice and validated metadata.
Deliberately does not contain any TikTok, uploader, Gemini or network code.
"""
from pathlib import Path
import json, subprocess, math, os, tempfile
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / ".preview_frames"
WORK.mkdir(exist_ok=True)
VOICE = ROOT / "voice.mp3"
OUTPUT = ROOT / "final_video.mp4"
METADATA = ROOT / "video_metadata.json"

FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_OPTIONS = [
    "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]
FONT_BOLD = next((x for x in FONT_OPTIONS if Path(x).exists()), FONT_BOLD)

W, H = 720, 1280
BG = "#080D18"
FG = "#F5F7FF"
BLUE = "#6CCFFF"
GREEN = "#63FFC4"
RED = "#FF5B75"
YELLOW = "#EBFF70"

# Narrative is a concise visual demonstration, not a 1-minute lecture.
# All values below are illustrative, NOT market quotes or trade recommendations.
STORY = [
    ("LE PARADOXE", ["7 / 10", "TRADES PERDUS", "ET TU GAGNES ?"], RED, 2.4),
    ("REGARDE BIEN", ["10 TRADES", "100 €", "RISQUÉS / TRADE"], YELLOW, 2.8),
    ("ÉTAPE 1", ["7 PERTES", "7 × -100 €", "-700 €"], RED, 3.7),
    ("ÉTAPE 2", ["3 GAINS", "3 × +300 €", "+900 €"], GREEN, 3.3),
    ("LE BILAN", ["-700 + 900", "= +200 €", "AVANT FRAIS"], YELLOW, 3.3),
    ("LE PARADOXE", ["70 %", "DE TRADES", "PERDANTS"], RED, 2.7),
    ("LE SECRET", ["RATIO", "GAIN / PERTE", "1 : 3"], BLUE, 3.0),
    ("ATTENTION", ["PAS DE MAGIE", "STOPS RESPECTÉS", "OBJECTIFS ATTEINTS"], YELLOW, 3.6),
    ("LE PIÈGE", ["90 %", "DE RÉUSSITE ?", "ET ALORS ?"], RED, 3.0),
    ("POSE LA QUESTION", ["COMBIEN TU", "PERDS QUAND", "TU AS TORT ?"], GREEN, 3.1),
    ("À RETENIR", ["RISQUE.", "RATIO.", "DISCIPLINE."], BLUE, 2.5),
]

def sh(*args):
    subprocess.run(list(args), check=True, stdout=subprocess.DEVNULL)

def duration(path):
    return float(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        text=True).strip())

def f(sz, bold=True):
    return ImageFont.truetype(FONT_BOLD if bold else FONT_REG, sz)

def center(draw, value, y, sz, color=FG, bold=True):
    font = f(sz, bold)
    while draw.textbbox((0,0), value, font=font)[2] > 645 and sz > 20:
        sz -= 2
        font = f(sz, bold)
    draw.text((W//2,y), value, anchor="mt", font=font, fill=color)

def scene(index, title, lines, accent):
    img=Image.new("RGB",(W,H),BG)
    d=ImageDraw.Draw(img)
    for x in range(20,W,66):
        d.line((x,170,x,1130),fill="#162130",width=1)
    for y in range(170,1130,66):
        d.line((22,y,698,y),fill="#162130",width=1)
    d.rounded_rectangle((36,62,188,108),radius=15,fill="#17283B",outline="#3A5367",width=2)
    d.text((49,75),"TRADE / LAB",font=f(18),fill=BLUE)
    d.text((656,84),f"{index+1:02d}/{len(STORY):02d}",anchor="ra",font=f(18),fill="#9EABB9")
    d.text((44,190),title,font=f(25),fill=accent)
    ys=[340,534,730] if len(lines)==3 else [360+i*170 for i in range(len(lines))]
    for j,(s,y) in enumerate(zip(lines,ys)):
        sz=100 if j in (0,2) else 62
        if "%" in s or "100 €" in s or ("+" in s and "€" in s):
            sz=116
        color=accent if (j==2 or (j==0 and index in (0,5,8))) else FG
        center(d,s,y,sz,color)
    d.line((35,1143,684,1143),fill="#39485B",width=2)
    d.text((37,1168),"TRADING DÉCRYPTÉ",font=f(19),fill=FG)
    d.text((37,1207),"EXEMPLE FICTIF • PAS UN CONSEIL",font=f(15,False),fill="#9EAABA")
    d.rounded_rectangle((35,1241,684,1248),radius=3,fill="#203347")
    d.rounded_rectangle((35,1241,35+round(649*(index+1)/len(STORY)),1248),
                        radius=3,fill=GREEN)
    return img

def main():
    metadata=json.loads(METADATA.read_text(encoding="utf-8"))
    assert metadata.get("publication_autorisee") is False, "Preview exige une autorisation de publication false"
    assert VOICE.exists() and VOICE.stat().st_size>1000, "voice.mp3 absent"
    audio_s=duration(VOICE)
    # Keep all content synchronized to real narration, not a hardcoded 60s.
    nominal=sum(s[3] for s in STORY)
    factor=audio_s/nominal
    clips=[]
    for i,(header,lines,col,secs) in enumerate(STORY):
        png=WORK/f"card_{i:02}.png"
        mp4=WORK/f"clip_{i:02}.mp4"
        scene(i,header,lines,col).save(png)
        secs=round(secs*factor,3)
        z="min(zoom+0.00135,1.12)" if i%2==0 else "if(eq(on,0),1.09,max(zoom-0.0012,1.00))"
        vf=(f"zoompan=z='{z}':x='(iw-iw/zoom)/2':"
            f"y='(ih-ih/zoom)/2':d=1:s={W}x{H}:fps=30,format=yuv420p")
        sh("ffmpeg","-hide_banner","-loglevel","error","-y","-loop","1",
           "-framerate","30","-i",str(png),"-vf",vf,"-t",str(secs),
           "-an","-c:v","libx264","-preset","fast","-crf","22","-r","30",str(mp4))
        clips.append(mp4)
    listfile=WORK/"clips.txt"
    listfile.write_text("".join(f"file '{p}'\n" for p in clips),encoding="utf-8")
    silent=WORK/"silent.mp4"
    sh("ffmpeg","-hide_banner","-loglevel","error","-y",
       "-f","concat","-safe","0","-i",str(listfile),"-c","copy",str(silent))
    # Voice remains the central element. Avoid competing music and fake stats.
    sh("ffmpeg","-hide_banner","-loglevel","error","-y",
       "-i",str(silent),"-i",str(VOICE),
       "-map","0:v:0","-map","1:a:0",
       "-c:v","copy","-c:a","aac","-b:a","192k",
       "-af","loudnorm=I=-16:TP=-1.5:LRA=9",
       "-t",str(audio_s),"-movflags","+faststart",str(OUTPUT))
    assert OUTPUT.exists() and OUTPUT.stat().st_size>20000
    print(f"Final preview (non publiée) : {OUTPUT} ({audio_s:.1f} s)")
if __name__=="__main__":
    main()
