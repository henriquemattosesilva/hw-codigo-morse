# hw-codigo-morse — telégrafo sem fio em morse

Manipulador de morse com um botão no Arduino Nano, rádio 433 MHz, display LCD 16x2 no
Arduino Uno. Repositório público em `https://github.com/henriquemattosesilva/hw-codigo-morse`,
página em `https://henriquemattosesilva.github.io/hw-codigo-morse/`.

Este arquivo é o documento vivo do projeto. O `README.md` e o `MONTAGEM.md` explicam o
projeto para quem vai montar; aqui ficam as decisões, o estado e o que ainda não foi
verificado.

> Para este arquivo ser carregado automaticamente, abra a sessão **dentro desta pasta**.
> Começando em `c:\HENRIQUE\Claude` ele não entra no contexto sozinho.

---

## Estado em 31/08/2026

Nada foi montado ainda. Tudo o que existe é código e documentação, e o que foi verificado
foi verificado sem hardware.

| Item | Situação |
|---|---|
| `transmissor-nano.ino` | compila para `arduino:avr:nano` — 27% de flash, 30% de RAM |
| `receptor-uno.ino` | compila para `arduino:avr:uno` — 27% de flash, 32% de RAM |
| `tinkercad/tx-tinkercad.ino` | compila para `arduino:avr:uno` — 17% de flash, 17% de RAM |
| `tinkercad/rx-tinkercad.ino` | compila para `arduino:avr:uno` — 15% de flash, 18% de RAM |
| Árvore de morse | os 36 caracteres testados nos dois sentidos contra a tabela ITU, 0 erro |
| `receptor-esp8266.ino` | compila para `esp8266:esp8266:nodemcuv2` — 24% de flash, 36% de RAM, **IRAM em 93%** |
| `ao-vivo/index.html` | testado de ponta a ponta contra o broker real: retidas, letras ao vivo e queda do telégrafo |
| `index.html` | renderização conferida por CDP: sem estouro em 390 e 1440 px, 0 erro de console |
| **Montagem física** | **não feita** |

**A próxima etapa é o Henrique montar na protoboard e testar.** Ele avisou que faria isso
em outro momento.

---

## O que ainda não foi testado, e pode estar errado

Esta é a parte que importa quando a montagem acontecer. Nada abaixo foi comprovado no
hardware — são decisões tomadas na leitura de datasheet e no raciocínio.

**O buzzer é acionado por nível alto?** O código assume que sim (`digitalWrite HIGH` liga).
Vários módulos de buzzer ativo são acionados por nível baixo. Se ele apitar parado e calar
ao apertar, é só inverter os `HIGH`/`LOW` de `PINO_BUZZER`. Está no guia de problemas.

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

**Os 25 ms de debounce servem para as chaves dele?** Chave táctil comum costuma repicar
menos que isso. Se registrar toques em dobro, sobe para 40.

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

**A faixa de 60 a 250 ms por unidade é confortável?** Chutada para cobrir de iniciante a
razoavelmente rápido. Depois de bater morse de verdade ele vai saber se quer outra faixa.

---

## Regra que não pode ser esquecida: o `index.html` é gerado

**Nunca editar `index.html` à mão.** Ele é montado por script a partir do modelo, dos
diagramas e dos `.ino`. Editar direto significa perder a alteração no próximo gerador.

```
python ferramentas/gerar-diagramas.py   # só se mudou a fiação real
python ferramentas/gerar-tinkercad.py   # só se mudou a montagem do simulador
python ferramentas/gerar-pagina.py      # sempre, depois de mexer em qualquer sketch
```

O `gerar-pagina.py` injeta os quatro `.ino` e os sete SVGs em `ferramentas/modelo.html` e
em `ferramentas/secao-tinkercad.html`. **Se você mexer num sketch e não rodar o gerador, a
página passa a mostrar um código diferente do que está no repositório** — que é
exatamente o jeito mais fácil de uma página dessas apodrecer.

O `.gitattributes` fixa LF, então regerar a página não produz diff falso em máquina com
outra configuração de `core.autocrlf`.

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

---

## A versão do Tinkercad

Existe porque o simulador não tem Arduino Nano, não tem módulo de rádio 433 MHz e não
aceita biblioteca externa. Fica em `tinkercad/`, e as diferenças são:

- Uno R3 no lugar do Nano — os pinos deste projeto são iguais nas duas placas
- um fio de D12 a D11 no lugar dos dois módulos, **mais o GND em comum entre as placas**
- `SoftwareSerial` no lugar da `RadioHead`, nos mesmos pinos
- `tone()` no lugar de `digitalWrite` no buzzer: o piezo do Tinkercad é passivo
- uma repetição por letra em vez de três, porque um fio não perde byte
- o receptor procura a marca `'M'` para achar o início do pacote, que era o que o preâmbulo
  da `RadioHead` fazia

Isso **não** substitui o teste na bancada: o simulador não reproduz alcance, ruído de
433 MHz, perda de pacote, repique de chave nem o comportamento real do módulo de rádio.

---

## Como verificar

**Compilar.** O `arduino-cli` foi baixado para o scratchpad da sessão de 31/08/2026, que
**não existe mais**. Para compilar de novo, baixar outra vez:

```
curl -sSL -o acli.zip https://downloads.arduino.cc/arduino-cli/arduino-cli_latest_Windows_64bit.zip
arduino-cli core install arduino:avr
arduino-cli compile -b arduino:avr:nano transmissor-nano
arduino-cli compile -b arduino:avr:uno  receptor-uno
```

As bibliotecas **já estão instaladas** e persistem: `RadioHead` 1.143.1 e `LiquidCrystal`
1.0.7, em `C:\Users\henri\Documents\Arduino\libraries`. Não precisa reinstalar.

**A tabela de morse.** O teste que compara os 36 caracteres nos dois sentidos contra a
tabela ITU não foi guardado no repositório. Se mexer na árvore, vale reescrever: é curto e
pega inversão de ponto com traço na hora.

**A página.** Conferir a renderização de verdade pelo Chrome via DevTools Protocol — ver a
memória `verificacao-visual-cdp`. O que vale medir: `scrollWidth` contra `clientWidth` em
390 e 1440 px, erros de console, e o manipulador do navegador respondendo a
`Input.dispatchKeyEvent` com os tempos de um ponto e de um traço.

---

## Quando a montagem for feita

O `MONTAGEM.md` manda montar o transmissor inteiro e testar pelo monitor serial **antes** de
encostar no receptor. Vale seguir: separa o problema de manipulação do problema de rádio.

Conforme ele for testando, o que aparecer de diferente do previsto deve voltar para os
documentos — principalmente para a tabela **"Quando não funciona"** do `MONTAGEM.md` e da
página, que hoje é feita de causas prováveis e não de causas observadas. Cada sintoma real
que ele encontrar vale mais do que os que estão lá.

E atualizar a seção "o que ainda não foi testado" deste arquivo: os itens que passarem
saem da lista.
