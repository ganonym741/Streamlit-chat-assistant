import streamlit as st
import socketio
import threading
import queue
import time
import os
from dotenv import load_dotenv

load_dotenv()

# --- INITIAL SCRIPT START ---

st.set_page_config(page_title="Demo AI Chat")
st.title("Buid with Streamlit and WebSocket")

# --- Session State Setup ---
# print("--- Setting up session state ---")
if "messages" not in st.session_state:
    st.session_state.messages = []
if "sio" not in st.session_state:
    st.session_state.sio = None
if "connected" not in st.session_state:
    st.session_state.connected = False
if "current_ai_response" not in st.session_state:
    st.session_state.current_ai_response = ""
if "current_ai_name" not in st.session_state:
    st.session_state.current_ai_name = "assistant"
if "ai_response_placeholder" not in st.session_state:
    st.session_state.ai_response_placeholder = None
if "message_queue" not in st.session_state:
    st.session_state.message_queue = queue.Queue()
if "websocket_thread" not in st.session_state:
    st.session_state.websocket_thread = None
if "current_answer_options" not in st.session_state:
    st.session_state.current_answer_options = []

# --- WebSocket Client Logic ---
NESTJS_WEBSOCKET_URL = os.getenv("API_HOST") + ":" + os.getenv("API_WS_PORT")

def websocket_thread_function(q):
    sio = socketio.Client()

    @sio.event
    def connect():
        # print("--- WebSocket Thread: CONNECTED to WebSocket server! ---")
        q.put({"type": "status", "connected": True})

    @sio.event
    def disconnect():
        # print("--- WebSocket Thread: DISCONNECTED from WebSocket server! ---")
        q.put({"type": "status", "connected": False})
        q.put({"type": "sio_clear"})

    @sio.event
    def connect_error(data):
        # print(f"--- WebSocket Thread: CONNECTION ERROR! Data: {data} ---")
        q.put({"type": "status", "connected": False, "error": f"Connection failed: {data}"})
        q.put({"type": "sio_clear"})

    @sio.on('messageReply')
    def on_create_chat(data):
        # print(f"--- WebSocket Thread: RECEIVED MESSAGE! Data: {data} ---")
        answers = data.get('answers', [])
        answer_options = data.get('answerOptions', {})

        if isinstance(answers, list): # Check if the received data is a list
            for item in answers: # Iterate through each item in the list
                if isinstance(item, dict) and 'name' in item and 'message' in item:
                    name = item.get('name', 'assistant')
                    message = item.get('message', '')
                    q.put({"type": "final_ai_response", "content": message, "name": name})
                else:
                    print(f"--- WebSocket Thread: WARNING: Received malformed item in createChat array: {item} ---")
        else:
            name = answers.get('name', 'assistant')
            message = answers.get('message', '')
            q.put({"type": "final_ai_response", "content": message, "name": name})
        
        if isinstance(answer_options, dict):
            is_needed = answer_options.get('isNeeded', False)
            options = answer_options.get('options', [])

            if is_needed and isinstance(options, list) and len(options) > 0:
                print(f"--- WebSocket Thread: Extracted answerOptions: {options} ---")
                q.put({"type": "answer_options", "options": options})

    try:
        sio.connect(NESTJS_WEBSOCKET_URL)
        q.put({"type": "sio_set", "sio_object": sio})

        while True:
            sio.sleep(0.1)

    except Exception as e:
        q.put({"type": "status", "connected": False, "error": f"Failed to connect or runtime error: {e}"})
        q.put({"type": "sio_clear"})


# --- Handle messages from the WebSocket queue in the main Streamlit thread ---
def process_queue_messages():
    rerun_needed = False
    while not st.session_state.message_queue.empty():
        msg = st.session_state.message_queue.get()

        if msg["type"] == "status":
            if st.session_state.connected != msg["connected"]:
                st.session_state.connected = msg["connected"]
                rerun_needed = True
            if "error" in msg:
                st.error(msg["error"])

        elif msg["type"] == "sio_set":
            st.session_state.sio = msg["sio_object"]
            rerun_needed = True
        elif msg["type"] == "sio_clear":
            st.session_state.sio = None
            rerun_needed = True

        elif msg["type"] == "final_ai_response":
            content = msg.get('content', '')
            name = msg.get('name', 'assistant')

            if not content.strip():
                continue

            st.session_state.messages.append({"role": name, "content": content})

            st.session_state.current_ai_response = ""
            st.session_state.current_ai_name = "assistant"
            st.session_state.ai_response_placeholder = None
            st.session_state.current_answer_options = []
            rerun_needed = True
        
        elif msg["type"] == "answer_options":
            options = msg.get('options', [])
            if isinstance(options, list) and len(options) > 0:
                st.session_state.current_answer_options = options
                st.session_state.current_ai_response = ""
                st.session_state.ai_response_placeholder = None
                rerun_needed = True

    return rerun_needed


