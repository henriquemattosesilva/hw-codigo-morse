# Gera os diagramas de montagem do projeto hw-codigo-morse.
# Saida: dois SVGs inline, escritos em arquivos separados para colar no index.html
import io, os

C = {
    "painel":  "#0E1526",
    "borda":   "#22304E",
    "texto":   "#D6E2F2",
    "fraco":   "#7E90AC",
    "apagado": "#3A4A66",
    "lcd":     "#1554B8",
    "lcdtxt":  "#CFE6FF",
    "sinal":   "#5AA9F0",
    "ponto":   "#45D964",
    "traco":   "#FFC24B",
    "espaco":  "#48B8F5",
    "rx":      "#FF5B52",
    "mais":    "#FF5B52",
    "menos":   "#8CA0BE",
    "placa":   "#132038",
}

MONO = "'IBM Plex Mono','SFMono-Regular',ui-monospace,monospace"


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def txt(x, y, s, tam=12, cor=None, peso="500", anc="middle"):
    return (f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anc}" font-family="{MONO}" '
            f'font-size="{tam}" font-weight="{peso}" fill="{cor or C["texto"]}"'
            f'>{esc(s)}</text>')


def chip(x, y, texto, cor, alvo="fim"):
    """Etiqueta arredondada. alvo='fim' alinha a direita terminando em x."""
    w = len(texto) * 8.6 + 20
    px = x - w if alvo == "fim" else x
    return (
        f'<rect x="{px:.1f}" y="{y}" width="{w:.1f}" height="26" rx="13" '
        f'fill="{cor}" fill-opacity="0.14" stroke="{cor}" stroke-opacity="0.55"/>'
        f'<text x="{px + w / 2:.1f}" y="{y + 17.5}" text-anchor="middle" '
        f'font-family="{MONO}" font-size="12.5" font-weight="600" fill="{cor}">{esc(texto)}</text>'
    ), w


# --------------------------------------------------------------- diagrama 1 e 2
def diagrama_placa(titulo, placa, linhas, ident,
                   trilhas=("trilha +   5V", "trilha −   GND")):
    """linhas: lista de dicts {nome, pino, cor, resistor, chips}"""
    W = 880
    topo, passo = 118, 76
    n = len(linhas)
    y_rail_mais = 52
    y_rail_menos = topo + passo * (n - 1) + 62
    H = y_rail_menos + 40

    bx, bw = 32, 152
    by, bh = topo - 44, passo * (n - 1) + 88

    s = io.StringIO()
    s.write(
        f'<svg viewBox="0 0 {W} {H}" role="img" xmlns="http://www.w3.org/2000/svg" '
        f'aria-labelledby="{ident}-t"><title id="{ident}-t">{esc(titulo)}</title>'
    )

    # trilhas de alimentacao da protoboard
    for y, cor, rot in ((y_rail_mais, C["mais"], trilhas[0]),
                        (y_rail_menos, C["menos"], trilhas[1])):
        s.write(
            f'<rect x="32" y="{y - 9}" width="{W - 64}" height="18" rx="9" '
            f'fill="{cor}" fill-opacity="0.12" stroke="{cor}" stroke-opacity="0.4"/>'
            f'<text x="48" y="{y + 5}" font-family="{MONO}" font-size="12.5" '
            f'font-weight="600" fill="{cor}" letter-spacing="0.06em">{esc(rot)}</text>'
        )

    # a placa
    s.write(
        f'<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" rx="10" '
        f'fill="{C["placa"]}" stroke="{C["borda"]}"/>'
        f'<text x="{bx + bw / 2}" y="{by + 26}" text-anchor="middle" font-family="{MONO}" '
        f'font-size="13" font-weight="700" fill="{C["texto"]}" letter-spacing="0.08em">{esc(placa)}</text>'
    )

    for i, ln in enumerate(linhas):
        y = topo + i * passo
        cor = ln["cor"]
        lp = max(46, len(ln["pino"]) * 8.4 + 14)
        # perna do pino, saindo da placa
        s.write(
            f'<rect x="{bx + bw}" y="{y - 11}" width="{lp}" height="22" rx="5" '
            f'fill="{cor}" fill-opacity="0.16" stroke="{cor}" stroke-opacity="0.5"/>'
            f'<text x="{bx + bw + lp / 2}" y="{y + 5}" text-anchor="middle" font-family="{MONO}" '
            f'font-size="12.5" font-weight="700" fill="{cor}">{esc(ln["pino"])}</text>'
        )
        # fio ate o componente
        x0, x1 = bx + bw + lp, 380
        s.write(f'<path d="M{x0} {y} H{x1}" stroke="{cor}" stroke-width="2.2" '
                f'stroke-opacity="0.75" fill="none"/>')
        if ln.get("resistor"):
            rx, rw = (x0 + x1) / 2 - 34, 68
            s.write(
                f'<rect x="{rx}" y="{y - 13}" width="{rw}" height="26" rx="4" '
                f'fill="{C["painel"]}" stroke="{cor}" stroke-opacity="0.75" stroke-width="1.5"/>'
                f'<text x="{rx + rw / 2}" y="{y + 5}" text-anchor="middle" font-family="{MONO}" '
                f'font-size="12" font-weight="600" fill="{cor}">{esc(ln["resistor"])}</text>'
            )
        # cartao do componente
        cx, cw = x1, W - 32 - x1
        s.write(
            f'<rect x="{cx}" y="{y - 28}" width="{cw}" height="56" rx="8" '
            f'fill="{C["painel"]}" stroke="{C["borda"]}"/>'
            f'<text x="{cx + 16}" y="{y + 5}" font-family="{MONO}" font-size="13.5" '
            f'font-weight="600" fill="{C["texto"]}">{esc(ln["nome"])}</text>'
        )
        # etiquetas de alimentacao, alinhadas a direita
        fim = cx + cw - 14
        for txt, ccor in reversed(ln["chips"]):
            marca, w = chip(fim, y - 13, txt, ccor)
            s.write(marca)
            fim -= w + 8

    s.write("</svg>")
    return s.getvalue()


