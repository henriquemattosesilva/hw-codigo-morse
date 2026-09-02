# Desenha a montagem com imagens dos componentes, no formato de quem vai
# remontar o circuito no Tinkercad: protoboard com os furos de verdade,
# Arduino Uno e as pecas nas posicoes exatas.
#
#   python ferramentas/gerar-tinkercad.py
import io
import os

# ------------------------------------------------------------------- cores
CB = {
    "placa":     "#E9E9E4",  # corpo da protoboard
    "placa_b":   "#C9C9C2",
    "furo":      "#26262A",
    "furo_b":    "#9A9A94",
    "trilha_p":  "#D8443C",
    "trilha_m":  "#3A6FD8",
    "letra":     "#7A7A74",
    "uno":       "#128494",  # azul-esverdeado da placa Arduino
    "uno_esc":   "#0B5F6C",
    "header":    "#1C1C1E",
    "metal":     "#C2C7CC",
    "metal_esc": "#8A9098",
    "preto":     "#232326",
    "resistor":  "#D9BD8F",
    "resist_b":  "#B99B6D",
    "pcb":       "#1F7A3E",
    "tela":      "#1554B8",
    "tela_txt":  "#D3E9FF",
    "pot":       "#2F6FD0",
    "texto":     "#D6E2F2",
    "fraco":     "#8296B4",
    "apagado":   "#5A6E8C",
}

LED_COR = {
    "verde":    ("#3FBF4A", "#7CE886"),
    "amarelo":  ("#F0C020", "#FFE47A"),
    "azul":     ("#3B8FE8", "#8CC6FF"),
    "vermelho": ("#E23B2E", "#FF8A7A"),
}

# faixas de resistor, por valor
FAIXAS_220 = ["#D4222A", "#D4222A", "#8B4A16", "#D4AF37"]  # vermelho vermelho marrom ouro

MONO = "'IBM Plex Mono','SFMono-Regular',ui-monospace,monospace"

# ------------------------------------------------------- geometria da placa
PASSO = 26
COLS = 30
X0 = 74                     # centro da coluna 1
LINHAS = {
    "+t": 30, "-t": 52,
    "j": 104, "i": 130, "h": 156, "g": 182, "f": 208,
    "e": 262, "d": 288, "c": 314, "b": 340, "a": 366,
    "-b": 418, "+b": 440,
}
PLACA_X, PLACA_L = 34, X0 + PASSO * (COLS - 1) + 40 - 34
PLACA_Y, PLACA_A = 12, 458


def cx(col):
    return X0 + PASSO * (col - 1)


def cy(linha):
    return LINHAS[linha]


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def rotulo_peca(x, y, s, tam=11.5):
    """Texto sobre a protoboard: escuro, com halo claro para nao sumir."""
    return (f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="middle" font-family="{MONO}" '
            f'font-size="{tam}" font-weight="700" fill="#2E3A4A" stroke="#F4F4F0" '
            f'stroke-width="3.6" stroke-linejoin="round" paint-order="stroke fill"'
            f'>{esc(s)}</text>')


def txt(x, y, s, tam=12, cor=None, peso="500", anc="middle", extra=""):
    return (f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anc}" font-family="{MONO}" '
            f'font-size="{tam}" font-weight="{peso}" fill="{cor or CB["texto"]}" '
            f'{extra}>{esc(s)}</text>')


