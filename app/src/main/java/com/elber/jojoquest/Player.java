package com.elber.jojoquest;

/** Estado do heroi: posicao em pixels do mundo, direcao e animacao de caminhada. */
public class Player {

    public static final int DIR_DOWN = 0;
    public static final int DIR_UP = 1;
    public static final int DIR_LEFT = 2;
    public static final int DIR_RIGHT = 3;

    /** Ordem dos frames na spritesheet para dar um passo natural. */
    private static final int[] WALK_CYCLE = {0, 1, 2, 3};

    public float x, y;                // centro dos pes, em pixels do mundo
    public int dir = DIR_DOWN;
    public float speed = 88f;         // pixels por segundo

    // caixa de colisao (menor que o sprite: so a base do corpo)
    public final float halfW = 8f;
    public final float bodyH = 10f;

    private float animTime = 0f;
    private boolean moving = false;

    public Player(float x, float y) {
        this.x = x;
        this.y = y;
    }

    public void update(float dt, float dx, float dy, GameMap map) {
        moving = (dx != 0f || dy != 0f);

        if (moving) {
            // direcao visual: privilegia o eixo dominante
            if (Math.abs(dx) > Math.abs(dy)) {
                dir = dx > 0 ? DIR_RIGHT : DIR_LEFT;
            } else {
                dir = dy > 0 ? DIR_DOWN : DIR_UP;
            }
            float len = (float) Math.sqrt(dx * dx + dy * dy);
            if (len > 1f) { dx /= len; dy /= len; }

            float step = speed * dt;
            moveAxis(dx * step, 0f, map);
            moveAxis(0f, dy * step, map);

            animTime += dt;
        } else {
            animTime = 0f;
        }
    }

    /** Move em um eixo por vez para permitir deslizar nas paredes. */
    private void moveAxis(float mx, float my, GameMap map) {
        if (mx == 0f && my == 0f) return;
        float nx = x + mx;
        float ny = y + my;
        if (!collides(nx, ny, map)) {
            x = nx;
            y = ny;
        }
    }

    private boolean collides(float cx, float cy, GameMap map) {
        float left = cx - halfW;
        float right = cx + halfW - 0.01f;
        float top = cy - bodyH;
        float bottom = cy - 0.01f;
        int t = GameMap.TILE;
        for (int ty = (int) Math.floor(top / t); ty <= (int) Math.floor(bottom / t); ty++) {
            for (int tx = (int) Math.floor(left / t); tx <= (int) Math.floor(right / t); tx++) {
                if (map.isSolid(tx, ty)) return true;
            }
        }
        return false;
    }

    /** Frame atual (0..3) na linha da direcao. */
    public int frame() {
        if (!moving) return 0;
        int i = (int) (animTime / 0.14f) % WALK_CYCLE.length;
        return WALK_CYCLE[i];
    }

    public boolean isMoving() { return moving; }
}
