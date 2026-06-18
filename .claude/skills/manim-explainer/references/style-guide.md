# Style des animations explicatives BANO

Référence détaillée. Le SKILL.md couvre le workflow ; ce fichier couvre les
choix visuels et les pièges concrets rencontrés. Lis-le avant d'écrire une
animation, et garde-le ouvert pendant que tu codes les scènes.

## Table des matières
1. Identité visuelle
2. Couleurs : une couleur = un concept
3. Structure d'une animation
4. Rythme et durées
5. Registre grand public vs technique
6. Placement du texte : pas de légende collée en bas
7. Pièges d'animation (à connaître absolument)
8. Patterns de transition réutilisables

---

## 1. Identité visuelle

- **Police** : monospace `Consolas` (constante `MONO`) **partout, titres
  compris**. C'est le défaut GLOBAL du projet : `anim_common.py` appelle
  `Text.set_default(font=MONO)` à l'import, donc tout `Text(...)` hérite du
  monospace sans qu'on répète `font=MONO`. Avantage bonus : ça évite le bug
  d'espaces écrasés des petites polices Pango par défaut (vécu sur ce projet).
  Pour une exception ponctuelle, passe `font=` explicitement à ce `Text`.
- **Fond** : noir par défaut de Manim. Ne pas le changer.
- **Helpers** : importer depuis `anim_common.py` (`chip`, `file_box`,
  `quoted`, `csv_row`, `code_line`). Ne pas recopier ces fonctions dans
  chaque fichier — c'est exactement la duplication que le module évite.

## 2. Couleurs : une couleur = un concept

La règle d'or du projet : **chaque concept du sujet reçoit une couleur, et
la garde du début à la fin**. Si « le texte brut » est bleu en scène 1, il
reste bleu en scène 5. L'œil suit la couleur, pas le texte.

`anim_common.py` fournit une palette sémantique de base (`COL_SOURCE` bleu,
`COL_GREEN` résultat/mot, `COL_ACCENT` corail pour ce qu'on retire, etc.).
Définis tes propres alias en haut de l'animation avec un commentaire qui dit
à quoi chaque couleur correspond. Exemple :

```python
COL_RAW = "#4FC3F7"      # bleu  : adresse telle qu'elle est écrite
COL_STEP = "#AED581"     # vert  : texte en cours de nettoyage
COL_ACCENT = "#FF8A65"   # corail: accents (ce qu'on retire)
```

Couleurs « marque » fixes : Android vert `#3DDC84`.

## 3. Structure d'une animation

Une classe `Scene` unique, dont `construct()` appelle des méthodes
`scene_*` courtes — une par idée. C'est le squelette des chapitres `workflow_pipeline_ch*.py` :

```python
class MaPipeline(Scene):
    def construct(self):
        self.scene_intro()
        self.scene_etapes()
        self.scene_zoom()
        self.scene_resultat()
        self.scene_recap()
```

Avantages : on relit la structure d'un coup d'œil, on passe l'état entre
scènes via `self.xxx`, et on peut commenter une scène pour itérer vite.

Compte typique : **4 à 6 scènes**, ~55–60 s au total.

Chaque scène :
1. introduit son idée (un titre court, `to_edge(UP)`),
2. la déroule visuellement,
3. **nettoie derrière elle** (`FadeOut`) avant de passer la main, sauf les
   objets explicitement transmis à la scène suivante via `self.xxx`.

## 4. Rythme et durées

- Animations d'entrée : `run_time` 0.6–1.2 s.
- Transformations clés : 1.0–1.6 s.
- `self.wait(0.4)` à `wait(1.0)` pour laisser lire un point important.
- `LaggedStart(..., lag_ratio=0.15–0.35)` pour faire apparaître une série
  d'éléments l'un après l'autre (liste de mots, lignes d'un tableau).
- Terminer l'animation par un `FadeOut` de tout :
  `self.play(*[FadeOut(m) for m in self.mobjects], run_time=1.0)`.

## 5. Registre grand public vs technique

**Défaut = grand public.** Sauf demande explicite de version technique.

Grand public :
- AUCUN code à l'écran, AUCUN nom de fonction (`tokenize`, `normalize`),
  AUCUN identifiant technique (`U+0301`, `u64`, `FST`, `rid`).
