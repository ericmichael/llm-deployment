import unittest
from app.utils.user_manager import UserManager
import os

class TestUserManager(unittest.TestCase):
    def setUp(self):
        """
        Set up the test environment before each test.
        """
        self.user_manager = UserManager()
        self.user_manager.seed_database()
        self.admin_username = os.getenv("ADMIN_USERNAME")
        self.admin_password = os.getenv("ADMIN_PASSWORD")

    def test_load_users(self):
        """
        Test that load_users method works correctly.
        """
        users = self.user_manager.load_users()
        self.assertEqual(len(users), 1)
        self.assertEqual(users.iloc[0]['username'], self.admin_username)
        self.assertEqual(users.iloc[0]['role'], 'admin')

    def test_authenticate(self):
        """
        Test that authenticate method works correctly.
        """
        self.assertTrue(self.user_manager.authenticate(self.admin_username, self.admin_password))
        self.assertFalse(self.user_manager.authenticate(self.admin_username, 'wrong_password'))
        self.assertFalse(self.user_manager.authenticate('wrong_username', self.admin_password))

    def test_add_user(self):
        """
        Test that add_user method works correctly.
        """
        self.user_manager.add_user('test_user', 'test_password', 'user')
        users = self.user_manager.load_users()
        self.assertEqual(len(users), 2)
        self.assertTrue('test_user' in users['username'].values)

    def test_no_duplicate_users(self):
        """
        Test that no duplicate users can be created.
        """
        self.user_manager.add_user('test_user', 'test_password', 'user')
        users_before = self.user_manager.load_users()
        self.user_manager.add_user('test_user', 'test_password', 'user')
        users_after = self.user_manager.load_users()
        self.assertEqual(len(users_before), len(users_after))
        self.user_manager.remove_user('test_user')

    def test_remove_user(self):
        """
        Test that remove_user method works correctly.
        """
        self.user_manager.add_user('test_user', 'test_password', 'user')
        self.user_manager.remove_user('test_user')
        users = self.user_manager.load_users()
        self.assertEqual(len(users), 1)
        self.assertFalse('test_user' in users['username'].values)

    def test_authorize(self):
        """
        Test that authorize method works correctly.
        """
        self.assertTrue(self.user_manager.authorize(self.admin_username, 'admin'))
        self.assertFalse(self.user_manager.authorize(self.admin_username, 'user'))
        self.assertFalse(self.user_manager.authorize('wrong_username', 'admin'))

    def tearDown(self):
        """
        Clean up the test environment after each test.
        """
        self.user_manager.remove_user(self.admin_username)
        self.user_manager = None

if __name__ == '__main__':
    unittest.main()