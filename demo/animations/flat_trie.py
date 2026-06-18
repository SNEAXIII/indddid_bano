"""Animation STANDALONE (hors film workflow) : le trie aplati du moteur Java.

NON liée au montage : le fichier n'est PAS nommé `*_pipeline.py`, donc `make anim`
et `concat_chapters.py` ne le ramassent pas. Lancement dédié : `make anim-flat-trie`.

Idée expliquée (registre semi-technique nommé) :
  1. un trie = arbre de préfixes (mêmes branches partagées que le FST) ;
  2. on NUMÉROTE les nœuds en préordre (profondeur d'abord) ;
  3. on APLATIT : nœud i -> case i d'un tableau d'entiers (pas de pointeurs) ;
  4. propriété clé : le sous-arbre d'un nœud = une TRANCHE CONTIGUË [i, subtreeEnd)
     -> « tous les mots qui commencent par X » = un balayage de tableau.
"""

from workflow_pipeline_shared import COL_INDEX, COL_TOK, COL_SRC, COL_POST

from anim_common import MONO, titled

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
    Indicate,
    LEFT,
    LaggedStart,
    Line,
    RIGHT,
    Rectangle,
    Scene,
    SurroundingRectangle,
    Text,
    UP,
    VGroup,
    WHITE,
    Write,
)


def node(pos, final=False):
    c = Circle(radius=0.2, stroke_color=COL_INDEX, stroke_width=3,
               fill_color=BLACK, fill_opacity=1.0).move_to(pos)
    grp = VGroup(c)
    if final:
        grp.add(Circle(radius=0.12, stroke_color=COL_TOK, stroke_width=3).move_to(pos))
    return grp


def edge(a, b, letter, off):
    line = Line(a.get_center(), b.get_center(), color=GREY_B, stroke_width=3, buff=0.21)
    lab = Text(letter, font=MONO, font_size=22, color=WHITE).move_to(line.get_center() + off)
    return VGroup(line, lab)


# Trie de rue / ruelle / remy. IDs = ordre PRÉORDRE (enfants triés par code point :
# 'e'(101) avant 'u'(117) sous le 'r'). C'est ce qui rend le sous-arbre contigu.
POS = {
    0: [-5.5, 0.8, 0],   # racine
    1: [-4.4, 0.8, 0],   # r
    2: [-3.3, -0.2, 0],  # e (remy)
    3: [-2.2, -0.2, 0],  # m
    4: [-1.1, -0.2, 0],  # y   -> remy
    5: [-3.3, 1.8, 0],   # u (rue/ruelle)
    6: [-2.2, 1.8, 0],   # e   -> rue
    7: [-1.1, 1.8, 0],   # l
    8: [0.0, 1.8, 0],    # l
    9: [1.1, 1.8, 0],    # e   -> ruelle
}
FINALS = {4, 6, 9}
WORD = {4: "remy", 6: "rue", 9: "ruelle"}
EDGES = [
    (0, 1, "r", UP * 0.3),
    (1, 2, "e", DOWN * 0.18 + LEFT * 0.16),
    (2, 3, "m", DOWN * 0.3),
    (3, 4, "y", DOWN * 0.3),
    (1, 5, "u", UP * 0.18 + LEFT * 0.16),
    (5, 6, "e", UP * 0.3),
    (6, 7, "l", UP * 0.3),
    (7, 8, "l", UP * 0.3),
    (8, 9, "e", UP * 0.3),
]


