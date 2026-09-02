/*
  TELEGRAFO SEM FIO - RECEPTOR COM ESP8266

  Faz o mesmo que o receptor-uno.ino — recebe a letra pelo radio 433MHz,
  reconstroi os pontos e tracos e escreve no LCD 16x2 — e ainda publica cada
  letra por MQTT, para a pagina em

      https://henriquemattosesilva.github.io/hw-codigo-morse/ao-vivo/

  mostrar a mensagem ao vivo, de qualquer lugar.

  ---------------------------------------------------------------- ATENCAO
  O ESP8266 e 3,3V e o modulo receptor de 433MHz e 5V. A saida DATA dele
  NAO pode ir direto num pino do ESP: precisa do divisor de 10k + 20k
  descrito no MONTAGEM-ESP8266.md. Ligar direto degrada o pino com o tempo.

  Os pinos GPIO0, GPIO2 e GPIO15 sao lidos no boot e nao aceitam qualquer
  coisa. A distribuicao deles esta explicada em "OS PINOS DE BOOT", logo
  abaixo das constantes — e nao e arbitraria: uma montagem anterior nao
  gravava por causa disso.
  ------------------------------------------------------------------------

  Bibliotecas: RadioHead, PubSubClient (Nick O'Leary) e LiquidCrystal.
  Placa: NodeMCU 1.0 (ESP-12E Module).

  Copie segredos-exemplo.h para segredos.h e ponha os seus dados la. O
  segredos.h esta no .gitignore: a senha do seu WiFi nao vai para o GitHub.
*/

#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <RH_ASK.h>
#include <LiquidCrystal.h>
#include "segredos.h"

// ------------------------------------------------------------------ pinos
// Rotulo da placa -> GPIO. O construtor da LiquidCrystal quer o GPIO.
//
// Sao tres os pinos que o ESP le no boot, e cada um deles ficou com a carga
// que empurra para o lado certo. Ver o comentario "OS PINOS DE BOOT" abaixo.
const uint8_t LCD_RS = 5;   // D1
const uint8_t LCD_E  = 16;  // D0 · tambem o LED da placa: vai piscar
const uint8_t LCD_D4 = 2;   // D4 · pino de boot (alto) e LED do modulo
const uint8_t LCD_D5 = 14;  // D5
const uint8_t LCD_D6 = 12;  // D6
const uint8_t LCD_D7 = 13;  // D7
const uint8_t PINO_RADIO  = 4;   // D2 · DATA do receptor, atras do divisor
const uint8_t PINO_LIMPAR = 0;   // D3 · pino de boot (alto); botao ao GND
const uint8_t PINO_LED_RX = 15;  // D8 · pino de boot (baixo); LED ao GND

/*
  OS PINOS DE BOOT, E POR QUE ELES ESTAO ASSIM

  GPIO0, GPIO2 e GPIO15 sao lidos no instante do reset para decidir o modo de
  inicializacao. O que estiver ligado neles tem de deixar o nivel exigido:

      GPIO0  (D3) alto para rodar, baixo para gravar
      GPIO2  (D4) alto
      GPIO15 (D8) baixo

  A primeira montagem punha o LCD nos tres, no raciocinio de que as entradas
  dele ficam em alta impedancia e nao perturbariam nada. Na bancada isso se
  mostrou falso no GPIO15: o LCD e alimentado em 5V pelo VU, e a fuga pelos
  diodos de protecao da entrada RS puxava o pino para cima, vencendo o resistor
  de 12k da placa. O ESP entrava em modo SDIO e a gravacao morria em
  "Timed out waiting for packet header".

  Agora cada pino de boot tem uma carga compativel:

      GPIO0  o botao de limpar, aberto no boot: o pull-up interno o deixa alto.
             E como o proprio botao FLASH da placa e ligado.
      GPIO2  uma linha de dados do LCD: a fuga dos 5V puxa para cima, que e
             justamente o nivel que este pino quer.
      GPIO15 o LED vermelho. Abaixo da tensao direta o LED e quase circuito
             aberto, entao ele nao e um pull-down — o merito e nao brigar com
             o resistor da placa, ao contrario do que o LCD fazia.

  Efeito colateral de por o botao no GPIO0: segurar "limpar" enquanto a placa
  reseta faz o ESP entrar em modo de gravacao. Nao segure no reset.

  O radio continua fora dos tres. A saida dele e ruido aleatorio enquanto nao
  ha transmissao — num pino de boot seria cara ou coroa a cada vez que voce
  ligasse.
*/

LiquidCrystal lcd(LCD_RS, LCD_E, LCD_D4, LCD_D5, LCD_D6, LCD_D7);

// 0xff para transmissao e PTT: este lado so escuta, e nao sobra pino. No
// core do ESP8266 o pinMode de um pino fora de faixa nao faz nada.
RH_ASK radio(2000, PINO_RADIO, 0xff, 0xff);

