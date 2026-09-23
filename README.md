# Rapper Laranja — mod para Friday Night Funkin'

Este repositório contém um mod V-Slice/Polymod que transforma a spritesheet enviada em um personagem substituto do Boyfriend no Friday Night Funkin' oficial para Android.

## Arquivo pronto

O pacote instalável é gerado em:

```text
release/RapperLaranja-v1.0.0.zip
```

Extraia o ZIP e copie a pasta `RapperLaranja` para a pasta `mods` do jogo.

## Conteúdo substituído

O mod cobre os IDs usados pelo Boyfriend nas músicas do jogo base:

- `bf`
- `bf-car`
- `bf-christmas`
- `bf-dark`
- `bf-holding-gf`
- `bf-pixel`

Também inclui animações de idle, quatro direções, erros, poses prolongadas, `hey`, susto, ícone de vida e compatibilidade com o Game Over original.

## Reconstrução

Requer ImageMagick, Python 3 e `zip`:

```bash
./tools/build_mod.sh
```

O script remove o fundo verde, reduz o spill de chroma key, gera o atlas Sparrow/XML, cria os ícones e empacota o ZIP.
