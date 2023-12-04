"""This module contains the Agent class and its helper class ToolInvoker.

The Agent class is responsible for interacting with the user and invoking
the necessary tools based on the user's input. The ToolInvoker class is
used to invoke a specific tool based on the tool's name and parameters.

Typical usage example:

    agent = Agent(tools={
        "search_food": {
            "params": "query",
            "description": "Tool to lookup food based on the user's query.",
            "function": vdb_collection.search 
        }
    })
    response = agent.chat("I'm looking for a good burger place.")
"""
import openai
import re
from django.conf import settings
from ..models import Message

openai.api_base = settings.OPENAI_API_BASE
openai.api_key = settings.OPENAI_API_KEY

class ToolInvoker:
    """A class used to invoke a specific tool based on its name and parameters.

    Attributes:
        tools: A dictionary of tools where the key is the tool's name and the
               value is a dictionary containing the tool's parameters and function.
    """
    def __init__(self, tools):
        self.tools = tools

    def invoke_tool(self, response):
        """Invokes a tool based on the tool's name and parameters found in the response.

        Args:
            response: A string containing the tool's name and parameters.

        Returns:
            The result of the tool's function.

        Raises:
            ValueError: If the tool's name is not found in the tools dictionary.
        """
        tool_name, parameters = self._extract_call(response)
        if tool_name in self.tools:
            tool_function = self.tools[tool_name]['function']
            return tool_function(*parameters)
        else:
            raise ValueError(f"Unknown tool: {tool_name}")

    def _extract_call(self, string):
        """Extracts the tool's name and parameters from a string.

        Args:
            string: A string containing the tool's name and parameters.

        Returns:
            A tuple containing the tool's name and a list of parameters.
        """
        pattern = r'Tool: (\w+)\((.*?)\)'
        match = re.search(pattern, string)
        if match:
            tool_name = match.group(1)
            parameters = match.group(2).replace('"', '').split(', ')
            return tool_name, parameters
        else:
            return None, None
        
class Agent:
    """A class used to interact with the user and invoke the necessary tools.

    Attributes:
        tools: A dictionary of tools where the key is the tool's name and the
               value is a dictionary containing the tool's parameters and function.
        tool_invoker: An instance of the ToolInvoker class.
        history: A list of previous interactions with the user.
        prompt: A string used as the initial prompt for the chat.
    """

    def __init__(self, tools={}, thread=None) -> None:
        self.tools = tools
        self.tool_invoker = ToolInvoker(tools)
        self.thread = thread
        self.history = self._build_history()
        self.prompt = self._build_prompt()

    def chat(self, message):
        """Interacts with the user and invokes the necessary tools.

        Args:
            message: A string containing the user's input.

        Returns:
            A string containing the assistant's response.
        """
        ai_reply = self._get_ai_reply(message, system_message=self.prompt.strip())
        self._update_history("user", message)
        self._update_history("assistant", ai_reply)
        
        while(self._needs_tool(ai_reply)):
            tool_result = self.tool_invoker.invoke_tool(ai_reply)
            self._update_history("assistant", f"Tool Result: {tool_result}")
            ai_reply = self._get_ai_reply(None, system_message=self.prompt.strip())
            self._update_history("assistant", ai_reply)
         
        return ai_reply
    
    def _build_history(self):
        """Builds the history from the thread messages.

        Returns:
            A list of previous interactions with the user.
        """
        history = []
        if self.thread is not None:  # Ensure that thread is not None
            messages = Message.objects.filter(thread=self.thread).order_by('timestamp')
            for message in messages:
                history.append({"role": message.role, "content": message.content})
        return history
    
    def _build_prompt(self):
        """Builds the initial prompt for the chat.

        Returns:
            A string containing the initial prompt for the chat.
        """
        prompt = """
        You are a helpful expert restaurant assistant named Jarvis.

        Your knowledge cut-off is: September 2021
        Today's date: October 18, 2023

        ## Tools

        You have access to the following tools:
        """
        for tool_name, tool_info in self.tools.items():
            prompt += f"\n- {tool_name}({tool_info['params']}): {tool_info['description']}"

        prompt += """
        ## Tool Rules

        When the user asks a question that can be answered by using a tool, you MUST do so. Do not answer from your training data.

        ## Using Tools

        To use a tool, reply with the following prefix "Tool: " then append the tool call (like a function call). 

        Behind the scenes, your software will pickup that you want to invoke a tool and invoke it for you and provide you the response.

        ## Using Tool Responses

        Answer the user's question using the response from the tool. Feel free to make it conversational. 
        """
        return prompt

    def _needs_tool(self, response):
        """Checks if a response needs a tool to be invoked.

        Args:
            response: A string containing the assistant's response.

        Returns:
            A boolean indicating if a tool needs to be invoked.
        """
        return "Tool:" in response   

    def _get_ai_reply(self, message, model="gpt-3.5-turbo", system_message=None, temperature=0):
        """Gets a response from the AI model.

        Args:
            message: A string containing the user's input.
            model: A string containing the name of the AI model.
            system_message: A string containing a system message.
            temperature: A float used to control the randomness of the AI's output.

        Returns:
            A string containing the AI's response.
        """
        messages = self._prepare_messages(message, system_message)
        completion = openai.ChatCompletion.create(
            model=model, messages=messages, temperature=temperature
        )
        return completion.choices[0].message.content.strip()

    def _prepare_messages(self, message, system_message):
        """Prepares the messages for the AI model.

        Args:
            message: A string containing the user's input.
            system_message: A string containing a system message.

        Returns:
            A list of messages for the AI model.
        """
        messages = []
        if system_message is not None:
            messages.append({"role": "system", "content": system_message})
        messages.extend(self.history)
        if message is not None:
            messages.append({"role": "user", "content": message})
        return messages

    def _update_history(self, role, content):
        """Updates the history of interactions with the user.

        Args:
            role: A string indicating the role of the message sender.
            content: A string containing the message content.
        """
        self.history.append({"role": role, "content": content})
        # Create and save a Message instance
        if self.thread is not None:  # Ensure that thread is not None
            Message.objects.create(thread=self.thread, user=self.thread.user, content=content, role=role)