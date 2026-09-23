package com.elber.jojoquest;

import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.Rect;
import android.graphics.RectF;
import android.graphics.Typeface;

/** Tela inicial: fundo pixel art, logo, botoes e resumo do Dex. */
public class TitleScreen {

    public static final int BTN_NONE = -1;
    public static final int BTN_START = 0;
    public static final int BTN_CONTINUE = 1;

    private final Bitmap bg;
    private final Bitmap coinIcon;
    private final Paint p = new Paint();
    private final Paint text = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Rect srcR = new Rect();
    private final RectF dstR = new RectF();

    private final RectF btnStart = new RectF();
    private final RectF btnContinue = new RectF();
    private boolean hasSave = false;
    private int pressed = BTN_NONE;
    private float time = 0f;

    public TitleScreen(Bitmap bg, Bitmap coinIcon) {
        this.bg = bg;
        this.coinIcon = coinIcon;
        p.setFilterBitmap(false);
        p.setAntiAlias(false);
        text.setTypeface(Typeface.create(Typeface.MONOSPACE, Typeface.BOLD));
        text.setTextAlign(Paint.Align.CENTER);
    }

    public void setHasSave(boolean v) { hasSave = v; }

    public void update(float dt) { time += dt; }

    public void layout(int w, int h) {
        float bw = Math.min(w * 0.44f, 420f);
        float bh = Math.max(h * 0.11f, 54f);
        float cx = w / 2f;
        float baseY = h * 0.60f;
        btnStart.set(cx - bw / 2, baseY, cx + bw / 2, baseY + bh);
        float gap = bh * 0.28f;
        btnContinue.set(cx - bw / 2, baseY + bh + gap, cx + bw / 2, baseY + bh * 2 + gap);
    }

    /** @return o botao sob o ponto, ou BTN_NONE */
    public int hitTest(float x, float y) {
        if (btnStart.contains(x, y)) return BTN_START;
        if (hasSave && btnContinue.contains(x, y)) return BTN_CONTINUE;
        return BTN_NONE;
    }

    public void setPressed(int b) { pressed = b; }

    public void draw(Canvas c, int w, int h, Dex dex) {
        // --- fundo: cover, escala inteira quando possivel
        float sx = w / (float) bg.getWidth();
        float sy = h / (float) bg.getHeight();
        float s = Math.max(sx, sy);
        float dw = bg.getWidth() * s, dh = bg.getHeight() * s;
        srcR.set(0, 0, bg.getWidth(), bg.getHeight());
        dstR.set((w - dw) / 2f, (h - dh) / 2f, (w + dw) / 2f, (h + dh) / 2f);
        c.drawBitmap(bg, srcR, dstR, p);

        // escurece um pouco a base para o texto respirar
        p.setColor(0x55000000);
        c.drawRect(0, h * 0.45f, w, h, p);

        drawLogo(c, w, h);

        // --- botoes
        drawButton(c, btnStart, hasSave ? "NOVO JOGO" : "JOGAR", pressed == BTN_START, true);
        if (hasSave) {
            drawButton(c, btnContinue, "CONTINUAR", pressed == BTN_CONTINUE, false);
        }

        drawDexSummary(c, w, h, dex);
    }

    private void drawLogo(Canvas c, int w, int h) {
        float cx = w / 2f;
        float size = Math.min(w * 0.13f, h * 0.20f);
        float y = h * 0.26f;
        float pulse = 1f + (float) Math.sin(time * 2.2) * 0.02f;

        text.setTextSize(size * pulse);
        // contorno grosso
        text.setStyle(Paint.Style.STROKE);
        text.setStrokeWidth(size * 0.18f);
        text.setColor(0xFF1A0B28);
        c.drawText("JOJO", cx, y, text);
        c.drawText("QUEST", cx, y + size * 1.05f, text);
        // preenchimento dourado
        text.setStyle(Paint.Style.FILL);
        text.setColor(0xFFFFE066);
        c.drawText("JOJO", cx, y, text);
        text.setColor(0xFFFFC93C);
        c.drawText("QUEST", cx, y + size * 1.05f, text);

        // subtitulo
        text.setTextSize(size * 0.22f);
        text.setColor(0xCCE6D8FF);
        c.drawText("UMA AVENTURA BIZARRA", cx, y + size * 1.55f, text);
    }

    private void drawButton(Canvas c, RectF r, String label, boolean down, boolean primary) {
        float off = down ? r.height() * 0.05f : 0f;
        float rad = r.height() * 0.24f;

        // sombra
        p.setColor(0x88000000);
        c.drawRoundRect(r.left, r.top + r.height() * 0.09f, r.right,
                r.bottom + r.height() * 0.09f, rad, rad, p);
        // corpo
        p.setColor(primary ? (down ? 0xFFD9A800 : 0xFFFFC93C)
                           : (down ? 0xFF4A2E73 : 0xFF6B3FA0));
        c.drawRoundRect(r.left, r.top + off, r.right, r.bottom + off, rad, rad, p);
        // borda
        p.setColor(primary ? 0xFF7A5A00 : 0xFF2B1440);
        p.setStyle(Paint.Style.STROKE);
        p.setStrokeWidth(Math.max(2f, r.height() * 0.06f));
        c.drawRoundRect(r.left, r.top + off, r.right, r.bottom + off, rad, rad, p);
        p.setStyle(Paint.Style.FILL);

        text.setTextSize(r.height() * 0.40f);
        text.setColor(primary ? 0xFF241436 : 0xFFFFFFFF);
        c.drawText(label, r.centerX(), r.centerY() + off + r.height() * 0.14f, text);
    }

    private void drawDexSummary(Canvas c, int w, int h, Dex dex) {
        if (dex == null) return;
        float pad = Math.min(w, h) * 0.035f;
        float ts = Math.min(w, h) * 0.038f;
        float icon = ts * 1.5f;

        // moedas no topo direito
        String coins = String.valueOf(dex.coins());
        text.setTextAlign(Paint.Align.RIGHT);
        text.setTextSize(ts);

        float bx = w - pad;
        p.setColor(0x99000000);
        float bw = text.measureText(coins) + icon + pad * 1.8f;
        c.drawRoundRect(bx - bw, pad, bx, pad + icon * 1.35f, icon * 0.35f, icon * 0.35f, p);

        dstR.set(bx - bw + pad * 0.6f, pad + icon * 0.17f,
                 bx - bw + pad * 0.6f + icon, pad + icon * 1.17f);
        c.drawBitmap(coinIcon, null, dstR, p);

        text.setColor(0xFFFFE066);
        c.drawText(coins, bx - pad * 0.7f, pad + icon * 0.95f, text);

        // progresso do dex no rodape
        text.setTextAlign(Paint.Align.CENTER);
        text.setTextSize(ts * 0.8f);
        text.setColor(0x99FFFFFF);
        c.drawText("DEX  " + dex.foundCount() + " / " + dex.totalCount(),
                w / 2f, h - pad, text);
    }
}
