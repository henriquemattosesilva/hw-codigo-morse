/*
  TESTE DO ENLACE DE RADIO NO ESP8266 (NodeMCU)

  Nao faz parte do telegrafo. E o espelho do teste-radio-uno, do outro lado do
  enlace, para responder uma pergunta so: o WiFi atrapalha a recepcao?

  O teste-radio-uno ja provou que o transmissor, os modulos e as antenas
  funcionam. O que sobra e o lado do ESP, e ali ha duas suspeitas empilhadas:
  o divisor de tensao e a disputa entre o WiFi e a amostragem do radio.

  Este sketch as separa no tempo, num log so:

      FASE 1  os primeiros 20 segundos, com o WiFi DESLIGADO
      FASE 2  dali em diante, com o WiFi LIGADO

  Bata no manipulador durante as duas.

  A RH_ASK amostra o pino 8 vezes por bit -- 16 000 vezes por segundo a
  2000 bps -- por uma interrupcao de timer0. A pilha WiFi desabilita
  interrupcao em rajadas, e cada rajada perdida desalinha a amostragem.

  ATENCAO AO LER "boas" E "mas". O _rxBad da RH_ASK so conta DEPOIS que ela
  reconheceu o simbolo de inicio do quadro: ou o CRC falhou no fim, ou o byte
  de tamanho veio absurdo. Se a amostragem estiver tao torta que o inicio
  nunca e reconhecido, as duas contagens ficam em zero -- exatamente como se
  nao chegasse sinal nenhum. Por isso "boas: 0  mas: 0" NAO prova que o fio
  esta morto.

  Quem separa isso e o "transicoes": uma contagem de bordas lidas direto do
  pino, fora da RH_ASK, numa janela de 20 ms. O receptor AM entrega ruido
  quando nao ha transmissao, entao um pino vivo transiciona muito, sempre.

      transicoes perto de zero     o fio esta morto: divisor, pino errado,
                                   alimentacao do modulo ou mau contato
      transicoes altas, boas em 0  o sinal chega e a decodificacao falha:
                                   e problema de tempo, nao de eletricidade
      boas subindo nas duas fases  o radio esta bem; o problema esta no
                                   sketch do receptor, nao aqui
      boas subindo so na fase 1    e o WiFi comendo as interrupcoes

  Na fase 2 ele reconecta com WiFi.begin() sem argumentos, que reaproveita a
  rede gravada na flash pelo receptor de verdade. Por isso este sketch nao
  precisa do segredos.h. Se aparecer "wifi: nao" no balanco, e porque nao ha
  credencial gravada -- grave o receptor uma vez e volte aqui.

  MONTAGEM: a mesma do receptor, e so o radio precisa estar ligado.

      DATA do modulo -> 10k -> no do D2 -> 10k -> 10k -> G
      VCC do modulo  -> VU        (o 5V da USB, nao o 3V3)
      GND do modulo  -> G
      ANT            -> fio reto de 17,3 cm

  Placa: NodeMCU 1.0 (ESP-12E Module). Serial a 115200.
*/

#include <ESP8266WiFi.h>
#include <RH_ASK.h>

const uint8_t PINO_RADIO = 4;  // D2, atras do divisor -- igual ao receptor

// 0xff para transmissao e PTT: este lado so escuta.
RH_ASK radio(2000, PINO_RADIO, 0xff, 0xff);

const uint16_t BALANCO_MS  = 5000;
const uint32_t FASE1_MS    = 20000;  // quanto tempo com o WiFi desligado

unsigned long tBalanco = 0;
uint16_t recebidos = 0;
uint16_t naFase1 = 0, naFase2 = 0;
bool wifiLigado = false;

void setup() {
  Serial.begin(115200);
  Serial.println();
  Serial.println(F("Teste do enlace de radio no ESP8266 - 2000 bps, D2"));

  // O ESP8266 reconecta sozinho na rede gravada, mesmo sem WiFi.begin().
  // Para a fase 1 valer alguma coisa, o radio tem de estar mesmo desligado.
  WiFi.persistent(false);   // nao apaga a credencial gravada na flash
  WiFi.disconnect(false);
  WiFi.mode(WIFI_OFF);
  WiFi.forceSleepBegin();
  delay(100);

  if (!radio.init()) {
    Serial.println(F("ERRO: radio nao iniciou"));
    while (true) { delay(1000); }
  }

  Serial.println(F("FASE 1: WiFi DESLIGADO por 20s. Bata no manipulador."));
  tBalanco = millis();
}

/*
  Conta bordas no pino do radio numa janela curta, lendo direto, sem passar
  pela RH_ASK. E a unica medida deste sketch que diz se chega ALGUMA coisa
  eletricamente, independente de a biblioteca conseguir decodificar.

  Um pino vivo transiciona aos milhares: o receptor AM abre o ganho quando
  nao ha transmissao e entrega ruido. Um pino parado significa fio morto.
*/
uint32_t contaTransicoes(uint16_t ms) {
  uint32_t n = 0;
  int ultimo = digitalRead(PINO_RADIO);
  unsigned long fim = millis() + ms;
  while ((long)(millis() - fim) < 0) {
    int nivel = digitalRead(PINO_RADIO);
    if (nivel != ultimo) { n++; ultimo = nivel; }
  }
  return n;
}

void loop() {
  unsigned long agora = millis();

  if (!wifiLigado && agora >= FASE1_MS) {
    wifiLigado = true;
    Serial.println(F("---- FASE 2: ligando o WiFi. Continue batendo. ----"));
    WiFi.forceSleepWake();
    delay(100);
    WiFi.mode(WIFI_STA);
    WiFi.begin();  // reaproveita a rede gravada na flash
  }

  uint8_t buffer[RH_ASK_MAX_MESSAGE_LEN];
  uint8_t tamanho = sizeof(buffer);

  if (radio.recv(buffer, &tamanho)) {
    recebidos++;
    if (wifiLigado) naFase2++; else naFase1++;

    Serial.print(wifiLigado ? F("[2] ") : F("[1] "));
    for (uint8_t i = 0; i < tamanho; i++) {
      if (buffer[i] < 0x10) Serial.print('0');
      Serial.print(buffer[i], HEX);
      Serial.print(' ');
    }
    if (tamanho == 3 && buffer[0] == 'M') {
      Serial.print(F(" -> letra '"));
      Serial.print(buffer[2] == ' ' ? '_' : (char)buffer[2]);
      Serial.print(F("', sequencia "));
      Serial.print(buffer[1]);
    } else {
      Serial.print(F(" -> nao e do telegrafo"));
    }
    Serial.println();
  }

  if (agora - tBalanco >= BALANCO_MS) {
    tBalanco = agora;
    Serial.print(F("[balanco] fase "));
    Serial.print(wifiLigado ? 2 : 1);
    Serial.print(F("   wifi: "));
    Serial.print(wifiLigado ? (WiFi.status() == WL_CONNECTED ? "sim" : "nao") : "off");
    Serial.print(F("   sem wifi: "));
    Serial.print(naFase1);
    Serial.print(F("   com wifi: "));
    Serial.print(naFase2);
    Serial.print(F("   boas: "));
    Serial.print(radio.rxGood());
    Serial.print(F("   mas: "));
    Serial.print(radio.rxBad());
    Serial.print(F("   transicoes/20ms: "));
    Serial.println(contaTransicoes(20));
  }
}
