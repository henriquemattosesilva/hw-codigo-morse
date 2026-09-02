# Montagem em protoboard

Duas protoboards independentes, uma para cada lado. Nada liga uma na outra —
a única ligação entre elas é o rádio.

Monte primeiro o transmissor inteiro e teste pelo monitor serial. Só depois
monte o receptor. Assim, se algo não funcionar, você sabe de que lado está.

---

## Antes de começar

**Sempre desligue o USB antes de mexer na fiação.** Ligar um fio no lugar errado
com a placa energizada é a forma mais comum de queimar um pino.

**Pinos que a biblioteca do rádio reserva sozinha.** A `RH_ASK` configura três
pinos por conta própria, mesmo que você não os use. Deixe-os vazios:

| Placa | Reservados | Uso |
|---|---|---|
| Nano | D10, D11, **D12** | D12 é o DATA do transmissor; D10 e D11 ficam vazios |
| Uno | D10, **D11**, D12 | D11 é o DATA do receptor; D10 e D12 ficam vazios |

**D0 e D1 são a USB.** Não use nos dois lados, ou o monitor serial para de
funcionar e o upload falha.

**Identificando o LED.** A perna longa é o anodo (+, vai para o resistor). A
perna curta fica do lado chanfrado do corpo e é o catodo (−, vai para o GND).

**Identificando a chave táctil.** Os quatro pinos são, na verdade, dois pares
já ligados internamente. Se você usar o par errado, a chave fica sempre
fechada. O jeito seguro é montá-la atravessando o canal central da protoboard e
usar **dois pinos na diagonal**.

---

## Lado A — Transmissor (Arduino Nano)

Encaixe o Nano atravessando o canal central da protoboard. Ligue o pino **5V**
do Nano na trilha vermelha (+) e o **GND** na trilha azul (−) das laterais.

### Ligações

| Componente | Ligação |
|---|---|
| Chave táctil (manipulador) | um pino → **D2**, pino na diagonal → GND (−) |
| LED **verde 1** (ponto) | **D3** → resistor 220 Ω → anodo; catodo → GND (−) |
| Buzzer ativo (2 pinos) | S → **D4**; GND → GND (−). Não tem pino de VCC |
| LED **verde 2** (traço) | **D5** → resistor 220 Ω → anodo; catodo → GND (−) |
| LED **azul** (espaço) | **D6** → resistor 220 Ω → anodo; catodo → GND (−) |
| Módulo transmissor 433 MHz | DATA → **D12**; VCC → 5V (+); GND → GND (−) |
| Potenciômetro 10K (velocidade) | pino da esquerda → 5V (+); **cursor (do meio) → A0**; pino da direita → GND (−) |

**O buzzer não tem pino de alimentação.** Com apenas S e GND, quem alimenta o
buzzer é o próprio pino D4: ao ir para nível alto, ele fornece os 5 V e a
corrente. É assim que os buzzers de dois pinos funcionam, mas repare que são uns
20 a 30 mA saindo de um pino só. O ATmega328 recomenda 20 mA por pino e admite
40 mA no limite absoluto, então isso fica no teto do recomendado.

Funciona direto, e é como esses buzzers são usados em qualquer kit. Se quiser
poupar o pino, um transistor **C945** com um resistor de 10 kΩ na base faz o
buzzer puxar corrente do 5 V em vez do D4 — você tem dez transistores e dezenove
resistores de 10 kΩ.

O módulo transmissor tem só três pinos e costuma vir com a serigrafia
`DATA / VCC / GND` (às vezes escrita `ATAD`). O furo maior sozinho, num canto
da plaquinha, é o da antena.

### Vista de cima

```
                        trilha +  (5V)
   ┌──────────────────────────────────────────────┐
   │  [POT 10K]        [BUZZER]      [TX 433MHz]  │
   │   │ │ │            │  │          │   │   │   │
   │   +A0 −            D4 −         D12  +   −   │      antena: fio reto
   │                                               │      de 17,3 cm no furo ANT
   │        ┌───────────────────┐                  │
   │        │   ARDUINO NANO    │                  │
   │        │  D2 D3 D4 D5 D6   │                  │
   │        └───┬──┬──┬──┬──┬───┘                  │
   │            │  │  │  │  │                      │
   │       [CHAVE] │  │  │  │                      │
   │            │ 220 │ 220 220                    │
   │            │  │  │  │  │                      │
   │            │ LED│ LED LED                     │
   │            │verde amar azul                   │
   └────────────┴──┴──┴──┴──┴──────────────────────┘
                        trilha −  (GND)
```

---

## Lado B — Receptor (Arduino Uno)

O Uno fica fora da protoboard, ligado a ela por jumpers macho-fêmea. Ligue o
**5V** e o **GND** do Uno nas trilhas da protoboard antes de tudo.

### Display LCD 16x2

O LCD tem 16 pinos, numerados da esquerda para a direita olhando a frente do
display com os pinos na parte de cima.

| Pino do LCD | Nome | Vai para |
|---|---|---|
| 1 | VSS | GND (−) |
| 2 | VDD | 5V (+) |
| 3 | V0 | **cursor do potenciômetro 10K** (contraste) |
| 4 | RS | **D2** |
| 5 | RW | GND (−) |
| 6 | E | **D3** |
| 7 a 10 | D0–D3 | não ligar |
| 11 | D4 | **D4** |
| 12 | D5 | **D5** |
| 13 | D6 | **D6** |
| 14 | D7 | **D7** |
| 15 | A | resistor 220 Ω → 5V (+) |
| 16 | K | GND (−) |

O pino 5 (RW) **precisa** ir ao GND. Ele escolhe entre escrever e ler no
display; solto, o LCD fica com a tela em branco ou cheia de blocos pretos.

