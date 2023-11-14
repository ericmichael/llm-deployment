from dotenv import load_dotenv

load_dotenv()  # take environment variables from .env.

import os
import whisper
import openai
import gradio as gr
# ---------------------------------------------------------------------------------------
model = whisper.load_model("base")

def transcribe(audio):
    result = model.transcribe(audio)
    return result["text"]
# ---------------------------------------------------------------------------------------
# Define a function to get the AI's reply using the OpenAI API
def get_ai_reply(
    message,
    model="gpt-3.5-turbo",
    system_message=None,
    temperature=0,
    message_history=[],
):
    # Initialize the messages list
    messages = []

    # Add the system message to the messages list
    if system_message is not None:
        messages += [{"role": "system", "content": system_message}]

    # Add the message history to the messages list
    if message_history is not None:
        messages += message_history

    if message is not None:
        # Add the user's message to the messages list
        messages += [{"role": "user", "content": message}]

    # Make an API call to the OpenAI ChatCompletion endpoint with the model and messages
    completion = openai.ChatCompletion.create(
        model=model, messages=messages, temperature=temperature
    )

    # Extract and return the AI's response from the API response
    return completion.choices[0].message.content.strip()


# ---------------------------------------------------------------------------------------
# Define a function to handle the chat interaction with the AI model
def chat(message, audio, chatbot_messages, history_state):
    # Initialize chatbot_messages and history_state if they are not provided
    chatbot_messages = chatbot_messages or []
    history_state = history_state or []

    ### NEW
    if audio:
        message = transcribe(audio)

    # Try to get the AI's reply using the get_ai_reply function
    try:
        prompt = """
        You are a helpful AI assistant named Jarvis.        
        """

        ai_reply = get_ai_reply(
            message,
            model="gpt-3.5-turbo-16k",
            system_message=prompt.strip(),
            message_history=history_state,
        )

        # Append the user's message and the AI's reply to the history_state list
        history_state.append({"role": "user", "content": message})
        history_state.append({"role": "assistant", "content": ai_reply})

        # Append the user's message and the AI's reply to the chatbot_messages list for the UI
        chatbot_messages.append((message, ai_reply))

        # Return None (empty out the user's message textbox), the updated chatbot_messages, and the updated history_state
    except Exception as e:
        # If an error occurs, raise a Gradio error
        raise gr.Error(e)

    return None, None, chatbot_messages, history_state


# Define a function to launch the chatbot interface using Gradio
def get_chatbot_app():
    # Create the Gradio interface using the Blocks layout
    with gr.Blocks() as app:
        # Create a chatbot interface for the conversation
        chatbot = gr.Chatbot(label="Conversation")
        # Create a microphone input for the user's message
        audio = gr.Audio(source="microphone", type="filepath")
        # Create a textbox for the user's message
        message = gr.Textbox(label="Message")
        # Create a state object to store the conversation history
        history_state = gr.State()
        # Create a button to send the user's message
        btn = gr.Button(value="Send")

        # Connect the send button to the chat function
        btn.click(
            chat,
            inputs=[message, audio, chatbot, history_state],
            outputs=[message, audio, chatbot, history_state],
        )
        # Return the app
        return app


# ---------------------------------------------------------------------------------------
# Call the launch_chatbot function to start the chatbot interface using Gradio
app = get_chatbot_app()
app.queue()  # this is to be able to queue multiple requests at once
app.launch(share=False, debug=True, server_name="0.0.0.0", server_port=7860)
