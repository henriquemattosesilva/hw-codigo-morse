# Montagem do receptor com ESP8266

Este é o receptor que, além de mostrar no LCD, publica a mensagem na internet.
Substitui o Arduino Uno; o transmissor com o Nano não muda em nada.

A versão com Uno continua no projeto e é mais simples. Se você nunca montou o
rádio antes, **monte primeiro a versão com Uno**: ela prova que o rádio funciona
sem trazer junto WiFi, tensão de 3,3 V e divisor resistivo. Aí é só trocar a
placa da ponta.

---

## As três diferenças que importam

### 1. O ESP8266 é 3,3 V e o módulo de rádio é 5 V

A saída `DATA` do receptor de 433 MHz entrega cerca de 5 V. Os pinos do ESP8266
não toleram isso: ligar direto vai degradar o pino com o tempo, e pode matá-lo
de uma vez. Entre os dois vai um divisor resistivo.

O módulo tem **quatro pinos, mas três ligações**: os dois `DATA` do meio são o
mesmo ponto, ligados por dentro da plaquinha. Use qualquer um dos dois e deixe o
outro livre.

```
              módulo receptor 433 MHz
        ┌────────────────────────────────────┐
        │   VCC     DATA     DATA      GND   │
        └────┬────────┬─────────┬────────┬───┘
             │        │         │        │
             │        │    (deixe livre) │
             │        │                  │
            VU     [10 kΩ]               G
                      │
                      ├──────────►  D2 do ESP8266   (3,33 V)
                      │
                   [10 kΩ]
                      │
                   [10 kΩ]
                      │
                      G      o mesmo terra do ESP
```

**A ordem dos pinos varia entre fabricantes — confira a serigrafia da sua plaquinha.**
No módulo desta bancada ela é o inverso do desenho acima: `GND` no primeiro pino e `VCC`
no quarto. Ligar pela figura, sem olhar a plaquinha, foi o que segurou este projeto por
duas sessões.

`VCC` vai no **`VU`**, que é o 5 V da USB — **nunca no `3V3`**. Este receptor é
superregenerativo e não estabelece ganho em 3,3 V: fica mudo, sem nenhum aviso, e o
sintoma é idêntico ao de um módulo queimado. `GND` vai no `G`, e é esse mesmo `G` que
fecha o pé do divisor: se os dois terras não forem o mesmo, a conta do divisor não
vale.

Os dois resistores de baixo, em série, somam 20 kΩ:
`5 V × 20 kΩ ÷ (10 kΩ + 20 kΩ) = 3,33 V`. Você tem 19 resistores de 10 kΩ, e
esta montagem usa três.

**Não pule esta parte nem para "só testar rápido".** É o tipo de dano que não
aparece na hora e depois deixa você caçando um defeito que parece de software.

### 2. Cada pino de boot leva a peça que empurra para o lado certo

O ESP8266 lê o nível de três pinos no instante em que liga, para decidir como
inicializar: **GPIO0 e GPIO2 têm que estar em nível alto, e GPIO15 em nível
baixo**. Com o nível errado ele não arranca, ou não aceita gravação.

Não é uma preocupação teórica. A primeira versão desta montagem punha o LCD nos
três, no raciocínio de que as entradas dele ficam em alta impedância e não
perturbariam nada. **Na bancada isso se mostrou falso**: o LCD é alimentado em
5 V pelo `VU`, e a fuga pelos diodos de proteção da entrada RS puxava o GPIO15
para cima, vencendo o resistor de 12 kΩ da placa. O ESP entrava em modo SDIO e
a gravação morria em `Timed out waiting for packet header`. Tirar aquele fio
único fazia gravar de novo.

Por isso os três pinos delicados agora ficam com peças compatíveis:

| Pino | Precisa | O que ficou nele | Por quê |
|---|---|---|---|
| GPIO0 (D3) | alto | chave de limpar | botão aberto + pull-up interno = alto. É como o próprio botão FLASH da placa é ligado |
| GPIO2 (D4) | alto | uma linha de dados do LCD | a fuga dos 5 V puxa para cima — justamente o nível que este pino quer |
| GPIO15 (D8) | baixo | LED vermelho | o LED não puxa para lado nenhum abaixo da tensão direta dele; o mérito é **não brigar** com o resistor da placa |

Repare que o LED **não é** um resistor de pull-down: abaixo de uns 2 V ele é
praticamente circuito aberto. Quem segura o GPIO15 é o resistor que já está na
placa. O que mudou é que agora nada disputa com ele.

