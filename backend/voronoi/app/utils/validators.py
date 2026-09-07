import re


def validate_email(email):
    """验证邮箱格式"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_username(username):
    """验证用户名: 3-20位，支持中英文、数字和下划线"""
    if not username or len(username) < 3 or len(username) > 20:
        return False
    pattern = r'^[a-zA-Z0-9_\u4e00-\u9fa5]+$'
    return bool(re.match(pattern, username))


def validate_password(password):
    """验证密码: 至少6位"""
    return password is not None and len(password) >= 6


def _safe_str_strip(value):
    """安全地对值做 strip，非字符串返回空串"""
    if isinstance(value, str):
        return value.strip()
    return ''


def validate_register_data(data):
    """验证注册数据，返回错误列表"""
    errors = []

    username = _safe_str_strip(data.get('username'))
    if not username:
        errors.append('用户名不能为空')
    elif not validate_username(username):
        errors.append('用户名长度3-20位，仅支持中英文、数字和下划线')

    email = _safe_str_strip(data.get('email'))
    if not email:
        errors.append('邮箱不能为空')
    elif not validate_email(email):
        errors.append('邮箱格式不正确')

    password = data.get('password')
    if not password or not isinstance(password, str):
        errors.append('密码不能为空')
    elif not validate_password(password):
        errors.append('密码长度不能少于6位')

    return errors


def validate_login_data(data):
    """验证登录数据，返回错误列表"""
    errors = []

    username = _safe_str_strip(data.get('username'))
    if not username:
        errors.append('用户名不能为空')

    password = data.get('password')
    if not password or not isinstance(password, str):
        errors.append('密码不能为空')

    return errors


def validate_json_structure(data):
    """
    验证上传的JSON是否为合法的层次数据结构。
    要求: 根节点为dict，必须含name字段，children为可选的list。
    返回 (is_valid, errors)
    """
    errors = []

    if not isinstance(data, dict):
        errors.append('根节点必须是一个JSON对象')
        return False, errors

    if 'name' not in data:
        errors.append('根节点缺少必需的"name"字段')

    visited = set()
    _check_node_recursive(data, visited, errors, path='root')

    return len(errors) == 0, errors


_MAX_VALIDATION_DEPTH = 500


def _check_node_recursive(node, visited, errors, path, depth=0):
    """递归检查每个节点的合法性"""
    if depth > _MAX_VALIDATION_DEPTH:
        errors.append(f'树的层级深度超过{_MAX_VALIDATION_DEPTH}层限制')
        return

    node_id = id(node)
    if node_id in visited:
        errors.append(f'在路径 {path} 检测到循环引用')
        return
    visited.add(node_id)

    if not isinstance(node, dict):
        errors.append(f'路径 {path} 处的节点不是有效的JSON对象')
        return

    if 'name' not in node:
        errors.append(f'路径 {path} 处的节点缺少"name"字段')

    if 'value' in node and node['value'] is not None:
        if not isinstance(node['value'], (int, float)):
            errors.append(f'路径 {path} 处的"value"字段必须是数值类型')

    if 'children' in node:
        if not isinstance(node['children'], list):
            errors.append(f'路径 {path} 处的"children"字段必须是数组')
            return
        for i, child in enumerate(node['children']):
            child_path = f'{path}.children[{i}]'
            _check_node_recursive(child, visited, errors, child_path, depth + 1)
