# chat/tests/test_models.py
from django.test import TestCase
from django.contrib.auth import get_user_model
from chat.models import Thread
from django.utils import timezone

class ThreadModelTest(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create_user(email='testuser', password='12345')

    def test_thread_user_required(self):
        with self.assertRaises(Exception):
            Thread.objects.create()

    def test_thread_name(self):
        thread = Thread.objects.create(user=self.user, name='Test Thread')
        self.assertEqual(thread.name, 'Test Thread')

    def test_thread_default_name(self):
        thread = Thread.objects.create(user=self.user)
        self.assertEqual(thread.name, 'New Thread')

    def test_thread_created_at_required(self):
        thread = Thread.objects.create(user=self.user)
        self.assertIsNotNone(thread.created_at)