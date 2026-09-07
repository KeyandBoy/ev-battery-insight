"""
降维分析服务

功能一：PCA 多维属性降权
  - 从树节点中提取所有数值型属性
  - StandardScaler 标准化 → PCA 降至 1 维
  - 将主成分得分归一化为正权重，写回 value 字段

功能二：CSV 表格数据 → 降维 + 层次聚类 → 生成树
  - 读取 CSV，选取数值列
  - PCA / t-SNE 降至 2D（用于散点图展示）
  - AgglomerativeClustering 层次聚类
  - 从聚类标签构建树形 JSON
"""

import io

import numpy as np
import pandas as pd
from sklearn.cluster import AgglomerativeClustering
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
from sklearn.preprocessing import StandardScaler


SKIP_KEYS = frozenset([
    'name', 'children', 'id', 'depth', 'value',
    'normalized_value', 'node_id', 'leaf_count',
])


def _collect_nodes(node, result):
    result.append(node)
    for child in node.get('children', []):
        _collect_nodes(child, result)


def _find_numeric_keys(nodes):
    keys = set()
    for node in nodes:
        for k, v in node.items():
            if k not in SKIP_KEYS and isinstance(v, (int, float)) and not isinstance(v, bool):
                keys.add(k)
    return sorted(keys)


def pca_weight_reduction(tree_data):
    """
    对树节点的多维数值属性做 PCA 降维，得到 1 维权重。

    Returns dict:
      tree_data    — 权重已更新的树
      analysis     — PCA 分析元信息（主成分方差比、特征贡献等）
    """
    import copy
    tree_data = copy.deepcopy(tree_data)

    nodes = []
    _collect_nodes(tree_data, nodes)

    numeric_keys = _find_numeric_keys(nodes)
    if not numeric_keys:
        raise ValueError('树节点中未找到可用的数值属性，无法进行 PCA 降维')

    matrix = np.array(
        [[n.get(k, 0) for k in numeric_keys] for n in nodes],
        dtype=float,
    )

    scaler = StandardScaler()
    scaled = scaler.fit_transform(matrix)

    pca = PCA(n_components=1)
    scores = pca.fit_transform(scaled).flatten()

    min_score = scores.min()
    weights = scores - min_score + 0.1

    for i, node in enumerate(nodes):
        node['value'] = round(float(weights[i]), 4)

    feature_importance = {
        k: round(float(v), 4)
        for k, v in zip(numeric_keys, pca.components_[0])
    }

    return {
        'tree_data': tree_data,
        'analysis': {
            'method': 'PCA',
            'features_used': numeric_keys,
            'explained_variance_ratio': round(float(pca.explained_variance_ratio_[0]), 4),
            'n_nodes': len(nodes),
            'feature_importance': feature_importance,
            'weight_stats': {
                'min': round(float(weights.min()), 4),
                'max': round(float(weights.max()), 4),
                'mean': round(float(weights.mean()), 4),
            },
        },
    }


def csv_to_hierarchical_tree(csv_content, method='pca', n_clusters=None, label_column=None):
    """
    CSV → 降维 + 层次聚类 → 树形 JSON。

    Args:
        csv_content  : CSV 字符串
        method       : 'pca' | 'tsne'
        n_clusters   : 聚类数量，None 时自动决定
        label_column : 用于标记行名的列名，不参与数值计算

    Returns dict:
      tree_data      — 生成的层次树
      analysis       — 降维 + 聚类元信息 + 2D 坐标
    """
    df = pd.read_csv(io.StringIO(csv_content))

    if df.empty:
        raise ValueError('CSV 文件为空')

    labels = None
    if label_column and label_column in df.columns:
        labels = df[label_column].astype(str).tolist()
        df = df.drop(columns=[label_column])

    numeric_df = df.select_dtypes(include=[np.number])
    if numeric_df.empty:
        raise ValueError('CSV 中未找到数值型列，无法进行分析')

    feature_names = numeric_df.columns.tolist()
    X = np.nan_to_num(numeric_df.values.astype(float), nan=0.0)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    n_samples, n_features = X_scaled.shape

    if method == 'tsne' and n_features > 2 and n_samples > 5:
        perplexity = min(30, n_samples - 1)
        reducer = TSNE(n_components=2, random_state=42, perplexity=perplexity)
        X_2d = reducer.fit_transform(X_scaled)
        reduction_info = {'method': 't-SNE', 'perplexity': perplexity}
    else:
        n_comp = min(2, n_features)
        reducer = PCA(n_components=n_comp)
        X_2d = reducer.fit_transform(X_scaled)
        if X_2d.shape[1] == 1:
            X_2d = np.column_stack([X_2d, np.zeros(n_samples)])
        reduction_info = {
            'method': 'PCA',
            'explained_variance_ratio': [
                round(float(v), 4) for v in reducer.explained_variance_ratio_
            ],
        }

    if n_samples < 2:
        raise ValueError('数据样本数不足，至少需要 2 条记录才能进行聚类分析')

    if n_clusters is None:
        n_clusters = min(max(3, n_samples // 5), 10)
    n_clusters = max(2, min(n_clusters, n_samples))

    clustering = AgglomerativeClustering(n_clusters=n_clusters)
    cluster_labels = clustering.fit_predict(X_scaled)

    if labels is None:
        labels = [f'Sample_{i}' for i in range(n_samples)]

    cluster_groups = {}
    for i, cl in enumerate(cluster_labels):
        cluster_groups.setdefault(int(cl), []).append(i)

    root = {'name': 'Root', 'children': []}
    for cl_id in sorted(cluster_groups):
        indices = cluster_groups[cl_id]
        cluster_node = {
            'name': f'Cluster_{cl_id}',
            'children': [],
        }
        for idx in indices:
            leaf = {
                'name': labels[idx],
                'value': round(float(np.linalg.norm(X_scaled[idx])), 4),
            }
            for j, fname in enumerate(feature_names):
                leaf[fname] = round(float(X[idx][j]), 4)
            cluster_node['children'].append(leaf)
        root['children'].append(cluster_node)

    coords = []
    for i in range(n_samples):
        coords.append({
            'x': round(float(X_2d[i, 0]), 4),
            'y': round(float(X_2d[i, 1]), 4),
            'label': labels[i],
            'cluster': int(cluster_labels[i]),
        })

    return {
        'tree_data': root,
        'analysis': {
            'reduction': reduction_info,
            'clustering': {
                'method': 'AgglomerativeClustering',
                'n_clusters': int(n_clusters),
                'cluster_sizes': {
                    f'Cluster_{k}': len(v) for k, v in sorted(cluster_groups.items())
                },
            },
            'data_info': {
                'n_samples': n_samples,
                'n_features': n_features,
                'feature_names': feature_names,
            },
            'scatter_data': coords,
        },
    }
