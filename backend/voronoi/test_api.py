"""
完整的 API 接口测试脚本
测试所有后端接口的功能正确性
"""
import json
import os
import sys

import requests

BASE_URL = 'http://127.0.0.1:5000'
TOKEN = None


def print_result(name, response):
    status = 'PASS' if response.ok else 'FAIL'
    print(f'  [{status}] {name}  (HTTP {response.status_code})')
    if not response.ok:
        print(f'        Response: {response.text[:200]}')
    return response


def test_register():
    """测试用户注册"""
    print('\n=== 1. 测试用户注册 ===')

    r = requests.post(f'{BASE_URL}/api/auth/register', json={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': '123456',
    })
    print_result('正常注册', r)
    assert r.status_code == 201
    data = r.json()
    assert data['success'] is True
    assert 'token' in data['data']
    assert data['data']['user']['username'] == 'testuser'

    r = requests.post(f'{BASE_URL}/api/auth/register', json={
        'username': 'testuser',
        'email': 'another@example.com',
        'password': '123456',
    })
    print_result('重复用户名被拒绝', r)
    assert r.status_code == 409

    r = requests.post(f'{BASE_URL}/api/auth/register', json={
        'username': 'ab',
        'email': 'bad',
        'password': '123',
    })
    print_result('非法数据被拒绝', r)
    assert r.status_code == 400

    r = requests.post(f'{BASE_URL}/api/auth/register', json={
        'username': 'testuser2',
        'email': 'test2@example.com',
        'password': '654321',
    })
    print_result('注册第二个用户', r)
    assert r.status_code == 201


def test_login():
    """测试用户登录"""
    global TOKEN
    print('\n=== 2. 测试用户登录 ===')

    r = requests.post(f'{BASE_URL}/api/auth/login', json={
        'username': 'testuser',
        'password': '123456',
    })
    print_result('正常登录', r)
    assert r.status_code == 200
    data = r.json()
    assert data['success'] is True
    TOKEN = data['data']['token']

    r = requests.post(f'{BASE_URL}/api/auth/login', json={
        'username': 'testuser',
        'password': 'wrongpass',
    })
    print_result('密码错误被拒绝', r)
    assert r.status_code == 401

    r = requests.post(f'{BASE_URL}/api/auth/login', json={
        'username': 'nobody',
        'password': '123456',
    })
    print_result('不存在用户被拒绝', r)
    assert r.status_code == 401


def test_profile():
    """测试用户资料操作"""
    print('\n=== 3. 测试用户资料 ===')
    headers = {'Authorization': f'Bearer {TOKEN}'}

    r = requests.get(f'{BASE_URL}/api/auth/profile', headers=headers)
    print_result('获取资料', r)
    assert r.status_code == 200
    assert r.json()['data']['username'] == 'testuser'

    r = requests.put(f'{BASE_URL}/api/auth/profile', headers=headers, json={
        'email': 'newemail@example.com',
        'avatar': 'https://example.com/avatar.png',
    })
    print_result('更新资料', r)
    assert r.status_code == 200
    assert r.json()['data']['email'] == 'newemail@example.com'

    r = requests.get(f'{BASE_URL}/api/auth/profile')
    print_result('无Token被拒绝', r)
    assert r.status_code == 401

    r = requests.get(f'{BASE_URL}/api/auth/profile',
                     headers={'Authorization': 'Bearer invalidtoken'})
    print_result('无效Token被拒绝', r)
    assert r.status_code == 401


def test_change_password():
    """测试修改密码"""
    print('\n=== 4. 测试修改密码 ===')
    headers = {'Authorization': f'Bearer {TOKEN}'}

    r = requests.put(f'{BASE_URL}/api/auth/password', headers=headers, json={
        'old_password': 'wrongold',
        'new_password': 'newpass123',
    })
    print_result('原密码错误被拒绝', r)
    assert r.status_code == 400

    r = requests.put(f'{BASE_URL}/api/auth/password', headers=headers, json={
        'old_password': '123456',
        'new_password': '654321',
    })
    print_result('正常修改密码', r)
    assert r.status_code == 200

    r = requests.post(f'{BASE_URL}/api/auth/login', json={
        'username': 'testuser',
        'password': '654321',
    })
    print_result('新密码登录成功', r)
    assert r.status_code == 200


