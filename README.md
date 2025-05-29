# Streamlit AI Chat Demo

This repository contains a demonstration of a simple AI chat application built with Streamlit in Python, showcasing different communication protocols for interacting with a backend service: WebSocket, REST API, and GraphQL.

## Project Overview

The goal of this project is to illustrate how a Streamlit frontend can communicate with a backend to power a conversational AI experience. Each version demonstrates a distinct method of sending user messages and receiving AI responses, including handling dynamic "answer options" from the AI.

## Features

* **Interactive Chat Interface:** A user-friendly chat interface built with Streamlit.
* **User Input:** Allows users to type messages.
* **AI Responses:** Displays responses from the AI backend.
* **Dynamic Answer Options:** Presents clickable buttons for pre-defined AI responses or follow-up questions.
* **Connection Status:** Provides visual feedback on the connection status to the backend.

## Prerequisites

To run any of the application versions, you'll need:

* Python 3.7+
* `pip` (Python package installer)
* A compatible backend service (e.g., a NestJS application) that implements the necessary endpoints for each communication protocol (WebSocket, REST, GraphQL).
* A `.env` file in the root directory of your Streamlit application with the appropriate host and port configurations for your backend.

### Example `.env` File:

```dotenv
# For WebSocket Version
API_HOST=http://localhost
API_WS_PORT=3012

# For REST API Version
# API_HOST=http://localhost
API_REST_PORT=3010

# For GraphQL Version
# API_HOST=http://localhost
API_GRAPHQL_PORT=3011
```

## Setup

1.  **Clone the repository (or save the code files):**
    If this were a full repository, you would clone it:

    ```bash
    git clone https://github.com/ganonym741/Streamlit-chat-assistant.git
    cd Streamlit-chat-assistant
    ```

    For now, ensure you have the Python script for the desired version in your working directory.

2.  **Install dependencies:**
    The required libraries depend on the version you want to run.

    * **For WebSocket Version:**

        ```bash
        pip install streamlit python-dotenv "python-socketio[client]"
        ```

    * **For REST API Version:**

        ```bash
        pip install streamlit python-dotenv requests
        ```

    * **For GraphQL Version:**

        ```bash
        pip install streamlit python-dotenv gql httpx
        ```

    If you plan to switch between versions, it's safest to install all of them:

    ```bash
    pip install streamlit python-dotenv "python-socketio[client]" requests gql httpx
    ```

3.  **Create `.env` file:**
    Create a file named `.env` in the same directory as your Streamlit application script and populate it with the appropriate `API_HOST` and port for the backend you intend to connect to (as shown in the example above).


## Application Versions

### 1. WebSocket Version (`ws-app.py`)

This version uses WebSockets for real-time, bi-directional communication with the backend. It's ideal for applications requiring immediate updates and persistent connections, like chat.

* **How it Works:**

    * A `socketio.Client` is initialized in a separate thread to maintain a persistent connection.

    * User messages are sent via `sio.emit('createChat', ...)`.

    * AI responses and answer options are received via the `sio.on('messageReply')` event listener.

    * A `queue` is used to safely pass messages from the WebSocket thread to the main Streamlit thread for UI updates.

* **Benefits:**

    * Low latency for real-time interactions.

    * Efficient for frequent, small data exchanges.

* **Backend Expectation:** Requires a WebSocket server (e.g., NestJS using `@nestjs/platform-socket.io`) that emits `messageReply` events and listens for `createChat` events.

* **To Run:**

    ```bash
    streamlit run ws-app.py
    ```

### 2. REST API Version (`restapi-app.py`)

This version uses traditional RESTful HTTP requests for communication. It's a common and straightforward approach for many web services.

* **How it Works:**

    * User messages trigger an HTTP `POST` request to a specific backend endpoint (e.g., `/api/chat`).

    * The Streamlit application waits for the HTTP response, which contains the AI's message and any answer options.

    * The `requests` library is used for making synchronous HTTP calls.

* **Benefits:**

    * Simplicity and wide adoption.

    * Stateless nature, making it easier to scale horizontally for some use cases.

* **Backend Expectation:** Requires a standard HTTP server (e.g., NestJS using `@nestjs/common` `Controller` and `Post` decorators) that accepts `POST` requests to a defined endpoint (e.g., `/api/chat`) and returns a JSON response.

* **To Run:**

    ```bash
    streamlit run restapi-app.py
    ```

### 3. GraphQL Version (`graphql-app.py`)

This version leverages GraphQL, a query language for APIs, allowing the client to request exactly the data it needs.

* **How it Works:**

    * All interactions go through a single GraphQL endpoint (e.g., `/graphql`).

    * User messages are sent as part of a GraphQL **mutation** (e.g., `createChat`).

    * The mutation's response explicitly defines the structure of the data expected back (e.g., `answers` and `answerOptions`).

    * The `gql` library with `httpx` (for async operations) is used to construct and send GraphQL requests.

* **Benefits:**

    * **Efficient Data Fetching:** Prevents over-fetching or under-fetching of data.

    * **Strongly Typed Schema:** Provides a clear contract between frontend and backend, improving development predictability.

    * **Flexible API Evolution:** Easier to add new features without breaking existing clients.

* **Backend Expectation:** Requires a GraphQL server (e.g., NestJS using `@nestjs/graphql` with Apollo or Mercurius) that defines a schema with a `createChat` mutation and corresponding types for responses.

* **To Run:**

    ```bash
    streamlit run graphql-app.py
    ```

---
## Future Improvements / Features

This demo provides a solid foundation, but there are many ways to enhance it:

* **Streaming Responses:**
    * [ ] For REST and GraphQL versions, implement server-sent events (SSE) or GraphQL subscriptions to allow the AI response to stream character by character, similar to how the WebSocket version might behave, for a more dynamic user experience.

* **Multimedia Support:**
    * [ ] **Send Images:** Allow users to upload and send images to the AI backend.
    * [ ] **Receive Images:** Display images sent by the AI.
    * [ ] **Send Voice Notes:** Implement recording and sending of audio messages (voice notes).
    * [ ] **Receive Voice Notes:** Playback audio messages from the AI.
    * [ ] **Send Videos:** Allow users to upload and send short video clips.
    * [ ] **Receive Videos:** Display video content sent by the AI.

* **AI Response Feedback:**
    * [ ] Implement a mechanism for users to provide feedback on AI responses (e.g., "thumbs up/down", star ratings, or a short text input for comments) to help improve model performance.

* **User Authentication:**
    * [ ] Implement user login/registration to personalize chat experiences and store user-specific chat histories.

* **Persistent Chat History:**
    * [ ] Integrate a database (e.g., PostgreSQL, MongoDB, Firestore) on the backend to store chat messages, allowing users to resume conversations.

* **Improved UI/UX:**
    * [ ] More sophisticated loading indicators.
    * [ ] Scroll to bottom automatically on new messages.
    * [ ] Better styling and responsiveness for various screen sizes.
    * [ ] Markdown rendering for AI responses to support rich text.

* **Error Handling and Retries:**
    * [ ] More robust error handling for network issues and backend errors, with retry mechanisms.
