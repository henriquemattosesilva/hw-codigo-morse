# hw-codigo-morse — telégrafo sem fio em morse

Manipulador de morse com um botão no Arduino Nano transmitindo por rádio 433 MHz. O
receptor mostra a mensagem num LCD 16x2 e pode ser **uma de duas placas**: um Arduino Uno,
mais simples, ou um ESP8266, que além do LCD publica a mensagem na internet.

- repositório público: `https://github.com/henriquemattosesilva/hw-codigo-morse`
- página do projeto: `https://henriquemattosesilva.github.io/hw-codigo-morse/`
- monitor ao vivo: `https://henriquemattosesilva.github.io/hw-codigo-morse/ao-vivo/`

Este arquivo é o documento vivo do projeto. O `README.md` e o `MONTAGEM.md` explicam o
projeto para quem vai montar; aqui ficam as decisões, o estado e o que ainda não foi
verificado.

> Para este arquivo ser carregado automaticamente, abra a sessão **dentro desta pasta**.
> Começando em `c:\HENRIQUE\Claude` ele não entra no contexto sozinho.

---

## Estado em 01/09/2026

O transmissor **já está montado e funcionando na bancada**. O receptor com ESP8266 está
montado mas ainda não foi gravado. O receptor com Uno não foi montado.

| Item | Situação |
|---|---|
| `transmissor-nano.ino` | compila para `arduino:avr:nano` — 27% de flash, 30% de RAM |
| `receptor-uno.ino` | compila para `arduino:avr:uno` — 27% de flash, 32% de RAM |
| Árvore de morse | os 36 caracteres testados nos dois sentidos contra a tabela ITU, 0 erro |
| `receptor-esp8266.ino` | compila para `esp8266:esp8266:nodemcuv2` — 24% de flash, 36% de RAM, **IRAM em 93%** |
| `ao-vivo/index.html` | testado de ponta a ponta contra o broker real: retidas, letras ao vivo e queda do telégrafo |
| `index.html` | renderização conferida por CDP: sem estouro em 390 e 1440 px, 0 erro de console |
| **Transmissor na protoboard** | **funcionando** — grava e o serial decodifica certo |
| **Receptor ESP8266 na protoboard** | montado, ainda não gravado |
| **Receptor Uno** | não montado |

### O que o hardware já provou (01/09/2026)

O Nano grava e o manipulador funciona. No monitor serial, com o potenciômetro no extremo
lento, saiu:

```
Telegrafo - transmissor
unidade: 250ms
. = E
[espaco]
- = T
```

Isso comprova de uma vez o debounce, o limiar de 2 unidades entre ponto e traço, o
fechamento de letra em 3 unidades, o espaço em 7 e a descida na árvore de morse. `E` e `T`
são os dois nós mais rasos, então prova o caminho, não a árvore inteira — essa já tinha
sido testada em software contra a tabela ITU.

**Para gravar o Nano é preciso Tools → Processor → _ATmega328P (Old Bootloader)_.** Sem
isso o avrdude dá `not in sync: resp=0x00` dez vezes. O clone dele fala a 57600 bauds e o
IDE tenta 115200. Já está na tabela de problemas.

**O `[espaco]` entre cada letra não é defeito.** A 250 ms por unidade o espaço de palavra
são 1,75 s, e quem testa letra por letra pensa mais que isso entre uma e outra.

**A próxima etapa é gravar o ESP8266.**

### O que existe

```
transmissor-nano/     o manipulador. É sempre esta placa que transmite.
receptor-uno/         receptor simples, só LCD
receptor-esp8266/     receptor com WiFi: LCD + publica por MQTT
  segredos-exemplo.h  modelo; o segredos.h de verdade está no .gitignore
ao-vivo/index.html    o monitor ao vivo, publicado no GitHub Pages
MONTAGEM.md           fiação do Nano e do receptor com Uno
MONTAGEM-ESP8266.md   fiação do receptor com ESP8266, com o divisor
ferramentas/          modelo.html, secao-esp8266.html e os dois geradores
index.html            GERADO. Nunca editar à mão.
```

O suporte ao **Tinkercad foi removido em 01/09/2026** a pedido dele — seção, sketches
adaptados, gerador e diagramas. Está no histórico do git (`git revert cb1c707`) se um dia
voltar a fazer sentido. Não recriar sem ele pedir.

---

## O que ainda não foi testado, e pode estar errado

Esta é a parte que importa conforme a montagem avança. Nada abaixo foi comprovado no
hardware — são decisões tomadas na leitura de datasheet e no raciocínio. O que passar sai
daqui.

