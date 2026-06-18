# Spécifications Techniques - Application BANO Performance Benchmark

## 1. Vue d'ensemble du projet

### 1.1 Description générale
Application Android de benchmark de performances pour la recherche d'adresses dans la base BANO (Base Adresse Nationale Ouverte). L'objectif principal est de **comparer les performances de différents formats de stockage de données** pour déterminer lequel offre les meilleures performances de lecture et de recherche sur Android.

### 1.2 Informations du projet
- **Nom de l'application** : BANO Performance Benchmark
- **Package** : `com.sneaxiii.banoparser`
- **Type** : Application Android native (Java)
- **Version** : 1.0 (versionCode: 1)

### 1.3 Objectifs principaux
- **🎯 Comparer les performances** de différents formats de stockage de données
- **⏱️ Mesurer les temps de recherche** pour chaque format avec des critères identiques
- **📊 Afficher les métriques de performance** (temps de chargement, temps de recherche, utilisation mémoire)
- **🔄 Permettre des tests reproductibles** avec les mêmes requêtes sur tous les formats
- Fournir une interface simple de recherche d'adresses avec sélection du format

### 1.4 Formats de stockage à comparer

| Format | Statut | Description | Avantages potentiels |
|--------|--------|-------------|---------------------|
| **SQLite** | ✅ Implémenté | Base de données relationnelle | Indexation, requêtes SQL optimisées |
| **Parquet** | 🚧 À implémenter | Format columnar Apache Arrow | Compression efficace, lecture columnar |
| **CSV** | 📋 Planifié | Fichier texte séparé par virgules | Simple, léger |
| **JSON** | 📋 Planifié | Fichiers JSON | Flexible, lisible |
| **Protocol Buffers** | 📋 Planifié | Format binaire Google | Compact, rapide à parser |

---

## 2. Spécifications techniques

### 2.1 Configuration Android

#### Versions SDK
- **compileSdk** : 35
- **minSdk** : 21 (Android 5.0 Lollipop)
- **targetSdk** : 35 (Android 15)

#### Versions Java
- **sourceCompatibility** : Java 8
- **targetCompatibility** : Java 8

#### Build System
- **Gradle Plugin** : 8.7.1
- **Gradle Wrapper** : Compatible avec le plugin

### 2.2 Dépendances

#### Bibliothèques principales
```gradle
androidx.appcompat:appcompat:1.7.0
com.google.android.material:material:1.12.0
androidx.constraintlayout:constraintlayout:2.2.0
androidx.annotation:annotation:1.9.1
```

#### Architecture Components
```gradle
androidx.lifecycle:lifecycle-livedata-ktx:2.8.7
androidx.lifecycle:lifecycle-viewmodel-ktx:2.8.7
```

#### Bibliothèques pour formats de données
```gradle
// Apache Arrow/Parquet pour lecture de fichiers Parquet
org.apache.arrow:arrow-memory-netty:latest
org.apache.arrow:arrow-vector:latest
org.apache.parquet:parquet-avro:latest (ou parquet-arrow)

// Gson pour parsing JSON (si nécessaire)
com.google.code.gson:gson:2.10.1

// Protocol Buffers (planifié)
com.google.protobuf:protobuf-javalite:latest
```

#### Tests
```gradle
junit:junit:4.13.2 (tests unitaires)
androidx.test.ext:junit:1.2.1 (tests instrumentés)
androidx.test.espresso:espresso-core:3.6.1 (tests UI)
```

### 2.3 Features activées
- **ViewBinding** : Activé pour une liaison de vue type-safe
- **AndroidX** : Activé
- **NonTransitiveRClass** : Activé pour réduire la taille des classes R

---

## 3. Architecture de l'application

