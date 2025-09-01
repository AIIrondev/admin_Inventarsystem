import user
import getpass
import re

def is_valid_username(username):
    """Check if username follows valid pattern (letters, numbers, underscore)"""
    return bool(re.match(r'^[a-zA-Z0-9_]+$', username))

def is_valid_password(password):
    """Check if password meets minimum requirements"""
    if len(password) < 6:
        return False, "Password must be at least 6 characters long"
    return True, ""

def generate_user_interactive(username, password, confirm_password):

    if not username:
        print("Error: Username cannot be empty")

    if not is_valid_username(username):
        print("Error: Username can only contain letters, numbers, and underscores")

    if not password:
        print("Error: Password cannot be empty")

        
    valid, message = is_valid_password(password)
    if not valid:
        print(f"Error: {message}")
            

    if password != confirm_password:
        exit(1)

    is_admin = True

    # Add the user
    added = user.add_user(username, password)
    if added:
        admin_result = user.make_admin(username)
    else:
        exit(1)
    
    return admin_result