def test_upload_dataset():
    """测试上传数据集"""
    global TOKEN
    print('\n=== 5. 测试上传数据集 ===')

    r = requests.post(f'{BASE_URL}/api/auth/login', json={
        'username': 'testuser',
        'password': '654321',
    })
    TOKEN = r.json()['data']['token']
    headers = {'Authorization': f'Bearer {TOKEN}'}

    sample_dir = os.path.join(os.path.dirname(__file__), 'sample_data')

    filepath = os.path.join(sample_dir, 'company_org.json')
    with open(filepath, 'rb') as f:
        r = requests.post(
            f'{BASE_URL}/api/datasets/upload',
            headers=headers,
            files={'file': ('company_org.json', f, 'application/json')},
            data={'name': '公司组织架构', 'description': '测试用的公司组织架构数据'},
        )
    print_result('上传公司组织架构', r)
    assert r.status_code == 201
    ds1 = r.json()['data']
    print(f'        节点数={ds1["node_count"]}, 深度={ds1["max_depth"]}, 叶节点={ds1["leaf_count"]}')

    filepath = os.path.join(sample_dir, 'file_system.json')
    with open(filepath, 'rb') as f:
        r = requests.post(
            f'{BASE_URL}/api/datasets/upload',
            headers=headers,
            files={'file': ('file_system.json', f, 'application/json')},
            data={'name': '项目文件结构', 'description': '前端项目目录树'},
        )
    print_result('上传文件系统结构', r)
    assert r.status_code == 201
    ds2 = r.json()['data']
    print(f'        节点数={ds2["node_count"]}, 深度={ds2["max_depth"]}, 叶节点={ds2["leaf_count"]}')

    filepath = os.path.join(sample_dir, 'world_population.json')
    with open(filepath, 'rb') as f:
        r = requests.post(
            f'{BASE_URL}/api/datasets/upload',
            headers=headers,
            files={'file': ('world_population.json', f, 'application/json')},
            data={'name': '世界人口分布', 'description': '按大洲和地区划分的世界人口数据'},
        )
    print_result('上传世界人口数据', r)
    assert r.status_code == 201
    ds3 = r.json()['data']
    print(f'        节点数={ds3["node_count"]}, 深度={ds3["max_depth"]}, 叶节点={ds3["leaf_count"]}')

    invalid_json = b'{"name": "test", "children": "not_a_list"}'
    r = requests.post(
        f'{BASE_URL}/api/datasets/upload',
        headers=headers,
        files={'file': ('invalid.json', invalid_json, 'application/json')},
    )
    print_result('非法结构被拒绝', r)
    assert r.status_code == 400

    return ds1['id'], ds2['id'], ds3['id']


def test_list_datasets():
    """测试数据集列表"""
    print('\n=== 6. 测试数据集列表 ===')
    headers = {'Authorization': f'Bearer {TOKEN}'}

    r = requests.get(f'{BASE_URL}/api/datasets', headers=headers)
    print_result('获取列表', r)
    assert r.status_code == 200
    data = r.json()['data']
    print(f'        共{data["total"]}条, 当前第{data["page"]}页')
    assert data['total'] == 3

    r = requests.get(f'{BASE_URL}/api/datasets?search=公司', headers=headers)
    print_result('搜索"公司"', r)
    assert r.status_code == 200
    assert r.json()['data']['total'] == 1

    r = requests.get(f'{BASE_URL}/api/datasets?page=1&per_page=2', headers=headers)
    print_result('分页(每页2条)', r)
    assert r.status_code == 200
    data = r.json()['data']
    assert len(data['items']) == 2
    assert data['has_next'] is True


def test_get_dataset(ds_id):
    """测试获取单个数据集"""
    print('\n=== 7. 测试获取数据集详情 ===')
    headers = {'Authorization': f'Bearer {TOKEN}'}

    r = requests.get(f'{BASE_URL}/api/datasets/{ds_id}', headers=headers)
    print_result('获取详情', r)
    assert r.status_code == 200
    assert r.json()['data']['id'] == ds_id

    r = requests.get(f'{BASE_URL}/api/datasets/99999', headers=headers)
    print_result('不存在的ID返回404', r)
    assert r.status_code == 404


def test_get_processed_data(ds_id):
    """测试获取预处理数据"""
    print('\n=== 8. 测试获取预处理数据(可视化) ===')
    headers = {'Authorization': f'Bearer {TOKEN}'}

    r = requests.get(f'{BASE_URL}/api/datasets/{ds_id}/data', headers=headers)
    print_result('获取预处理数据', r)
    assert r.status_code == 200
    data = r.json()['data']
    tree = data['tree_data']
    assert 'normalized_value' in tree
    assert 'depth' in tree
    assert 'id' in tree
    assert 'leaf_count' in tree
    assert tree['depth'] == 0
    assert tree['normalized_value'] == 1.0
    print(f'        根节点: name={tree["name"]}, value={tree["value"]}, children={len(tree.get("children", []))}')

    if tree.get('children'):
        child = tree['children'][0]
        print(f'        第一个子节点: name={child["name"]}, normalized_value={child["normalized_value"]:.4f}, depth={child["depth"]}')