# ------------------------------------------------------------- a protoboard
def protoboard():
    s = io.StringIO()
    s.write(f'<rect x="{PLACA_X}" y="{PLACA_Y}" width="{PLACA_L}" height="{PLACA_A}" '
            f'rx="8" fill="{CB["placa"]}" stroke="{CB["placa_b"]}" stroke-width="1.5"/>')

    # canal central, onde os CIs e as chaves se encaixam
    s.write(f'<rect x="{PLACA_X + 8}" y="{cy("f") + 18}" width="{PLACA_L - 16}" '
            f'height="{cy("e") - cy("f") - 36}" fill="{CB["placa_b"]}" fill-opacity="0.55"/>')

    # trilhas de alimentacao
    for lado, (lp, lm) in (("t", ("+t", "-t")), ("b", ("-b", "+b"))):
        for linha, cor, sinal in ((lp, CB["trilha_p"] if lp.startswith("+") else CB["trilha_m"],
                                   "+" if lp.startswith("+") else "−"),
                                  (lm, CB["trilha_p"] if lm.startswith("+") else CB["trilha_m"],
                                   "+" if lm.startswith("+") else "−")):
            y = cy(linha)
            s.write(f'<path d="M{cx(2) - 14} {y} H{cx(COLS - 1) + 14}" stroke="{cor}" '
                    f'stroke-width="1.6" stroke-opacity="0.85"/>')
            for lb, ax in ((sinal, PLACA_X + 16), (sinal, PLACA_X + PLACA_L - 16)):
                s.write(txt(ax, y + 5, lb, 14, cor, "700"))

    # furos das trilhas: grupos de cinco, com folga a cada grupo
    for linha in ("+t", "-t", "-b", "+b"):
        y = cy(linha)
        for col in range(2, COLS):
            if col % 6 == 0:
                continue
            s.write(furo(cx(col), y))

    # furos da area principal
    for linha in ("j", "i", "h", "g", "f", "e", "d", "c", "b", "a"):
        y = cy(linha)
        for col in range(1, COLS + 1):
            s.write(furo(cx(col), y))
        for ax, anc in ((PLACA_X + 16, "middle"), (PLACA_X + PLACA_L - 16, "middle")):
            s.write(txt(ax, y + 4, linha, 11, CB["letra"], "500", anc))

    # numeros das colunas
    for col in range(1, COLS + 1):
        if col == 1 or col % 5 == 0:
            for y in (cy("j") - 20, cy("a") + 22):
                s.write(txt(cx(col), y, str(col), 10, CB["letra"], "500"))
    return s.getvalue()


def furo(x, y):
    return (f'<rect x="{x - 4.5:.1f}" y="{y - 4.5:.1f}" width="9" height="9" rx="1.4" '
            f'fill="{CB["furo"]}"/>'
            f'<rect x="{x - 4.5:.1f}" y="{y - 4.5:.1f}" width="9" height="2" rx="1" '
            f'fill="{CB["furo_b"]}" fill-opacity="0.35"/>')


# ------------------------------------------------------------ Arduino Uno
DIGITAIS = ["AREF", "GND", "13", "12", "11", "10", "9", "8"]
DIGITAIS2 = ["7", "6", "5", "4", "3", "2", "1", "0"]
PODER = ["IOR", "RST", "3V3", "5V", "GND", "GND", "VIN"]
ANALOG = ["A0", "A1", "A2", "A3", "A4", "A5"]


def arduino_uno(ox, oy, usados):
    """Placa vista de cima. usados: {rotulo do pino: cor do destaque}"""
    L, A = 470, 268
    s = io.StringIO()
    s.write(f'<g transform="translate({ox},{oy})">')
    s.write(f'<rect x="0" y="0" width="{L}" height="{A}" rx="10" fill="{CB["uno"]}" '
            f'stroke="{CB["uno_esc"]}" stroke-width="1.5"/>')
    # conector USB e jack de energia
    s.write(f'<rect x="-16" y="30" width="62" height="52" rx="4" fill="{CB["metal"]}" '
            f'stroke="{CB["metal_esc"]}"/>')
    s.write(f'<rect x="-14" y="176" width="54" height="46" rx="6" fill="{CB["preto"]}"/>')
    # chip principal
    s.write(f'<rect x="150" y="150" width="150" height="46" rx="3" fill="{CB["preto"]}"/>')
    s.write(txt(225, 178, "ATmega328P", 10, "#8B8B90", "500"))
    s.write(txt(300, 128, "ARDUINO  UNO", 15, "#EAF6F8", "700"))

    def header(pinos, x_ini, y, para_cima):
        out = io.StringIO()
        larg = len(pinos) * 22 + 8
        out.write(f'<rect x="{x_ini - 4}" y="{y - 11}" width="{larg}" height="22" rx="3" '
                  f'fill="{CB["header"]}"/>')
        for i, p in enumerate(pinos):
            px = x_ini + 11 + i * 22
            out.write(f'<rect x="{px - 6}" y="{y - 8}" width="12" height="16" rx="1.5" '
                      f'fill="#3A3A3E"/>')
            cor = usados.get(p)
            if cor:
                out.write(f'<circle cx="{px}" cy="{y}" r="7.5" fill="{cor}" '
                          f'stroke="#fff" stroke-width="1.4"/>')
            ry = y - 18 if para_cima else y + 26
            # "AREF", "RESET" e afins nao cabem no passo de 22px do header
            tam = 10.5 if len(p) <= 2 else 8.6
            out.write(txt(px, ry, p, tam, "#EAF6F8" if cor else "#9FD3DA",
                          "700" if cor else "500"))
        return out.getvalue()

    # header digital, em cima. Na placa real o grupo AREF/GND/13..8 fica a
    # esquerda e o 7..0 a direita, com uma folga entre os dois.
    s.write(header(DIGITAIS, 26, 22, True))
    s.write(header(DIGITAIS2, 222, 22, True))
    # header de energia e analogico, embaixo
    s.write(header(PODER, 60, 246, False))
    s.write(header(ANALOG, 250, 246, False))
    s.write('</g>')
    return s.getvalue()


