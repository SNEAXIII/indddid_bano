package com.sneaxiii.banoparser;

import android.os.Bundle;

import androidx.appcompat.app.AppCompatActivity;
import androidx.fragment.app.Fragment;
import androidx.fragment.app.FragmentManager;
import androidx.fragment.app.FragmentTransaction;

import com.google.android.material.bottomnavigation.BottomNavigationView;
import com.sneaxiii.banoparser.ui.benchmark.BenchmarkFragment;
import com.sneaxiii.banoparser.ui.search.SearchFragment;
import com.sneaxiii.banoparser.ui.suggestions.SuggestionsFragment;

import java.util.HashMap;
import java.util.Map;

/**
 * Activity principale avec Bottom Navigation Bar.
 * Optimisée pour éviter les créations/destructions répétées de fragments.
 */
public class MainActivity extends AppCompatActivity {

    private final Map<Integer, Fragment> fragmentMap = new HashMap<>();
    private FragmentManager fragmentManager;
    private Fragment currentFragment;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        BottomNavigationView bottomNavigationView = findViewById(R.id.bottom_navigation);

        // Récupérer le FragmentManager une seule fois
        fragmentManager = getSupportFragmentManager();

        // Créer les fragments une seule fois
        fragmentMap.put(R.id.navigation_search, new SearchFragment());
        fragmentMap.put(R.id.navigation_suggestions, new SuggestionsFragment());
        fragmentMap.put(R.id.navigation_benchmark, new BenchmarkFragment());

        // Ajouter tous les fragments cachés lors de l'initialisation
        // Cela évite de les recréer à chaque changement d'onglet
        if (savedInstanceState == null) {
            for (Fragment fragment : fragmentMap.values()) {
                fragmentManager.beginTransaction()
                        .add(R.id.fragment_container, fragment)
                        .hide(fragment)
                        .commit();
            }
        }

        // Afficher le fragment par défaut (Recherche)
        Fragment defaultFragment = fragmentMap.get(R.id.navigation_search);
        showFragment(defaultFragment);

        // Gérer les clics sur la navigation bar
        bottomNavigationView.setOnItemSelectedListener(item -> {
            Fragment fragment = fragmentMap.get(item.getItemId());
            if (fragment != null) {
                showFragment(fragment);
                return true;
            }
            return false;
        });
    }

    /**
     * Affiche un fragment et cache le fragment actuel.
     * Utilise show/hide au lieu de replace pour éviter la destruction/recréation.
     *
     * Avantages :
     * - Pas de Garbage Collection excessive
     * - Conservation de l'état des fragments (scroll position, données, etc.)
     * - Performance optimale lors de changements rapides d'onglets
     *
     * @param fragment Le fragment à afficher
     */
    private void showFragment(Fragment fragment) {
        // Si c'est déjà le fragment affiché, ne rien faire
        if (fragment == currentFragment) {
            return;
        }

        // Créer une transaction
        FragmentTransaction transaction = fragmentManager.beginTransaction();

        // Cacher le fragment actuel s'il existe
        if (currentFragment != null) {
            transaction.hide(currentFragment);
        }

        // Afficher le nouveau fragment
        transaction.show(fragment);

        // Optimisation : setReorderingAllowed permet d'optimiser les transactions
        transaction.setReorderingAllowed(true);

        // Appliquer les changements
        transaction.commit();

        // Mettre à jour le fragment actuel
        currentFragment = fragment;
    }
}