WiFiClient rede;
PubSubClient mqtt(rede);

// ------------------------------------------------------------- constantes
const uint8_t  MAX_LCD      = 15;   // 15 letras e o cursor cabem na linha 2
const uint16_t MAX_MENSAGEM = 160;  // o ESP tem RAM para guardar bem mais
const uint8_t  COL_MORSE    = 0;
const uint8_t  COL_LETRA    = 7;
const uint8_t  COL_ENLACE   = 13;
const uint8_t  COL_SINAL    = 15;
const uint16_t INDICADOR_MS = 150;
const uint16_t BLOQUEIO_MS  = 200;
const uint16_t ESPERA_MQTT  = 3000;  // entre tentativas de reconexao
const uint16_t ATRASO_TEXTO = 500;   // nao publica a mensagem inteira a cada letra

const char ARVORE_MORSE[] PROGMEM =
  "*ETIANMSURWDKGOHVF*L*PJBXCYZQ**54*3***2*******16*******7***8*90";
const uint8_t ULTIMO_NO = 62;

const uint8_t CHAR_PONTO  = 1;
const uint8_t CHAR_TRACO  = 2;
const uint8_t CHAR_ANTENA = 3;
byte DESENHO_PONTO[8]  = { B00000, B00000, B00000, B01100, B01100, B00000, B00000, B00000 };
byte DESENHO_TRACO[8]  = { B00000, B00000, B00000, B11110, B11110, B00000, B00000, B00000 };
byte DESENHO_ANTENA[8] = { B00001, B00001, B00101, B00101, B10101, B10101, B10101, B00000 };

// ----------------------------------------------------------------- estado
char     mensagem[MAX_MENSAGEM + 1];
uint16_t nMensagem = 0;
uint8_t  ultimaSequencia = 0;

bool          indicadorAceso = false;
unsigned long tIndicador = 0, tLimpar = 0, tMqtt = 0, tTexto = 0;
bool          limparPressionado = false;
bool          textoSujo = false;      // mudou desde a ultima publicacao
bool          enlaceDesenhado = false;
bool          telaInicial = true;     // ainda mostrando "ligando WiFi..."

char topicoLetra[96], topicoTexto[96], topicoStatus[96];

// ------------------------------------------------------------------ setup
void setup() {
  pinMode(PINO_LED_RX, OUTPUT);
  pinMode(PINO_LIMPAR, INPUT_PULLUP);

  lcd.begin(16, 2);
  lcd.createChar(CHAR_PONTO, DESENHO_PONTO);
  lcd.createChar(CHAR_TRACO, DESENHO_TRACO);
  lcd.createChar(CHAR_ANTENA, DESENHO_ANTENA);
  lcd.clear();

  Serial.begin(115200);
  Serial.println();
  Serial.println(F("Telegrafo - receptor ESP8266"));

  snprintf(topicoLetra,  sizeof(topicoLetra),  "%s/letra",    MQTT_TOPICO_BASE);
  snprintf(topicoTexto,  sizeof(topicoTexto),  "%s/mensagem", MQTT_TOPICO_BASE);
  snprintf(topicoStatus, sizeof(topicoStatus), "%s/status",   MQTT_TOPICO_BASE);

  if (!radio.init()) {
    lcd.print(F("ERRO no radio"));
    Serial.println(F("ERRO: radio nao iniciou"));
    while (true) {
      digitalWrite(PINO_LED_RX, HIGH); delay(200);
      digitalWrite(PINO_LED_RX, LOW);  delay(200);
    }
  }

  lcd.setCursor(0, 0); lcd.print(F("MORSE + WiFi"));
  lcd.setCursor(0, 1); lcd.print(F("ligando WiFi..."));

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_SENHA);
  mqtt.setServer(MQTT_SERVIDOR, MQTT_PORTA);

  // A tela de abertura fica ate o WiFi entrar, ou ate a primeira letra chegar.
  // Quem troca para a tela de trabalho e o saiDaTelaInicial(), no loop.
  mensagem[0] = '\0';
  nMensagem = 0;
}

// ------------------------------------------------------------------- loop
void loop() {
  unsigned long agora = millis();

  recebeRadio(agora);
  cuidaDoMqtt(agora);
  if (telaInicial && WiFi.status() == WL_CONNECTED) {
    Serial.println(F("WiFi conectado"));
    saiDaTelaInicial();
  }
  desenhaEnlace();

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
    if (limpar) limpaMensagem(true);
  }

  // A mensagem inteira sai no maximo duas vezes por segundo; a letra sozinha
  // sai na hora. Publicar o texto todo a cada letra encheria o broker sem
  // deixar a tela mais rapida.
  if (textoSujo && (agora - tTexto) >= ATRASO_TEXTO) publicaMensagem();
}

