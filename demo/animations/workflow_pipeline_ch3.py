"""Chapitre 3 du workflow BANO : normalisation."""

from workflow_pipeline_shared import COL_SRC, COL_TOK, COL_DROP

from anim_common import MONO, titled

# Slide = Scene + points d'arrêt `next_slide()` (présentation au clic). Sous
# `manim` normal, rend la MÊME vidéo continue -> montage/CI inchangés.
from manim_slides import Slide

from manim import (
    Arrow,
    DOWN,
    FadeIn,
    FadeOut,
    FadeTransform,
    GREY_A,
    GREY_B,
    GrowArrow,
    LEFT,
    LaggedStart,
    RED,
    RIGHT,
    Text,
    UP,
    VGroup,
    WHITE,
    Write,
)


class Ch3Normalisation(Slide):
    """Chapitre 3 — deux versions d'une adresse : la version affichée (gardée)
    et la clé normalisée (pour comparer). Elles coexistent."""

    def construct(self):
        title, sub = titled("Deux versions d'une adresse", "normalisation", chapter=3)
        self.play(Write(title), run_time=1.0)
        self.play(FadeIn(sub), run_time=0.6)

        # Adresses décalées à droite pour laisser la place aux libellés de rôle
        # à GAUCHE de chaque ligne.
        disp = Text(
            "Impasse des Acacias 01310 Saint-Rémy",
            font=MONO,
            font_size=26,
            color=COL_SRC,
        ).move_to(UP * 1.5 + RIGHT * 0.7)
        disp_cap = (
            VGroup(
                Text("affichage réel", font=MONO, font_size=18, color=COL_SRC),
                Text(
                    "utilisé tel par le programme",
                    font=MONO,
                    font_size=14,
                    color=GREY_B,
                ),
            )
            .arrange(DOWN, buff=0.1)
            .next_to(disp, LEFT, buff=0.4)
        )
        self.play(FadeIn(disp_cap), FadeIn(disp), run_time=0.8)
        self.wait(0.6)
        self.next_slide()  # pause sur l'adresse affichée avant normalisation

        keyP = DOWN * 0.3 + RIGHT * 0.7

        def kline(txt, color, t2c=None):
            return Text(
                txt, font=MONO, font_size=26, color=color, t2c=t2c or {}
            ).move_to(keyP)

        # Construit un t2c qui met EN ROUGE les caractères normalisés à ce passage.
        def red(*idxs):
            return {f"[{i}:{i + 1}]": RED for i in idxs}

        key = disp.copy()
        self.play(key.animate.move_to(keyP), run_time=0.8)

        lbl = None

        def npass(label, txt, color, t2c=None, rt=0.9):
            nonlocal key, lbl
            new_lbl = Text(label, font=MONO, font_size=20, color=COL_DROP).next_to(
                key, DOWN, buff=0.5
            )
            if lbl is None:
                self.play(FadeIn(new_lbl), run_time=0.4)
            else:
                self.play(FadeOut(lbl), FadeIn(new_lbl), run_time=0.4)
            lbl = new_lbl
            nw = kline(txt, color, t2c=t2c)
            self.play(FadeTransform(key, nw), run_time=rt)
            key = nw
            self.wait(0.6)

        # rouge sur les lettres qui changent : majuscules abaissées (I, A, S, R)…
        npass(
            "On supprime les majuscules",
            "impasse des acacias 01310 saint-rémy",
            COL_SRC,
            t2c=red(0, 12, 26, 32),
        )
        # …puis l'accent retiré (é → e)…
        npass(
            "On retire les accents",
            "impasse des acacias 01310 saint-remy",
            COL_SRC,
            t2c=red(33),
        )
        # …le tiret devient une espace (rien à colorer : ce n'est pas une lettre).
        npass(
            "On remplace le tiret par un espace",
            "impasse des acacias 01310 saint remy",
            COL_TOK,
        )
        self.play(FadeOut(lbl), run_time=0.3)

        key_cap = (
            VGroup(
                Text("la clé normalisée", font=MONO, font_size=18, color=COL_TOK),
            )
            .arrange(DOWN, buff=0.1)
            .next_to(key, LEFT, buff=0.4)
        )
        link = Text("même adresse, deux usages", font_size=20, color=GREY_A).move_to(
            UP * 0.6 + RIGHT * 0.7
        )
        self.play(FadeIn(key_cap), FadeIn(link), run_time=0.7)
        self.wait(1.6)
        self.next_slide()  # pause sur affichage + clé normalisée côte à côte

        self.play(FadeOut(VGroup(disp, disp_cap, key, key_cap, link)), run_time=0.7)
        demo_t = Text(
            "En écrivant le même mot différemment, même clé", font_size=24, color=GREY_A
        ).move_to(UP * 1.4)
        variants = (
            VGroup(
                Text("Rémy", font=MONO, font_size=40, color=COL_SRC),
                Text("RÉMY", font=MONO, font_size=40, color=COL_SRC),
                Text("remy", font=MONO, font_size=40, color=COL_SRC),
            )
            .arrange(DOWN, buff=0.45)
            .move_to(LEFT * 3.3)
        )
        target = Text("remy", font=MONO, font_size=44, color=COL_TOK).move_to(
            RIGHT * 3.0
        )
        tgt_cap = Text(
            "la clé normalisée", font=MONO, font_size=20, color=COL_TOK
        ).next_to(target, DOWN, buff=0.3)
        # Bleu = ce que tape l'utilisateur ; flèche blanche = on aboutit à la clé.
        var_cap = Text(
            "ce que l'utilisateur écrit", font_size=20, color=COL_SRC
        ).next_to(variants, DOWN, buff=0.35)
        flow = Arrow(variants.get_right(), target.get_left(), color=WHITE, buff=0.4)
        self.play(FadeIn(demo_t), run_time=0.5)
        self.play(
            LaggedStart(
                *[FadeIn(v, shift=0.2 * RIGHT) for v in variants], lag_ratio=0.25
            ),
            run_time=1.2,
        )
        self.play(FadeIn(var_cap), run_time=0.4)
        self.play(GrowArrow(flow), run_time=0.5)
        self.wait(0.5)
        copies = [v.copy() for v in variants]
        self.add(*copies)
        self.play(
            LaggedStart(
                *[
                    c.animate.scale(0.3).move_to(target.get_center()).set_opacity(0.0)
                    for c in copies
                ],
                lag_ratio=0.2,
            ),
            run_time=1.4,
        )
        self.remove(*copies)
        self.play(
            FadeIn(target),
            FadeIn(tgt_cap),
            run_time=0.9,
        )
        self.wait(1.0)

        why = (
            Text(
                "la clé est un mot normalisé, pour comparer les variantes",
                font_size=20,
                color=GREY_B,
            )
            .next_to(VGroup(variants, target), DOWN, buff=0.9)
            .set_x(0)
        )
        self.play(FadeIn(why), run_time=0.7)
        self.wait(2.0)
        self.next_slide()  # pause sur « variantes → même clé »
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=1.0)
