# Telégrafo sem fio em código morse — 433 MHz

Data: 2026-08-31

## Objetivo

Um manipulador de morse com um botão no Arduino Nano transmite por rádio
frequência 433 MHz para um Arduino Uno, que exibe a mensagem decodificada em um
display LCD 16x2. A montagem inicial é em protoboard.

## Componentes usados

Todos já estão no inventário em `../Componentes`.

| Peça | Qtd | Lado |
|---|---|---|
| Arduino Nano V3.0 | 1 | transmissor |
| Arduino Uno R3 | 1 | receptor |
| Módulo Transmissor RF 433MHz AM | 1 | transmissor |
| Módulo Receptor RF 433MHz AM | 1 | receptor |
| Display LCD 16x2 | 1 | receptor |
| Chave táctil | 2 | 1 manipulador, 1 limpar tela |
| Potenciômetro linear 10K | 2 | 1 velocidade, 1 contraste |
| LED verde 5mm difuso | 2 | transmissor, ponto e traço |
| LED azul 5mm difuso | 1 | transmissor, letra e espaço |
| LED vermelho 5mm difuso | 1 | receptor |
| Resistor 220Ω | 5 | 4 LEDs + backlight do LCD |
| Protoboard 830 pontos | 2 | um por lado |

## Arquitetura

Duas peças independentes acopladas apenas por um pacote de três bytes. Nenhum
dos lados conhece o estado interno do outro.

```
[botão] -> Nano: máquina de estados de timing -> letra -> RF 433MHz
                                                            |
        LCD 16x2 <- morse reconstruído <- letra <- Uno: RH_ASK  |
```

### Tabela morse compartilhada

Os dois sketches usam a mesma árvore binária de 63 bytes em PROGMEM:

```
"*ETIANMSURWDKGOHVF*L*PJBXCYZQ**54*3***2*******16*******7***8*90"
```

A partir do índice 0 (raiz vazia), ponto desce para `2i+1` e traço para `2i+2`.
O transmissor desce a árvore para achar a letra. O receptor faz o caminho
inverso: localiza a letra na tabela e sobe pelos pais (`(i-1)/2`), em que
`(i-1)%2 == 0` significa ponto e `1` significa traço. Uma tabela só, nos dois
lados, sem risco de divergirem.

`*` marca posições sem letra correspondente. Um índice acima de 62 ou apontando
para `*` produz `?`.

### Transmissor (Nano)

Máquina de estados sobre a duração dos toques, com a unidade de tempo lida do
potenciômetro em A0 (250 ms a 60 ms, do mais lento ao mais rápido). A unidade é
relida apenas quando o manipulador está ocioso, para não alterar os limiares no
meio de uma letra.

Limiares, em unidades:

| Evento | Limiar | Efeito |
|---|---|---|
| Toque solto antes de 2u | < 2u | símbolo é ponto |
| Toque solto depois de 2u | >= 2u | símbolo é traço |
| Silêncio com símbolos no buffer | >= 3u | fecha a letra, decodifica, transmite |
| Silêncio depois de fechar a letra | >= 7u | transmite espaço de palavra |

Debounce de 25 ms na borda de descida; toques abaixo disso são descartados.
O buffer de símbolos tem 6 posições; um sétimo símbolo força o fecho da letra
como `?` em vez de estourar o buffer.

LEDs como limiares ao vivo, para dar retorno antes de o operador soltar:

- um verde acende ao tocar (o símbolo em curso é um ponto)
- o segundo verde acende junto quando a duração cruza 2u (virou traço).
  Dois LEDs iguais em vez de duas cores: conta-se quantos estão acesos
- azul acende quando o silêncio cruza 3u (letra fechada e transmitida) e dá um
  pisca duplo antes de apagar quando cruza 7u (espaço de palavra transmitido)

O buzzer ativo apita enquanto o botão está pressionado, como sidetone. Ele tem
apenas dois pinos, S e GND, então é o próprio D4 que o alimenta ao ir para
nível alto — 20 a 30 mA num pino que recomenda 20 mA.

### Protocolo de rádio

Biblioteca RadioHead `RH_ASK` a 2000 bps, que já fornece preâmbulo, codificação
4b6b e CRC-16. Pacote de 3 bytes:

