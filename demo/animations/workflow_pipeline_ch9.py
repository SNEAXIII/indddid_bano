"""Chapitre 9 du workflow BANO : la requête de l'utilisateur, côté Rust.

Vue d'ensemble de `fn search()` sans descendre au détail :
  1. `tokenize(query)` : on normalise (minuscules, accents, ponctuation) et on
     découpe la requête en mots ;
  2. chaque mot est cherché dans l'index (préfixe ∪ fautes tolérées) ;
  3. intersection ET : on ne garde que les adresses qui contiennent TOUS les
     mots, en additionnant les poids.

Registre semi-technique : quelques vraies lignes Rust en annotation, le reste
illustré visuellement. Le « pourquoi acasias trouve acacias » est détaillé au
chapitre suivant (Levenshtein) ; ici on reste au niveau du pipeline.
"""

from workflow_pipeline_shared import COL_SRC, COL_TOK, COL_INDEX, COL_SCORE

from anim_common import MONO, chip, code_line, titled

from manim import (
    Arrow,
    Create,
    DOWN,
    FadeIn,
    FadeOut,
    FadeTransform,
    GREY_A,
    GREY_B,
    GrowArrow,
    LaggedStart,
    LEFT,
    MoveToTarget,
    RED,
    RIGHT,
    RoundedRectangle,
    Scene,
    SurroundingRectangle,
    Text,
    UP,
    VGroup,
    Write,
)