def pino_uno(ox, oy, rotulo):
    """Coordenada absoluta do pino, para as pontas dos fios."""
    for pinos, x_ini, y in ((DIGITAIS, 26, 22), (DIGITAIS2, 222, 22),
                            (PODER, 60, 246), (ANALOG, 250, 246)):
        if rotulo in pinos:
            i = pinos.index(rotulo)
            return ox + x_ini + 11 + i * 22, oy + y
    raise KeyError(rotulo)


# --------------------------------------------------------------- as pecas
def led(col_a, col_k, linha, cor, nome):
    """Anodo na coluna col_a, catodo na col_k, ambos na mesma linha."""
    escuro, claro = LED_COR[cor]
    xa, xk, y = cx(col_a), cx(col_k), cy(linha)
    meio = (xa + xk) / 2
    s = io.StringIO()
    s.write(f'<path d="M{xa} {y} V{y - 24} M{xk} {y} V{y - 18}" stroke="{CB["metal_esc"]}" '
            f'stroke-width="2.4" fill="none"/>')
    s.write(f'<path d="M{meio - 13} {y - 30} a13 13 0 0 1 26 0 v14 h-26 z" fill="{escuro}"/>')
    s.write(f'<ellipse cx="{meio - 4}" cy="{y - 36}" rx="4" ry="6" fill="{claro}" '
            f'fill-opacity="0.75"/>')
    s.write(f'<rect x="{meio - 15}" y="{y - 17}" width="30" height="5" rx="2.5" fill="{escuro}" '
            f'fill-opacity="0.8"/>')
    s.write(rotulo_peca(meio, y - 48, nome))
    return s.getvalue()


def resistor(col1, col2, linha):
    x1, x2, y = cx(col1), cx(col2), cy(linha)
    meio, larg = (x1 + x2) / 2, 34
    s = io.StringIO()
    s.write(f'<path d="M{x1} {y} H{x2}" stroke="{CB["metal_esc"]}" stroke-width="2.4"/>')
    s.write(f'<rect x="{meio - larg / 2}" y="{y - 9}" width="{larg}" height="18" rx="7" '
            f'fill="{CB["resistor"]}" stroke="{CB["resist_b"]}"/>')
    for i, c in enumerate(FAIXAS_220):
        bx = meio - larg / 2 + 6 + i * 6.5
        s.write(f'<rect x="{bx}" y="{y - 9}" width="3.2" height="18" fill="{c}"/>')
    return s.getvalue()


def botao(col_esq, col_dir):
    """Chave tactil atravessando o canal central, pernas em f e e."""
    x1, x2 = cx(col_esq), cx(col_dir)
    y1, y2 = cy("f"), cy("e")
    s = io.StringIO()
    for x in (x1, x2):
        s.write(f'<path d="M{x} {y1} V{y2}" stroke="{CB["metal_esc"]}" stroke-width="2.4"/>')
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    s.write(f'<rect x="{mx - 24}" y="{my - 22}" width="48" height="44" rx="4" '
            f'fill="{CB["preto"]}" stroke="#3C3C40"/>')
    s.write(f'<circle cx="{mx}" cy="{my}" r="12" fill="{CB["metal"]}" stroke="{CB["metal_esc"]}"/>')
    s.write(f'<circle cx="{mx}" cy="{my}" r="6" fill="{CB["metal_esc"]}" fill-opacity="0.5"/>')
    return s.getvalue()


