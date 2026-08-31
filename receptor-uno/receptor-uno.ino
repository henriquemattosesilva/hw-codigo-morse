/*
  TELEGRAFO SEM FIO - RECEPTOR (Arduino Uno)

  Recebe o caractere pelo radio 433MHz, reconstroi os pontos e tracos da letra e
  escreve no LCD 16x2:

      linha 1:  .-..  L          *      morse da letra, a letra, indicador de RX
      linha 2:  CHAMANDO_               texto acumulado, rolando para a esquerda

  Ponto e traco sao caracteres desenhados na altura do meio da linha. Usar o '.'
  e o '-' do proprio display deixaria os dois em alturas diferentes.

  A chave tactil em D9 limpa a mensagem.

  Bibliotecas: RadioHead (Mike McCauley) e LiquidCrystal (ja vem com a IDE).
  Placa: Arduino Uno.
*/

#include <RH_ASK.h>
#include <SPI.h>  // a RadioHead nao usa SPI aqui, mas exige o include para compilar
#include <LiquidCrystal.h>

// ---------------------------------------------------------------- pinos
// LCD: RS, E, D4, D5, D6, D7
LiquidCrystal lcd(2, 3, 4, 5, 6, 7);
const uint8_t PINO_LED_RX = 8;  // LED vermelho + resistor 220R
const uint8_t PINO_LIMPAR = 9;  // chave tactil, outro terminal no GND
// D11 e o DATA do modulo receptor, padrao da RH_ASK no AVR.

// ------------------------------------------------------------- constantes
const uint8_t  MAX_TEXTO    = 15;   // 15 letras + o cursor cabem na linha 2
const uint8_t  COL_MORSE    = 0;    // linha 1: morse nas colunas 0 a 5
const uint8_t  COL_LETRA    = 7;    // linha 1: a letra
const uint8_t  COL_SINAL    = 15;   // linha 1: indicador de recepcao
const uint16_t INDICADOR_MS = 150;  // duracao do LED e do indicador
const uint8_t  BLOQUEIO_MS  = 200;  // debounce da chave de limpar

// Mesma arvore do transmissor. Aqui ela e percorrida ao contrario: acha-se a
// letra e sobe-se pelos pais para remontar os pontos e tracos.
const char ARVORE_MORSE[] PROGMEM =
  "*ETIANMSURWDKGOHVF*L*PJBXCYZQ**54*3***2*******16*******7***8*90";
const uint8_t ULTIMO_NO = 62;

// Caracteres customizados do LCD, centralizados na altura da linha. O traco
// ocupa 4 das 5 colunas para que dois tracos seguidos nao virem uma linha so.
const uint8_t CHAR_PONTO = 1;
const uint8_t CHAR_TRACO = 2;
byte DESENHO_PONTO[8] = { B00000, B00000, B00000, B01100, B01100, B00000, B00000, B00000 };
byte DESENHO_TRACO[8] = { B00000, B00000, B00000, B11110, B11110, B00000, B00000, B00000 };

RH_ASK radio;  // 2000 bps, RX em D11

// ----------------------------------------------------------------- estado
char    texto[MAX_TEXTO + 1];
uint8_t nTexto = 0;
uint8_t ultimaSequencia = 0;  // o transmissor comeca em 1, entao 0 nunca colide

bool          indicadorAceso = false;
unsigned long tIndicador = 0;
unsigned long tLimpar = 0;
bool          limparPressionado = false;

// ------------------------------------------------------------------ setup
void setup() {
  pinMode(PINO_LED_RX, OUTPUT);
  pinMode(PINO_LIMPAR, INPUT_PULLUP);

  lcd.begin(16, 2);
  lcd.createChar(CHAR_PONTO, DESENHO_PONTO);
  lcd.createChar(CHAR_TRACO, DESENHO_TRACO);
  lcd.clear();

  Serial.begin(9600);
  Serial.println(F("Telegrafo - receptor"));

  if (!radio.init()) {
    lcd.print(F("ERRO no radio"));
    Serial.println(F("ERRO: radio nao iniciou"));
    while (true) {
      digitalWrite(PINO_LED_RX, HIGH); delay(200);
      digitalWrite(PINO_LED_RX, LOW);  delay(200);
    }
  }

  lcd.setCursor(0, 0); lcd.print(F("MORSE 433MHz"));
  limpaTexto();
}

