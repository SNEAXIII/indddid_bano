"""Chapitre 11 du workflow BANO : scoring et affichage Android."""

from workflow_pipeline_shared import (
    COL_ANDROID,
    COL_SCORE,
    COL_SRC,
    COL_TOK,
    QUERY_TYPO,
)

from anim_common import MONO, titled

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
    RED,
    RIGHT,
    RoundedRectangle,
    Scene,
    SurroundingRectangle,
    Text,
    UP,
    VGroup,
    WHITE,
    Write,
)


class Ch11Scoring(Scene):
    """Chapitre 11 — on classe les résultats : score + affichage sur Android."""

    def construct(self):
        title, sub = titled("On classe les résultats", "score", chapter=11)
        self.play(Write(title), run_time=1.0)
        self.play(FadeIn(sub), run_time=0.6)

        qbox = RoundedRectangle(
            corner_radius=0.15,
            width=5.8,
            height=0.8,
            stroke_color=COL_SRC,
            stroke_width=3,
            fill_color=COL_SRC,
            fill_opacity=0.10,
        ).move_to(UP * 1.9)
        qtext = Text(
            QUERY_TYPO, font=MONO, font_size=26, color=COL_SRC, t2c={"acasias": RED}
        ).move_to(qbox)
        qcap = Text("ce que tape l'utilisateur", font=MONO, font_size=20, color=GREY_B)
        qcap.next_to(qbox, UP, buff=0.12)
        self.play(FadeIn(qcap), FadeIn(qbox), FadeIn(qtext), run_time=0.8)
        self.wait(0.6)

        name = Text("Impasse des Acacias", font=MONO, font_size=24, color=WHITE)
        name.move_to(UP * 0.9)

        def pts_row(word, note, pts, y, word_t2c=None):
            w = Text(word, font=MONO, font_size=22, color=COL_TOK, t2c=word_t2c or {})
            w.move_to([-4.8, y, 0], aligned_edge=LEFT)
            n = Text(note, font=MONO, font_size=20, color=GREY_B)
            n.move_to([-0.4, y, 0], aligned_edge=LEFT)
            p = Text(pts, font=MONO, font_size=22, color=COL_SCORE)
            p.move_to([2.6, y, 0], aligned_edge=LEFT)
            return VGroup(w, n, p)

        r1 = pts_row("impasse", "mot exact", "+ 1.00", 0.35)
        r2 = pts_row("des", "mot exact", "+ 1.00", -0.15)
        r3 = pts_row(
            "acasias → acacias", "une faute", "+ 0.86", -0.65, word_t2c={"acasias": RED}
        )

        self.play(FadeIn(name, shift=0.2 * DOWN), run_time=0.6)
        self.play(
            LaggedStart(
                FadeIn(r1, shift=0.2 * RIGHT),
                FadeIn(r2, shift=0.2 * RIGHT),
                FadeIn(r3, shift=0.2 * RIGHT),
                lag_ratio=0.5,
            ),
            run_time=1.8,
        )
        self.wait(0.5)

        sep = Line([-4.8, -0.95, 0], [3.7, -0.95, 0], color=GREY_D, stroke_width=2)
        total = Text("score = 2.86", font=MONO, font_size=26, color=COL_SCORE)
        total.move_to([2.05, -1.35, 0], aligned_edge=LEFT)
        explain = VGroup(
            Text(
                "Une faute pénalise moins un mot long",
                font=MONO,
                font_size=20,
                color=GREY_A,
            ),
        ).arrange(DOWN, buff=0.12, aligned_edge=LEFT)
        explain.move_to([-4.8, -1.45, 0], aligned_edge=LEFT)
        self.play(Create(sep), run_time=0.4)
        self.play(FadeIn(total), FadeIn(explain), run_time=0.8)
        self.wait(1.2)

        winner = VGroup(
            Text("Impasse des Acacias", font=MONO, font_size=24, color=WHITE),
            Text("2.86", font=MONO, font_size=24, color=COL_SCORE),
        ).arrange(RIGHT, buff=0.6)
        winner.move_to(LEFT * 1.7 + UP * 0.1)
        win_box = SurroundingRectangle(winner, color=COL_SCORE, buff=0.15)
        self.play(
            FadeOut(VGroup(name, r1, r2, r3, sep, total, explain)),
            FadeIn(winner),
            run_time=0.9,
        )
        self.play(Create(win_box), run_time=0.5)

        phone = RoundedRectangle(
            corner_radius=0.2,
            width=1.9,
            height=3.0,
            stroke_color=COL_ANDROID,
            stroke_width=4,
        )
        screen = RoundedRectangle(
            corner_radius=0.1,
            width=1.6,
            height=2.5,
            fill_color=COL_ANDROID,
            fill_opacity=0.12,
            stroke_width=0,
        ).move_to(phone)
        result = Text(
            "Impasse\ndes Acacias\n01310\nSaint-Rémy",
            font=MONO,
            font_size=15,
            color=COL_ANDROID,
            line_spacing=0.8,
        ).move_to(screen)
        phone_grp = VGroup(phone, screen, result).to_edge(RIGHT, buff=1.0).set_y(0.1)
        arrow = Arrow(
            win_box.get_right() + RIGHT * 0.1,
            phone_grp.get_left() + LEFT * 0.1,
            color=GREY_B,
            buff=0.2,
        )
        self.play(GrowArrow(arrow), FadeIn(phone_grp), run_time=1.0)
        self.wait(0.6)

        footer = VGroup(
            Text(
                "« impasse des acasias » retrouve « Impasse des Acacias », faute comprise",
                font_size=22,
                color=GREY_A,
            ),
            Text(
                "on réaffiche l'adresse d'origine (avec accent) — jamais la clé",
                font_size=19,
                color=COL_SRC,
            ),
        ).arrange(DOWN, buff=0.22)
        footer.next_to(phone_grp, DOWN, buff=0.5).set_x(0)
        self.play(FadeIn(footer), run_time=0.9)
        self.wait(2.5)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=1.0)
