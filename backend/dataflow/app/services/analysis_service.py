import math
import os

import numpy as np

from app.models import DataRecord, Dataset
from app.services.dataset_service import detect_numeric_fields, parse_rows, resolve_dataset_file_path


class AnalysisValidationError(ValueError):
    pass


def load_dataset_records(dataset_id, user_id):
    dataset = Dataset.query.filter_by(id=dataset_id, user_id=user_id).first()
    if dataset is None:
        raise AnalysisValidationError("Dataset does not exist or is not accessible.")

    records = (
        DataRecord.query.filter_by(dataset_id=dataset_id)
        .order_by(DataRecord.level.asc(), DataRecord.id.asc())
        .all()
    )
    if not records:
        raise AnalysisValidationError("The dataset has no records available for analysis.")

    return dataset, records


def build_pca_projection(dataset_id, user_id, max_rows=300, max_features=6):
    dataset = Dataset.query.filter_by(id=dataset_id, user_id=user_id).first()
    if dataset is None:
        raise AnalysisValidationError("Dataset does not exist or is not accessible.")

    file_path = resolve_dataset_file_path(dataset.file_path)
    if not file_path or not os.path.exists(file_path):
        raise AnalysisValidationError("Dataset file does not exist; PCA cannot run.")

    rows = parse_rows(file_path=file_path, source_type=dataset.source_type)
    if not rows:
        raise AnalysisValidationError("Dataset is empty; PCA cannot run.")

    max_rows = max(20, min(int(max_rows or 300), 2000))
    max_features = max(2, min(int(max_features or 6), 12))

    fields = list(rows[0].keys())
    numeric_fields = detect_numeric_fields(rows)
    if len(numeric_fields) < 1:
        raise AnalysisValidationError("PCA requires at least one numeric field.")

    selected_fields = numeric_fields[:max_features]
    if len(selected_fields) == 1:
        selected_fields.append("__row_index__")
    candidate_label_fields = [field for field in fields if field not in numeric_fields]
    label_field = candidate_label_fields[0] if candidate_label_fields else ""

    vectors = []
    labels = []
    for row_index, row in enumerate(rows):
        values = []
        has_numeric_value = False
        for field in selected_fields:
            if field == "__row_index__":
                num = float(row_index + 1)
            else:
                num = _to_float_or_none(row.get(field))
            values.append(num)
            if num is not None:
                has_numeric_value = True
        if not has_numeric_value:
            continue

        vectors.append(values)
        raw_label = row.get(label_field) if label_field else None
        labels.append(str(raw_label or "Sample").strip() or "Sample")
        if len(vectors) >= max_rows:
            break

    if len(vectors) < 3:
        raise AnalysisValidationError("PCA requires at least 3 valid samples.")

    matrix = _fill_missing_with_col_means(vectors)
    if matrix.shape[0] < 3 or matrix.shape[1] < 2:
        raise AnalysisValidationError("PCA requires enough valid samples and features.")

    means = matrix.mean(axis=0)
    stds = matrix.std(axis=0)
    valid_mask = stds > 1e-12
    if int(valid_mask.sum()) < 2:
        raise AnalysisValidationError("Numeric feature variance is too small for PCA.")

    matrix = matrix[:, valid_mask]
    used_fields = []
    for idx, field in enumerate(selected_fields):
        if not bool(valid_mask[idx]):
            continue
        if field == "__row_index__":
            used_fields.append("Sample Index (derived)")
        else:
            used_fields.append(field)
    means = means[valid_mask]
    stds = stds[valid_mask]
    standardized = (matrix - means) / stds

    covariance = np.cov(standardized, rowvar=False)
    if np.ndim(covariance) == 0:
        raise AnalysisValidationError("Covariance matrix shape is invalid for PCA.")

    eig_values, eig_vectors = np.linalg.eigh(covariance)
    order = np.argsort(eig_values)[::-1]
    eig_values = eig_values[order]
    eig_vectors = eig_vectors[:, order]

    component_count = min(2, eig_vectors.shape[1])
    principal_vectors = eig_vectors[:, :component_count]
    projected = standardized @ principal_vectors
    if component_count < 2:
        projected = np.column_stack([projected[:, 0], np.zeros(projected.shape[0])])

    positive_eig_values = np.maximum(eig_values, 0.0)
    total_variance = float(np.sum(positive_eig_values))
    if total_variance <= 1e-12:
        explained_ratios = [0.0, 0.0]
    else:
        explained_ratios = []
        for idx in range(2):
            if idx < len(positive_eig_values):
                explained_ratios.append(float(positive_eig_values[idx] / total_variance))
            else:
                explained_ratios.append(0.0)

    points = []
    for idx in range(projected.shape[0]):
        points.append(
            {
                "index": idx + 1,
                "label": labels[idx] if idx < len(labels) else "Sample",
                "pc1": round(float(projected[idx, 0]), 6),
                "pc2": round(float(projected[idx, 1]), 6),
            }
        )

    component_weights = []
    for field_idx, field in enumerate(used_fields):
        pc1_weight = float(principal_vectors[field_idx, 0]) if principal_vectors.shape[1] > 0 else 0.0
        pc2_weight = float(principal_vectors[field_idx, 1]) if principal_vectors.shape[1] > 1 else 0.0
        component_weights.append(
            {
                "field": field,
                "pc1_weight": round(pc1_weight, 6),
                "pc2_weight": round(pc2_weight, 6),
                "pc_abs_sum": round(abs(pc1_weight) + abs(pc2_weight), 6),
            }
        )
    component_weights.sort(key=lambda item: item["pc_abs_sum"], reverse=True)

    return {
        "dataset": dataset,
        "sample_count": projected.shape[0],
        "feature_count": len(used_fields),
        "label_field": label_field,
        "features": used_fields,
        "explained_variance_ratio": [round(explained_ratios[0], 6), round(explained_ratios[1], 6)],
        "points": points,
        "component_weights": component_weights[: min(10, len(component_weights))],
    }


