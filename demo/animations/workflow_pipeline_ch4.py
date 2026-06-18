"""Chapitre 4 du workflow BANO : tokenisation."""

from workflow_pipeline_shared import COL_TOK, TOKENS

from anim_common import MONO, chip, titled

# Slide = Scene + points d'arrêt `next_slide()` (présentation au clic). Sous
# `manim` normal, rend la MÊME vidéo continue -> montage/CI inchangés.
from manim_slides import Slide

from manim import (
    DOWN,
    FadeIn,
    FadeOut,
    GREY_B,
    LaggedStart,
    RIGHT,
    Text,
    UP,
    VGroup,
    Write,
)


class Ch4Tokenisation(Slide):
    """Chapitre 4 — on découpe en mots : le texte propre devient des jetons."""

    def construct(self):
        title, sub = titled("On découpe en mots", "tokenisation", chapter=4)
        self.play(Write(title), run_time=1.0)
        self.play(FadeIn(sub), run_time=0.6)

        key = Text(
            "impasse des acacias 01310 saint remy",
            font=MONO,
            font_size=30,
            color=COL_TOK,
        ).move_to(UP * 1.6)
        key_cap = Text(
            "la clé, prête à être découpée", font=MONO, font_size=20, color=GREY_B
        ).next_to(key, DOWN, buff=0.4)
        self.play(FadeIn(key), run_time=0.8)
        self.play(FadeIn(key_cap), run_time=0.5)
        self.wait(0.6)
        self.next_slide()  # pause sur la clé avant découpage

        chips = VGroup(*[chip(t) for t in TOKENS]).arrange(RIGHT, buff=0.25)
        chips.move_to(DOWN * 0.2)
        self.play(
            LaggedStart(*[FadeIn(c, shift=0.4 * DOWN) for c in chips], lag_ratio=0.18),
            run_time=2.0,
        )
        self.wait(0.5)
        self.next_slide()  # pause sur les jetons (mots découpés)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=1.0)
