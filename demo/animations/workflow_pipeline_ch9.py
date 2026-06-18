"""Chapitre 9 du workflow BANO : recherche tolérante aux fautes."""

from workflow_pipeline_shared import COL_SCORE, COL_SRC, COL_TOK, QUERY_TYPO, COL_INDEX
from anim_common import MONO, titled
from workflow_pipeline_ch6 import node, edge  # mêmes états/arêtes que l'arbre du ch.7

# Slide = Scene + points d'arrêt `next_slide()` (présentation au clic). Sous
# `manim` normal, rend la MÊME vidéo continue -> montage/CI inchangés.
from manim_slides import Slide

from manim import (
    Create,
    DOWN,
    FadeIn,
    FadeOut,
    FadeTransform,
    Flash,
    GREY_A,
    GREY_B,
    LaggedStart,
    LEFT,
    Line,
    RED,
    RIGHT,
    RoundedRectangle,
    SurroundingRectangle,
    Text,
    Transform,
    UP,
    VGroup,
    Write,
)


def cut_mark(pt, color=RED):
    """Petite croix « branche coupée » centrée sur un point."""
    d = 0.14
    return VGroup(
        Line(
            pt + d * (LEFT + DOWN), pt + d * (RIGHT + UP), color=color, stroke_width=6
        ),
        Line(
            pt + d * (LEFT + UP), pt + d * (RIGHT + DOWN), color=color, stroke_width=6
        ),
    )