def build_tree(records):
    node_map = {}
    root_children = []

    for record in records:
        node_map[record.id] = {
            "id": int(record.id),
            "parent_id": int(record.parent_id) if record.parent_id else None,
            "node_key": record.node_key,
            "node_name": record.node_name,
            "level": int(record.level),
            "value_num": float(record.value_num or 0),
            "is_abnormal": int(record.is_abnormal or 0),
            "children": [],
        }

    for record in records:
        current = node_map[record.id]
        if record.parent_id and record.parent_id in node_map:
            node_map[record.parent_id]["children"].append(current)
        else:
            root_children.append(current)

    root_value = sum(node["value_num"] for node in root_children)
    root = {
        "id": 0,
        "parent_id": None,
        "node_key": "root",
        "node_name": "Root",
        "level": -1,
        "value_num": root_value,
        "is_abnormal": 0,
        "children": root_children,
    }
    return _maybe_expand_flat_path_tree(root)


def extract_features(root):
    nodes = []
    _collect_nodes(root, nodes)
    non_root = [node for node in nodes if node["level"] >= 0]
    leaf_nodes = [node for node in non_root if not node["children"]]
    parent_nodes = [node for node in non_root if node["children"]]
    max_depth = max([node["level"] for node in non_root], default=0)
    level_count = max_depth + 1 if non_root else 0

    level_distribution = {}
    for node in non_root:
        key = str(node["level"])
        level_distribution[key] = level_distribution.get(key, 0) + 1

    top_categories = sorted(
        [node for node in non_root if node["level"] == 0],
        key=lambda item: item["value_num"],
        reverse=True,
    )[:8]

    single_child_parent_count = sum(1 for node in parent_nodes if len(node["children"]) == 1)
    single_child_parent_ratio = (
        round(single_child_parent_count / len(parent_nodes), 4) if parent_nodes else 0.0
    )
    avg_branch_factor = (
        round(sum(len(node["children"]) for node in parent_nodes) / len(parent_nodes), 4)
        if parent_nodes
        else 0.0
    )

    return {
        "total_nodes": len(non_root),
        "leaf_nodes": len(leaf_nodes),
        "abnormal_leaf_nodes": sum(1 for node in leaf_nodes if node["is_abnormal"] == 1),
        "max_depth": max_depth,
        "level_count": level_count,
        "total_value": round(sum(node["value_num"] for node in leaf_nodes), 4),
        "level_distribution": level_distribution,
        "single_child_parent_ratio": single_child_parent_ratio,
        "avg_branch_factor": avg_branch_factor,
        "top_categories": [
            {
                "name": item["node_name"],
                "value": round(item["value_num"], 4),
            }
            for item in top_categories
        ],
    }