def potenciometro(col1, linha, nome):
    """Tres pernas em colunas seguidas, a partir de col1."""
    x, y = cx(col1 + 1), cy(linha)
    s = io.StringIO()
    for i in range(3):
        s.write(f'<path d="M{cx(col1 + i)} {y} V{y - 26}" stroke="{CB["metal_esc"]}" '
                f'stroke-width="2.4"/>')
    s.write(f'<rect x="{x - 30}" y="{y - 66}" width="60" height="42" rx="5" fill="{CB["pot"]}" '
            f'stroke="#1F55A8"/>')
    s.write(f'<circle cx="{x}" cy="{y - 45}" r="15" fill="{CB["metal"]}" stroke="{CB["metal_esc"]}"/>')
    s.write(f'<path d="M{x} {y - 45} L{x - 9} {y - 54}" stroke="{CB["preto"]}" stroke-width="3" '
            f'stroke-linecap="round"/>')
    s.write(rotulo_peca(x, y + 32, nome))
    return s.getvalue()


def piezo(col1, col2, linha):
    x1, x2, y = cx(col1), cx(col2), cy(linha)
    mx = (x1 + x2) / 2
    s = io.StringIO()
    for x in (x1, x2):
        s.write(f'<path d="M{x} {y} V{y - 30}" stroke="{CB["metal_esc"]}" stroke-width="2.4"/>')
    s.write(f'<circle cx="{mx}" cy="{y - 48}" r="26" fill="{CB["preto"]}" stroke="#3C3C40"/>')
    s.write(f'<circle cx="{mx}" cy="{y - 48}" r="9" fill="#3C3C40"/>')
    s.write(rotulo_peca(mx, y - 78, "piezo"))
    return s.getvalue()


def lcd16x2(ox, oy, texto1, texto2):
    """Display com os 16 pinos na borda de baixo. Devolve (svg, x do pino 1)."""
    L, A = 480, 150
    s = io.StringIO()
    s.write(f'<g transform="translate({ox},{oy})">')
    s.write(f'<rect x="0" y="0" width="{L}" height="{A}" rx="6" fill="{CB["pcb"]}" '
            f'stroke="#155C2D"/>')
    s.write(f'<rect x="30" y="26" width="{L - 60}" height="86" rx="4" fill="{CB["tela"]}"/>')
    for i, t in enumerate((texto1, texto2)):
        s.write(f'<text x="46" y="{62 + i * 32}" font-family="{MONO}" font-size="20" '
                f'font-weight="500" fill="{CB["tela_txt"]}" letter-spacing="0.2em">{esc(t)}</text>')
    s.write(f'<rect x="20" y="{A - 14}" width="{16 * 22 + 8}" height="18" rx="3" '
            f'fill="{CB["header"]}"/>')
    for i in range(16):
        px = 31 + i * 22
        s.write(f'<rect x="{px - 5}" y="{A - 11}" width="10" height="12" rx="1.5" fill="#3A3A3E"/>')
        s.write(txt(px, A + 22, str(i + 1), 10, "#BFE0C8", "600"))
    s.write('</g>')
    return s.getvalue(), ox + 31


def fio(x1, y1, x2, y2, cor, curva=0.45):
    """Fio com barriga, como os do Tinkercad."""
    dx, dy = x2 - x1, y2 - y1
    mx, my = x1 + dx / 2, y1 + dy / 2
    nx, ny = -dy, dx
    n = (nx * nx + ny * ny) ** 0.5 or 1
    off = min(70, abs(dx) * curva + abs(dy) * 0.12)
    px, py = mx + nx / n * off * 0.35, my + ny / n * off * 0.35
    return (f'<path d="M{x1:.1f} {y1:.1f} Q{px:.1f} {py:.1f} {x2:.1f} {y2:.1f}" '
            f'stroke="{cor}" stroke-width="3.4" fill="none" stroke-linecap="round" '
            f'stroke-opacity="0.95"/>'
            f'<circle cx="{x1:.1f}" cy="{y1:.1f}" r="3.4" fill="{cor}"/>'
            f'<circle cx="{x2:.1f}" cy="{y2:.1f}" r="3.4" fill="{cor}"/>')