def test_get_raw_data(ds_id):
    """测试获取原始数据"""
    print('\n=== 9. 测试获取原始数据 ===')
    headers = {'Authorization': f'Bearer {TOKEN}'}

    r = requests.get(f'{BASE_URL}/api/datasets/{ds_id}/raw', headers=headers)
    print_result('获取原始数据', r)
    assert r.status_code == 200
    tree = r.json()['data']['tree_data']
    assert 'normalized_value' not in tree
    assert 'depth' not in tree


def test_preview_dataset(ds_id):
    """测试数据集预览"""
    print('\n=== 10. 测试数据集预览 ===')
    headers = {'Authorization': f'Bearer {TOKEN}'}

    r = requests.get(f'{BASE_URL}/api/datasets/{ds_id}/preview?max_depth=2', headers=headers)
    print_result('预览(深度=2)', r)
    assert r.status_code == 200
    preview = r.json()['data']['preview']
    print(f'        预览根节点: {preview["name"]}')


def test_update_dataset(ds_id):
    """测试更新数据集"""
    print('\n=== 11. 测试更新数据集 ===')
    headers = {'Authorization': f'Bearer {TOKEN}'}

    r = requests.put(f'{BASE_URL}/api/datasets/{ds_id}', headers=headers, json={
        'name': '更新后的名称',
        'description': '更新后的描述信息',
    })
    print_result('更新元信息', r)
    assert r.status_code == 200
    assert r.json()['data']['name'] == '更新后的名称'
    assert r.json()['data']['description'] == '更新后的描述信息'


def test_delete_dataset(ds_id):
    """测试删除数据集"""
    print('\n=== 12. 测试删除数据集 ===')
    headers = {'Authorization': f'Bearer {TOKEN}'}

    r = requests.delete(f'{BASE_URL}/api/datasets/{ds_id}', headers=headers)
    print_result('删除数据集', r)
    assert r.status_code == 200

    r = requests.get(f'{BASE_URL}/api/datasets/{ds_id}', headers=headers)
    print_result('删除后查询返回404', r)
    assert r.status_code == 404


def test_data_isolation():
    """测试用户数据隔离"""
    print('\n=== 13. 测试用户数据隔离 ===')

    r = requests.post(f'{BASE_URL}/api/auth/login', json={
        'username': 'testuser2',
        'password': '654321',
    })
    token2 = r.json()['data']['token']
    headers2 = {'Authorization': f'Bearer {token2}'}

    r = requests.get(f'{BASE_URL}/api/datasets', headers=headers2)
    print_result('用户2看不到用户1的数据', r)
    assert r.status_code == 200
    assert r.json()['data']['total'] == 0


def test_error_handlers():
    """测试全局错误处理"""
    print('\n=== 14. 测试错误处理 ===')

    r = requests.get(f'{BASE_URL}/api/nonexistent')
    print_result('404处理', r)
    assert r.status_code == 404
    assert r.json()['success'] is False

    r = requests.put(f'{BASE_URL}/api/auth/register')
    print_result('405处理', r)
    assert r.status_code == 405


if __name__ == '__main__':
    print('=' * 60)
    print('  Voronoi Diagram 后端 API 完整测试')
    print('=' * 60)

    try:
        test_register()
        test_login()
        test_profile()
        test_change_password()
        ds1_id, ds2_id, ds3_id = test_upload_dataset()
        test_list_datasets()
        test_get_dataset(ds1_id)
        test_get_processed_data(ds1_id)
        test_get_raw_data(ds1_id)
        test_preview_dataset(ds3_id)
        test_update_dataset(ds2_id)
        test_delete_dataset(ds2_id)
        test_data_isolation()
        test_error_handlers()

        print('\n' + '=' * 60)
        print('  ALL TESTS PASSED!')
        print('=' * 60)
    except AssertionError as e:
        print(f'\n  TEST FAILED: {e}')
        sys.exit(1)
    except requests.ConnectionError:
        print('\n  ERROR: 无法连接服务器，请确保 Flask 服务已在 http://127.0.0.1:5000 运行')
        sys.exit(1)
