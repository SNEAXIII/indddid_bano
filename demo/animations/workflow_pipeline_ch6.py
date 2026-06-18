"""Chapitre 6 du workflow BANO : le dictionnaire rangé en arbre (automate / FST).

Registre semi-technique nommé : métaphore visuelle (un arbre de branches
partagées) MAIS on nomme les vrais termes en sous-titre et en légendes
(automate fini, FST). Le chapitre répond à l'intuition « ça range les mots
sous forme de branches » :
  1. branches partagées en DÉBUT de mot (arbre de préfixes), avec des mots
     similaires : rue / ruelle / ruette / remy ;
  2. PARCOURS visuel : un mot descend l'arbre lettre par lettre, puis un mot
     voisin réutilise le début « rue » et bifurque (on VOIT le partage) ;
  3. fins de mots partagées AUSSI (la vraie nouveauté du FST) ;
  4. chaque mot complet porte une valeur → ses adresses (lien avec l'index).

Le détail octet de index.fst est au chapitre suivant (les fichiers binaires) ;
ici on reste au niveau de la STRUCTURE.
"""

from workflow_pipeline_shared import COL_INDEX, COL_TOK, COL_POST, COL_SRC, COL_DROP

from anim_common import MONO, chip, titled

# Slide = Scene + points d'arrêt `next_slide()` pour la présentation au clic.
# IMPORTANT : sous `manim` normal, une Slide rend la MÊME vidéo continue (les
# next_slide() sont ignorés au rendu) -> le montage/CI ne change pas.
from manim_slides import Slide

from manim import (
    BLACK,
    Circle,
    Create,
    DOWN,
    FadeIn,
    FadeOut,
    Flash,
    GREY_A,
    GREY_B,
    GrowArrow,
    LEFT,
    LaggedStart,
    Line,
    RIGHT,
    SurroundingRectangle,
    Text,
    UP,
    VGroup,
    WHITE,
    Write,
    Arrow,
)


def node(pos, final=False):
    """Un état de l'automate : petit cercle. Un état FINAL (= mot complet)
    porte un second cercle vert concentrique (notation classique)."""
    c = Circle(
        radius=0.22,
        stroke_color=COL_INDEX,
        stroke_width=3,
        fill_color=BLACK,
        fill_opacity=1.0,
    ).move_to(pos)
    grp = VGroup(c)
    if final:
        grp.add(Circle(radius=0.13, stroke_color=COL_TOK, stroke_width=3).move_to(pos))
    return grp


def edge(a, b, letter, off):
    """Arête étiquetée d'une lettre entre deux états (bord à bord)."""
    line = Line(a.get_center(), b.get_center(), color=GREY_B, stroke_width=3, buff=0.24)
    lab = Text(letter, font=MONO, font_size=24, color=WHITE)
    lab.move_to(line.get_center() + off)
    return VGroup(line, lab)


# Disposition de l'arbre : 4 mots similaires. rue/ruelle/ruette partagent
# « r-u-e » ; ruelle/ruette divergent ensuite (l.. vs t..) ; remy ne partage
# que le « r ». Chaque état a une position fixe (clé -> [x, y, 0]).
POS = {
    "S": [-6.3, 0.0, 0],
    "A": [-5.2, 0.0, 0],
    "B": [-4.1, 1.25, 0],
    "C": [-3.0, 1.25, 0],  # C = "rue" (final)
    "D": [-1.9, 1.95, 0],
    "E": [-0.8, 1.95, 0],
    "F": [0.3, 1.95, 0],  # ruelle
    "G": [-1.9, 0.55, 0],
    "H": [-0.8, 0.55, 0],
    "I": [0.3, 0.55, 0],  # ruette
    "J": [-4.1, -1.3, 0],
    "K": [-3.0, -1.3, 0],
    "L": [-1.9, -1.3, 0],  # remy
}
FINALS = {"C", "F", "I", "L"}
# (de, vers, lettre, décalage du label)
EDGES = [
    ("S", "A", "r", UP * 0.32),
    ("A", "B", "u", UP * 0.18 + LEFT * 0.18),
    ("B", "C", "e", UP * 0.32),
    ("C", "D", "l", UP * 0.28 + RIGHT * 0.18),
    ("D", "E", "l", UP * 0.32),
    ("E", "F", "e", UP * 0.32),
    ("C", "G", "t", DOWN * 0.28 + RIGHT * 0.18),
    ("G", "H", "t", UP * 0.32),
    ("H", "I", "e", UP * 0.32),
    ("A", "J", "e", DOWN * 0.18 + LEFT * 0.18),
    ("J", "K", "m", DOWN * 0.32),
    ("K", "L", "y", DOWN * 0.32),
]