class FlatTrieDemo(Scene):
    """Le trie aplati : arbre de préfixes rangé en tableaux, sous-arbre = tranche."""

    def construct(self):
        self.title, self.sub = titled("Le trie aplati", "un arbre de préfixes rangé en tableaux")
        self.play(Write(self.title), run_time=1.0)
        self.play(FadeIn(self.sub), run_time=0.6)

        self.build_tree()
        self.scene_arbre()
        self.scene_preordre()
        self.scene_aplatir()
        self.scene_slice()
        self.scene_recap()

        self.play(*[FadeOut(m) for m in self.mobjects], run_time=1.0)

    def build_tree(self):
        self.nodes = {i: node(p, final=(i in FINALS)) for i, p in POS.items()}
        self.edges = {(a, b): edge(self.nodes[a], self.nodes[b], l, o) for (a, b, l, o) in EDGES}
        self.labels = {
            4: Text("remy", font=MONO, font_size=18, color=COL_TOK).next_to(self.nodes[4], DOWN, buff=0.18),
            6: Text("rue", font=MONO, font_size=18, color=COL_TOK).next_to(self.nodes[6], UP, buff=0.18).shift(LEFT * 0.25),
            9: Text("ruelle", font=MONO, font_size=18, color=COL_TOK).next_to(self.nodes[9], UP, buff=0.18),
        }
        # Cases du tableau (créées ici, montrées à l'aplatissement).
        self.cells = {}
        for i in range(10):
            x = -5.4 + i * 1.2
            sq = Rectangle(width=1.0, height=0.8, stroke_color=GREY_B, stroke_width=2,
                           fill_color=COL_INDEX, fill_opacity=0.08).move_to([x, -2.3, 0])
            idx = Text(str(i), font=MONO, font_size=20, color=GREY_A).move_to(sq.get_center())
            self.cells[i] = VGroup(sq, idx)

    def scene_arbre(self):
        self.play(FadeIn(self.nodes[0]), run_time=0.3)
        self.play(
            LaggedStart(*[FadeIn(VGroup(self.edges[(a, b)], self.nodes[b]))
                          for (a, b, *_ ) in EDGES], lag_ratio=0.4),
            run_time=2.2,
        )
        self.play(*[FadeIn(l) for l in self.labels.values()], run_time=0.6)
        cap = Text("un trie : préfixes partagés (comme le FST)", font_size=20, color=GREY_A).move_to([0, -3.3, 0])
        self.play(FadeIn(cap), run_time=0.5)
        self.wait(1.2)
        self.play(FadeOut(cap), run_time=0.4)

    def scene_preordre(self):
        cap = Text("on numérote les nœuds en profondeur d'abord (préordre)",
                   font_size=20, color=COL_POST).move_to([0, -3.3, 0])
        self.play(FadeIn(cap), run_time=0.5)
        # Les numéros apparaissent DANS l'ordre des IDs (= préordre).
        self.num = {}
        anims = []
        for i in range(10):
            t = Text(str(i), font=MONO, font_size=18, color=COL_POST)
            t.move_to(self.nodes[i].get_center())
            self.num[i] = t
        self.play(LaggedStart(*[FadeIn(self.num[i]) for i in range(10)], lag_ratio=0.35),
                  run_time=2.6)
        self.wait(1.0)
        self.play(FadeOut(cap), run_time=0.4)

    def scene_aplatir(self):
        cap = Text("aplati : nœud i  →  case i (des tableaux d'entiers, zéro pointeur)",
                   font_size=20, color=GREY_A).move_to([0, -3.45, 0])
        self.play(FadeIn(cap), run_time=0.5)
        # Chaque nœud (avec son numéro) envoie une copie dans sa case.
        flights = []
        for i in range(10):
            src = VGroup(self.nodes[i], self.num[i]).copy()
            flights.append(src.animate.move_to(self.cells[i][0].get_center()).scale(0.4).set_opacity(0.0))
        self.play(LaggedStart(*flights, lag_ratio=0.12), run_time=1.8)
        self.play(LaggedStart(*[FadeIn(self.cells[i]) for i in range(10)], lag_ratio=0.12),
                  run_time=1.4)
        # Marque les cases finales = des mots.
        for i, w in WORD.items():
            self.cells[i][0].set_fill(COL_TOK, opacity=0.18)
            lab = Text(w, font=MONO, font_size=13, color=COL_TOK).next_to(self.cells[i], DOWN, buff=0.12)
            self.cells[i].add(lab)
            self.play(FadeIn(lab), run_time=0.2)
        self.wait(1.0)
        self.play(FadeOut(cap), run_time=0.4)

    def scene_slice(self):
        cap = Text("« commence par rue » = le sous-arbre du nœud 6",
                   font_size=20, color=COL_SRC).move_to([0, -3.45, 0])
        self.play(FadeIn(cap), run_time=0.5)
        # Sous-arbre de 6 = nœuds 6,7,8,9 (= rue, ruelle). remy (4) est AILLEURS.
        sub = [6, 7, 8, 9]
        tree_box = SurroundingRectangle(VGroup(*[self.nodes[i] for i in sub]),
                                        color=COL_SRC, buff=0.15)
        self.play(Create(tree_box), run_time=0.6)
        self.play(*[Indicate(self.nodes[i], color=COL_SRC, scale_factor=1.3) for i in sub],
                  run_time=0.6)
        self.wait(0.4)
        # ... et dans le tableau : une TRANCHE CONTIGUË [6, 10).
        arr_box = SurroundingRectangle(VGroup(*[self.cells[i] for i in sub]),
                                       color=COL_SRC, buff=0.1)
        slice_lbl = Text("tranche [6, 10) — contiguë", font=MONO, font_size=18, color=COL_SRC)
        slice_lbl.next_to(arr_box, UP, buff=0.15)
        self.play(Create(arr_box), FadeIn(slice_lbl), run_time=0.8)
        self.wait(0.6)
        # remy est HORS de la tranche.
        out = SurroundingRectangle(self.cells[4], color=GREY_B, buff=0.08)
        out_lbl = Text("remy : hors tranche", font=MONO, font_size=15, color=GREY_B)
        out_lbl.next_to(self.cells[4], UP, buff=0.15)
        self.play(Create(out), FadeIn(out_lbl), run_time=0.7)
        self.wait(1.6)
        self.play(FadeOut(VGroup(cap, tree_box, arr_box, slice_lbl, out, out_lbl)), run_time=0.5)

    def scene_recap(self):
        # On nettoie l'arbre + le tableau pour laisser le punch seul, centré.
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.6)
        punch = Text(
            "Sous-arbre = tranche contiguë de tableau.\n"
            "Préfixe trouvé par balayage — pas de pointeurs, cache-friendly.",
            font_size=24, color=WHITE, line_spacing=0.9,
        ).move_to([0, 0, 0])
        self.play(FadeIn(punch), run_time=0.8)
        self.wait(2.2)