### 3.1 Pattern architectural
L'application suit le pattern **MVVM (Model-View-ViewModel)** avec les principes suivants :
- Séparation claire des responsabilités
- Utilisation de LiveData pour l'observation réactive des données
- **Strategy Pattern** pour les différentes implémentations de lecture de données
- Repository pattern pour l'accès aux données avec abstraction du format
- ViewModel pour la gestion de l'état UI et des métriques de performance
- ExecutorService pour les opérations asynchrones

### 3.2 Structure des packages

```
com.sneaxiii.banoparser/
├── data/
│   ├── model/
│   │   ├── Address.java                    # Modèle de données commun
│   │   └── BenchmarkResult.java            # Métriques de performance
│   ├── datasource/
│   │   ├── DataSource.java                 # Interface commune
│   │   ├── SQLiteDataSource.java           # Implémentation SQLite
│   │   ├── ParquetDataSource.java          # Implémentation Parquet
│   │   ├── CsvDataSource.java              # Implémentation CSV (planifié)
│   │   └── JsonDataSource.java             # Implémentation JSON (planifié)
│   └── AddressRepository.java              # Repository avec sélection du format
├── benchmark/
│   ├── BenchmarkManager.java               # Gestion des benchmarks
│   └── PerformanceMetrics.java             # Mesure des performances
└── ui/
    └── search/
        ├── SearchActivity.java             # Activity principale
        ├── SearchViewModel.java            # Logique métier et benchmarks
        ├── SearchViewModelFactory.java     # Factory pour injection
        └── AddressAdapter.java             # Adapter RecyclerView
```

### 3.3 Concepts clés

#### Interface DataSource
Tous les formats de données implémentent une interface commune :
```java
public interface DataSource {
    void initialize(Context context) throws IOException;
    List<Address> search(String street, String postalCode, String city);
    BenchmarkResult getLastBenchmark();
    void close();
    String getFormatName();
}
```

#### BenchmarkResult
Contient les métriques de performance pour chaque recherche :
- Temps d'initialisation (ms)
- Temps de recherche (ms)
- Nombre de résultats
- Mémoire utilisée (MB)
- Format de données utilisé

---

## 4. Couche de données

### 4.1 Formats de données supportés

#### 4.1.1 SQLite (✅ Implémenté)

**Nom du fichier** : `bano_no_joins_wo_rowid.db`

**Localisation** :
- **Dans les assets** : `app/src/main/assets/bano_no_joins_wo_rowid.db`
- **Après copie** : `[app_data_dir]/databases/bano_no_joins_wo_rowid.db`

**Structure de la table `adresses`** :

| Colonne | Type | Description | Indexation |
|---------|------|-------------|------------|
| nom_voie | TEXT | Nom de la voie | ✅ Index recommandé |
| code_postal | TEXT | Code postal (5 chiffres) | ✅ Index recommandé |
| nom_commune | TEXT | Nom de la commune | ✅ Index recommandé |

**Note** : La base utilise l'option `WITHOUT ROWID` pour optimiser l'espace et les performances.

**Logique de requête SQL** :
```sql
SELECT nom_voie, code_postal, nom_commune 
FROM adresses 
WHERE 1=1
  [AND nom_voie LIKE '%{street}%']       -- Si street non vide
  [AND code_postal = '{postalCode}']    -- Si postalCode non vide
  [AND nom_commune LIKE '%{city}%']     -- Si city non vide
LIMIT 100
```

**Avantages** :
- Indexation native pour recherches rapides
- Support SQL avec opérateurs LIKE
- Optimisé pour Android (intégré au système)

**Inconvénients** :
- Taille de fichier importante
- Nécessite copie depuis assets au premier lancement

#### 4.1.2 Parquet (🚧 À implémenter)

**Nom du fichier** : `bano_simple.parquet`

**Localisation** :
- **Dans les assets** : `app/src/main/assets/bano_simple.parquet`
- **Après copie** : `[app_data_dir]/files/bano_simple.parquet`

**Schéma Parquet** :
```
nom_voie: STRING
code_postal: STRING
nom_commune: STRING
```

**Bibliothèques** :
- Apache Arrow pour lecture des données
- Parquet pour format de fichier