Saiu em 01/09/2026: o **debounce de 25 ms** e a **faixa de 60 a 250 ms**, que se
comportaram no manipulador real sem toque em dobro nem letra perdida. A faixa foi provada
só no extremo lento — ele ainda não girou o potenciômetro.

**O buzzer é mesmo ativo?** Ele tem só dois pinos, S e GND — sem VCC, quem o alimenta é o
próprio D4, então **não há como ele ser acionado por nível baixo**: nível alto é a única
forma de dar energia a ele. O que resta em aberto é se tem oscilador interno. Se der um
clique em vez de apitar, é passivo, e aí é `tone()` em vez de `digitalWrite`. Está no
guia de problemas.

**Os 20 a 30 mA do buzzer no D4 incomodam?** Com dois pinos, o pino alimenta o buzzer
inteiro. O ATmega328 recomenda 20 mA por pino e admite 40 mA no limite absoluto, então
está no teto do recomendado. Funciona, mas se ele quiser poupar o pino, um C945 com
10 kΩ na base resolve.

**A serigrafia dos módulos RF bate com o assumido?** O transmissor foi assumido como
`DATA / VCC / GND` e o receptor como `VCC / DATA / DATA / GND`. Existem versões com a ordem
invertida. Conferir na plaquinha antes de ligar.

**A `RH_ASK` e a `LiquidCrystal` convivem no Uno sem perder pacote?** A `RH_ASK` roda numa
interrupção de Timer1 a 16 kHz e as escritas no LCD são lentas. O raciocínio foi que
`delayMicroseconds` não desabilita interrupção, então a ISR continua rodando e nada se
perde — mas isso nunca foi medido. Se aparecerem letras faltando com o LCD atualizando,
é aqui que se olha primeiro. O receptor já só redesenha quando algo muda, justamente por
causa disso.

**Três repetições por letra são suficientes?** Escolhido no chute educado. Se o ambiente
dele tiver muito ruído de 433 MHz, `REPETICOES` sobe para 5. Se sobrar folga, pode descer.

**O LCD aceita sinais de 3,3 V do ESP8266 com VDD em 5 V?** Pela folha de dados o
HD44780 quer 3,5 V para nível alto. A maioria dos módulos aceita 3,3 V, mas o dele pode
não aceitar. Se der lixo na tela, a saída é derrubar o VDD com um diodo — ou com a junção
base-emissor de um C945, que ele tem dez.

**O `VU` da NodeMCU v3 dele entrega mesmo 5 V?** É o padrão dessa placa, mas há clones em
que o `VU` não está ligado. Se o LCD não acender, é o primeiro a conferir.

**Quanto o WiFi come de pacote de rádio?** A `RH_ASK` amostra o pino por timer0 e a pilha
WiFi desliga interrupção de vez em quando. Não foi medido. Se faltar letra que a versão
com Uno pegava, subir `REPETICOES` para 5.

**A IRAM do ESP8266 está em 93%.** Compila com folga de 4 KB. Outra biblioteca com código
em IRAM pode não caber — se der erro de link falando em IRAM, é isso.

---

## Regra que não pode ser esquecida: o `index.html` é gerado

**Nunca editar `index.html` à mão.** Ele é montado por script a partir do modelo, dos
diagramas e dos `.ino`. Editar direto significa perder a alteração no próximo gerador.

```
python ferramentas/gerar-diagramas.py   # só se mudou a fiação real
python ferramentas/gerar-pagina.py      # sempre, depois de mexer em qualquer sketch
```

O `gerar-pagina.py` injeta os três `.ino` e os seis SVGs em `ferramentas/modelo.html` e
em `ferramentas/secao-esp8266.html`. **Se você mexer num sketch e não rodar o gerador, a
página passa a mostrar um código diferente do que está no repositório** — que é
exatamente o jeito mais fácil de uma página dessas apodrecer.

O `.gitattributes` fixa LF, então regerar a página não produz diff falso em máquina com
outra configuração de `core.autocrlf`.

### Como a página está organizada

Cinco seções: componentes, montagem, como funciona, melhorias e o guia de problemas.

A **montagem tem três abas**, uma por placa — `m-nano`, `m-uno` e `m-esp` — e cada uma
termina com o código daquela placa dentro de um `<details class="dobra">`, fechado por
padrão. **Não existe seção de código separada**: cada sketch mora junto da fiação a que
pertence. O bloco do ESP vem de `ferramentas/secao-esp8266.html` e é injetado dentro da
aba `m-esp`.

