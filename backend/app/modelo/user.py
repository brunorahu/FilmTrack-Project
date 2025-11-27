# backend/app/modelo/user.py

class User:
    def __init__(self, user_id=0, username='', email='', created_at=None):
        self.user_id = user_id
        self.username = username
        self.email = email
        self.created_at = created_at