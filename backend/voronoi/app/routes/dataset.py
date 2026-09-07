from flask import Blueprint, request, jsonify

from ..services.data_service import DataService
from ..utils.decorators import token_required

dataset_bp = Blueprint('dataset', __name__, url_prefix='/api/datasets')


@dataset_bp.route('/upload', methods=['POST'])
@token_required
def upload_dataset(current_user):
    """上传 JSON 层次数据文件"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': '请选择要上传的文件'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': '未选择文件'}), 400

    if not file.filename.lower().endswith('.json'):
        return jsonify({
            'success': False,
            'message': '仅支持JSON格式文件',
        }), 400

    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()

    dataset, error = DataService.save_uploaded_file(
        file=file,
        user_id=current_user.id,
        name=name if name else None,
        description=description,
    )

    if error:
        return jsonify({'success': False, 'message': error}), 400

    return jsonify({
        'success': True,
        'message': '数据集上传成功',
        'data': dataset.to_dict(),
    }), 201


@dataset_bp.route('', methods=['GET'])
@token_required
def list_datasets(current_user):
    """获取当前用户的数据集列表（分页）"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    search = request.args.get('search', None, type=str)

    page = max(page, 1)
    per_page = min(max(per_page, 1), 100)

    result = DataService.get_user_datasets(
        user_id=current_user.id,
        page=page,
        per_page=per_page,
        search=search,
    )

    return jsonify({'success': True, 'data': result}), 200


@dataset_bp.route('/<int:dataset_id>', methods=['GET'])
@token_required
def get_dataset(current_user, dataset_id):
    """获取单个数据集的详细信息"""
    dataset = DataService.get_dataset_by_id(dataset_id, current_user.id)
    if not dataset:
        return jsonify({'success': False, 'message': '数据集不存在'}), 404

    return jsonify({
        'success': True,
        'data': dataset.to_dict(),
    }), 200


@dataset_bp.route('/<int:dataset_id>/data', methods=['GET'])
@token_required
def get_dataset_data(current_user, dataset_id):
    """获取经过预处理的数据（供可视化前端使用）"""
    dataset = DataService.get_dataset_by_id(dataset_id, current_user.id)
    if not dataset:
        return jsonify({'success': False, 'message': '数据集不存在'}), 404

    processed_data, error = DataService.get_dataset_processed_data(dataset)
    if error:
        return jsonify({'success': False, 'message': error}), 500

    return jsonify({
        'success': True,
        'data': {
            'dataset_info': dataset.to_dict(),
            'tree_data': processed_data,
        },
    }), 200


@dataset_bp.route('/<int:dataset_id>/raw', methods=['GET'])
@token_required
def get_dataset_raw(current_user, dataset_id):
    """获取原始未处理的数据"""
    dataset = DataService.get_dataset_by_id(dataset_id, current_user.id)
    if not dataset:
        return jsonify({'success': False, 'message': '数据集不存在'}), 404

    raw_data, error = DataService.get_dataset_raw_data(dataset)
    if error:
        return jsonify({'success': False, 'message': error}), 500

    return jsonify({
        'success': True,
        'data': {
            'dataset_info': dataset.to_dict(),
            'tree_data': raw_data,
        },
    }), 200


@dataset_bp.route('/<int:dataset_id>/preview', methods=['GET'])
@token_required
def preview_dataset(current_user, dataset_id):
    """获取数据集的截断预览（限制深度和宽度）"""
    dataset = DataService.get_dataset_by_id(dataset_id, current_user.id)
    if not dataset:
        return jsonify({'success': False, 'message': '数据集不存在'}), 404

    max_depth = request.args.get('max_depth', 3, type=int)
    max_depth = min(max(max_depth, 1), 10)

    raw_data, error = DataService.get_dataset_raw_data(dataset)
    if error:
        return jsonify({'success': False, 'message': error}), 500

    preview = DataService.get_tree_structure_preview(
        raw_data, max_depth=max_depth
    )

    return jsonify({
        'success': True,
        'data': {
            'dataset_info': dataset.to_summary_dict(),
            'preview': preview,
        },
    }), 200


@dataset_bp.route('/<int:dataset_id>', methods=['PUT'])
@token_required
def update_dataset(current_user, dataset_id):
    """更新数据集元信息（名称、描述）"""
    dataset = DataService.get_dataset_by_id(dataset_id, current_user.id)
    if not dataset:
        return jsonify({'success': False, 'message': '数据集不存在'}), 404

    data = request.get_json()
    if not data:
        return jsonify({
            'success': False,
            'message': '请提供JSON格式的请求数据',
        }), 400

    dataset, error = DataService.update_dataset(dataset, data)
    if error:
        return jsonify({'success': False, 'message': error}), 400

    return jsonify({
        'success': True,
        'message': '数据集更新成功',
        'data': dataset.to_dict(),
    }), 200


@dataset_bp.route('/<int:dataset_id>', methods=['DELETE'])
@token_required
def delete_dataset(current_user, dataset_id):
    """删除数据集及其文件"""
    dataset = DataService.get_dataset_by_id(dataset_id, current_user.id)
    if not dataset:
        return jsonify({'success': False, 'message': '数据集不存在'}), 404

    DataService.delete_dataset(dataset)

    return jsonify({
        'success': True,
        'message': '数据集删除成功',
    }), 200
