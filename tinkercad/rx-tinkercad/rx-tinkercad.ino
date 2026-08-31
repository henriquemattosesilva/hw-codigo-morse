/*
  TELEGRAFO SEM FIO - RECEPTOR, VERSAO PARA O TINKERCAD

  Mesma logica do receptor-uno.ino. So muda o que o simulador nao tem:

    modulo RF 433MHz  -> o fio que chega de D12 da outra placa em D11 desta
    biblioteca RadioHead -> SoftwareSerial (o Tinkercad so aceita as oficiais)

  O que a RadioHead fazia sozinha e aqui e feito na mao: achar o inicio do
  pacote. Ela punha preambulo e CRC em cada mensagem; num fio nao ha ruido
  para filtrar, mas ainda e preciso saber onde um pacote de 3 bytes comeca,
  e e para isso que serve a marca 'M'.

  IMPORTANTE: ligue o GND desta placa no GND da outra. Sem terra em comum as
  duas nao tem referencia de tensao e nao trocam nada.

  Placa: Arduino Uno R3.
*/

#include <SoftwareSerial.h>
#include <LiquidCrystal.h>

// ---------------------------------------------------------------- pinos
LiquidCrystal lcd(2, 3, 4, 5, 6, 7);   // RS, E, D4, D5, D6, D7
const uint8_t PINO_LED_RX = 8;         // LED vermelho + resistor 220R
const uint8_t PINO_LIMPAR = 9;         // chave tactil, outro terminal no GND

SoftwareSerial radio(11, 12);          // RX em D11 (o fio), TX em D12 (sem uso)

// ------------------------------------------------------------- constantes
const uint8_t  MAX_TEXTO    = 15;
const uint8_t  COL_MORSE    = 0;
const uint8_t  COL_LETRA    = 7;
const uint8_t  COL_SINAL    = 15;
const uint16_t INDICADOR_MS = 150;
const uint8_t  BLOQUEIO_MS  = 200;

const char ARVORE_MORSE[] PROGMEM =
  "*ETIANMSURWDKGOHVF*L*PJBXCYZQ**54*3***2*******16*******7***8*90";
const uint8_t ULTIMO_NO = 62;

const uint8_t CHAR_PONTO = 1;
const uint8_t CHAR_TRACO = 2;
byte DESENHO_PONTO[8] = { B00000, B00000, B00000, B01100, B01100, B00000, B00000, B00000 };
byte DESENHO_TRACO[8] = { B00000, B00000, B00000, B11110, B11110, B00000, B00000, B00000 };

// ----------------------------------------------------------------- estado
char    texto[MAX_TEXTO + 1];
uint8_t nTexto = 0;
uint8_t ultimaSequencia = 0;

uint8_t pacote[3];
uint8_t nPacote = 0;

bool          indicadorAceso = false;
unsigned long tIndicador = 0, tLimpar = 0;
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
  radio.begin(9600);
  Serial.println(F("Telegrafo - receptor (Tinkercad)"));

  lcd.setCursor(0, 0); lcd.print(F("MORSE  no  fio"));
  limpaTexto();
}

// ------------------------------------------------------------------- loop
void loop() {
  unsigned long agora = millis();

  /*
    Monta o pacote byte a byte. Enquanto nao vier a marca 'M' nada e
    guardado, entao um byte perdido no meio nao desalinha o resto para
    sempre: o proximo 'M' recomeca a contagem.
  */
  while (radio.available()) {
    uint8_t b = radio.read();
    if (nPacote == 0 && b != 'M') continue;
    pacote[nPacote++] = b;
    if (nPacote < 3) continue;
    nPacote = 0;
    if (pacote[1] != ultimaSequencia) {
      ultimaSequencia = pacote[1];
      recebeCaractere((char)pacote[2], agora);
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
  if (nTexto >= MAX_TEXTO) {
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
  lcd.write(c == ' ' ? '_' : c);
}

void desenhaLinha2() {
  lcd.setCursor(0, 1);
  for (uint8_t i = 0; i < 16; i++) {
    if (i < nTexto)       lcd.write(texto[i]);
    else if (i == nTexto) lcd.write('_');
    else                  lcd.write(' ');
  }
}

void morseDaLetra(char c, char *saida) {
  saida[0] = '\0';
  int8_t no = -1;
  for (uint8_t i = 1; i <= ULTIMO_NO; i++) {
    if ((char)pgm_read_byte(&ARVORE_MORSE[i]) == c) { no = (int8_t)i; break; }
  }
  if (no < 0) return;

  char invertido[8];
  uint8_t n = 0;
  while (no > 0) {
    invertido[n++] = (((no - 1) % 2) == 0) ? '.' : '-';
    no = (no - 1) / 2;
  }
  for (uint8_t i = 0; i < n; i++) saida[i] = invertido[n - 1 - i];
  saida[n] = '\0';
}
