# Monta o index.html do projeto a partir de ferramentas/modelo.html, dos diagramas
# em ferramentas/diagramas e dos sketches .ino.
#
#   python ferramentas/gerar-pagina.py
#
# Rode sempre que mexer no codigo de uma das placas ou nos diagramas: o index.html
# e gerado, nao editado a mao.
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FERR = os.path.join(BASE, "ferramentas")

PECAS = {
    # A secao entra primeiro: ela mesma traz as marcas que as linhas de baixo
    # precisam substituir depois.
    "SECAO_TINKERCAD": os.path.join(FERR, "secao-tinkercad.html"),
    "SVG_TK_GAL":  os.path.join(FERR, "diagramas", "tk_galeria.svg"),
    "SVG_TK_LINK": os.path.join(FERR, "diagramas", "tk_link.svg"),
    "SVG_TK_TX":   os.path.join(FERR, "diagramas", "tk_tx.svg"),
    "SVG_TK_RX":   os.path.join(FERR, "diagramas", "tk_rx.svg"),
    "CODIGO_TK_TX": os.path.join(BASE, "tinkercad", "tx-tinkercad", "tx-tinkercad.ino"),
    "CODIGO_TK_RX": os.path.join(BASE, "tinkercad", "rx-tinkercad", "rx-tinkercad.ino"),
    "SVG_TX":  os.path.join(FERR, "diagramas", "svg_tx.svg"),
    "SVG_RX":  os.path.join(FERR, "diagramas", "svg_rx.svg"),
    "SVG_LCD": os.path.join(FERR, "diagramas", "svg_lcd.svg"),
    "CODIGO_TX": os.path.join(BASE, "transmissor-nano", "transmissor-nano.ino"),
    "CODIGO_RX": os.path.join(BASE, "receptor-uno", "receptor-uno.ino"),
}


def ler(caminho):
    with open(caminho, encoding="utf-8") as f:
        return f.read()


def main():
    pagina = ler(os.path.join(FERR, "modelo.html"))
    faltando = []

    for marca, caminho in PECAS.items():
        if not os.path.exists(caminho):
            faltando.append(caminho)
            continue
        conteudo = ler(caminho).strip("\n")
        # O codigo entra dentro de <script type="text/plain">, onde o navegador so
        # para no fechamento da tag. Nenhum .ino tem isso, mas se um dia tiver, o
        # texto quebraria a pagina inteira sem aviso.
        if marca.startswith("CODIGO") and "</script" in conteudo.lower():
            print(f"ERRO: {caminho} contem '</script'", file=sys.stderr)
            return 1
        pagina = pagina.replace("{{" + marca + "}}", conteudo)

    if faltando:
        print("ERRO: arquivo nao encontrado:", file=sys.stderr)
        for c in faltando:
            print("  " + c, file=sys.stderr)
        print("\nGere os diagramas antes: python ferramentas/gerar-diagramas.py",
              file=sys.stderr)
        return 1

    sobrou = [m for m in PECAS if "{{" + m + "}}" in pagina]
    if sobrou:
        print(f"ERRO: marcas nao substituidas: {', '.join(sobrou)}", file=sys.stderr)
        return 1

    saida = os.path.join(BASE, "index.html")
    with open(saida, "w", encoding="utf-8", newline="\n") as f:
        f.write(pagina)
    print(f"index.html gerado: {len(pagina):,} bytes".replace(",", "."))
    return 0


if __name__ == "__main__":
    sys.exit(main())
