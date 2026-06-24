package com.example.bano;

/** Un résultat de recherche : score + triplet d'adresse. */
public record Result(double score, String voie, String cp, String ville) {
}