tx = diagrama_placa(
    "Ligacoes do transmissor", "ARDUINO NANO", [
        {"nome": "Chave táctil — manipulador", "pino": "D2", "cor": C["sinal"],
         "chips": [("GND", C["menos"])]},
        {"nome": "LED verde 1 — ponto", "pino": "D3", "cor": C["ponto"],
         "resistor": "220 Ω", "chips": [("GND", C["menos"])]},
        {"nome": "Buzzer ativo — 2 pinos", "pino": "D4", "cor": C["sinal"],
         "chips": [("GND", C["menos"])]},
        {"nome": "LED verde 2 — traço", "pino": "D5", "cor": C["ponto"],
         "resistor": "220 Ω", "chips": [("GND", C["menos"])]},
        {"nome": "LED azul — espaço", "pino": "D6", "cor": C["espaco"],
         "resistor": "220 Ω", "chips": [("GND", C["menos"])]},
        {"nome": "Módulo TX 433 MHz", "pino": "D12", "cor": C["sinal"],
         "chips": [("5V", C["mais"]), ("GND", C["menos"]), ("ANT 17,3 cm", C["fraco"])]},
        {"nome": "Potenciômetro 10K — velocidade", "pino": "A0", "cor": C["traco"],
         "chips": [("5V", C["mais"]), ("GND", C["menos"])]},
    ], "dtx")

rx = diagrama_placa(
    "Ligacoes do receptor", "ARDUINO UNO", [
        {"nome": "LCD 16x2 — RS, E, D4 a D7", "pino": "D2–D7", "cor": C["lcd"],
         "chips": [("ver diagrama do LCD", C["fraco"])]},
        {"nome": "LED vermelho — recebendo", "pino": "D8", "cor": C["rx"],
         "resistor": "220 Ω", "chips": [("GND", C["menos"])]},
        {"nome": "Chave táctil — limpar tela", "pino": "D9", "cor": C["sinal"],
         "chips": [("GND", C["menos"])]},
        {"nome": "Módulo RX 433 MHz", "pino": "D11", "cor": C["sinal"],
         "chips": [("5V", C["mais"]), ("GND", C["menos"]), ("ANT 17,3 cm", C["fraco"])]},
        {"nome": "Potenciômetro 10K — contraste", "pino": "LCD 3", "cor": C["traco"],
         "chips": [("5V", C["mais"]), ("GND", C["menos"])]},
    ], "drx")

NOTA_LCD_UNO = ("* o pino 15 vai ao 5V através de um resistor de 220 Ω. "
                "Os pinos 7 a 10 ficam sem ligação.")
NOTA_LCD_ESP = ("* o pino 15 vai ao VU através de um resistor de 220 Ω. VU é o 5V da USB, "
                "não o 3V3: o LCD não enxerga 3,3 V como nível alto. Pinos 7 a 10 sem ligação.")