**O rádio continua fora dos três**, e por um motivo diferente: enquanto não há
transmissão, a saída do receptor AM é **ruído aleatório**. Num pino de boot,
seria cara ou coroa a cada vez que você ligasse.

**Efeito colateral do botão no GPIO0:** segurar a chave de limpar enquanto a
placa reseta faz o ESP entrar em modo de gravação. Não segure no reset.

### 3. WiFi e rádio disputam o mesmo processador

A `RH_ASK` no ESP8266 usa o timer0 para amostrar o pino oito vezes por bit, e a
pilha de WiFi desliga a interrupção de vez em quando para cuidar do rádio dela.
Isso pode comer um pacote aqui e ali — coisa que a versão com Uno não tem.

As três repetições de cada letra, que já existiam por causa do ruído de 433 MHz,
cobrem a maior parte disso. Se ainda assim faltar letra, subir `REPETICOES` no
transmissor para 5 é o primeiro ajuste.

---

## A placa

A sua é uma **NodeMCU v3 (LoLin)**, de PCB preto e conversor CH340G.

**Ela é larga demais para protoboard.** Os 25,5 mm cobrem o canal central e
quase todas as fileiras dos dois lados, sobrando no máximo uma coluna de furos —
não dá para trabalhar. Deixe a placa fora da protoboard e ligue por **jumpers
macho-fêmea** direto nos headers dela. Você tem 80.

**Use o pino `VU`, não o `3V3`.** O `VU` é o 5 V da USB, e é dele que saem a
alimentação do LCD e do módulo de rádio. Fica na fileira de baixo, entre `G` e
`S3`. O `VIN` é entrada de energia, não saída.

---

## Ligações

| Função | Pino da placa | GPIO | Observação |
|---|---|---|---|
| LCD RS | **D1** | 5 | |
| LCD E | **D0** | 16 | é também um LED da placa, que vai piscar |
| LCD D4 | **D4** | 2 | pino de boot; é também o LED do módulo, que vai piscar |
| LCD D5 | **D5** | 14 | |
| LCD D6 | **D6** | 12 | |
| LCD D7 | **D7** | 13 | |
| DATA do rádio | **D2** | 4 | **atrás do divisor**, nunca direto. Qualquer um dos dois DATA |
| VCC do rádio | **VU** | — | o 5 V da USB, não o `3V3` |
| Chave de limpar | **D3** | 0 | outro terminal no `G`. Pino de boot — não segure no reset |
| LED vermelho | **D8** | 15 | com resistor de 220 Ω. Pino de boot |
| 5 V do LCD (pinos 2 e 15) | **VU** | — | o mesmo `VU` do rádio |
| Terra | **G** | — | |

O LCD liga igual à versão com Uno, menos a alimentação: os pinos 2 e 15 vão ao
`VU`, não a um pino de 5 V do Arduino. O pino 5 (RW) continua obrigatoriamente
no terra, e o contraste continua no potenciômetro pelo pino 3.

### Um detalhe que pode dar trabalho

O LCD é alimentado com 5 V mas recebe sinais de 3,3 V. Pela folha de dados, o
HD44780 quer 3,5 V para reconhecer nível alto — 3,3 V está tecnicamente abaixo.
Na prática a maioria dos módulos aceita sem reclamar, e é por isso que vamos
assim.

Se a tela mostrar lixo, blocos, ou nada com o contraste bem ajustado, o problema
é esse. A correção é baixar a tensão do LCD: um diodo comum em série com o pino
2 derruba uns 0,7 V, e a 4,3 V o limite cai para cerca de 3,0 V, abaixo dos
3,3 V que o ESP entrega. Você não tem diodos avulsos, mas a junção base-emissor
de um transistor **C945** funciona como um: base e coletor juntos formam o
anodo, o emissor é o catodo. Você tem dez.

---

## Antes de gravar

Copie `receptor-esp8266/segredos-exemplo.h` para `receptor-esp8266/segredos.h` e
preencha:

```c
#define WIFI_SSID   "sua-rede"
#define WIFI_SENHA  "sua-senha"
#define MQTT_TOPICO_BASE "hw-codigo-morse/algo-so-seu"
```

O `segredos.h` está no `.gitignore`: **a senha do seu WiFi não vai para o
GitHub.** Sem esse arquivo o sketch não compila, e isso é de propósito.

O `MQTT_TOPICO_BASE` precisa ser **exatamente igual** ao `TOPICO_BASE` que está
em `ao-vivo/index.html`. Se os dois não baterem, a página fica escutando um
telégrafo que não é o seu — sem nenhum erro na tela, simplesmente nunca chega
nada.

