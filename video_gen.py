import os
import json
import asyncio
import edge_tts
import shutil
from gradio_client import Client, handle_file

# Space officiel SadTalker (talking head audio-driven)
HF_SPACE_ID = "vinthony/SadTalker"
AVATAR_PATH = "assets/1774899221632.png"

async def generate_audio(text):
    print(f"🎙️ Création audio...")
    short_text = text.split('.')[0] + "."
    communicate = edge_tts.Communicate(short_text, "fr-FR-DeniseNeural")
    await communicate.save("voice.mp3")
    print("✅ Audio prêt.")

def animate_character():
    print(f"🚀 Connexion à {HF_SPACE_ID}...")
    try:
        client = Client(HF_SPACE_ID)

        result = client.predict(
            source_image=handle_file(AVATAR_PATH),
            driven_audio=handle_file("voice.mp3"),
            preprocess="crop",
            still_mode=False,
            use_enhancer=False,
            batch_size=1,
            size=256,
            pose_style=0,
            exp_scale=1.0,
            use_ref_video=False,
            ref_video=None,
            ref_info="pose",
            use_idle_mode=False,
            length_of_audio=0,
            blink_every=True,
            fps=int,
            api_name="/test"
        )

        # result est un tuple, la vidéo est le premier élément
        video_path = result[0] if isinstance(result, (list, tuple)) else result
        return video_path

    except Exception as e:
        print(f"❌ Erreur SadTalker : {e}")
        return None

async def main():
    if not os.path.exists("video_metadata.json"):
        print("❌ Erreur : Pas de JSON trouvé.")
        return

    with open("video_metadata.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    # 1. Générer le son
    await generate_audio(data.get("voix_off", "Succès."))

    # 2. Générer l'animation
    video_tmp = animate_character()

    if video_tmp:
        if os.path.exists("avatar_talking.mp4"):
            os.remove("avatar_talking.mp4")
        shutil.copy(video_tmp, "avatar_talking.mp4")
        print("✨ VICTOIRE : avatar_talking.mp4 créé !")
    else:
        print("⚠️ Le serveur est surchargé ou indisponible. Retente dans quelques minutes.")

if __name__ == "__main__":
    asyncio.run(main())
