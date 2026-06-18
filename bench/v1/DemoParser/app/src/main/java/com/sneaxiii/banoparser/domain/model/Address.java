package com.sneaxiii.banoparser.domain.model;

import androidx.annotation.NonNull;

/**
 * Modèle représentant une adresse BANO.
 */
public class Address {
    private final String street;
    private final String postalCode;
    private final String city;

    public Address(String street, String postalCode, String city) {
        this.street = street;
        this.postalCode = postalCode;
        this.city = city;
    }

    public String getStreet() {
        return street;
    }

    public String getPostalCode() {
        return postalCode;
    }

    public String getCity() {
        return city;
    }


    /**
     * Retourne l'adresse formatée complète.
     */
    public String getFullAddress() {
        return street + ", " + postalCode + " " + city;
    }

    @NonNull
    @Override
    public String toString() {
        return getFullAddress();
    }
}

