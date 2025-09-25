#include <Arduino.h>

// ⚡ Pines de LEDs
#define LED_FOSAS         12
#define LED_LARINGE       13
#define LED_TRAQUEA       14
#define LED_BRONQUIOS     16
#define LED_BRONQUIOLOS   18
#define LED_ALVEOLOS      19
#define LED_PULMON_SANO   17
#define LED_PULMON_ENFER  26

// ⚡ Variables
bool parpadeoActivo = false;
int zonasParpadeo[8];
int numZonasParpadeo = 0;

// ============================
// 🚦 Control de LEDs
// ============================
void controlarLed(String zona, String accion) {
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
    Serial.println("Zona no reconocida");
    return;
  }

  if (accion == "on") {
    zonasParpadeo[numZonasParpadeo++] = pin;
    parpadeoActivo = true;
    Serial.println(zona + " encendido");
  } else if (accion == "off") {
    digitalWrite(pin, LOW);
    parpadeoActivo = false;
    numZonasParpadeo = 0;
    Serial.println(zona + " apagado");
  } else {
    Serial.println("Accion no valida");
  }
}

// ============================
// 🚦 Flujo respiratorio
// ============================
void flujo() {
  int flujo[] = {LED_FOSAS, LED_LARINGE, LED_TRAQUEA, LED_BRONQUIOS, LED_BRONQUIOLOS, LED_ALVEOLOS};
  int pasos = sizeof(flujo) / sizeof(flujo[0]);

  // Apagar todo primero
  int leds[] = {LED_FOSAS, LED_LARINGE, LED_TRAQUEA, LED_BRONQUIOS, LED_BRONQUIOLOS, LED_ALVEOLOS, LED_PULMON_SANO, LED_PULMON_ENFER};
  for (int i=0;i<8;i++) digitalWrite(leds[i], LOW);

  for (int ciclo=0; ciclo<3; ciclo++) {
    for (int i=0; i<pasos; i++) {
      digitalWrite(flujo[i], HIGH);
      delay(500);
    }
    delay(1000);
    for (int i=pasos-1; i>=0; i--) {
      digitalWrite(flujo[i], LOW);
      delay(500);
    }
  }
  Serial.println("Flujo de aire simulado");
}

// ============================
// Setup
// ============================
void setup() {
  Serial.begin(115200);
  int leds[] = {LED_FOSAS, LED_LARINGE, LED_TRAQUEA, LED_BRONQUIOS, LED_BRONQUIOLOS, LED_ALVEOLOS, LED_PULMON_SANO, LED_PULMON_ENFER};
  for (int i=0;i<8;i++) pinMode(leds[i], OUTPUT);

  Serial.println("ESP32 listo para recibir comandos por USB Serial");
}

// ============================
// Loop
// ============================
void loop() {
  // Leer comandos desde Python
  if (Serial.available()) {
    String input = Serial.readStringUntil('\n');
    input.trim();

    if (input.startsWith("control")) {
      int espacio1 = input.indexOf(' ');
      int espacio2 = input.indexOf(' ', espacio1 + 1);
      String zona = input.substring(espacio1 + 1, espacio2);
      String accion = input.substring(espacio2 + 1);
      controlarLed(zona, accion);

    } else if (input == "all on") {
      int leds[] = {LED_FOSAS, LED_LARINGE, LED_TRAQUEA, LED_BRONQUIOS, LED_BRONQUIOLOS, LED_ALVEOLOS, LED_PULMON_SANO, LED_PULMON_ENFER};
      for (int i=0;i<8;i++) zonasParpadeo[i] = leds[i];
      numZonasParpadeo = 8;
      parpadeoActivo = true;
      Serial.println("Todas las zonas encendidas");

    } else if (input == "all off") {
      int leds[] = {LED_FOSAS, LED_LARINGE, LED_TRAQUEA, LED_BRONQUIOS, LED_BRONQUIOLOS, LED_ALVEOLOS, LED_PULMON_SANO, LED_PULMON_ENFER};
      for (int i=0;i<8;i++) digitalWrite(leds[i], LOW);
      parpadeoActivo = false;
      numZonasParpadeo = 0;
      Serial.println("Todas las zonas apagadas");

    } else if (input == "flujo") {
      flujo();

    } else {
      Serial.println("Comando no valido");
    }
  }

  // 🔄 Parpadeo automático si hay varias zonas activas
  if (parpadeoActivo && numZonasParpadeo > 0) {
    for (int i=0; i<numZonasParpadeo; i++) digitalWrite(zonasParpadeo[i], HIGH);
    delay(2000);
    for (int i=0; i<numZonasParpadeo; i++) digitalWrite(zonasParpadeo[i], LOW);
    delay(2000);
  }
}