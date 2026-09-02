# Telégrafo sem fio em código morse

Um manipulador de morse com um botão no Arduino Nano transmite por rádio
433 MHz para um receptor, que mostra a mensagem decodificada num LCD 16x2.
São **dois receptores possíveis**: um Arduino Uno, mais simples, e um ESP8266,
que além do LCD publica a mensagem na internet.

O botão é uma chave telegráfica de verdade: toque curto vira ponto, toque longo
vira traço, e as pausas separam as letras e as palavras. Você escreve qualquer
coisa, não uma mensagem programada de antemão.

```
   botão                                            LCD 16x2
     │                                                 ▲
     ▼                                                 │
   NANO  ──►  433 MHz  ))))))))))))))))))))  ──►  UNO ─┘
     │                                             │
  3 LEDs + buzzer                            LED + botão limpar
```

## Arquivos

**A página do projeto reúne tudo — componentes, montagem com diagramas, código das
duas placas e melhorias — numa tela só, boa de consultar no celular durante a montagem:**

### 👉 https://henriquemattosesilva.github.io/hw-codigo-morse/

Ela também traz um manipulador de morse que funciona no navegador, com os mesmos LEDs
e o mesmo display do projeto real. Dá para treinar antes de montar qualquer coisa.

| Arquivo | O que é |
|---|---|
| [index.html](index.html) | a página do projeto, publicada no GitHub Pages |
| [MONTAGEM.md](MONTAGEM.md) | esquema de ligação, ordem de teste e o que fazer quando não funciona |
| [transmissor-nano/](transmissor-nano/) | sketch do Nano (manipulador) |
| [receptor-uno/](receptor-uno/) | sketch do Uno (display) |
| [receptor-esp8266/](receptor-esp8266/) | sketch do ESP8266 (display + internet) |
| [MONTAGEM-ESP8266.md](MONTAGEM-ESP8266.md) | montagem do receptor com ESP8266 |
| [ao-vivo/](ao-vivo/) | a página que mostra a mensagem ao vivo |
| [tinkercad/](tinkercad/) | os dois sketches adaptados para o simulador |
| [ferramentas/](ferramentas/) | scripts que geram os diagramas e a página |
| [docs/superpowers/specs/](docs/superpowers/specs/) | o projeto escrito, com as decisões e os porquês |

O `index.html` é **gerado**, não editado à mão. Depois de mexer num sketch ou nos
diagramas, rode:

```
python ferramentas/gerar-diagramas.py   # só se mudou a fiação
python ferramentas/gerar-tinkercad.py   # só se mudou a montagem do simulador
python ferramentas/gerar-pagina.py      # sempre
```

## Os dois receptores

| | Arduino Uno | ESP8266 |
|---|---|---|
| Lógica | 5 V, liga o rádio direto | 3,3 V, **exige divisor** no DATA do rádio |
| Pinos | qualquer um serve | três são lidos no boot e mudam quem vai onde |
| Rádio | sozinho no processador | disputando com a pilha de WiFi |
| Mensagem | 15 letras no LCD | 160 guardadas, 15 no LCD, e **na internet** |
| Tinkercad | simula | não existe ESP8266 no simulador |

**Comece pelo Uno.** Ele prova que o rádio funciona sem trazer junto WiFi, tensão de
3,3 V e divisor resistivo. Trocar a placa da ponta depois é rápido.

Com o telégrafo com ESP8266 ligado, a mensagem aparece ao vivo em
**https://henriquemattosesilva.github.io/hw-codigo-morse/ao-vivo/** — a montagem está
no [MONTAGEM-ESP8266.md](MONTAGEM-ESP8266.md).

> A saída de dados do módulo de rádio entrega 5 V, e os pinos do ESP8266 não toleram
> isso. O divisor de 10 kΩ + 20 kΩ não é opcional.

## Simular antes de montar