def fio_faixa(x1, y1, x2, y2, faixa, cor):
    """
    Fio em angulo reto, descendo ate a sua faixa, correndo na horizontal e
    descendo de novo. Seis fios em curva entre dois headers viram um no no
    meio; com uma faixa por fio, os cruzamentos ficam em angulo reto e da
    para seguir cada um com o dedo.
    """
    return (f'<path d="M{x1:.1f} {y1:.1f} V{faixa:.1f} H{x2:.1f} V{y2:.1f}" '
            f'stroke="{cor}" stroke-width="3.2" fill="none" stroke-linejoin="round" '
            f'stroke-linecap="round"/>'
            f'<circle cx="{x1:.1f}" cy="{y1:.1f}" r="3.4" fill="{cor}"/>'
            f'<circle cx="{x2:.1f}" cy="{y2:.1f}" r="3.4" fill="{cor}"/>')


def moldura(largura, altura, ident, titulo, corpo):
    return (f'<svg viewBox="0 0 {largura} {altura}" xmlns="http://www.w3.org/2000/svg" '
            f'role="img" aria-labelledby="{ident}-t">'
            f'<title id="{ident}-t">{esc(titulo)}</title>{corpo}</svg>')


# =========================================================== transmissor
def diagrama_tx():
    """
    Cada peca ocupa colunas proprias. Vale lembrar que as metades de cima
    (f a j) e de baixo (a a e) sao separadas pelo canal central, entao a
    mesma coluna nos dois lados sao dois nos diferentes.
    """
    UX, UY = 200, 560
    usados = {"2": "#5AA9F0", "3": LED_COR["verde"][0], "4": "#E08A2E",
              "5": LED_COR["verde"][0], "6": LED_COR["azul"][0],
              "12": "#C48FE0", "A0": "#F0C020",
              "5V": CB["trilha_p"], "GND": CB["trilha_m"]}
    s = io.StringIO()
    s.write(protoboard())

    s.write(botao(7, 9))                              # manipulador
    s.write(piezo(12, 14, "h"))                       # sidetone
    s.write(potenciometro(24, "h", "velocidade"))     # A0
    for col_r, cor, nome in ((12, "verde", "ponto"), (18, "verde", "traço"),
                             (24, "azul", "espaço")):
        s.write(resistor(col_r, col_r + 2, "b"))
        s.write(led(col_r + 2, col_r + 4, "d", cor, nome))

    s.write(arduino_uno(UX, UY, usados))

    fios = []
    # sinais que saem da placa
    for pino, col, linha, cor in (("2", 7, "f", "#5AA9F0"),
                                  ("4", 12, "j", "#E08A2E"),
                                  ("3", 12, "a", LED_COR["verde"][0]),
                                  ("5", 18, "a", LED_COR["verde"][0]),
                                  ("6", 24, "a", LED_COR["azul"][0]),
                                  ("A0", 25, "j", "#F0C020")):
        px, py = pino_uno(UX, UY, pino)
        fios.append(fio(px, py, cx(col), cy(linha), cor))
    # alimentacao da protoboard
    px, py = pino_uno(UX, UY, "5V")
    fios.append(fio(px, py, cx(2), cy("+b"), CB["trilha_p"]))
    px, py = pino_uno(UX, UY, "GND")
    fios.append(fio(px, py, cx(4), cy("-b"), CB["trilha_m"]))
    # as trilhas de cima repetem as de baixo
    fios.append(fio(cx(2), cy("+b"), cx(2), cy("+t"), CB["trilha_p"], 0.04))
    fios.append(fio(cx(4), cy("-b"), cx(4), cy("-t"), CB["trilha_m"], 0.04))
    # terra de cada peca ate a trilha mais perto
    for co, lo, cd, ld in ((9, "e", 10, "-b"),      # chave
                           (16, "b", 16, "-b"),     # LED verde
                           (22, "b", 22, "-b"),     # LED verde 2
                           (28, "b", 28, "-b"),     # LED azul
                           (14, "j", 15, "-t"),     # piezo
                           (24, "j", 23, "-t")):    # potenciometro
        fios.append(fio(cx(co), cy(lo), cx(cd), cy(ld), CB["trilha_m"], 0.05))
    fios.append(fio(cx(26), cy("j"), cx(27), cy("+t"), CB["trilha_p"], 0.05))

    s.write("".join(fios))
    return moldura(PLACA_X + PLACA_L + 40, UY + 330, "tk-tx",
                   "Montagem do transmissor no Tinkercad", s.getvalue())


