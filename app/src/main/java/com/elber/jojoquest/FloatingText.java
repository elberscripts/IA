package com.elber.jojoquest;

/** Texto flutuante tipo "+1" que sobe e some ao pegar uma moeda. */
public class FloatingText {

    private static final float LIFE = 0.9f;

    public final String text;
    public float x, y;
    public float age = 0f;

    public FloatingText(String text, float x, float y) {
        this.text = text;
        this.x = x;
        this.y = y;
    }

    public void update(float dt) {
        age += dt;
        y -= 26f * dt;
    }

    public boolean dead() { return age >= LIFE; }

    /** 255 -> 0 conforme envelhece. */
    public int alpha() {
        float t = 1f - (age / LIFE);
        return (int) (Math.max(0f, Math.min(1f, t)) * 255);
    }
}