# ------------------------------------------------------------ diagrama do LCD
DESTINOS_UNO = [
    ("1", "VSS", "GND", C["menos"]), ("2", "VDD", "5V", C["mais"]),
    ("3", "V0", "POT", C["traco"]), ("4", "RS", "D2", C["lcd"]),
    ("5", "RW", "GND", C["menos"]), ("6", "E", "D3", C["lcd"]),
    ("7", "D0", "", None), ("8", "D1", "", None),
    ("9", "D2", "", None), ("10", "D3", "", None),
    ("11", "D4", "D4", C["lcd"]), ("12", "D5", "D5", C["lcd"]),
    ("13", "D6", "D6", C["lcd"]), ("14", "D7", "D7", C["lcd"]),
    ("15", "A", "5V *", C["mais"]), ("16", "K", "GND", C["menos"]),
]

DESTINOS_ESP = [
    ("1", "VSS", "G", C["menos"]),   ("2", "VDD", "VU", C["mais"]),
    ("3", "V0", "POT", C["traco"]),  ("4", "RS", "D8", C["lcd"]),
    ("5", "RW", "G", C["menos"]),    ("6", "E", "D3", C["lcd"]),
    ("7", "D0", "", None),           ("8", "D1", "", None),
    ("9", "D2", "", None),           ("10", "D3", "", None),
    ("11", "D4", "D4", C["lcd"]),    ("12", "D5", "D5", C["lcd"]),
    ("13", "D6", "D6", C["lcd"]),    ("14", "D7", "D7", C["lcd"]),
    ("15", "A", "VU *", C["mais"]),  ("16", "K", "G", C["menos"]),
]


def diagrama_lcd(pinos=None, ident="dlcd", nota=None):
    pinos = pinos or DESTINOS_UNO
    col, x0 = 57, 46
    W, H = x0 * 2 + col * 16, 302
    s = io.StringIO()
    s.write(f'<svg viewBox="0 0 {W} {H}" role="img" xmlns="http://www.w3.org/2000/svg" '
            f'aria-labelledby="{ident}-t"><title id="{ident}-t">Pinos do LCD 16x2</title>')
    # corpo do display, com duas linhas de celulas
    s.write(f'<rect x="{x0}" y="18" width="{col * 16}" height="92" rx="8" '
            f'fill="{C["lcd"]}" fill-opacity="0.9"/>')
    for linha, txt in enumerate(["·−··  L", "CHAMANDO_"]):
        s.write(f'<text x="{x0 + 18}" y="{54 + linha * 30}" font-family="{MONO}" '
                f'font-size="19" font-weight="500" fill="{C["lcdtxt"]}" '
                f'letter-spacing="0.22em">{esc(txt)}</text>')
    for i, (num, nome, dest, cor) in enumerate(pinos):
        cx = x0 + col * i + col / 2
        ativo = cor is not None
        c = cor if ativo else C["apagado"]
        s.write(f'<rect x="{cx - 5}" y="110" width="10" height="16" rx="2" fill="{c}" '
                f'fill-opacity="{"0.9" if ativo else "0.4"}"/>')
        s.write(f'<text x="{cx}" y="146" text-anchor="middle" font-family="{MONO}" '
                f'font-size="12" font-weight="700" fill="{C["fraco"]}">{esc(num)}</text>')
        s.write(f'<text x="{cx}" y="166" text-anchor="middle" font-family="{MONO}" '
                f'font-size="12.5" font-weight="600" '
                f'fill="{C["texto"] if ativo else C["apagado"]}">{esc(nome)}</text>')
        if ativo:
            s.write(f'<path d="M{cx} 178 V218" stroke="{c}" stroke-width="2.2" '
                    f'stroke-opacity="0.7"/>')
            marca, _ = chip(cx, 220, dest, c, alvo="centro")
            # chip() com alvo centro devolve alinhado a esquerda; recentraliza
            w = len(dest) * 8.6 + 20
            marca, _ = chip(cx + w / 2, 220, dest, c)
            s.write(marca)
        else:
            s.write(f'<text x="{cx}" y="228" text-anchor="middle" font-family="{MONO}" '
                    f'font-size="15" fill="{C["apagado"]}">—</text>')
    s.write(f'<text x="{x0}" y="278" font-family="{MONO}" font-size="12.5" '
            f'fill="{C["fraco"]}">{esc(nota or NOTA_LCD_UNO)}</text>')
    s.write("</svg>")
    return s.getvalue()