**Stratégie de recherche** :
- Lecture columnar pour optimisation mémoire
- Filtrage en mémoire après lecture
- Utilisation de Row Groups pour lecture partielle

**Avantages** :
- Compression très efficace (taille réduite)
- Lecture columnar (seulement les colonnes nécessaires)
- Format standard Big Data

**Inconvénients** :
- Pas d'indexation native
- Nécessite lecture et filtrage en mémoire
- Bibliothèques tierces requises

#### 4.1.3 CSV (📋 Planifié)

**Nom du fichier** : `bano_simple.csv`

**Localisation** :
- **Dans les assets** : `app/src/main/assets/bano_simple.csv`
- **Après copie** : `[app_data_dir]/files/bano_simple.csv`

**Format** :
```csv
nom_voie,code_postal,nom_commune
"Voie de la Paix","75001","Paris"
```

**Stratégie de recherche** :
- Lecture ligne par ligne
- Filtrage en mémoire
- Parser CSV natif ou bibliothèque tierce

**Avantages** :
- Format simple et universel
- Lisible par humain
- Pas de dépendances

**Inconvénients** :
- Pas de compression
- Lecture séquentielle uniquement
- Performances potentiellement faibles

#### 4.1.4 JSON (📋 Planifié)

**Nom du fichier** : `bano_simple.json`

**Localisation** :
- **Dans les assets** : `app/src/main/assets/bano_simple.json`
- **Après copie** : `[app_data_dir]/files/bano_simple.json`

**Format** :
```json
[
  {"nom_voie": "Voie de la Paix", "code_postal": "75001", "nom_commune": "Paris"},
  ...
]
```

**Avantages** :
- Format structuré et flexible
- Parsers efficaces disponibles (Gson, Moshi)
- Lisible par humain

**Inconvénients** :
- Taille de fichier importante
- Nécessite chargement complet en mémoire
- Pas d'indexation

### 4.2 Modèle de données (Address.java)

#### Attributs
```java
- String street          // Nom de la voie
- String postalCode      // Code postal
- String city            // Nom de la ville
- String houseNumber     // Numéro de voie (optionnel)
- double latitude        // Latitude (optionnel)
- double longitude       // Longitude (optionnel)
```

#### Constructeurs
- `Address(String street, String postalCode, String city)`
- `Address(String street, String postalCode, String city, String houseNumber, double latitude, double longitude)`

#### Méthodes publiques
- `String getFullAddress()` : Retourne l'adresse complète formatée
- Getters pour tous les attributs

### 4.3 Modèle BenchmarkResult

#### Attributs
```java
- String formatName          // Nom du format (SQLite, Parquet, etc.)
- long initTimeMs            // Temps d'initialisation (ms)
- long searchTimeMs          // Temps de recherche (ms)
- int resultCount            // Nombre de résultats trouvés
- long memoryUsedMb          // Mémoire utilisée (MB)
- long fileSizeMb            // Taille du fichier de données (MB)
- String timestamp           // Date/heure du benchmark
```

#### Méthodes publiques
- `String getFormattedSummary()` : Résumé formaté des métriques
- Getters pour tous les attributs
- Méthodes de comparaison avec d'autres résultats

### 4.4 Repository (AddressRepository.java)

#### Pattern
**Singleton** avec initialisation thread-safe (Double-Checked Locking)

#### Méthodes publiques
- `static AddressRepository getInstance(Context context)` : Obtenir l'instance unique
- `void setDataSource(DataSource dataSource)` : Changer le format de données
- `List<Address> searchAddresses(String street, String postalCode, String city)` : Rechercher des adresses
- `BenchmarkResult getLastBenchmarkResult()` : Récupérer les métriques de la dernière recherche
- `List<DataSource> getAvailableDataSources()` : Liste des formats disponibles
- `void close()` : Fermer la connexion active