- Langage du quotidien : « on découpe en mots », « on retire les accents »,
  « adresses enregistrées » / « ce que tape l'utilisateur ».
- Métaphores concrètes plutôt que termes exacts.
- Phrase finale qui ancre dans un cas réel : « *Église* retrouve bien
  *eglise*, accent ou pas ».
- Évite les tics de langage (« du coup », « enfin », « en fait »...) dans les
  textes à l'écran comme dans les commentaires : ça alourdit sans rien dire.

Technique (sur demande) :
- Extraits de code Rust via `code_line()`, termes exacts, vrais noms de
  fichiers (`index.fst`, `postings.bin`), détails comme `(position << 32) | longueur`.
- C'est le style des chapitres techniques (ex. `workflow_pipeline_ch7.py`).

## 6. Placement du texte : pas de légende collée en bas

Ne fixe pas les légendes au bas de l'écran avec `to_edge(DOWN)`. C'est
pénible à lire : l'œil est sur l'action (au centre/en haut) et doit faire un
aller-retour jusqu'en bas, souvent hors champ visuel. **Vécu sur ce projet.**

Règle : une légende vit **près de ce qu'elle décrit**. Utilise `next_to(obj,
DOWN, buff=...)` ancré sur l'objet concerné (la boîte, le mot, le schéma),
pas sur le bord de l'écran. Pour une accroche générale, mets-la **sous le
titre** (`next_to(title, DOWN)`), là où le regard se pose déjà.

- légende d'un résultat → `note.next_to(box, DOWN, buff=0.4)`
- légende d'une série de mots → `note.next_to(chips, DOWN, buff=0.6)`
- phrase de conclusion d'un schéma → `footer.next_to(diagramme, DOWN, buff=1.3)`

`to_edge(UP)` pour le **titre** reste la norme — c'est le bas qui pose
problème, pas le haut.

## 7. Pièges d'animation (à connaître absolument)

### Le faux « slide » de TransformFromCopy
`TransformFromCopy(texte_a, texte_b)` morph les glyphes lettre par lettre.
Si les deux textes se ressemblent (`EGALITE` → `egalite`) et sont alignés,
ça produit un glissement parasite qui distrait — l'œil voit « ça glisse »
au lieu de « ça se transforme ». **Vécu sur ce projet.**

Préfère, pour faire « converger N choses vers un résultat » :
```python
copies = [v.copy() for v in variants]
self.play(LaggedStart(
    *[c.animate.scale(0.3).move_to(cible.get_center()).set_opacity(0.0)
      for c in copies], lag_ratio=0.2), run_time=1.4)
self.play(GrowFromCenter(cible), Flash(cible, color=COL_GREEN, flash_radius=1.2))
```
Les copies filent vers la cible et disparaissent, puis le résultat apparaît
net. Pas de morphing de lettres.

### Alignement collinéaire
Si plusieurs objets partent vers une même cible et que l'un est pile aligné
(même y), son trajet droit paraît « sans raison » à côté des trajets
diagonaux des autres. Décale en y, ou utilise `LaggedStart`, ou la technique
ci-dessus.

### Transformer une chaîne « en place »
Pour montrer les étapes successives d'un nettoyage de texte, garde un objet
`current` et fais `Transform(current, nouvelle_version)` à chaque étape, la
nouvelle version repositionnée sur l'ancienne (`new.move_to(current)`).
L'effet « le même texte qui se nettoie » est très lisible.

### Accolades dans une f-string de code
`code_line(f"... {{ ... }}")` : doubler les accolades littérales `{{` `}}`
pour qu'elles ne soient pas interprétées par la f-string Python.

## 8. Patterns de transition réutilisables

- **Apparition d'une série** : `LaggedStart(*[FadeIn(x, shift=0.3*DOWN) for x in groupe], lag_ratio=0.2)`.
- **Mise en avant** : `SurroundingRectangle(obj, color=COL, buff=0.1)` + une
  note `next_to(box, RIGHT)`, puis `FadeOut` des deux.
- **Un objet « entre » dans un fichier** : `copie.animate.scale(0.3).move_to(file_box.get_center())` puis `FadeOut` + `Flash(file_box[0], color=COL)`.
- **Deux flux qui rejoignent un même traitement** (récap) : une boîte
  centrale + deux `Arrow` venant de gauche et de droite, couleurs des deux
  côtés.