// ------------------------------------------------------------------- loop
void loop() {
  unsigned long agora = millis();

  uint8_t buffer[RH_ASK_MAX_MESSAGE_LEN];
  uint8_t tamanho = sizeof(buffer);
  if (radio.recv(buffer, &tamanho)) {
    // O CRC da RH_ASK ja barrou o lixo. A marca 'M' e o tamanho fixo descartam
    // o que sobra do trafego alheio na faixa de 433MHz.
    if (tamanho == 3 && buffer[0] == 'M' && buffer[1] != ultimaSequencia) {
      ultimaSequencia = buffer[1];
      recebeCaractere((char)buffer[2], agora);
    }
  }

  if (indicadorAceso && (agora - tIndicador) >= INDICADOR_MS) {
    indicadorAceso = false;
    digitalWrite(PINO_LED_RX, LOW);
    lcd.setCursor(COL_SINAL, 0);
    lcd.write(' ');
  }

  bool limpar = (digitalRead(PINO_LIMPAR) == LOW);
  if (limpar != limparPressionado && (agora - tLimpar) >= BLOQUEIO_MS) {
    tLimpar = agora;
    limparPressionado = limpar;
    if (limpar) limpaTexto();
  }
}

// -------------------------------------------------------------- recepcao
void recebeCaractere(char c, unsigned long agora) {
  Serial.println(c);
  acrescentaTexto(c);
  desenhaLinha1(c);
  desenhaLinha2();

  digitalWrite(PINO_LED_RX, HIGH);
  lcd.setCursor(COL_SINAL, 0);
  lcd.write('*');
  indicadorAceso = true;
  tIndicador = agora;
}

void acrescentaTexto(char c) {
  if (nTexto >= MAX_TEXTO) {  // cheio: rola uma casa para a esquerda
    memmove(texto, texto + 1, MAX_TEXTO - 1);
    nTexto = MAX_TEXTO - 1;
  }
  texto[nTexto++] = c;
  texto[nTexto] = '\0';
}

void limpaTexto() {
  nTexto = 0;
  texto[0] = '\0';
  desenhaLinha1(' ');
  desenhaLinha2();
}

// --------------------------------------------------------------- display
void desenhaLinha1(char c) {
  char morse[8];
  morseDaLetra(c, morse);
  uint8_t n = strlen(morse);

  lcd.setCursor(COL_MORSE, 0);
  for (uint8_t i = 0; i < 6; i++) {
    if (i >= n)                lcd.write(' ');
    else if (morse[i] == '.')  lcd.write(CHAR_PONTO);
    else                       lcd.write(CHAR_TRACO);
  }
  lcd.setCursor(COL_LETRA, 0);
  lcd.write(c == ' ' ? '_' : c);  // o espaco de palavra nao tem simbolo proprio
}

void desenhaLinha2() {
  lcd.setCursor(0, 1);
  for (uint8_t i = 0; i < 16; i++) {
    if (i < nTexto)       lcd.write(texto[i]);
    else if (i == nTexto) lcd.write('_');
    else                  lcd.write(' ');
  }
}

// Acha a letra na arvore e sobe ate a raiz. Um no filho a esquerda vale 2p+1
// (ponto) e a direita 2p+2 (traco), entao o resto de (no-1) por 2 diz qual foi.
void morseDaLetra(char c, char *saida) {
  saida[0] = '\0';
  int8_t no = -1;
  for (uint8_t i = 1; i <= ULTIMO_NO; i++) {
    if ((char)pgm_read_byte(&ARVORE_MORSE[i]) == c) { no = (int8_t)i; break; }
  }
  if (no < 0) return;  // espaco, '?' ou qualquer coisa fora da tabela

  char invertido[8];
  uint8_t n = 0;
  while (no > 0) {
    invertido[n++] = (((no - 1) % 2) == 0) ? '.' : '-';
    no = (no - 1) / 2;
  }
  for (uint8_t i = 0; i < n; i++) saida[i] = invertido[n - 1 - i];
  saida[n] = '\0';
}