#### Avantages
- Point d'accès unique aux données
- Abstraction complète du format de stockage
- Facilite le changement dynamique de format
- Gestion centralisée des benchmarks

---

## 5. Couche présentation (UI)

### 5.1 SearchActivity

#### Rôle
Activity principale et unique de l'application. Point d'entrée de l'application (LAUNCHER).

#### Composants UI (ViewBinding)
- `EditText streetInput` : Champ de saisie pour la voie
- `EditText postalCodeInput` : Champ de saisie pour le code postal (5 chiffres max)
- `EditText cityInput` : Champ de saisie pour la ville
- `Button searchButton` : Bouton de recherche
- `ProgressBar loading` : Indicateur de chargement
- `RecyclerView resultsRecyclerView` : Liste des résultats

#### Fonctionnalités
1. **Saisie utilisateur** : 3 champs de recherche avec hints
2. **Validation** : Code postal limité à 5 chiffres numériques
3. **Recherche déclenchée par** :
   - Clic sur le bouton "Rechercher"
   - Touche "Entrée" sur le clavier (IME_ACTION_SEARCH)
4. **Feedback visuel** :
   - ProgressBar pendant la recherche
   - Toast si aucun résultat
   - Toast en cas d'erreur

#### Cycle de vie
- Observe les LiveData du ViewModel
- Affiche automatiquement les résultats via l'Adapter

### 5.2 SearchViewModel

#### Rôle
Gère la logique métier de la recherche et maintient l'état UI.

#### LiveData exposées
- `LiveData<List<Address>> searchResults` : Résultats de la recherche
- `LiveData<String> searchError` : Messages d'erreur

#### Méthodes publiques
- `void search(String street, String postalCode, String city)` : Lance une recherche asynchrone

#### Gestion de la concurrence
- **ExecutorService** : SingleThreadExecutor pour les recherches en background
- **postValue()** : Mise à jour thread-safe des LiveData
- **onCleared()** : Arrêt propre de l'ExecutorService

