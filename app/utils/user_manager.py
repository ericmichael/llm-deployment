from dotenv import load_dotenv

load_dotenv()  # take environment variables from .env.

import os
import duckdb
import bcrypt
from pathlib import Path

class UserManager:
    """
    UserManager class is responsible for managing users in the database.
    It provides functionalities such as loading users, seeding the database,
    authenticating users, adding and removing users, and authorizing users.
    """
class UserManager:
    def __init__(self):
        """
        Initialize UserManager with a connection to the database.
        """
         # If the DUCKDB_STORAGE_PATH environment variable is set, use it as the path
        # otherwise, use an in-memory database
        path = os.getenv('DUCKDB_STORAGE_PATH', None)

        # If we're not connecting to SQLite in-memory database
        if path is not None:
            # Combine the folder path and the database file name
            full_db_path = os.path.join(path, "app.db")

            # Make sure that the directory containing the db file exists
            Path(full_db_path).parent.mkdir(parents=True, exist_ok=True)

            self.conn = duckdb.connect(full_db_path)
        else:
            self.conn = duckdb.connect(":memory:")

        
    def load_users(self):
        """
        Load all users from the database.
        """
        try:
            return self.conn.execute("""
                SELECT username, role FROM users           
            """).df()
        except Exception as e:
            print(f"Error loading users: {e}")
            return None

    def seed_database(self):
        """
        Seed the database with initial data.
        """
        try:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    username VARCHAR,
                    password VARCHAR,
                    role VARCHAR
                )
            """)
            self.conn.commit()
            users = self.load_users()
            if users.empty:
                admin_username = os.getenv("ADMIN_USERNAME")
                admin_password = os.getenv("ADMIN_PASSWORD")
                if admin_username and admin_password:
                    self.add_user(admin_username, admin_password, 'admin')
        except Exception as e:
            print(f"Error seeding database: {e}")

    def __hash_password(self, password):
        """
        Hash a password for storing.
        """
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode()

    def __verify_password(self, stored_password, provided_password):
        """
        Verify a stored password against one provided by user.
        """
        return bcrypt.checkpw(provided_password.encode('utf-8'), stored_password.encode('utf-8'))

    def authenticate(self, username, provided_password):
        """
        Authenticate a user with a username and password.
        """
        try:
            user = self.conn.execute("""
                SELECT username, password FROM users 
                WHERE username = ?
            """, (username,)).fetchone()

            if user is None:
                return False

            stored_password = user[1]
            return self.__verify_password(stored_password, provided_password)
        except Exception as e:
            print(f"Error authenticating user: {e}")
            return False

    def add_user(self, username, password, role):
        """
        Add a new user to the database.
        """
        try:
            if username and password:
                # Check if a user with the given username already exists
                existing_user = self.conn.execute("""
                    SELECT * FROM users 
                    WHERE username = ?
                """, (username,)).fetchone()

                if existing_user is not None:
                    return
                hashed_password = self.__hash_password(password)
                self.conn.execute("""
                    INSERT INTO users (username, password, role) 
                    VALUES (?, ?, ?)
                """, (username, hashed_password, role.lower()))
                self.conn.commit()
        except Exception as e:
            print(f"Error adding user: {e}")

    def remove_user(self, username):
        """
        Remove a user from the database.
        """
        try:
            self.conn.execute("""
                DELETE FROM users 
                WHERE username = ?
            """, (username,))

            self.conn.commit()
        except Exception as e:
            print(f"Error removing user: {e}")

    def authorize(self, username, role):
        """
        Authorize a user with a specific role.
        """
        try:
            # Query the database for a user with the provided username and role
            user = self.conn.execute("""
                SELECT * FROM users 
                WHERE username = ? AND role = ?
            """, (username,role)).fetchone()
            # If a user was found, return True, otherwise return False
            return user is not None
        except Exception as e:
            print(f"Error authorizing user: {e}")
            return False