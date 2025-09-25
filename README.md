# 🌬️ Proyecto Sistema Respiratorio con ESP32 + Python + OpenAI

Este proyecto conecta un **ESP32** con una maqueta del sistema respiratorio y un programa en **Python** que responde preguntas sobre el sistema respiratorio usando **IA de OpenAI**, controla LEDs en la maqueta y reproduce voz con **playsound**.

---

## 🔌 Conexiones de hardware

El ESP32 controla **8 zonas** del sistema respiratorio mediante LEDs:

| Parte del sistema       | Pin ESP32 |
|--------------------------|-----------|
| Fosas nasales           | GPIO 12   |
| Laringe-Faringe         | GPIO 13   |
| Tráquea                 | GPIO 14   |
| Bronquios               | GPIO 16   |
| Bronquiolos             | GPIO 18   |
| Alveolos                | GPIO 19   |
| Pulmón sano             | GPIO 17   |
| Pulmón enfermo          | GPIO 26   |

⚠️ **Importante:**  
- Cada LED debe conectarse en **serie con una resistencia de 220 Ω – 330 Ω**.  
- Conectar el **cátodo del LED a GND** del ESP32.  

---

## 💻 Código ESP32 (firmware)

El archivo principal es **`esp32_respiratorio.ino`**.  
Este programa:  
- Conecta el ESP32 a WiFi.  
- Abre un servidor web en el puerto 80.  
- Expone endpoints para encender/apagar LEDs y simular el **flujo de aire**.

Ejemplo de rutas disponibles:  

- `http://<IP_ESP32>/control?zona=fosas_nasales&accion=on`  
- `http://<IP_ESP32>/control?zona=bronquios&accion=off`  
- `http://<IP_ESP32>/flujo` → simula el ciclo respiratorio (sin usar pulmones sano/enfermo).  
- `http://<IP_ESP32>/all/on` → enciende todos.  
- `http://<IP_ESP32>/all/off` → apaga todos.  

---

## 🐍 Código Python (control e IA)

El archivo principal es **`main.py`**.  
Este programa:  
1. Lee la API Key de OpenAI y la IP del ESP32 desde `.env`.  
2. Usa `openai` para generar respuestas inteligentes.  
3. Controla los LEDs vía HTTP.  
4. Reproduce las respuestas en voz con **playsound**.

### 📂 `.env` ejemplo

```
OPENAI_API_KEY=sk-xxxxxx
ESP32_IP=10.20.0.147
```

### 📦 Dependencias requeridas

Dentro del entorno virtual (`venv`) instala:

```bash
pip install requests playsound==1.2.2 openai==1.109.1 python-dotenv
```

👉 Nota: usamos `playsound 1.2.2` porque es ligero y funciona bien en macOS.  

---

## 🚀 Pasos para ejecutar

### 1. Subir el firmware al ESP32
1. Abre el **Arduino IDE** o **PlatformIO**.  
2. Copia el contenido de `esp32_respiratorio.ino`.  
3. Selecciona la placa `ESP32 Dev Module`.  
4. Configura la velocidad de carga en `115200`.  
5. Carga el programa en el ESP32.  
6. En el monitor serie aparecerá la **IP local asignada** (ej. `10.20.0.147`).  

### 2. Configurar Python
1. Crea y activa el entorno virtual:
   ```bash
   python -m venv venv
   source venv/bin/activate  # macOS/Linux
   venv\Scripts\activate     # Windows
   ```
2. Instala las dependencias:
   ```bash
   pip install requests playsound==1.2.2 openai==1.109.1 python-dotenv
   ```
3. Crea el archivo `.env` con tu API Key y la IP del ESP32.  

### 3. Ejecutar el programa
```bash
python main.py
```

Ejemplo de interacción:
```
❓ Pregunta (o 'salir' para terminar): ¿Qué es el asma?
🤖 Explicación: El asma es una enfermedad crónica que inflama y estrecha las vías respiratorias...
💡 Luces encendidas: fosas_nasales, laringe_faringe, tráquea, bronquios, bronquiolos
🔊 Reproduciendo voz...
```

---

## 📖 Notas finales
- Si mueves el sistema a otra red WiFi, debes cambiar las credenciales en el firmware o implementar múltiples SSID en el `.ino`.  
- El flujo respiratorio (`/flujo`) solo recorre **fosas, laringe, tráquea, bronquios, bronquiolos y alveolos**, no incluye pulmones sano/enfermo.  
- El programa Python es modular y se puede ampliar fácilmente para más órganos o funciones.  