class Ch9Levenshtein(Slide):
    """Chapitre 9 — on cherche même avec une faute : distance de Levenshtein."""

    def construct(self):
        title, sub = titled(
            "On cherche, même avec une faute", "distance de Levenshtein", chapter=9
        )
        self.sub = sub
        self.play(Write(title), run_time=1.0)
        self.play(FadeIn(sub), run_time=0.6)

        # --- A. la requête fautive devient une clé ---------------------------
        qbox = RoundedRectangle(
            corner_radius=0.15,
            width=6.2,
            height=1.0,
            stroke_color=COL_SRC,
            stroke_width=3,
            fill_color=COL_SRC,
            fill_opacity=0.10,
        )
        qbox.move_to(UP * 1.45)
        qtyped = Text(
            "Impasse des Acasias",
            font=MONO,
            font_size=30,
            color=COL_SRC,
            t2c={"Acasias": RED},
        ).move_to(qbox)
        qcap = Text("ce que tape l'utilisateur", font_size=20, color=GREY_B).next_to(
            qbox, UP, buff=0.15
        )
        self.play(FadeIn(qbox), FadeIn(qtyped), FadeIn(qcap), run_time=0.8)
        self.wait(0.8)

        qtext = Text(
            QUERY_TYPO, font=MONO, font_size=30, color=COL_TOK, t2c={"acasias": RED}
        ).move_to(qbox)
        same = Text(
            "→ traitée comme une adresse : même clé", font_size=20, color=COL_TOK
        ).next_to(qbox, DOWN, buff=0.3)
        self.play(FadeTransform(qtyped, qtext), run_time=0.9)
        self.play(FadeIn(same), run_time=0.6)
        self.wait(1.2)
        self.next_slide()  # pause sur « faute traitée comme une adresse »
        # La requête a joué son rôle : on libère le haut pour la comparaison.
        self.play(FadeOut(VGroup(qbox, qtext, qcap, same)), run_time=0.5)

        # --- A2. on parcourt l'arbre du dico (façon ch.7) --------------------
        self.scene_parcours_arbre()

        # --- B. comparaison lettre par lettre (membre à membre) --------------
        # Le mot tapé et le mot de l'index, alignés EN COLONNES. On compare
        # chaque position : un trait vert si les deux lettres coïncident,
        # rouge sinon. C'est la lecture concrète de la distance de Levenshtein.
        typed_s, index_s = "acasias", "acacias"
        n = len(typed_s)
        step = 0.64
        x0 = -(n - 1) / 2 * step
        y_top, y_bot = 1.1, 0.1

        typed_chars = VGroup(
            *[Text(ch, font=MONO, font_size=42, color=COL_TOK) for ch in typed_s]
        )
        index_chars = VGroup(
            *[Text(ch, font=MONO, font_size=42, color=COL_INDEX) for ch in index_s]
        )
        for i, c in enumerate(typed_chars):
            c.move_to([x0 + i * step, y_top, 0])
        for i, c in enumerate(index_chars):
            c.move_to([x0 + i * step, y_bot, 0])

        typed_lbl = Text("ce qui est tapé", font=MONO, font_size=18, color=COL_TOK)
        good_lbl = Text("dans l'index", font=MONO, font_size=18, color=COL_INDEX)
        typed_lbl.next_to(typed_chars, LEFT, buff=0.6)
        good_lbl.next_to(index_chars, LEFT, buff=0.6)
        good_lbl.align_to(typed_lbl, RIGHT)  # bord droit net entre les 2 étiquettes

        self.play(FadeIn(typed_chars, shift=0.2 * UP), FadeIn(typed_lbl), run_time=0.6)
        self.play(FadeIn(index_chars, shift=0.2 * DOWN), FadeIn(good_lbl), run_time=0.6)
        self.wait(0.3)

        # Un trait par colonne, révélés l'un après l'autre (on « passe » sur
        # chaque lettre). Vert = pareil, rouge = différent.
        links = VGroup()
        for i in range(n):
            same_letter = typed_s[i] == index_s[i]
            links.add(
                Line(
                    typed_chars[i].get_bottom() + DOWN * 0.06,
                    index_chars[i].get_top() + UP * 0.06,
                    color=COL_SCORE if same_letter else RED,
                    stroke_width=4 if same_letter else 6,
                )
            )
        self.play(LaggedStart(*[Create(l) for l in links], lag_ratio=0.4), run_time=2.2)
        self.wait(0.3)

        # La seule colonne qui diffère : encadrée des deux côtés.
        diff_i = 3
        db_t = SurroundingRectangle(typed_chars[diff_i], color=RED, buff=0.08)
        db_i = SurroundingRectangle(index_chars[diff_i], color=COL_SCORE, buff=0.08)
        self.play(Create(db_t), Create(db_i), run_time=0.6)
        self.wait(0.4)

        tally = Text(
            "6 lettres identiques · 1 différente", font=MONO, font_size=22, color=GREY_A
        )
        tally.next_to(index_chars, DOWN, buff=0.6).set_x(0)
        corr = Text("→ 1 seule correction", font=MONO, font_size=24, color=COL_SCORE)
        corr.next_to(tally, DOWN, buff=0.22).set_x(0)
        self.play(FadeIn(tally), run_time=0.5)
        self.play(FadeIn(corr), run_time=0.5)
        self.wait(0.8)

        # --- C. la tolérance : 1 faute passe pour un mot long ----------------
        tol = VGroup(
            Text(
                "mot de plus de 4 lettres : jusqu'à 2 fautes tolérées",
                font_size=20,
                color=GREY_A,
            ),
        ).arrange(DOWN, buff=0.2)
        tol.next_to(corr, DOWN, buff=0.4).set_x(0)
        self.play(FadeIn(tol[0]), run_time=0.6)
        self.wait(1.2)
        self.next_slide()  # pause sur la comparaison lettre à lettre (1 correction)

        # --- D. adresse trouvée ----------------------------------------------
        found_word = Text("acacias", font=MONO, font_size=46, color=COL_INDEX)
        found_word.move_to(DOWN * 0.2)
        self.play(
            FadeOut(
                VGroup(
                    typed_chars,
                    index_chars,
                    typed_lbl,
                    good_lbl,
                    links,
                    db_t,
                    db_i,
                    tally,
                    corr,
                    tol,
                )
            ),
            FadeIn(found_word),
            run_time=0.9,
        )
        found_box = SurroundingRectangle(found_word, color=COL_INDEX, buff=0.25)
        found = Text("adresse trouvée", font=MONO, font_size=24, color=COL_INDEX)
        found.next_to(found_box, DOWN, buff=0.4)
        self.play(Create(found_box), FadeIn(found), run_time=1.0)
        self.wait(2.0)
        self.next_slide()  # pause sur « adresse trouvée »
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=1.0)

    # --- A2. parcours de l'arbre du dico, façon chapitre 7 -------------------
    def scene_parcours_arbre(self):
        """Comme l'arbre du ch.7, mais on le PARCOURT avec la requête fautive
        « acasias ». Tant que le compteur de fautes reste ≤ 2 on descend ;
        une branche qui dépasse le budget est coupée. « acacias » est atteint
        à 1 faute -> trouvé. Deux voisines (« acajou », « abricot ») sont
        écartées : l'une après le budget, l'autre dès le début."""
        sp = 0.92

        def P(i, y):
            return [-5.3 + i * sp, y, 0]

        Y_MAIN, Y_SIB = 0.85, -0.75

        # Chemin principal : a-c-a-c-i-a-s (le mot « acacias » de l'index).
        main = [node(P(i, Y_MAIN), final=(i == 7)) for i in range(8)]
        mlett = ["a", "c", "a", "c", "i", "a", "s"]
        medges = [edge(main[i], main[i + 1], mlett[i], UP * 0.26) for i in range(7)]

        # Voisine « acajou » : diverge après « aca » (état 3) -> j-o-u.
        aca = [node(P(i, Y_SIB), final=(i == 6)) for i in (4, 5, 6)]
        aedges = [
            edge(main[3], aca[0], "j", DOWN * 0.22 + RIGHT * 0.12),
            edge(aca[0], aca[1], "o", DOWN * 0.28),
            edge(aca[1], aca[2], "u", DOWN * 0.28),
        ]
        # Voisine « abricot » : diverge dès la 2e lettre (état 1) -> b...
        abr = node(P(2, Y_SIB))
        bedge = edge(main[1], abr, "b", DOWN * 0.22 + LEFT * 0.12)

        # Requête tapée, avec la faute (4e lettre) en rouge ; compteur de fautes.
        q = (
            Text(
                "on descend l'arbre avec « acasias »",
                font_size=22,
                color=GREY_A,
                t2c={"acasias": RED},
            )
            .next_to(self.sub, DOWN, buff=0.35)
            .set_x(0)
        )
        badge = Text("fautes : 0", font=MONO, font_size=24, color=COL_TOK)
        badge.move_to([4.7, 2.1, 0])

        all_tree = VGroup(*main, *medges, *aca, *aedges, abr, bedge)
        self.play(FadeIn(q), run_time=0.5)
        self.play(
            LaggedStart(*[FadeIn(m) for m in all_tree], lag_ratio=0.12), run_time=2.4
        )
        self.play(FadeIn(badge), run_time=0.4)
        self.wait(0.4)

        # Parcours du chemin principal, lettre par lettre. La 4e (index « c »
        # contre requête « s ») est une faute : arête jaune + compteur à 1.
        fautes = 0
        self.play(main[0][0].animate.set_stroke(COL_TOK, width=5), run_time=0.25)
        for i in range(7):
            faute = i == 3
            col = COL_SCORE if faute else COL_TOK
            anims = [
                medges[i][0].animate.set_color(col),
                main[i + 1][0].animate.set_stroke(col if faute else COL_TOK, width=5),
            ]
            self.play(*anims, run_time=0.34)
            if faute:
                fautes = 1
                new_badge = Text(
                    "fautes : 1", font=MONO, font_size=24, color=COL_SCORE
                ).move_to(badge)
                self.play(Transform(badge, new_badge), run_time=0.4)
        self.play(Flash(main[7], color=COL_TOK, flash_radius=0.55), run_time=0.6)
        ok = Text(
            "acacias — trouvé (1 faute ≤ 2)", font=MONO, font_size=21, color=COL_TOK
        ).next_to(main[7], RIGHT, buff=0.3)
        self.play(FadeIn(ok), run_time=0.5)
        self.wait(1.0)
        self.next_slide()  # pause sur « acacias trouvé (1 faute ≤ 2) »

        # Voisine « acajou » : on l'explore aussi (1 faute au départ), mais les
        # lettres suivantes accumulent -> on dépasse 2 -> branche coupée.
        for e in aedges:
            e[0].set_color(GREY_B)
        for nd in aca:
            nd[0].set_stroke(GREY_B)
        cut_a = cut_mark(aedges[2][0].get_center())
        lbl_a = Text(
            "acajou — trop de fautes, coupée", font=MONO, font_size=19, color=GREY_B
        ).next_to(aca[2], RIGHT, buff=0.3)
        self.play(Create(cut_a), FadeIn(lbl_a), run_time=0.7)
        self.wait(0.6)

        # Voisine « abricot » : diverge dès le « b » -> écartée tout de suite.
        bedge[0].set_color(GREY_B)
        abr[0].set_stroke(GREY_B)
        cut_b = cut_mark(bedge[0].get_center())
        lbl_b = (
            Text("abricot — coupée d'emblée", font=MONO, font_size=19, color=GREY_B)
            .next_to(abr, DOWN, buff=0.25)
            .set_x(P(2, 0)[0])
        )
        self.play(Create(cut_b), FadeIn(lbl_b), run_time=0.7)
        self.wait(1.4)
        self.next_slide()  # pause sur les branches coupées (budget de fautes)

        scene_mobs = VGroup(q, badge, all_tree, ok, cut_a, lbl_a, cut_b, lbl_b)
        self.play(FadeOut(scene_mobs), run_time=0.8)
