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
import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;

/** SurfaceView com game loop proprio: tela de titulo, mapa, heroi, moedas e HUD. */
public class GameView extends SurfaceView implements SurfaceHolder.Callback, Runnable,
        Dex.Listener {

    private static final int SPRITE = 64;      // celula na hero.png
    private static final int TILE = GameMap.TILE;

    private static final int STATE_TITLE = 0;
    private static final int STATE_PLAY = 1;

    private Thread thread;
    private volatile boolean running = false;

    private Bitmap tiles, hero, dpadBmp, coinSheet, coinHud, titleBg;
    private GameMap map;
    private Player player;
    private Dex dex;
    private TitleScreen title;
    private final Dpad dpad = new Dpad();

    private List<Coin> coins = new ArrayList<>();
    private final List<FloatingText> floaters = new ArrayList<>();

    private final Paint paint = new Paint();
    private final Paint hudPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint shadowPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Rect src = new Rect();
    private final RectF dst = new RectF();

    private int state = STATE_TITLE;
    private float scale = 3f;
    private float camX = 0f, camY = 0f;
    private float gameTime = 0f;
    private float coinPulse = 0f;              // anima o HUD ao ganhar moeda
    private long lastNanos = 0L;

    public GameView(Context ctx) {
        super(ctx);
        getHolder().addCallback(this);
        setFocusable(true);

        paint.setFilterBitmap(false);          // nearest neighbour = pixel art nitida
        paint.setAntiAlias(false);
        paint.setDither(false);

        hudPaint.setColor(Color.WHITE);
        hudPaint.setTypeface(Typeface.create(Typeface.MONOSPACE, Typeface.BOLD));

        shadowPaint.setColor(0x55000000);

        try {
            tiles = load("tiles.png");
            hero = load("hero.png");
            dpadBmp = load("dpad.png");
            coinSheet = load("coin.png");
            coinHud = load("coin_hud.png");
            titleBg = load("title_bg.png");
            map = new GameMap(ctx.getAssets(), "map.txt");
        } catch (Exception e) {
            throw new RuntimeException("Falha ao carregar assets do jogo", e);
        }

        dex = new Dex(ctx);
        dex.addListener(this);
        title = new TitleScreen(titleBg, coinHud);
        title.setHasSave(dex.totalEarned() > 0);

        resetWorld(false);
    }

    /** Recria o mundo. Se {@code fresh}, zera o progresso e devolve as moedas. */
    private void resetWorld(boolean fresh) {
        if (fresh) {
            dex.resetAll();
        }
        player = new Player(15 * TILE + TILE / 2f, 24 * TILE + TILE);
        coins = Coin.scatter(map, 40, dex);
        floaters.clear();
        dex.discover("jotaro");
        dex.discover("village");
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
        int s = Math.max(2, Math.round(w / (17f * TILE)));
        scale = s;
        float size = Math.min(w, h) * 0.34f;
        float margin = Math.min(w, h) * 0.05f;
        dpad.layout(margin, h - size - margin, size);
        title.layout(w, h);
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

    /** @return true se o back foi tratado (volta ao titulo). */
    public boolean onBackPressed() {
        if (state == STATE_PLAY) {
            state = STATE_TITLE;
            title.setHasSave(true);
            return true;
        }
        return false;
    }

    // ------------------------------------------------------------------- input

    @SuppressLint("ClickableViewAccessibility")
    @Override
    public boolean onTouchEvent(MotionEvent e) {
        if (state == STATE_TITLE) {
            handleTitleTouch(e);
        } else {
            dpad.onTouch(e);
        }
        return true;
    }

    private void handleTitleTouch(MotionEvent e) {
        switch (e.getActionMasked()) {
            case MotionEvent.ACTION_DOWN:
                title.setPressed(title.hitTest(e.getX(), e.getY()));
                break;
            case MotionEvent.ACTION_UP: {
                int b = title.hitTest(e.getX(), e.getY());
                title.setPressed(TitleScreen.BTN_NONE);
                if (b == TitleScreen.BTN_START) {
                    resetWorld(true);
                    state = STATE_PLAY;
                } else if (b == TitleScreen.BTN_CONTINUE) {
                    state = STATE_PLAY;
                }
                break;
            }
            case MotionEvent.ACTION_CANCEL:
                title.setPressed(TitleScreen.BTN_NONE);
                break;
        }
    }

    // ----------------------------------------------------------- Dex.Listener

    @Override
    public void onCoinsChanged(int total, int delta) {
        if (delta > 0) coinPulse = 1f;
    }

    // -------------------------------------------------------------- game loop

    @Override
    public void run() {
        while (running) {
            long now = System.nanoTime();
            if (lastNanos == 0L) lastNanos = now;
            float dt = (now - lastNanos) / 1_000_000_000f;
            lastNanos = now;
            if (dt > 0.05f) dt = 0.05f;

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
        gameTime += dt;
        if (coinPulse > 0f) coinPulse = Math.max(0f, coinPulse - dt * 2.6f);

        if (state == STATE_TITLE) {
            title.update(dt);
            return;
        }

        // botas velozes compradas no Dex deixam o heroi mais rapido
        player.speed = dex.isOwned("boots") ? 123f : 88f;
        player.update(dt, dpad.dirX(), dpad.dirY(), map);

        collectCoins();

        for (Iterator<FloatingText> it = floaters.iterator(); it.hasNext(); ) {
            FloatingText f = it.next();
            f.update(dt);
            if (f.dead()) it.remove();
        }

        followCamera();
    }

    private void collectCoins() {
        for (Coin c : coins) {
            if (c.collected) continue;
            if (c.touches(player.x, player.y)) {
                c.collected = true;
                dex.markPicked(c.id);
                int before = dex.coins();
                dex.addCoins(1);
                int gained = dex.coins() - before;
                dex.discover("coin");
                floaters.add(new FloatingText("+" + gained, c.x, c.y - 6f));
            }
        }
    }

    private void followCamera() {
        int w = getWidth(), h = getHeight();
        if (w == 0 || h == 0) return;
        float viewW = w / scale, viewH = h / scale;
        float targetX = player.x - viewW / 2f;
        float targetY = (player.y - SPRITE / 4f) - viewH / 2f;
        camX = clamp(targetX, 0f, Math.max(0f, map.pixelWidth() - viewW));
        camY = clamp(targetY, 0f, Math.max(0f, map.pixelHeight() - viewH));
    }

    private static float clamp(float v, float lo, float hi) {
        return v < lo ? lo : (v > hi ? hi : v);
    }

    // ----------------------------------------------------------------- render

    private void renderFrame(Canvas c) {
        int w = getWidth(), h = getHeight();

        if (state == STATE_TITLE) {
            title.draw(c, w, h, dex);
            return;
        }

        c.drawColor(Color.BLACK);
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

        drawCoins(c, viewW, viewH);

        // --- sombra + heroi
        float px = (player.x - camX) * scale;
        float py = (player.y - camY) * scale;
        c.drawOval(px - 10f * scale, py - 5f * scale,
                px + 10f * scale, py + 2f * scale, shadowPaint);

        src.set(player.frame() * SPRITE, player.dir * SPRITE,
                (player.frame() + 1) * SPRITE, (player.dir + 1) * SPRITE);
        float hw = SPRITE * scale;
        dst.set(px - hw / 2f, py - hw + 2f * scale, px + hw / 2f, py + 2f * scale);
        c.drawBitmap(hero, src, dst, paint);

        drawFloaters(c);
        drawHud(c, w, h);
    }

    private void drawCoins(Canvas c, float viewW, float viewH) {
        float cs = Coin.SIZE;
        for (Coin coin : coins) {
            if (coin.collected) continue;
            // culling: so desenha o que esta na tela
            if (coin.x < camX - cs || coin.x > camX + viewW + cs) continue;
            if (coin.y < camY - cs || coin.y > camY + viewH + cs) continue;

            int f = coin.frame(gameTime);
            src.set(f * Coin.SIZE, 0, (f + 1) * Coin.SIZE, Coin.SIZE);

            float cx = (coin.x - camX) * scale;
            float cy = (coin.y + coin.bob(gameTime) - camY) * scale;
            float s = Coin.SIZE * scale * 0.62f;

            // sombrinha no chao
            shadowPaint.setColor(0x33000000);
            c.drawOval(cx - s * 0.30f, cy + s * 0.34f,
                       cx + s * 0.30f, cy + s * 0.50f, shadowPaint);
            shadowPaint.setColor(0x55000000);

            dst.set(cx - s / 2f, cy - s / 2f, cx + s / 2f, cy + s / 2f);
            c.drawBitmap(coinSheet, src, dst, paint);
        }
    }

    private void drawFloaters(Canvas c) {
        if (floaters.isEmpty()) return;
        hudPaint.setTextAlign(Paint.Align.CENTER);
        float ts = 11f * scale;
        hudPaint.setTextSize(ts);
        for (FloatingText f : floaters) {
            float fx = (f.x - camX) * scale;
            float fy = (f.y - camY) * scale;
            int a = f.alpha();
            hudPaint.setStyle(Paint.Style.STROKE);
            hudPaint.setStrokeWidth(ts * 0.22f);
            hudPaint.setColor((a << 24) | 0x00201000);
            c.drawText(f.text, fx, fy, hudPaint);
            hudPaint.setStyle(Paint.Style.FILL);
            hudPaint.setColor((a << 24) | 0x00FFE066);
            c.drawText(f.text, fx, fy, hudPaint);
        }
        hudPaint.setTextAlign(Paint.Align.LEFT);
    }

    private void drawHud(Canvas c, int w, int h) {
        // --- d-pad
        RectF b = dpad.bounds();
        paint.setAlpha(210);
        c.drawBitmap(dpadBmp, null, b, paint);
        paint.setAlpha(255);
        dpad.drawHighlight(c, hudPaint);

        float pad = Math.min(w, h) * 0.025f;
        float ts = Math.min(w, h) * 0.045f;
        float icon = ts * 1.25f;

        // --- carteira de moedas (canto superior direito)
        String coinTxt = String.valueOf(dex.coins());
        hudPaint.setTextSize(ts);
        float tw = hudPaint.measureText(coinTxt);
        float boxW = tw + icon + pad * 2.4f;
        float boxH = icon * 1.5f;
        float bx = w - pad - boxW;

        hudPaint.setColor(0xAA000000);
        c.drawRoundRect(bx, pad, bx + boxW, pad + boxH, boxH * 0.3f, boxH * 0.3f, hudPaint);
        if (coinPulse > 0f) {
            hudPaint.setColor(((int) (coinPulse * 120) << 24) | 0x00FFE066);
            c.drawRoundRect(bx, pad, bx + boxW, pad + boxH,
                    boxH * 0.3f, boxH * 0.3f, hudPaint);
        }

        float grow = 1f + coinPulse * 0.22f;
        float ic = icon * grow;
        dst.set(bx + pad, pad + (boxH - ic) / 2f, bx + pad + ic, pad + (boxH + ic) / 2f);
        c.drawBitmap(coinHud, null, dst, paint);

        hudPaint.setColor(0xFFFFE066);
        c.drawText(coinTxt, bx + pad * 1.4f + icon, pad + boxH * 0.68f, hudPaint);

        // --- contador de moedas restantes no mapa
        int left = 0;
        for (Coin coin : coins) if (!coin.collected) left++;
        hudPaint.setTextSize(ts * 0.62f);
        hudPaint.setColor(0x99FFFFFF);
        c.drawText(left == 0 ? "TODAS AS MOEDAS!" : left + " no mapa",
                bx + pad, pad + boxH * 1.55f, hudPaint);

        // --- coordenadas (canto superior esquerdo)
        hudPaint.setTextSize(ts * 0.72f);
        String txt = "X " + (int) (player.x / TILE) + "   Y " + (int) (player.y / TILE);
        float th = hudPaint.getTextSize();
        hudPaint.setColor(0x99000000);
        c.drawRoundRect(pad, pad, pad * 2 + hudPaint.measureText(txt), pad + th * 1.9f,
                th * 0.3f, th * 0.3f, hudPaint);
        hudPaint.setColor(0xFFFFFFFF);
        c.drawText(txt, pad * 1.5f, pad + th * 1.32f, hudPaint);
    }
}