def prepare_treemap_tree(root, top_n=None, min_ratio=0.0):
    top_n = int(top_n or 0)
    min_ratio = float(min_ratio or 0.0)
    if top_n < 0:
        raise AnalysisValidationError("top_n cannot be less than 0.")
    if min_ratio < 0 or min_ratio >= 1:
        raise AnalysisValidationError("min_ratio must be in the range [0, 1).")

    cloned_root = _clone_tree(root)
    cloned_root = _collapse_single_child_chains(cloned_root, is_root=True)
    id_generator = _VirtualIdGenerator(start=-1)
    stats = {
        "aggregated_nodes": 0,
        "others_nodes": 0,
    }
    _compress_tree_for_treemap(
        node=cloned_root,
        id_generator=id_generator,
        top_n=top_n,
        min_ratio=min_ratio,
        stats=stats,
    )
    return cloned_root, stats


def build_treemap_layout(root, width, height, padding=1.0, layout_stats=None):
    if width <= 0 or height <= 0:
        raise AnalysisValidationError("Canvas width and height must be greater than 0.")

    root_rect = {"x": 0.0, "y": 0.0, "width": float(width), "height": float(height)}
    root_with_rect = dict(root)
    root_with_rect["rect"] = root_rect

    result = []
    _layout_node(
        root_with_rect,
        result,
        padding=float(padding),
        layout_stats=layout_stats or {},
    )
    return result


def _layout_node(node, result, padding, layout_stats):
    children = node.get("children") or []
    if not children:
        return

    rect = node["rect"]
    inner = _shrink_rect(rect, padding)
    if inner["width"] <= 0 or inner["height"] <= 0:
        return

    children = _filter_small_other_children(children, inner, layout_stats)
    if not children:
        return

    placements = _squarify(children, inner)
    for child, child_rect in placements:
        child_with_rect = dict(child)
        child_with_rect["rect"] = child_rect
        result.append(
            {
                "id": child_with_rect["id"],
                "parent_id": child_with_rect["parent_id"],
                "node_key": child_with_rect["node_key"],
                "node_name": child_with_rect["node_name"],
                "level": child_with_rect["level"],
                "value_num": round(float(child_with_rect["value_num"]), 4),
                "is_abnormal": child_with_rect["is_abnormal"],
                "x": round(child_rect["x"], 2),
                "y": round(child_rect["y"], 2),
                "width": round(child_rect["width"], 2),
                "height": round(child_rect["height"], 2),
            }
        )
        _layout_node(child_with_rect, result, padding, layout_stats)


def _squarify(nodes, container):
    if not nodes:
        return []

    total_area = container["width"] * container["height"]
    if total_area <= 0:
        return []

    weights = [max(float(node.get("value_num") or 0), 0.0) for node in nodes]
    total_weight = sum(weights)
    if total_weight <= 0:
        weights = [1.0 for _ in nodes]
        total_weight = float(len(nodes))

    items = []
    for node, weight in zip(nodes, weights):
        items.append(
            {
                "node": node,
                "area": total_area * weight / total_weight,
            }
        )

    items.sort(key=lambda item: item["area"], reverse=True)
    x = container["x"]
    y = container["y"]
    w = container["width"]
    h = container["height"]
    row = []
    placements = []

    while items:
        next_item = items[0]
        side = min(w, h)
        if not row or _worst_ratio(row + [next_item], side) <= _worst_ratio(row, side):
            row.append(next_item)
            items.pop(0)
        else:
            row_rects, x, y, w, h = _layout_row(row, x, y, w, h)
            placements.extend(row_rects)
            row = []

    if row:
        row_rects, x, y, w, h = _layout_row(row, x, y, w, h)
        placements.extend(row_rects)

    return [(item["node"], item["rect"]) for item in placements]


def _layout_row(row, x, y, w, h):
    area_sum = sum(item["area"] for item in row)
    placed = []

    if w >= h:
        # When the container is wider than tall, lock the short side (height)
        # and carve a vertical strip. This keeps aspect ratios close to square.
        row_width = area_sum / h if h > 0 else 0
        cursor_y = y
        for item in row:
            item_height = item["area"] / row_width if row_width > 0 else 0
            placed.append(
                {
                    "node": item["node"],
                    "rect": {
                        "x": x,
                        "y": cursor_y,
                        "width": max(row_width, 0.0),
                        "height": max(item_height, 0.0),
                    },
                }
            )
            cursor_y += item_height
        x += row_width
        w = max(w - row_width, 0.0)
    else:
        row_height = area_sum / w if w > 0 else 0
        cursor_x = x
        for item in row:
            item_width = item["area"] / row_height if row_height > 0 else 0
            placed.append(
                {
                    "node": item["node"],
                    "rect": {
                        "x": cursor_x,
                        "y": y,
                        "width": max(item_width, 0.0),
                        "height": max(row_height, 0.0),
                    },
                }
            )
            cursor_x += item_width
        y += row_height
        h = max(h - row_height, 0.0)

    return placed, x, y, w, h


