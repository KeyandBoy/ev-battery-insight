# -*- coding: utf-8 -*-
import sys
import os

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import User
from app.services.auth_service import hash_password, ensure_user_profile
from app.extensions import db


def reset_admin_user():
    """重置 admin 用户，确保 ID 与 Chain-Connect 一致"""
    
    app = create_app()
    
    with app.app_context():
        print('=' * 60)
        print('  DataFlow Admin 用户重置工具')
        print('  确保 admin 用户 ID 与 Chain-Connect 一致 (ID=2)')
        print('=' * 60)
        print()
        
        # 先删除已存在的 admin 用户
        existing_admin = User.query.filter_by(username='admin').first()
        if existing_admin:
            print(f'[DELETE] 删除旧 admin 用户 (ID={existing_admin.id})')
            db.session.delete(existing_admin)
            db.session.commit()
        
        # 删除 test 用户（避免 ID 冲突）
        test_user = User.query.filter_by(username='test').first()
        if test_user:
            print(f'[DELETE] 删除 test 用户 (ID={test_user.id})')
            db.session.delete(test_user)
            db.session.commit()
        
        # 创建新的 admin 用户
        password_hash = hash_password('123456')
        new_admin = User(
            id=2,  # 强制设置 ID=2，与 Chain-Connect 一致
            username='admin',
            password_hash=password_hash,
            email='admin@test.com',
        )
        
        db.session.add(new_admin)
        db.session.flush()  # 获取 ID 但不提交
        ensure_user_profile(new_admin)
        db.session.commit()
        
        print(f'[✓] 创建成功: admin (ID={new_admin.id})')
        print()
        print('现在 DataFlow 和 Chain-Connect 的 admin 用户 ID 一致了！')
        print('Token 可以在两个系统间通用。')
        print()


if __name__ == '__main__':
    reset_admin_user()