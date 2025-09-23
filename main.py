import os
import requests
import unicodedata
import json
import simpleaudio as sa
from openai import OpenAI
from dotenv import load_dotenv
import httpx # Importa httpx

# ================================
# ⚡ Cargar variables de entorno
# ================================
load_dotenv()

# 🚀 Claves desde .env
OPENAI_KEY = os.getenv("OPENAI_API_KEY")   # Tu API Key de OpenAI
ESP32_IP = os.getenv("ESP32_IP", "10.20.0.147")  # IP del ESP32, configurable


# ⚡ Configura cliente de OpenAI
client = OpenAI()  # La API key se toma de OPENAI_API_KEY en tu .env

# ================================
# ⚡ Diccionario de LEDs en la maqueta
# ================================
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

# ================================
# 🔊 Función para hablar con voz natural (TTS)
# ================================
def hablar(texto: str):
    try:
        respuesta_audio = client.audio.speech.create(
            model="gpt-4o-mini-tts",
            voice="alloy",
            input=texto
        )

        # Guardar en MP3 primero
        ruta_mp3 = "respuesta.mp3"
        with open(ruta_mp3, "wb") as f:
            f.write(respuesta_audio.read())

        # Convertir a WAV porque simpleaudio no soporta MP3
        from pydub import AudioSegment
        ruta_wav = "respuesta.wav"
        AudioSegment.from_mp3(ruta_mp3).export(ruta_wav, format="wav")

        # Reproducir con simpleaudio
        wave_obj = sa.WaveObject.from_wave_file(ruta_wav)
        play_obj = wave_obj.play()
        play_obj.wait_done()

    except Exception as e:
        print(f"[ERROR] No se pudo generar/reproducir la voz: {e}")

# ================================
# 🔧 Control de LEDs en el ESP32
# ================================
def controlar_led(zona: str, accion: str):
    nombre_luz_esp32 = ZONAS_LUCES.get(zona)
    if not nombre_luz_esp32:
        print(f"[ADVERTENCIA] Zona desconocida: {zona}")
        return
    url = f"http://{ESP32_IP}/control?zona={nombre_luz_esp32}&accion={accion}"
    try:
        requests.get(url, timeout=3)
        print(f"[OK] {zona} -> {accion}")
    except Exception as e:
        print(f"[ERROR] {zona}: {e}")

# ================================
# 🔡 Normalizar texto
# ================================
def normalizar(texto: str) -> str:
    if not isinstance(texto, str):
        return ""
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    ).lower()

# ================================
# 🤖 Función principal con IA
# ================================
def consulta_ia(pregunta_usuario: str):
    pregunta_normalizada = normalizar(pregunta_usuario)

    prompt = f"""
    Eres un experto en el sistema respiratorio humano y controlas luces físicas.
    Responde con:
    - Una explicación breve (máx. 50 palabras).
    - Un JSON con las luces a encender.
    
    ⚡ Importante:
    - Usa siempre la palabra "aire".
    - Termina siempre con: "En la maqueta se visualizan las partes indicadas."
    - Si preguntan por el ciclo de la respiración o flujo de aire, activa todas las zonas.
    """

    try:
        respuesta_api = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful biology assistant."},
                {"role": "user", "content": prompt + f"\n\nPregunta: {pregunta_normalizada}"}
            ],
            response_format={"type": "json_object"}
        )

        respuesta_json = json.loads(respuesta_api.choices[0].message.content)
        explicacion = respuesta_json.get("explicacion", "No se pudo obtener explicación.")
        luces_a_encender = respuesta_json.get("luces_a_encender", [])

        if "En la maqueta se visualizan las partes indicadas." not in explicacion:
            explicacion += " En la maqueta se visualizan las partes indicadas."

        print("\n🤖 Respuesta de la IA:")
        print(f"Explicación: {explicacion}")
        print(f"Luces sugeridas: {luces_a_encender}")

        # 🔦 Control de LEDs
        todas = list(ZONAS_LUCES.keys())
        if sorted(luces_a_encender) == sorted(todas):
            try:
                requests.get(f"http://{ESP32_IP}/flujo", timeout=5)
                print("[OK] Flujo de aire simulado en la maqueta")
            except Exception as e:
                print(f"[ERROR] No se pudo ejecutar flujo: {e}")
        else:
            for zona in ZONAS_LUCES:
                controlar_led(zona, "off")
            for luz in luces_a_encender:
                controlar_led(luz, "on")

        hablar(explicacion)

    except Exception as e:
        print(f"[ERROR IA] {e}")
        for zona in ZONAS_LUCES:
            controlar_led(zona, "off")

# ================================
# 🚀 Programa principal
# ================================
if __name__ == "__main__":
    print("🌬 Sistema respiratorio con LEDs y voz natural.")
    for zona in ZONAS_LUCES:
        controlar_led(zona, "off")
    while True:
        pregunta = input("\n❓ Pregunta (o 'salir' para terminar): ")
        if pregunta.lower() == "salir":
            for zona in ZONAS_LUCES:
                controlar_led(zona, "off")
            print("¡Hasta luego!")
            break
        if pregunta.strip():
            consulta_ia(pregunta)