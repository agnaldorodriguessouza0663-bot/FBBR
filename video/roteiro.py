# -*- coding: utf-8 -*-
"""Roteiro do vídeo: Art. 148 do Código Penal — Sequestro e Cárcere Privado.

Cada cena define os elementos visuais (com o "passo" em que aparecem) e os
segmentos de narração (texto falado, passo visual exibido durante a fala).
Números por extenso na narração para a síntese de voz pronunciar corretamente.
"""

BLUE, GOLD, WINE, GREEN, GREY = "blue", "gold", "wine", "green", "grey"

SCENES = [
    # 1. ABERTURA -------------------------------------------------------------
    dict(
        kind="title",
        sec="1", secname="Abertura",
        segs=[
            ('Artigo cento e quarenta e oito do Código Penal: sequestro e cárcere privado.', 1),
            ('Vamos ver o conceito, a diferença entre as duas formas, as qualificadoras, a hediondez e as distinções com outros crimes.', 2),
        ],
    ),
    dict(
        sec="1", secname="Abertura",
        title="O que o art. 148 protege?",
        items=[
            dict(t="bullet", step=1, text="Capítulo dos crimes contra a **liberdade individual**"),
            dict(t="bullet", step=1, text="Bem jurídico: **liberdade de locomoção** — ir, vir e permanecer"),
            dict(t="quote", step=2, label="Art. 148, caput — Código Penal",
                 text="Privar alguém de sua liberdade, mediante sequestro ou cárcere privado:"),
            dict(t="penalty", step=3, color=BLUE, text="Pena — reclusão, de 1 (um) a 3 (três) anos."),
        ],
        segs=[
            ('O artigo protege a liberdade individual, especialmente a liberdade de locomoção: ir, vir e permanecer.', 1),
            ('Diz o caput: privar alguém de sua liberdade, mediante sequestro ou cárcere privado.', 2),
            ('Pena: reclusão, de um a três anos.', 3),
        ],
    ),
    # 2. CONCEITO ---------------------------------------------------------------
    dict(
        sec="2", secname="Conceito do crime",
        title="Conceito: privar alguém de sua liberdade",
        items=[
            dict(t="bullet", step=1, text="Impedir a vítima de **sair** de um local ou obrigá-la a **permanecer** em certo espaço"),
            dict(t="bullet", step=2, text="Crime comum: **qualquer pessoa** pode ser sujeito ativo ou passivo"),
            dict(t="bullet", step=3, text="**Não exige violência física**: pode haver grave ameaça, fraude ou uma porta trancada"),
            dict(t="card", step=4, color=GOLD, head="Exemplo hipotético",
                 body="Carlos esconde a chave e tranca a porta do apartamento, impedindo que Ana saia "
                      "durante toda a tarde. Mesmo sem agressão, há **privação da liberdade**."),
        ],
        segs=[
            ('Privar a liberdade é impedir a vítima de sair de um local, ou obrigá-la a permanecer em certo espaço.', 1),
            ('É crime comum: qualquer pessoa pode ser autor ou vítima.', 2),
            ('E não exige violência física: basta, por exemplo, grave ameaça, fraude ou uma porta trancada.', 3),
            ('Exemplo: Carlos tranca a porta e esconde a chave, impedindo Ana de sair durante a tarde. Mesmo sem agressão, há privação da liberdade.', 4),
        ],
    ),
    # 3. SEQUESTRO x CÁRCERE -----------------------------------------------------
    dict(
        kind="compare",
        sec="3", secname="Sequestro x Cárcere Privado",
        title="Sequestro x Cárcere Privado",
        segs=[
            ('A doutrina distingue sequestro e cárcere privado pela extensão do confinamento.', 1),
            ('No sequestro, a vítima pode circular por um espaço amplo, como uma casa ou um sítio, mas não pode deixá-lo.', 2),
            ('No cárcere privado, ela fica confinada em espaço delimitado, como um quarto ou um cômodo.', 3),
            ('Mas o núcleo é o mesmo, privar alguém de sua liberdade, e a pena também.', 4),
        ],
    ),
    # 4. ELEMENTOS -----------------------------------------------------------------
    dict(
        sec="4", secname="Elementos do crime",
        title="Elementos do crime",
        items=[
            dict(t="row", step=1, cards=[
                dict(color=BLUE, head="Conduta", body="**Privar** alguém de sua liberdade"),
                dict(color=BLUE, head="Bem jurídico", body="**Liberdade individual** (de locomoção)"),
                dict(color=BLUE, head="Elemento subjetivo", body="**Dolo** — não há forma culposa", step=2),
            ]),
            dict(t="card", step=3, color=GOLD, head="Consumação",
                 body="Quando a vítima é **efetivamente privada** da liberdade por tempo juridicamente "
                      "relevante. Crime **permanente**: a consumação se prolonga enquanto durar a privação "
                      "(flagrante possível a qualquer momento)."),
            dict(t="card", step=4, color=GOLD, head="Tentativa — admissível",
                 body="O agente **inicia a execução**, mas não consegue privar a vítima da liberdade por "
                      "circunstâncias alheias à sua vontade (ex.: ela foge antes de ser trancada)."),
        ],
        segs=[
            ('A conduta é privar alguém de sua liberdade, e o bem jurídico é a liberdade individual.', 1),
            ('O elemento subjetivo é o dolo. Não há forma culposa.', 2),
            ('A consumação ocorre com a efetiva privação da liberdade, por tempo relevante. E o crime é permanente: a consumação se prolonga enquanto durar a privação.', 3),
            ('A tentativa é admissível: por exemplo, quando a vítima foge antes de ser trancada.', 4),
        ],
    ),
    # 5. QUALIFICADORAS ----------------------------------------------------------------
    dict(
        sec="5", secname="Formas qualificadas",
        title="Formas qualificadas e causas de aumento de pena",
        items=[
            dict(t="row", step=1, cards=[
                dict(color=BLUE, head="Caput — tipo básico", body="Reclusão de **1 a 3 anos**"),
                dict(color=GOLD, head="§ 1º — qualificadora", body="Reclusão de **2 a 5 anos**\nincisos I a V"),
                dict(color=WINE, head="§ 2º — qualificadora", body="Reclusão de **2 a 8 anos**\ngrave sofrimento físico ou moral"),
            ]),
            dict(t="banner", step=2, color=GOLD,
                 text="§§ 1º e 2º são **qualificadoras**: fixam novos limites mínimo e máximo. "
                      "O art. 148 **não prevê causa de aumento** em fração."),
        ],
        segs=[
            ('Estrutura das penas: o caput prevê reclusão de um a três anos; o parágrafo primeiro, de dois a cinco; e o parágrafo segundo, de dois a oito.', 1),
            ('Os dois parágrafos são qualificadoras, pois fixam novos limites de pena. O artigo não prevê causa de aumento em fração.', 2),
        ],
    ),
    dict(
        sec="5", secname="Formas qualificadas",
        title="§ 1º — Reclusão de 2 a 5 anos",
        items=[
            dict(t="inciso", step=1, num="I", text="Vítima **ascendente, descendente, cônjuge ou companheiro** do agente, ou **maior de 60 anos**"),
            dict(t="inciso", step=2, num="II", text="Crime praticado mediante **internação** da vítima em **casa de saúde ou hospital**"),
            dict(t="inciso", step=3, num="III", text="Privação da liberdade que dura **mais de 15 dias**"),
            dict(t="inciso", step=4, num="IV", text="Crime praticado contra **menor de 18 anos**"),
            dict(t="inciso", step=5, num="V", text="Crime praticado com **fins libidinosos**"),
            dict(t="banner", step=6, color=WINE,
                 text="Atenção: finalidade de obter **vantagem econômica** como condição ou preço do resgate "
                      "**não está no art. 148** — é extorsão mediante sequestro (**art. 159**)."),
        ],
        segs=[
            ('O parágrafo primeiro traz cinco hipóteses. Primeira: vítima ascendente, descendente, cônjuge ou companheiro do agente, ou maior de sessenta anos.', 1),
            ('Segunda: internação da vítima em casa de saúde ou hospital.', 2),
            ('Terceira: privação por mais de quinze dias.', 3),
            ('Quarta: vítima menor de dezoito anos.', 4),
            ('Quinta: fins libidinosos.', 5),
            ('Cuidado: sequestrar para obter vantagem, como condição ou preço do resgate, não está aqui. Isso é extorsão mediante sequestro, do artigo cento e cinquenta e nove.', 6),
        ],
    ),
    dict(
        sec="5", secname="Formas qualificadas",
        title="§ 2º — Reclusão de 2 a 8 anos",
        items=[
            dict(t="quote", step=1, label="Art. 148, § 2º — Código Penal", color=WINE,
                 text="Se resulta à vítima, em razão de maus-tratos ou da natureza da detenção, "
                      "grave sofrimento físico ou moral:"),
            dict(t="penalty", step=1, color=WINE, text="Pena — reclusão, de 2 (dois) a 8 (oito) anos."),
            dict(t="bullet", step=2, color=WINE, text="Aqui, o que qualifica é o **resultado**: o grave sofrimento suportado pela vítima"),
        ],
        segs=[
            ('O parágrafo segundo pune com dois a oito anos quando resulta à vítima, por maus-tratos ou pela natureza da detenção, grave sofrimento físico ou moral.', 1),
            ('Aqui, o que qualifica o crime é o resultado.', 2),
        ],
    ),
    # 6. DIMINUIÇÃO -------------------------------------------------------------------
    dict(
        sec="6", secname="Causas de diminuição",
        title="Existe causa de diminuição de pena no art. 148?",
        items=[
            dict(t="banner", step=1, color=WINE, big=True,
                 text="**Não.** O art. 148 não prevê minorante própria."),
            dict(t="row", step=2, cards=[
                dict(color=GOLD, head="Qualificadora", body="Altera a pena **mínima e máxima**\n(ex.: § 1º: 2 a 5 anos)"),
                dict(color=BLUE, head="Causa de aumento", body="Aplica **fração** de aumento\n3ª fase da dosimetria"),
            ]),
            dict(t="row", step=3, cards=[
                dict(color=GREEN, head="Causa de diminuição", body="Aplica **fração** de redução\n3ª fase (ex.: tentativa, art. 14)"),
                dict(color=GREY, head="Atenuante", body="Art. 65 do CP — **2ª fase**\n(ex.: confissão espontânea)"),
            ]),
        ],
        segs=[
            ('Há causa de diminuição de pena no artigo cento e quarenta e oito? Não. Não existe minorante própria.', 1),
            ('Não confunda: qualificadoras mudam os limites da pena; causas de aumento aplicam frações, na terceira fase.', 2),
            ('Causas gerais de diminuição, como a tentativa, vêm da Parte Geral. E atenuantes, como a confissão, incidem na segunda fase.', 3),
        ],
    ),
    # 7. HEDIONDEZ --------------------------------------------------------------------
    dict(
        sec="7", secname="Hediondez",
        title="Sequestro e cárcere privado são crimes hediondos?",
        items=[
            dict(t="quote", step=1, label="Lei 8.072/1990, art. 1º, XI — incluído pela Lei 14.811/2024", color=GOLD,
                 text="sequestro e cárcere privado cometido contra menor de 18 (dezoito) anos "
                      "(art. 148, § 1º, inciso IV);"),
            dict(t="row", step=2, cards=[
                dict(color=WINE, head="Hediondo", body="Somente **§ 1º, IV**\nvítima menor de 18 anos"),
                dict(color=GREY, head="Fora do rol expresso", body="caput; § 1º, I, II, III e V; § 2º"),
            ]),
            dict(t="banner", step=3, color=GOLD, big=True,
                 text="Nem toda modalidade do art. 148 recebe automaticamente o tratamento de crime hediondo."),
        ],
        segs=[
            ('É crime hediondo? Depende da modalidade. A Lei catorze mil, oitocentos e onze, de dois mil e vinte e quatro, incluiu no rol da Lei dos Crimes Hediondos', 1),
            ('somente o sequestro e cárcere privado contra menor de dezoito anos, do parágrafo primeiro, inciso quarto. As demais modalidades não constam do rol.', 2),
            ('Portanto, nem toda modalidade é hedionda. E essa regra, mais gravosa, não retroage.', 3),
        ],
    ),
    dict(
        sec="7", secname="Hediondez",
        title="Consequências da hediondez",
        items=[
            dict(t="row", step=1, cards=[
                dict(color=WINE, head="Vedações", body="Insuscetível de **anistia, graça, indulto e fiança** (Lei 8.072, art. 2º, I e II)"),
                dict(color=WINE, head="Progressão de regime", body="Exige **frações maiores** de cumprimento (LEP, art. 112)"),
            ]),
            dict(t="row", step=2, cards=[
                dict(color=WINE, head="Livramento condicional", body="Após **mais de 2/3** da pena; vedado ao reincidente específico (CP, art. 83, V)"),
                dict(color=WINE, head="Prisão temporária", body="Até **30 dias**, prorrogáveis por igual período (Lei 8.072, art. 2º, § 4º)"),
            ]),
            dict(t="banner", step=3, color=GOLD,
                 text="Hediondez **não aumenta a pena** do tipo: continua de 2 a 5 anos. Muda o **tratamento** penal e processual."),
        ],
        segs=[
            ('Consequências: não cabe anistia, graça, indulto nem fiança, e a progressão de regime exige frações maiores.', 1),
            ('O livramento condicional exige mais de dois terços da pena, e a prisão temporária pode chegar a trinta dias, prorrogáveis.', 2),
            ('Mas a hediondez não aumenta a pena, que continua de dois a cinco anos. Muda o tratamento penal e processual.', 3),
        ],
    ),
    # 8. EXEMPLOS ----------------------------------------------------------------------
    dict(
        sec="8", secname="Exemplos práticos",
        title="Exemplos práticos (fictícios)",
        items=[
            dict(t="card", step=1, color=BLUE, head="Exemplo 1 — Cárcere privado",
                 body="Pedro tranca Marta em um **quarto**, contra a vontade dela, e impede sua saída. "
                      "Espaço delimitado → **caput: 1 a 3 anos**."),
            dict(t="card", step=2, color=BLUE, head="Exemplo 2 — Sequestro",
                 body="Bruno leva Júlio a um **sítio** e o impede de deixar a propriedade, embora Júlio circule "
                      "pelo terreno. Espaço amplo → **caput: 1 a 3 anos**."),
            dict(t="card", step=3, color=GOLD, head="Exemplo 3 — Forma qualificada (§ 1º, I e III)",
                 body="Lúcia mantém a vizinha, de **67 anos**, trancada em casa por **20 dias**. "
                      "Vítima maior de 60 e privação por mais de 15 dias → **2 a 5 anos**."),
        ],
        segs=[
            ('Exemplo um: Pedro tranca Marta em um quarto e impede sua saída. Espaço delimitado: cárcere privado, pena do caput.', 1),
            ('Exemplo dois: Bruno leva Júlio a um sítio e o impede de sair, embora ele circule pelo terreno. Espaço amplo: sequestro, também no caput.', 2),
            ('Exemplo três: Lúcia mantém a vizinha, de sessenta e sete anos, trancada por vinte dias. Vítima maior de sessenta e privação por mais de quinze dias: forma qualificada, de dois a cinco anos. As penas não se somam; a hipótese excedente pode pesar na pena-base.', 3),
        ],
    ),
    # 9. DISTINÇÃO ----------------------------------------------------------------------
    dict(
        sec="9", secname="Distinção de outros crimes",
        title="Distinção de outros crimes",
        items=[
            dict(t="row", step=1, cards=[
                dict(color=GREY, head="Art. 146 — Constrangimento ilegal",
                     body="Obrigar a vítima, mediante violência ou grave ameaça, a **fazer ou não fazer** algo\n"
                          "Detenção de **3 meses a 1 ano**, ou multa"),
                dict(color=BLUE, head="Art. 148 — Sequestro e cárcere",
                     body="**Privar** alguém da liberdade de locomoção\n"
                          "Reclusão de **1 a 3 anos** (caput)", step=2),
                dict(color=WINE, head="Art. 159 — Extorsão med. sequestro",
                     body="Sequestrar com o fim de obter **vantagem, como condição ou preço do resgate**\n"
                          "Reclusão de **8 a 15 anos** · hediondo", step=3),
            ]),
            dict(t="banner", step=4, color=GOLD,
                 text="A tipificação correta depende das **circunstâncias concretas**, especialmente da **finalidade** do agente."),
        ],
        segs=[
            ('No constrangimento ilegal, artigo cento e quarenta e seis, a vítima é obrigada, por violência ou grave ameaça, a fazer ou não fazer algo. Pena: detenção de três meses a um ano, ou multa.', 1),
            ('No artigo cento e quarenta e oito, o núcleo é privar a liberdade de locomoção.', 2),
            ('Na extorsão mediante sequestro, artigo cento e cinquenta e nove, o fim é obter vantagem, como condição ou preço do resgate. É crime patrimonial e hediondo, com pena de oito a quinze anos.', 3),
            ('A tipificação depende das circunstâncias concretas, principalmente da finalidade do agente.', 4),
        ],
    ),
    # 10. QUADRO-RESUMO ------------------------------------------------------------------
    dict(
        sec="10", secname="Quadro-resumo",
        title="Quadro-resumo",
        items=[
            dict(t="table", step=1, rows=[
                ("Artigo", "148 do Código Penal"),
                ("Crime", "Sequestro e cárcere privado"),
                ("Bem jurídico", "Liberdade individual"),
                ("Conduta", "Privar alguém de sua liberdade"),
                ("Pena básica", "Reclusão de 1 a 3 anos"),
                ("Formas qualificadas", "§ 1º (2 a 5 anos) e § 2º (2 a 8 anos)"),
                ("Tentativa", "Admissível"),
                ("Hediondez", "Só § 1º, IV (menor de 18) — Lei 8.072/1990, art. 1º, XI"),
                ("Diminuição específica", "Não há minorante própria no art. 148"),
            ]),
        ],
        segs=[
            ('Confira o quadro-resumo com os pontos principais.', 1),
        ],
    ),
    # 11. CONCLUSÃO -----------------------------------------------------------------------
    dict(
        sec="11", secname="Conclusão",
        title="Para a prova, lembre-se:",
        items=[
            dict(t="check", step=1, text="O art. 148 protege a **liberdade individual**"),
            dict(t="check", step=1, text="Sequestro e cárcere privado estão no **mesmo dispositivo**"),
            dict(t="check", step=1, text="A diferença tradicional está na **forma e extensão** da privação"),
            dict(t="check", step=2, text="§ 1º: hipóteses punidas com **2 a 5 anos** · § 2º: **grave sofrimento** físico ou moral"),
            dict(t="check", step=2, text="Não confunda **qualificadora** com causa de aumento ou de diminuição"),
            dict(t="check", step=3, text="Não confunda o art. 148 com a **extorsão mediante sequestro** (art. 159)"),
            dict(t="check", step=3, text="Hediondez: conforme a modalidade da **Lei 8.072/1990** — hoje, § 1º, IV"),
        ],
        segs=[
            ('Para a prova, lembre-se: o artigo protege a liberdade individual; sequestro e cárcere privado estão no mesmo dispositivo e diferem na extensão da privação.', 1),
            ('Os parágrafos primeiro e segundo são qualificadoras, que não se confundem com causas de aumento ou de diminuição.', 2),
            ('Não confunda com a extorsão mediante sequestro. E verifique a hediondez conforme a modalidade, na redação vigente da Lei oito mil e setenta e dois.', 3),
        ],
    ),
    dict(
        kind="end",
        sec="11", secname="Conclusão",
        segs=[("Bons estudos, e até a próxima!", 1)],
    ),
]
