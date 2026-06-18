//! Bibliothèque `bano_fst` : logique partagée entre le binaire CLI et la
//! bibliothèque native (JNI) embarquée dans l'app Android.
//!
//! - `normalize` : normalisation accents/casse (identique build & search).
//! - `build`     : construction de l'artefact binaire (3 fichiers).
//! - `index`     : ouverture mmap + recherche floue -> liste de `Hit`.
//! - `jni_bridge`: pont JNI (compilé seulement avec la feature `jni`).

pub mod build;
pub mod index;
pub mod normalize;

#[cfg(feature = "jni")]
pub mod jni_bridge;