# --- Thread Management and Rerun Trigger ---
if st.session_state.sio is None and not st.session_state.connected and \
   (st.session_state.websocket_thread is None or not st.session_state.websocket_thread.is_alive()):
    st.info("Attempting to connect to backend...")
    thread = threading.Thread(target=websocket_thread_function, args=(st.session_state.message_queue,), daemon=True)
    thread.start()
    st.session_state.websocket_thread = thread
    time.sleep(0.1)

if process_queue_messages():
    st.rerun()
else:
    print("--- Main Thread: process_queue_messages() returned False. No st.rerun() triggered from queue. ---")


# --- UI Rendering Section ---
for i, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Placeholder for AI's streamed response
if st.session_state.current_ai_response:
    with st.chat_message(st.session_state.current_ai_name):
        if st.session_state.ai_response_placeholder is None:
            st.session_state.ai_response_placeholder = st.empty()
        st.session_state.ai_response_placeholder.markdown(st.session_state.current_ai_response)
else:
    print("--- Main Thread: No current_ai_response to render. ---")

# --- NEW: Render answer options as buttons ---
if st.session_state.current_answer_options:
    print(f"--- Main Thread: Rendering answer options: {st.session_state.current_answer_options} ---")
    # Use st.container() for better layout control
    with st.container():
        st.write("---") # Separator for options
        st.markdown("Choose an option:")
        cols = st.columns(len(st.session_state.current_answer_options)) # Create columns for buttons

        for i, option_text in enumerate(st.session_state.current_answer_options):
            # Place button in a column
            with cols[i]:
                if st.button(option_text, key=f"option_button_{i}"): # Use unique key for each button
                    print(f"--- Main Thread: Option button clicked: '{option_text}' ---")
                    # Append chosen option as a user message
                    st.session_state.messages.append({"role": "user", "content": option_text})

                    # Clear the options so buttons disappear
                    st.session_state.current_answer_options = []

                    # Send the chosen option back to the server
                    if st.session_state.sio:
                        try:
                            st.session_state.sio.emit('createChat', {"storyId": "STRY1", "message": option_text})
                            print(f"--- Main Thread: Emitted '{option_text}' from option button. ---")
                        except Exception as e:
                            st.error(f"Error sending option message: {e}")
                            st.session_state.connected = False
                            st.session_state.sio = None
                    st.rerun()
else:
    print("--- Main Thread: No answer options to render. ---")

    
# Status messages
if not st.session_state.connected and (st.session_state.websocket_thread is None or not st.session_state.websocket_thread.is_alive()):
    st.error("Not connected to backend. Ensure NestJS server is running and try refreshing.")
elif not st.session_state.connected and st.session_state.websocket_thread is not None and st.session_state.websocket_thread.is_alive():
    st.warning("Connecting to backend... (Please wait)")
elif not st.session_state.connected and st.session_state.websocket_thread is not None and not st.session_state.websocket_thread.is_alive():
    st.error("Backend connection failed or disconnected. Please check NestJS server logs.")


# User input and send message
if st.session_state.connected and not st.session_state.current_answer_options:
    if prompt := st.chat_input("Say something"):
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        if st.session_state.sio:
            try:
                st.session_state.sio.emit('createChat', {"storyId": "STRY1", "message": prompt})
                st.session_state.current_ai_response = ""
                st.session_state.current_ai_name = "assistant"
                st.session_state.ai_response_placeholder = None
                st.session_state.current_answer_options = []
                st.rerun()
            except Exception as e:
                st.error(f"Error sending message: {e}. Connection lost?")
                st.session_state.connected = False
                st.session_state.sio = None
                st.rerun()
elif not st.session_state.connected:
    st.info("Waiting for connection to establish...")
elif st.session_state.current_answer_options:
    st.chat_input("Choose from options above...", disabled=True)


if st.session_state.connected and not st.session_state.message_queue.empty():
    time.sleep(0.1)
    st.rerun()
elif st.session_state.connected:
    time.sleep(0.05)
    st.rerun()