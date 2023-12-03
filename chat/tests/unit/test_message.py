# chat/tests/test_models.py
from django.test import TestCase
from django.contrib.auth import get_user_model
from chat.models import Thread, Message
from django.core.exceptions import ValidationError

class MessageModelTest(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create_user(email='testuser', password='12345')
        self.thread = Thread.objects.create(user=self.user)

    def test_message_thread_user_required(self):
        with self.assertRaises(Exception):
            Message.objects.create()

    def test_message_content_default(self):
        message = Message.objects.create(thread=self.thread, user=self.user, role='user')
        self.assertEqual(message.content, '')

    def test_message_role_choices(self):
        message = Message(thread=self.thread, user=self.user, role='invalid_role')
        with self.assertRaises(ValidationError):
            message.full_clean()