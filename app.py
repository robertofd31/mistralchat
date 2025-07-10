import streamlit as st
from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage

# --- Configuración de la Página y Título ---
st.set_page_config(page_title="Chat con Mistral", page_icon="🤖")
st.title("💬 Chat con Mistral AI")
st.caption("Una aplicación de chat para conversar con los modelos de Mistral AI.")

# --- Gestión de la API Key de Mistral ---
# Se busca la clave de API en los secretos de Streamlit, que es la forma segura de manejarla en producción.
# Como alternativa para desarrollo local, permite ingresarla en la barra lateral.
try:
    mistral_api_key = st.secrets["MISTRAL_API_KEY"]
except KeyError:
    st.warning("La API Key de Mistral no se encontró en los secretos. Por favor, ingrésala abajo.")
    mistral_api_key = st.sidebar.text_input("Introduce tu API Key de Mistral", type="password", help="Obtén tu clave en https://console.mistral.ai/")

if not mistral_api_key:
    st.info("Por favor, introduce tu API Key para comenzar.")
    st.stop()

# --- Selección del Modelo ---
st.sidebar.title("Configuración")
model_selection = st.sidebar.selectbox(
    "Elige un modelo de Mistral:",
    (
        "mistral-large-latest", # El más potente
        "mistral-medium-latest",
        "mistral-small-latest", # El más rápido
        "open-mixtral-8x7b",
        "open-mistral-7b"
    )
)

# --- Inicialización del Cliente y el Historial del Chat ---
try:
    client = MistralClient(api_key=mistral_api_key)
except Exception as e:
    st.error(f"No se pudo inicializar el cliente de Mistral. Verifica tu API Key. Error: {e}")
    st.stop()

# Usamos st.session_state para mantener el historial de mensajes entre interacciones.
if "messages" not in st.session_state:
    # El historial comienza con un mensaje del sistema para guiar al asistente.
    st.session_state.messages = [ChatMessage(role="system", content="Eres un asistente útil y amigable.")]

# --- Mostrar Mensajes Anteriores ---
# Itera sobre los mensajes guardados en st.session_state y los muestra en la interfaz.
for message in st.session_state.messages:
    # No mostramos el mensaje inicial del "system" en el chat.
    if message.role != "system":
        with st.chat_message(message.role):
            st.markdown(message.content)

# --- Entrada del Usuario y Generación de Respuesta ---
# st.chat_input crea un campo de texto fijo en la parte inferior de la pantalla.
if prompt := st.chat_input("¿En qué puedo ayudarte?"):
    # 1. Añadir y mostrar el mensaje del usuario.
    st.session_state.messages.append(ChatMessage(role="user", content=prompt))
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Generar y mostrar la respuesta del asistente.
    with st.chat_message("assistant"):
        # Placeholder para la respuesta mientras se genera.
        message_placeholder = st.empty()
        full_response = ""

        # Llamada a la API de Mistral en modo streaming.
        try:
            stream_response = client.chat_stream(
                model=model_selection,
                messages=st.session_state.messages
            )

            # Iterar sobre los chunks de la respuesta y mostrarlos en tiempo real.
            for chunk in stream_response:
                # Asegurarse de que el chunk tiene contenido y no es solo una señal de finalización.
                if chunk.choices[0].delta.content is not None:
                    full_response += chunk.choices[0].delta.content
                    message_placeholder.markdown(full_response + "▌") # El cursor indica que está escribiendo.
            
            message_placeholder.markdown(full_response) # Respuesta final sin cursor.

        except Exception as e:
            st.error(f"Ocurrió un error al contactar la API de Mistral: {e}")
            # Si hay un error, eliminamos el último mensaje del usuario para que pueda intentarlo de nuevo.
            st.session_state.messages.pop()
            st.stop()


    # 3. Añadir la respuesta completa del asistente al historial.
    st.session_state.messages.append(ChatMessage(role="assistant", content=full_response))
