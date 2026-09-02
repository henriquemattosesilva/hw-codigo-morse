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

```
   DATA do receptor 433 MHz  (5 V)
            │
          [10 kΩ]
            │
            ├───────────────►  D2 do ESP8266   (3,33 V)
            │
          [10 kΩ]
            │
          [10 kΩ]
            │
           GND
```

Os dois resistores de baixo, em série, somam 20 kΩ:
`5 V × 20 kΩ ÷ (10 kΩ + 20 kΩ) = 3,33 V`. Você tem 19 resistores de 10 kΩ, e
esta montagem usa três.

**Não pule esta parte nem para "só testar rápido".** É o tipo de dano que não
aparece na hora e depois deixa você caçando um defeito que parece de software.

### 2. O LCD vai nos pinos de boot, e o rádio não

O ESP8266 lê o nível de três pinos no instante em que liga, para decidir como
inicializar: **GPIO0 e GPIO2 têm que estar em nível alto, e GPIO15 em nível
baixo**. Com o nível errado ele não arranca, ou entra em modo de gravação.

Parece que a saída de dados do rádio deveria ficar longe deles, e é exatamente
isso: enquanto não há transmissão, a saída do receptor AM é **ruído aleatório**.
Num pino de boot, seria cara ou coroa a cada vez que você ligasse.

As entradas do LCD, ao contrário, ficam em alta impedância até o programa
começar — não puxam para lado nenhum. Os resistores que já estão na placa
seguram o nível que o boot precisa. Por isso o LCD é que fica nos pinos
delicados, e o rádio num pino comum.

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
| LCD RS | **D8** | 15 | pino de boot, precisa de nível baixo |
| LCD E | **D3** | 0 | pino de boot, precisa de nível alto |
| LCD D4 | **D4** | 2 | pino de boot; é também o LED da placa, que vai piscar |
| LCD D5 | **D5** | 14 | |
| LCD D6 | **D6** | 12 | |
| LCD D7 | **D7** | 13 | |
| DATA do rádio | **D2** | 4 | **atrás do divisor**, nunca direto |
| Chave de limpar | **D1** | 5 | outro terminal no `G` |
| LED vermelho | **D0** | 16 | com resistor de 220 Ω |
| 5 V do LCD e do rádio | **VU** | — | o 5 V da USB |
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
| Tela com lixo ou blocos, contraste bem ajustado | os 3,3 V do ESP estão no limite para o LCD: veja o truque do diodo acima |
| LCD apagado e o `3V3` foi usado | o LCD precisa do `VU`; em 3,3 V ele não funciona direito |
| A bolinha da página nunca fica verde | o tópico da página e o do `segredos.h` estão diferentes |
| Página verde mas nenhuma letra | o problema é o rádio, não a internet — teste o transmissor pelo serial |
| Faltam letras que a versão com Uno pegava | WiFi disputando com o rádio: suba `REPETICOES` para 5 no transmissor |
| `WiFi` conecta e cai o tempo todo | alimentação; o ESP puxa picos de corrente ao transmitir |
| O LED da placa pisca sozinho ao escrever no LCD | é normal: GPIO2 é ao mesmo tempo o LED da placa e uma linha de dados do LCD |
