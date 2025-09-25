import requests
import unicodedata
import json
from openai import OpenAI
import os
import tempfile
from dotenv import load_dotenv
from playsound import playsound  # 👈 Solo playsound, más simple

# ⚡ Cargar variables de entorno desde .env
load_dotenv()

# ⚡ Configuración desde .env
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ESP32_IP = os.getenv("ESP32_IP")

# Cliente OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)

# ⚡ Diccionario para mapear zonas a LEDs del ESP32
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

# Bandera global para conexión con ESP32
ESP32_CONECTADO = True


# 🔊 Voz con playsound (MP3 directo)
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


# 💡 Control de LEDs vía ESP32
def controlar_led(zona, accion):
    """Enciende o apaga un LED del ESP32"""
    global ESP32_CONECTADO
    if not ESP32_CONECTADO:
        return

    nombre_luz_esp32 = ZONAS_LUCES.get(zona)
    if not nombre_luz_esp32:
        return

    url = f"http://{ESP32_IP}/control?zona={nombre_luz_esp32}&accion={accion}"
    try:
        requests.get(url, timeout=2)
        print(f"[OK] {zona} -> {accion}")
    except Exception as e:
        print(f"[WARN] No se pudo comunicar con el ESP32 ({zona}): {e}")
        ESP32_CONECTADO = False


# 🔠 Normalizar texto
def normalizar(texto):
    """Quita tildes y convierte a minúsculas"""
    if not isinstance(texto, str):
        return ""
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    ).lower()


# 🤖 Consulta IA
def consulta_ia(pregunta_usuario):
    """Consulta a la IA y controla la maqueta"""
    pregunta_normalizada = normalizar(pregunta_usuario)

    prompt = f"""
    Responde en formato JSON con las claves:
    - "explicacion": Explicación clara y breve (máx 3 frases). 
      Debe incluir una breve descripción de la enfermedad o función, 
      y al final mencionar explícitamente qué partes del sistema respiratorio 
      se muestran en la maqueta.
    - "luces_a_encender": lista de partes del sistema respiratorio relevantes 
      (usa estas claves exactas: {list(ZONAS_LUCES.keys())}).
    - Si la pregunta NO trata del sistema respiratorio, responde:
      "explicacion": "Esa no es una pregunta sobre el sistema respiratorio."
      "luces_a_encender": []
    Pregunta del usuario: {pregunta_normalizada}
    """

    try:
        respuesta_api = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Eres un asistente de biología que responde solo sobre el sistema respiratorio."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )

        respuesta_json = json.loads(respuesta_api.choices[0].message.content)

        explicacion = respuesta_json.get("explicacion", "No se pudo obtener explicación.")
        luces_a_encender = respuesta_json.get("luces_a_encender", [])

        # 🟢 Ajustar para mencionar explícitamente la maqueta
        if luces_a_encender:
            partes = ", ".join(luces_a_encender[:-1]) + " y " + luces_a_encender[-1] if len(luces_a_encender) > 1 else luces_a_encender[0]
            explicacion += f" En la maqueta se están mostrando {partes}."

        print("\n🤖 Respuesta de la IA:")
        print(f"Explicación: {explicacion}")
        print(f"Luces sugeridas: {luces_a_encender}")

        # Control de LEDs
        if ESP32_CONECTADO and luces_a_encender:
            todas = list(ZONAS_LUCES.keys())
            if sorted(luces_a_encender) == sorted(todas):
                try:
                    requests.get(f"http://{ESP32_IP}/flujo", timeout=3)
                    print("[OK] Flujo de aire simulado en la maqueta")
                except Exception as e:
                    print(f"[WARN] No se pudo ejecutar flujo: {e}")
            else:
                for zona in ZONAS_LUCES.keys():
                    controlar_led(zona, "off")
                for luz in luces_a_encender:
                    if luz in ZONAS_LUCES:
                        controlar_led(luz, "on")
        elif not luces_a_encender:
            print("[INFO] Pregunta fuera del sistema respiratorio. No se encienden LEDs.")

        hablar(explicacion)

    except Exception as e:
        print(f"[ERROR] IA: {e}")


# 🚀 Programa principal
if __name__ == "__main__":
    print("Sistema respiratorio con LEDs y voz natural.")
    # Apagamos todas las luces al inicio
    for zona in ZONAS_LUCES.keys():
        controlar_led(zona, "off")

    while True:
        pregunta = input("\n❓ Pregunta (o 'salir' para terminar): ")
        if pregunta.lower() == "salir":
            for zona in ZONAS_LUCES.keys():
                controlar_led(zona, "off")
            print("¡Hasta luego!")
            break
        if not pregunta.strip():
            continue
        consulta_ia(pregunta)