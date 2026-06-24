# Makefile — orchestration monorepo BANO
# Layout : data/ (CSV) · dataprep/ (download) · demo/ (rust+android) · bench/v1 (stockage) · bench/v2 (recherche)
# Usage  : `make` ou `make help`. Surcharge : `make v2-bench LIMIT=5`, `make data-force`, etc.

ROOT       := $(CURDIR)
DATA       := $(ROOT)/data
# CSV source partagé (voie,cp,ville)
STREETS    ?= $(DATA)/streets.csv
CARGO      ?= cargo
# Dossier du crate Rust (relatif) + raccourci pour entrer dedans dans les recettes.
RUSTDIR    := demo/rust/bano-fst
CD_RUST     = cd $(RUSTDIR) &&
CRATE      := $(ROOT)/$(RUSTDIR)
BIN         = ./target/release/bano-fst$(EXE)
# Sortie index FST (rust-index)
FST_OUT    ?= $(ROOT)/data/fst

# bench/v2 (recherche/autocomplétion)
V2_SHARED  ?= $(ROOT)/bench/v2/shared
QUERIES    ?= $(V2_SHARED)/queries.json
ARTIFACTS  ?= $(V2_SHARED)/artifacts
ANDROID_OUT?= $(V2_SHARED)/android
# Relatif à bench/v2/ -> bench/v2/reports
REPORTS    ?= reports

# Paramètres bench (surchargeables)
N          ?= 100
SEED       ?= 42
LIMIT      ?= 10
# Sous-échantillon BANO pour v2 (lignes chargées). Vide = jeu complet.
# Ex : make v2 ROWS=50000
ROWS       ?= 50000
MAXREC      = $(if $(ROWS),-m $(ROWS),)
# Requête pour `make rust-search Q="..."`
Q          ?=
# DEBUG=1 active les traces [DEBUG] du moteur (var d'env BANO_DEBUG).
DEBUG      ?=
DBG_ENV     = $(if $(DEBUG),BANO_DEBUG=1 ,)

# --- Spécificités Windows ---------------------------------------------------
# Sous Windows, make utilise cmd.exe par défaut -> pas de grep/awk/cp/rm ni de
# ./gradlew. On force le bash de Git pour que toutes les recettes (et help)
# tournent en POSIX, quel que soit le terminal (PowerShell, cmd, git bash).
# .exe : suffixe du binaire Rust. JBR valide pour le gradle CLI (le JAVA_HOME
# par défaut pointe un JBR cassé sur cette machine -> voir mémoire projet).
ifeq ($(OS),Windows_NT)
  EXE := .exe
  # bash de Git en chemin court DOS (PROGRA~1) : make découpe sur les espaces,
  # donc "Program Files" casserait. PAS System32\bash.exe (= WSL).
  # Surcharge si Git est ailleurs : make <cible> SHELL=C:/chemin/bash.exe
  SHELL := C:/PROGRA~1/Git/bin/bash.exe
  .SHELLFLAGS := -c
else
  EXE :=
endif
-include Makefile.local
GRADLEW     = cd demo/android && JAVA_HOME="$(GRADLE_JDK)" ./gradlew

.DEFAULT_GOAL := help

