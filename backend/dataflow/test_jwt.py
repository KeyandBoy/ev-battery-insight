# -*- coding: utf-8 -*-
import sys
import os

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app

app = create_app()

print('=' * 60)
print('  DataFlow JWT Configuration Check')
print('=' * 60)
print()
print(f"JWT_SECRET_KEY: {app.config.get('JWT_SECRET_KEY')}")
print(f"JWT_ACCESS_TOKEN_EXPIRES: {app.config.get('JWT_ACCESS_TOKEN_EXPIRES')}")
print()

# Test token verification
from flask_jwt_extended import decode_token
import jwt

token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTc3ODE3MDg3NiwianRpIjoiY2YzMmQzZGYtZjdjZC00MTk5LTg3YzUtMDhmZGZiZTJjMzM1IiwidHlwZSI6ImFjY2VzcyIsInN1YiI6IjIiLCJuYmYiOjE3NzgxNzA4NzYsImNzcmYiOiJjZjVkZmYyNi1hZWZkLTQwNTYtOWQzNi03MzU3YjJhM2Q4MzYiLCJleHAiOjE3Nzg3NzU2NzZ9.a3fuQ1wfsH8FdZ11DO9coAHSY5M6LYddH1q8F2_EYdM"

try:
    with app.app_context():
        decoded = decode_token(token)
        print('[OK] Token decoded successfully!')
        print(f'User ID: {decoded.get("sub")}')
except Exception as e:
    print(f'[ERROR] Token decode failed: {e}')

print()
print('Trying with jwt library directly...')
try:
    decoded = jwt.decode(token, app.config.get('JWT_SECRET_KEY'), algorithms=['HS256'])
    print('[OK] Token decoded with jwt library!')
    print(f'User ID: {decoded.get("sub")}')
except Exception as e:
    print(f'[ERROR] jwt.decode failed: {e}')

print()