# ============================================================== receptor
def diagrama_rx():
    """O LCD vai direto nos pinos da placa; so o contraste, a luz de fundo,
    o LED e a chave passam pela protoboard."""
    LX, LY = 200, 500
    UX, UY = 200, 790
    azul = "#5AA9F0"
    usados = {"2": azul, "3": azul, "4": azul, "5": azul, "6": azul, "7": azul,
              "8": LED_COR["vermelho"][0], "9": "#7FD8A8", "11": "#C48FE0",
              "5V": CB["trilha_p"], "GND": CB["trilha_m"]}
    s = io.StringIO()
    s.write(protoboard())
    s.write(botao(7, 9))                              # limpar tela
    s.write(resistor(13, 15, "b"))
    s.write(led(15, 17, "d", "vermelho", "recebendo"))
    s.write(resistor(21, 23, "b"))                    # luz de fundo
    s.write(rotulo_peca(cx(22), cy("c") - 6, "luz de fundo"))
    s.write(potenciometro(25, "h", "contraste"))

    lcd_svg, p1 = lcd16x2(LX, LY, "·−··  L", "CHAMANDO_")
    s.write(lcd_svg)
    s.write(arduino_uno(UX, UY, usados))

    lcd_y = LY + 150
    def lcd_pino(n):
        return p1 + (n - 1) * 22, lcd_y

    fios = []
    # os seis pinos de dados e controle vao direto na placa, um por faixa
    dados = ((4, "2"), (6, "3"), (11, "4"), (12, "5"), (13, "6"), (14, "7"))
    for i, (n, pino) in enumerate(dados):
        lx, ly = lcd_pino(n)
        px, py = pino_uno(UX, UY, pino)
        fios.append(fio_faixa(lx, ly, px, py, ly + 42 + i * 21, azul))
    # alimentacao e terra do display: cada pino no furo de trilha mais perto,
    # em vez de um fio atravessando o desenho inteiro
    for n, col, linha, cor in ((1, 5, "-b", CB["trilha_m"]), (2, 3, "+b", CB["trilha_p"]),
                               (5, 11, "-b", CB["trilha_m"]), (16, 29, "-b", CB["trilha_m"])):
        lx, ly = lcd_pino(n)
        fios.append(fio(lx, ly, cx(col), cy(linha), cor, 0.12))
    # contraste e luz de fundo
    lx, ly = lcd_pino(3)
    fios.append(fio(cx(26), cy("j"), lx, ly, "#F0C020", 0.12))
    lx, ly = lcd_pino(15)
    fios.append(fio(lx, ly, cx(21), cy("a"), CB["trilha_p"], 0.12))
    fios.append(fio(cx(23), cy("b"), cx(23), cy("+b"), CB["trilha_p"], 0.05))

    for pino, col, linha, cor in (("8", 13, "a", LED_COR["vermelho"][0]),
                                  ("9", 7, "f", "#7FD8A8")):
        px, py = pino_uno(UX, UY, pino)
        fios.append(fio(px, py, cx(col), cy(linha), cor))
    px, py = pino_uno(UX, UY, "5V")
    fios.append(fio(px, py, cx(2), cy("+b"), CB["trilha_p"]))
    px, py = pino_uno(UX, UY, "GND")
    fios.append(fio(px, py, cx(4), cy("-b"), CB["trilha_m"]))
    fios.append(fio(cx(2), cy("+b"), cx(2), cy("+t"), CB["trilha_p"], 0.04))
    fios.append(fio(cx(4), cy("-b"), cx(4), cy("-t"), CB["trilha_m"], 0.04))
    for co, lo, cd, ld in ((9, "e", 10, "-b"),      # chave
                           (17, "b", 17, "-b"),     # LED
                           (25, "j", 24, "-t")):    # potenciometro
        fios.append(fio(cx(co), cy(lo), cx(cd), cy(ld), CB["trilha_m"], 0.05))
    fios.append(fio(cx(27), cy("j"), cx(28), cy("+t"), CB["trilha_p"], 0.05))

    s.write("".join(fios))
    return moldura(PLACA_X + PLACA_L + 40, UY + 330, "tk-rx",
                   "Montagem do receptor no Tinkercad", s.getvalue())


