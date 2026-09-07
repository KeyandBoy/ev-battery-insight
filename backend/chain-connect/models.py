from database import get_db
from werkzeug.security import generate_password_hash, check_password_hash
import json


class User:
    @staticmethod
    def create(username, password, email=''):
        db = get_db()
        try:
            password_hash = generate_password_hash(password)
            cursor = db.execute(
                "INSERT INTO users (username, password_hash, email) VALUES (?, ?, ?)",
                (username, password_hash, email)
            )
            db.commit()
            user_id = cursor.lastrowid
            db.close()
            return {"id": user_id, "username": username, "email": email}
        except Exception as e:
            db.close()
            raise e

    @staticmethod
    def authenticate(username, password):
        db = get_db()
        try:
            user = db.execute(
                "SELECT * FROM users WHERE username = ?", (username,)
            ).fetchone()
            if user and check_password_hash(user['password_hash'], password):
                return {"id": user['id'], "username": user['username'], "email": user['email'] or ''}
            return None
        finally:
            db.close()

    @staticmethod
    def get_by_id(user_id):
        db = get_db()
        try:
            user = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
            if user:
                return {"id": user['id'], "username": user['username'], "email": user['email'] or ''}
            return None
        finally:
            db.close()

    @staticmethod
    def update_profile(user_id, email=None):
        db = get_db()
        try:
            if email is not None:
                db.execute("UPDATE users SET email = ? WHERE id = ?", (email, user_id))
            db.commit()
        finally:
            db.close()


class Project:
    @staticmethod
    def create(user_id, name, description='', data_type='social', graph_data=None, layout_config=None, visual_config=None):
        db = get_db()
        try:
            graph_data_str = json.dumps(graph_data or {}, ensure_ascii=False)
            layout_config_str = json.dumps(layout_config or {}, ensure_ascii=False)
            visual_config_str = json.dumps(visual_config or {}, ensure_ascii=False)
            cursor = db.execute(
                """INSERT INTO projects (user_id, name, description, data_type, graph_data, layout_config, visual_config)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (user_id, name, description, data_type, graph_data_str, layout_config_str, visual_config_str)
            )
            db.commit()
            return cursor.lastrowid
        finally:
            db.close()

    @staticmethod
    def get_by_id(project_id, user_id):
        db = get_db()
        try:
            project = db.execute(
                "SELECT * FROM projects WHERE id = ? AND user_id = ?", (project_id, user_id)
            ).fetchone()
            if project:
                return {
                    "id": project['id'],
                    "user_id": project['user_id'],
                    "name": project['name'],
                    "description": project['description'],
                    "data_type": project['data_type'],
                    "graph_data": json.loads(project['graph_data']),
                    "layout_config": json.loads(project['layout_config']),
                    "visual_config": json.loads(project['visual_config']),
                    "created_at": project['created_at'],
                    "updated_at": project['updated_at']
                }
            return None
        finally:
            db.close()

    @staticmethod
    def get_all_by_user(user_id):
        db = get_db()
        try:
            projects = db.execute(
                "SELECT * FROM projects WHERE user_id = ? ORDER BY updated_at DESC", (user_id,)
            ).fetchall()
            result = []
            for p in projects:
                result.append({
                    "id": p['id'],
                    "name": p['name'],
                    "description": p['description'],
                    "data_type": p['data_type'],
                    "graph_data": json.loads(p['graph_data']),
                    "layout_config": json.loads(p['layout_config']),
                    "visual_config": json.loads(p['visual_config']),
                    "created_at": p['created_at'],
                    "updated_at": p['updated_at']
                })
            return result
        finally:
            db.close()

    @staticmethod
    def update(project_id, user_id, **kwargs):
        db = get_db()
        try:
            allowed_fields = ['name', 'description', 'data_type', 'graph_data', 'layout_config', 'visual_config']
            updates = []
            values = []
            for field in allowed_fields:
                if field in kwargs and kwargs[field] is not None:
                    if field in ('graph_data', 'layout_config', 'visual_config'):
                        updates.append(f"{field} = ?")
                        values.append(json.dumps(kwargs[field], ensure_ascii=False))
                    else:
                        updates.append(f"{field} = ?")
                        values.append(kwargs[field])
            if not updates:
                return False
            updates.append("updated_at = CURRENT_TIMESTAMP")
            values.extend([project_id, user_id])
            query = f"UPDATE projects SET {', '.join(updates)} WHERE id = ? AND user_id = ?"
            db.execute(query, values)
            db.commit()
            return True
        finally:
            db.close()

    @staticmethod
    def delete(project_id, user_id):
        db = get_db()
        try:
            db.execute("DELETE FROM projects WHERE id = ? AND user_id = ?", (project_id, user_id))
            db.commit()
            return True
        finally:
            db.close()


class SampleDataset:
    @staticmethod
    def get_all():
        db = get_db()
        try:
            datasets = db.execute("SELECT * FROM sample_datasets").fetchall()
            result = []
            for d in datasets:
                result.append({
                    "id": d['id'],
                    "name": d['name'],
                    "description": d['description'],
                    "category": d['category'],
                    "graph_data": json.loads(d['graph_data'])
                })
            return result
        finally:
            db.close()

    @staticmethod
    def get_by_id(dataset_id):
        db = get_db()
        try:
            d = db.execute("SELECT * FROM sample_datasets WHERE id = ?", (dataset_id,)).fetchone()
            if d:
                return {
                    "id": d['id'],
                    "name": d['name'],
                    "description": d['description'],
                    "category": d['category'],
                    "graph_data": json.loads(d['graph_data'])
                }
            return None
        finally:
            db.close()
