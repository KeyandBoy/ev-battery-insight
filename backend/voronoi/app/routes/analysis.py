"""
降维分析 API 路由

端点:
  POST /api/analysis/pca-weight/<dataset_id>  — 对已有数据集做 PCA 降维权重
  POST /api/analysis/cluster                  — 上传 CSV 做降维聚类生成层次树
  POST /api/analysis/cluster/save             — 将聚类结果保存为数据集
"""

import json
import os
import uuid

from flask import Blueprint, jsonify, request, current_app

from ..extensions import db
from ..models.dataset import Dataset
from ..services.analysis_service import pca_weight_reduction, csv_to_hierarchical_tree
from ..services.data_service import DataService
from ..utils.decorators import token_required

analysis_bp = Blueprint('analysis', __name__, url_prefix='/api/analysis')


@analysis_bp.route('/pca-weight/<int:dataset_id>', methods=['POST'])
@token_required
def apply_pca_weight(current_user, dataset_id):
    """对已有数据集的树节点做 PCA 多维属性降维，生成新权重"""
    dataset = db.session.get(Dataset, dataset_id)
    if not dataset or dataset.user_id != current_user.id:
        return jsonify({'success': False, 'message': '数据集不存在'}), 404

    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], dataset.filename)
    if not os.path.exists(filepath):
        return jsonify({'success': False, 'message': '数据文件不存在'}), 404

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            tree_data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return jsonify({'success': False, 'message': '数据文件读取失败'}), 500

    try:
        result = pca_weight_reduction(tree_data)
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': f'PCA 分析出错: {type(e).__name__}'}), 500

    preprocessed = DataService.normalize_weights(result['tree_data'])
    DataService.add_node_ids(preprocessed)

    return jsonify({
        'success': True,
        'data': {
            'tree_data': preprocessed,
            'analysis': result['analysis'],
            'dataset_info': dataset.to_dict(),
        },
    })


@analysis_bp.route('/cluster', methods=['POST'])
@token_required
def cluster_csv(current_user):
    """上传 CSV 文件，做降维 + 层次聚类，返回生成的树和分析结果"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': '请上传 CSV 文件'}), 400

    file = request.files['file']
    if not file.filename or not file.filename.lower().endswith('.csv'):
        return jsonify({'success': False, 'message': '仅支持 .csv 格式'}), 400

    method = request.form.get('method', 'pca')
    if method not in ('pca', 'tsne'):
        method = 'pca'

    label_column = request.form.get('label_column', '').strip() or None

    n_clusters = request.form.get('n_clusters', '')
    try:
        n_clusters = int(n_clusters) if n_clusters else None
    except ValueError:
        n_clusters = None

    try:
        csv_content = file.read().decode('utf-8')
    except UnicodeDecodeError:
        try:
            file.seek(0)
            csv_content = file.read().decode('gbk')
        except Exception:
            return jsonify({'success': False, 'message': '无法解析文件编码'}), 400

    try:
        result = csv_to_hierarchical_tree(csv_content, method, n_clusters, label_column)
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception:
        return jsonify({'success': False, 'message': '聚类分析出错，请检查数据格式和参数'}), 500

    preprocessed = DataService.normalize_weights(result['tree_data'])
    DataService.add_node_ids(preprocessed)

    return jsonify({
        'success': True,
        'data': {
            'tree_data': preprocessed,
            'analysis': result['analysis'],
        },
    })


@analysis_bp.route('/cluster/save', methods=['POST'])
@token_required
def save_cluster_result(current_user):
    """将聚类生成的树保存为一个数据集"""
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': '请求体为空'}), 400

    tree_data = data.get('tree_data')
    name = data.get('name', '').strip()
    description = data.get('description', '').strip()

    if not tree_data:
        return jsonify({'success': False, 'message': '缺少树数据'}), 400
    if not name:
        name = '聚类分析结果'

    metrics = DataService.calculate_tree_metrics(tree_data)
    filename = uuid.uuid4().hex + '.json'
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)

    json_str = json.dumps(tree_data, ensure_ascii=False, indent=2)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(json_str)

    dataset = Dataset(
        name=name,
        description=description or '通过降维聚类自动生成',
        filename=filename,
        original_filename=f'{name}.json',
        file_size=len(json_str.encode('utf-8')),
        node_count=metrics['node_count'],
        max_depth=metrics['max_depth'],
        leaf_count=metrics['leaf_count'],
        user_id=current_user.id,
    )

    try:
        db.session.add(dataset)
        db.session.commit()
    except Exception:
        db.session.rollback()
        if os.path.exists(filepath):
            os.remove(filepath)
        return jsonify({'success': False, 'message': '保存失败'}), 500

    return jsonify({
        'success': True,
        'data': dataset.to_dict(),
        'message': '聚类结果已保存为数据集',
    }), 201
