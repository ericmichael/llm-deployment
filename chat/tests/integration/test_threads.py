from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from chat.models import Thread

class AuthenticatedThreadIntegrationTestCase(TestCase):
    def setUp(self):
        # Create a user for the tests
        self.user = get_user_model().objects.create_user(email='testuser@test.com', password='12345')
        # Log the user in
        self.client.login(username='testuser@test.com', password='12345')
        # Create a thread
        self.thread = Thread.objects.create(name='Test Thread', user=self.user)

    def test_thread_creation(self):
        # Get the count of threads for the user before creation
        user_thread_count_before = Thread.objects.filter(user=self.user).count()

        # Test that a user can create a thread
        response = self.client.post(reverse('create_thread'), {'name': 'New Test Thread'})

        # Get the count of threads for the user after creation
        user_thread_count_after = Thread.objects.filter(user=self.user).count()

        # Check that the response is a redirect (status code 302)
        self.assertEqual(response.status_code, 302)

        # Check that the count of threads for the user has increased by one
        self.assertEqual(user_thread_count_after, user_thread_count_before + 1)
        
    def test_thread_list_view(self):
        # Test that the thread list page can be accessed
        response = self.client.get(reverse('thread_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Thread')  # The created thread should be listed

    def test_thread_detail_view(self):
        # Test that the thread detail page can be accessed
        response = self.client.get(reverse('thread_detail', kwargs={'pk': self.thread.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No messages yet.')  # Should be an empty thread at this state

    def test_thread_deletion(self):
        # Test that a thread can be deleted
        response = self.client.post(reverse('delete_thread', kwargs={'pk': self.thread.pk}))
        self.assertEqual(response.status_code, 302)  # Expect a redirect after deletion
        self.assertFalse(Thread.objects.filter(name='Test Thread').exists())  # Thread should no longer exist

    def tearDown(self):
        # Clean up after each test method
        self.client.logout()

class ThreadNonAuthenticatedTestCase(TestCase):
    def setUp(self):
        # Create a user but do not log in
        self.user = get_user_model().objects.create_user(email='testuser@test.com', password='12345')
        # Create a thread
        self.thread = Thread.objects.create(name='Test Thread', user=self.user)

    def test_thread_creation_requires_login(self):
        # Get the count of threads before attempting creation
        thread_count_before = Thread.objects.count()

        # Attempt to create a thread without being logged in
        response = self.client.post(reverse('create_thread'), {'name': 'New Test Thread'})

        # Get the count of threads after attempting creation
        thread_count_after = Thread.objects.count()

        # Check that the response is a redirect to the login page
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('create_thread')}")

        # Check that the count of threads has not changed
        self.assertEqual(thread_count_before, thread_count_after)

    def test_thread_list_view_requires_login(self):
        # Attempt to access the thread list page without being logged in
        response = self.client.get(reverse('thread_list'))

        # Check that the response is a redirect to the login page
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('thread_list')}")

    def test_thread_detail_view_requires_login(self):
        # Attempt to access the thread detail page without being logged in
        response = self.client.get(reverse('thread_detail', kwargs={'pk': self.thread.pk}))

        # Check that the response is a redirect to the login page
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('thread_detail', kwargs={'pk': self.thread.pk})}")

    def test_thread_deletion_requires_login(self):
        # Get the count of threads before attempting deletion
        thread_count_before = Thread.objects.count()

        # Attempt to delete a thread without being logged in
        response = self.client.post(reverse('delete_thread', kwargs={'pk': self.thread.pk}))

        # Get the count of threads after attempting deletion
        thread_count_after = Thread.objects.count()

        # Check that the response is a redirect to the login page
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('delete_thread', kwargs={'pk': self.thread.pk})}")

        # Check that the count of threads has not changed
        self.assertEqual(thread_count_before, thread_count_after)