package com.elber.jojoquest;

import android.content.Context;
import android.content.SharedPreferences;

import java.util.ArrayList;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * Dex do jogo: catalogo de entradas + carteira de moedas, tudo persistido.
 *
 * <p>Guarda o progresso do jogador (moedas, total acumulado, entradas
 * descobertas e itens comprados) em SharedPreferences, de forma que o estado
 * sobrevive a fechar e reabrir o app.
 */
public class Dex {

    private static final String PREFS = "jojoquest_dex";
    private static final String K_COINS = "coins";
    private static final String K_TOTAL = "coins_total";
    private static final String K_SPENT = "coins_spent";
    private static final String K_FOUND = "found_";
    private static final String K_OWNED = "owned_";
    private static final String K_PICKED = "picked_";

    /** Uma entrada do catalogo. */
    public static class Entry {
        public final String id;
        public final String name;
        public final String description;
        /** Custo em moedas; 0 = nao comprável (so descoberta). */
        public final int price;

        Entry(String id, String name, String description, int price) {
            this.id = id;
            this.name = name;
            this.description = description;
            this.price = price;
        }
    }

    /** Resultado de uma tentativa de compra. */
    public enum Purchase { OK, ALREADY_OWNED, NOT_ENOUGH_COINS, UNKNOWN_ENTRY }

    /** Observador de mudancas na carteira (para HUD / efeitos). */
    public interface Listener {
        void onCoinsChanged(int coins, int delta);
    }

    private final SharedPreferences prefs;
    private final Map<String, Entry> catalog = new LinkedHashMap<>();
    private final List<Listener> listeners = new ArrayList<>();

    private int coins;
    private int totalEarned;
    private int totalSpent;

    public Dex(Context ctx) {
        prefs = ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
        coins = prefs.getInt(K_COINS, 0);
        totalEarned = prefs.getInt(K_TOTAL, 0);
        totalSpent = prefs.getInt(K_SPENT, 0);
        buildCatalog();
    }

    private void buildCatalog() {
        add("jotaro", "Jotaro", "O herói. Delinquente de coração mole.", 0);
        add("coin", "Moeda de Ouro", "Brilha e gira. Vale 1 na carteira.", 0);
        add("village", "A Vila", "Cinco casas, um lago e muito caminho.", 0);
        add("lake", "O Lago", "Água fria demais para nadar.", 0);
        add("boots", "Botas Velozes", "Deixa o Jotaro 40% mais rápido.", 25);
        add("lamp", "Lanterna", "Ilumina os cantos escuros do mapa.", 40);
        add("charm", "Amuleto Dourado", "Moedas valem o dobro.", 80);
        add("hat", "Boné Extra", "Puramente estético. Vale cada moeda.", 120);
    }

    private void add(String id, String name, String desc, int price) {
        catalog.put(id, new Entry(id, name, desc, price));
    }

    // ------------------------------------------------------------- carteira

    public int coins() { return coins; }

    public int totalEarned() { return totalEarned; }

    public int totalSpent() { return totalSpent; }

    /** Credita moedas na carteira. Aplica o bônus do amuleto, se comprado. */
    public void addCoins(int amount) {
        if (amount <= 0) return;
        if (isOwned("charm")) amount *= 2;
        coins += amount;
        totalEarned += amount;
        prefs.edit().putInt(K_COINS, coins).putInt(K_TOTAL, totalEarned).apply();
        notifyCoins(amount);
    }

    /** Debita moedas se houver saldo. @return true se conseguiu gastar. */
    public boolean spendCoins(int amount) {
        if (amount <= 0 || coins < amount) return false;
        coins -= amount;
        totalSpent += amount;
        prefs.edit().putInt(K_COINS, coins).putInt(K_SPENT, totalSpent).apply();
        notifyCoins(-amount);
        return true;
    }

    public boolean canAfford(int amount) { return coins >= amount; }

    // ------------------------------------------------------------- catalogo

    public List<Entry> entries() {
        return Collections.unmodifiableList(new ArrayList<>(catalog.values()));
    }

    public Entry entry(String id) { return catalog.get(id); }

    /** Marca uma entrada como descoberta. @return true se foi a primeira vez. */
    public boolean discover(String id) {
        if (!catalog.containsKey(id) || isFound(id)) return false;
        prefs.edit().putBoolean(K_FOUND + id, true).apply();
        return true;
    }

    public boolean isFound(String id) { return prefs.getBoolean(K_FOUND + id, false); }

    public boolean isOwned(String id) { return prefs.getBoolean(K_OWNED + id, false); }

    /** Tenta comprar uma entrada do catálogo com as moedas da carteira. */
    public Purchase buy(String id) {
        Entry e = catalog.get(id);
        if (e == null || e.price <= 0) return Purchase.UNKNOWN_ENTRY;
        if (isOwned(id)) return Purchase.ALREADY_OWNED;
        if (!spendCoins(e.price)) return Purchase.NOT_ENOUGH_COINS;
        prefs.edit().putBoolean(K_OWNED + id, true).apply();
        discover(id);
        return Purchase.OK;
    }

    public int foundCount() {
        int n = 0;
        for (String id : catalog.keySet()) if (isFound(id)) n++;
        return n;
    }

    public int totalCount() { return catalog.size(); }

    // ------------------------------------- moedas coletadas no mapa (por id)

    /** Marca uma moeda do mapa como já pega, para não reaparecer. */
    public void markPicked(int coinId) {
        prefs.edit().putBoolean(K_PICKED + coinId, true).apply();
    }

    public boolean isPicked(int coinId) {
        return prefs.getBoolean(K_PICKED + coinId, false);
    }

    /** Devolve todas as moedas ao mapa (usado no "Novo Jogo"). */
    public void resetPickups() {
        SharedPreferences.Editor ed = prefs.edit();
        for (String k : prefs.getAll().keySet()) {
            if (k.startsWith(K_PICKED)) ed.remove(k);
        }
        ed.apply();
    }

    /** Zera todo o progresso. */
    public void resetAll() {
        prefs.edit().clear().apply();
        coins = 0;
        totalEarned = 0;
        totalSpent = 0;
        notifyCoins(0);
    }

    // ------------------------------------------------------------ listeners

    public void addListener(Listener l) {
        if (l != null && !listeners.contains(l)) listeners.add(l);
    }

    public void removeListener(Listener l) { listeners.remove(l); }

    private void notifyCoins(int delta) {
        for (int i = listeners.size() - 1; i >= 0; i--) {
            listeners.get(i).onCoinsChanged(coins, delta);
        }
    }
}
