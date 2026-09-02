/*
  TESTE DO ENLACE DE RADIO (Arduino Uno)

  Nao faz parte do telegrafo. E uma ferramenta de bancada para responder uma
  pergunta so: o radio de 433MHz esta chegando?

  Ele tira do caminho tudo o que nao e radio -- WiFi, LCD, divisor de tensao,
  3,3V -- e escuta com o Uno, que e 5V nativo como os modulos. Se as letras
  aparecerem aqui e nao aparecerem no ESP8266, o problema esta no lado do ESP.
  Se nao aparecerem nem aqui, o problema esta nos modulos, na fiacao ou nas
  antenas.

  MONTAGEM (so isto, mais nada):

      modulo receptor 433MHz        Arduino Uno
      ----------------------        -----------
      VCC                     ->    5V
      GND                     ->    GND
      DATA (qualquer um dos 2) ->   D11
      ANT                     ->    fio reto de 17,3 cm

  Deixe D10 e D12 vazios: a RH_ASK reserva os tres.

  A CADA 5 SEGUNDOS ele imprime um balanco. As duas contagens do fim sao o
  que mais interessa:

      boas  pacotes que passaram no CRC
      mas   pacotes que chegaram e falharam no CRC

  "mas" subindo com "boas" em zero significa que ha sinal chegando mas
  corrompido -- antena, alcance ou ruido. As duas em zero significa que nao
  chega nada: confira a serigrafia do modulo, a alimentacao e se o
  transmissor esta mesmo transmitindo.

  Biblioteca: RadioHead (Mike McCauley).
  Placa: Arduino Uno.
*/

#include <RH_ASK.h>
#include <SPI.h>  // a RadioHead nao usa SPI aqui, mas exige o include

RH_ASK radio;  // 2000 bps, RX em D11 -- os mesmos do receptor de verdade

const uint16_t BALANCO_MS = 5000;

unsigned long tBalanco = 0;
uint16_t recebidos = 0;

void setup() {
  Serial.begin(9600);
  Serial.println(F("Teste do enlace de radio - 2000 bps, RX em D11"));

  if (!radio.init()) {
    Serial.println(F("ERRO: radio nao iniciou"));
    while (true) {}
  }

  Serial.println(F("escutando. bata no manipulador do transmissor."));
  tBalanco = millis();
}

void loop() {
  uint8_t buffer[RH_ASK_MAX_MESSAGE_LEN];
  uint8_t tamanho = sizeof(buffer);

  if (radio.recv(buffer, &tamanho)) {
    recebidos++;
    Serial.print(F("pacote de "));
    Serial.print(tamanho);
    Serial.print(F(" bytes: "));

    // Byte a byte em hexa, e depois a leitura do que o telegrafo mandaria.
    for (uint8_t i = 0; i < tamanho; i++) {
      if (buffer[i] < 0x10) Serial.print('0');
      Serial.print(buffer[i], HEX);
      Serial.print(' ');
    }

    if (tamanho == 3 && buffer[0] == 'M') {
      Serial.print(F("  -> letra '"));
      Serial.print(buffer[2] == ' ' ? '_' : (char)buffer[2]);
      Serial.print(F("', sequencia "));
      Serial.print(buffer[1]);
    } else {
      Serial.print(F("  -> nao e do telegrafo"));
    }
    Serial.println();
  }

  unsigned long agora = millis();
  if (agora - tBalanco >= BALANCO_MS) {
    tBalanco = agora;
    Serial.print(F("[balanco] recebidos: "));
    Serial.print(recebidos);
    Serial.print(F("   boas: "));
    Serial.print(radio.rxGood());
    Serial.print(F("   mas: "));
    Serial.println(radio.rxBad());
  }
}
