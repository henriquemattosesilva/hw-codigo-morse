/*
  TELEGRAFO SEM FIO - TRANSMISSOR (Arduino Nano)

  O botao e um manipulador de morse de verdade: toque curto vira ponto, toque
  longo vira traco, e as pausas separam letras e palavras. A letra fechada e
  decodificada aqui e sai pelo radio 433MHz ja como caractere ASCII.

  Os tres LEDs mostram os limiares de tempo do morse, que normalmente sao
  invisiveis, e acendem ANTES de voce soltar o botao:

      um verde aceso    -> o toque em curso ainda e um ponto
      os dois verdes    -> o toque ja passou de 2 unidades, virou traco
      azul aceso        -> silencio passou de 3 unidades, a letra foi enviada
      azul piscando 2x  -> silencio passou de 7 unidades, espaco enviado

  A unidade de tempo e fixa em UNIDADE, la embaixo. Para mudar o ritmo, troque
  esse numero e regrave. O buzzer apita junto com o toque, como sidetone.

  Biblioteca necessaria: RadioHead (Mike McCauley), no Library Manager.
  Placa: Arduino Nano, processador ATmega328P (Old Bootloader nos clones).
*/

#include <RH_ASK.h>
#include <SPI.h>  // a RadioHead nao usa SPI aqui, mas exige o include para compilar

// ---------------------------------------------------------------- pinos
const uint8_t PINO_BOTAO  = 2;   // chave tactil, outro terminal no GND
const uint8_t PINO_PONTO  = 3;   // LED verde 1 + resistor 220R
const uint8_t PINO_BUZZER = 4;   // buzzer ativo, so S e GND
const uint8_t PINO_TRACO  = 5;   // LED verde 2 + resistor 220R
const uint8_t PINO_ESPACO = 6;   // LED azul    + resistor 220R
// D12 e o DATA do modulo transmissor, padrao da RH_ASK no AVR.

// ------------------------------------------------------------- constantes
// A unidade de tempo do morse, em ms. Tudo o mais e multiplo dela: ponto 1,
// traco 3, pausa entre letras 3, entre palavras 7. Numero maior, morse mais
// lento. 250 e confortavel para aprender; abaixo de 100 ja e bem rapido.
const uint16_t UNIDADE        = 250;
const uint8_t  DEBOUNCE_MS    = 25;   // transicoes mais rapidas que isso sao ruido
const uint8_t  MAX_SIMBOLOS   = 6;    // pontos e tracos por letra
const uint8_t  REPETICOES     = 3;    // copias de cada caractere no ar
const uint16_t PISCA_MS       = 80;   // meio periodo do pisca do LED azul

/*
  Arvore binaria do morse, a mesma tabela usada pelo receptor.
  Comecando na raiz (indice 0), um ponto desce para 2i+1 e um traco para 2i+2.
  O '*' marca posicoes sem letra correspondente.
*/
const char ARVORE_MORSE[] PROGMEM =
  "*ETIANMSURWDKGOHVF*L*PJBXCYZQ**54*3***2*******16*******7***8*90";
const uint8_t ULTIMO_NO = 62;

RH_ASK radio;  // 2000 bps, TX em D12

// ----------------------------------------------------------------- estado
char     simbolos[MAX_SIMBOLOS + 1];  // pontos e tracos da letra em construcao
uint8_t  nSimbolos = 0;

bool     pressionado = false;
unsigned long tTransicao = 0;  // ultima borda aceita, para o debounce
unsigned long tInicio    = 0;  // inicio do toque atual
unsigned long tSoltura   = 0;  // fim do ultimo toque

bool     aguardandoEspaco = false;  // letra fechada, espaco de palavra ainda nao saiu
uint8_t  sequencia = 0;

uint8_t  piscaRestante = 0;
unsigned long tPisca = 0;

uint8_t  pacote[3];
uint8_t  repeticoesPendentes = 0;

// ------------------------------------------------------------------ setup
void setup() {
  pinMode(PINO_BOTAO, INPUT_PULLUP);
  pinMode(PINO_PONTO, OUTPUT);
  pinMode(PINO_TRACO, OUTPUT);
  pinMode(PINO_ESPACO, OUTPUT);
  pinMode(PINO_BUZZER, OUTPUT);

  Serial.begin(9600);
  Serial.println(F("Telegrafo - transmissor"));

  if (!radio.init()) {
    Serial.println(F("ERRO: radio nao iniciou"));
    while (true) {  // pisca os tres LEDs para sempre
      digitalWrite(PINO_PONTO, HIGH); digitalWrite(PINO_TRACO, HIGH);
      digitalWrite(PINO_ESPACO, HIGH); delay(200);
      digitalWrite(PINO_PONTO, LOW); digitalWrite(PINO_TRACO, LOW);
      digitalWrite(PINO_ESPACO, LOW); delay(200);
    }
  }

  testeInicial();
  simbolos[0] = '\0';
  tSoltura = millis();
  Serial.print(F("unidade: ")); Serial.print(UNIDADE); Serial.println(F("ms"));
}