def _worst_ratio(row, side):
    if not row or side <= 0:
        return math.inf

    areas = [max(item["area"], 1e-12) for item in row]
    total = sum(areas)
    max_area = max(areas)
    min_area = min(areas)
    side_sq = side * side
    return max((side_sq * max_area) / (total * total), (total * total) / (side_sq * min_area))


def _shrink_rect(rect, padding):
    if padding <= 0:
        return rect

    width = rect["width"] - padding * 2
    height = rect["height"] - padding * 2
    if width <= 0 or height <= 0:
        return rect

    return {
        "x": rect["x"] + padding,
        "y": rect["y"] + padding,
        "width": width,
        "height": height,
    }


def _filter_small_other_children(children, container, layout_stats, max_ratio=10.0):
    if len(children) <= 1:
        return children

    total_value = sum(max(float(child.get("value_num") or 0.0), 0.0) for child in children)
    if total_value <= 0:
        return children

    long_side = max(float(container["width"]), float(container["height"]), 1e-9)
    short_side = max(min(float(container["width"]), float(container["height"])), 1e-9)
    min_share = short_side / (long_side * max(float(max_ratio or 10.0), 1.0))

    visible_children = []
    hidden_children = []
    for child in children:
        node_key = str(child.get("node_key") or "")
        node_name = str(child.get("node_name") or "")
        value = max(float(child.get("value_num") or 0.0), 0.0)
        share = value / total_value if total_value > 0 else 0.0
        is_other = node_name == "Other" or node_key.endswith("/__others__")
        if is_other and share < min_share:
            hidden_children.append(child)
            continue
        visible_children.append(child)

    if hidden_children:
        layout_stats["hidden_other_nodes"] = int(layout_stats.get("hidden_other_nodes", 0)) + len(hidden_children)
        layout_stats["hidden_other_value"] = round(
            float(layout_stats.get("hidden_other_value", 0.0))
            + sum(float(child.get("value_num") or 0.0) for child in hidden_children),
            4,
        )

    return visible_children or children


def _collect_nodes(node, sink):
    sink.append(node)
    for child in node.get("children") or []:
        _collect_nodes(child, sink)


def _clone_tree(node):
    cloned = {
        "id": int(node["id"]),
        "parent_id": int(node["parent_id"]) if node["parent_id"] is not None else None,
        "node_key": node["node_key"],
        "node_name": node["node_name"],
        "level": int(node["level"]),
        "value_num": float(node["value_num"]),
        "is_abnormal": int(node["is_abnormal"]),
        "children": [],
    }
    for child in node.get("children") or []:
        child_clone = _clone_tree(child)
        child_clone["parent_id"] = None if cloned["id"] == 0 else cloned["id"]
        cloned["children"].append(child_clone)
    return cloned


def _collapse_single_child_chains(node, is_root=False):
    children = [_collapse_single_child_chains(child) for child in (node.get("children") or [])]
    node["children"] = children

    if is_root:
        return node

    while len(node["children"]) == 1:
        child = node["children"][0]
        merged_name = "{0} / {1}".format(node["node_name"], child["node_name"])
        node = {
            "id": child["id"],
            "parent_id": node["parent_id"],
            "node_key": child["node_key"],
            "node_name": merged_name,
            "level": node["level"],
            "value_num": float(child["value_num"]),
            "is_abnormal": int(child["is_abnormal"]),
            "children": child.get("children") or [],
        }
        for grandchild in node["children"]:
            grandchild["parent_id"] = node["id"]

    return node


