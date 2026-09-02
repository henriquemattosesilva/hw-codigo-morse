/*
  TELEGRAFO SEM FIO - TRANSMISSOR, VERSAO PARA O TINKERCAD

  Mesma logica do transmissor-nano.ino. So muda o que o simulador nao tem:

    Arduino Nano      -> Arduino Uno R3 (o Tinkercad nao tem Nano; os pinos
                         que este projeto usa sao iguais nas duas placas)
    modulo RF 433MHz  -> um fio de D12 desta placa ate D11 da outra
    biblioteca RadioHead -> SoftwareSerial (o Tinkercad so aceita as oficiais)
    buzzer ativo      -> Piezo, que e passivo: precisa de tone(), porque um
                         digitalWrite nele daria um clique, nao um apito

  IMPORTANTE: ligue tambem o GND de uma placa no GND da outra. Sem terra em
  comum as duas nao tem referencia de tensao e o link nao funciona. E o erro
  mais comum ao ligar dois Arduinos.

  Placa: Arduino Uno R3.
*/

#include <SoftwareSerial.h>

// ---------------------------------------------------------------- pinos
const uint8_t PINO_BOTAO  = 2;   // chave tactil, outro terminal no GND
const uint8_t PINO_PONTO  = 3;   // LED verde 1 + resistor 220R
const uint8_t PINO_BUZZER = 4;   // piezo
const uint8_t PINO_TRACO  = 5;   // LED verde 2 + resistor 220R
const uint8_t PINO_ESPACO = 6;   // LED azul    + resistor 220R
const uint8_t PINO_POT    = A0;  // potenciometro 10K, velocidade

SoftwareSerial radio(11, 12);    // RX em D11 (sem uso aqui), TX em D12

// ------------------------------------------------------------- constantes
const uint16_t UNIDADE_LENTA  = 250;
const uint16_t UNIDADE_RAPIDA = 60;
const uint8_t  DEBOUNCE_MS    = 25;
const uint8_t  MAX_SIMBOLOS   = 6;
const uint16_t TOM_SIDETONE   = 620;  // Hz do apito no piezo
const uint16_t PISCA_MS       = 80;

/*
  No projeto de verdade cada letra vai tres vezes ao ar, porque o 433MHz AM
  perde pacotes e nao ha canal de retorno. Aqui e um fio: nao perde byte
  nenhum, entao uma copia basta.
*/
const uint8_t REPETICOES = 1;

const char ARVORE_MORSE[] PROGMEM =
  "*ETIANMSURWDKGOHVF*L*PJBXCYZQ**54*3***2*******16*******7***8*90";
const uint8_t ULTIMO_NO = 62;

// ----------------------------------------------------------------- estado
char     simbolos[MAX_SIMBOLOS + 1];
uint8_t  nSimbolos = 0;

bool     pressionado = false;
unsigned long tTransicao = 0, tInicio = 0, tSoltura = 0;

bool     aguardandoEspaco = false;
uint16_t unidade = 120;
uint8_t  sequencia = 0;

uint8_t  piscaRestante = 0;
unsigned long tPisca = 0;

// ------------------------------------------------------------------ setup
void setup() {
  pinMode(PINO_BOTAO, INPUT_PULLUP);
  pinMode(PINO_PONTO, OUTPUT);
  pinMode(PINO_TRACO, OUTPUT);
  pinMode(PINO_ESPACO, OUTPUT);
  pinMode(PINO_BUZZER, OUTPUT);

  Serial.begin(9600);
  radio.begin(9600);
  Serial.println(F("Telegrafo - transmissor (Tinkercad)"));

  testeInicial();
  unidade = leVelocidade();
  simbolos[0] = '\0';
  tSoltura = millis();
}

void testeInicial() {
  const uint8_t leds[3] = { PINO_PONTO, PINO_TRACO, PINO_ESPACO };
  for (uint8_t i = 0; i < 3; i++) {
    digitalWrite(leds[i], HIGH); delay(150); digitalWrite(leds[i], LOW);
  }
  tone(PINO_BUZZER, TOM_SIDETONE); delay(80); noTone(PINO_BUZZER);
}

