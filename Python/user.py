"""
Module for managing user accounts and authentication.
Provides methods for creating, validating, and retrieving user information.
"""
'''
   Copyright 2025 Maximilian Gründinger

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
'''
from pymongo import MongoClient
import hashlib
import time
import pyotp
import qrcode

totp_key = "Hsdfisdf4n34234dfiseLoasjfj3asnnvhxbbfgrzzuewwndcodrweokyn"


def generate_totp_qrcode():
    uri = pyotp.totp.TOTP(totp_key).provisioning_uri(name='',issuer_name='Lehrmittelgs3')
    qrcode.make(uri).save("qr.png")

def check_totp(key):
    totp = pyotp.TOTP(totp_key)
    return totp.verify(key)


def check_password_strength(password):
    """
    Check if a password meets minimum security requirements.
    
    Args:
        password (str): Password to check
        
    Returns:
        bool: True if password is strong enough, False otherwise
    """
    if len(password) < 6:
        return False
    return True


def hashing(password):
    """
    Hash a password using SHA-512.
    
    Args:
        password (str): Password to hash
        
    Returns:
        str: Hexadecimal digest of the hashed password
    """
    return hashlib.sha512(password.encode()).hexdigest()


def add_user(username, password):
    """
    Add a new user to the database.
    
    Args:
        username (str): Username for the new user
        password (str): Password for the new user
        
    Returns:
        bool: True if user was added successfully, False if password was too weak
    """
    client = MongoClient('localhost', 27017)
    db = client['Inventarsystem']
    users = db['users']
    if not check_password_strength(password):
        return False
    users.insert_one({'Username': username, 'Password': hashing(password), 'Admin': True, 'active_ausleihung': None})
    client.close()
    return True

def get_all_users():
    """
    Retrieve all users from the database.
    Administrative function for user management.
    
    Returns:
        list: List of all user documents
    """
    try:
        client = MongoClient('localhost', 27017)
        db = client['Inventarsystem']  # Match your actual database name
        users = db['users']
        all_users = list(users.find())
        client.close()
        return all_users
    except Exception as e:
        return []


def get_user(username):
    """
    Retrieve a specific user by username.
    
    Args:
        username (str): Username to search for
        
    Returns:
        dict: User document or None if not found
    """
    client = MongoClient('localhost', 27017)
    db = client['Inventarsystem']
    users = db['users']
    users_return = users.find_one({'Username': username})
    client.close()
    return users_return

def delete_user(username):
    """
    Delete a user from the database.
    Administrative function for removing user accounts.
    
    Args:
        username (str): Username of the account to delete
        
    Returns:
        bool: True if user was deleted successfully, False otherwise
    """
    client = MongoClient('localhost', 27017)
    db = client['Inventarsystem']
    users = db['users']
    result = users.delete_one({'username': username})
    client.close()
    if result.deleted_count == 0:
        # Try with different field name
        client = MongoClient('localhost', 27017)
        db = client['Inventarsystem']
        users = db['users']
        result = users.delete_one({'Username': username})
        client.close()
    
    return result.deleted_count > 0

def delete_all_user():
    client = MongoClient('localhost', 27017)
    db = client['Inventarsystem']
    db.drop_collection("users")
    