import streamlit as st
import os
from dotenv import load_dotenv
from gql import Client, gql
from gql.transport.httpx import HTTPXAsyncTransport
import asyncio

load_dotenv()

# --- INITIAL SCRIPT START ---

st.set_page_config(page_title="Demo AI Chat")
st.title("Buid with Streamlit and GraphQL")

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

# --- GraphQL Configuration ---
# Assuming your NestJS backend has a GraphQL endpoint like /graphql
GRAPHQL_URL = os.getenv("API_HOST") + ":" + os.getenv("API_GRAPHQL_PORT") + "/graphql"

# --- GraphQL Client Setup (cached to prevent re-creation on every rerun) ---
@st.cache_resource
def get_graphql_client():
    transport = HTTPXAsyncTransport(url=GRAPHQL_URL)
    return Client(transport=transport, fetch_schema_from_transport=True)

# --- GraphQL Mutation Definition ---
# This is a conceptual mutation. Your actual backend GraphQL schema
# must define a mutation like `createChat` that takes `storyId` and `message`
# and returns `answers` and `answerOptions` with their respective types.
CHAT_MUTATION = gql(
    """
    mutation CreateChatMessage($storyId: String!, $message: String!) {
        createChat(input: { storyId: $storyId, message: $message }) {
            answers {
                name
                message
            }
            answerOptions {
                isNeeded
                options
            }
        }
    }
    """
)

# --- Function to send message to GraphQL API ---
async def send_graphql_message(message_content, story_id="STRY1"):
    client = get_graphql_client()
    variables = {"storyId": story_id, "message": message_content}

    try:
        # Execute the mutation
        response_data = await client.execute_async(CHAT_MUTATION, variable_values=variables)
        st.session_state.connected = True
        return response_data
    except Exception as e:
        st.error(f"GraphQL request failed: {e}")
        st.session_state.connected = False
        return None

# --- Process GraphQL Response ---
def process_graphql_response(data):
    if data is None or 'createChat' not in data:
        print("--- No valid GraphQL response data or 'createChat' field not found ---")
        return

    chat_data = data['createChat']
    answers = chat_data.get('answers', [])
    answer_options = chat_data.get('answerOptions', {})

    # Ensure answers is always a list for consistent processing
    if not isinstance(answers, list):
        answers = [answers]

    for item in answers:
        if isinstance(item, dict) and 'name' in item and 'message' in item:
            name = item.get('name', 'assistant')
            message = item.get('message', '')
            if message.strip():
                st.session_state.messages.append({"role": name, "content": message})
        else:
            print(f"--- WARNING: Received malformed item in answers array: {item} ---")
    
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

    st.rerun()


# --- UI Rendering Section ---
for i, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if st.session_state.current_ai_response:
    with st.chat_message(st.session_state.current_ai_name):
        if st.session_state.ai_response_placeholder is None:
            st.session_state.ai_response_placeholder = st.empty()
        st.session_state.ai_response_placeholder.markdown(st.session_state.current_ai_response)

# --- Render answer options as buttons ---
if st.session_state.current_answer_options:
    print(f"--- Main Thread: Rendering answer options: {st.session_state.current_answer_options} ---")
    with st.container():
        st.write("---")
        st.markdown("Choose an option:")
        cols = st.columns(len(st.session_state.current_answer_options))

        for i, option_text in enumerate(st.session_state.current_answer_options):
            with cols[i]:
                if st.button(option_text, key=f"option_button_{i}"):
                    print(f"--- Main Thread: Option button clicked: '{option_text}' ---")
                    st.session_state.messages.append({"role": "user", "content": option_text})
                    st.session_state.current_answer_options = [] # Clear options immediately

                    asyncio.run(send_graphql_message(option_text))
                    st.rerun()
else:
    print("--- Main Thread: No answer options to render. ---")
    
# Status messages
if not st.session_state.connected:
    st.error("Not connected to backend or connection failed. Please ensure the NestJS GraphQL server is running and try refreshing.")
else:
    st.success("Connected to backend.")


# User input and send message
if st.session_state.connected and not st.session_state.current_answer_options:
    if prompt := st.chat_input("Say something"):
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Send message via GraphQL
        # We need to run the async function using asyncio.run()
        graphql_response_data = asyncio.run(send_graphql_message(prompt))
        if graphql_response_data:
            process_graphql_response(graphql_response_data)
        else:
            st.rerun()

elif not st.session_state.connected:
    st.info("Attempting to connect to backend...")
    if not st.session_state.messages and not st.session_state.current_answer_options:
        st.info("Enter a message to initiate communication.")
elif st.session_state.current_answer_options:
    st.chat_input("Choose from options above...", disabled=True)