/*
  Copie este arquivo para segredos.h, na mesma pasta, e ponha os seus dados.
  O segredos.h esta no .gitignore: a senha do seu WiFi nao vai para o GitHub.
  Sem ele o sketch nao compila, e e de proposito — assim nao tem como esquecer.
*/
#pragma once

#define WIFI_SSID   "nome-da-sua-rede"
#define WIFI_SENHA  "senha-da-sua-rede"

// O ESP fala com o broker em texto puro, na 1883. Quem precisa de conexao
// segura e o navegador, e a pagina ao vivo usa a 8884.
#define MQTT_SERVIDOR "broker.hivemq.com"
#define MQTT_PORTA    1883

/*
  Este broker e publico e nao pede senha: qualquer um que saiba o nome do
  topico consegue ler o que voce transmite, e escrever nele. Por isso o
  sufixo abaixo tem que ser trocado por algo so seu — invente uma sequencia
  qualquer. O mesmo valor precisa estar em ao-vivo/index.html, na constante
  TOPICO_BASE, ou a pagina escuta um telegrafo que nao e o seu.
*/
#define MQTT_TOPICO_BASE "hw-codigo-morse/troque-este-sufixo"
