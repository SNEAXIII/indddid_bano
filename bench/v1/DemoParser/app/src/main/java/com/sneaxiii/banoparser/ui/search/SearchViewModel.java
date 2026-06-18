package com.sneaxiii.banoparser.ui.search;

import androidx.lifecycle.LiveData;
import androidx.lifecycle.MutableLiveData;
import androidx.lifecycle.ViewModel;

import com.sneaxiii.banoparser.data.AddressRepository;
import com.sneaxiii.banoparser.domain.model.Address;

import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * ViewModel pour la recherche d'adresses.
 * Gère l'état du formulaire et les résultats de recherche.
 */
public class SearchViewModel extends ViewModel {

    private final MutableLiveData<List<Address>> searchResults = new MutableLiveData<>();
    private final MutableLiveData<String> searchError = new MutableLiveData<>();
    private final AddressRepository addressRepository;
    private final ExecutorService executorService;

    public SearchViewModel(AddressRepository addressRepository) {
        this.addressRepository = addressRepository;
        this.executorService = Executors.newSingleThreadExecutor();
    }

    public LiveData<List<Address>> getSearchResults() {
        return searchResults;
    }

    public LiveData<String> getSearchError() {
        return searchError;
    }

    /**
     * Lance une recherche d'adresses avec les critères fournis.
     * La recherche est exécutée en background.
     *
     * @param street     Nom de la voie (peut être vide)
     * @param postalCode Code postal (peut être vide)
     * @param city       Nom de la ville (peut être vide)
     */
    public void search(String street, String postalCode, String city) {
        executorService.execute(() -> {
            try {
                List<Address> results = addressRepository.searchAddresses(street, postalCode, city);
                searchResults.postValue(results);
            } catch (Exception e) {
                searchError.postValue(e.getMessage());
            }
        });
    }

    @Override
    protected void onCleared() {
        super.onCleared();
        executorService.shutdown();
    }
}