O resistor no pino 15 não é opcional. Vários módulos não têm resistor interno
na luz de fundo, e ligá-lo direto no 5V queima o LED do backlight.

Os pinos 3 (contraste) e 15 (luz de fundo) fazem coisas diferentes e são
confundidos o tempo todo. Se a tela acende mas não aparece nada, o problema é o
contraste, no pino 3.

### Demais ligações

| Componente | Ligação |
|---|---|
| Potenciômetro 10K (contraste) | esquerda → 5V (+); **cursor → pino 3 do LCD**; direita → GND (−) |
| Módulo receptor 433 MHz | DATA → **D11**; VCC → 5V (+); GND → GND (−) |
| LED **vermelho** (recebendo) | **D8** → resistor 220 Ω → anodo; catodo → GND (−) |
| Chave táctil (limpar tela) | um pino → **D9**, pino na diagonal → GND (−) |

O módulo receptor tem quatro pinos, e os **dois do meio são o mesmo DATA**,
ligados internamente. Use qualquer um dos dois. A ordem costuma ser
`VCC / DATA / DATA / GND`, mas confira a serigrafia da sua plaquinha, porque
existem versões com a ordem invertida.

---

## Antenas

Sem antena o alcance é de uns poucos centímetros — dá para testar na bancada e
mais nada. Com antena, passa de 30 metros em campo aberto.

Corte **17,3 cm** de fio rígido em cada módulo e enfie no furo marcado `ANT`.
Essa medida é um quarto do comprimento de onda de 433 MHz e não é arbitrária:
encurtar ou alongar derruba o alcance. Deixe o fio o mais reto possível, para
cima, e afastado da placa e dos jumpers.

---

## Ordem de montagem e teste

Testar por partes é o que evita passar horas procurando um problema que está em
outro lugar.

**1. Bibliotecas.** Na IDE do Arduino, *Ferramentas → Gerenciar Bibliotecas*,
procure **RadioHead** (de Mike McCauley) e instale. A `LiquidCrystal` já vem
com a IDE.

**2. Transmissor sozinho.** Monte o lado A, envie o `transmissor-nano.ino` e
abra o monitor serial em **9600 baud**. Ao ligar, os três LEDs devem acender em
sequência e o buzzer dar um bipe — isso confirma a fiação sem multímetro.

Gire o potenciômetro para o lado lento e bata no botão. Cada letra fechada
aparece no monitor assim:

```
.- = A
... = S
[espaco]
```

Aqui o rádio ainda não importa. Se as letras saem certas no serial, o
manipulador está bom.

**Placa a selecionar:** *Arduino Nano*, processador **ATmega328P**. Se o upload
der erro de sincronismo, troque para **ATmega328P (Old Bootloader)** — quase
todo Nano clone precisa disso.

**3. Receptor sozinho.** Monte o lado B e envie o `receptor-uno.ino`. Antes de
mais nada, gire o potenciômetro de contraste devagar de ponta a ponta: em algum
ponto do curso o texto `MORSE 433MHz` aparece. Se você não girar o
potenciômetro, é normal a tela parecer morta ou mostrar só uma fileira de
quadrados.

**4. Os dois juntos.** Deixe as duas protoboards a meio metro de distância.
Bata uma letra no botão: o LED vermelho pisca e a letra aparece no LCD.

**5. Distância.** Só depois que funcionar lado a lado, vá afastando.

---

## Quando não funciona

| Sintoma | Causa provável |
|---|---|
| LCD aceso, tela em branco | contraste: gire o potenciômetro ligado ao pino 3 |
| LCD com uma fileira de quadrados pretos | mesma coisa, contraste no extremo errado |
| LCD totalmente apagado | luz de fundo: confira o resistor no pino 15 e o pino 16 no GND |
| Tela em branco e contraste não resolve | pino 5 (RW) solto — precisa ir ao GND |
| Letras erradas ou embaralhadas no LCD | inverta os fios de D4–D7 do LCD, é fácil trocar a ordem |
| Nada chega, mas o serial do Nano mostra as letras certas | antena faltando, ou DATA do receptor fora do D11 |
| Chegam letras aleatórias sem você bater nada | ruído de 433 MHz de portão ou campainha; é normal que apareça pouca coisa, o CRC barra quase tudo |
| Botão dispara sozinho ou em dobro | você pegou o par de pinos errado da chave táctil; use os pinos na diagonal |
| Buzzer dá um clique em vez de apitar | ele é passivo, não ativo: troque os `digitalWrite` de `PINO_BUZZER` por `tone(PINO_BUZZER, 620)` e `noTone(PINO_BUZZER)` |
| Todo toque vira traço | potenciômetro de velocidade no extremo rápido; gire para o lado lento |
| Todo toque vira ponto | o contrário, ou o cursor do potenciômetro não está em A0 |
| Os três LEDs piscam sem parar ao ligar | o rádio não iniciou; confira VCC e GND do módulo |
| Upload no Nano falha com `not in sync: resp=0x00`, dez tentativas | **confirmado em 01/09/2026:** selecione Tools → Processor → *ATmega328P (Old Bootloader)*. O clone fala a 57600 bauds e o IDE tenta 115200 |
| Upload falha e você tem as duas placas no USB | a COM escolhida pode ser a do ESP8266, que também aparece como porta. Desconecte o ESP e veja qual porta some |
| Toda letra sai separada por `[espaco]` | é a pausa entre as suas letras passando de 7 unidades. A 250 ms isso é 1,75 s — normal quando se testa letra por letra |
| O serial mostra sempre `unidade: 250ms` | o valor só é impresso no `setup()`. Gire o potenciômetro e aperte o reset: se não mudar, o cursor não está no A0 |