help: ## Affiche cette aide
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-18s\033[0m %s\n",$$1,$$2}'

# ===================== Données (BANO -> data/streets.csv) ====================

data: ## Télécharge le BANO et extrait data/streets.csv (skip si présent)
	cd dataprep && uv run python -m dataprep -o "$(STREETS)"

data-force: ## Régénère data/streets.csv même s'il existe
	cd dataprep && uv run python -m dataprep -o "$(STREETS)" --force

# ===================== Rust (demo/rust/bano-fst) ============================

rust-build: ## Compile la brique Rust en release
	$(CD_RUST) $(CARGO) build --release

rust-test: ## Lance les tests Rust
	$(CD_RUST) $(CARGO) test --release

rust-index: rust-build ## Construit l'index FST depuis streets.csv (STREETS=, FST_OUT=)
	$(CD_RUST) $(BIN) build "$(STREETS)" "$(FST_OUT)"

rust-search: rust-build ## Recherche FST : make rust-search Q="rue de la paix" [DEBUG=1]
	$(CD_RUST) $(DBG_ENV)$(BIN) search "$(FST_OUT)" "$(Q)" $(LIMIT)

# --- Mini-jeu 5 lignes (demo/rust/bano-fst/sample5.csv) pour comprendre le moteur
SAMPLE_CSV ?= sample5.csv
SAMPLE_IDX ?= sample5_index

sample-index: rust-build ## Build l'index du mini-jeu 5 lignes
	$(CD_RUST) $(BIN) build "$(SAMPLE_CSV)" "$(SAMPLE_IDX)"

sample-search: rust-build ## Cherche dans le mini-jeu : make sample-search Q="bourg bres" [DEBUG=1]
	$(CD_RUST) $(DBG_ENV)$(BIN) search "$(SAMPLE_IDX)" "$(Q)" $(LIMIT)

sample-demo: sample-index ## Build le mini-jeu + 1 recherche commentee (DEBUG force)
	$(CD_RUST) BANO_DEBUG=1 $(BIN) search "$(SAMPLE_IDX)" "$(if $(Q),$(Q),bourg bres)" $(LIMIT)

# --- Cibles mini-jeu avec DEBUG toujours ON (pas besoin de DEBUG=1) ----------
sample-debug: sample-index ## Mini-jeu : build + recherche, traces [DEBUG] ON (Q=, defaut "bourg bres")
	$(CD_RUST) BANO_DEBUG=1 $(BIN) search "$(SAMPLE_IDX)" "$(if $(Q),$(Q),bourg bres)" $(LIMIT)

sample-search-debug: rust-build ## Mini-jeu : recherche seule, traces [DEBUG] ON : make sample-search-debug Q="paris"
	$(CD_RUST) BANO_DEBUG=1 $(BIN) search "$(SAMPLE_IDX)" "$(if $(Q),$(Q),bourg bres)" $(LIMIT)

sample-index-debug: rust-build ## Mini-jeu : build de l'index avec traces [DEBUG] ON
	$(CD_RUST) BANO_DEBUG=1 $(BIN) build "$(SAMPLE_CSV)" "$(SAMPLE_IDX)"

# ===================== Android (demo/android, via Gradle) ===================
# Le plugin rust-android compile le .so ; generateBanoIndex remplit assets/index.

android-so: ## Compile bano_fst.so (cargoBuild, arm64 + x86_64)
	$(GRADLEW) cargoBuild

android-index: ## Construit l'index FST dans les assets de l'app
	$(GRADLEW) generateBanoIndex

android-debug: ## Build l'APK debug (cargo + index + assemble)
	$(GRADLEW) assembleDebug

android-install: ## Installe l'APK debug sur l'appareil connecté
	$(GRADLEW) installDebug

android-clean: ## Nettoie le build Gradle
	$(GRADLEW) clean

# ===================== Animation (demo/animations, via Manim) ===============
# Manim vit dans son propre projet uv (demo/animations/pyproject.toml) : le
# 1er `uv run manim` crée/synchronise .venv tout seul, puis réutilise l'env
# QUALITY : l (480p), m (720p), h (1080p, défaut), k (4K).
ANIM_DIR   ?= $(ROOT)/demo/animations
ANIM_FILE  ?= workflow_pipeline_ch0.py
ANIM_SCENE ?= Ch0Apercu
QUALITY    ?= h
MANIM       = cd "$(ANIM_DIR)" && uv run manim -q$(QUALITY)
# Dossier média correspondant à QUALITY (pour retrouver les MP4 à monter).
Q_DIR_l    := 480p15
Q_DIR_m    := 720p30
Q_DIR_h    := 1080p60
Q_DIR_k    := 2160p60
MONTAGE_QDIR = $(Q_DIR_$(QUALITY))

anim: ## Rend TOUTES les anims (chapitres du workflow) (QUALITY=)
	cd "$(ANIM_DIR)" && for f in workflow_pipeline_ch*.py; do uv run manim -q$(QUALITY) -a "$$f"; done

anim-one: ## Rend une anim précise (ANIM_FILE=, ANIM_SCENE=)
	$(MANIM) $(ANIM_FILE) $(ANIM_SCENE)

anim-preview: ## Rend en basse qualité et ouvre le lecteur (-p -ql)
	cd "$(ANIM_DIR)" && uv run manim -pql $(ANIM_FILE) $(ANIM_SCENE)

# Liste des chapitres -> prérequis : `make -jN anim-workflow` les rend en parallèle.
WF_CHAPTERS := anim-wf-ch0 anim-wf-ch1 anim-wf-ch2 anim-wf-ch3 anim-wf-ch4 \
               anim-wf-ch5 anim-wf-ch6 anim-wf-ch7 anim-wf-ch8 anim-wf-ch9 \
               anim-wf-ch10

anim-workflow: $(WF_CHAPTERS) ## Rend les 11 chapitres-clips (parallèle : make -j11 anim-workflow)

anim-workflow-montage: anim-workflow ## Workflow + montage continu (PyAV) (QUALITY=)
	cd "$(ANIM_DIR)" && uv run python concat_chapters.py $(MONTAGE_QDIR)

# Nombre de chapitres rendus en même temps (surcharge : make ... JOBS=4)
JOBS ?= 11
anim-workflow-par: ## Rend les 11 chapitres EN PARALLÈLE puis monte (JOBS=, QUALITY=)
	$(MAKE) -j$(JOBS) anim-workflow
	cd "$(ANIM_DIR)" && uv run python concat_chapters.py $(MONTAGE_QDIR)

WF_SCENES := Ch0Apercu Ch1Donnees Ch2Extraction Ch3Normalisation Ch4Tokenisation \
             Ch5Index Ch6Fst Ch7Fichiers Ch8Requete Ch9Levenshtein Ch10Scoring
SLIDES_OPTS := --offline -c auto_play_media=true -c controls=true

anim-present: ## Talk complet en diaporama HTML au clic -> present/talk.html (parallèle, JOBS=, QUALITY=)
	$(MAKE) -j$(JOBS) anim-workflow
	# On nettoie SEULEMENT les artefacts (pas le dossier present/ : un serveur
	# `anim-present-serve` actif le verrouille comme cwd sous Windows).
	cd "$(ANIM_DIR)" && rm -rf present/talk_assets present/talk.html && uv run manim-slides convert $(SLIDES_OPTS) $(WF_SCENES) present/talk.html

anim-present-serve: ## Sert present/ en HTTP (autoplay OK) : http://localhost:8000/talk.html
	cd "$(ANIM_DIR)/present" && uv run python -m http.server 8000

# --- Chapitres du workflow, un par un (pour itérer sur un seul clip) ---------
anim-wf-ch0: ## Workflow ch.0 — vue d'ensemble (Ch0Apercu)
	$(MANIM) workflow_pipeline_ch0.py Ch0Apercu

anim-wf-ch1: ## Workflow ch.1 — récupérer les données (Ch1Donnees)
	$(MANIM) workflow_pipeline_ch1.py Ch1Donnees

anim-wf-ch2: ## Workflow ch.2 — extraction streets.csv (Ch2Extraction)
	$(MANIM) workflow_pipeline_ch2.py Ch2Extraction

anim-wf-ch3: ## Workflow ch.3 — normalisation (Ch3Normalisation)
	$(MANIM) workflow_pipeline_ch3.py Ch3Normalisation

anim-wf-ch4: ## Workflow ch.4 — tokenisation (Ch4Tokenisation)
	$(MANIM) workflow_pipeline_ch4.py Ch4Tokenisation

anim-wf-ch5: ## Workflow ch.5 — construction de l'index (Ch5Index)
	$(MANIM) workflow_pipeline_ch5.py Ch5Index

anim-wf-ch6: ## Workflow ch.6 — le dictionnaire en arbre / FST (Ch6Fst)
	$(MANIM) workflow_pipeline_ch6.py Ch6Fst

anim-wf-ch7: ## Workflow ch.7 — l'index en fichiers binaires (Ch7Fichiers)
	$(MANIM) workflow_pipeline_ch7.py Ch7Fichiers

anim-wf-ch8: ## Workflow ch.8 — la requête côté Rust : normalise/tokenise/ET (Ch8Requete)
	$(MANIM) workflow_pipeline_ch8.py Ch8Requete

anim-wf-ch9: ## Workflow ch.9 — recherche Levenshtein (Ch9Levenshtein)
	$(MANIM) workflow_pipeline_ch9.py Ch9Levenshtein

anim-wf-ch10: ## Workflow ch.10 — scoring + résultats (Ch10Scoring)
	$(MANIM) workflow_pipeline_ch10.py Ch10Scoring

# Anim STANDALONE (hors film : pas un *_pipeline.py, pas dans le montage).
anim-flat-trie: ## Anim standalone : le trie aplati Java (FlatTrieDemo)
	$(MANIM) flat_trie.py FlatTrieDemo

# Extrait une frame d'un chapitre rendu (vérif visuelle). ANIM_SCENE= obligatoire.
# AT=0..1 (position, défaut 0.95). Sortie -> media/frames/<Scene>.png (ou OUT=).
ANIM_AT  ?= 0.95
anim-frame: ## Capture une frame d'un chapitre : make anim-frame ANIM_SCENE=Ch10Scoring QUALITY=l [ANIM_AT=0.95] [OUT=...]
	cd "$(ANIM_DIR)" && uv run python grab_frame.py $(ANIM_SCENE) --quality $(MONTAGE_QDIR) --at $(ANIM_AT) $(if $(OUT),--out "$(OUT)",)

# ===================== Bench v1 (formats de stockage) =======================
# Builders codent en dur "streets.csv" en cwd -> on le copie dans bench/v1/.

v1-data: ## Copie streets.csv dans bench/v1/
	cp "$(STREETS)" bench/v1/streets.csv

v1-build: v1-data ## Génère tous les fichiers (SQLite x4, Parquet, Arrow)
	cd bench/v1 && uv run python -m DatabaseBuilder.BANODatabaseBuilderNoJoinsRowid
	cd bench/v1 && uv run python -m DatabaseBuilder.BANODatabaseBuilderNoJoinsWoRowid
	cd bench/v1 && uv run python -m DatabaseBuilder.BANODatabaseBuilderJoinsRowid
	cd bench/v1 && uv run python -m DatabaseBuilder.BANODatabaseBuilderJoins2Rowid
	cd bench/v1 && uv run python -m ParquetBuilder.BANOParquetBuilderSimple
	cd bench/v1 && uv run python -m ArrowBuilder.BANOArrowBuilderSimple

v1-bench: ## Compare les formats générés (taille / lecture / requêtes)
	cd bench/v1 && uv run python benchmark.py

v1: v1-build v1-bench ## Pipeline v1 complet (build -> bench)

# ===================== Bench v2 (recherche / autocomplétion) ================

v2-queries: ## Génère le jeu de requêtes labellisé (N=, SEED=, ROWS=)
	cd bench/v2 && uv run python -m search_bench.queryset.generate -i "$(STREETS)" -o "$(QUERIES)" -n $(N) -s $(SEED) $(MAXREC)

v2-prebuild: ## Construit les artefacts UNE fois (+ manifest.json) (ROWS=)
	cd bench/v2 && uv run python -m search_bench.prebuild -i "$(STREETS)" -o "$(ARTIFACTS)" $(MAXREC)

v2-bench: ## Benchmark en RECHARGEANT les artefacts (rapide, + load_ms)
	cd bench/v2 && uv run python -m search_bench.bench.run --artifacts "$(ARTIFACTS)" -q "$(QUERIES)" -o $(REPORTS) --limit $(LIMIT)

v2-bench-build: ## Benchmark en (re)construisant les index (lent) (ROWS=)
	cd bench/v2 && uv run python -m search_bench.bench.run -i "$(STREETS)" -q "$(QUERIES)" -o $(REPORTS) --limit $(LIMIT) $(MAXREC)

v2-export-android: ## Exporte les survivantes (report.json) en SQLite Android
	cd bench/v2 && uv run python -m search_bench.export_android -a "$(ARTIFACTS)" -r $(REPORTS)/report.json -o "$(ANDROID_OUT)"

v2-test: ## Lance les tests pytest de bench/v2
	cd bench/v2 && uv run pytest -q

v2: v2-queries v2-prebuild v2-bench ## Pipeline v2 complet (queries -> prebuild -> bench)

# ===================== Nettoyage ============================================

clean: ## Supprime artefacts/rapports générés (bench v1/v2)
	rm -f bench/v1/streets.csv bench/v1/*.db bench/v1/*.parquet bench/v1/*.arrow
	rm -rf bench/v2/$(REPORTS) "$(ARTIFACTS)" "$(ANDROID_OUT)" "$(FST_OUT)"

.PHONY: help data data-force rust-build rust-test rust-index rust-search \
        sample-index sample-search sample-demo \
        sample-debug sample-search-debug sample-index-debug \
        android-so android-index android-debug android-install android-clean \
        anim anim-one anim-preview \
        anim-workflow anim-workflow-montage anim-workflow-par \
        anim-present anim-present-pptx anim-present-serve \
        anim-wf-ch0 anim-wf-ch1 anim-wf-ch2 anim-wf-ch3 anim-wf-ch4 \
        anim-wf-ch5 anim-wf-ch6 anim-wf-ch7 anim-wf-ch8 anim-wf-ch9 \
        anim-wf-ch10 anim-flat-trie anim-frame \
        v1-data v1-build v1-bench v1 \
        v2-queries v2-prebuild v2-bench v2-bench-build v2-export-android v2-test v2 \
        clean
