"""Helpers partagés pour les animations explicatives Manim du projet BANO.

Copier ce fichier dans `demo/animations/` (s'il n'y est pas déjà) puis
l'importer depuis une animation :

    from anim_common import MONO, chip, file_box, quoted, csv_row

Ces helpers fixent l'identité visuelle commune (police monospace, badges
arrondis, boîtes de fichier, lignes de tableau). Les COULEURS de concept,
elles, se définissent DANS chaque animation : une couleur = un concept du
sujet traité, pour que l'œil suive « la même chose » d'une scène à l'autre.
"""

from manim import (
    BLACK,
    GREY_B,
    LEFT,
    RIGHT,
    RoundedRectangle,
    Text,
    VGroup,
    WHITE,
)

# Police monospace partagée : le sujet est technique (adresses, fichiers),
# le monospace aligne joliment et signale « donnée brute ».
MONO = "Consolas"

# Police PAR DÉFAUT, globale : tout `Text(...)` du projet hérite du monospace,
# titres compris. Importer ce module suffit à l'activer (exécuté à l'import).
# Évite de répéter `font=MONO` partout ET le bug d'espaces écrasés des petites
# polices Pango par défaut. Pour une exception ponctuelle : `Text(..., font=...)`.
Text.set_default(font=MONO)

# Quelques couleurs sémantiques réutilisables. Une animation peut en définir
# d'autres ; l'important est qu'UNE couleur colle à UN concept tout du long.
COL_SOURCE = "#4FC3F7"  # bleu   : donnée d'entrée / texte tel qu'écrit
COL_GREEN = "#AED581"  # vert   : résultat propre / mot / jeton
COL_ACCENT = "#FF8A65"  # corail : élément qu'on retire ou met en garde
COL_TEAL = "#4DB6AC"  # teal   : un fichier / un côté du système
COL_PURPLE = "#BA68C8"  # violet : un autre fichier / l'autre côté
COL_AMBER = "#FFD54F"  # jaune  : encore un autre fichier
COL_ORANGE = "#FFB74D"  # orange : variante chaude


def chip(txt: str, color=COL_GREEN, font_size=24) -> VGroup:
    """Badge arrondi plein contenant un mot/jeton. Texte en noir sur fond
    coloré : un « mot » devient une unité visuelle qu'on peut déplacer."""
    label = Text(txt, font=MONO, font_size=font_size, color=BLACK)
    box = RoundedRectangle(
        corner_radius=0.12,
        width=label.width + 0.4,
        height=label.height + 0.3,
        fill_color=color,
        fill_opacity=1.0,
        stroke_width=0,
    )
    label.move_to(box.get_center())
    return VGroup(box, label)


def file_box(name: str, color, width=3.0, height=1.0) -> VGroup:
    """Boîte contour + remplissage léger figurant un fichier produit."""
    rect = RoundedRectangle(
        corner_radius=0.15,
        width=width,
        height=height,
        stroke_color=color,
        stroke_width=3,
        fill_color=color,
        fill_opacity=0.15,
    )
    title = Text(name, font=MONO, font_size=24, color=color)
    title.move_to(rect.get_center())
    return VGroup(rect, title)


def quoted(txt: str, color=COL_GREEN, font_size=32) -> VGroup:
    """Le texte en cours, entre guillemets gris : montre qu'on manipule une
    chaîne, et permet de la transformer « en place » d'une étape à l'autre."""
    q1 = Text('"', font=MONO, font_size=font_size, color=GREY_B)
    body = Text(txt, font=MONO, font_size=font_size, color=color)
    q2 = Text('"', font=MONO, font_size=font_size, color=GREY_B)
    return VGroup(q1, body, q2).arrange(RIGHT, buff=0.05)


def csv_row(cells: list[str], xs: list[float], color=WHITE, font_size=22) -> VGroup:
    """Une ligne de tableau : cellules à des positions x fixes pour un
    alignement « colonnes ». `cells` et `xs` doivent avoir la même longueur."""
    cols = VGroup(
        *[Text(c, font=MONO, font_size=font_size, color=color) for c in cells]
    )
    for text, x in zip(cols, xs):
        text.move_to([x, 0, 0], aligned_edge=LEFT)
    return cols


def code_line(txt: str, font_size=22, color="#90A4AE") -> Text:
    """Une ligne de code monospace — UNIQUEMENT pour le registre technique.
    À éviter pour le grand public (voir le style-guide de la skill)."""
    return Text(txt, font=MONO, font_size=font_size, color=color)