// Acende os LEDs em sequencia e da um bipe. Confere a fiacao sem multimetro.
void testeInicial() {
  const uint8_t leds[3] = { PINO_PONTO, PINO_TRACO, PINO_ESPACO };
  for (uint8_t i = 0; i < 3; i++) {
    digitalWrite(leds[i], HIGH); delay(150); digitalWrite(leds[i], LOW);
  }
  digitalWrite(PINO_BUZZER, HIGH); delay(80); digitalWrite(PINO_BUZZER, LOW);
}

// ------------------------------------------------------------------- loop
void loop() {
  unsigned long agora = millis();
  bool nivel = (digitalRead(PINO_BOTAO) == LOW);  // pull-up: LOW = pressionado

  // Borda de subida ou descida, filtrando repiques do contato.
  if (nivel != pressionado && (agora - tTransicao) >= DEBOUNCE_MS) {
    tTransicao = agora;
    pressionado = nivel;
    if (pressionado) inicioDoToque(agora);
    else             fimDoToque(agora);
  }

  if (pressionado) {
    // O segundo verde acende no instante em que o toque deixa de ser um ponto.
    if (agora - tInicio >= 2UL * UNIDADE) digitalWrite(PINO_TRACO, HIGH);
  } else {
    unsigned long silencio = agora - tSoltura;
    if (nSimbolos > 0 && silencio >= 3UL * UNIDADE) {
      fechaLetra();
    } else if (nSimbolos == 0 && aguardandoEspaco && silencio >= 7UL * UNIDADE) {
      enviaCaractere(' ');
      Serial.println(F("[espaco]"));
      aguardandoEspaco = false;
      piscaRestante = 4;
      tPisca = agora;
      digitalWrite(PINO_ESPACO, LOW);
    }
  }

  atualizaPisca(agora);
  bombeiaRadio();
}

// ------------------------------------------------------------ manipulador
void inicioDoToque(unsigned long agora) {
  tInicio = agora;
  digitalWrite(PINO_PONTO, HIGH);   // todo toque comeca valendo um ponto
  digitalWrite(PINO_TRACO, LOW);
  digitalWrite(PINO_ESPACO, LOW);   // voltou a manipular: cancela o espaco pendente
  digitalWrite(PINO_BUZZER, HIGH);
  piscaRestante = 0;
  aguardandoEspaco = false;
}

void fimDoToque(unsigned long agora) {
  unsigned long duracao = agora - tInicio;
  tSoltura = agora;
  digitalWrite(PINO_PONTO, LOW);
  digitalWrite(PINO_TRACO, LOW);
  digitalWrite(PINO_BUZZER, LOW);
  registraSimbolo(duracao >= 2UL * UNIDADE ? '-' : '.');
}

void registraSimbolo(char s) {
  if (nSimbolos >= MAX_SIMBOLOS) {
    // Um setimo simbolo nao existe no morse. Fecha como desconhecido em vez
    // de escrever fora do buffer.
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

// Desce a arvore: ponto para a esquerda, traco para a direita.
char decodifica(const char *s) {
  uint8_t no = 0;
  for (uint8_t i = 0; s[i] != '\0'; i++) {
    no = (s[i] == '.') ? (2 * no + 1) : (2 * no + 2);
    if (no > ULTIMO_NO) return '?';
  }
  char c = (char)pgm_read_byte(&ARVORE_MORSE[no]);
  return (c == '*') ? '?' : c;
}

// ------------------------------------------------------------------ radio
void enviaCaractere(char c) {
  sequencia++;  // o receptor usa isto para descartar as repeticoes
  pacote[0] = 'M';
  pacote[1] = sequencia;
  pacote[2] = (uint8_t)c;
  repeticoesPendentes = REPETICOES;
}

/*
  Manda uma copia por vez, so quando o radio esta livre. RH_ASK::send() espera o
  pacote anterior terminar, entao chamar as tres em seguida travaria o loop por
  uns 200ms e perderia toques do operador.
*/
void bombeiaRadio() {
  if (repeticoesPendentes == 0) return;
  if (radio.mode() == RHGenericDriver::RHModeTx) return;
  radio.send(pacote, sizeof(pacote));
  repeticoesPendentes--;
}

// ------------------------------------------------------------------ apoio
void atualizaPisca(unsigned long agora) {
  if (piscaRestante == 0) return;
  if (agora - tPisca < PISCA_MS) return;
  tPisca = agora;
  piscaRestante--;
  digitalWrite(PINO_ESPACO, (piscaRestante % 2) == 1 ? HIGH : LOW);
}
