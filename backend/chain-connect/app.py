from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager, create_access_token, jwt_required, get_jwt_identity
)
from datetime import timedelta
import os

from database import init_db, get_db
from models import User, Project, SampleDataset
from text_processor import process_text

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'change-me-in-env')
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'change-me-in-env')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=7)

CORS(app, supports_credentials=True)
jwt = JWTManager(app)

# 初始化数据库
init_db()


# ==================== 认证接口 ====================

@app.route('/api/auth/register', methods=['POST'])
def register():
    """用户注册"""
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    email = data.get('email', '').strip()

    if not username or not password:
        return jsonify({"code": 400, "message": "用户名和密码不能为空"}), 400

    if len(username) < 3 or len(username) > 20:
        return jsonify({"code": 400, "message": "用户名长度应在3-20个字符之间"}), 400

    if len(password) < 6:
        return jsonify({"code": 400, "message": "密码长度不能少于6个字符"}), 400

    try:
        user = User.create(username, password, email)
        access_token = create_access_token(identity=str(user['id']))
        return jsonify({
            "code": 200,
            "message": "注册成功",
            "data": {
                "token": access_token,
                "user": user
            }
        })
    except Exception as e:
        if 'UNIQUE constraint' in str(e):
            return jsonify({"code": 409, "message": "用户名已存在"}), 409
        return jsonify({"code": 500, "message": f"注册失败: {str(e)}"}), 500


@app.route('/api/auth/login', methods=['POST'])
def login():
    """用户登录"""
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()

    if not username or not password:
        return jsonify({"code": 400, "message": "用户名和密码不能为空"}), 400

    user = User.authenticate(username, password)
    if user:
        access_token = create_access_token(identity=str(user['id']))
        return jsonify({
            "code": 200,
            "message": "登录成功",
            "data": {
                "token": access_token,
                "user": user
            }
        })
    return jsonify({"code": 401, "message": "用户名或密码错误"}), 401


