package com.elber.jojoquest;

import java.util.ArrayList;
import java.util.List;
import java.util.Random;

/** Uma moeda colecionável posicionada no mapa. */
public class Coin {

    public static final int SIZE = 32;          // celula na coin.png
    private static final float PICK_RADIUS = 18f;

    public final int id;
    public final float x, y;                    // centro, em pixels do mundo
    public boolean collected = false;

    /** deslocamento inicial da animacao, para as moedas nao piscarem juntas */
    public final float phase;

    public Coin(int id, float x, float y, float phase) {
        this.id = id;
        this.x = x;
        this.y = y;
        this.phase = phase;
    }

    public boolean touches(float px, float py) {
        float dx = px - x;
        float dy = (py - 8f) - y;               // pes do jogador -> centro do corpo
        return dx * dx + dy * dy <= PICK_RADIUS * PICK_RADIUS;
    }

    /** Frame atual do giro (0..5). */
    public int frame(float time) {
        return ((int) ((time + phase) / 0.11f)) % 6;
    }

    /** Flutuacao vertical suave. */
    public float bob(float time) {
        return (float) Math.sin((time + phase) * 3.0) * 2.0f;
    }

    /**
     * Espalha moedas pelo mapa em tiles andáveis, longe das bordas.
     * A geracao usa semente fixa: o mesmo mapa gera sempre as mesmas moedas.
     */
    public static List<Coin> scatter(GameMap map, int count, Dex dex) {
        List<Coin> out = new ArrayList<>();
        Random rnd = new Random(20240923L);
        int id = 0;
        int guard = 0;
        while (out.size() < count && guard++ < count * 200) {
            int tx = 2 + rnd.nextInt(Math.max(1, map.cols - 4));
            int ty = 2 + rnd.nextInt(Math.max(1, map.rows - 4));
            if (map.isSolid(tx, ty)) continue;

            // evita moeda encostada numa parede (dificil de pegar)
            if (map.isSolid(tx - 1, ty) && map.isSolid(tx + 1, ty)) continue;

            float cx = tx * GameMap.TILE + GameMap.TILE / 2f;
            float cy = ty * GameMap.TILE + GameMap.TILE / 2f;

            boolean tooClose = false;
            for (Coin c : out) {
                float dx = c.x - cx, dy = c.y - cy;
                if (dx * dx + dy * dy < (GameMap.TILE * 3f) * (GameMap.TILE * 3f)) {
                    tooClose = true;
                    break;
                }
            }
            if (tooClose) continue;

            Coin c = new Coin(id, cx, cy, rnd.nextFloat() * 2f);
            if (dex != null && dex.isPicked(id)) c.collected = true;
            out.add(c);
            id++;
        }
        return out;
    }
}
