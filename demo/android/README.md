# 📱 bano-android — recherche d'adresses BANO, lib Rust embarquée (JNI)

POC dans l'esprit de la brique `bano-fst`, mais sous forme d'**application
Android native (Java 17, minSdk 30 / Android 11)** avec un **champ de
recherche**. À chaque frappe, l'app interroge **en direct** la brique Rust
`bano-fst` (recherche floue FST + automate de Levenshtein) **embarquée dans
l'APK** via **JNI**. 100 % offline : aucun réseau, aucun SQLite.

> Pourquoi JNI et pas Panama/FFM : l'API `java.lang.foreign` n'est pas
> disponible sur le runtime Android (ART). JNI est le seul pont Rust↔Java sur
> Android.

## 🧱 Comment ça marche

```
EditText (champ)  ──frappe (debounce 80 ms)──►  BanoFst.search(q, 10)        [Java]
                                                       │ JNI downcall
                                                       ▼
                              libbano_fst.so  ──►  Index::search() (mmap FST)  [Rust]
                                                       │
RecyclerView  ◄── List<Result> (record) ◄── JSON ──────┘
```

- **Rust** (`../rust/bano-fst`) : `Index::open` mmap les 3 fichiers de l'index,
  `Index::search` renvoie des `Hit`. Le module `jni_bridge.rs` (feature `jni`)
  expose `nativeOpen` / `nativeSearch` (JSON) / `nativeClose`.
- **Java** : `BanoFst.java` charge `libbano_fst.so` et parse le JSON en
  `record Result(...)`. `MainActivity.java` gère le champ, le debounce et
  l'exécution **hors UI thread** (`ExecutorService`). Au 1er lancement, l'index
  est copié de `assets/index/` vers `filesDir/index/`, puis ouvert.

## ✅ Pré-requis

| Outil | Pourquoi | Installé ici ? |
|---|---|---|
| `cargo` (rustup) | compiler la brique Rust | ✅ `~/.cargo/bin` |
| `cargo-ndk` | cross-compiler en `.so` Android | `cargo install cargo-ndk` |
| targets Rust Android | `aarch64`/`x86_64-linux-android` | `rustup target add …` |
| Android NDK | toolchain native | ✅ `~/android_sdk/ndk/` |
| **JDK 17** | requis par AGP/Gradle | ⚠️ le `java` système est en 8 |
| Gradle 8.7+ ou Android Studio | builder l'APK | à fournir |

## 🚀 Build

### 1. Compiler la lib Rust pour Android (`.so`)

Depuis `new/` :

```bash
make android-lib
# -> android/app/src/main/jniLibs/{arm64-v8a,x86_64}/libbano_fst.so
```

### 2. Construire l'index dans les assets (OBLIGATOIRE avant le build APK)

L'index FST n'est **pas** versionné (volumineux + régénérable, cf. `.gitignore`).
Il faut le construire une fois dans `app/src/main/assets/index/` :

```bash
# depuis new/ — index France entière (par défaut STREETS=rust/bano-fst/streets.csv)
make android-index
# ou depuis un autre CSV :
make android-index STREETS=/chemin/vers/streets.csv
```

> ⚠️ **Taille** : la France entière (~2,2 M adresses) pèse **~142 Mo**
> (index.fst 4 Mo + postings 51 Mo + records 86 Mo). L'APK sera d'autant plus
> lourd, et l'index est recopié dans `filesDir` au 1er lancement (≈ ×2 en
> stockage). Pour un APK léger, construire depuis un échantillon :
> `head -n 200001 rust/bano-fst/streets.csv > /tmp/s.csv && make android-index STREETS=/tmp/s.csv`.

### 3. Builder l'APK (nécessite JDK 17 + Gradle)

```bash
cd android
# Le wrapper est versionné et épinglé (Gradle 8.9). Il faut juste un JDK 17 :
JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64 ANDROID_HOME=$HOME/android_sdk \
  ./gradlew assembleDebug
# -> app/build/outputs/apk/debug/app-debug.apk  (~55 Mo avec l'index France entière)
```

> ✅ Build vérifié de bout en bout (Gradle 8.9 + JDK 17) : APK ~55 Mo, embarquant
> `lib/{arm64-v8a,x86_64}/libbano_fst.so` + `assets/index/`.

Le plus simple : ouvrir le dossier `android/` dans **Android Studio** (qui
embarque JDK 17 + Gradle) et cliquer **Run**.

Config Gradle : **version catalog** (`gradle/libs.versions.toml`), wrapper
épinglé, `.gitignore` par module, DSL Groovy (aucun code Kotlin).

### 4. Installer sur l'émulateur (x86_64) ou un appareil

```bash
~/android_sdk/platform-tools/adb install -r app/build/outputs/apk/debug/app-debug.apk
```

## 🔎 Utilisation

Ouvrir l'app → attendre « Prêt. Tapez une adresse. » → taper par exemple
`bourg en bress` (faute volontaire). La liste affiche les adresses
correspondantes et la barre de statut indique le **nombre de résultats** et la
**latence** (quelques millisecondes, recherche in-process).

## 🗂️ Structure

```
android/
├── settings.gradle / build.gradle / gradle.properties
└── app/
    ├── build.gradle                  (minSdk 30, Java 17, abiFilters)
    └── src/main/
        ├── AndroidManifest.xml
        ├── java/com/example/bano/
        │   ├── BanoFst.java          (loadLibrary + natives + parse JSON)
        │   ├── Result.java           (record)
        │   ├── ResultAdapter.java
        │   └── MainActivity.java     (champ + debounce + executor + copie assets)
        ├── jniLibs/<abi>/libbano_fst.so   (produit par `make android-lib`, gitignored)
        ├── assets/index/{index.fst,postings.bin,records.bin}
        └── res/layout/{activity_main,item_result}.xml
```
