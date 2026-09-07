import jieba
import jieba.posseg as pseg
import re
from collections import defaultdict


class TextRelationExtractor:
    """从文本中提取人物关系图谱"""

    # 常见关系词
    RELATION_KEYWORDS = {
        '父亲': '父子', '母亲': '母子', '儿子': '父子', '女儿': '父女',
        '丈夫': '夫妻', '妻子': '夫妻', '哥哥': '兄弟', '弟弟': '兄弟',
        '姐姐': '姐妹', '妹妹': '姐妹', '朋友': '朋友', '同事': '同事',
        '老师': '师生', '学生': '师生', '师父': '师徒', '徒弟': '师徒',
        '上司': '上下级', '下属': '上下级', '老板': '上下级', '员工': '上下级',
        '恋人': '恋人', '爱人': '夫妻', '同学': '同学', '邻居': '邻居',
        '对手': '对手', '敌人': '敌对', '盟友': '同盟', '合作': '合作',
        '喜欢': '好感', '讨厌': '厌恶', '帮助': '帮助', '杀': '敌对',
        '救': '帮助', '打': '冲突', '骂': '冲突', '爱': '好感',
        '恨': '敌对', '嫁': '夫妻', '娶': '夫妻',
    }

    # 停用人名（常见非人名的词）
    STOP_NAMES = {
        '什么', '怎么', '这个', '那个', '一个', '自己', '大家', '我们',
        '他们', '你们', '谁', '有人', '别人', '人家', '先生', '小姐',
        '同志', '老师', '学生', '我', '你', '他', '她', '它',
    }

    def __init__(self):
        pass

    def extract_relations(self, text, window_size=5, min_co_occurrence=1):
        """
        从文本中提取人物关系
        Args:
            text: 输入文本
            window_size: 共现窗口大小（句子数）
            min_co_occurrence: 最小共现次数
        Returns:
            dict: 包含 nodes 和 links 的图数据
        """
        # 1. 分句
        sentences = self._split_sentences(text)

        # 2. 提取人名
        name_freq = defaultdict(int)
        sentence_names = []
        for sentence in sentences:
            names = self._extract_names(sentence)
            sentence_names.append(names)
            for name in names:
                name_freq[name] += 1

        # 过滤低频人名（至少出现1次）
        valid_names = {name for name, freq in name_freq.items() if freq >= 1}

        # 3. 统计共现关系
        co_occurrence = defaultdict(int)
        relation_labels = defaultdict(lambda: defaultdict(int))

        for i, names_i in enumerate(sentence_names):
            # 在窗口内查找共现
            window_names = set()
            for j in range(max(0, i - window_size), min(len(sentence_names), i + window_size + 1)):
                for name in sentence_names[j]:
                    if name in valid_names:
                        window_names.add(name)

            names_list = [n for n in names_i if n in valid_names]

            for a in names_list:
                for b in window_names:
                    if a != b:
                        key = tuple(sorted([a, b]))
                        co_occurrence[key] += 1

            # 提取关系词
            sentence_text = sentences[i]
            for name_a in names_list:
                for name_b in names_list:
                    if name_a != name_b:
                        rel = self._find_relation(sentence_text, name_a, name_b)
                        if rel:
                            key = tuple(sorted([name_a, name_b]))
                            relation_labels[key][rel] += 1

        # 4. 构建图数据
        # 社区发现（简单基于共现聚类）
        communities = self._simple_community_detection(valid_names, co_occurrence)

        nodes = []
        name_to_idx = {}
        for idx, name in enumerate(sorted(valid_names, key=lambda x: name_freq[x], reverse=True)):
            name_to_idx[name] = idx
            nodes.append({
                "id": f"person_{idx}",
                "name": name,
                "category": communities.get(name, 0),
                "value": name_freq[name],
                "desc": f"出现次数: {name_freq[name]}"
            })

        links = []
        for (a, b), count in co_occurrence.items():
            if count >= min_co_occurrence and a in name_to_idx and b in name_to_idx:
                # 获取最常见的关系标签
                key = tuple(sorted([a, b]))
                rel = "共现"
                if key in relation_labels and relation_labels[key]:
                    rel = max(relation_labels[key], key=relation_labels[key].get)

                links.append({
                    "source": f"person_{name_to_idx[a]}",
                    "target": f"person_{name_to_idx[b]}",
                    "value": min(count, 10),
                    "relation": rel
                })

        # 生成分类
        max_cat = max(communities.values()) + 1 if communities else 1
        categories = [{"name": f"群组{i + 1}"} for i in range(max_cat)]

        return {
            "nodes": nodes,
            "links": links,
            "categories": categories
        }

    def _split_sentences(self, text):
        """将文本分割为句子"""
        # 按标点分句
        sentences = re.split(r'[。！？；\n.!?;]', text)
        return [s.strip() for s in sentences if s.strip()]

    def _extract_names(self, sentence):
        """从句子中提取人名"""
        names = set()
        words = pseg.cut(sentence)
        for word, flag in words:
            if flag == 'nr' and len(word) >= 2 and word not in self.STOP_NAMES:
                names.add(word)
        return list(names)

    def _find_relation(self, sentence, name_a, name_b):
        """在句子中查找两个人名之间的关系"""
        pos_a = sentence.find(name_a)
        pos_b = sentence.find(name_b)
        if pos_a == -1 or pos_b == -1:
            return None

        start = min(pos_a, pos_b)
        end = max(pos_a + len(name_a), pos_b + len(name_b))
        between = sentence[start:end]

        for keyword, relation in self.RELATION_KEYWORDS.items():
            if keyword in between:
                return relation

        return None

    def _simple_community_detection(self, names, co_occurrence):
        """简单的社区发现算法（基于连通分量）"""
        if not names:
            return {}

        # 构建邻接表
        adj = defaultdict(set)
        for (a, b), count in co_occurrence.items():
            if count >= 1:
                adj[a].add(b)
                adj[b].add(a)

        # BFS找连通分量
        visited = set()
        communities = {}
        community_id = 0

        for name in sorted(names):
            if name not in visited:
                queue = [name]
                visited.add(name)
                component = []
                while queue:
                    current = queue.pop(0)
                    component.append(current)
                    for neighbor in adj[current]:
                        if neighbor not in visited and neighbor in names:
                            visited.add(neighbor)
                            queue.append(neighbor)
                for n in component:
                    communities[n] = community_id
                community_id += 1

        # 对于没有任何共现的孤立节点
        for name in names:
            if name not in communities:
                communities[name] = community_id
                community_id += 1

        return communities


# 全局实例
extractor = TextRelationExtractor()


def process_text(text, window_size=5, min_co_occurrence=1):
    """处理文本，提取人物关系图谱"""
    return extractor.extract_relations(text, window_size, min_co_occurrence)
