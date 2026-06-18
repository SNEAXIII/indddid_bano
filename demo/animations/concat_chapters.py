"""Montage : concatène les 11 chapitres de workflow_pipeline en un seul MP4.

Usage :  uv run python concat_chapters.py [qualité]     (défaut 1080p60)
Exemple : uv run python concat_chapters.py 480p15

PyAV est déjà embarqué par Manim : pas besoin d'un ffmpeg système (le rendu
Manim n'en a pas besoin non plus). Le script ré-encode chaque clip en H.264
dans un conteneur unique — robuste même si les clips diffèrent légèrement.
"""

import sys
from fractions import Fraction
from pathlib import Path

import av

# Ordre des chapitres = ordre du film. Chaque chapitre est une Scene dans son
# propre module workflow_pipeline_ch<N>.py ; Manim range donc son MP4 sous
# media/videos/workflow_pipeline_ch<N>/<qualité>/<Scene>.mp4. (module, Scene).
# Doit rester aligné avec les ch files et la liste .PHONY du Makefile.
CHAPTERS = [
    ("workflow_pipeline_ch1", "Ch1Apercu"),
    ("workflow_pipeline_ch2", "Ch2Donnees"),
    ("workflow_pipeline_ch3", "Ch3Extraction"),
    ("workflow_pipeline_ch4", "Ch4Normalisation"),
    ("workflow_pipeline_ch5", "Ch5Tokenisation"),
    ("workflow_pipeline_ch6", "Ch6Index"),
    ("workflow_pipeline_ch7", "Ch7Fst"),
    ("workflow_pipeline_ch8", "Ch8Fichiers"),
    ("workflow_pipeline_ch9", "Ch9Requete"),
    ("workflow_pipeline_ch10", "Ch10Levenshtein"),
    ("workflow_pipeline_ch11", "Ch11Scoring"),
]


def main() -> int:
    quality = sys.argv[1] if len(sys.argv) > 1 else "1080p60"
    here = Path(__file__).parent
    videos = here / "media" / "videos"
    clips = [videos / module / quality / f"{scene}.mp4" for module, scene in CHAPTERS]

    missing = [c for c in clips if not c.exists()]
    if missing:
        print(f"MP4 manquants sous {videos} (rendre les chapitres d'abord) :")
        for m in missing:
            print("  -", m.relative_to(videos))
        print("\nLance d'abord :  make anim-workflow QUALITY=<l|h>")
        return 1

    out_path = here / "media" / "workflow_montage.mp4"
    out = av.open(str(out_path), mode="w")
    out_stream = None
    time_base = None
    frame_index = 0  # compteur global -> pts monotones sur tout le film

    for clip in clips:
        inp = av.open(str(clip))
        in_stream = inp.streams.video[0]
        if out_stream is None:
            fps = int(in_stream.average_rate)
            time_base = Fraction(1, fps)
            out_stream = out.add_stream("h264", rate=fps)
            out_stream.width = in_stream.codec_context.width
            out_stream.height = in_stream.codec_context.height
            out_stream.pix_fmt = "yuv420p"
            out_stream.codec_context.time_base = time_base
        for frame in inp.decode(in_stream):
            # Chaque clip repart de 0 : on réécrit un pts global croissant
            # (sinon DTS non monotones au remux -> ArgumentError).
            frame.pts = frame_index
            frame.time_base = time_base
            frame_index += 1
            for packet in out_stream.encode(frame):
                out.mux(packet)
        inp.close()

    # Vider l'encodeur (frames en attente) puis fermer le conteneur.
    for packet in out_stream.encode():
        out.mux(packet)
    out.close()

    print("Montage écrit :", out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
