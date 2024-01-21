from django.test import TestCase
from chat.ai.agent import Agent
from unittest.mock import MagicMock
from .vcr_config import vcr


class TestAgent(TestCase):
    def setUp(self):
        self.agent = Agent(prompt="You are a helpful assistant named Jarvis.")

    @vcr.use_cassette(
        "chat/tests/fixtures/vcr_cassettes/agent.yaml",
        filter_headers=[("authorization", None)],
    )
    def test_chat(self):
        response = self.agent.chat("Hello, what is your name?")
        self.assertIn("Jarvis", response)