Duas armadilhas ao mexer nisso:

- **Link para dentro de uma aba.** O README aponta para `#esp8266`, que fica num painel
  escondido. A função `abreAbaDoAlvo()` no script da página abre a aba antes de rolar. Sem
  ela o navegador fica parado onde está, sem erro nenhum. Vale na carga e no `hashchange`.
- **A numeração em morse das seções.** Cada `<p class="marca">` traz o número da seção em
  morse (1 = `·−−−−`, 2 = `··−−−`, 3 = `···−−`, 4 = `····−`, 5 = `·····`). Acrescentar ou
  remover uma seção obriga a renumerar as de baixo, à mão.

**Publicar no GitHub a cada entrega, sem perguntar** (é o padrão dos projetos `hw-`).
O Pages leva de um a três minutos para refletir o push.

---

## Decisões que não devem ser desfeitas

Cada uma resolve um problema concreto. Desfazer sem saber disso reintroduz o problema.

**A letra é decodificada no transmissor; pelo ar vai ASCII, não pulso.** Mandar os pontos e
traços crus seria mais fiel a um telégrafo, mas o 433 AM perde pulsos curtos com
facilidade e as letras chegariam erradas. Decodificando antes, uma interferência ou some
com a letra inteira ou não a afeta — ela nunca vira outra letra.

**Os dois sketches compartilham a mesma árvore binária de 63 bytes.** O transmissor desce a
árvore (ponto = `2i+1`, traço = `2i+2`); o receptor acha a letra e sobe pelos pais
(`(i-1)/2`, com `(i-1)%2` dizendo se foi ponto ou traço). Uma tabela só, nos dois lados,
sem como divergir. Não trocar por duas tabelas de string.

**As repetições do pacote saem uma por volta do loop, em `bombeiaRadio()`.** `RH_ASK::send()`
chama `waitPacketSent()` internamente, então mandar as três cópias em sequência travaria o
Nano por uns 200 ms a cada letra. Na velocidade rápida um ponto dura 60 ms: o operador
perderia toques. O `bombeiaRadio()` só chama `send()` quando `radio.mode() != RHModeTx`.

**O pisca duplo do LED azul é máquina de estados, não `delay()`.** Um `delay(320)` cairia
bem no momento em que a próxima palavra pode começar.

**O potenciômetro só é lido com o manipulador parado.** Reler no meio de uma letra mudaria
os limiares entre o aperto e a soltura.

**Os LEDs acendem antes de soltar o botão, não depois.** Um verde no toque, o segundo ao
cruzar 2 unidades, azul ao cruzar 3 e piscando ao cruzar 7. É o ponto do projeto: mostrar os
tempos que normalmente são invisíveis, enquanto ainda dá para corrigir. Confirmar o
símbolo depois de solto não serviria para nada.

**O caminho até a internet usa três tópicos MQTT, com papéis diferentes.** A letra sai na
hora, em `.../letra`, e é ela que faz a página andar ao vivo. A mensagem inteira sai
represada, no máximo duas vezes por segundo, em `.../mensagem` e **retida** — retida
significa que o broker guarda a última, então quem abre a página depois já vê o texto que
está lá em vez de tela vazia. E `.../status` é a *última vontade* registrada no broker: se
o ESP perder energia ou WiFi, o próprio broker avisa a página. Publicar o texto todo a
cada letra encheria o broker sem deixar a tela mais rápida.

**O cliente MQTT da página é escrito à mão sobre WebSocket**, em vez de puxar a mqtt.js de
uma CDN. São poucos pacotes (CONNECT, SUBSCRIBE, PUBLISH, PINGREQ) e assim a página não
passa a depender de mais um servidor além do broker. O trecho que junta os quadros antes
de decodificar não é enfeite: um quadro de WebSocket pode trazer meio pacote MQTT ou três
inteiros.

**O tópico tem de bater em dois lugares:** `MQTT_TOPICO_BASE` no `segredos.h` e
`TOPICO_BASE` em `ao-vivo/index.html`. Divergindo, a página escuta um telégrafo que não é
o dele — e não aparece erro nenhum, simplesmente nunca chega nada. É o primeiro suspeito
quando a bolinha da página não fica verde.

**O número de sequência descarta as repetições no receptor**, para a letra aparecer uma vez
só. Ele começa em 1 no transmissor e `ultimaSequencia` começa em 0, então não colide.

---

## Restrições de pinos

A `RH_ASK` configura três pinos sozinha, mesmo os que o projeto não usa: **D10, D11 e D12**
nas duas placas. Em cada lado só um deles leva fio — D12 no Nano, D11 no Uno — e os outros
têm de ficar vazios. **D0 e D1 são a USB** e não podem ser usados em lado nenhum.

