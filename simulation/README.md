# Simulation TikTok V2 — ChatGPT, sans Gemini, sans publication

Branche : `simulation-chatgpt-preview-20261016`.
PR : https://github.com/berlandierx-cell/Tiktok/pull/1

## Modifications

- Script de **98 mots** écrit manuellement par ChatGPT dans `simulation/video_metadata_chatgpt.json`.
- Voix française plus naturelle prévue via Edge TTS : Vivienne Multilingual, repli Denise, débit +15 %.
- Nouveau montage rapide dans `simulation/fast_preview.py` : 11 plans, gros chiffres, alternance rouge/vert, coupes courtes et zooms.
- Durée du montage synchronisée sur la **durée réelle de la voix** détectée avec ffprobe.
- Suppression de l'introduction de cinq secondes, de l'outro longue et du passage Wav2Lip dans le workflow de prévisualisation : l'image est désormais dédiée à l'information.
- Contrôle strict du champ `publication_autorisee: false` : toute autre valeur empêche le rendu.
- Artefact : `final_video.mp4` disponible 7 jours après le job.

## Sécurité

Le workflow `.github/workflows/preview_chatgpt.yml` n'utilise jamais `uploader.py`, aucun token TikTok, aucun secret Gemini, aucune étape de publication. Les fichiers de la branche `main` n'ont pas été modifiés.

## Exécution

Le workflow est disponible une fois enregistré par GitHub pour cette branche / PR ; il utilise un runner auto-hébergé équipé de Python et de FFmpeg. Edge TTS nécessite la connectivité de sortie du runner.

Le premier rendu V2 fourni dans la conversation est une **maquette texte + musique originale**, sans narration : la narration premium a été créée dans Runway mais n'a pas pu être téléchargée dans le conteneur local. Ne pas confondre cette maquette et le MP4 final généré par le workflow.

**Statut des tests :** branche et code préparés ; validation d'intégration sur le runner non confirmée. Aucune publication TikTok n'a été effectuée lors de cette simulation.
