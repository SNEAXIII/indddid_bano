package com.example.bano;

import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;

import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;

import java.util.ArrayList;
import java.util.List;

/** Adapter RecyclerView : affiche voie + "cp ville" par résultat. */
public class ResultAdapter extends RecyclerView.Adapter<ResultAdapter.VH> {

    private final List<Result> items = new ArrayList<>();

    public void submit(List<Result> results) {
        items.clear();
        items.addAll(results);
        notifyDataSetChanged();
    }

    @NonNull
    @Override
    public VH onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        View v = LayoutInflater.from(parent.getContext())
                .inflate(R.layout.item_result, parent, false);
        return new VH(v);
    }

    @Override
    public void onBindViewHolder(@NonNull VH holder, int position) {
        Result r = items.get(position);
        holder.voie.setText(r.voie());
        holder.cpVille.setText(r.cp() + "  " + r.ville());
        holder.score.setText(String.format(java.util.Locale.US, "%.3f", r.score()));
    }

    @Override
    public int getItemCount() {
        return items.size();
    }

    static class VH extends RecyclerView.ViewHolder {
        final TextView voie;
        final TextView cpVille;
        final TextView score;

        VH(@NonNull View itemView) {
            super(itemView);
            voie = itemView.findViewById(R.id.voie);
            cpVille = itemView.findViewById(R.id.cpVille);
            score = itemView.findViewById(R.id.score);
        }
    }
}