Nano: D2 botão, D3 LED verde 1, D4 buzzer, D5 LED verde 2, D6 LED azul, D12 rádio, A0 pot.
Uno: D2-D7 LCD (RS, E, D4-D7), D8 LED vermelho, D9 botão limpar, D11 rádio.

**No ESP8266 a regra é outra.** GPIO0 e GPIO2 precisam de nível alto no boot e GPIO15 de
nível baixo. O rádio **não** pode ir num desses: a saída dele é ruído aleatório sem
transmissão, e seria cara ou coroa a cada ligada. As entradas do LCD ficam em alta
impedância até o programa começar, então são elas que ocupam os pinos delicados.
ESP: D8/D3/D4/D5/D6/D7 no LCD, D2 rádio (atrás do divisor), D1 botão, D0 LED, VU o 5 V.

## Como verificar

**Compilar.** O `arduino-cli` foi baixado para o scratchpad da sessão de 31/08/2026, que
**não existe mais**. Para compilar de novo, baixar outra vez:

```
curl -sSL -o acli.zip https://downloads.arduino.cc/arduino-cli/arduino-cli_latest_Windows_64bit.zip
arduino-cli core install arduino:avr
arduino-cli compile -b arduino:avr:nano transmissor-nano
arduino-cli compile -b arduino:avr:uno  receptor-uno
arduino-cli compile -b esp8266:esp8266:nodemcuv2 receptor-esp8266
```

O core do ESP8266 vem de uma URL extra, que precisa ser registrada antes:
`arduino-cli config add board_manager.additional_urls https://arduino.esp8266.com/stable/package_esp8266com_index.json`

As bibliotecas **já estão instaladas** e persistem, em
`C:\Users\henri\Documents\Arduino\libraries`: `RadioHead` 1.143.1, `LiquidCrystal`
1.0.7 e `PubSubClient` 2.8.0. Não precisa reinstalar.

O `receptor-esp8266` **não compila sem `receptor-esp8266/segredos.h`**, que está no
.gitignore. Para compilar, criar um a partir do `segredos-exemplo.h` com valores
quaisquer — e não commitar.

**A tabela de morse.** O teste que compara os 36 caracteres nos dois sentidos contra a
tabela ITU não foi guardado no repositório. Se mexer na árvore, vale reescrever: é curto e
pega inversão de ponto com traço na hora.

**A página ao vivo, de ponta a ponta.** Dá para testar sem hardware nenhum: `npm i mqtt`
num diretório temporário, publicar no tópico com o cliente Node e conferir pelo CDP o que
a página mostrou. Foi assim que se validou o cliente MQTT escrito à mão. O que vale medir:
as mensagens retidas chegando **na assinatura** (publicar antes de abrir a página), as
letras ao vivo com o morse certo, e o `status` mudando quando o telégrafo "cai". Usar um
tópico próprio do teste — o broker é público — e apagar as retidas no fim, publicando
vazio com `retain`.

**A página do projeto.** Conferir a renderização de verdade pelo Chrome via DevTools Protocol — ver a
memória `verificacao-visual-cdp`. O que vale medir: `scrollWidth` contra `clientWidth` em
390 e 1440 px, erros de console, e o manipulador do navegador respondendo a
`Input.dispatchKeyEvent` com os tempos de um ponto e de um traço.

---

## Quando a montagem for feita

A ordem que os documentos mandam seguir, e que vale a pena respeitar porque cada passo
isola um problema:

1. ~~**O transmissor sozinho**, testado pelo monitor serial.~~ **Feito em 01/09/2026.**
2. **O receptor com Uno.** Prova o rádio sem envolver WiFi, 3,3 V nem divisor.
3. **Só então o ESP8266**, se ele quiser a parte de internet. E dentro dele: primeiro o
   LCD, depois o WiFi e a página (a bolinha fica verde sem nenhuma letra ter chegado), e
   só por último o rádio com o divisor.

Pular direto para o ESP junta quatro fontes de problema de uma vez.

Conforme ele for testando, o que aparecer de diferente do previsto deve voltar para os
documentos — principalmente para a tabela **"Quando não funciona"** do `MONTAGEM.md` e da
página, que hoje é feita de causas prováveis e não de causas observadas. Cada sintoma real
que ele encontrar vale mais do que os que estão lá.

E atualizar a seção "o que ainda não foi testado" deste arquivo: os itens que passarem
saem da lista.
