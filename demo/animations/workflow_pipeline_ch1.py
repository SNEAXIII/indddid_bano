"""Chapitre 1 du workflow BANO : donnees source."""

from workflow_pipeline_shared import COL_SRC, COL_TOK


from anim_common import MONO, file_box, titled

# Slide = Scene + points d'arrêt `next_slide()` (présentation au clic). Sous
# `manim` normal, rend la MÊME vidéo continue -> montage/CI inchangés.
from manim_slides import Slide

from manim import (
    Arrow,
    Create,
    DOWN,
    FadeIn,
    FadeOut,
    GREY_A,
    GREY_B,
    GREY_D,
    GrowArrow,
    LEFT,
    LaggedStart,
    Line,
    Text,
    VGroup,
    Write,
)


class Ch1Donnees(Slide):
    """Chapitre 1 — d'où viennent les adresses : le fichier national BANO,
    avec un APERÇU RÉEL de son contenu (beaucoup de colonnes inutiles)."""

    def construct(self):
        title, sub = titled(
            "D'où viennent les adresses", "le fichier national BANO complet", chapter=1
        )
        self.play(Write(title), run_time=1.0)
        self.play(FadeIn(sub), run_time=0.6)

        fb = file_box("full.csv", COL_SRC, width=3.2)
        fb.next_to(sub, DOWN, buff=0.45)
        self.play(FadeIn(fb, shift=0.3 * DOWN), run_time=0.9)
        self.wait(0.4)

        useful = {
            "Impasse des Acacias": COL_SRC,
            "01400": COL_SRC,
            "L'Abergement-Clémenciat": COL_SRC,
        }
        raw = [
            "010010005-103  103  Impasse des Acacias  01400  L'Abergement-Clémenciat  OSM  46.147615  4.924047",
            "010010005-104  104  Impasse des Acacias  01400  L'Abergement-Clémenciat  OSM  46.147662  4.924207",
            "010010005-26   26   Impasse des Acacias  01400  L'Abergement-Clémenciat  OSM  46.146906  4.924205",
        ]

        cols = [
            (0, "id"),
            (15, "num"),
            (20, "voie"),
            (41, "cp"),
            (48, "ville"),
            (73, "src"),
            (78, "lat"),
            (89, "lon"),
        ]
        hdr = [" "] * 96
        for off, label in cols:
            for i, ch in enumerate(label):
                hdr[off + i] = ch
        header_line = Text(
            "".join(hdr).rstrip(),
            font=MONO,
            font_size=18,
            color=GREY_A,
            t2c={"voie": COL_SRC, "cp": COL_SRC, "ville": COL_SRC},
        )
        data_rows = VGroup(
            *[
                Text(line, font=MONO, font_size=18, color=GREY_B, t2c=useful)
                for line in raw
            ]
        )
        data_rows.arrange(DOWN, buff=0.28, aligned_edge=LEFT)
        data_rows.next_to(header_line, DOWN, buff=0.22, aligned_edge=LEFT)
        table = VGroup(header_line, data_rows)
        if table.width > 12.6:
            table.scale_to_fit_width(12.6)
        table.next_to(fb, DOWN, buff=0.5)
        sep = Line(
            header_line.get_left(),
            header_line.get_right(),
            color=GREY_D,
            stroke_width=2,
        ).next_to(header_line, DOWN, buff=0.06)
        arrow = Arrow(fb.get_bottom(), table.get_top(), color=GREY_B, buff=0.15)

        self.play(GrowArrow(arrow), run_time=0.7)
        self.play(FadeIn(header_line), Create(sep), run_time=0.7)
        self.play(
            LaggedStart(
                *[FadeIn(r, shift=0.1 * DOWN) for r in data_rows], lag_ratio=0.2
            ),
            run_time=1.4,
        )
        self.wait(0.6)
        self.next_slide()  # pause sur le fichier brut (colonnes inutiles)

        legend = Text(
            "en bleu : voie · code postal · ville",
            font_size=22,
            color=GREY_A,
            t2c={"voie · code postal · ville": COL_SRC},
        )
        legend.next_to(table, DOWN, buff=0.45)
        note = VGroup(
            Text(
                "Fichier complet : 26,5 millions d'adresses  ~  2 Go",
                font=MONO,
                font_size=24,
                color=COL_TOK,
            ),
            Text(
                "on veut juste l'adresse — pas la géoloc (lat/lon) ni le reste",
                font_size=20,
                color=GREY_B,
            ),
        ).arrange(DOWN, buff=0.18)
        note.next_to(legend, DOWN, buff=0.35)

        self.play(FadeIn(legend), run_time=0.7)
        self.play(FadeIn(note), run_time=0.7)
        self.wait(2.0)
        self.next_slide()  # pause sur le constat « 2 Go, on ne garde que l'adresse »
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=1.0)
