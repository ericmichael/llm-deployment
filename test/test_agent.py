# test/test_agent.py
import unittest
import vcr
from app.agent import Agent, ToolInvoker
from unittest.mock import MagicMock

class TestAgent(unittest.TestCase):
    def setUp(self):
        self.tools = {
            "search_food": {
                "params": "query",
                "description": "Tool to lookup food based on the user's query.",
                "function": MagicMock(return_value="Taco Palenque") 
            }
        }
        self.agent = Agent(tools=self.tools)

    @vcr.use_cassette('test/fixtures/vcr_cassettes/agent.yaml', filter_headers=[('authorization', None)])
    def test_chat(self):
        response = self.agent.chat("Where can I get tacos in Edinburg?")
        self.assertIn("Taco Palenque", response)

    @vcr.use_cassette('test/fixtures/vcr_cassettes/agent.yaml', filter_headers=[('authorization', None)])
    def test_chat_with_tool_invocation(self):
        response = self.agent.chat("Where can I get tacos in Edinburg?")
        self.assertIn("Taco Palenque", response)

    @vcr.use_cassette('test/fixtures/vcr_cassettes/agent.yaml', filter_headers=[('authorization', None)])
    def test_chat_without_tool_invocation(self):
        response = self.agent.chat("Hello")
        self.assertNotIn("Tool:", response)


class TestToolInvoker(unittest.TestCase):
    def setUp(self):
        self.tools = {
            "search_food": {
                "params": "query",
                "description": "Tool to lookup food based on the user's query.",
                "function": MagicMock(return_value="Taco Palenque") 
            }
        }
        self.tool_invoker = ToolInvoker(tools=self.tools)

    def test_invoke_tool(self):
        result = self.tool_invoker.invoke_tool("Tool: search_food('tacos')")
        self.assertEqual(result, "Taco Palenque")

    def test_invoke_tool_with_unknown_tool(self):
        with self.assertRaises(ValueError):
            self.tool_invoker.invoke_tool("Tool: unknown_tool('tacos')")

if __name__ == '__main__':
    unittest.main()