| Byte | Conteúdo |
|---|---|
| 0 | `'M'`, marca de aplicação |
| 1 | número de sequência, 0-255, incrementado a cada caractere novo |
| 2 | o caractere ASCII |

Cada caractere é transmitido três vezes seguidas. O 433 AM perde pacotes com
facilidade e não há canal de retorno, então a redundância é a única defesa. O
receptor descarta o pacote cujo número de sequência for igual ao último aceito,
de modo que as repetições não escrevem letras duplicadas. Um caractere
legitimamente repetido (`SS`) recebe números de sequência diferentes e passa.

### Receptor (Uno)

Layout do LCD:

```
linha 1:  ·-··  L         *
linha 2:  CHAMANDO_
```

Linha 1: o morse reconstruído da última letra (colunas 0-5), a letra (coluna 7)
e um indicador de recepção na coluna 15 que aparece por 150 ms a cada pacote
válido. Linha 2: as últimas 16 letras recebidas, rolando para a esquerda quando
enche, com um cursor `_` na posição seguinte.

Ponto e traço são caracteres customizados do HD44780, desenhados centralizados
na altura da linha. Um `.` e um `-` do próprio charset ficariam na base e no
meio, desalinhados entre si.

O LED vermelho acende por 150 ms a cada pacote válido. A segunda chave táctil
limpa o texto acumulado.

O LCD só é reescrito quando algo muda. `RH_ASK` roda numa interrupção de Timer1
a 16 kHz e as escritas no LCD são lentas; redesenhar a tela a cada volta do loop
aumenta a chance de perder pacotes.

## Pinagem

### Nano — transmissor

| Pino | Ligação |
|---|---|
| D2 | chave táctil (INPUT_PULLUP, outro terminal ao GND) |
| D3 | LED verde (ponto) + 220Ω |
| D4 | buzzer ativo de 2 pinos: S no pino, GND no terra. Sem VCC — o pino é que alimenta |
| D5 | LED verde 2 (traço) + 220Ω |
| D6 | LED azul (espaço/letra) + 220Ω |
| D12 | DATA do módulo transmissor RF |
| A0 | cursor do potenciômetro 10K (velocidade) |

### Uno — receptor

| Pino | Ligação |
|---|---|
| D2 | LCD RS |
| D3 | LCD E |
| D4-D7 | LCD D4-D7 |
| D8 | LED vermelho (pacote recebido) + 220Ω |
| D9 | chave táctil (limpar tela, INPUT_PULLUP) |
| D11 | DATA do módulo receptor RF |
| A0 | livre |

D12 no Nano e D11 no Uno são os padrões da `RH_ASK` no AVR. Mantidos como estão
para não precisar reconfigurar a biblioteca.

## Tratamento de erro

| Falha | Comportamento |
|---|---|
| Sequência de pontos e traços sem letra | transmite `?` |
| Mais de 6 símbolos numa letra | fecha como `?` |
| Toque menor que o debounce | descartado, nada é registrado |
| Pacote corrompido no ar | CRC da `RH_ASK` rejeita, nada aparece |
| Pacote perdido no ar | as duas repetições cobrem |
| Repetição recebida | descartada pelo número de sequência |
| Pacote sem a marca `'M'` ou de tamanho errado | ignorado |

Ruído de 433 MHz do ambiente (portões, campainhas) é filtrado pela combinação de
CRC, marca `'M'` e tamanho fixo de 3 bytes.

## Verificação

Não há como testar automaticamente o rádio ou o LCD sem o hardware montado. A
verificação possível antes da bancada é a compilação dos dois sketches com
`arduino-cli` para `arduino:avr:nano` e `arduino:avr:uno`, checando também que o
uso de RAM deixa folga no Nano.

Na bancada, a ordem de teste é: primeiro o transmissor sozinho pelo monitor
serial (confere a decodificação dos toques sem envolver o rádio), depois o
receptor com os dois lado a lado, e só então a distância.

## Fora de escopo

Confirmação de recebimento, retransmissão sob demanda, criptografia,
comunicação bidirecional e pontuação além de letras e números. O manipulador
cobre A-Z, 0-9 e espaço.
