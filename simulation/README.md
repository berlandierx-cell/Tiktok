# Simulation TikTok avec ChatGPT (sans publication)

Cette branche permet de tester une video educative **sans appeler Gemini et sans envoyer quoi que ce soit sur TikTok**.

## Ce qui change

- `simulation/video_metadata_chatgpt.json` contient un script redige pour cette simulation, et non genere via Gemini.
- `.github/workflows/preview_chatgpt.yml` est **manuel uniquement** (`workflow_dispatch`). Il n'a **aucune** etape `uploader.py`, n'utilise **aucun** secret TikTok, ne fait **aucun** `git push` et livre `final_video.mp4` comme artefact GitHub Actions (7 jours).
- `background.py` mesure maintenant la duree de `voice.mp3` pour eviter un fond anime arbitrairement fixe a 60 secondes.

## Executer la preview sur le runner

La commande `Actions > TikTok - Preview ChatGPT (sans publication) > Run workflow` est disponible une fois le fichier workflow present sur la branche par defaut de GitHub (en fusionnant seulement ce workflow ou la PR). Choisir ensuite la branche de simulation si necessaire.

Le runner self-hosted doit disposer de ffmpeg/ffprobe et de Wav2Lip avec son checkpoint sous `$HOME/Wav2Lip/checkpoints/wav2lip.pth`.

## Important

Le MP4 de demonstration fourni dans la conversation a ete rendu independamment (animation vectorielle + voix locale + musique originale) pour permettre de voir un resultat immediat. Le rendu GitHub utilise toujours l'habillage et l'avatar Wav2Lip du depot, donc son apparence sera differente.

La publication quotidienne existante (`daily_post.yml`) sur `main` **n'a pas ete modifiee**. Ne pas lancer ce workflow pour une simulation. Pour securiser egalement la production, la prochaine etape conseillee est de rendre toute publication dependante d'une validation explicite.

Aucun test sur le runner n'a ete lance lors de la preparation de cette branche.
