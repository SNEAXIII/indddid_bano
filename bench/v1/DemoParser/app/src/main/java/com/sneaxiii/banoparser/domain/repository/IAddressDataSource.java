package com.sneaxiii.banoparser.domain.repository;

import com.sneaxiii.banoparser.domain.model.Address;

import java.util.List;

/**
 * Interface pour les sources de données d'adresses.
 * Permet d'implémenter différentes sources : SQLite, CSV, Parquet, API, etc.
 */
public interface IAddressDataSource {

    /**
     * Recherche des adresses correspondant aux critères.
     *
     * @param street     Nom de la voie (peut être null ou vide)
     * @param postalCode Code postal (peut être null ou vide)
     * @param city       Nom de la ville (peut être null ou vide)
     * @return Liste des adresses correspondantes
     */
    List<Address> search(String street, String postalCode, String city);

    /**
     * Ferme la connexion à la source de données.
     */
    void close();
}