class Ch9Requete(Scene):
    """Chapitre 9 — la requête de l'utilisateur : normalise, tokenise, ET."""

    def construct(self):
        self.title, self.sub = titled(
            "Quand l'utilisateur cherche", "fn search() — en trois temps", chapter=9
        )
        self.play(Write(self.title), run_time=1.0)
        self.play(FadeIn(self.sub), run_time=0.6)

        self.scene_tokenise()
        self.scene_par_mot()
        self.scene_intersection()

        self.play(*[FadeOut(m) for m in self.mobjects], run_time=1.0)

    # --- 1. normalise + tokenise --------------------------------------------
    def scene_tokenise(self):
        # La requête brute, telle que tapée (avec sa faute « Acasias »).
        raw_box = RoundedRectangle(
            corner_radius=0.15,
            width=5.0,
            height=0.9,
            stroke_color=COL_SRC,
            stroke_width=3,
            fill_color=COL_SRC,
            fill_opacity=0.10,
        ).move_to(UP * 1.8)
        raw = Text(
            "Impasse des Acasias",
            font=MONO,
            font_size=28,
            color=COL_SRC,
            t2c={"Acasias": RED},
        ).move_to(raw_box)
        # Annotation Rust courte, à droite de la boîte (sans détail).
        rust = code_line("tokenize(query)", font_size=20)
        rust.next_to(raw_box, RIGHT, buff=0.5)

        self.play(FadeIn(raw_box), FadeIn(raw), run_time=0.7)
        self.play(FadeIn(rust), run_time=0.5)
        self.wait(0.5)

        # Étape a : normaliser (minuscules, accents, ponctuation propre).
        norm = Text(
            "impasse des acasias",
            font=MONO,
            font_size=28,
            color=COL_TOK,
            t2c={"acasias": RED},
        ).move_to(UP * 0.3)
        a1 = Arrow(
            raw_box.get_bottom(), norm.get_top() + UP * 0.05, color=GREY_B, buff=0.18
        )
        norm_cap = Text("minuscules, sans accent", font_size=18, color=GREY_A)
        norm_cap.next_to(norm, RIGHT, buff=0.5)
        self.play(GrowArrow(a1), run_time=0.4)
        self.play(FadeTransform(raw.copy(), norm), FadeIn(norm_cap), run_time=0.9)
        self.wait(0.6)

        # Étape b : découper en mots (jetons).
        toks = (
            VGroup(
                chip("impasse", font_size=24),
                chip("des", font_size=24),
                chip("acasias", color=COL_SRC, font_size=24),
            )
            .arrange(RIGHT, buff=0.4)
            .move_to(DOWN * 1.4)
        )
        a2 = Arrow(
            norm.get_bottom(), toks.get_top() + UP * 0.05, color=GREY_B, buff=0.18
        )
        toks_cap = Text("découpée en mots", font_size=18, color=GREY_A)
        toks_cap.next_to(toks, DOWN, buff=0.22)
        self.play(GrowArrow(a2), run_time=0.4)
        self.play(
            LaggedStart(*[FadeIn(t, shift=0.2 * DOWN) for t in toks], lag_ratio=0.3),
            FadeIn(toks_cap),
            run_time=1.0,
        )
        self.wait(1.0)

        self.play(
            FadeOut(VGroup(raw_box, raw, rust, a1, norm, norm_cap, a2, toks_cap)),
            run_time=0.6,
        )
        # On transmet les jetons à la scène suivante.
        self.toks = toks

    # --- 2. chaque mot cherché dans l'index ---------------------------------
    def scene_par_mot(self):
        # Replace les 3 jetons en colonne, à gauche.
        toks = self.toks
        toks.generate_target()
        toks.target.arrange(DOWN, buff=0.7, aligned_edge=LEFT)
        toks.target.to_edge(LEFT, buff=1.2).shift(DOWN * 0.2)
        self.play(MoveToTarget(toks), run_time=0.8)
        self.wait(0.5)

        # Chaque jeton -> le(s) mot(s) trouvé(s) dans l'index. impasse/des = exact,
        # acasias = trouvé via tolérance (≈ acacias) — détaillé au chap. suivant.
        found = [
            ("impasse", COL_INDEX, "exact"),
            ("des", COL_INDEX, "exact"),
            ("acacias", COL_INDEX, "≈ 1 faute"),
        ]
        # Colonnes alignées : flèches de longueur identique (x fixes), mots de
        # droite alignés sur leur bord GAUCHE, notes dans une colonne commune.
        arrow_x0 = toks.get_right()[0] + 0.25  # départ commun (bord droit colonne)
        word_x = 2.0  # bord gauche commun des mots trouvés
        note_x = 4.4  # colonne des annotations
        arrows, words, notes = VGroup(), VGroup(), VGroup()
        for tok, (label, col, note) in zip(toks, found):
            y = tok.get_y()
            w = chip(label, color=col, font_size=24)
            w.move_to([word_x, y, 0], aligned_edge=LEFT)
            ar = Arrow([arrow_x0, y, 0], [word_x - 0.1, y, 0], color=GREY_B, buff=0.1)
            nt = Text(note, font_size=17, color=(RED if note != "exact" else GREY_A))
            nt.move_to([note_x, y, 0], aligned_edge=LEFT)
            arrows.add(ar)
            words.add(w)
            notes.add(nt)

        for ar, w, nt in zip(arrows, words, notes):
            self.play(GrowArrow(ar), FadeIn(w), FadeIn(nt), run_time=0.6)
        self.wait(0.4)

        # On souligne le seul cas non trivial (lien vers le chapitre Levenshtein).
        hl = SurroundingRectangle(VGroup(toks[2], words[2]), color=RED, buff=0.18)
        hl_cap = Text(
            "faute corrigée — détail au chapitre suivant", font_size=18, color=RED
        )
        hl_cap.next_to(hl, DOWN, buff=0.25).set_x(0)
        self.play(Create(hl), FadeIn(hl_cap), run_time=0.7)
        self.wait(1.2)

        self.play(
            FadeOut(VGroup(arrows, words, notes, hl, hl_cap)),
            FadeOut(toks),
            run_time=0.6,
        )

    # --- 3. intersection ET --------------------------------------------------
    def scene_intersection(self):
        # On repart propre : 3 lignes « mot -> numéros d'adresses qui le
        # contiennent », puis l'intersection (records présents PARTOUT).
        rows_data = [
            ("impasse", "0", COL_INDEX),
            ("des", "0, 1", COL_INDEX),
            ("acacias", "0, 1", COL_INDEX),
        ]

        def line(word, ids, col):
            return VGroup(
                chip(word, color=col, font_size=22),
                Text("→", font=MONO, font_size=22, color=GREY_B),
                Text(f"adresses {{{ids}}}", font=MONO, font_size=22, color=COL_SCORE),
            ).arrange(RIGHT, buff=0.25)

        rows = VGroup(*[line(w, i, c) for w, i, c in rows_data])
        rows.arrange(DOWN, buff=0.3, aligned_edge=LEFT).move_to(UP * 0.8 + LEFT * 1.2)

        rust = code_line("// intersection ET (somme des poids)", font_size=19)
        rust.next_to(self.sub, DOWN, buff=0.3).set_x(0)
        self.play(FadeIn(rust), run_time=0.5)
        self.play(
            LaggedStart(*[FadeIn(r, shift=0.2 * RIGHT) for r in rows], lag_ratio=0.25),
            run_time=1.2,
        )
        self.wait(0.6)

        # Le ET : seule l'adresse 0 est présente dans les trois lignes.
        keep = VGroup(rows[0][2], rows[1][2], rows[2][2])
        flash = [SurroundingRectangle(r[2], color=COL_SCORE, buff=0.08) for r in rows]
        self.play(*[Create(f) for f in flash], run_time=0.6)
        self.wait(0.3)

        res = VGroup(
            Text("présentes PARTOUT  →  adresse n°0", font_size=24, color=COL_SCORE),
            Text(
                "Impasse des Acacias 01310 Saint-Rémy",
                font=MONO,
                font_size=22,
                color=COL_INDEX,
            ),
        ).arrange(DOWN, buff=0.25)
        res.next_to(rows, DOWN, buff=0.7).set_x(0)
        self.play(FadeIn(res[0]), run_time=0.6)
        self.play(FadeIn(res[1], shift=0.2 * UP), run_time=0.7)
        self.wait(0.6)

        # Pourquoi l'adresse 1 tombe : « Rue des Acacias » n'a pas « impasse ».
        why = Text(
            "« Rue des Acacias » (n°1) écartée : pas de « impasse »",
            font_size=18,
            color=GREY_A,
        )
        why.next_to(res, DOWN, buff=0.4).set_x(0)
        self.play(FadeIn(why), run_time=0.6)
        self.wait(1.6)

        self.play(
            FadeOut(VGroup(rust, rows, *flash, res, why)),
            run_time=0.6,
        )
