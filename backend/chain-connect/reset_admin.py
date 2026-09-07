import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

db_path = 'app.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 获取当前admin用户的密码哈希
cursor.execute('SELECT id, username, password_hash FROM users WHERE username = ?', ('admin',))
user = cursor.fetchone()
print(f'Current user: ID={user[0]}, username={user[1]}')
print(f'Current password hash: {user[2][:50]}...')

# 测试当前密码是否是123456
is_valid = check_password_hash(user[2], '123456')
print(f'\nTest password 123456: {"VALID" if is_valid else "INVALID"}')

if not is_valid:
    # 重置密码为123456
    new_hash = generate_password_hash('123456')
    cursor.execute('UPDATE users SET password_hash = ? WHERE username = ?', (new_hash, 'admin'))
    conn.commit()

    # 验证更新
    cursor.execute('SELECT password_hash FROM users WHERE username = ?', ('admin',))
    updated_user = cursor.fetchone()
    is_valid_new = check_password_hash(updated_user[0], '123456')
    print(f'\n[OK] Password reset to 123456')
    print(f'Verify new password: {"SUCCESS" if is_valid_new else "FAILED"}')
else:
    print('\nPassword is already 123456, issue might be elsewhere')

conn.close()
