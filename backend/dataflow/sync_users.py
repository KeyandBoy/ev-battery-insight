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


def sync_users_from_chain_connect():
    """从 Chain-Connect 同步用户到 DataFlow"""
    
    # Chain-Connect 的测试账号（需要与 chain-connect-code/backend/create_test_user.py 一致）
    test_accounts = [
        {'username': 'admin', 'password': '123456', 'email': 'admin@test.com'},
        {'username': 'test', 'password': '123456', 'email': 'test@test.com'},
    ]
    
    app = create_app()
    
    with app.app_context():
        print('=' * 60)
        print('  DataFlow 用户同步工具')
        print('  从 Chain-Connect 同步用户到 DataFlow 数据库')
        print('=' * 60)
        print()
        
        for account in test_accounts:
            username = account['username']
            password = account['password']
            email = account['email']
            
            try:
                existing_user = User.query.filter_by(username=username).first()
                
                if existing_user:
                    print(f'[OK] 用户已存在: {username} (ID={existing_user.id})')
                    continue
                
                password_hash = hash_password(password)
                new_user = User(
                    username=username,
                    password_hash=password_hash,
                    email=email,
                )
                
                db.session.add(new_user)
                db.session.flush()
                ensure_user_profile(new_user)
                db.session.commit()
                
                print(f'[✓] 创建成功: {username} (ID={new_user.id})')
                
            except Exception as e:
                db.session.rollback()
                print(f'[✗] 创建失败 {username}: {e}')
        
        print()
        print('完成！现在可以在 DataFlow 模块中使用这些账号了。')
        print()


if __name__ == '__main__':
    sync_users_from_chain_connect()