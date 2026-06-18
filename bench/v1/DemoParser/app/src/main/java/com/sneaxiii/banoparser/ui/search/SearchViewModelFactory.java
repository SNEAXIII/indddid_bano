package com.sneaxiii.banoparser.ui.search;

import android.content.Context;

import androidx.annotation.NonNull;
import androidx.lifecycle.ViewModel;
import androidx.lifecycle.ViewModelProvider;

import com.sneaxiii.banoparser.data.AddressRepository;

/**
 * Factory pour créer le SearchViewModel avec ses dépendances.
 */
public class SearchViewModelFactory implements ViewModelProvider.Factory {

    private final Context context;

    public SearchViewModelFactory(Context context) {
        this.context = context.getApplicationContext();
    }

    @NonNull
    @Override
    @SuppressWarnings("unchecked")
    public <T extends ViewModel> T create(@NonNull Class<T> modelClass) {
        if (modelClass.isAssignableFrom(SearchViewModel.class)) {
            return (T) new SearchViewModel(
                    AddressRepository.getInstance(context)
            );
        }
        throw new IllegalArgumentException("Unknown ViewModel class");
    }
}

