# -*- coding: utf-8 -*-
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from database import get_db
from models import User


def create_test_user():
    conn = get_db()
    cursor = conn.cursor()

    test_username = 'admin'
    test_password = '123456'

    try:
        user = User.create(test_username, test_password, 'admin@test.com')
        print(f'[OK] Test account created!')
        print(f'    Username: {test_username}')
        print(f'    Password: {test_password}')
        print(f'    User ID: {user["id"]}')
        return True
    except Exception as e:
        if 'UNIQUE constraint' in str(e):
            print(f'[INFO] Test account already exists')
            print(f'    Username: {test_username}')
            print(f'    Password: {test_password}')

            cursor.execute("SELECT id, username FROM users WHERE username = ?", (test_username,))
            existing_user = cursor.fetchone()
            if existing_user:
                print(f'    User ID: {existing_user[0]}')
            return True
        else:
            print(f'[ERROR] Failed to create: {e}')
            return False
    finally:
        conn.close()


if __name__ == '__main__':
    print('=' * 50)
    print('  Chain-Connect Test Account Creator')
    print('=' * 50)
    print()

    success = create_test_user()

    if success:
        print()
        print('Usage:')
        print('  1. Open browser: http://localhost:5175/login')
        print(f'  2. Username: {test_username}')
        print(f'  3. Password: {test_password}')
        print('  4. After login, redirect to Chain-Connect module')
        print()
        print('Note:')
        print('  - Login will save JWT Token to localStorage')
        print('  - All subsequent API requests will include Token')
        print('  - The 422 error will be resolved')
        print()