def _compress_tree_for_treemap(node, id_generator, top_n, min_ratio, stats):
    children = node.get("children") or []
    if not children:
        return

    for child in children:
        _compress_tree_for_treemap(
            node=child,
            id_generator=id_generator,
            top_n=top_n,
            min_ratio=min_ratio,
            stats=stats,
        )

    original_children = children
    total_value = sum(max(float(item.get("value_num") or 0.0), 0.0) for item in original_children)
    if total_value <= 0:
        return

    sorted_children = sorted(original_children, key=lambda item: float(item.get("value_num") or 0), reverse=True)
    kept = []
    dropped = []
    for index, child in enumerate(sorted_children):
        child_value = max(float(child.get("value_num") or 0.0), 0.0)
        child_ratio = child_value / total_value if total_value > 0 else 0.0
        should_drop_by_top_n = top_n > 0 and index >= top_n
        should_drop_by_ratio = min_ratio > 0 and child_ratio < min_ratio
        if should_drop_by_top_n or should_drop_by_ratio:
            dropped.append(child)
        else:
            kept.append(child)

    if not dropped:
        node["children"] = kept
        return

    if not kept and dropped:
        kept.append(dropped.pop(0))

    others_value = sum(max(float(item.get("value_num") or 0.0), 0.0) for item in dropped)
    if others_value > 0:
        others_node = {
            "id": id_generator.next_id(),
            "parent_id": node["id"],
            "node_key": "{0}/__others__".format(node["node_key"]),
            "node_name": "Other",
            "level": int(node["level"]) + 1,
            "value_num": others_value,
            "is_abnormal": 0,
            "children": [],
        }
        kept.append(others_node)
        stats["others_nodes"] += 1

    stats["aggregated_nodes"] += len(dropped)
    node["children"] = kept


class _VirtualIdGenerator:
    def __init__(self, start=-1):
        self.current = int(start)

    def next_id(self):
        value = self.current
        self.current -= 1
        return value


def _maybe_expand_flat_path_tree(root):
    first_level = root.get("children") or []
    if not first_level:
        return root

    if any((child.get("children") or []) for child in first_level):
        return root

    split_candidates = []
    for child in first_level:
        parts = _split_compound_label(child.get("node_name", ""))
        if len(parts) >= 2:
            split_candidates.append((child, parts))

    if len(split_candidates) < max(2, int(len(first_level) * 0.4)):
        return root

    node_map = {}
    id_generator = _VirtualIdGenerator(start=-1000000)

    for source_node, parts in split_candidates:
        value = float(source_node.get("value_num") or 0.0)
        parent_key = None
        path_parts = []
        for level, part in enumerate(parts):
            path_parts.append(part)
            path_key = "/".join(path_parts)
            existing = node_map.get(path_key)
            if existing is None:
                existing = {
                    "id": id_generator.next_id(),
                    "parent_id": None,
                    "node_key": path_key,
                    "node_name": part,
                    "level": level,
                    "value_num": 0.0,
                    "is_abnormal": 0,
                    "children": [],
                }
                node_map[path_key] = existing
            existing["value_num"] += value

            if parent_key is not None:
                parent_node = node_map[parent_key]
                if existing not in parent_node["children"]:
                    existing["parent_id"] = parent_node["id"]
                    parent_node["children"].append(existing)

            parent_key = path_key

    top_nodes = [node for node in node_map.values() if node["level"] == 0]
    if not top_nodes:
        return root

    root["children"] = top_nodes
    root["value_num"] = sum(node["value_num"] for node in top_nodes)
    return root


def _split_compound_label(label):
    text = str(label or "").strip()
    if not text:
        return []

    separators = ["/", ">", "|", "->", "=>"]
    for separator in separators:
        if separator in text:
            parts = [item.strip() for item in text.split(separator) if item.strip()]
            if 2 <= len(parts) <= 6:
                return parts
    return []


def _to_float_or_none(value):
    if value is None:
        return None
    if isinstance(value, str):
        raw = value.strip()
        if not raw:
            return None
        raw = raw.replace(",", "")
        try:
            num = float(raw)
        except ValueError:
            return None
    else:
        try:
            num = float(value)
        except (TypeError, ValueError):
            return None
    if math.isnan(num) or math.isinf(num):
        return None
    return float(num)


def _fill_missing_with_col_means(vectors):
    matrix = np.array(vectors, dtype=object)
    num_rows, num_cols = matrix.shape
    result = np.zeros((num_rows, num_cols), dtype=float)

    for col_idx in range(num_cols):
        col_values = []
        for row_idx in range(num_rows):
            num = _to_float_or_none(matrix[row_idx, col_idx])
            if num is not None:
                col_values.append(num)
        col_mean = float(np.mean(col_values)) if col_values else 0.0

        for row_idx in range(num_rows):
            num = _to_float_or_none(matrix[row_idx, col_idx])
            result[row_idx, col_idx] = col_mean if num is None else num

    return result
