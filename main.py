import serial
import serial.tools.list_ports
import unicodedata
import json
from openai import OpenAI
import os
import tempfile
from dotenv import load_dotenv
from playsound import playsound

# ⚡ Cargar variables de entorno
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
BAUDRATE = 115200

# Cliente OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)

# ⚡ Diccionario de LEDs
ZONAS_LUCES = {
    "fosas_nasales": "fosas_nasales",
    "laringe_faringe": "laringe_faringe",
    "traquea": "traquea",
    "bronquios": "bronquios",
    "bronquiolos": "bronquiolos",
    "alveolos": "alveolos",
    "pulmon_sano": "pulmon_sano",
    "pulmon_enfermo": "pulmon_enfermo"
}

# 🔎 Autodetectar puerto ESP32
def autodetectar_esp32():
    puertos = serial.tools.list_ports.comports()
    for puerto in puertos:
        if "USB" in puerto.device or "usbserial" in puerto.device.lower() or "COM" in puerto.device:
            print(f"[INFO] ESP32 detectado en {puerto.device}")
            return puerto.device
    raise Exception("⚠️ No se detectó ESP32. Conéctalo por USB y vuelve a intentar.")

# 📡 Conexión Serial (autodetección al inicio)
try:
    ESP32_PORT = autodetectar_esp32()
    ser = serial.Serial(ESP32_PORT, BAUDRATE, timeout=1)
except Exception as e:
    print(f"[ERROR] No se pudo abrir conexión serial: {e}")
    exit(1)

def hablar(texto):
    """Convierte texto en voz con OpenAI y lo reproduce con playsound"""
    try:
        respuesta_audio = client.audio.speech.create(
            model="gpt-4o-mini-tts",
            voice="alloy",
            input=texto
        )

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
            f.write(respuesta_audio.read())
            ruta_mp3 = f.name

        print(f"[INFO] Reproduciendo audio: {texto[:50]}...")

        try:
            playsound(ruta_mp3)
        except Exception:
            # Fallback en macOS
            os.system(f"afplay '{ruta_mp3}'")

        os.remove(ruta_mp3)  # Limpieza

    except Exception as e:
        print(f"[WARN] Voz no disponible: {e}")


# 💡 Control de LEDs vía Serial
def controlar_led(zona, accion):
    comando = f"control {zona} {accion}\n"
    ser.write(comando.encode())
    print(f"[OK] {zona} -> {accion}")

# 🔠 Normalizar texto
def normalizar(texto):
    if not isinstance(texto, str):
        return ""
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    ).lower()

# 🤖 Consulta IA
def consulta_ia(pregunta):
    pregunta_n = normalizar(pregunta)

    # 👉 Prompt claro y restringido
    prompt = f"""
    Responde en formato JSON con las claves:
    - "explicacion": Explicación clara y breve (máx 2 frases).
    - "luces_a_encender": lista de las partes del sistema respiratorio a encender.

    ⚠️ IMPORTANTE: Solo puedes usar exactamente estas claves y nada más:
    fosas_nasales, laringe_faringe, traquea, bronquios, bronquiolos, alveolos, pulmon_sano, pulmon_enfermo.

    Reglas:
    - Si la pregunta se refiere a enfermedades, síntomas, condiciones respiratorias 
    (ej: covid, neumonía, asma, alergia, gripe, bronquitis, enfisema, etc.),
    o menciona **vacunas, virus o tratamientos asociados al sistema respiratorio**, 
    **sí debes responder** como parte del sistema.
    Usa "pulmon_enfermo" y agrega las zonas afectadas si aplica (ej: alveolos en COVID).
    - Si la pregunta se refiere al ciclo de la respiracion, responde con:
    "explicacion": breve explicación del ciclo
    "luces_a_encender": ["fosas_nasales", "laringe_faringe", "traquea", "bronquios", "bronquiolos", "alveolos"]
    ⚠️ Además, se debe activar la animación especial "flujo" en el ESP32.
    - Si la pregunta NO trata del sistema respiratorio (ej: autos, política, cocina), responde:
    "explicacion": "Esa no es una pregunta sobre el sistema respiratorio."
    "luces_a_encender": []

    Pregunta del usuario: {pregunta_n}
"""

    try:
        # 👉 Llamada a OpenAI
        r = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Eres un asistente de biología que responde solo sobre el sistema respiratorio."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )

        # 👉 Procesar JSON
        data = json.loads(r.choices[0].message.content)
        explicacion = data.get("explicacion", "No se pudo obtener explicación.")
        luces = data.get("luces_a_encender", [])

        # 🚦 Caso especial: ciclo de la respiración
        if "ciclo" in pregunta_n and "respiracion" in pregunta_n:
            ser.write(b"flujo\n")  # 👉 activa animación en ESP32
            print("[OK] Animación del ciclo de la respiración activada")

        # ✨ Agregar referencia a la maqueta si hay luces encendidas
        if luces:
            partes_mostradas = ", ".join(luces).replace("_", " ")
            explicacion += f" En la maqueta se está mostrando: {partes_mostradas}."

        # 👉 Mostrar en consola
        print("\n🤖 Respuesta IA:")
        print(f"Explicación: {explicacion}")
        print(f"Luces: {luces}")

        # 👉 Controlar LEDs manualmente solo si NO es ciclo
        if not ("ciclo" in pregunta_n and "respiracion" in pregunta_n):
            ser.write(b"all off\n")
            for luz in luces:
                if luz in ZONAS_LUCES:
                    controlar_led(luz, "on")

        # 🔊 Reproducir voz
        hablar(explicacion)

    except Exception as e:
        print(f"[ERROR] IA: {e}")

# 🚀 Programa principal
if __name__ == "__main__":
    print("Sistema respiratorio con LEDs y voz natural (USB Serial).")
    ser.write(b"all off\n")

    while True:
        pregunta = input("\n❓ Pregunta (o 'salir' para terminar): ")
        if pregunta.lower() == "salir":
            ser.write(b"all off\n")
            print("¡Hasta luego!")
            break
        if not pregunta.strip():
            continue
        consulta_ia(pregunta)