# ================================================= receptor com ESP8266
esp = diagrama_placa(
    "Ligacoes do receptor com ESP8266", "NODEMCU  ESP8266", [
        {"nome": "LCD 16x2 — RS, E, D4 a D7", "pino": "D8,D3–D7", "cor": C["lcd"],
         "chips": [("ver diagrama do LCD", C["fraco"])]},
        {"nome": "Módulo RX 433 MHz", "pino": "D2", "cor": C["sinal"],
         "chips": [("DIVISOR 10k+20k", C["rx"]), ("VU", C["mais"]), ("G", C["menos"])]},
        {"nome": "LED vermelho — recebendo", "pino": "D0", "cor": C["rx"],
         "resistor": "220 Ω", "chips": [("G", C["menos"])]},
        {"nome": "Chave táctil — limpar tela", "pino": "D1", "cor": C["sinal"],
         "chips": [("G", C["menos"])]},
        {"nome": "Potenciômetro 10K — contraste", "pino": "LCD 3", "cor": C["traco"],
         "chips": [("VU", C["mais"]), ("G", C["menos"])]},
    ], "desp", ("trilha +   5V, tirada do VU", "trilha −   GND"))


# ============================== o divisor entre o rádio de 5V e o ESP de 3,3V
def diagrama_divisor():
    """
    A peça que não pode ser esquecida: a saída DATA do receptor entrega 5 V
    num pino que só tolera 3,3 V.
    """
    W, H = 780, 420
    x = 250
    s = io.StringIO()
    s.write(f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" '
            f'aria-labelledby="ddiv-t"><title id="ddiv-t">Divisor de tensão entre o '
            f'receptor de 433 MHz e o ESP8266</title>')

    def caixa(cx_, cy_, larg, rot, sub, cor):
        return (f'<rect x="{cx_ - larg / 2}" y="{cy_ - 26}" width="{larg}" height="52" rx="9" '
                f'fill="{C["painel"]}" stroke="{cor}" stroke-opacity="0.7"/>'
                + txt(cx_, cy_ - 3, rot, 13.5, C["texto"], "700")
                + txt(cx_, cy_ + 15, sub, 11.5, cor, "600"))

    def resistor(cy_, valor):
        faixas = ["#8B4A16", "#1A1A1A", "#E08A2E", "#D4AF37"]  # marrom preto laranja ouro
        out = (f'<rect x="{x - 15}" y="{cy_ - 26}" width="30" height="52" rx="7" '
               f'fill="#D9BD8F" stroke="#B99B6D"/>')
        for i, c in enumerate(faixas):
            out += f'<rect x="{x - 15}" y="{cy_ - 19 + i * 10}" width="30" height="4.5" fill="{c}"/>'
        return out + txt(x + 34, cy_ + 5, valor, 13, C["texto"], "700", "start")

    s.write(f'<path d="M{x} 74 V346" stroke="{C["sinal"]}" stroke-width="2.6" fill="none"/>')
    s.write(caixa(x, 48, 300, "DATA do receptor 433 MHz", "5 V — não pode ir direto", C["rx"]))
    s.write(resistor(130, "10 kΩ"))
    s.write(resistor(238, "10 kΩ"))
    s.write(resistor(310, "10 kΩ"))
    s.write(txt(x + 150, 279, "os dois em série somam 20 kΩ", 11.5,
                C["fraco"], "500", "start"))

    # a derivação para o ESP, no meio do divisor
    s.write(f'<path d="M{x} 186 H{x + 210}" stroke="{C["ponto"]}" stroke-width="2.6"/>')
    s.write(f'<circle cx="{x}" cy="186" r="5.5" fill="{C["ponto"]}"/>')
    s.write(caixa(x + 340, 186, 250, "D2 do ESP8266", "3,33 V — dentro do limite", C["ponto"]))

    # terra
    for i, larg in enumerate((46, 30, 15)):
        s.write(f'<path d="M{x - larg / 2} {350 + i * 8} H{x + larg / 2}" '
                f'stroke="{C["menos"]}" stroke-width="3"/>')
    s.write(txt(x + 34, 366, "G do ESP", 12, C["menos"], "600", "start"))

    s.write(txt(30, 400, "5 V × 20 kΩ ÷ (10 kΩ + 20 kΩ) = 3,33 V", 13, C["fraco"], "600", "start"))
    s.write("</svg>")
    return s.getvalue()


base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "diagramas")
for nome, conteudo in (("svg_tx.svg", tx), ("svg_rx.svg", rx),
                       ("svg_lcd.svg", diagrama_lcd()),
                       ("svg_esp.svg", esp),
                       ("svg_lcd_esp.svg", diagrama_lcd(DESTINOS_ESP, "dlcdesp", NOTA_LCD_ESP)),
                       ("svg_divisor.svg", diagrama_divisor())):
    with open(os.path.join(base, nome), "w", encoding="utf-8") as f:
        f.write(conteudo)
    print(f"{nome}: {len(conteudo)} bytes")
