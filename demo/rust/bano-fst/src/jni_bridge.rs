//! Pont JNI : expose `Index` à Java pour l'app Android.
//!
//! Compilé UNIQUEMENT avec la feature `jni` (voir Cargo.toml) afin de ne pas
//! alourdir le binaire CLI desktop. Côté Java, la classe
//! `com.example.bano.BanoFst` déclare 3 méthodes `native` dont les noms se
//! mappent EXACTEMENT sur les fonctions ci-dessous (convention JNI :
//! `Java_<package_avec_underscores>_<Classe>_<methode>`).
//!
//! Le `handle` (jlong) renvoyé par `nativeOpen` est un pointeur brut vers un
//! `Box<Index>` ; Java le garde et le repasse à `nativeSearch`/`nativeClose`.

use jni::objects::{JClass, JString};
use jni::sys::{jint, jlong, jstring};
use jni::JNIEnv;

use crate::index::{hits_to_json, Index};

/// Ouvre l'index (dossier passé en String). Renvoie un handle (>0) ou 0 si échec.
#[no_mangle]
pub extern "system" fn Java_com_example_bano_BanoFst_nativeOpen(
    mut env: JNIEnv,
    _class: JClass,
    dir: JString,
) -> jlong {
    let dir: String = match env.get_string(&dir) {
        Ok(s) => s.into(),
        Err(_) => return 0,
    };
    match Index::open(&dir) {
        Ok(index) => Box::into_raw(Box::new(index)) as jlong,
        Err(_) => 0,
    }
}

/// Recherche. Renvoie une chaîne JSON `[{score,voie,cp,ville}, ...]`.
#[no_mangle]
pub extern "system" fn Java_com_example_bano_BanoFst_nativeSearch(
    mut env: JNIEnv,
    _class: JClass,
    handle: jlong,
    query: JString,
    limit: jint,
) -> jstring {
    if handle == 0 {
        return std::ptr::null_mut();
    }
    // SECURITE : handle provient de nativeOpen ; l'Index reste vivant tant que
    // Java n'a pas appelé nativeClose. On emprunte sans reprendre la propriété.
    let index = unsafe { &*(handle as *const Index) };

    let query: String = match env.get_string(&query) {
        Ok(s) => s.into(),
        Err(_) => String::new(),
    };

    let hits = index.search(&query, limit.max(0) as usize).unwrap_or_default();
    let json = hits_to_json(&hits);

    match env.new_string(json) {
        Ok(s) => s.into_raw(),
        Err(_) => std::ptr::null_mut(),
    }
}

/// Libère l'index (reprend la propriété du Box et le drop).
#[no_mangle]
pub extern "system" fn Java_com_example_bano_BanoFst_nativeClose(
    _env: JNIEnv,
    _class: JClass,
    handle: jlong,
) {
    if handle != 0 {
        unsafe {
            drop(Box::from_raw(handle as *mut Index));
        }
    }
}
