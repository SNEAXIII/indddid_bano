package com.sneaxiii.banoparser.ui.search;

import android.os.Bundle;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.view.inputmethod.EditorInfo;
import android.widget.Button;
import android.widget.EditText;
import android.widget.ProgressBar;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.fragment.app.Fragment;
import androidx.lifecycle.ViewModelProvider;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;

import com.sneaxiii.banoparser.R;

/**
 * Fragment permettant de rechercher des adresses BANO.
 * Formulaire avec 3 champs : voie, code postal, ville.
 */
public class SearchFragment extends Fragment {

    private SearchViewModel searchViewModel;
    private AddressAdapter addressAdapter;

    private EditText streetInput;
    private EditText postalCodeInput;
    private EditText cityInput;
    private Button searchButton;
    private Button exportCsvButton;
    private ProgressBar loadingProgressBar;
    private RecyclerView resultsRecyclerView;

    @Nullable
    @Override
    public View onCreateView(@NonNull LayoutInflater inflater, @Nullable ViewGroup container, @Nullable Bundle savedInstanceState) {
        return inflater.inflate(R.layout.fragment_search, container, false);
    }

    @Override
    public void onViewCreated(@NonNull View view, @Nullable Bundle savedInstanceState) {
        super.onViewCreated(view, savedInstanceState);

        searchViewModel = new ViewModelProvider(this, new SearchViewModelFactory(requireContext()))
                .get(SearchViewModel.class);

        streetInput = view.findViewById(R.id.streetInput);
        postalCodeInput = view.findViewById(R.id.postalCodeInput);
        cityInput = view.findViewById(R.id.cityInput);
        searchButton = view.findViewById(R.id.searchButton);
        exportCsvButton = view.findViewById(R.id.exportCsvButton);
        loadingProgressBar = view.findViewById(R.id.loading);
        resultsRecyclerView = view.findViewById(R.id.resultsRecyclerView);

        // Configuration du RecyclerView
        addressAdapter = new AddressAdapter();
        resultsRecyclerView.setLayoutManager(new LinearLayoutManager(requireContext()));
        resultsRecyclerView.setAdapter(addressAdapter);

        // Observer les résultats de recherche
        searchViewModel.getSearchResults().observe(getViewLifecycleOwner(), results -> {
            loadingProgressBar.setVisibility(View.GONE);
            if (results != null && !results.isEmpty()) {
                addressAdapter.setAddresses(results);
            } else {
                addressAdapter.clearAddresses();
                Toast.makeText(requireContext(), R.string.no_results, Toast.LENGTH_SHORT).show();
            }
        });

        // Observer les erreurs
        searchViewModel.getSearchError().observe(getViewLifecycleOwner(), error -> {
            loadingProgressBar.setVisibility(View.GONE);
            if (error != null) {
                Toast.makeText(requireContext(), R.string.search_error, Toast.LENGTH_SHORT).show();
            }
        });

        // Lancer la recherche avec le bouton Enter sur le clavier
        cityInput.setOnEditorActionListener((v, actionId, event) -> {
            if (actionId == EditorInfo.IME_ACTION_SEARCH) {
                performSearch();
                return true;
            }
            return false;
        });

        // Lancer la recherche avec le bouton
        searchButton.setOnClickListener(v -> performSearch());

        // Placeholder pour l'export CSV
        exportCsvButton.setOnClickListener(v -> {
            // TODO: Implémenter l'export CSV
            Toast.makeText(requireContext(), "Export CSV - À implémenter", Toast.LENGTH_SHORT).show();
        });
    }

    private void performSearch() {
        String street = streetInput.getText().toString().trim();
        String postalCode = postalCodeInput.getText().toString().trim();
        String city = cityInput.getText().toString().trim();

        loadingProgressBar.setVisibility(View.VISIBLE);
        searchViewModel.search(street, postalCode, city);
    }
}

