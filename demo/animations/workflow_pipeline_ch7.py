"""Chapitre 7 du workflow BANO : on emballe l'index en fichiers binaires."""

from workflow_pipeline_shared import COL_POST, COL_REC, COL_INDEX

from anim_common import MONO, chip, titled

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
    GrowArrow,
    LEFT,
    LaggedStart,
    RIGHT,
    RoundedRectangle,
    SurroundingRectangle,
    Text,
    UP,
    VGroup,
    Write,
)


def file_card(name, sample, color, width=3.6, height=1.05):
    """Boîte de fichier qui MONTRE son contenu : nom en haut, aperçu réel en
    dessous. L'aperçu reste visible jusqu'au plan final (le simple nom ne dit
    pas ce que le fichier contient — c'est le reproche corrigé ici)."""
    rect = RoundedRectangle(
        corner_radius=0.15,
        width=width,
        height=height,
        stroke_color=color,
        stroke_width=3,
        fill_color=color,
        fill_opacity=0.15,
    )
    title = Text(name, font=MONO, font_size=22, color=color)
    samp = Text(sample, font=MONO, font_size=13, color=color)
    if samp.width > width - 0.3:
        samp.scale((width - 0.3) / samp.width)
    VGroup(title, samp).arrange(DOWN, buff=0.12).move_to(rect.get_center())
    return VGroup(rect, title, samp)


class Ch7Fichiers(Slide):
    """Chapitre 7 — l'index trié devient 3 fichiers livrés avec l'appli.
    Registre mi-technique : on nomme les fichiers et on montre le lien
    clé → liste de numéros → adresse complète, sans descendre aux octets."""

    def construct(self):
        title, sub = titled(
            "On emballe l'index", "les fichiers livrés avec l'appli", chapter=7
        )
        self.play(Write(title), run_time=1.0)
        self.play(FadeIn(sub), run_time=0.6)

        # --- A. rappel de l'index trié (compact, repris de Ch6) ---------------
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
        rows.arrange(DOWN, buff=0.22, aligned_edge=LEFT)
        rows.move_to(DOWN * 0.2)
        frame = SurroundingRectangle(rows, color=COL_INDEX, buff=0.3)
        idx_title = Text("index trié", font=MONO, font_size=20, color=COL_INDEX)
        idx_title.next_to(frame, UP, buff=0.15)

        self.play(Create(frame), FadeIn(idx_title), run_time=0.7)
        self.play(
            LaggedStart(*[FadeIn(r, shift=0.2 * RIGHT) for r in rows], lag_ratio=0.18),
            run_time=1.4,
        )
        self.wait(0.6)

        cap = Text(
            "on le range dans des fichiers, livrés avec l'appli",
            font_size=22,
            color=GREY_A,
        ).next_to(frame, DOWN, buff=0.6)
        self.play(FadeIn(cap), run_time=0.7)
        self.wait(1.2)
        self.next_slide()  # pause sur le rappel de l'index trié
        self.play(FadeOut(VGroup(rows, frame, idx_title, cap)), run_time=0.7)

        # --- B. les 3 fichiers, EMPILÉS et reliés : jeton → numéros → adresses
        # Chaque boîte porte un APERÇU de son vrai contenu (repris de l'index
        # trié ci-dessus) : le nom seul ne disait pas ce qu'il y a dedans.
        fst_box = file_card(
            "index.fst", "acacias · impasse · remy · rue · saint", COL_INDEX
        )
        post_box = file_card(
            "postings.bin", "[0,1] · [0] · [0,1] · [1] · [0,1]", COL_POST
        )
        rec_box = file_card(
            "records.bin", "Impasse des Acacias…  ·  Rue des Acacias…", COL_REC
        )

        fst_val = chip("acacias", font_size=20)
        post_val = Text("[0, 1]", font=MONO, font_size=24, color=COL_POST)
        # records.bin : CHAQUE numéro -> son adresse COMPLÈTE (0 et 1 expliqués).
        rec_val = VGroup(
            Text(
                "0 → Impasse des Acacias 01310 Saint-Rémy",
                font=MONO,
                font_size=18,
                color=COL_REC,
            ),
            Text(
                "1 → Rue des Acacias 01310 Saint-Rémy",
                font=MONO,
                font_size=18,
                color=COL_REC,
            ),
        ).arrange(DOWN, buff=0.16, aligned_edge=LEFT)

        row_fst = VGroup(fst_box, fst_val).arrange(RIGHT, buff=0.5)
        row_post = VGroup(post_box, post_val).arrange(RIGHT, buff=0.5)
        row_rec = VGroup(rec_box, rec_val).arrange(RIGHT, buff=0.5)

        # Empile les 3 rangées en colonne (boxes alignées à gauche) : sans ça
        # elles se superposent à l'origine et les flèches deviennent nulles.
        VGroup(row_fst, row_post, row_rec).arrange(
            DOWN, buff=0.7, aligned_edge=LEFT
        ).to_edge(LEFT, buff=0.8).shift(DOWN * 0.2)

        a_fp = Arrow(fst_box.get_bottom(), post_box.get_top(), color=GREY_B, buff=0.1)
        a_pr = Arrow(post_box.get_bottom(), rec_box.get_top(), color=GREY_B, buff=0.1)

        fst_role = Text(
            "Un mot enregistré sous forme normalisée",
            font=MONO,
            font_size=15,
            color=GREY_B,
        )
        fst_role.next_to(row_fst, RIGHT, buff=0.5)
        post_role = Text(
            "les numéros des adresses qui le contiennent",
            font=MONO,
            font_size=15,
            color=GREY_B,
        )
        post_role.next_to(row_post, RIGHT, buff=0.5)
        rec_role = Text(
            "les adresses complètes à afficher", font=MONO, font_size=15, color=COL_REC
        )
        rec_role.next_to(rec_val, DOWN, buff=0.2, aligned_edge=LEFT)

        # On déroule le fil, fichier par fichier.
        self.play(FadeIn(row_fst, shift=0.3 * UP), run_time=0.7)
        self.play(FadeIn(fst_role), run_time=0.4)
        self.play(GrowArrow(a_fp), run_time=0.4)
        self.play(FadeIn(row_post, shift=0.3 * UP), run_time=0.7)
        self.play(FadeIn(post_role), run_time=0.4)
        self.wait(0.3)
        self.play(GrowArrow(a_pr), run_time=0.4)
        self.play(FadeIn(row_rec, shift=0.3 * UP), run_time=0.7)
        self.play(FadeIn(rec_role), run_time=0.4)
        self.wait(0.6)

        # Le numéro 1 = la 2e adresse (celui qu'on ne comprenait pas).
        self.wait(1)
        self.next_slide()  # pause sur la chaîne mot → numéros → adresses
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=1.0)
