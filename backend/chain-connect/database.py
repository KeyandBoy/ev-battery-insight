import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.db')


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # 用户表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            email TEXT,
            avatar TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 项目/数据集表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            description TEXT DEFAULT '',
            data_type TEXT NOT NULL DEFAULT 'social',
            graph_data TEXT NOT NULL DEFAULT '{}',
            layout_config TEXT DEFAULT '{}',
            visual_config TEXT DEFAULT '{}',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')

    # 预置示例社交网络数据集表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sample_datasets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT DEFAULT '',
            category TEXT DEFAULT 'social',
            graph_data TEXT NOT NULL DEFAULT '{}'
        )
    ''')

    conn.commit()

    # 插入预置示例数据
    cursor.execute("SELECT COUNT(*) FROM sample_datasets")
    count = cursor.fetchone()[0]
    if count == 0:
        _insert_sample_data(conn)
    else:
        _ensure_ev_sample_data(conn)

    conn.close()


def _ensure_ev_sample_data(conn):
    """Add generated application-case data to existing installations once."""
    import json
    from pathlib import Path

    name = "新能源汽车电池健康与充电风险关系网络"
    exists = conn.execute("SELECT 1 FROM sample_datasets WHERE name = ? LIMIT 1", (name,)).fetchone()
    graph_path = Path(__file__).resolve().parents[2] / "data" / "processed" / "public_ev_battery_network.json"
    if not graph_path.exists():
        return
    graph = json.loads(graph_path.read_text(encoding="utf-8"))
    if exists:
        conn.execute(
            "UPDATE sample_datasets SET description = ?, graph_data = ? WHERE name = ?",
            (graph["description"], json.dumps(graph, ensure_ascii=False), name),
        )
        conn.commit()
        return
    conn.execute(
        "INSERT INTO sample_datasets (name, description, category, graph_data) VALUES (?, ?, ?, ?)",
        (name, graph["description"], "ev_battery", json.dumps(graph, ensure_ascii=False)),
    )
    conn.commit()


def _insert_sample_data(conn):
    import json
    cursor = conn.cursor()

    # 示例1: 小型社交网络
    social_small = {
        "nodes": [
            {"id": "alice", "name": "Alice", "category": 0, "value": 28, "desc": "软件工程师，热爱开源"},
            {"id": "bob", "name": "Bob", "category": 0, "value": 35, "desc": "数据科学家，专注于机器学习"},
            {"id": "charlie", "name": "Charlie", "category": 1, "value": 22, "desc": "前端开发者，擅长Vue"},
            {"id": "diana", "name": "Diana", "category": 1, "value": 31, "desc": "产品经理，负责用户体验"},
            {"id": "eve", "name": "Eve", "category": 2, "value": 26, "desc": "UI设计师，擅长交互设计"},
            {"id": "frank", "name": "Frank", "category": 2, "value": 40, "desc": "技术总监，团队管理"},
            {"id": "grace", "name": "Grace", "category": 0, "value": 24, "desc": "后端开发者，擅长Python"},
            {"id": "henry", "name": "Henry", "category": 1, "value": 33, "desc": "运维工程师，负责部署"},
            {"id": "ivy", "name": "Ivy", "category": 2, "value": 29, "desc": "测试工程师，质量保障"},
            {"id": "jack", "name": "Jack", "category": 0, "value": 27, "desc": "全栈开发者，技术多面手"}
        ],
        "links": [
            {"source": "alice", "target": "bob", "value": 5, "relation": "同事"},
            {"source": "alice", "target": "charlie", "value": 3, "relation": "朋友"},
            {"source": "alice", "target": "frank", "value": 8, "relation": "上下级"},
            {"source": "bob", "target": "diana", "value": 4, "relation": "合作"},
            {"source": "bob", "target": "grace", "value": 6, "relation": "同事"},
            {"source": "charlie", "target": "eve", "value": 7, "relation": "搭档"},
            {"source": "charlie", "target": "jack", "value": 3, "relation": "朋友"},
            {"source": "diana", "target": "frank", "value": 9, "relation": "上下级"},
            {"source": "diana", "target": "eve", "value": 5, "relation": "合作"},
            {"source": "eve", "target": "ivy", "value": 4, "relation": "同事"},
            {"source": "frank", "target": "henry", "value": 7, "relation": "上下级"},
            {"source": "frank", "target": "ivy", "value": 6, "relation": "上下级"},
            {"source": "grace", "target": "henry", "value": 5, "relation": "同事"},
            {"source": "grace", "target": "jack", "value": 4, "relation": "朋友"},
            {"source": "henry", "target": "jack", "value": 3, "relation": "同事"},
            {"source": "alice", "target": "jack", "value": 6, "relation": "搭档"},
            {"source": "bob", "target": "frank", "value": 5, "relation": "上下级"},
            {"source": "diana", "target": "ivy", "value": 2, "relation": "合作"}
        ],
        "categories": [
            {"name": "开发组"},
            {"name": "产品组"},
            {"name": "管理组"}
        ]
    }

    # 示例2: 《红楼梦》人物关系网络
    red_mansion = {
        "nodes": [
            {"id": "jia_baoyu", "name": "贾宝玉", "category": 0, "value": 50, "desc": "荣国府贾政之子，贾府核心人物"},
            {"id": "lin_daiyu", "name": "林黛玉", "category": 1, "value": 45, "desc": "贾母外孙女，宝玉表妹"},
            {"id": "xue_baochai", "name": "薛宝钗", "category": 2, "value": 42, "desc": "薛姨妈之女，宝玉表姐"},
            {"id": "wang_xifeng", "name": "王熙凤", "category": 0, "value": 38, "desc": "贾琏之妻，荣国府管家"},
            {"id": "jia_mu", "name": "贾母", "category": 0, "value": 35, "desc": "荣国府太夫人，贾府最高辈分"},
            {"id": "jia_zheng", "name": "贾政", "category": 0, "value": 30, "desc": "贾母之子，宝玉之父"},
            {"id": "wang_furen", "name": "王夫人", "category": 0, "value": 28, "desc": "贾政之妻，宝玉之母"},
            {"id": "xue_yima", "name": "薛姨妈", "category": 2, "value": 22, "desc": "薛宝钗之母，王夫人之姐"},
            {"id": "shi_xiangyun", "name": "史湘云", "category": 1, "value": 25, "desc": "贾母侄孙女，豪爽开朗"},
            {"id": "miaoyu", "name": "妙玉", "category": 3, "value": 20, "desc": "栊翠庵尼姑，出身仕宦"},
            {"id": "jia_tanchun", "name": "贾探春", "category": 0, "value": 24, "desc": "贾政庶女，才干出众"},
            {"id": "jia_yingchun", "name": "贾迎春", "category": 0, "value": 18, "desc": "贾赦之女，温柔懦弱"},
            {"id": "jia_xichun", "name": "贾惜春", "category": 0, "value": 16, "desc": "贾珍之妹，出家为尼"},
            {"id": "qin_keqing", "name": "秦可卿", "category": 0, "value": 20, "desc": "贾蓉之妻，金陵十二钗"},
            {"id": "li_wan", "name": "李纨", "category": 0, "value": 22, "desc": "贾珠之妻，寡居"},
            {"id": "xiren", "name": "袭人", "category": 4, "value": 18, "desc": "宝玉贴身丫鬟"},
            {"id": "qingwen", "name": "晴雯", "category": 4, "value": 16, "desc": "宝玉丫鬟，性格刚烈"},
            {"id": "zijuan", "name": "紫鹃", "category": 4, "value": 15, "desc": "黛玉贴身丫鬟"},
            {"id": "ping_er", "name": "平儿", "category": 4, "value": 17, "desc": "王熙凤贴身丫鬟"},
            {"id": "jia_lian", "name": "贾琏", "category": 0, "value": 26, "desc": "贾赦之子，王熙凤之夫"}
        ],
        "links": [
            {"source": "jia_baoyu", "target": "lin_daiyu", "value": 10, "relation": "知己/恋人"},
            {"source": "jia_baoyu", "target": "xue_baochai", "value": 8, "relation": "夫妻(后)"},
            {"source": "jia_baoyu", "target": "jia_mu", "value": 9, "relation": "祖孙"},
            {"source": "jia_baoyu", "target": "jia_zheng", "value": 6, "relation": "父子"},
            {"source": "jia_baoyu", "target": "wang_furen", "value": 7, "relation": "母子"},
            {"source": "jia_baoyu", "target": "wang_xifeng", "value": 5, "relation": "堂兄嫂"},
            {"source": "jia_baoyu", "target": "shi_xiangyun", "value": 6, "relation": "表亲"},
            {"source": "jia_baoyu", "target": "miaoyu", "value": 3, "relation": "知交"},
            {"source": "jia_baoyu", "target": "xiren", "value": 8, "relation": "主仆"},
            {"source": "jia_baoyu", "target": "qingwen", "value": 7, "relation": "主仆"},
            {"source": "jia_baoyu", "target": "jia_tanchun", "value": 5, "relation": "兄妹"},
            {"source": "jia_baoyu", "target": "jia_yingchun", "value": 3, "relation": "堂兄妹"},
            {"source": "jia_baoyu", "target": "jia_xichun", "value": 3, "relation": "堂兄妹"},
            {"source": "lin_daiyu", "target": "jia_mu", "value": 8, "relation": "外祖孙"},
            {"source": "lin_daiyu", "target": "zijuan", "value": 9, "relation": "主仆"},
            {"source": "lin_daiyu", "target": "xue_baochai", "value": 5, "relation": "姐妹(后和好)"},
            {"source": "lin_daiyu", "target": "shi_xiangyun", "value": 4, "relation": "姐妹"},
            {"source": "xue_baochai", "target": "xue_yima", "value": 9, "relation": "母女"},
            {"source": "xue_baochai", "target": "shi_xiangyun", "value": 5, "relation": "姐妹"},
            {"source": "wang_xifeng", "target": "jia_lian", "value": 7, "relation": "夫妻"},
            {"source": "wang_xifeng", "target": "jia_mu", "value": 8, "relation": "孙媳"},
            {"source": "wang_xifeng", "target": "ping_er", "value": 8, "relation": "主仆"},
            {"source": "wang_xifeng", "target": "qin_keqing", "value": 6, "relation": "好友"},
            {"source": "jia_zheng", "target": "jia_mu", "value": 8, "relation": "母子"},
            {"source": "jia_zheng", "target": "wang_furen", "value": 7, "relation": "夫妻"},
            {"source": "jia_zheng", "target": "jia_tanchun", "value": 5, "relation": "父女"},
            {"source": "wang_furen", "target": "xue_yima", "value": 7, "relation": "姐妹"},
            {"source": "wang_furen", "target": "wang_xifeng", "value": 6, "relation": "婆侄"},
            {"source": "jia_lian", "target": "jia_mu", "value": 5, "relation": "祖孙"},
            {"source": "li_wan", "target": "jia_tanchun", "value": 4, "relation": "嫂叔妹"},
            {"source": "jia_tanchun", "target": "jia_yingchun", "value": 4, "relation": "姐妹"},
            {"source": "jia_tanchun", "target": "jia_xichun", "value": 4, "relation": "姐妹"},
            {"source": "jia_yingchun", "target": "jia_xichun", "value": 3, "relation": "姐妹"}
        ],
        "categories": [
            {"name": "贾府"},
            {"name": "林家"},
            {"name": "薛家"},
            {"name": "方外"},
            {"name": "丫鬟"}
        ]
    }

    # 示例3: 公司组织架构网络
    company_network = {
        "nodes": [
            {"id": "ceo", "name": "张总(CEO)", "category": 0, "value": 50, "desc": "首席执行官"},
            {"id": "cto", "name": "李工(CTO)", "category": 1, "value": 40, "desc": "首席技术官"},
            {"id": "cfo", "name": "王财(CFO)", "category": 2, "value": 38, "desc": "首席财务官"},
            {"id": "coo", "name": "赵运(COO)", "category": 3, "value": 36, "desc": "首席运营官"},
            {"id": "dev_lead", "name": "陈开发(开发主管)", "category": 1, "value": 30, "desc": "开发团队负责人"},
            {"id": "qa_lead", "name": "周测试(测试主管)", "category": 1, "value": 28, "desc": "测试团队负责人"},
            {"id": "fe_dev1", "name": "前端-小明", "category": 1, "value": 20, "desc": "前端开发工程师"},
            {"id": "fe_dev2", "name": "前端-小红", "category": 1, "value": 20, "desc": "前端开发工程师"},
            {"id": "be_dev1", "name": "后端-小刚", "category": 1, "value": 22, "desc": "后端开发工程师"},
            {"id": "be_dev2", "name": "后端-小丽", "category": 1, "value": 22, "desc": "后端开发工程师"},
            {"id": "qa1", "name": "测试-小华", "category": 1, "value": 18, "desc": "测试工程师"},
            {"id": "fin1", "name": "财务-小芳", "category": 2, "value": 20, "desc": "财务专员"},
            {"id": "fin2", "name": "财务-小伟", "category": 2, "value": 20, "desc": "财务专员"},
            {"id": "ops1", "name": "运营-小强", "category": 3, "value": 22, "desc": "运营专员"},
            {"id": "ops2", "name": "运营-小燕", "category": 3, "value": 22, "desc": "运营专员"},
            {"id": "hr", "name": "人事-小梅", "category": 3, "value": 24, "desc": "人事经理"}
        ],
        "links": [
            {"source": "ceo", "target": "cto", "value": 10, "relation": "管理"},
            {"source": "ceo", "target": "cfo", "value": 10, "relation": "管理"},
            {"source": "ceo", "target": "coo", "value": 10, "relation": "管理"},
            {"source": "cto", "target": "dev_lead", "value": 8, "relation": "管理"},
            {"source": "cto", "target": "qa_lead", "value": 8, "relation": "管理"},
            {"source": "dev_lead", "target": "fe_dev1", "value": 6, "relation": "管理"},
            {"source": "dev_lead", "target": "fe_dev2", "value": 6, "relation": "管理"},
            {"source": "dev_lead", "target": "be_dev1", "value": 6, "relation": "管理"},
            {"source": "dev_lead", "target": "be_dev2", "value": 6, "relation": "管理"},
            {"source": "qa_lead", "target": "qa1", "value": 6, "relation": "管理"},
            {"source": "cfo", "target": "fin1", "value": 7, "relation": "管理"},
            {"source": "cfo", "target": "fin2", "value": 7, "relation": "管理"},
            {"source": "coo", "target": "ops1", "value": 7, "relation": "管理"},
            {"source": "coo", "target": "ops2", "value": 7, "relation": "管理"},
            {"source": "coo", "target": "hr", "value": 7, "relation": "管理"},
            {"source": "fe_dev1", "target": "fe_dev2", "value": 5, "relation": "协作"},
            {"source": "be_dev1", "target": "be_dev2", "value": 5, "relation": "协作"},
            {"source": "fe_dev1", "target": "be_dev1", "value": 4, "relation": "协作"},
            {"source": "fe_dev2", "target": "be_dev2", "value": 4, "relation": "协作"},
            {"source": "qa1", "target": "fe_dev1", "value": 3, "relation": "协作"},
            {"source": "qa1", "target": "be_dev1", "value": 3, "relation": "协作"},
            {"source": "ops1", "target": "ops2", "value": 5, "relation": "协作"},
            {"source": "fin1", "target": "fin2", "value": 5, "relation": "协作"}
        ],
        "categories": [
            {"name": "高管"},
            {"name": "技术部"},
            {"name": "财务部"},
            {"name": "运营部"}
        ]
    }

    # 示例4: 学术引用网络
    academic_network = {
        "nodes": [
            {"id": "paper1", "name": "深度学习综述", "category": 0, "value": 45, "desc": "2015年发表，被引次数极高"},
            {"id": "paper2", "name": "卷积神经网络", "category": 0, "value": 40, "desc": "图像识别奠基之作"},
            {"id": "paper3", "name": "循环神经网络", "category": 0, "value": 35, "desc": "序列建模经典论文"},
            {"id": "paper4", "name": "Transformer架构", "category": 1, "value": 50, "desc": "注意力机制革新"},
            {"id": "paper5", "name": "BERT模型", "category": 1, "value": 42, "desc": "预训练语言模型"},
            {"id": "paper6", "name": "GPT系列", "category": 1, "value": 48, "desc": "生成式预训练"},
            {"id": "paper7", "name": "图神经网络", "category": 2, "value": 30, "desc": "图结构学习"},
            {"id": "paper8", "name": "知识图谱嵌入", "category": 2, "value": 28, "desc": "知识表示学习"},
            {"id": "paper9", "name": "强化学习", "category": 3, "value": 32, "desc": "决策优化"},
            {"id": "paper10", "name": "GAN生成模型", "category": 3, "value": 38, "desc": "生成对抗网络"},
            {"id": "paper11", "name": "注意力机制", "category": 1, "value": 36, "desc": "Attention基础"},
            {"id": "paper12", "name": "ResNet残差网络", "category": 0, "value": 40, "desc": "深层网络训练"}
        ],
        "links": [
            {"source": "paper1", "target": "paper2", "value": 8, "relation": "引用"},
            {"source": "paper1", "target": "paper3", "value": 7, "relation": "引用"},
            {"source": "paper4", "target": "paper11", "value": 9, "relation": "引用"},
            {"source": "paper4", "target": "paper3", "value": 6, "relation": "引用"},
            {"source": "paper5", "target": "paper4", "value": 10, "relation": "引用"},
            {"source": "paper5", "target": "paper1", "value": 5, "relation": "引用"},
            {"source": "paper6", "target": "paper4", "value": 10, "relation": "引用"},
            {"source": "paper6", "target": "paper5", "value": 8, "relation": "引用"},
            {"source": "paper7", "target": "paper1", "value": 6, "relation": "引用"},
            {"source": "paper7", "target": "paper2", "value": 5, "relation": "引用"},
            {"source": "paper8", "target": "paper7", "value": 7, "relation": "引用"},
            {"source": "paper8", "target": "paper1", "value": 4, "relation": "引用"},
            {"source": "paper9", "target": "paper1", "value": 5, "relation": "引用"},
            {"source": "paper10", "target": "paper1", "value": 7, "relation": "引用"},
            {"source": "paper10", "target": "paper2", "value": 6, "relation": "引用"},
            {"source": "paper11", "target": "paper3", "value": 8, "relation": "引用"},
            {"source": "paper12", "target": "paper2", "value": 9, "relation": "引用"},
            {"source": "paper12", "target": "paper1", "value": 7, "relation": "引用"},
            {"source": "paper5", "target": "paper11", "value": 8, "relation": "引用"},
            {"source": "paper6", "target": "paper11", "value": 7, "relation": "引用"}
        ],
        "categories": [
            {"name": "深度学习基础"},
            {"name": "NLP方向"},
            {"name": "图学习方向"},
            {"name": "其他方向"}
        ]
    }

    datasets = [
        ("小型社交网络", "10个节点18条边的社交关系网络，展示一个小团队的人际交往", "social", json.dumps(social_small, ensure_ascii=False)),
        ("红楼梦人物关系", "20个节点34条边的红楼梦主要人物关系网络", "literature", json.dumps(red_mansion, ensure_ascii=False)),
        ("公司组织架构", "16个节点23条边的公司内部组织架构与协作关系", "organization", json.dumps(company_network, ensure_ascii=False)),
        ("学术引用网络", "12个节点20条边的AI领域学术论文引用关系", "academic", json.dumps(academic_network, ensure_ascii=False)),
    ]
    from pathlib import Path
    ev_graph_path = Path(__file__).resolve().parents[2] / "data" / "processed" / "public_ev_battery_network.json"
    if ev_graph_path.exists():
        ev_graph = json.loads(ev_graph_path.read_text(encoding="utf-8"))
        datasets.append(("新能源汽车电池健康与充电风险关系网络", ev_graph["description"], "ev_battery", json.dumps(ev_graph, ensure_ascii=False)))

    cursor.executemany(
        "INSERT INTO sample_datasets (name, description, category, graph_data) VALUES (?, ?, ?, ?)",
        datasets
    )
    conn.commit()