// ------------------------------------------------------------------ radio
void recebeRadio(unsigned long agora) {
  uint8_t buffer[RH_ASK_MAX_MESSAGE_LEN];
  uint8_t tamanho = sizeof(buffer);
  if (!radio.recv(buffer, &tamanho)) return;
  if (tamanho != 3 || buffer[0] != 'M' || buffer[1] == ultimaSequencia) return;

  ultimaSequencia = buffer[1];
  char c = (char)buffer[2];
  Serial.println(c);

  // Se uma letra chegar antes do WiFi entrar, a tela de trabalho comeca aqui.
  if (telaInicial) saiDaTelaInicial();

  acrescenta(c);
  desenhaLinha1(c);
  desenhaLinha2();

  char morse[8];
  morseDaLetra(c, morse);
  char carga[16];
  // A pagina refaz o morse sozinha a partir da letra, mas mandar os dois
  // deixa o monitor certo mesmo se um dia as tabelas divergirem.
  snprintf(carga, sizeof(carga), "%c %s", c == ' ' ? '_' : c, morse);
  if (mqtt.connected()) mqtt.publish(topicoLetra, carga);
  textoSujo = true;

  digitalWrite(PINO_LED_RX, HIGH);
  lcd.setCursor(COL_SINAL, 0);
  lcd.write('*');
  indicadorAceso = true;
  tIndicador = agora;
}

void acrescenta(char c) {
  if (nMensagem >= MAX_MENSAGEM) {
    memmove(mensagem, mensagem + 1, MAX_MENSAGEM - 1);
    nMensagem = MAX_MENSAGEM - 1;
  }
  mensagem[nMensagem++] = c;
  mensagem[nMensagem] = '\0';
}

/*
  Troca a tela de abertura pela de trabalho. Sem isto, escrever a mensagem por
  cima do "MORSE + WiFi" deixaria pedacos do texto antigo espalhados: a
  desenhaLinha1() so mexe nas colunas 0 a 5 e na 7, e o resto do banner fica.
*/
void saiDaTelaInicial() {
  telaInicial = false;
  lcd.clear();
  enlaceDesenhado = false;  // a tela foi limpa, o indicador tem de ser refeito
  limpaMensagem(false);
}

void limpaMensagem(bool publica) {
  nMensagem = 0;
  mensagem[0] = '\0';
  desenhaLinha1(' ');
  desenhaLinha2();
  if (publica) { textoSujo = true; tTexto = 0; }
}

// ------------------------------------------------------------------- mqtt
void cuidaDoMqtt(unsigned long agora) {
  if (WiFi.status() != WL_CONNECTED) return;
  if (mqtt.connected()) { mqtt.loop(); return; }
  if (agora - tMqtt < ESPERA_MQTT) return;
  tMqtt = agora;

  char id[32];
  snprintf(id, sizeof(id), "morse-%06x", ESP.getChipId());
  // Ultima vontade: se o telegrafo cair, o broker avisa a pagina sozinho.
  if (mqtt.connect(id, topicoStatus, 0, true, "desligado")) {
    Serial.println(F("MQTT conectado"));
    mqtt.publish(topicoStatus, "ligado", true);
    publicaMensagem();
  }
}

void publicaMensagem() {
  if (!mqtt.connected()) return;
  mqtt.publish(topicoTexto, mensagem, true);  // retido: quem abrir depois ve
  textoSujo = false;
  tTexto = millis();
}

// --------------------------------------------------------------- display
void desenhaEnlace() {
  // Canto da linha 1: vazio sem WiFi, 'w' com WiFi mas sem broker, antena
  // quando os dois estao de pe.
  bool wifi = (WiFi.status() == WL_CONNECTED);
  bool tudo = wifi && mqtt.connected();
  static bool ultimoWifi = false, ultimoTudo = false;
  if (enlaceDesenhado && wifi == ultimoWifi && tudo == ultimoTudo) return;
  ultimoWifi = wifi; ultimoTudo = tudo; enlaceDesenhado = true;

  lcd.setCursor(COL_ENLACE, 0);
  if (tudo)       lcd.write(CHAR_ANTENA);
  else if (wifi)  lcd.write('w');
  else            lcd.write(' ');
}

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
  // O LCD mostra o fim da mensagem; a pagina mostra ela inteira.
  uint16_t inicio = (nMensagem > MAX_LCD) ? nMensagem - MAX_LCD : 0;
  uint16_t visiveis = nMensagem - inicio;
  lcd.setCursor(0, 1);
  for (uint8_t i = 0; i < 16; i++) {
    if (i < visiveis)       lcd.write(mensagem[inicio + i]);
    else if (i == visiveis) lcd.write('_');
    else                    lcd.write(' ');
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
