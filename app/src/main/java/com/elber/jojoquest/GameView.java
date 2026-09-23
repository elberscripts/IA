package com.elber.jojoquest;

import android.annotation.SuppressLint;
import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.Rect;
import android.graphics.RectF;
import android.graphics.Typeface;
import android.view.MotionEvent;
import android.view.SurfaceHolder;
import android.view.SurfaceView;

import java.io.InputStream;

/** SurfaceView com game loop proprio: desenha mapa, heroi e HUD. */
public class GameView extends SurfaceView implements SurfaceHolder.Callback, Runnable {

    private static final int SPRITE = 64;      // celula na hero.png
    private static final int TILE = GameMap.TILE;

    private Thread thread;
    private volatile boolean running = false;

    private Bitmap tiles, hero, dpadBmp;
    private GameMap map;
    private Player player;
    private final Dpad dpad = new Dpad();

    private final Paint paint = new Paint();
    private final Paint hudPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint shadowPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Rect src = new Rect();
    private final RectF dst = new RectF();

    private float scale = 3f;                  // zoom do mundo (pixel perfect)
    private float camX = 0f, camY = 0f;
    private long lastNanos = 0L;
    private float fps = 0f;

    public GameView(Context ctx) {
        super(ctx);
        getHolder().addCallback(this);
        setFocusable(true);

        paint.setFilterBitmap(false);          // nearest neighbour = pixel art nitido
        paint.setAntiAlias(false);
        paint.setDither(false);

        hudPaint.setColor(Color.WHITE);
        hudPaint.setTypeface(Typeface.create(Typeface.MONOSPACE, Typeface.BOLD));

        shadowPaint.setColor(0x55000000);

        try {
            tiles = load("tiles.png");
            hero = load("hero.png");
            dpadBmp = load("dpad.png");
            map = new GameMap(ctx.getAssets(), "map.txt");
        } catch (Exception e) {
            throw new RuntimeException("Falha ao carregar assets do jogo", e);
        }

        // spawn no cruzamento de caminhos perto do canto superior esquerdo
        player = new Player(15 * TILE + TILE / 2f, 24 * TILE + TILE);
    }

    private Bitmap load(String name) throws Exception {
        BitmapFactory.Options o = new BitmapFactory.Options();
        o.inScaled = false;
        o.inPreferredConfig = Bitmap.Config.ARGB_8888;
        try (InputStream is = getContext().getAssets().open(name)) {
            return BitmapFactory.decodeStream(is, null, o);
        }
    }

    // ------------------------------------------------------------ ciclo de vida

    @Override
    public void surfaceCreated(SurfaceHolder holder) { resume(); }

    @Override
    public void surfaceChanged(SurfaceHolder holder, int f, int w, int h) {
        // escolhe um zoom inteiro que mostre ~17 tiles na horizontal
        int s = Math.max(2, Math.round(w / (17f * TILE)));
        scale = s;
        float size = Math.min(w, h) * 0.34f;
        float margin = Math.min(w, h) * 0.05f;
        dpad.layout(margin, h - size - margin, size);
    }

    @Override
    public void surfaceDestroyed(SurfaceHolder holder) { pause(); }

    public void resume() {
        if (running) return;
        running = true;
        lastNanos = 0L;
        thread = new Thread(this, "GameLoop");
        thread.start();
    }

    public void pause() {
        running = false;
        if (thread != null) {
            try { thread.join(800); } catch (InterruptedException ignored) { }
            thread = null;
        }
    }

    // ------------------------------------------------------------------- input

    @SuppressLint("ClickableViewAccessibility")
    @Override
    public boolean onTouchEvent(MotionEvent e) {
        dpad.onTouch(e);
        return true;
    }

    // -------------------------------------------------------------- game loop

