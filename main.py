import requests
import unicodedata
import json
import simpleaudio as sa
from openai import OpenAI
import os
import tempfile
from dotenv import load_dotenv
from pydub import AudioSegment  # 👈 Para convertir MP3 → WAV

# ⚡ Cargar variables de entorno desde .env
load_dotenv()

# ⚡ Configura OpenAI con la API Key desde el .env
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ⚡ IP del ESP32
ESP32_IP = "10.20.0.147"

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


# 🔊 Voz con simpleaudio + pydub
def hablar(texto):
    """Convierte texto en voz, convierte MP3 → WAV y lo reproduce"""
    try:
        respuesta_audio = client.audio.speech.create(
            model="gpt-4o-mini-tts",
            voice="alloy",
            input=texto
        )

        # Guardar archivo temporal MP3
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
            f.write(respuesta_audio.read())
            ruta_mp3 = f.name

        # Convertir a WAV
        ruta_wav = ruta_mp3.replace(".mp3", ".wav")
        AudioSegment.from_mp3(ruta_mp3).export(ruta_wav, format="wav")

        # Reproducir con simpleaudio
        wave_obj = sa.WaveObject.from_wave_file(ruta_wav)
        play_obj = wave_obj.play()
        play_obj.wait_done()

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
    - "explicacion": explicación clara de la respuesta.
    - "luces_a_encender": lista de partes del sistema respiratorio relevantes.

    Pregunta del usuario: {pregunta_normalizada}
    """

    try:
        respuesta_api = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful biology assistant."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )

        respuesta_ia_str = respuesta_api.choices[0].message.content
        respuesta_json = json.loads(respuesta_ia_str)

        explicacion = respuesta_json.get("explicacion", "No se pudo obtener explicación.")
        luces_a_encender = respuesta_json.get("luces_a_encender", [])

        if luces_a_encender and "En la maqueta se visualizan las partes indicadas." not in explicacion:
            explicacion += " En la maqueta se visualizan las partes indicadas."

        print("\n🤖 Respuesta de la IA:")
        print(f"Explicación: {explicacion}")
        print(f"Luces sugeridas: {luces_a_encender}")

        # Control de LEDs si hay conexión
        if ESP32_CONECTADO:
            todas_las_zonas = list(ZONAS_LUCES.keys())
            if sorted(luces_a_encender) == sorted(todas_las_zonas):
                try:
                    url_flujo = f"http://{ESP32_IP}/flujo"
                    requests.get(url_flujo, timeout=3)
                    print("[OK] Flujo de aire simulado en la maqueta")
                except Exception as e:
                    print(f"[WARN] No se pudo ejecutar flujo: {e}")
            else:
                # Apagar todas antes
                for zona in ZONAS_LUCES.keys():
                    controlar_led(zona, "off")
                # Encender solo las necesarias
                for luz in luces_a_encender:
                    if luz in ZONAS_LUCES:
                        controlar_led(luz, "on")
        else:
            print("[INFO] ESP32 no disponible. Solo se muestra la explicación.")

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