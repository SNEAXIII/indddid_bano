"""Chapitre 5 du workflow BANO : index trie + postings."""

from workflow_pipeline_shared import COL_SRC, COL_POST, COL_DROP, COL_INDEX

from anim_common import MONO, chip, titled

# Slide = Scene + points d'arrêt `next_slide()` (présentation au clic). Sous
# `manim` normal, rend la MÊME vidéo continue -> montage/CI inchangés.
from manim_slides import Slide

from manim import (
    Arrow,
    Create,
    Cross,
    DOWN,
    FadeIn,
    FadeOut,
    GREY_A,
    GREY_B,
    GREY_C,
    GrowArrow,
    LEFT,
    LaggedStart,
    Rectangle,
    RIGHT,
    SurroundingRectangle,
    Text,
    UP,
    VGroup,
    Write,
)


class Ch5Index(Slide):
    """Chapitre 5 — on range tout dans un index : dictionnaire trié + postings."""

    def construct(self):
        title, sub = titled(
            "On range tout dans un index", "index trié + listes d'adresses", chapter=5
        )
        self.play(Write(title), run_time=1.0)
        self.play(FadeIn(sub), run_time=0.6)

        stack = (
            VGroup(
                *[
                    Rectangle(
                        width=4.3,
                        height=0.26,
                        stroke_width=1,
                        stroke_color=GREY_C,
                        fill_color=COL_SRC,
                        fill_opacity=0.08,
                    )
                    for _ in range(6)
                ]
            )
            .arrange(DOWN, buff=0.1)
            .move_to(LEFT * 2.7 + UP * 0.2)
        )
        stack_lbl = Text("2,2 M lignes", font=MONO, font_size=18, color=GREY_B).next_to(
            stack, UP, buff=0.15
        )
        self.play(FadeIn(stack), FadeIn(stack_lbl), run_time=0.7)

        # 1) Méthode naïve : un curseur descend ligne par ligne -> on le RESSENT lent.
        scan = SurroundingRectangle(stack[0], color=COL_DROP, buff=0.02, stroke_width=3)
        self.play(FadeIn(scan), run_time=0.3)
        for r in stack[1:]:
            self.play(scan.animate.move_to(r), run_time=0.28)
        slow = Text(
            "Lire les adresses une par une = trop lent",
            font=MONO,
            font_size=20,
            color=COL_DROP,
        )
        slow.next_to(stack, DOWN, buff=0.3)
        cross = Cross(stack, stroke_color=COL_DROP, stroke_width=4)
        self.play(Create(cross), FadeIn(slow), run_time=0.7)
        self.wait(1.0)
        self.next_slide()  # pause sur « lire une par une = trop lent »

        # 2) Avec un index : une clé saute DIRECT à la bonne ligne (on montre le saut).
        self.play(FadeOut(VGroup(scan, cross, slow)), run_time=0.4)
        key = chip("remy", font_size=20).move_to(RIGHT * 3.4 + UP * 1.3)
        direct = Text(
            "un index : on va droit\nà la bonne ligne",
            font=MONO,
            font_size=20,
            color=COL_INDEX,
            line_spacing=0.8,
        ).next_to(key, DOWN, buff=0.35)
        hit = SurroundingRectangle(stack[3], color=COL_INDEX, buff=0.02, stroke_width=3)
        jump = Arrow(key.get_left(), hit.get_right(), color=COL_INDEX, buff=0.25)
        self.play(FadeIn(key), run_time=0.5)
        self.play(GrowArrow(jump), Create(hit), run_time=0.7)
        self.play(FadeIn(direct), run_time=0.5)
        self.wait(1.4)
        self.next_slide()  # pause sur « un index = on va droit à la ligne »
        self.play(
            FadeOut(VGroup(stack, stack_lbl, key, direct, hit, jump)), run_time=0.7
        )

        entries = [
            ("acacias", "[0, 1]"),
            ("impasse", "[0]"),
            ("remy", "[0, 1]"),
            ("rue", "[1]"),
            ("saint", "[0, 1]"),
        ]

        def index_row(token, lst):
            return VGroup(
                chip(token, font_size=20),
                Text("→", font=MONO, font_size=20, color=GREY_B),
                Text(lst, font=MONO, font_size=20, color=COL_POST),
            ).arrange(RIGHT, buff=0.2)

        rows = VGroup(*[index_row(t, lst) for t, lst in entries])
        rows.arrange(DOWN, buff=0.24, aligned_edge=LEFT)
        rows.move_to(LEFT * 3.0 + DOWN * 0.2)
        frame = SurroundingRectangle(rows, color=COL_INDEX, buff=0.3)
        idx_title = Text("index trié", font=MONO, font_size=20, color=COL_INDEX)
        idx_title.next_to(frame, UP, buff=0.15)

        # Les numéros pointent vers l'ADRESSE COMPLÈTE (pas juste la voie).
        legend = VGroup(
            Text(
                "0 = Impasse des Acacias 01310 Saint-Rémy",
                font=MONO,
                font_size=16,
                color=GREY_B,
            ),
            Text(
                "1 = Rue des Acacias 01310 Saint-Rémy",
                font=MONO,
                font_size=16,
                color=GREY_B,
            ),
        ).arrange(DOWN, buff=0.2, aligned_edge=LEFT)
        legend.next_to(frame, RIGHT, buff=0.5)
        legend_cap = Text(
            "la clé pointe vers l'adresse entière :", font_size=15, color=GREY_A
        ).next_to(legend, UP, buff=0.25, aligned_edge=LEFT)

        self.play(Create(frame), FadeIn(idx_title), run_time=0.8)
        self.play(
            LaggedStart(*[FadeIn(r, shift=0.2 * RIGHT) for r in rows], lag_ratio=0.2),
            run_time=1.8,
        )
        self.play(FadeIn(legend_cap), FadeIn(legend), run_time=0.7)
        self.wait(0.6)

        box = SurroundingRectangle(rows[0], color=COL_POST, buff=0.1)
        note = Text(
            "« acacias » est dans les 2 adresses",
            font=MONO,
            font_size=20,
            color=COL_POST,
        )
        note.next_to(legend, DOWN, buff=0.7, aligned_edge=LEFT)
        self.play(Create(box), FadeIn(note), run_time=0.9)
        self.wait(2.0)
        self.next_slide()  # pause sur l'index trié + listes d'adresses
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=1.0)
