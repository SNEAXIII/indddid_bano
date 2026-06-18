"""Extrait une image d'un chapitre rendu (vérif visuelle sans ouvrir le lecteur).

Usage :  uv run python grab_frame.py <Scene> [--quality 480p15] [--at 0.95] [--out chemin.png]

Défauts : qualité 480p15, frame à 95 % du clip, sortie media/frames/<Scene>.png.
Passe par le Makefile : `make anim-frame ANIM_SCENE=Ch8Scoring QUALITY=l`.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import av

# QUALITY (l/m/h/k) -> dossier média Manim, aligné sur le Makefile.
QDIR = {"l": "480p15", "m": "720p30", "h": "1080p60", "k": "2160p60"}


def main() -> int:
    p = argparse.ArgumentParser(description="Extrait une frame d'un chapitre rendu.")
    p.add_argument("scene", help="Nom de la classe Scene (ex. Ch8Scoring)")
    p.add_argument(
        "--quality",
        default="480p15",
        help="Dossier média ou raccourci l/m/h/k (defaut 480p15)",
    )
    p.add_argument(
        "--at",
        type=float,
        default=0.95,
        help="Position dans le clip, 0..1 (defaut 0.95)",
    )
    p.add_argument("--out", default=None, help="Chemin PNG de sortie")
    args = p.parse_args()

    here = Path(__file__).parent
    qdir = QDIR.get(args.quality, args.quality)
    # Chaque chapitre vit dans son module workflow_pipeline_ch<N>.py -> Manim
    # range le MP4 sous media/videos/<module>/<qdir>/<Scene>.mp4. On cherche la
    # scène dans tous les dossiers workflow_pipeline*/.
    videos = here / "media" / "videos"
    hits = sorted(videos.glob(f"*/{qdir}/{args.scene}.mp4"))
    if not hits:
        print(
            f"MP4 absent pour {args.scene} (qualité {qdir}) sous {videos}\n"
            f"Rends d'abord le chapitre (make anim-wf-...)."
        )
        return 1
    mp4 = hits[0]

    out = (
        Path(args.out) if args.out else here / "media" / "frames" / f"{args.scene}.png"
    )
    out.parent.mkdir(parents=True, exist_ok=True)

    container = av.open(str(mp4))
    total = container.streams.video[0].frames or 0
    container.close()

    target = int(total * args.at) if total else 0
    container = av.open(str(mp4))
    stream = container.streams.video[0]
    for i, frame in enumerate(container.decode(stream)):
        if i == target:
            frame.to_image().save(str(out))
            break
    container.close()

    print(f"Frame {target}/{total} -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