# ======================================================= o fio entre elas
def diagrama_link():
    W, H = 900, 360
    s = io.StringIO()
    a = arduino_uno(20, 40, {"12": "#C48FE0", "GND": CB["trilha_m"]})
    b = arduino_uno(20, 40, {"11": "#C48FE0", "GND": CB["trilha_m"]})
    s.write(f'<g transform="translate(0,0) scale(0.62)">{a}</g>')
    s.write(f'<g transform="translate(560,0) scale(0.62)">{b}</g>')
    p1 = pino_uno(20, 40, "12")
    p2 = pino_uno(20, 40, "11")
    g1 = pino_uno(20, 40, "GND")
    ax, ay = p1[0] * 0.62, p1[1] * 0.62
    bx, by = 560 + p2[0] * 0.62, p2[1] * 0.62
    agx, agy = g1[0] * 0.62, g1[1] * 0.62
    bgx, bgy = 560 + g1[0] * 0.62, g1[1] * 0.62
    s.write(fio(ax, ay, bx, by, "#C48FE0", 0.16))
    s.write(fio(agx, agy, bgx, bgy, CB["trilha_m"], 0.1))
    s.write(txt((ax + bx) / 2, 26, "D12  →  D11     o fio que substitui o rádio",
                13, "#C48FE0", "700"))
    s.write(txt((agx + bgx) / 2, 250, "GND  —  GND     terra em comum, sem ele nada funciona",
                13, CB["fraco"], "600"))
    s.write(txt(ax, 300, "transmissor", 13, CB["texto"], "700"))
    s.write(txt(bx, 300, "receptor", 13, CB["texto"], "700"))
    return moldura(W, H, "tk-link", "O fio entre as duas placas", s.getvalue())