#### Avantages
- Survit aux changements de configuration (rotation d'écran)
- Séparation de la logique métier et de l'UI
- Gestion automatique du cycle de vie

### 5.3 SearchViewModelFactory

#### Rôle
Factory pour créer le SearchViewModel avec injection de dépendances.

#### Dépendances injectées
- `AddressRepository` : Récupéré via getInstance(context)

### 5.4 AddressAdapter

#### Rôle
Adapter pour afficher la liste des adresses dans le RecyclerView.

#### Layout utilisé
`android.R.layout.simple_list_item_2` (layout système à 2 lignes)

#### Affichage
- **Ligne 1 (text1)** : Nom de la voie
- **Ligne 2 (text2)** : Code postal + ville (format : "75001 Paris")

#### Méthodes publiques
- `void setAddresses(List<Address> addresses)` : Met à jour la liste
- `void clearAddresses()` : Vide la liste

---

## 6. Interface utilisateur (Layout)

### 6.1 Fichier layout principal
`activity_search.xml`

### 6.2 Structure
```
ConstraintLayout (conteneur principal)
├── TextView (title) : "Recherche d'adresses"
├── EditText (streetInput) : Champ voie
├── EditText (postalCodeInput) : Champ code postal
├── EditText (cityInput) : Champ ville
├── Button (searchButton) : Bouton de recherche
├── ProgressBar (loading) : Indicateur de chargement (initialement invisible)
└── RecyclerView (resultsRecyclerView) : Liste des résultats
```

### 6.3 Contraintes de layout
- Disposition verticale des éléments
- Marges standard définies dans `dimens.xml`
- RecyclerView occupe l'espace restant en bas

### 6.4 Ressources textuelles (strings.xml)

| Clé | Valeur | Usage |
|-----|--------|-------|
| app_name | "BANO Search" | Nom de l'application |
| search_title | "Recherche d'adresses" | Titre de l'écran |
| hint_street | "Voie" | Hint champ voie |
| hint_postal_code | "Code postal" | Hint champ code postal |
| hint_city | "Ville" | Hint champ ville |
| action_search | "Rechercher" | Texte du bouton |
| no_results | "Aucun résultat trouvé" | Message si aucun résultat |
| search_error | "Erreur lors de la recherche" | Message d'erreur |

---

## 7. Flux de données

### 7.1 Flux de recherche

```
[Utilisateur]
    ↓ Saisit critères + Clic bouton
[SearchActivity]
    ↓ Appel search()
[SearchViewModel]
    ↓ ExecutorService.execute()
[AddressRepository]
    ↓ searchAddresses()
[AddressDataSource]
    ↓ Requête SQL
[SQLite Database]
    ↓ Résultats
[AddressDataSource]
    ↓ List<Address>
[AddressRepository]
    ↓ List<Address>
[SearchViewModel]
    ↓ postValue() sur LiveData
[SearchActivity]
    ↓ Observe LiveData
[AddressAdapter]
    ↓ notifyDataSetChanged()
[RecyclerView]
    ↓ Affichage
[Utilisateur]
```

### 7.2 Flux d'initialisation de la base

```
[Application démarrée]
    ↓
[AddressDataSource.initDatabase()]
    ↓ Vérifie existence
[Base existe?]
    ↓ Non
[copyDatabaseFromAssets()]
    ↓ Copie depuis assets
[Format prêt]
    ↓
[Liste des formats disponibles]
```

---

## 8. Gestion des threads

### 8.1 Thread principal (UI Thread)
- Affichage de l'interface
- Observation des LiveData
- Mise à jour du RecyclerView
- Affichage des Toast et ProgressBar

### 8.2 Thread background (ExecutorService)
- Accès à la base SQLite
- Exécution des requêtes SQL
- Traitement des résultats

### 8.3 Communication inter-threads
- **LiveData.postValue()** : Mise à jour thread-safe depuis le background
- **LiveData.observe()** : Réception sur le thread principal

---

## 9. Performances et optimisations

### 9.1 Base de données
- **OPEN_READONLY** : Ouverture en lecture seule pour éviter les locks
- **WITHOUT ROWID** : Table optimisée pour l'espace et la vitesse
- **LIMIT 100** : Limitation des résultats pour éviter les surcharges
- **Index recommandés** : Sur nom_voie, code_postal, nom_commune

### 9.2 UI
- **ViewBinding** : Pas de findViewById(), moins d'erreurs
- **RecyclerView** : Réutilisation des vues pour performance
- **ExecutorService** : Recherches en background, UI fluide
- **LiveData** : Mises à jour automatiques et efficaces

### 9.3 Mémoire
- **Singleton Repository** : Une seule instance de la base
- **ExecutorService.shutdown()** : Libération des ressources dans onCleared()
- **Cursor.close()** : Fermeture systématique des curseurs

---

## 10. Gestion des erreurs

### 10.1 Erreurs de formats de données

#### SQLite
- **Fichier manquant** : Copie automatique depuis assets
- **Erreur de copie** : RuntimeException avec message explicite
- **Erreur de requête** : Capturée et postée via searchError LiveData
- **Base corrompue** : Message d'erreur et suggestion de réinstallation

#### Parquet
- **Fichier manquant** : Copie automatique depuis assets
- **Format invalide** : Capture ParquetException, message explicite
- **Erreur de lecture** : Tentative de récupération, sinon fallback vers autre format
- **Dépendances manquantes** : Vérification au démarrage

#### CSV/JSON
- **Parsing error** : Ligne ignorée ou message d'erreur selon gravité
- **Encodage invalide** : Tentative avec différents encodages (UTF-8, ISO-8859-1)
- **Fichier incomplet** : Avertissement mais traitement des données valides

### 10.2 Erreurs UI
- **Aucun résultat** : Toast "Aucun résultat trouvé"
- **Erreur de recherche** : Toast avec détails de l'erreur
- **Champs vides** : Recherche autorisée (tous critères optionnels)
- **Format non disponible** : Désactivation dans le spinner, message explicatif

### 10.3 Erreurs de benchmark
- **Échec sur un format** : Continue avec les autres formats
- **Timeout** : Limite de temps par recherche (configurable)
- **OutOfMemory** : Capture et rapport dans les métriques

---

## 11. Sécurité et bonnes pratiques

### 11.1 Sécurité

#### Protection contre les injections SQL
- **Requêtes paramétrées** : Utilisation systématique de placeholders `?` et arguments séparés
- **Aucune concaténation** : Les valeurs utilisateur ne sont jamais concaténées dans la requête SQL
- **SQLite binding** : Les arguments sont traités comme des données, jamais comme du code SQL
- **Exemple sécurisé** :
  ```java
  // ✅ Sécurisé - Requête paramétrée
  queryBuilder.append(" AND nom_voie LIKE ?");
  args.add("%" + street.trim() + "%");
  database.rawQuery(query, argsArray);
  ```

#### Autres aspects de sécurité
- **Lecture seule** : Base de données ouverte en mode `OPEN_READONLY` - pas de modification possible
- **Validation des entrées** : Trim() appliqué sur toutes les entrées utilisateur
- **Limitation des résultats** : LIMIT 100 pour éviter les attaques par surcharge
- **Context.getApplicationContext()** : Évite les fuites mémoire

### 11.2 Bonnes pratiques
- **Immutabilité** : Address utilise des champs final
- **Thread safety** : Double-checked locking pour le Singleton
- **Lifecycle awareness** : ViewModel survit aux rotations
- **Clean Architecture** : Séparation claire des couches

---

## 12. Tests

### 12.1 Tests unitaires (JUnit)
- **Localisation** : `app/src/test/java/`
- **Framework** : JUnit 4.13.2
- **Cibles** :
  - Repository : Changement de format, recherche
  - ViewModel : Gestion des benchmarks, changement de format
  - Address model : Validation des données
  - BenchmarkResult : Calculs et comparaisons

### 12.2 Tests instrumentés (Android)
- **Localisation** : `app/src/androidTest/java/`
- **Framework** : AndroidX Test + Espresso
- **Cibles** :
  - UI : Sélection de format, affichage des résultats
  - Formats de données : Lecture SQLite, Parquet, CSV, JSON
  - Intégration : Recherche end-to-end sur chaque format
  - Performance : Validation des métriques

### 12.3 Tests de performance
- **Benchmarks automatisés** : Suite de requêtes prédéfinies
- **Régression** : Comparaison avec résultats précédents
- **Profiling** : Utilisation de Android Profiler pour validation
- **Validation** : Cohérence des résultats entre formats

---

## 13. Configuration requise

### 13.1 Environnement de développement
- **Android Studio** : Arctic Fox ou plus récent recommandé
- **JDK** : 11 ou supérieur
- **Android SDK** : API Level 21 minimum, 35 recommandé
- **Gradle** : 8.x (via wrapper)

### 13.2 Appareils cibles
- **Android minimum** : 5.0 Lollipop (API 21)
- **Android cible** : 15 (API 35)
- **Architectures** : ARM, ARM64, x86, x86_64
- **Espace requis** : Dépend de la taille de bano_no_joins_wo_rowid.db

---

## 14. Points d'amélioration potentiels

### 14.1 Fonctionnalités de benchmark
- ✨ Export des résultats de benchmark (CSV, JSON)
- ✨ Graphiques de comparaison interactifs
- ✨ Historique des benchmarks avec tendances
- ✨ Benchmarks automatiques au démarrage
- ✨ Configuration des scénarios de test
- ✨ Warmup configurable
- ✨ Statistiques avancées (percentiles, écart-type)

### 14.2 Nouveaux formats
- 📦 Protocol Buffers
- 📦 FlatBuffers
- 📦 Avro
- 📦 ORC (Optimized Row Columnar)
- 📦 MessagePack
- 📦 BSON

### 14.3 Technique
- 🔧 Migration vers Kotlin
- 🔧 Utilisation de Room au lieu de SQLite natif
- 🔧 Injection de dépendances (Hilt/Dagger)
- 🔧 Coroutines au lieu d'ExecutorService
- 🔧 Pagination des résultats
- 🔧 FTS (Full-Text Search) pour SQLite
- 🔧 Optimisations Parquet (predicate pushdown)
- 🔧 Tests unitaires et UI plus complets
- 🔧 Profiling automatique avec Macrobenchmark

### 14.4 UX
- 🎨 Material Design 3
- 🎨 Mode sombre
- 🎨 Animations de transition
- 🎨 Graphiques de performance en temps réel
- 🎨 Comparaison visuelle côte à côte
- 🎨 Accessibilité améliorée
- 🎨 Partage des résultats

---

## 15. Annexes

### 15.1 Commandes Gradle utiles

```bash
# Build debug APK
./gradlew assembleDebug

# Run unit tests
./gradlew test

# Run instrumented tests
./gradlew connectedAndroidTest

# Clean project
./gradlew clean

# Generate lint report
./gradlew lint
```

### 15.2 Structure des fichiers générés

```
app/build/
├── generated/              # Code généré (ViewBinding, etc.)
├── intermediates/          # Fichiers intermédiaires de build
└── outputs/
    └── apk/
        └── debug/          # APK debug signé
```

### 15.3 Manifest permissions
**Aucune permission requise** - L'application fonctionne entièrement offline avec une base locale.

---

## 16. Historique et contexte

### 16.1 Type de projet
**Spike / Proof of Concept** - Projet expérimental pour comparer les performances de différents formats de stockage de données (SQLite, Parquet, CSV, JSON, etc.) dans le contexte de la base BANO.

### 16.2 Localisation dans le repository
`AFC_APPLICATIONS_ANDROID/trunk/Common/Spikes/BANO/parser/python_parser/DemoParser`

### 16.3 Motivation
Déterminer le format de stockage optimal pour les données BANO sur Android en termes de :
- Vitesse de recherche
- Utilisation mémoire
- Taille de stockage
- Complexité d'implémentation

### 16.4 Nom du package historique
Le package `com.sneaxiii.banoparser` suggère que le projet a été initialement créé à partir d'un template "Login Activity" d'Android Studio, puis adapté pour les besoins du benchmark BANO.

---

## 17. Conclusion

Cette application constitue un outil de benchmark complet pour évaluer les performances des formats de stockage de données sur Android :

### 17.1 Forces du projet
- **Architecture MVVM claire** : Séparation des responsabilités et maintenabilité
- **Strategy Pattern** : Abstraction permettant d'ajouter facilement de nouveaux formats
- **Mesures précises** : Métriques détaillées pour comparaison objective
- **Reproductibilité** : Tests identiques sur tous les formats
- **Gestion asynchrone** : UI fluide pendant les benchmarks

### 17.2 Formats implémentés
- ✅ **SQLite** : Base de données relationnelle avec indexation
- 🚧 **Parquet** : Format columnar avec compression efficace

### 17.3 Résultats attendus
Le benchmark permettra de répondre aux questions :
- Quel format offre les meilleures performances de recherche ?
- Quel est le compromis taille/vitesse optimal ?
- Quelle complexité d'implémentation pour chaque format ?
- Quelle utilisation mémoire en production ?

### 17.4 Impact
Les résultats guideront le choix du format de stockage pour la version production de l'application BANO, avec un impact direct sur :
- L'expérience utilisateur (temps de réponse)
- La consommation de ressources (batterie, mémoire)
- La taille de l'application (APK size)

---

**Date de génération des spécifications** : 12 janvier 2026
**Version de l'application** : 1.0
**Statut** : Proof of Concept / Spike - Focus sur benchmark de performances