Dá para rodar o projeto inteiro no [Tinkercad](https://www.tinkercad.com/) antes de
encostar num componente. O simulador não tem Arduino Nano, nem módulo de rádio
433 MHz, nem aceita a RadioHead — mas o rádio já era um link serial, então os dois
módulos viram **um fio de D12 a D11** e a RadioHead vira **SoftwareSerial**, nos
mesmos pinos. O buzzer ativo vira um piezo passivo, que precisa de `tone()`.

A montagem desenhada peça por peça, com os furos de cada perna, está na
[seção Tinkercad da página](https://henriquemattosesilva.github.io/hw-codigo-morse/#tinkercad).
Os sketches adaptados ficam em [tinkercad/](tinkercad/).

**Comece pelo [MONTAGEM.md](MONTAGEM.md).** A única biblioteca a instalar é a
**RadioHead**, pelo Gerenciador de Bibliotecas da IDE.

## Os LEDs do transmissor

O difícil no morse é que os tempos são invisíveis: você não sabe se o aperto já
virou traço até a letra sair errada. Os três LEDs mostram exatamente os limiares,
e acendem **antes** de você soltar o botão.

| O que você vê | O que significa |
|---|---|
| um verde aceso | o toque em curso ainda vale um **ponto** |
| os **dois** verdes acesos | o toque passou de 2 unidades, virou **traço** |
| azul aceso | o silêncio passou de 3 unidades: a **letra fechou e foi enviada** |
| azul piscando duas vezes | o silêncio passou de 7 unidades: **espaço** enviado |

Na prática você bate no botão contando os LEDs acesos, e solta quando o
símbolo que quer estiver na tela. O buzzer apita junto, para o ouvido acompanhar.

## A velocidade

Todo o morse é medido em múltiplos de uma **unidade** de tempo, e o
potenciômetro do transmissor define quanto ela vale — de 250 ms (bem lento, bom
para aprender) a 60 ms (rápido).

| Evento | Duração |
|---|---|
| ponto | 1 unidade |
| traço | 3 unidades |
| pausa entre pontos e traços da mesma letra | 1 unidade |
| pausa entre letras | 3 unidades |
| pausa entre palavras | 7 unidades |

O código separa ponto de traço em **2 unidades**, que é o meio do caminho entre
1 e 3. O potenciômetro só é lido com o manipulador parado, para que os limiares
não mudem no meio de uma letra.

## O alfabeto

```
A ·−      H ····    O −−−     V ···−     2 ··−−−    7 −−···
B −···    I ··      P ·−−·    W ·−−      3 ···−−    8 −−−··
C −·−·    J ·−−−    Q −−·−    X −··−     4 ····−    9 −−−−·
D −··     K −·−     R ·−·     Y −·−−     5 ·····    0 −−−−−
E ·       L ·−··    S ···     Z −−··     6 −····
F ··−·    M −−      T −                  1 ·−−−−
G −−·     N −·      U ··−
```

Comece por `E` (·), `T` (−), `A` (·−) e `N` (−·). `SOS` é `··· −−− ···`.

Uma sequência que não existe no alfabeto vira `?` — não trava nada, e é a forma
mais rápida de perceber que o timing está fora.

## Como a mensagem viaja

O Nano decodifica a letra antes de transmitir, e o que vai pelo ar é um pacote
de 3 bytes: uma marca `'M'`, um número de sequência e o caractere.

Mandar os pontos e traços crus pelo rádio seria mais fiel a um telégrafo, mas o
433 MHz AM é ruidoso e perde pulsos curtos com facilidade — as letras chegariam
erradas o tempo todo. Decodificando antes, uma interferência ou some com a letra
inteira ou não a afeta; ela nunca vira outra letra.

Como não existe canal de retorno, **cada letra é transmitida três vezes**. O
receptor usa o número de sequência para descartar as repetições, então a letra
só aparece uma vez no display. Uma perda isolada não come nada.

## Ajustes rápidos

| Quero | Onde mexer |
|---|---|
| Mais alcance, aceitando lentidão | `RH_ASK radio(1000);` nos **dois** sketches |
| Ambiente muito ruidoso | `REPETICOES` de 3 para 5, no transmissor |
| Mudar a faixa de velocidade | `UNIDADE_LENTA` e `UNIDADE_RAPIDA`, no transmissor |
| Botão registrando toques em dobro | aumente `DEBOUNCE_MS` para 40 |
| Buzzer dá um clique em vez de apitar | ele é passivo: use `tone()` no lugar de `digitalWrite` |

Se mudar a velocidade do rádio, mude **nos dois lados**. Com bitrates
diferentes, um lado não escuta o outro e não há nenhuma mensagem de erro.

---

# Melhorias

## Alcance

**Antena de 17,3 cm nos dois módulos.** Esta é, de longe, a que mais muda o
resultado: sem antena o alcance é de centímetros, com antena passa de 30 metros
em campo aberto. Já está no [MONTAGEM.md](MONTAGEM.md), mas vale repetir porque
é comum deixar para depois e concluir que o rádio é ruim.

**Alimentar o transmissor com mais tensão.** O módulo 433 MHz aceita de 3 V a
12 V, e a potência sobe junto. Em 5 V ele está na base da faixa. Ligue uma
bateria de 9 V no `VIN` do Nano e alimente o VCC do módulo pelo próprio `VIN`,
não pelo 5 V. O pino DATA continua em 5 V, o que é normal — o módulo só usa a
tensão maior para transmitir.

**Capacitor de desacoplamento no receptor.** Um de 100 nF em paralelo com um de
10 µF entre o VCC e o GND do módulo receptor, o mais perto possível dos pinos.
O receptor AM é sensível a ruído na alimentação, e o LCD com a luz de fundo
puxando corrente é justamente uma fonte de ruído. Você não tem capacitores na
lista de componentes — valem a compra, custam centavos e servem em todo projeto
daqui para frente.

**Afaste as antenas dos cabos USB e das fontes chaveadas.** Carregador de
celular perto da bancada derruba o alcance de forma dramática.

## Uso

**Manipulador iâmbico (a evolução clássica).** Com duas chaves tácteis em vez de
uma, o Arduino gera os pontos e traços com a duração certa sozinho: segure a
esquerda e saem pontos perfeitos, segure a direita e saem traços perfeitos. É
como todo radioamador opera hoje, e resolve de vez o problema de acertar a
duração na mão. Você tem 19 chaves tácteis sobrando.

**Chave táctil emborrachada como manipulador.** Você tem quatro delas, e o toque
macio é bem mais confortável para bater morse do que o clique seco da chave
comum.

**Sensor touch TTP223B no lugar do botão.** Você tem um. Manipular por toque,
sem parte móvel, fica bem mais parecido com uma chave telegráfica moderna.

**Chave SS de 2 posições para escolher o modo.** Você tem três. Uma posição
manipula livre, a outra dispara uma mensagem pronta (`SOS`, seu indicativo)
inteira em morse a cada aperto.

**Brilho da luz de fundo por software.** Em vez do resistor fixo no pino 15 do
LCD, use um transistor C945 (você tem dez) comandado por um pino PWM do Uno.
Aí o brilho vira uma variável no código, e não uma peça soldada.

## Evoluções, todas com peças que você já tem

**Registrador telegráfico.** Junte o módulo de cartão SD com o RTC DS1307 no
receptor e grave cada mensagem recebida com data e hora. Vira um projeto
completo por si só, e é o passo natural depois que este funcionar.

**A letra em tamanho grande.** A matriz de LED 8x8 com MAX7219 no receptor,
mostrando a letra que acabou de chegar enquanto o LCD segue com o texto. Fica
ótimo de ver de longe.

**Mais texto na tela.** O display Nokia 5110 cabe várias linhas e permite manter
um histórico em vez de só as últimas 15 letras.

**Mensagens na internet.** O ESP8266 no lugar do Uno como receptor, publicando o
que chega. Aí o telégrafo alcança qualquer lugar, não 30 metros.

**Áudio no lado que recebe.** Um segundo buzzer no receptor, reproduzindo o
morse da letra que chegou. Você só tem um buzzer, e ele faz mais falta no
transmissor como sidetone — mas com um buzzer **passivo** e a função `tone()`
dá para escolher a frequência do apito, o que soa muito mais parecido com um
rádio de verdade do que o bipe fixo do buzzer ativo.

## Cuidados

**Comunicação nos dois sentidos exige mais peças.** Você tem um transmissor e um
receptor; para conversar nos dois sentidos precisaria de mais um par. Não dá
para usar o mesmo módulo nas duas funções.

**A faixa de 433 MHz é compartilhada.** Portões eletrônicos, campainhas sem fio
e sensores de alarme usam a mesma frequência e vão aparecer como ruído. O CRC da
biblioteca barra quase tudo, e a marca `'M'` do pacote barra o resto — mas se
o vizinho tiver um portão que dispara muito, espere alguma perda de pacote.

**Não há criptografia.** Qualquer receptor 433 MHz na vizinhança consegue ler o
que você transmite. Para um projeto de bancada tanto faz; só não mande nada que
importe.
