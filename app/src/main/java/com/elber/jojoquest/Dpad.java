package com.elber.jojoquest;

import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.RectF;
import android.view.MotionEvent;

/**
 * D-pad de setas desenhado a partir do bitmap dpad.png.
 * Suporta multitouch e diagonais (dois setores pressionados).
 */
public class Dpad {

    private final RectF bounds = new RectF();
    private float cx, cy, radius;

    /** zona morta central em fracao do raio */
    private static final float DEAD_ZONE = 0.28f;

    private float dirX = 0f, dirY = 0f;
    private int activePointer = -1;

    public void layout(float left, float top, float size) {
        bounds.set(left, top, left + size, top + size);
        cx = bounds.centerX();
        cy = bounds.centerY();
        radius = size * 0.5f;
    }

    public RectF bounds() { return bounds; }

    public float dirX() { return dirX; }

    public float dirY() { return dirY; }

    /** @return true se o evento foi consumido pelo d-pad */
    public boolean onTouch(MotionEvent e) {
        int action = e.getActionMasked();
        switch (action) {
            case MotionEvent.ACTION_DOWN:
            case MotionEvent.ACTION_POINTER_DOWN: {
                int idx = e.getActionIndex();
                if (inHitArea(e.getX(idx), e.getY(idx))) {
                    activePointer = e.getPointerId(idx);
                    update(e.getX(idx), e.getY(idx));
                    return true;
                }
                return false;
            }
            case MotionEvent.ACTION_MOVE: {
                if (activePointer < 0) return false;
                int idx = e.findPointerIndex(activePointer);
                if (idx >= 0) {
                    update(e.getX(idx), e.getY(idx));
                    return true;
                }
                return false;
            }
            case MotionEvent.ACTION_UP:
            case MotionEvent.ACTION_POINTER_UP:
            case MotionEvent.ACTION_CANCEL: {
                int idx = e.getActionIndex();
                if (action == MotionEvent.ACTION_CANCEL
                        || e.getPointerId(idx) == activePointer) {
                    release();
                    return true;
                }
                return false;
            }
        }
        return false;
    }

    private boolean inHitArea(float x, float y) {
        // area de toque generosa: 1.35x o desenho
        float r = radius * 1.35f;
        return x >= cx - r && x <= cx + r && y >= cy - r && y <= cy + r;
    }

    private void update(float x, float y) {
        float dx = (x - cx) / radius;
        float dy = (y - cy) / radius;
        float len = (float) Math.sqrt(dx * dx + dy * dy);
        if (len < DEAD_ZONE) {
            dirX = 0f;
            dirY = 0f;
            return;
        }
        // quantiza em 8 direcoes para dar sensacao de d-pad classico
        double ang = Math.atan2(dy, dx);
        int sector = (int) Math.round(ang / (Math.PI / 4.0));
        if (sector < 0) sector += 8;
        final float[] sx = {1, 1, 0, -1, -1, -1, 0, 1};
        final float[] sy = {0, 1, 1, 1, 0, -1, -1, -1};
        dirX = sx[sector];
        dirY = sy[sector];
    }

    private void release() {
        activePointer = -1;
        dirX = 0f;
        dirY = 0f;
    }

    /** Overlay de brilho no setor pressionado. */
    public void drawHighlight(Canvas c, Paint p) {
        if (dirX == 0f && dirY == 0f) return;
        float arm = radius * 0.62f;
        float w = radius * 0.46f;
        float hx = cx + dirX * arm;
        float hy = cy + dirY * arm;
        p.setColor(0x66FFE066);
        c.drawRoundRect(hx - w / 2, hy - w / 2, hx + w / 2, hy + w / 2,
                w * 0.25f, w * 0.25f, p);
    }
}
