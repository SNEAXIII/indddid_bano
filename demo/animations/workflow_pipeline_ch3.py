"""Chapitre 3 du workflow BANO : extraction de streets.csv."""

from workflow_pipeline_shared import ADDR1, ADDR2, COL_DROP, COL_SRC, COL_TOK, COLS_X


from anim_common import MONO, csv_row, titled

from manim import (
    Create,
    Cross,
    DOWN,
    FadeIn,
    FadeOut,
    GREY_A,
    GREY_B,
    GREY_C,
    LEFT,
    LaggedStart,
    Line,
    ORIGIN,
    RIGHT,
    Scene,
    SurroundingRectangle,
    Text,
    UP,
    VGroup,
    WHITE,
    Write,
)


class Ch3Extraction(Scene):
    """Chapitre 3 — on ne garde que l'essentiel : extraction vers streets.csv."""

    def construct(self):
        title, sub = titled(
            "On ne garde que l'essentiel", "extraction → streets.csv", chapter=3
        )
        self.play(Write(title), run_time=1.0)
        self.play(FadeIn(sub), run_time=0.6)

        header = csv_row(
            ["voie", "code postal", "ville"], COLS_X, color=COL_SRC, font_size=22
        )
        header.shift(UP * 1.5)
        sep = Line(
            header.get_left() + LEFT * 0.1,
            header.get_right() + RIGHT * 0.4,
            color=GREY_C,
            stroke_width=2,
        )
        sep.next_to(header, DOWN, buff=0.15)

        r1 = csv_row(list(ADDR2), COLS_X, color=WHITE, font_size=22)
        r1.shift(UP * 0.7)
        r2 = csv_row(list(ADDR1), COLS_X, color=WHITE, font_size=22)
        r2.shift(ORIGIN)
        r3 = csv_row(list(ADDR1), COLS_X, color=GREY_B, font_size=22)
        r3.shift(DOWN * 0.7)

        label = Text("streets.csv", font=MONO, font_size=22, color=COL_SRC)
        label.next_to(header, UP, buff=0.35, aligned_edge=LEFT)

        self.play(FadeIn(label), FadeIn(header), Create(sep), run_time=0.9)
        self.play(
            LaggedStart(
                FadeIn(r1, shift=0.2 * DOWN),
                FadeIn(r2, shift=0.2 * DOWN),
                FadeIn(r3, shift=0.2 * DOWN),
                lag_ratio=0.35,
            ),
            run_time=1.6,
        )
        self.wait(0.6)

        dup = Text("en double", font=MONO, font_size=20, color=COL_DROP).next_to(
            r3, RIGHT, buff=0.5
        )
        cross = Cross(r3, stroke_color=COL_DROP, stroke_width=4)
        self.play(FadeIn(dup), Create(cross), run_time=0.8)
        self.wait(0.6)
        dedup_note = Text(
            "on retire les adresses en double", font=MONO, font_size=22, color=GREY_A
        )
        dedup_note.next_to(r2, DOWN, buff=1.0)
        self.play(
            FadeOut(VGroup(r3, cross, dup), shift=0.3 * DOWN),
            FadeIn(dedup_note),
            run_time=0.9,
        )
        self.wait(1.0)

        box = SurroundingRectangle(r2, color=COL_SRC, buff=0.12)
        note = Text(
            "On ne retient que les adresses uniques",
            font=MONO,
            font_size=22,
            color=COL_SRC,
        )
        note.move_to(dedup_note)
        self.play(FadeOut(dedup_note), Create(box), FadeIn(note), run_time=0.9)
        self.wait(1.0)

        lines = Text(
            "26,5 millions d'adresses  →  2,2 millions d'adresses uniques",
            font=MONO,
            font_size=22,
            color=COL_TOK,
        )
        lines.next_to(note, DOWN, buff=0.5)
        saved = Text(
            "≈ 24 millions d'adresses en double économisées",
            font=MONO,
            font_size=20,
            color=GREY_B,
        )
        saved.next_to(lines, DOWN, buff=0.25)
        size = Text("2 Go  →  80 Mo", font=MONO, font_size=24, color=COL_TOK)
        size.next_to(saved, DOWN, buff=0.45)
        self.play(FadeIn(lines), run_time=0.7)
        self.play(FadeIn(saved), run_time=0.6)
        self.play(FadeIn(size), run_time=0.7)
        self.wait(2.0)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=1.0)