@app.route('/api/auth/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """获取当前用户信息"""
    user_id = int(get_jwt_identity())
    user = User.get_by_id(user_id)
    if user:
        return jsonify({"code": 200, "data": user})
    return jsonify({"code": 404, "message": "用户不存在"}), 404


@app.route('/api/auth/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """更新用户信息"""
    user_id = int(get_jwt_identity())
    data = request.get_json()
    email = data.get('email')
    User.update_profile(user_id, email=email)
    user = User.get_by_id(user_id)
    return jsonify({"code": 200, "message": "更新成功", "data": user})


# ==================== 示例数据集接口 ====================

@app.route('/api/datasets', methods=['GET'])
@jwt_required()
def get_datasets():
    """获取所有预置示例数据集"""
    datasets = SampleDataset.get_all()
    return jsonify({"code": 200, "data": datasets})


@app.route('/api/datasets/<int:dataset_id>', methods=['GET'])
@jwt_required()
def get_dataset(dataset_id):
    """获取单个示例数据集"""
    dataset = SampleDataset.get_by_id(dataset_id)
    if dataset:
        return jsonify({"code": 200, "data": dataset})
    return jsonify({"code": 404, "message": "数据集不存在"}), 404


# ==================== 项目管理接口 ====================

@app.route('/api/projects', methods=['GET'])
@jwt_required()
def get_projects():
    """获取当前用户的所有项目"""
    user_id = int(get_jwt_identity())
    projects = Project.get_all_by_user(user_id)
    return jsonify({"code": 200, "data": projects})


@app.route('/api/projects', methods=['POST'])
@jwt_required()
def create_project():
    """创建新项目"""
    user_id = int(get_jwt_identity())
    data = request.get_json()

    name = data.get('name', '').strip()
    if not name:
        return jsonify({"code": 400, "message": "项目名称不能为空"}), 400

    project_id = Project.create(
        user_id=user_id,
        name=name,
        description=data.get('description', ''),
        data_type=data.get('data_type', 'social'),
        graph_data=data.get('graph_data'),
        layout_config=data.get('layout_config'),
        visual_config=data.get('visual_config')
    )
    project = Project.get_by_id(project_id, user_id)
    return jsonify({"code": 200, "message": "创建成功", "data": project})


@app.route('/api/projects/<int:project_id>', methods=['GET'])
@jwt_required()
def get_project(project_id):
    """获取单个项目"""
    user_id = int(get_jwt_identity())
    project = Project.get_by_id(project_id, user_id)
    if project:
        return jsonify({"code": 200, "data": project})
    return jsonify({"code": 404, "message": "项目不存在"}), 404


@app.route('/api/projects/<int:project_id>', methods=['PUT'])
@jwt_required()
def update_project(project_id):
    """更新项目"""
    user_id = int(get_jwt_identity())
    data = request.get_json()
    success = Project.update(project_id, user_id, **data)
    if success:
        project = Project.get_by_id(project_id, user_id)
        return jsonify({"code": 200, "message": "更新成功", "data": project})
    return jsonify({"code": 400, "message": "更新失败"}), 400


@app.route('/api/projects/<int:project_id>', methods=['DELETE'])
@jwt_required()
def delete_project(project_id):
    """删除项目"""
    user_id = int(get_jwt_identity())
    Project.delete(project_id, user_id)
    return jsonify({"code": 200, "message": "删除成功"})


# ==================== 文本处理接口 ====================

@app.route('/api/text/extract', methods=['POST'])
@jwt_required()
def extract_relations():
    """从文本中提取人物关系"""
    data = request.get_json()
    text = data.get('text', '').strip()

    if not text:
        return jsonify({"code": 400, "message": "文本内容不能为空"}), 400

    if len(text) < 10:
        return jsonify({"code": 400, "message": "文本内容过短，请输入至少10个字符"}), 400

    window_size = data.get('window_size', 3)
    min_co_occurrence = data.get('min_co_occurrence', 1)

    try:
        graph_data = process_text(text, window_size, min_co_occurrence)

        if not graph_data['nodes']:
            return jsonify({
                "code": 200,
                "message": "未能从文本中提取到人物，请确保文本中包含人名",
                "data": graph_data
            })

        return jsonify({
            "code": 200,
            "message": f"成功提取到 {len(graph_data['nodes'])} 个人物，{len(graph_data['links'])} 条关系",
            "data": graph_data
        })
    except Exception as e:
        return jsonify({"code": 500, "message": f"文本处理失败: {str(e)}"}), 500


# ==================== 图数据分析接口 ====================

@app.route('/api/analysis/stats', methods=['POST'])
@jwt_required()
def analyze_graph():
    """分析图数据的统计信息"""
    data = request.get_json()
    graph_data = data.get('graph_data', {})

    nodes = graph_data.get('nodes', [])
    links = graph_data.get('links', [])

    if not nodes:
        return jsonify({"code": 400, "message": "图数据为空"}), 400

    # 计算度数
    degree_map = {}
    for node in nodes:
        degree_map[node['id']] = {'in': 0, 'out': 0, 'total': 0}

    for link in links:
        src = link.get('source')
        tgt = link.get('target')
        if src in degree_map:
            degree_map[src]['out'] += 1
            degree_map[src]['total'] += 1
        if tgt in degree_map:
            degree_map[tgt]['in'] += 1
            degree_map[tgt]['total'] += 1

    # 找最大度数节点
    max_degree_node = max(degree_map.items(), key=lambda x: x[1]['total']) if degree_map else (None, {'total': 0})

    # 关系类型统计
    relation_types = {}
    for link in links:
        rel = link.get('relation', '未知')
        relation_types[rel] = relation_types.get(rel, 0) + 1

    # 分类统计
    category_stats = {}
    categories = graph_data.get('categories', [])
    for node in nodes:
        cat_idx = node.get('category', 0)
        cat_name = categories[cat_idx]['name'] if cat_idx < len(categories) else f'分类{cat_idx}'
        category_stats[cat_name] = category_stats.get(cat_name, 0) + 1

    # 图密度
    node_count = len(nodes)
    max_edges = node_count * (node_count - 1) / 2 if node_count > 1 else 1
    density = len(links) / max_edges if max_edges > 0 else 0

    # 平均度数
    avg_degree = sum(d['total'] for d in degree_map.values()) / len(degree_map) if degree_map else 0

    stats = {
        "node_count": node_count,
        "link_count": len(links),
        "density": round(density, 4),
        "avg_degree": round(avg_degree, 2),
        "max_degree_node": {
            "id": max_degree_node[0],
            "name": next((nd['name'] for nd in nodes if nd['id'] == max_degree_node[0]), ''),
            "degree": max_degree_node[1]['total']
        },
        "degree_distribution": {node_id: d['total'] for node_id, d in degree_map.items()},
        "relation_types": relation_types,
        "category_stats": category_stats
    }

    return jsonify({"code": 200, "data": stats})


# ==================== 数据导入导出接口 ====================

@app.route('/api/import/json', methods=['POST'])
@jwt_required()
def import_json():
    """导入JSON格式的图数据"""
    data = request.get_json()
    graph_data = data.get('graph_data')

    if not graph_data:
        return jsonify({"code": 400, "message": "数据为空"}), 400

    # 验证数据格式
    if 'nodes' not in graph_data or 'links' not in graph_data:
        return jsonify({"code": 400, "message": "数据格式错误，需要包含nodes和links字段"}), 400

    # 验证节点格式
    for node in graph_data['nodes']:
        if 'id' not in node or 'name' not in node:
            return jsonify({"code": 400, "message": "节点数据需要包含id和name字段"}), 400

    # 补全缺失字段
    for node in graph_data['nodes']:
        node.setdefault('category', 0)
        node.setdefault('value', 10)
        node.setdefault('desc', '')

    for link in graph_data['links']:
        link.setdefault('value', 1)
        link.setdefault('relation', '关联')

    if 'categories' not in graph_data:
        cats = set(n.get('category', 0) for n in graph_data['nodes'])
        graph_data['categories'] = [{"name": f"分类{i}"} for i in range(max(cats) + 1)]

    return jsonify({
        "code": 200,
        "message": f"成功导入 {len(graph_data['nodes'])} 个节点，{len(graph_data['links'])} 条边",
        "data": graph_data
    })


@app.route('/api/export/json', methods=['POST'])
@jwt_required()
def export_json():
    """导出图数据为JSON"""
    data = request.get_json()
    graph_data = data.get('graph_data', {})
    return jsonify({
        "code": 200,
        "data": graph_data
    })


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        db = get_db()
        db.execute("SELECT 1")
        return jsonify({
            "status": "healthy",
            "service": "chain-connect",
            "version": "1.0.0",
            "database": "connected"
        }), 200
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 503


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5004)
