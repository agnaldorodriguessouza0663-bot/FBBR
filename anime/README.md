# Direito Penal em Anime: Episódio 148, "A Porta Trancada"

Encenação em estilo anime sobre o **art. 148 do Código Penal** (sequestro e cárcere privado).

- **Vídeo:** `episodio148_anime.mp4` (1920×1080, 30 fps, cerca de 3 min 50 s, legendas embutidas no estilo fansub)
- **Legendas separadas:** `episodio148_anime.srt`
- **Código:** `episodio.py` (roteiro, cenas, vozes, efeitos sonoros e trilha) e `anime_chars.py` (personagens anime)

## Estilo

- Personagens com olhos grandes e brilho, sombreamento em duas cores, contorno e animação a 12 quadros por segundo ("em dois"), como nos animes de TV.
- Recursos de anime:
  - linhas de impacto e close nos olhos na abertura;
  - onomatopeias ("CLIC!", "TRANC!", "TREC! TREC!", "TOC TOC!"), gota de suor e sombra dramática no rosto;
  - cartela de título ("第148話"), eyecatch no meio do episódio e prévia do "próximo episódio";
  - flores de ipê-amarelo caindo, no lugar das cerejeiras.
- Vozes: cada personagem tem um tom próprio (Ana, Carlos, Bruno, policial e narrador). Os pensamentos de Ana têm eco.
  As vozes são sintéticas e offline.

## Personagens

Os personagens são os mesmos da animação 2D, redesenhados em traço de anime a partir das fotos de referência:

- **Ana:** a vítima. Estudante de Direito, pele negra, black power volumoso, blusa mostarda.
- **Carlos:** quem priva Ana da liberdade. Barba cheia, camiseta preta, correntinha.
- **Bruno:** o amigo que procura ajuda. Óculos, barba aparada, camiseta branca, relógio dourado.

## Conteúdo jurídico (conferido)

- **Caput:** privar alguém de sua liberdade, mediante sequestro ou cárcere privado. Reclusão de 1 a 3 anos.
- **Sequestro x cárcere privado:** a distinção é doutrinária. Os dois estão no mesmo artigo, com a mesma pena.
- **§ 1º (2 a 5 anos):**
  - vítima ascendente, descendente, cônjuge ou companheiro do agente, ou maior de 60 anos;
  - internação em casa de saúde ou hospital;
  - privação por mais de 15 dias;
  - vítima menor de 18 anos;
  - fins libidinosos.
- **§ 2º (2 a 8 anos):** grave sofrimento físico ou moral, por maus-tratos ou pela natureza da detenção.
- **Qualificadoras:** o art. 148 não tem causa de aumento nem de diminuição própria.
- **Hediondez:** somente o § 1º, IV (vítima menor de 18 anos), incluído no art. 1º, XI, da Lei 8.072/1990 pela Lei 14.811/2024.
- **Pedido de resgate:** é o art. 159 (extorsão mediante sequestro).
- **Constrangimento ilegal:** é o art. 146.

Na história, Ana fala em "ascendente, descendente, cônjuge ou companheira", como está na lei, e não em "parente".
A lei não abrange qualquer parente: irmãos, por exemplo, não estão no § 1º, I.

## Como regenerar

```bash
pip install pillow numpy piper-tts imageio-ffmpeg
python3 episodio.py --voice pt-br-edresson-low.onnx            # vídeo completo
python3 episodio.py --voice pt-br-edresson-low.onnx --preview  # quadros de prévia
```
