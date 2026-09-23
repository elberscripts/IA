package com.elber.jojoquest;

import android.content.res.AssetManager;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.util.ArrayList;
import java.util.List;

/** Grid de tiles carregado de assets/map.txt, com regras de colisao. */
public class GameMap {

    public static final int TILE = 32;

    // indices na tiles.png (mesma ordem de tools/make_tiles.py)
    private static final String LEGEND = ".,#~TORWSHLD";

    private final char[][] grid;
    public final int cols;
    public final int rows;

    public GameMap(AssetManager am, String path) throws Exception {
        List<String> lines = new ArrayList<>();
        try (BufferedReader r = new BufferedReader(new InputStreamReader(am.open(path)))) {
            String s;
            while ((s = r.readLine()) != null) {
                if (!s.isEmpty()) lines.add(s);
            }
        }
        rows = lines.size();
        cols = lines.get(0).length();
        grid = new char[rows][cols];
        for (int y = 0; y < rows; y++) {
            String line = lines.get(y);
            for (int x = 0; x < cols; x++) {
                grid[y][x] = x < line.length() ? line.charAt(x) : '.';
            }
        }
    }

    public char charAt(int tx, int ty) {
        if (tx < 0 || ty < 0 || tx >= cols || ty >= rows) return 'T';
        return grid[ty][tx];
    }

    /** Indice do tile no tileset horizontal. */
    public int tileIndex(int tx, int ty) {
        int i = LEGEND.indexOf(charAt(tx, ty));
        return i < 0 ? 0 : i;
    }

    /** Tiles que bloqueiam o movimento. */
    public boolean isSolid(int tx, int ty) {
        char c = charAt(tx, ty);
        return c == 'T' || c == 'O' || c == '~' || c == 'R' || c == 'W' || c == 'H';
    }

    public int pixelWidth() { return cols * TILE; }

    public int pixelHeight() { return rows * TILE; }
}