Troque o sufixo por algo só seu. O broker é público e sem senha: quem souber o
nome do tópico lê o que você transmite, e escreve nele.

**Placa a selecionar na IDE:** *NodeMCU 1.0 (ESP-12E Module)*. Bibliotecas:
RadioHead, PubSubClient e LiquidCrystal.

---

## Ordem de teste

**1. Só a placa e o LCD.** Grave o sketch sem ligar o rádio ainda. Gire o
potenciômetro de contraste de ponta a ponta até aparecer `MORSE + WiFi` e
`ligando WiFi...`. Se a tela não acender nada em ponto nenhum do curso, pare
aqui: é contraste, alimentação ou o RW solto.

**2. O WiFi.** Depois de conectar, o canto direito da linha 1 mostra o estado:
vazio sem WiFi, `w` com WiFi mas sem o broker, e um desenho de antena quando os
dois estão de pé. O monitor serial em **115200** conta o resto.

**3. A página ao vivo.** Abra
[a página](https://henriquemattosesilva.github.io/hw-codigo-morse/ao-vivo/) com
o telégrafo ligado: a bolinha do canto tem que ficar verde e dizer "telégrafo
ligado", mesmo sem nenhuma letra ter chegado ainda. Isso já prova o caminho
inteiro até a internet, antes de envolver o rádio.

**4. O rádio.** Aí sim, ligue o receptor com o divisor e bata um `E` no
transmissor.

---

## Quando não funciona

| Sintoma | Causa provável |
|---|---|
| A placa não inicia, ou entra em modo de gravação sozinha | algo está segurando GPIO0, GPIO2 ou GPIO15 no nível errado no boot. O rádio não pode estar em nenhum desses |
| `Timed out waiting for packet header` com o LCD ligado | **aconteceu de verdade:** era o RS do LCD no D8. Confira se o RS está no **D1**, e não no D8 — este projeto trocou esses pinos justamente por isso |
| A placa entra em modo de gravação ao resetar | você segurou a chave de limpar. Ela está no GPIO0, o mesmo pino do botão FLASH |
| `Timed out waiting for packet header` na gravação | **primeiro** confira se a porta é mesmo a do ESP: o Nano e a NodeMCU aparecem os dois como `USB-SERIAL CH340`, e a lista de portas não distingue. Desconecte o Nano e veja qual porta some |
| `could not open port` na gravação | a porta sumiu naquele instante — quase sempre o cabo desencostou. O Windows leva alguns segundos para reenumerar |
| Ao resetar, o serial mostra caracteres quebrados e só depois o texto | normal: o bootloader de ROM fala a 74880 bauds, taxa fixa de fábrica. O que vem depois é o seu programa, a 115200 |
| Quer testar WiFi e página sem montar nada | pode: `radio.init()` não detecta hardware, então a placa pelada conecta igual. É a forma mais limpa de separar rede de rádio |
| Tela com lixo ou blocos, contraste bem ajustado | os 3,3 V do ESP estão no limite para o LCD: veja o truque do diodo acima |
| LCD apagado e o `3V3` foi usado | o LCD precisa do `VU`; em 3,3 V ele não funciona direito |
| A bolinha da página nunca fica verde | o tópico da página e o do `segredos.h` estão diferentes |
| Página verde mas nenhuma letra | o problema é o rádio, não a internet. **Antes de qualquer teoria, confira a alimentação do módulo:** o `VCC` dele tem de estar no `VU`, e no pino certo da plaquinha |
| Nada chega, e o transmissor está comprovadamente certo | **aconteceu de verdade, duas vezes seguidas:** o módulo estava sem 5 V. Uma vez porque o fio do `VU` estava num dos `DATA`, outra porque a linha `+` da protoboard vinha do `3V` |
| A ordem dos pinos do módulo não bate com o diagrama | acontece: **no módulo desta bancada o `GND` é o primeiro pino e o `VCC` o quarto**, invertido em relação ao desenho. Vá pela serigrafia, não pela figura |
| Faltam letras que a versão com Uno pegava | WiFi disputando com o rádio: suba `REPETICOES` para 5 no transmissor |
| `WiFi` conecta e cai o tempo todo | alimentação; o ESP puxa picos de corrente ao transmitir |
| Os LEDs da placa piscam sozinhos ao escrever no LCD | é normal: GPIO2 e GPIO16 são LEDs da placa e ao mesmo tempo linhas do LCD (D4 e E) |
