"""Point d'entree de compatibilite pour le workflow BANO.

Les chapitres vivent dans:
workflow_pipeline_ch1.py ... workflow_pipeline_ch9.py.
Ce module re-exporte les Scene pour garder les commandes existantes:

    manim -ql workflow_pipeline.py Ch4Normalisation

Pour rendre TOUS les chapitres d'un coup, passe par le Makefile
(`make anim-workflow`), qui boucle sur workflow_pipeline_ch*.py — `manim -a`
sur ce module ne rendrait rien (il ignore les Scene importées).
"""
