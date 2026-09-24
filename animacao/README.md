# Animação — Art. 148 do CP: estudo de caso (Ana, Carlos e Bruno)

- **Vídeo:** `art148_estudo_de_caso.mp4` (1920×1080, 30 fps, ~5 min 50 s, narração pt-BR, trilha discreta, legendas embutidas)
- **Legendas separadas:** `art148_estudo_de_caso.srt`
- **Código:** `animacao.py` (cenas e roteiro), `personagens.py` (personagens) e `cenarios.py` (cenários)
- **Versão realista com IA de vídeo:** `prompts_ia_video.md`

## Personagens

Os personagens são ilustrados a partir dos traços das fotos de referência. Não são retratos:

| Personagem | Referência | Traços mantidos em todas as cenas |
|---|---|---|
| **Ana**: vítima | foto da mulher | pele negra, cabelo crespo volumoso, blusa mostarda com decote em V, brincos dourados |
| **Carlos**: autor da privação | homem de barba cheia | barba cheia preta com fios grisalhos, cabelo curto, camiseta preta, correntinha |
| **Bruno**: amigo que busca ajuda | homem de óculos | óculos de armação fina, barba aparada, camiseta branca, jeans claro, relógio dourado |

## Cenas

1. Introdução
2. Personagens
3. O caso: a porta trancada
4. Tela do art. 148
5. Sequestro ≠ cárcere privado
6. Bruno percebe e liga para o 190
7. Formas qualificadas (§§ 1º e 2º)
8. Atenção para a prova
9. Hediondez (Lei 8.072/1990)
10. Arts. 146, 148 e 159
11. Desfecho, sem confronto
12. Resumo
13. Encerramento

## Precisão jurídica: ajustes feitos em relação ao briefing

- O **§ 1º, V** do art. 148 é "**fins libidinosos**". A "finalidade de obter vantagem econômica" **não** é hipótese
  do art. 148: sequestrar com o fim de obter vantagem como condição ou preço do resgate é o **art. 159**. A cena 7 mostra isso.
- O **§ 1º, II** fala em internação "em **casa de saúde ou hospital**".
- Os §§ 1º e 2º são **qualificadoras**. O art. 148 não prevê causa de aumento nem de diminuição própria.
- **Hediondez:** somente o § 1º, IV (vítima menor de 18 anos). A hipótese está no art. 1º, XI, da Lei 8.072/1990 e foi incluída pela Lei 14.811/2024.

Antes de publicar, confira a redação vigente no site do Planalto. Ele não estava acessível no ambiente em que o vídeo foi gerado.

## Como regenerar

```bash
pip install pillow numpy piper-tts imageio-ffmpeg
python3 animacao.py --voice pt-br-edresson-low.onnx            # vídeo completo
python3 animacao.py --voice pt-br-edresson-low.onnx --preview  # quadros de prévia
```
