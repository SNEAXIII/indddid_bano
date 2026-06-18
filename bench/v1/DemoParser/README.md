# BANO Search

Application Android de recherche d'adresses BANO (Base Adresse Nationale Ouverte).

## Fonctionnalités

- Formulaire de recherche avec 3 champs :
    - **Voie** : Nom de la voie
    - **Code postal** : Code postal (5 chiffres)
    - **Ville** : Nom de la commune
- Affichage des résultats dans une liste

## Configuration de la base de données

L'application utilise la base SQLite `bano_no_joins_wo_rowid.db`.

### Structure de la table `adresses`

| Colonne     | Type | Description       |
|-------------|------|-------------------|
| nom_voie    | TEXT | Nom de la voie    |
| code_postal | TEXT | Code postal       |
| nom_commune | TEXT | Nom de la commune |

### Installation de la base

1. Copier le fichier `bano_no_joins_wo_rowid.db` dans le dossier `app/src/main/assets/`
2. L'application copiera automatiquement la base au premier lancement

## Structure du projet

```
app/src/main/java/com/sneaxiii/banoparser/
├── MainActivity.java                 # Activity hôte (bottom nav)
├── data/
│   ├── AddressRepository.java        # Repository singleton
│   ├── CSVAddressDataSource.java     # Source CSV (copie depuis assets)
│   └── SQLiteAddressDataSource.java  # Source SQLite (bano_no_joins_wo_rowid.db)
├── domain/
│   ├── model/
│   │   └── Address.java              # Modèle d'adresse
│   └── repository/
│       └── IAddressDataSource.java   # Interface de source de données
└── ui/
    ├── search/
    │   ├── SearchFragment.java       # Recherche
    │   ├── SearchViewModel.java      # ViewModel avec ExecutorService
    │   ├── SearchViewModelFactory.java
    │   └── AddressAdapter.java       # Adapter pour RecyclerView
    ├── suggestions/
    │   └── SuggestionsFragment.java  # Autocomplétion
    └── benchmark/
        └── BenchmarkFragment.java    # Mesures in-app
```

## Requirements

- Android Studio
- Java JDK 11+
- Android SDK 31+

