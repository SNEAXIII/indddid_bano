package com.sneaxiii.banoparser.ui.search;

import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;

import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;

import com.sneaxiii.banoparser.domain.model.Address;

import java.util.ArrayList;
import java.util.List;

/**
 * Adapter pour afficher la liste des adresses dans un RecyclerView.
 */
public class AddressAdapter extends RecyclerView.Adapter<AddressAdapter.AddressViewHolder> {

    private List<Address> addresses = new ArrayList<>();

    public void setAddresses(List<Address> addresses) {
        this.addresses = addresses != null ? addresses : new ArrayList<>();
        notifyDataSetChanged();
    }

    public void clearAddresses() {
        this.addresses.clear();
        notifyDataSetChanged();
    }

    @NonNull
    @Override
    public AddressViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        View view = LayoutInflater.from(parent.getContext())
                .inflate(android.R.layout.simple_list_item_2, parent, false);
        return new AddressViewHolder(view);
    }

    @Override
    public void onBindViewHolder(@NonNull AddressViewHolder holder, int position) {
        Address address = addresses.get(position);
        holder.bind(address);
    }

    @Override
    public int getItemCount() {
        return addresses.size();
    }

    static class AddressViewHolder extends RecyclerView.ViewHolder {
        private final TextView text1;
        private final TextView text2;

        public AddressViewHolder(@NonNull View itemView) {
            super(itemView);
            text1 = itemView.findViewById(android.R.id.text1);
            text2 = itemView.findViewById(android.R.id.text2);
        }

        public void bind(Address address) {
            text1.setText(address.getStreet());
            text2.setText(address.getPostalCode() + " " + address.getCity());
        }
    }
}
