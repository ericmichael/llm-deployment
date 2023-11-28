from dotenv import load_dotenv
from utils.user_manager import UserManager
from utils.vector_collection import Document, VectorCollection

load_dotenv()  # take environment variables from .env.
import json
import whisper
import gradio as gr
import logging

from agent import Agent

# Set up logging
logging.basicConfig(filename='app.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Load whisper model
try:
    model = whisper.load_model("base") # needs to be outside since loading is expensive
except Exception as e:
    logging.error(f"Error loading whisper model: {e}")
    raise

def load_data():
    try:
        with open("data/data.json") as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        logging.error("Error: data file not found.")
        raise
    except json.JSONDecodeError:
        logging.error("Error: could not decode JSON.")
        raise

def transcribe(audio):
    result = model.transcribe(audio)
    return result["text"]

def chat(agent, message, audio, chatbot_messages, history_state):
    chatbot_messages = chatbot_messages or []
    history_state = history_state or []
    
    if audio:
        message = transcribe(audio)

    try:
        ai_reply = agent.chat(message)
        chatbot_messages.append((message, ai_reply))
    except Exception as e:
        raise gr.Error(e)
        
    return None, None, chatbot_messages, history_state

def get_chatbot_app(user_manager, vdb_collection):
    def is_admin(username):
        return user_manager.authorize(username, 'admin')
    
    def add_user(username, password, role):
        user_manager.add_user(username, password, role)
        return user_manager.load_users()
    
    def remove_user(username):
        user_manager.remove_user(username)
        return user_manager.load_users()

    def check_admin_status(request: gr.Request):
        username = request.username
        if username and is_admin(username):
            return gr.Row(visible=True)
        else:
            return gr.Row(visible=False)
        
    def get_agent():
        return Agent(tools={
            "search_food": {
                "params": "query",
                "description": """Tool to lookup food based close to the user based on their query. Use this tools when the user is looking for food suggestions near them. You don't need to know the user's location, the tool doesn't need it. Be careful, the tool will return the top results in the database but not all of them may be relevant. Use your judgement when answering the user's question. Example: search_food("place to get a good burger and craft beer")""",
                "function": vdb_collection.search 
            }
        })

    with gr.Blocks() as app:
        agent = gr.State(value=get_agent)
        with gr.Tab("Main"):
            chatbot = gr.Chatbot(label="Conversation")
            audio = gr.Audio(source="microphone", type="filepath")
            message = gr.Textbox(label="Message")
            history_state = gr.State()
            btn = gr.Button(value="Send")

            btn.click(
                chat,
                inputs=[agent, message, audio, chatbot, history_state],
                outputs=[message, audio, chatbot, history_state],
            )
        with gr.Tab("More"):
            with gr.Row(visible=False) as manage_users_row:
                with gr.Column():
                    users = gr.DataFrame(label="Users", value=user_manager.load_users(), interactive=False, headers=["Username", "Role"])
                with gr.Column():
                    with gr.Group():
                        username_add = gr.Textbox(label="Username")
                        password_add = gr.Textbox(label="Password", type="password")
                        role_add = gr.Dropdown(label="Role", choices=["Admin", "User"])
                        add_user_btn = gr.Button(value="Add")
                        add_user_btn.click(add_user, inputs=[username_add, password_add, role_add], outputs=[users])
                with gr.Column():
                    with gr.Group():
                        username_delete = gr.Textbox(label="Username")
                        remove_user_btn = gr.Button(value="Remove")
                        remove_user_btn.click(remove_user, inputs=[username_delete], outputs=[users])
                app.load(check_admin_status, inputs=None, outputs=[manage_users_row])
        return app

try:
    user_manager = UserManager()
    user_manager.seed_database()
except Exception as e:
    logging.error(f"Error initializing UserManager: {e}")
    raise

try:
    vdb_collection = VectorCollection(collection_name="food")
    data = load_data()
        
    for i, restaurant in enumerate(data):
        vdb_collection.add(Document(i, restaurant))
except Exception as e:
    logging.error(f"Error initializing VectorCollection: {e}")
    raise

try:
    app = get_chatbot_app(user_manager, vdb_collection)
    app.queue()
    app.launch(auth=user_manager.authenticate, share=False, debug=True, server_name="0.0.0.0", server_port=7860)
except Exception as e:
    logging.error(f"Error launching app: {e}")
    raise