---



## ⚡ ESP32 - Firmware

Archivo: `esp32_respiratorio.ino`

Este firmware enciende y controla los LEDs que representan el sistema respiratorio.  
Incluye conexión automática a múltiples redes WiFi (en este ejemplo: `TANGUISNET` y `Claro_QP`).  

### 🔌 Conexiones de LEDs
- Pin 12 → LED fosas nasales  
- Pin 13 → LED laringe/faringe  
- Pin 14 → LED tráquea  
- Pin 16 → LED bronquios  
- Pin 18 → LED bronquiolos  
- Pin 19 → LED alveolos  
- Pin 17 → LED pulmón sano  
- Pin 26 → LED pulmón enfermo  

### 🌐 Endpoints disponibles
- `http://<ESP32_IP>/control?zona=fosas_nasales&accion=on|off`  
- `http://<ESP32_IP>/all/on` → enciende todas las zonas  
- `http://<ESP32_IP>/all/off` → apaga todas las zonas  
- `http://<ESP32_IP>/flujo` → animación del ciclo de respiración  

### 📡 Configuración WiFi
Puedes añadir más redes editando las listas en `esp32_respiratorio.ino`:

```cpp
const char* ssidList[]     = {"TANGUISNET", "Claro_QP"};
const char* passwordList[] = {"IA2025@ft",  "Lucia_21"};
const int numNetworks = 2;


### 🖥️ Mostrar IP en OLED SSD1306 (opcional)

Para no depender del **monitor serie**, puedes usar un display **OLED SSD1306 (128x64, I²C)** para mostrar la IP asignada al ESP32.

#### 🔌 Conexiones del OLED SSD1306 (I²C)
| OLED SSD1306 | ESP32 |
|--------------|-------|
| VCC          | 3.3V  |
| GND          | GND   |
| SDA          | GPIO 21 |
| SCL          | GPIO 22 |

#### 📦 Librerías necesarias
Instala desde el **Library Manager** en Arduino IDE:
- `Adafruit SSD1306`
- `Adafruit GFX`

#### 📄 Ejemplo de uso en `setup()`
```cpp
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

#define ANCHO 128
#define ALTO 64
Adafruit_SSD1306 display(ANCHO, ALTO, &Wire, -1);

void setup() {
  Serial.begin(115200);

  if(!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    Serial.println("⚠️ No se detecta el OLED");
    for(;;);
  }
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0,0);
  display.println("Conectando WiFi...");
  display.display();

  if (connectWiFi()) {
    display.clearDisplay();
    display.setCursor(0,0);
    display.println("WiFi OK");
    display.print("IP: ");
    display.println(WiFi.localIP());
    display.display();
  }
}

# 🔌 Conexiones del Proyecto Sistema Respiratorio

Este documento resume las conexiones necesarias entre el **ESP32**, el **OLED SSD1306 (I²C)** y los **LEDs** que representan las partes del sistema respiratorio.

---

## 📺 Conexión ESP32 → OLED SSD1306 (I²C)

| OLED SSD1306 | ESP32 (DevKit) |
|--------------|----------------|
| **VCC**      | 3.3V           |
| **GND**      | GND            |
| **SDA**      | GPIO 21        |
| **SCL**      | GPIO 22        |

⚠️ Nota: algunos módulos OLED aceptan **5V**, pero se recomienda alimentarlo con **3.3V** para seguridad del ESP32.

---

## 💡 Conexión ESP32 → LEDs del sistema respiratorio

Cada LED debe conectarse con **una resistencia de 220–330 Ω en serie**.  
El **cátodo** de cada LED va a **GND** del ESP32.

| Parte del sistema       | Pin ESP32 |
|--------------------------|-----------|
| Fosas nasales           | GPIO 12   |
| Laringe-Faringe         | GPIO 13   |
| Tráquea                 | GPIO 14   |
| Bronquios               | GPIO 16   |
| Bronquiolos             | GPIO 18   |
| Alveolos                | GPIO 19   |
| Pulmón sano             | GPIO 17   |
| Pulmón enfermo          | GPIO 26   |

---

✅ Con estas conexiones tendrás:  
- El **OLED** mostrando la IP del ESP32 al iniciar.  
- Los **8 LEDs** representando las zonas del sistema respiratorio.  