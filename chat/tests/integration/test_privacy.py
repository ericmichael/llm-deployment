# aistarterkit/chat/tests/test_privacy.py
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from chat.models import Thread, Message

class ThreadPrivacyTestCase(TestCase):
    def setUp(self):
        # Create two users
        self.user1 = get_user_model().objects.create_user(email='testuser1@test.com', password='testpassword1')
        self.user2 = get_user_model().objects.create_user(email='testuser2@test.com', password='testpassword2')
        # Create a thread for each user
        self.thread1 = Thread.objects.create(name='User1 Thread', user=self.user1)
        self.thread2 = Thread.objects.create(name='User2 Thread', user=self.user2)

    def test_thread_list_contains_only_user_threads(self):
        # Log in as user1
        self.client.login(username='testuser1@test.com', password='testpassword1')
        # Get the thread list page
        response = self.client.get(reverse('thread_list'))
        # Check that the response contains user1's thread but not user2's thread
        self.assertContains(response, 'User1 Thread')
        self.assertNotContains(response, 'User2 Thread')

    def test_user_cannot_view_another_users_thread_detail(self):
        # Log in as user1
        self.client.login(username='testuser1@test.com', password='testpassword1')
        # Attempt to access user2's thread detail page
        response = self.client.get(reverse('thread_detail', kwargs={'pk': self.thread2.pk}))
        # Check that user1 is forbidden from viewing user2's thread
        self.assertEqual(response.status_code, 404)

    def test_thread_creation_does_not_increase_other_users_thread_count(self):
        # Get the count of threads for user2 before user1 creates a new thread
        user2_thread_count_before = Thread.objects.filter(user=self.user2).count()
        # Log in as user1 and create a new thread
        self.client.login(username='testuser1@test.com', password='testpassword1')
        self.client.post(reverse('create_thread'), {'name': 'Another User1 Thread'})
        # Get the count of threads for user2 after user1 has created a new thread
        user2_thread_count_after = Thread.objects.filter(user=self.user2).count()
        # Check that the count of threads for user2 has not changed
        self.assertEqual(user2_thread_count_before, user2_thread_count_after)

    def test_user_cannot_delete_another_users_thread(self):
        # Log in as user1
        self.client.login(username='testuser1@test.com', password='testpassword1')
        # Attempt to delete user2's thread
        response = self.client.post(reverse('delete_thread', kwargs={'pk': self.thread2.pk}))
        # Check that user1 is forbidden from deleting user2's thread
        self.assertEqual(response.status_code, 404)
        # Check that user2's thread still exists
        self.assertTrue(Thread.objects.filter(pk=self.thread2.pk).exists())
        
class MessagePrivacyTestCase(TestCase):
    def setUp(self):
        # Create two users
        self.user1 = get_user_model().objects.create_user(email='testuser1@test.com', password='testpassword1')
        self.user2 = get_user_model().objects.create_user(email='testuser2@test.com', password='testpassword2')
        # Create a thread for each user
        self.thread1 = Thread.objects.create(name='User1 Thread', user=self.user1)
        self.thread2 = Thread.objects.create(name='User2 Thread', user=self.user2)

    def test_message_creation_does_not_increase_other_users_message_count(self):
        # Create a message in user2's thread
        Message.objects.create(thread=self.thread2, user=self.user2, content='Hello from User2!')
        # Get the count of messages for user2 before user1 creates a new message
        user2_message_count_before = Message.objects.filter(thread=self.thread2).count()
        # Log in as user1 and create a new message in user1's thread
        self.client.login(username='testuser1@test.com', password='testpassword1')
        self.client.post(reverse('new_message', kwargs={'pk': self.thread1.pk}), {'content': 'Hello from User1!'})
        # Get the count of messages for user2 after user1 has created a new message
        user2_message_count_after = Message.objects.filter(thread=self.thread2).count()
        # Check that the count of messages for user2 has not changed
        self.assertEqual(user2_message_count_before, user2_message_count_after)