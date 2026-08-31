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
def diagrama_placa(titulo, placa, linhas, ident):
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
    for y, cor, rot in ((y_rail_mais, C["mais"], "trilha +   5V"),
                        (y_rail_menos, C["menos"], "trilha −   GND")):
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
        # perna do pino, saindo da placa
        s.write(
            f'<rect x="{bx + bw}" y="{y - 11}" width="46" height="22" rx="5" '
            f'fill="{cor}" fill-opacity="0.16" stroke="{cor}" stroke-opacity="0.5"/>'
            f'<text x="{bx + bw + 23}" y="{y + 5}" text-anchor="middle" font-family="{MONO}" '
            f'font-size="12.5" font-weight="700" fill="{cor}">{esc(ln["pino"])}</text>'
        )
        # fio ate o componente
        x0, x1 = bx + bw + 46, 380
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
        {"nome": "LED verde — ponto", "pino": "D3", "cor": C["ponto"],
         "resistor": "220 Ω", "chips": [("GND", C["menos"])]},
        {"nome": "Módulo buzzer ativo", "pino": "D4", "cor": C["sinal"],
         "chips": [("5V", C["mais"]), ("GND", C["menos"])]},
        {"nome": "LED amarelo — traço", "pino": "D5", "cor": C["traco"],
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

# ------------------------------------------------------------ diagrama do LCD
def diagrama_lcd():
    pinos = [
        ("1", "VSS", "GND", C["menos"]), ("2", "VDD", "5V", C["mais"]),
        ("3", "V0", "POT", C["traco"]), ("4", "RS", "D2", C["lcd"]),
        ("5", "RW", "GND", C["menos"]), ("6", "E", "D3", C["lcd"]),
        ("7", "D0", "", None), ("8", "D1", "", None),
        ("9", "D2", "", None), ("10", "D3", "", None),
        ("11", "D4", "D4", C["lcd"]), ("12", "D5", "D5", C["lcd"]),
        ("13", "D6", "D6", C["lcd"]), ("14", "D7", "D7", C["lcd"]),
        ("15", "A", "5V *", C["mais"]), ("16", "K", "GND", C["menos"]),
    ]
    col, x0 = 57, 46
    W, H = x0 * 2 + col * 16, 302
    s = io.StringIO()
    s.write(f'<svg viewBox="0 0 {W} {H}" role="img" xmlns="http://www.w3.org/2000/svg" '
            f'aria-labelledby="dlcd-t"><title id="dlcd-t">Pinos do LCD 16x2</title>')
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
            f'fill="{C["fraco"]}">* o pino 15 vai ao 5V através de um resistor de 220 Ω. '
            f'Os pinos 7 a 10 ficam sem ligação.</text>')
    s.write("</svg>")
    return s.getvalue()


base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "diagramas")
for nome, conteudo in (("svg_tx.svg", tx), ("svg_rx.svg", rx), ("svg_lcd.svg", diagrama_lcd())):
    with open(os.path.join(base, nome), "w", encoding="utf-8") as f:
        f.write(conteudo)
    print(f"{nome}: {len(conteudo)} bytes")
