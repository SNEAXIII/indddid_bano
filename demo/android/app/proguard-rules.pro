# Règles ProGuard/R8 (actives seulement si minifyEnabled true).
#
# Conserver les méthodes natives JNI et la classe qui les déclare : leurs noms
# doivent rester intacts pour correspondre aux symboles de libbano_fst.so.
-keepclasseswithmembernames,includedescriptorclasses class * {
    native <methods>;
}
-keep class com.example.bano.BanoFst { *; }
