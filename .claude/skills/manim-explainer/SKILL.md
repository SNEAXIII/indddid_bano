---
name: manim-explainer
description: >-
  Crée, modifie ou rend des animations explicatives Manim pour ce projet BANO
  (moteur de recherche d'adresses Rust/Java). Utilise cette skill dès que
  l'utilisateur veut une vidéo ou une animation qui explique un module, un
  algorithme ou une étape du système (normalisation, tokenisation, build de
  l'index, recherche floue, structure FST, postings...), OU qu'il dit
  « anime », « fais une vidéo », « explique visuellement », « schéma animé »,
  « Manim », « comme le workflow_pipeline », même sans nommer Manim explicitement.
  Vaut aussi pour éditer/corriger une animation existante de demo/animations/.
---

# Animations explicatives Manim (projet BANO)

Ce projet explique son moteur de recherche d'adresses avec de courtes
animations Manim « grand public ». Des animations existent déjà dans
`demo/animations/` et servent de référence vivante :
`workflow_pipeline_ch1.py` … `workflow_pipeline_ch9.py` (le pipeline complet
en 9 chapitres, du CSV au scoring). Cette skill capture leur style pour en
produire de nouvelles, cohérentes entre elles.

## Avant de commencer

Lis **`references/style-guide.md`** — il contient la palette, la structure
des scènes, le rythme, le choix grand-public/technique, et surtout une liste
de **pièges d'animation** déjà rencontrés sur ce projet (le faux « slide »
de `TransformFromCopy`, l'alignement collinéaire...). Ne saute pas cette
lecture : ces pièges reviennent à chaque animation.

Regarde aussi le fichier de référence le plus proche de ton sujet :
- transformation de texte étape par étape → `workflow_pipeline_ch4.py` (Ch4Normalisation)
- flux de données / fichiers produits → `workflow_pipeline_ch7.py` (Ch7Fichiers)

## Registre par défaut : grand public

Sauf demande explicite de version technique, vise un public **non
technique** : aucun code à l'écran, aucun nom de fonction ni identifiant
(`tokenize`, `U+0301`, `u64`, `FST`, `rid`). Langage du quotidien,
métaphores concrètes, et une phrase finale ancrée dans un cas réel. Le
détail du contraste grand-public/technique est dans le style-guide §5.

Si l'utilisateur veut la version technique, le modèle est `workflow_pipeline_ch7.py`
(vrais noms de fichiers, détails de format binaire).

## Workflow

### 1. Cadrer le sujet
Identifie ce qu'on explique et découpe-le en **4 à 6 idées**, une par scène.
Pour un sujet « transformation » (une donnée qui change d'état), pense en
étapes successives. Pour un sujet « système » (des pièces qui collaborent),
pense en flux entre boîtes.

### 2. Mettre les helpers en place
Vérifie que `demo/animations/anim_common.py` existe. S'il n'existe pas,
copie-le depuis `assets/anim_common.py` de cette skill. Importe ce dont tu
as besoin :

```python
from manim import Create, FadeIn, FadeOut, Scene, Text, VGroup, Write  # etc. — pas de `import *`
from anim_common import MONO, chip, file_box, quoted, csv_row
```

Définis ensuite TES couleurs de concept en haut du fichier, une par concept,
avec un commentaire (voir style-guide §2).

### 3. Écrire les scènes
Une classe `Scene`, `construct()` qui appelle des méthodes `scene_*`
courtes. Chaque scène introduit son idée, la déroule, puis **nettoie
derrière elle** (`FadeOut`) sauf ce qu'elle transmet via `self.xxx`. Suis le
rythme et les patterns du style-guide (§4, §8). Et place les légendes près
de leur contenu, jamais collées en bas de l'écran (§6).

### 4. Rendre et vérifier — TOUJOURS
Rends d'abord en **basse qualité** pour itérer vite et attraper les erreurs.

**Passe TOUJOURS par les cibles `make`, jamais par `uv run manim` en direct.**
Le Makefile encapsule l'environnement uv (`demo/animations/pyproject.toml`), le
`cd`, et la qualité via `QUALITY=` (`l` 480p, `m` 720p, `h` 1080p défaut, `k`
4K). Lancer `uv run …` à la main contourne cette convention.

```bash
make anim-<sujet> QUALITY=l                                   # une anim, basse qualité (itération)
make anim-one ANIM_FILE=<f>.py ANIM_SCENE=<NomScene> QUALITY=l  # rendu ad hoc d'une scène
```

Vérifie la sortie : `Rendered <Scene>` + `Played N animations` = OK ; une
`Traceback` = à corriger. Le `.mp4` atterrit dans `demo/animations/media/`
(gitignored). Repasse en `QUALITY=h` une fois le visuel validé.

**Inspecter le rendu sans ouvrir de lecteur** (pour relire une frame en agent) :
`make anim-frame ANIM_SCENE=<NomScene> QUALITY=l [ANIM_AT=0.95]` extrait une
image PNG du clip (par défaut à 95 % du clip) dans `media/frames/<Scene>.png`,
qu'on peut relire directement. `ANIM_AT=0..1` choisit la position dans le clip.

**Itérer encore plus vite** : commente les autres scènes dans `construct()` pour
ne rendre que celle que tu ajustes ; garde le cache Manim ACTIF (défaut) — les
scènes inchangées ne sont pas re-rendues, ne mets jamais `--disable_caching`.

Pour un rendu final de **toutes** les anims d'un coup (vérif d'ensemble) :
`make anim` (ou `make anim QUALITY=l` pour aller vite).

### 5. Nommer le fichier et ajouter une cible make — obligatoire
**Nomme le fichier `<sujet>_pipeline.py`.** C'est la convention que
`make anim` exploite : cette cible rend automatiquement toutes les scènes de
chaque `*_pipeline.py` (via `manim -a`). Un fichier bien nommé est donc
inclus dans `make anim` sans rien configurer.

**Et donne quand même à l'anim sa propre cible make dédiée.** Chaque anim
doit être lançable par un nom court (pour itérer dessus sans rendre les
autres). Une anim sans cible make dédiée est une anim non terminée.

Ajoute-la dans le `Makefile` (section « Animation »), sur le modèle de
`anim-wf-ch4` / `anim-workflow` :

```makefile
anim-<sujet>: ## Anim de <sujet> (<NomScene>)
	$(MANIM) <sujet>_pipeline.py <NomScene>
```

Puis ajoute son nom à la liste `.PHONY` (sinon make peut la confondre avec un
fichier du même nom).

Récap des cibles existantes :
- `make anim` — rend **toutes** les anims (toutes les scènes de chaque
  `*_pipeline.py`). C'est le rendu « tout » de référence.
- `make anim-<sujet>` — une anim précise, pour itérer.
- `make anim-one ANIM_FILE=… ANIM_SCENE=…` — rendu générique d'une scène au
  coup par coup.

**Film à chapitres (plusieurs Scenes + montage).** `workflow_pipeline.py` est la
référence : 8 classes `Scene` (un chapitre = un clip), un montage continu via
`concat_chapters.py` (concat PyAV, pas besoin d'un ffmpeg système). Ses cibles,
à reproduire pour tout film de ce type :
- `make anim-workflow` — rend les 8 chapitres (`manim -a`).
- `make anim-wf-<chapitre>` — un chapitre précis (`apercu`, `donnees`, … ) pour
  itérer sans rendre les autres.
- `make anim-workflow-montage` — rend les chapitres puis monte le film continu.
- `make anim-frame ANIM_SCENE=<Chapitre> QUALITY=l` — capture une frame du clip
  (via `grab_frame.py`) dans `media/frames/` pour relire un chapitre sans lecteur.

Toute nouvelle cible doit être ajoutée à la liste `.PHONY`.

## Itération

Les animations sont visuelles et subjectives : on itère **à l'œil**, pas
avec des tests automatiques. Rends en basse qualité, regarde, ajuste. Quand
l'utilisateur signale un effet bizarre (ex. « ça glisse sans raison »),
c'est presque toujours un des pièges du style-guide §7 — va le relire avant
de bricoler.

## Erreurs à ne pas commettre

- **Recopier les helpers** dans chaque fichier au lieu d'importer
  `anim_common.py`. C'est la duplication que le module élimine.
- **Mettre du code ou du jargon** dans une anim grand public.
- **Oublier de rendre** avant de dire que c'est fini : une animation non
  rendue peut planter sur une `Traceback` invisible à la lecture.
- **Lancer `uv run manim` (ou `uv run python …`) à la main** au lieu des cibles
  `make`. Toujours passer par `make anim-…` / `make anim-one` : le Makefile
  encapsule l'env uv et la qualité. Si une commande manque, ajoute une cible.
- **Livrer une anim sans cible make dédiée** : chaque nouvelle animation doit
  avoir sa propre cible `anim-<sujet>` (+ entrée `.PHONY`). Sans ça, l'anim
  n'apparaît pas dans `make help` et personne ne la retrouve.
- **Changer la couleur d'un concept** en cours d'animation : l'œil perd le
  fil. Une couleur = un concept, du début à la fin.
- **Coller une légende en bas** (`to_edge(DOWN)`) : pénible à lire. Ancre-la
  près de son contenu avec `next_to(obj, DOWN)` (voir style-guide §6).
