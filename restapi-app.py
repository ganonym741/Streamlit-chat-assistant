import streamlit as st
import requests
import os
from dotenv import load_dotenv

load_dotenv()

# --- INITIAL SCRIPT START ---

st.set_page_config(page_title="Demo AI Chat")
st.title("Buid with Streamlit and REST API")

# --- Session State Setup ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "connected" not in st.session_state:
    st.session_state.connected = False
if "current_ai_response" not in st.session_state:
    st.session_state.current_ai_response = ""
if "current_ai_name" not in st.session_state:
    st.session_state.current_ai_name = "assistant"
if "ai_response_placeholder" not in st.session_state:
    st.session_state.ai_response_placeholder = None
if "current_answer_options" not in st.session_state:
    st.session_state.current_answer_options = []

# --- REST API Configuration ---
# Assuming your NestJS backend has an endpoint like /api/chat that accepts POST requests
# and returns a JSON response similar to your WebSocket 'messageReply' structure.
NESTJS_REST_API_URL = os.getenv("API_HOST") + ":" + os.getenv("API_REST_PORT") + "/api/chat"

# --- Function to send message to REST API ---
def send_message_to_api(message_content, story_id="STRY1"):
    headers = {"Content-Type": "application/json"}
    payload = {"storyId": story_id, "message": message_content}
    
    try:
        response = requests.post(NESTJS_REST_API_URL, json=payload, headers=headers, timeout=10)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
        st.session_state.connected = True
        return response.json()
    except requests.exceptions.ConnectionError as e:
        st.error(f"Connection error: Could not connect to the backend. Please ensure the server is running at {NESTJS_REST_API_URL}. Error: {e}")
        st.session_state.connected = False
        return None
    except requests.exceptions.Timeout:
        st.error(f"Request timed out. The server took too long to respond from {NESTJS_REST_API_URL}.")
        st.session_state.connected = False
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"An error occurred during the API request: {e}")
        st.session_state.connected = False
        return None

# --- Process API Response ---
def process_api_response(data):
    if data is None:
        return

    answers = data.get('answers', [])
    answer_options = data.get('answerOptions', {})

    if isinstance(answers, list):
        for item in answers:
            if isinstance(item, dict) and 'name' in item and 'message' in item:
                name = item.get('name', 'assistant')
                message = item.get('message', '')
                if message.strip():
                    st.session_state.messages.append({"role": name, "content": message})
            else:
                print(f"--- WARNING: Received malformed item in answers array: {item} ---")
    else: # Handle single object response for 'answers'
        name = answers.get('name', 'assistant')
        message = answers.get('message', '')
        if message.strip():
            st.session_state.messages.append({"role": name, "content": message})
    
    # Reset current AI response and options state before processing new ones
    st.session_state.current_ai_response = ""
    st.session_state.current_ai_name = "assistant"
    st.session_state.ai_response_placeholder = None
    st.session_state.current_answer_options = [] # Clear existing options

    if isinstance(answer_options, dict):
        is_needed = answer_options.get('isNeeded', False)
        options = answer_options.get('options', [])

        if is_needed and isinstance(options, list) and len(options) > 0:
            st.session_state.current_answer_options = options
            print(f"--- Extracted answerOptions: {options} ---")

    st.rerun() # Rerun to update the UI with new messages/options


# --- UI Rendering Section ---
for i, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Placeholder for AI's streamed response (less relevant with REST, but kept for consistency)
if st.session_state.current_ai_response:
    with st.chat_message(st.session_state.current_ai_name):
        if st.session_state.ai_response_placeholder is None:
            st.session_state.ai_response_placeholder = st.empty()
        st.session_state.ai_response_placeholder.markdown(st.session_state.current_ai_response)

# --- Render answer options as buttons ---
if st.session_state.current_answer_options:
    print(f"--- Main Thread: Rendering answer options: {st.session_state.current_answer_options} ---")
    with st.container():
        st.write("---") # Separator for options
        st.markdown("Choose an option:")
        cols = st.columns(len(st.session_state.current_answer_options))

        for i, option_text in enumerate(st.session_state.current_answer_options):
            with cols[i]:
                if st.button(option_text, key=f"option_button_{i}"):
                    print(f"--- Main Thread: Option button clicked: '{option_text}' ---")
                    st.session_state.messages.append({"role": "user", "content": option_text})
                    st.session_state.current_answer_options = [] # Clear options immediately

                    api_response_data = send_message_to_api(option_text)
                    if api_response_data:
                        process_api_response(api_response_data) # This will rerun
                    else:
                        st.rerun() # Rerun to update connection status/error if API call failed
else:
    print("--- Main Thread: No answer options to render. ---")
    
# Status messages
if not st.session_state.connected:
    st.error("Not connected to backend or connection failed. Please ensure the NestJS REST API server is running and try refreshing.")
else:
    st.success("Connected to backend.")


# User input and send message
if st.session_state.connected and not st.session_state.current_answer_options:
    if prompt := st.chat_input("Say something"):
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Send message via REST API
        api_response_data = send_message_to_api(prompt)
        if api_response_data:
            process_api_response(api_response_data) # This will rerun
        else:
            st.rerun() # Rerun to update connection status/error if API call failed

elif not st.session_state.connected:
    st.info("Attempting to connect to backend...")
    # You might want to trigger an initial connection check here if desired
    # For a simple chat, the first user input or button click will test the connection.
    if not st.session_state.messages and not st.session_state.current_answer_options:
        st.info("Enter a message to initiate communication.")
elif st.session_state.current_answer_options:
    st.chat_input("Choose from options above...", disabled=True)