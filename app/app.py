from dotenv import load_dotenv

load_dotenv()  # take environment variables from .env.
import os
import re

import whisper
import openai
import requests
import geocoder
import gradio as gr

from elevenlabs import set_api_key
from elevenlabs import generate, play
from serpapi import GoogleSearch
from datetime import datetime
from datetime import timedelta

set_api_key(os.getenv("ELEVENLABS_API_KEY"))
model = whisper.load_model("base")


# ---------------------------------------------------------------------------------------
# given a city name, returns latitude and longitude of top results
def geocode(city_name):
    url = f"https://geocoding-api.open-meteo.com/v1/search?name={city_name}&count=10&language=en&format=json"

    try:
        response = requests.get(url)

        # If the response was successful, no Exception will be raised
        response.raise_for_status()
    except HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
    except Exception as err:
        print(f"Other error occurred: {err}")
    else:
        return response.json()  # If successful, return json response


# returns the weather for a particular latitude and longitude
def weather(latitude, longitude):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current=temperature_2m,is_day,precipitation,rain,showers,snowfall&timezone=America%2FChicago"

    try:
        response = requests.get(url)

        # If the response was successful, no Exception will be raised
        response.raise_for_status()
    except HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
    except Exception as err:
        print(f"Other error occurred: {err}")
    else:
        return response.json()  # If successful, return json response


# gets todays date
def get_todays_date():
    return datetime.now().strftime("%B %d, %Y")


# gets tomorrows date
def get_tomorrows_date():
    now = datetime.now()
    tomorrow = now + timedelta(days=1)
    return tomorrow.strftime("%B %d, %Y")


# gets the current time
def get_current_time():
    return datetime.now().strftime("%m/%d/%Y %-I:%M %p")


# finds your city and state based on your IP address
def user_location():
    g = geocoder.ip("me")
    city = g.city
    state = g.state
    return f"{city}, {state}"


# searches Google Local results
def search_google_local(query):
    search = GoogleSearch(
        {
            "q": query,
            "location": user_location(),
            "api_key": os.getenv("SERPAPI_API_KEY"),
        }
    )
    result = search.get_dict()
    return result["local_results"]["places"]


def search_google_web(query):
    search = GoogleSearch(
        {
            "q": query,
            "location": user_location(),
            "api_key": os.getenv("SERPAPI_API_KEY"),
        }
    )
    result = search.get_dict()
    return result["organic_results"]


# searches Google News and returns the results
def search_google_news(query):
    search = GoogleSearch(
        {
            "q": query,  # search search
            "tbm": "nws",  # news
            "tbs": "qdr:d",  # last 24h
            "location": user_location(),
            "api_key": os.getenv("SERPAPI_API_KEY"),
            "num": 10,
        }
    )
    data = search.get_dict()
    return data["news_results"]


# def speak(text):
#     audio = generate(
#       text=text,
#       voice="Bella",
#       model="eleven_multilingual_v2"
#     )

#     play(audio)


# ---------------------------------------------------------------------------------------
def transcribe(audio):
    result = model.transcribe(audio)
    return result["text"]


def needs_tool(response):
    return "Tool:" in response


def extract_call(string):
    # regex pattern
    pattern = r"Tool: (\w+)\((.*?)\)"
    match = re.search(pattern, string)
    if match:
        tool_name = match.group(1)
        parameters = match.group(2).replace('"', "").split(", ")
        return tool_name, parameters
    else:
        return None, None


def invoke_tool(response):
    tool_name, parameters = extract_call(response)

    if tool_name == "geocode":
        tool_result = geocode(*parameters)
    elif tool_name == "weather":
        tool_result = weather(*parameters)
    elif tool_name == "search_google_web":
        tool_result = search_google_web(*parameters)

    return tool_result


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

        Your knowledge cut-off is: September 2021
        
        You do have access to the following real-time information:
        - Current date and time: {date}
        - My location: {location}

        ## Tools

        You have access to the following tools:
        - geocode(city): Tool to lookup the latitude and longitide of a US city. Does not accept state in the parameter. Do not specify the state. Example: geocode("New York")
        - weather(lat, long): Tool to lookup weather for a specific latitude and longitude. Example: weather(52.52, 13.41)
        - search_google_web(query): Tool to search on google to look up real-time information. Use this tool when you need to access to real time information such as current events, local and national news, general information . Example: search_google_web("Who won the 2002 World Cup?")

        ## Tool Rules

        When the user asks a question that can be answered by using a tool, you MUST do so. Do not answer from your training data. 
        Infer what tool to be used based on the conversation and follow through with execution of the tool without asking for permission.
        If you suspect a tool can be used, USE IT.

        ## Using Tools

        To use a tool, reply with the following prefix "Tool: " then append the tool call (like a function call). 

        Behind the scenes, your software will pickup that you want to invoke a tool and invoke it for you and provide you the response.

        ## Using Tool Responses

        Answer the user's question using the response from the tool. Feel free to make it conversational. 

        ## Chaining Tools

        You are allowed to chain together multiple calls to tools before giving an answer, if needed.
        
        ## Responses
        
        Aside from when you decide to invoke a tool, your responses are being spoken outloud by a "Text-to-Speech" engine.
        When producing your responses make sure to write them in the way you intend for them to be spoken out loud.
        For example, 11/1/2023 should respond with November 1st, 2023.
        
        
        """.format(
            date=get_current_time(), location=user_location()
        )
        ai_reply = get_ai_reply(
            message,
            model="gpt-3.5-turbo-16k",
            system_message=prompt.strip(),
            message_history=history_state,
        )

        # Append the user's message and the AI's reply to the history_state list
        history_state.append({"role": "user", "content": message})
        history_state.append({"role": "assistant", "content": ai_reply})

        while needs_tool(ai_reply):
            tool_result = invoke_tool(ai_reply)
            history_state.append(
                {"role": "assistant", "content": f"Tool Result: {tool_result}"}
            )
            ai_reply = get_ai_reply(
                None,
                model="gpt-3.5-turbo-16k",
                system_message=prompt.strip(),
                message_history=history_state,
            )
            history_state.append({"role": "assistant", "content": ai_reply})

        ## NEW!!
        # speak(ai_reply)

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
app.launch(share=False, debug=True)