# ========================================================== a prateleira
def galeria():
    """As pecas do jeito que aparecem no painel do Tinkercad."""
    itens = [
        ("Arduino Uno R3", "2", "placa"),
        ("Placa de ensaio pequena", "2", "protoboard"),
        ("LED", "5", "led"),
        ("Resistor", "5", "resistor"),
        ("Botão", "2", "botao"),
        ("Potenciômetro", "2", "pot"),
        ("Piezo", "1", "piezo"),
        ("LCD 16 x 2", "1", "lcd"),
    ]
    cel, col = 178, 4
    W = cel * col + 20
    H = ((len(itens) + col - 1) // col) * (cel + 34) + 20
    s = io.StringIO()
    for i, (nome, qtd, tipo) in enumerate(itens):
        gx, gy = 10 + (i % col) * cel, 10 + (i // col) * (cel + 34)
        s.write(f'<rect x="{gx}" y="{gy}" width="{cel - 12}" height="{cel - 12}" rx="10" '
                f'fill="#F4F5F7" stroke="#D3D6DB"/>')
        s.write(f'<g transform="translate({gx + (cel - 12) / 2},{gy + (cel - 12) / 2})">')
        s.write(miniatura(tipo))
        s.write('</g>')
        s.write(txt(gx + (cel - 12) / 2, gy + cel + 4, nome, 12, CB["texto"], "600"))
        s.write(txt(gx + (cel - 12) / 2, gy + cel + 20, f"{qtd}×", 11, CB["fraco"], "500"))
    return moldura(W, H, "tk-gal", "Peças a arrastar no Tinkercad", s.getvalue())


def miniatura(tipo):
    if tipo == "placa":
        return (f'<rect x="-52" y="-34" width="104" height="68" rx="6" fill="{CB["uno"]}"/>'
                f'<rect x="-46" y="-32" width="88" height="9" rx="2" fill="{CB["header"]}"/>'
                f'<rect x="-40" y="23" width="76" height="9" rx="2" fill="{CB["header"]}"/>'
                f'<rect x="-16" y="-6" width="40" height="14" rx="2" fill="{CB["preto"]}"/>'
                f'<rect x="-60" y="-22" width="18" height="16" rx="2" fill="{CB["metal"]}"/>')
    if tipo == "protoboard":
        p = ''.join(f'<rect x="{-48 + c * 8}" y="{-30 + r * 9}" width="4" height="4" rx="1" '
                    f'fill="{CB["furo"]}" fill-opacity="0.75"/>'
                    for c in range(13) for r in range(7))
        return (f'<rect x="-56" y="-38" width="112" height="76" rx="5" fill="{CB["placa"]}" '
                f'stroke="{CB["placa_b"]}"/>{p}')
    if tipo == "led":
        return ('<path d="M-7 34 V6 M7 34 V12" stroke="#8A9098" stroke-width="3"/>'
                '<path d="M-19 -6 a19 19 0 0 1 38 0 v20 h-38 z" fill="#E23B2E"/>'
                '<ellipse cx="-6" cy="-12" rx="5" ry="8" fill="#FF8A7A" fill-opacity="0.8"/>')
    if tipo == "resistor":
        b = ''.join(f'<rect x="{-19 + i * 9}" y="-11" width="4.5" height="22" fill="{c}"/>'
                    for i, c in enumerate(FAIXAS_220))
        return (f'<path d="M-48 0 H48" stroke="#8A9098" stroke-width="3"/>'
                f'<rect x="-26" y="-11" width="52" height="22" rx="9" fill="{CB["resistor"]}" '
                f'stroke="{CB["resist_b"]}"/>{b}')
    if tipo == "botao":
        return (f'<rect x="-30" y="-30" width="60" height="60" rx="5" fill="{CB["preto"]}"/>'
                f'<circle cx="0" cy="0" r="16" fill="{CB["metal"]}" stroke="{CB["metal_esc"]}"/>'
                f'<path d="M-30 -22 h-12 M30 -22 h12 M-30 22 h-12 M30 22 h12" '
                f'stroke="{CB["metal_esc"]}" stroke-width="4"/>')
    if tipo == "pot":
        return (f'<rect x="-34" y="-24" width="68" height="46" rx="6" fill="{CB["pot"]}"/>'
                f'<circle cx="0" cy="-2" r="17" fill="{CB["metal"]}" stroke="{CB["metal_esc"]}"/>'
                f'<path d="M0 -2 L-10 -12" stroke="{CB["preto"]}" stroke-width="3.4" '
                f'stroke-linecap="round"/>'
                f'<path d="M-18 22 V38 M0 22 V38 M18 22 V38" stroke="{CB["metal_esc"]}" '
                f'stroke-width="3"/>')
    if tipo == "piezo":
        return (f'<circle cx="0" cy="-4" r="32" fill="{CB["preto"]}"/>'
                f'<circle cx="0" cy="-4" r="11" fill="#3C3C40"/>'
                f'<path d="M-10 28 V40 M10 28 V40" stroke="{CB["metal_esc"]}" stroke-width="3"/>')
    if tipo == "lcd":
        return (f'<rect x="-56" y="-34" width="112" height="64" rx="4" fill="{CB["pcb"]}"/>'
                f'<rect x="-46" y="-26" width="92" height="40" rx="3" fill="{CB["tela"]}"/>'
                f'<text x="-40" y="0" font-family="{MONO}" font-size="12" '
                f'fill="{CB["tela_txt"]}" letter-spacing="0.1em">·−·· L</text>'
                f'<rect x="-44" y="26" width="88" height="7" rx="2" fill="{CB["header"]}"/>')
    return ''


base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "diagramas")
os.makedirs(base, exist_ok=True)
for nome, conteudo in (("tk_galeria.svg", galeria()),
                       ("tk_tx.svg", diagrama_tx()),
                       ("tk_rx.svg", diagrama_rx()),
                       ("tk_link.svg", diagrama_link())):
    with open(os.path.join(base, nome), "w", encoding="utf-8", newline="\n") as f:
        f.write(conteudo)
    print(f"{nome}: {len(conteudo):,} bytes".replace(",", "."))
