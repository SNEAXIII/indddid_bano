"""Chapitre 1 du workflow BANO : vue d'ensemble."""

from anim_common import MONO, titled

from manim import (
    Create,
    DOWN,
    FadeIn,
    FadeOut,
    GREY_A,
    GREY_D,
    LEFT,
    LaggedStart,
    Line,
    RIGHT,
    Scene,
    Text,
    UP,
    VGroup,
    Write,
)


class Ch1Apercu(Scene):
    """Chapitre 1 — la vue d'ensemble : les grandes étapes en feuille de route."""

    def construct(self):
        title, sub = titled(
            "Étape de construction de l'application de démo",
            "vue d'ensemble, étape par étape",
            chapter=1,
        )
        self.play(Write(title), run_time=1.0)
        self.play(FadeIn(sub), run_time=0.6)

        etapes = [
            "1.   Données source : fichier national BANO",
            "2.   Extraction des adresses utiles (streets.csv)",
            "3.   Normalisation des adresses",
            "4.   Tokenisation des adresses",
            "5.   Construction de l'index trié",
            "6.   Le dictionnaire en arbre partagé (FST)",
            "7.   Emballage de l'index en fichiers binaires",
            "8.   La requête de l'utilisateur",
            "9.   Recherche tolérante aux fautes (Levenshtein)",
            "10.  Scoring et classement des résultats",
            "11.  Affichage des adresses trouvées",
        ]
        rows = VGroup(*[Text(e, font=MONO, font_size=20, color=GREY_A) for e in etapes])
        rows.arrange(DOWN, buff=0.22, aligned_edge=LEFT)
        rows.next_to(sub, DOWN, buff=0.3)
        rows.set_x(0)

        line = Line(
            rows.get_top() + UP * 0.1,
            rows.get_bottom() + DOWN * 0.1,
            color=GREY_D,
            stroke_width=2,
        )
        line.next_to(rows, LEFT, buff=0.3)

        self.play(Create(line), run_time=0.6)
        self.play(
            LaggedStart(*[FadeIn(r, shift=0.3 * RIGHT) for r in rows], lag_ratio=0.25),
            run_time=2.4,
        )
        self.wait(2.0)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=1.0)
