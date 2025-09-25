#include <WiFi.h>
#include <WebServer.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

// ⚡ Lista de WiFi
const char* ssidList[]     = {"TANGUISNET", "Claro_QP"};
const char* passwordList[] = {"IA2025@ft",  "Lucia_21"};
const int numNetworks = 2;

// ⚡ Pines de LEDs
#define LED_FOSAS         12
#define LED_LARINGE       13
#define LED_TRAQUEA       14
#define LED_BRONQUIOS     16
#define LED_BRONQUIOLOS   18
#define LED_ALVEOLOS      19
#define LED_PULMON_SANO   17
#define LED_PULMON_ENFER  26

WebServer server(80);

// ⚡ OLED
#define ANCHO 128
#define ALTO 64
Adafruit_SSD1306 display(ANCHO, ALTO, &Wire, -1);

// ⚡ Variables
bool parpadeoActivo = false;
int zonasParpadeo[8];
int numZonasParpadeo = 0;

// ============================
// 🚀 Intento de conexión WiFi
// ============================
bool connectWiFi() {
  for (int i = 0; i < numNetworks; i++) {
    Serial.printf("🔎 Intentando conectar a %s...\n", ssidList[i]);
    WiFi.begin(ssidList[i], passwordList[i]);

    unsigned long startAttempt = millis();
    while (WiFi.status() != WL_CONNECTED && millis() - startAttempt < 8000) {
      delay(500);
      Serial.print(".");
    }

    if (WiFi.status() == WL_CONNECTED) {
      String ip = WiFi.localIP().toString();
      Serial.printf("\n✅ Conectado a %s, IP: %s\n", ssidList[i], ip.c_str());

      // Mostrar en OLED
      display.clearDisplay();
      display.setTextSize(1);
      display.setTextColor(SSD1306_WHITE);
      display.setCursor(0, 0);
      display.println("WiFi conectado:");
      display.println(ssidList[i]);
      display.println("IP:");
      display.println(ip);
      display.display();

      return true;
    }
    Serial.println("\n❌ Falló la conexión, probando siguiente...");
  }
  return false;
}

// ============================
// Handlers (igual que antes)
// ============================
void handleControl() {
  if (!server.hasArg("zona") || !server.hasArg("accion")) {
    server.send(400, "text/plain", "Faltan parámetros");
    return;
  }
  String zona = server.arg("zona");
  String accion = server.arg("accion");
  int pin = -1;

  if (zona == "fosas_nasales") pin = LED_FOSAS;
  else if (zona == "laringe_faringe") pin = LED_LARINGE;
  else if (zona == "traquea") pin = LED_TRAQUEA;
  else if (zona == "bronquios") pin = LED_BRONQUIOS;
  else if (zona == "bronquiolos") pin = LED_BRONQUIOLOS;
  else if (zona == "alveolos") pin = LED_ALVEOLOS;
  else if (zona == "pulmon_sano") pin = LED_PULMON_SANO;
  else if (zona == "pulmon_enfermo") pin = LED_PULMON_ENFER;

  if (pin == -1) {
    server.send(400, "text/plain", "Zona no reconocida");
    return;
  }

  if (accion == "on") {
    zonasParpadeo[numZonasParpadeo++] = pin;
    parpadeoActivo = true;
    server.send(200, "text/plain", zona + " encendido");
  } else if (accion == "off") {
    digitalWrite(pin, LOW);
    numZonasParpadeo = 0;
    parpadeoActivo = false;
    server.send(200, "text/plain", zona + " apagado");
  } else {
    server.send(400, "text/plain", "Accion no valida");
  }
}

void handleOnAll() {
  int leds[] = {LED_FOSAS, LED_LARINGE, LED_TRAQUEA, LED_BRONQUIOS, LED_BRONQUIOLOS, LED_ALVEOLOS, LED_PULMON_SANO, LED_PULMON_ENFER};
  for (int i=0;i<8;i++) zonasParpadeo[i] = leds[i];
  numZonasParpadeo = 8;
  parpadeoActivo = true;
  server.send(200, "text/plain", "Todas las zonas encendidas");
}

void handleOffAll() {
  int leds[] = {LED_FOSAS, LED_LARINGE, LED_TRAQUEA, LED_BRONQUIOS, LED_BRONQUIOLOS, LED_ALVEOLOS, LED_PULMON_SANO, LED_PULMON_ENFER};
  for (int i=0;i<8;i++) digitalWrite(leds[i], LOW);
  numZonasParpadeo = 0;
  parpadeoActivo = false;
  server.send(200, "text/plain", "Todas las zonas apagadas");
}

void handleFlujo() {
  int flujo[] = {LED_FOSAS, LED_LARINGE, LED_TRAQUEA, LED_BRONQUIOS, LED_BRONQUIOLOS, LED_ALVEOLOS};
  int pasos = sizeof(flujo)/sizeof(flujo[0]);
  handleOffAll();
  for (int ciclo=0;ciclo<3;ciclo++) {
    for (int i=0;i<pasos;i++) { digitalWrite(flujo[i], HIGH); delay(500); }
    delay(1000);
    for (int i=pasos-1;i>=0;i--) { digitalWrite(flujo[i], LOW); delay(500); }
  }
  server.send(200, "text/plain", "Flujo de aire simulado");
}

// ============================
// Setup y Loop
// ============================
void setup() {
  Serial.begin(115200);

  // Inicia OLED
  if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    Serial.println("⚠️ No se detecta OLED en 0x3C");
    for(;;);
  }
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0, 0);
  display.println("Iniciando...");
  display.display();

  int leds[] = {LED_FOSAS, LED_LARINGE, LED_TRAQUEA, LED_BRONQUIOS, LED_BRONQUIOLOS, LED_ALVEOLOS, LED_PULMON_SANO, LED_PULMON_ENFER};
  for (int i=0;i<8;i++) pinMode(leds[i], OUTPUT);

  if (!connectWiFi()) {
    display.clearDisplay();
    display.setCursor(0, 0);
    display.println("WiFi fallo!");
    display.display();
  }

  server.on("/control", handleControl);
  server.on("/all/on", handleOnAll);
  server.on("/all/off", handleOffAll);
  server.on("/flujo", handleFlujo);
  server.begin();
}

void loop() {
  server.handleClient();
  if (parpadeoActivo && numZonasParpadeo > 0) {
    for (int i=0;i<numZonasParpadeo;i++) digitalWrite(zonasParpadeo[i], HIGH);
    delay(2000);
    for (int i=0;i<numZonasParpadeo;i++) digitalWrite(zonasParpadeo[i], LOW);
    delay(2000);
  }
}