// ------------------------------------------------------------------- loop
void loop() {
  unsigned long agora = millis();
  bool nivel = (digitalRead(PINO_BOTAO) == LOW);

  if (nivel != pressionado && (agora - tTransicao) >= DEBOUNCE_MS) {
    tTransicao = agora;
    pressionado = nivel;
    if (pressionado) inicioDoToque(agora);
    else             fimDoToque(agora);
  }

  if (pressionado) {
    if (agora - tInicio >= 2UL * unidade) digitalWrite(PINO_TRACO, HIGH);
  } else {
    unsigned long silencio = agora - tSoltura;
    if (nSimbolos > 0 && silencio >= 3UL * unidade) {
      fechaLetra();
    } else if (nSimbolos == 0 && aguardandoEspaco && silencio >= 7UL * unidade) {
      enviaCaractere(' ');
      Serial.println(F("[espaco]"));
      aguardandoEspaco = false;
      piscaRestante = 4;
      tPisca = agora;
      digitalWrite(PINO_ESPACO, LOW);
    }
    if (nSimbolos == 0 && !aguardandoEspaco) unidade = leVelocidade();
  }

  atualizaPisca(agora);
}

// ------------------------------------------------------------ manipulador
void inicioDoToque(unsigned long agora) {
  tInicio = agora;
  digitalWrite(PINO_PONTO, HIGH);
  digitalWrite(PINO_TRACO, LOW);
  digitalWrite(PINO_ESPACO, LOW);
  tone(PINO_BUZZER, TOM_SIDETONE);
  piscaRestante = 0;
  aguardandoEspaco = false;
}

void fimDoToque(unsigned long agora) {
  unsigned long duracao = agora - tInicio;
  tSoltura = agora;
  digitalWrite(PINO_PONTO, LOW);
  digitalWrite(PINO_TRACO, LOW);
  noTone(PINO_BUZZER);
  registraSimbolo(duracao >= 2UL * unidade ? '-' : '.');
}

void registraSimbolo(char s) {
  if (nSimbolos >= MAX_SIMBOLOS) {
    Serial.println(F("simbolos demais = ?"));
    enviaCaractere('?');
    nSimbolos = 0;
    simbolos[0] = '\0';
    aguardandoEspaco = true;
    digitalWrite(PINO_ESPACO, HIGH);
    return;
  }
  simbolos[nSimbolos++] = s;
  simbolos[nSimbolos] = '\0';
}

void fechaLetra() {
  char c = decodifica(simbolos);
  Serial.print(simbolos); Serial.print(F(" = ")); Serial.println(c);
  enviaCaractere(c);
  nSimbolos = 0;
  simbolos[0] = '\0';
  aguardandoEspaco = true;
  digitalWrite(PINO_ESPACO, HIGH);
}

char decodifica(const char *s) {
  uint8_t no = 0;
  for (uint8_t i = 0; s[i] != '\0'; i++) {
    no = (s[i] == '.') ? (2 * no + 1) : (2 * no + 2);
    if (no > ULTIMO_NO) return '?';
  }
  char c = (char)pgm_read_byte(&ARVORE_MORSE[no]);
  return (c == '*') ? '?' : c;
}

// ------------------------------------------------------------------ link
void enviaCaractere(char c) {
  sequencia++;
  // Mesmo pacote do projeto real: marca, sequencia e o caractere. A marca
  // deixa o receptor reencontrar o inicio do pacote se os bytes saírem de
  // sincronia.
  for (uint8_t i = 0; i < REPETICOES; i++) {
    radio.write('M');
    radio.write(sequencia);
    radio.write((uint8_t)c);
  }
}

// ------------------------------------------------------------------ apoio
void atualizaPisca(unsigned long agora) {
  if (piscaRestante == 0) return;
  if (agora - tPisca < PISCA_MS) return;
  tPisca = agora;
  piscaRestante--;
  digitalWrite(PINO_ESPACO, (piscaRestante % 2) == 1 ? HIGH : LOW);
}

uint16_t leVelocidade() {
  return (uint16_t)map(analogRead(PINO_POT), 0, 1023, UNIDADE_LENTA, UNIDADE_RAPIDA);
}
