import copy
import json
import os
import uuid

from flask import current_app
from sqlalchemy import or_

from ..extensions import db
from ..models.dataset import Dataset
from ..utils.validators import validate_json_structure


MAX_TREE_DEPTH = 500


class DataService:
    """层次数据集相关业务逻辑"""

    # ------------------------------------------------------------------
    # 数据验证
    # ------------------------------------------------------------------

    @staticmethod
    def validate_hierarchical_data(data):
        """
        验证数据是否为合法的层次树结构。
        返回错误列表，空列表表示验证通过。
        """
        is_valid, errors = validate_json_structure(data)
        return errors

    # ------------------------------------------------------------------
    # 树形指标计算
    # ------------------------------------------------------------------

    @staticmethod
    def calculate_tree_metrics(data):
        """
        计算树的统计指标: 节点总数、最大深度、叶节点数。
        返回 dict: {node_count, max_depth, leaf_count}
        """
        metrics = {'node_count': 0, 'max_depth': 0, 'leaf_count': 0}
        DataService._traverse_for_metrics(data, 0, metrics)
        return metrics

    @staticmethod
    def _traverse_for_metrics(node, depth, metrics):
        if depth > MAX_TREE_DEPTH:
            return
        metrics['node_count'] += 1
        metrics['max_depth'] = max(metrics['max_depth'], depth)

        children = node.get('children', [])
        if not children:
            metrics['leaf_count'] += 1
        else:
            for child in children:
                DataService._traverse_for_metrics(child, depth + 1, metrics)

    # ------------------------------------------------------------------
    # 权重规范化
    # ------------------------------------------------------------------

    @staticmethod
    def normalize_weights(data):
        """
        权重处理流水线:
        1. 叶节点缺省 value 设为 1
        2. 非叶节点 value = 子节点 value 之和
        3. 同层兄弟节点 normalized_value 归一化到 [0, 1]
        """
        DataService._assign_default_values(data)
        DataService._aggregate_values(data)
        DataService._normalize_sibling_values(data)
        return data

    @staticmethod
    def _assign_default_values(node):
        children = node.get('children', [])
        if not children:
            if node.get('value') is None or (
                isinstance(node.get('value'), (int, float)) and node['value'] <= 0
            ):
                node['value'] = 1
        else:
            for child in children:
                DataService._assign_default_values(child)

    @staticmethod
    def _aggregate_values(node):
        children = node.get('children', [])
        if children:
            total = 0
            for child in children:
                DataService._aggregate_values(child)
                total += child.get('value', 1)
            node['value'] = total
        return node

    @staticmethod
    def _normalize_sibling_values(node):
        node['normalized_value'] = 1.0
        children = node.get('children', [])
        if children:
            total = sum(child.get('value', 1) for child in children)
            for child in children:
                if total > 0:
                    child['normalized_value'] = child.get('value', 1) / total
                else:
                    child['normalized_value'] = 1.0 / len(children)
                DataService._normalize_sibling_values(child)

    # ------------------------------------------------------------------
    # 节点信息注入
    # ------------------------------------------------------------------

    @staticmethod
    def add_depth_info(node, depth=0):
        """为每个节点添加 depth 字段"""
        node['depth'] = depth
        for child in node.get('children', []):
            DataService.add_depth_info(child, depth + 1)
        return node

    @staticmethod
    def add_node_ids(node, node_id=None):
        """为每个节点添加唯一路径 ID，方便前端追踪。同名兄弟自动追加索引。"""
        if node_id is None:
            node_id = node.get('name', 'unknown')
        node['id'] = node_id

        name_counter = {}
        for child in node.get('children', []):
            child_name = child.get('name', 'unknown')
            count = name_counter.get(child_name, 0)
            name_counter[child_name] = count + 1
            dedup_name = f'{child_name}_{count}' if count > 0 else child_name
            child_id = f'{node_id}/{dedup_name}'
            DataService.add_node_ids(child, node_id=child_id)
        return node

    @staticmethod
    def count_subtree_leaves(node):
        """为每个节点添加 leaf_count 字段（子树叶节点数）"""
        children = node.get('children', [])
        if not children:
            node['leaf_count'] = 1
            return 1
        total = 0
        for child in children:
            total += DataService.count_subtree_leaves(child)
        node['leaf_count'] = total
        return total

    # ------------------------------------------------------------------
    # 完整预处理流水线
    # ------------------------------------------------------------------

    @staticmethod
    def preprocess_data(data):
        """
        数据预处理完整流水线:
        1. 权重规范化（默认值、聚合、归一化）
        2. 注入深度信息
        3. 注入节点ID
        4. 计算子树叶节点数
        """
        processed = copy.deepcopy(data)
        processed = DataService.normalize_weights(processed)
        processed = DataService.add_depth_info(processed)
        processed = DataService.add_node_ids(processed)
        DataService.count_subtree_leaves(processed)
        return processed

    # ------------------------------------------------------------------
    # 文件存储与数据集 CRUD
    # ------------------------------------------------------------------

    @staticmethod
    def save_uploaded_file(file, user_id, name=None, description=''):
        """
        保存上传的 JSON 文件并创建数据集记录。
        返回 (dataset, error_message)。
        """
        original_filename = file.filename

        # 读取并解析 JSON
        try:
            content = file.read()
            data = json.loads(content.decode('utf-8'))
        except json.JSONDecodeError as e:
            return None, f'JSON解析失败: {str(e)}'
        except UnicodeDecodeError:
            return None, '文件编码错误，请使用UTF-8编码'

        # 验证层次结构
        errors = DataService.validate_hierarchical_data(data)
        if errors:
            return None, '; '.join(errors)

        # 计算树指标
        metrics = DataService.calculate_tree_metrics(data)

        # 生成唯一存储文件名
        ext = 'json'
        if '.' in original_filename:
            ext = original_filename.rsplit('.', 1)[1].lower()
        stored_filename = f'{uuid.uuid4().hex}.{ext}'

        # 写入磁盘
        upload_folder = current_app.config['UPLOAD_FOLDER']
        filepath = os.path.join(upload_folder, stored_filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        file_size = len(content)

        # 创建数据库记录，失败时清理磁盘文件
        try:
            dataset = Dataset(
                name=name or original_filename.rsplit('.', 1)[0],
                description=description,
                filename=stored_filename,
                original_filename=original_filename,
                file_size=file_size,
                node_count=metrics['node_count'],
                max_depth=metrics['max_depth'],
                leaf_count=metrics['leaf_count'],
                user_id=user_id,
            )
            db.session.add(dataset)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            if os.path.exists(filepath):
                os.remove(filepath)
            return None, f'数据库保存失败: {str(e)}'

        return dataset, None

    @staticmethod
    def get_dataset_raw_data(dataset):
        """读取原始 JSON 数据。返回 (data, error_message)。"""
        filepath = os.path.join(
            current_app.config['UPLOAD_FOLDER'], dataset.filename
        )
        if not os.path.exists(filepath):
            return None, '数据文件不存在'

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            current_app.logger.error('读取数据文件失败: %s', e)
            return None, '数据文件读取失败，文件可能已损坏'
        return data, None

    @staticmethod
    def get_dataset_processed_data(dataset):
        """获取经过预处理的可视化就绪数据。返回 (data, error_message)。"""
        data, error = DataService.get_dataset_raw_data(dataset)
        if error:
            return None, error
        processed = DataService.preprocess_data(data)
        return processed, None

    @staticmethod
    def get_user_datasets(user_id, page=1, per_page=20, search=None):
        """分页获取用户数据集列表"""
        query = Dataset.query.filter_by(user_id=user_id)

        if search:
            like_pattern = '%{}%'.format(
                search.replace('%', r'\%').replace('_', r'\_')
            )
            query = query.filter(
                or_(
                    Dataset.name.ilike(like_pattern),
                    Dataset.description.ilike(like_pattern),
                    Dataset.original_filename.ilike(like_pattern),
                )
            )

        query = query.order_by(Dataset.created_at.desc())
        pagination = query.paginate(
            page=page, per_page=per_page, error_out=False
        )

        return {
            'items': [item.to_summary_dict() for item in pagination.items],
            'total': pagination.total,
            'page': pagination.page,
            'per_page': pagination.per_page,
            'pages': pagination.pages,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev,
        }

    @staticmethod
    def get_dataset_by_id(dataset_id, user_id):
        """根据ID获取数据集（确保属于当前用户）"""
        return Dataset.query.filter_by(
            id=dataset_id, user_id=user_id
        ).first()

    @staticmethod
    def update_dataset(dataset, data):
        """更新数据集元信息。返回 (dataset, error_message)。"""
        if 'name' in data and data['name']:
            name = str(data['name']).strip()
            if len(name) > 200:
                return None, '名称长度不能超过200个字符'
            dataset.name = name
        if 'description' in data:
            dataset.description = str(data.get('description', '') or '')
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error('更新数据集失败: %s', e)
            return None, '更新失败，请重试'
        return dataset, None

    @staticmethod
    def delete_dataset(dataset):
        """删除数据集及其文件。文件删除失败不影响数据库记录删除。"""
        filepath = os.path.join(
            current_app.config['UPLOAD_FOLDER'], dataset.filename
        )
        db.session.delete(dataset)
        db.session.commit()
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
        except OSError:
            pass
        return True

    # ------------------------------------------------------------------
    # 树结构预览（限深度）
    # ------------------------------------------------------------------

    @staticmethod
    def get_tree_structure_preview(data, max_depth=3):
        """获取截断深度后的树结构预览"""
        return DataService._truncate_tree(data, 0, max_depth)

    @staticmethod
    def _truncate_tree(node, current_depth, max_depth):
        result = {
            'name': node.get('name', ''),
            'value': node.get('value', None),
        }
        children = node.get('children', [])

        if children and current_depth < max_depth:
            truncated_children = [
                DataService._truncate_tree(child, current_depth + 1, max_depth)
                for child in children
            ]
            if len(truncated_children) > 20:
                result['children'] = truncated_children[:20]
                result['_truncated'] = True
                result['_total_children'] = len(children)
            else:
                result['children'] = truncated_children
        elif children:
            result['_children_count'] = len(children)
            result['_truncated_at_depth'] = current_depth

        return result
