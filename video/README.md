# Vídeo educativo — Art. 148 do Código Penal (Sequestro e Cárcere Privado)

- **Vídeo:** `art148_sequestro_carcere_privado.mp4` (1920×1080, 30 fps, ~6 min 50 s, narração em pt-BR)
- **Legendas:** `art148_sequestro_carcere_privado.srt`
- **Roteiro (texto da tela + narração):** `roteiro.py`
- **Gerador:** `gerar_video.py` (Pillow + NumPy + Piper TTS + ffmpeg)

## Estrutura

1. Abertura e texto do caput · 2. Conceito · 3. Sequestro x Cárcere Privado (animação comparativa)
· 4. Elementos do crime · 5. Formas qualificadas (caput, § 1º e § 2º, diferenciados por cor)
· 6. Causa de diminuição · 7. Hediondez e consequências · 8. Exemplos fictícios
· 9. Distinção dos arts. 146 e 159 · 10. Quadro-resumo · 11. Conclusão e referências

## Notas de precisão jurídica

Pontos conferidos na redação vigente e ajustados em relação ao briefing:

- **§ 1º, V** do art. 148 é "se o crime é praticado com **fins libidinosos**" (Lei 11.106/2005).
  A finalidade de obter vantagem econômica **não** está no art. 148: sequestrar para obter vantagem
  "como condição ou preço do resgate" é **extorsão mediante sequestro (art. 159)**. O vídeo explica essa diferença.
- **§ 1º, II** fala em internação "em **casa de saúde ou hospital**".
- Os §§ 1º e 2º são **qualificadoras**, porque fixam novas penas mínima e máxima (2 a 5 e 2 a 8 anos).
  O art. 148 não tem causa de aumento em fração nem minorante própria.
- **Hediondez:** a Lei 14.811/2024 incluiu o inciso XI no art. 1º da Lei 8.072/1990. Por isso, só é hediondo
  o sequestro e cárcere privado **contra menor de 18 anos (art. 148, § 1º, IV)**. Como a lei é mais gravosa,
  não retroage.

Não foi possível acessar o site do Planalto a partir do ambiente de geração. Por isso, a redação foi conferida
em fontes secundárias que reproduzem o texto legal. Antes de publicar, recomenda-se revisar em:

- https://www.planalto.gov.br/ccivil_03/decreto-lei/del2848compilado.htm
- https://www.planalto.gov.br/ccivil_03/leis/l8072.htm

## Como regenerar

```bash
pip install pillow numpy piper-tts imageio-ffmpeg
# voz pt-BR: https://github.com/rhasspy/piper/releases/download/v0.0.2/voice-pt-br-edresson-low.tar.gz
python3 gerar_video.py --voice pt-br-edresson-low.onnx --out art148_sequestro_carcere_privado.mp4
python3 gerar_video.py --voice pt-br-edresson-low.onnx --preview   # só PNGs de cada tela
```