class Ch6Fst(Slide):
    """Chapitre 6 — le dictionnaire trié est rangé en arbre de branches
    partagées : un automate fini (FST). Réponse à « ça stocke les mots sous
    forme de branches », avec un parcours visuel."""

    def construct(self):
        self.title, self.sub = titled(
            "Les mots rangés en arbre", "un automate fini — FST", chapter=6
        )
        self.play(Write(self.title), run_time=1.0)
        self.play(FadeIn(self.sub), run_time=0.6)

        # Points d'arrêt (`next_slide()`) placés DANS les scènes, toujours JUSTE
        # AVANT un FadeOut : la pause tombe sur le contenu plein, et c'est le clic
        # suivant qui déclenche le fade + la scène d'après. Aucun effet sur la
        # vidéo continue (next_slide ignoré au rendu, le fade reste).
        self.next_slide()  # pause sur le titre
        self.scene_arbre()
        self.scene_parcours()
        self.scene_suffixe()
        self.scene_valeur()
        self.scene_recap()

        self.next_slide()  # pause sur le recap avant le fondu final
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=1.0)

    # --- construction de l'arbre (mobjects, pas d'animation) -----------------
    def build_tree(self):
        """Crée les états + arêtes + libellés des 4 mots et les range sur
        `self`. N'anime rien : les scènes décident quoi montrer."""
        self.nodes = {k: node(p, final=(k in FINALS)) for k, p in POS.items()}
        self.edges = {
            (a, b): edge(self.nodes[a], self.nodes[b], letter, off)
            for (a, b, letter, off) in EDGES
        }
        self.word_labels = {
            "rue": Text("rue", font=MONO, font_size=20, color=COL_TOK).next_to(
                self.nodes["C"], RIGHT, buff=0.28
            ),
            "ruelle": Text("ruelle", font=MONO, font_size=20, color=COL_TOK).next_to(
                self.nodes["F"], RIGHT, buff=0.28
            ),
            "ruette": Text("ruette", font=MONO, font_size=20, color=COL_TOK).next_to(
                self.nodes["I"], RIGHT, buff=0.28
            ),
            "remy": Text("remy", font=MONO, font_size=20, color=COL_TOK).next_to(
                self.nodes["L"], RIGHT, buff=0.28
            ),
        }

    # --- 1. branches partagées en début de mot (arbre de préfixes) -----------
    def scene_arbre(self):
        self.build_tree()
        nodes = VGroup(*self.nodes.values())

        self.play(FadeIn(self.nodes["S"]), run_time=0.4)
        # On déroule l'arbre arête par arête : l'œil voit les branches naître.
        self.play(
            LaggedStart(
                *[
                    FadeIn(VGroup(self.edges[(a, b)], self.nodes[b]))
                    for (a, b, *_) in EDGES
                ],
                lag_ratio=0.4,
            ),
            run_time=3.0,
        )
        self.play(
            LaggedStart(
                *[FadeIn(l) for l in self.word_labels.values()], lag_ratio=0.25
            ),
            run_time=1.0,
        )
        self.wait(0.5)
        self.next_slide()  # pause sur l'arbre complet

        # Le partage : « r-u-e » écrit UNE fois, sert à rue, ruelle ET ruette.
        # On entoure les BULLES r-u-e (S→C) en plus des arêtes, sinon l'état
        # final « rue » (C) déborde à droite du cadre.
        shared = SurroundingRectangle(
            VGroup(
                self.nodes["S"],
                self.nodes["A"],
                self.nodes["B"],
                self.nodes["C"],
                self.edges[("S", "A")],
                self.edges[("A", "B")],
                self.edges[("B", "C")],
            ),
            color=COL_SRC,
            buff=0.26,
        )
        cap = Text(
            "« rue » : écrit une seule fois, partagé par 3 mots",
            font_size=20,
            color=COL_SRC,
        ).move_to([0.0, -2.6, 0])
        self.play(Create(shared), FadeIn(cap), run_time=0.9)
        self.wait(1.6)
        self.next_slide()  # pause sur le surlignage « rue partagé »

        # On garde l'arbre (transmis à la scène de parcours), on retire le surlignage.
        self.play(FadeOut(VGroup(shared, cap)), run_time=0.5)

    # --- 2. PARCOURS : un mot descend l'arbre, un voisin réutilise le début ---
    def scene_parcours(self):
        cap0 = Text(
            "chercher un mot = descendre les branches, lettre par lettre",
            font_size=20,
            color=GREY_A,
        ).move_to([0.0, -2.5, 0])
        self.play(FadeIn(cap0), run_time=0.6)

        # --- 2a. parcours complet de « ruelle » ------------------------------
        path1 = [("S", "A"), ("A", "B"), ("B", "C"), ("C", "D"), ("D", "E"), ("E", "F")]
        letters1 = self._letters("ruelle", [0.0, -3.3, 0])
        self.play(FadeIn(letters1), run_time=0.5)
        self._walk(path1, letters1, start=0)
        self.play(
            Flash(self.nodes["F"], color=COL_TOK, flash_radius=0.55), run_time=0.6
        )
        ok1 = Text("ruelle trouvé", font=MONO, font_size=22, color=COL_TOK).move_to(
            [0.0, -2.5, 0]
        )
        self.play(FadeOut(cap0), FadeIn(ok1), run_time=0.5)
        self.wait(1.0)
        self.next_slide()  # pause sur « ruelle trouvé »

        # On efface la FIN propre à ruelle (l-l-e), on GARDE « r-u-e » en vert :
        # ce début est réutilisé par le mot suivant.
        for key in (("C", "D"), ("D", "E"), ("E", "F")):
            self.edges[key][0].set_color(GREY_B)
        for nm in ("D", "E", "F"):
            self.nodes[nm][0].set_stroke(COL_INDEX, width=3)
        self.play(FadeOut(letters1), FadeOut(ok1), run_time=0.6)

        # --- 2b. « ruette » : réutilise r-u-e (déjà vert), puis bifurque ------
        letters2 = self._letters("ruette", [0.0, -3.3, 0])
        # r, u, e déjà parcourus -> on les montre déjà verts.
        for i in range(3):
            letters2[i].set_color(COL_TOK)
        self.play(FadeIn(letters2), run_time=0.5)
        # On ne parcourt QUE la nouvelle fin : t-t-e.
        path2 = [("C", "G"), ("G", "H"), ("H", "I")]
        self._walk(path2, letters2, start=3)
        # La légende n'apparaît qu'UNE FOIS la bifurcation tracée : on voit
        # d'abord « rue » réutilisé (vert) puis la nouvelle fin t-t-e, et alors
        # seulement on explique « seule la fin diffère ».
        cap2 = Text(
            "même début « rue » réutilisé — seule la fin diffère",
            font_size=20,
            color=COL_SRC,
        ).move_to([0.0, -2.5, 0])
        self.play(FadeIn(cap2), run_time=0.5)
        self.play(
            Flash(self.nodes["I"], color=COL_TOK, flash_radius=0.55), run_time=0.6
        )
        ok2 = Text("trouvé", font=MONO, font_size=22, color=COL_TOK)
        ok2.next_to(self.word_labels["ruette"], RIGHT, buff=0.3)
        self.play(FadeIn(ok2), run_time=0.4)
        self.wait(1.4)
        self.next_slide()  # pause sur « ruette trouvé » (arbre plein)

        self.play(
            FadeOut(
                VGroup(
                    *self.nodes.values(),
                    *self.edges.values(),
                    *self.word_labels.values(),
                    letters2,
                    ok2,
                    cap2,
                )
            ),
            run_time=0.8,
        )

    def _letters(self, word, center):
        """Rangée de lettres (la requête) sous l'arbre ; chacune s'allume
        quand on consomme la branche correspondante."""
        row = VGroup(*[Text(c, font=MONO, font_size=34, color=COL_SRC) for c in word])
        row.arrange(RIGHT, buff=0.45).move_to(center)
        return row

    def _walk(self, path, letters, start):
        """Allume, pas à pas, l'arête + l'état d'arrivée + la lettre consommée."""
        for i, (a, b) in enumerate(path):
            li = start + i
            anims = [
                self.edges[(a, b)][0].animate.set_color(COL_TOK),
                self.nodes[b][0].animate.set_stroke(COL_TOK, width=5),
            ]
            if li < len(letters):
                anims.append(letters[li].animate.set_color(COL_TOK))
            self.play(*anims, run_time=0.34)

    # --- 3. les FINS de mots se partagent aussi (la vraie idée du FST) --------
    def scene_suffixe(self):
        head = (
            Text(
                "et les fins de mots se partagent aussi",
                font_size=24,
                color=GREY_A,
            )
            .next_to(self.sub, DOWN, buff=0.35)
            .set_x(0)
        )
        self.play(FadeIn(head), run_time=0.6)

        # rue (r) et avenue (a-v-e-n) finissent toutes deux par « u-e » :
        # cette fin commune n'est stockée QU'UNE fois (états M-N-FIN partagés).
        M = node([0.4, 0.0, 0])
        N = node([1.7, 0.0, 0])
        Z = node([3.0, 0.0, 0], final=True)

        S1 = node([-1.4, 1.1, 0])  # départ "rue"
        S2 = node([-5.4, -1.1, 0])  # départ "avenue"
        b1 = node([-4.1, -1.1, 0])
        b2 = node([-2.8, -1.1, 0])
        b3 = node([-1.5, -1.1, 0])

        nodes = VGroup(M, N, Z, S1, S2, b1, b2, b3)

        edges = VGroup(
            edge(S1, M, "r", UP * 0.22 + RIGHT * 0.1),  # rue : r -> fin commune
            edge(S2, b1, "a", DOWN * 0.3),
            edge(b1, b2, "v", DOWN * 0.3),
            edge(b2, b3, "e", DOWN * 0.3),
            edge(b3, M, "n", DOWN * 0.22 + RIGHT * 0.1),  # avenue : ...n -> fin commune
            edge(M, N, "u", UP * 0.3),  # FIN PARTAGÉE
            edge(N, Z, "e", UP * 0.3),
        )

        lbl_rue = Text("rue", font=MONO, font_size=20, color=COL_TOK).next_to(
            S1, UP, buff=0.2
        )
        lbl_av = Text("avenue", font=MONO, font_size=20, color=COL_TOK).next_to(
            S2, LEFT, buff=0.2
        )

        self.play(
            LaggedStart(*[FadeIn(VGroup(e)) for e in edges], lag_ratio=0.25),
            FadeIn(nodes),
            run_time=2.2,
        )
        self.play(FadeIn(lbl_rue), FadeIn(lbl_av), run_time=0.6)
        self.wait(0.4)

        # On entoure la fin commune « u-e » et on la nomme.
        tail = SurroundingRectangle(
            VGroup(M, edges[5], N, edges[6], Z), color=COL_SRC, buff=0.14
        )
        cap = Text(
            "fin « ue » : une seule fois",
            font_size=20,
            color=COL_SRC,
        ).next_to(tail, DOWN, buff=0.35)
        self.play(
            Create(tail),
            FadeIn(cap),
            Flash(Z, color=COL_TOK, flash_radius=0.6),
            run_time=1.0,
        )
        self.wait(1.0)

        name = (
            Text(
                "préfixes ET fins partagés  →  automate fini (FST)",
                font_size=22,
                color=COL_INDEX,
            )
            .next_to(nodes, DOWN, buff=0.9)
            .set_x(0)
        )
        self.play(FadeIn(name), run_time=0.7)
        self.wait(1.8)
        self.next_slide()  # pause sur la fin commune « ue » + le nom FST

        self.play(
            FadeOut(VGroup(head, nodes, edges, lbl_rue, lbl_av, tail, cap, name)),
            run_time=0.7,
        )

    # --- 4. chaque mot complet porte une valeur -> ses adresses --------------
    def scene_valeur(self):
        head = (
            Text(
                "chaque mot complet pointe vers ses adresses",
                font_size=24,
                color=GREY_A,
            )
            .next_to(self.sub, DOWN, buff=0.35)
            .set_x(0)
        )
        self.play(FadeIn(head), run_time=0.6)

        # Un état final (mot complet) -> une valeur -> la liste de ses adresses.
        word = chip("acacias", color=COL_INDEX, font_size=26)
        grp_word = VGroup(word).move_to(LEFT * 3.0)

        a = Arrow(
            grp_word.get_right(),
            grp_word.get_right() + RIGHT * 1.6,
            color=GREY_B,
            buff=0.2,
        )
        val = Text("adresses 0, 1", font=MONO, font_size=26, color=COL_POST)
        val.next_to(a, RIGHT, buff=0.3)

        self.play(FadeIn(grp_word), run_time=0.6)
        self.play(GrowArrow(a), FadeIn(val), run_time=0.8)
        self.wait(0.4)

        cap = (
            Text(
                "comme l'index trié du chapitre 6 : le mot mène à l'adresse entière",
                font_size=19,
                color=GREY_B,
            )
            .next_to(VGroup(grp_word, val), DOWN, buff=0.7)
            .set_x(0)
        )
        legend = (
            VGroup(
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
            )
            .arrange(DOWN, buff=0.18, aligned_edge=LEFT)
            .next_to(cap, DOWN, buff=0.35)
        )
        self.play(FadeIn(cap), run_time=0.5)
        self.play(FadeIn(legend), run_time=0.6)
        self.wait(1.8)
        self.next_slide()  # pause sur « mot → adresses »

        self.play(FadeOut(VGroup(head, grp_word, a, val, cap, legend)), run_time=0.7)

    # --- 5. recap : pourquoi un arbre + tolérance ----------------------------
    def scene_recap(self):
        # Recap = le bénéfice de l'ARBRE (sujet du chapitre) : le début « rue »
        # est partagé par ruelle/ruette, donc descendu UNE seule fois pour
        # atteindre les deux. La tolérance aux fautes (Levenshtein) n'est PAS
        # expliquée ici : c'est le chapitre 10 ; on n'y fait qu'un renvoi.
        S = node([-4.4, 0.95, 0])
        A = node([-3.3, 0.95, 0])
        B = node([-2.2, 0.95, 0])
        C = node([-1.1, 0.95, 0])
        nL = node([0.4, 1.7, 0], final=True)
        nT = node([0.4, 0.2, 0], final=True)

        e_r = edge(S, A, "r", UP * 0.26)
        e_u = edge(A, B, "u", UP * 0.26)
        e_e = edge(B, C, "e", UP * 0.26)
        e_l = edge(C, nL, "l", UP * 0.14 + LEFT * 0.14)
        e_t = edge(C, nT, "t", DOWN * 0.14 + LEFT * 0.14)

        for e in (e_r, e_u, e_e, e_l, e_t):
            e[0].set_color(COL_TOK)
        nL[0].set_stroke(COL_TOK, width=5)
        nT[0].set_stroke(COL_TOK, width=5)

        typed = Text("on tape « rue… »", font=MONO, font_size=20, color=COL_SRC)
        typed.next_to(S, UP, buff=0.3).set_x(-3.7)

        lblL = Text("ruelle", font=MONO, font_size=20, color=COL_TOK).next_to(
            nL, RIGHT, buff=0.3
        )
        lblT = Text("ruette", font=MONO, font_size=20, color=COL_TOK).next_to(
            nT, RIGHT, buff=0.3
        )

        tree = VGroup(S, e_r, A, e_u, B, e_e, C, e_l, nL, e_t, nT)
        self.play(FadeIn(typed), run_time=0.4)
        self.play(LaggedStart(*[FadeIn(m) for m in tree], lag_ratio=0.16), run_time=1.7)
        self.play(FadeIn(lblL), FadeIn(lblT), run_time=0.5)
        self.wait(0.4)

        # On surligne le début « rue » partagé : descendu une seule fois.
        shared = SurroundingRectangle(
            VGroup(S, e_r, A, e_u, B, e_e, C), color=COL_SRC, buff=0.14
        )
        cap = (
            Text(
                "« rue » partagé — parcourus une seule fois pour les deux mots",
                font_size=20,
                color=COL_SRC,
            )
            .next_to(nT, DOWN, buff=0.55)
            .set_x(0)
        )
        self.play(Create(shared), FadeIn(cap), run_time=0.9)
        self.wait(1.4)
        self.next_slide()  # pause sur « rue partagé »

        # Renvoi vers le chapitre dédié à la tolérance aux fautes.
        tease = (
            Text(
                "On tolère la faute → voir chapitre 10",
                font_size=20,
                color=COL_DROP,
            )
            .next_to(cap, DOWN, buff=0.45)
            .set_x(0)
        )
        self.play(FadeIn(tease), run_time=0.6)
        self.wait(2.2)