    @Override
    public void run() {
        while (running) {
            long now = System.nanoTime();
            if (lastNanos == 0L) lastNanos = now;
            float dt = (now - lastNanos) / 1_000_000_000f;
            lastNanos = now;
            if (dt > 0.05f) dt = 0.05f;        // evita saltos apos pausa
            if (dt > 0f) fps = fps * 0.92f + (1f / dt) * 0.08f;

            update(dt);

            Canvas c = null;
            SurfaceHolder holder = getHolder();
            try {
                c = holder.lockHardwareCanvas();
                if (c != null) renderFrame(c);
            } finally {
                if (c != null) holder.unlockCanvasAndPost(c);
            }
        }
    }

    private void update(float dt) {
        player.update(dt, dpad.dirX(), dpad.dirY(), map);
        followCamera();
    }

    private void followCamera() {
        int w = getWidth(), h = getHeight();
        if (w == 0 || h == 0) return;
        float viewW = w / scale, viewH = h / scale;
        float targetX = player.x - viewW / 2f;
        float targetY = (player.y - SPRITE / 4f) - viewH / 2f;

        float maxX = Math.max(0f, map.pixelWidth() - viewW);
        float maxY = Math.max(0f, map.pixelHeight() - viewH);
        camX = clamp(targetX, 0f, maxX);
        camY = clamp(targetY, 0f, maxY);
    }

    private static float clamp(float v, float lo, float hi) {
        return v < lo ? lo : (v > hi ? hi : v);
    }

    // ----------------------------------------------------------------- render

    private void renderFrame(Canvas c) {
        c.drawColor(Color.BLACK);

        int w = getWidth(), h = getHeight();
        float viewW = w / scale, viewH = h / scale;

        int x0 = (int) Math.floor(camX / TILE);
        int y0 = (int) Math.floor(camY / TILE);
        int x1 = (int) Math.ceil((camX + viewW) / TILE);
        int y1 = (int) Math.ceil((camY + viewH) / TILE);

        // --- camada do mapa
        for (int ty = y0; ty <= y1; ty++) {
            for (int tx = x0; tx <= x1; tx++) {
                int i = map.tileIndex(tx, ty);
                src.set(i * TILE, 0, (i + 1) * TILE, TILE);
                float dx = (tx * TILE - camX) * scale;
                float dy = (ty * TILE - camY) * scale;
                dst.set(dx, dy, dx + TILE * scale, dy + TILE * scale);
                c.drawBitmap(tiles, src, dst, paint);
            }
        }

        // --- sombra do heroi
        float px = (player.x - camX) * scale;
        float py = (player.y - camY) * scale;
        c.drawOval(px - 10f * scale, py - 5f * scale,
                px + 10f * scale, py + 2f * scale, shadowPaint);

        // --- heroi
        int row = player.dir;
        int col = player.frame();
        src.set(col * SPRITE, row * SPRITE, (col + 1) * SPRITE, (row + 1) * SPRITE);
        float hw = SPRITE * scale;
        dst.set(px - hw / 2f, py - hw + 2f * scale, px + hw / 2f, py + 2f * scale);
        c.drawBitmap(hero, src, dst, paint);

        drawHud(c, w, h);
    }

    private void drawHud(Canvas c, int w, int h) {
        RectF b = dpad.bounds();
        paint.setAlpha(210);
        c.drawBitmap(dpadBmp, null, b, paint);
        paint.setAlpha(255);
        dpad.drawHighlight(c, hudPaint);
        hudPaint.setColor(Color.WHITE);

        // painel de coordenadas no canto superior esquerdo
        float pad = Math.min(w, h) * 0.02f;
        hudPaint.setTextSize(Math.min(w, h) * 0.035f);
        String txt = "X " + (int) (player.x / TILE) + "   Y " + (int) (player.y / TILE);
        float tw = hudPaint.measureText(txt);
        float th = hudPaint.getTextSize();
        hudPaint.setColor(0x99000000);
        c.drawRoundRect(pad, pad, pad * 2 + tw, pad + th * 1.8f, th * 0.3f, th * 0.3f, hudPaint);
        hudPaint.setColor(0xFFFFE066);
        c.drawText(txt, pad * 1.5f, pad + th * 1.25f, hudPaint);
    }
}
