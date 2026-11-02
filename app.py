import time
import streamlit as st
import speech_recognition as sr
from gtts import gTTS
from deep_translator import GoogleTranslator, MyMemoryTranslator
from io import BytesIO

st.set_page_config(page_title="Traductor de viaje", layout="centered")

st.markdown("""
<style>
.stApp {
    background: linear-gradient(160deg, #e0f4f6, #fff6ee);
}
[data-testid="stHeader"] {
    background: transparent;
}
section[data-testid="stSidebar"] {
    background-color: #cdeef0;
}
h1, h2, h3 {
    color: #0e7c86 !important;
}
div.stButton > button {
    background-color: #ff7f50;
    color: white !important;
    border-radius: 20px;
    border: none;
    padding: 6px 22px;
}
div.stButton > button:hover {
    background-color: #e5603a;
}
</style>
""", unsafe_allow_html=True)

idiomas = {
    "Español": ("es", "es-ES"),
    "Inglés": ("en", "en-US"),
    "Japonés": ("ja", "ja-JP"),
    "Coreano": ("ko", "ko-KR"),
    "Mandarín": ("zh-CN", "zh-CN"),
    "Bengali": ("bn", "bn-BD"),
}

acentos = {
    "Por defecto": "com",
    "México": "com.mx",
    "Reino Unido": "co.uk",
    "Estados Unidos": "com",
    "Canadá": "ca",
    "Australia": "com.au",
    "Irlanda": "ie",
    "Sudáfrica": "co.za",
}

respaldo = {"es": "es-ES", "en": "en-GB", "ja": "ja-JP", "ko": "ko-KR", "zh-CN": "zh-CN", "bn": "bn-IN"}


@st.cache_data(show_spinner=False)
def traducir(texto, origen, destino):
    for intento in range(3):
        try:
            return GoogleTranslator(source=origen, target=destino).translate(texto)
        except Exception:
            time.sleep(2)
    return MyMemoryTranslator(source=respaldo[origen], target=respaldo[destino]).translate(texto)


if "chat" not in st.session_state:
    st.session_state.chat = []
if "entrada" not in st.session_state:
    st.session_state.entrada = "Español"
if "salida" not in st.session_state:
    st.session_state.salida = "Japonés"


def intercambiar():
    st.session_state.entrada, st.session_state.salida = st.session_state.salida, st.session_state.entrada


with st.sidebar:
    st.subheader("Configuración")
    entrada = st.selectbox("Hablo en", list(idiomas.keys()), key="entrada")
    st.button("⇄ Intercambiar idiomas", on_click=intercambiar)
    salida = st.selectbox("Quiero escuchar en", list(idiomas.keys()), key="salida")
    acento = st.selectbox("Acento", list(acentos.keys()))
    lenta = st.toggle("Voz lenta")
    st.caption("El acento cambia el resultado solo en algunos idiomas, como inglés y español.")

st.title("🌍 Traductor de viaje")
st.write("Habla o escribe, y escucha la traducción al instante.")

modo = st.radio("¿Cómo quieres decirlo?", ["🎤 Hablar", "⌨️ Escribir"], horizontal=True)

texto = ""

if modo == "🎤 Hablar":
    grabacion = st.audio_input("Presiona el micrófono y habla")
    if grabacion:
        huella = hash(grabacion.getvalue())
        if st.session_state.get("ultima") != huella:
            st.session_state.ultima = huella
            try:
                grabacion.seek(0)
                r = sr.Recognizer()
                with sr.AudioFile(grabacion) as fuente:
                    datos = r.record(fuente)
                texto = r.recognize_google(datos, language=idiomas[entrada][1])
            except sr.UnknownValueError:
                st.warning("No te entendí, intenta de nuevo.")
            except Exception as e:
                st.error(f"No se pudo reconocer el audio: {e}")
else:
    escrito = st.text_input("Escribe lo que quieres traducir")
    if st.button("Traducir"):
        texto = escrito

if texto.strip() != "":
    try:
        traducido = traducir(texto, idiomas[entrada][0], idiomas[salida][0])
        audio = BytesIO()
        gTTS(traducido, lang=idiomas[salida][0], tld=acentos[acento], slow=lenta).write_to_fp(audio)
        st.session_state.chat.append({
            "de": entrada,
            "a": salida,
            "original": texto,
            "traducido": traducido,
            "audio": audio.getvalue(),
        })
    except Exception as e:
        st.error(f"No se pudo generar la traducción: {e}")

st.divider()

if len(st.session_state.chat) == 0:
    st.write("Tus traducciones aparecerán aquí.")
else:
    if st.button("Borrar conversación"):
        st.session_state.chat = []
        st.rerun()

for item in reversed(st.session_state.chat):
    with st.chat_message("user"):
        st.write(item["original"])
        st.caption(item["de"])
    with st.chat_message("assistant"):
        st.write(item["traducido"])
        st.caption(item["a"])
        st.audio(item["audio"], format="audio/mp3")
