# 06 · RAG 知识库构建

> 目标：把 EEQS 的数据字典、操作手册、指标说明、历史报告等文档变成智能体可检索的知识库，回答时**有依据、带引用、不编造**。

---

## 1. 全流程一张图

```
离线（建库，文档更新时重跑）:
  文档(PDF/Word/MD/网页) → 解析 → 清洗 → 切块 → Embedding → 向量库
                                              ↘ 元数据(来源/章节/权限标签) ↗

在线（问答时）:
  用户问题 → (可选)改写 → 混合检索(向量+关键词) → Rerank → top-k 片段
  → 套上不可信标记(05篇) → 进 prompt → LLM 生成带引用的回答
```

## 2. 建库流水线（pgvector 方案）

```bash
# 数据库启用向量扩展
psql -U postgres -d eeqs -c "CREATE EXTENSION IF NOT EXISTS vector;"
uv add pgvector sentence-transformers langchain-text-splitters pypdf python-docx
```

```sql
CREATE TABLE kb_chunks (
    id          bigserial PRIMARY KEY,
    doc_id      varchar NOT NULL,          -- 来源文档
    title       varchar,                   -- 文档标题
    section     varchar,                   -- 章节
    acl_role    varchar DEFAULT 'viewer',  -- 权限标签：检索时按角色过滤（LLM08）
    content     text NOT NULL,
    embedding   vector(1024)               -- BGE-M3 维度
);
CREATE INDEX ON kb_chunks USING hnsw (embedding vector_cosine_ops);
CREATE INDEX ON kb_chunks (acl_role);
-- 关键词检索（中文建议配合 pg_trgm 或 zhparser 分词扩展）
```

```python
# app/kb/ingest.py
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter

emb_model = SentenceTransformer("BAAI/bge-m3")   # 首次运行自动下载 ~2GB

splitter = RecursiveCharacterTextSplitter(
    chunk_size=400,        # 中文 300~500 字是经验甜区
    chunk_overlap=80,      # 重叠防语义被切断
    separators=["\n\n", "\n", "。", "；", "，"],
)

def ingest_document(doc_id: str, title: str, text: str, acl_role="viewer"):
    chunks = splitter.split_text(text)
    vectors = emb_model.encode(chunks, normalize_embeddings=True)
    with engine.connect() as conn:
        for chunk, vec in zip(chunks, vectors):
            conn.execute(text(
                "INSERT INTO kb_chunks(doc_id,title,content,embedding,acl_role) "
                "VALUES (:d,:t,:c,:v,:r)"),
                {"d": doc_id, "t": title, "c": chunk, "v": vec.tolist(), "r": acl_role})
        conn.commit()
```

**切块（chunking）是 RAG 效果的第一杠杆**，注意：
- 按语义边界切（标题、段落），别按固定字符硬切；Markdown 文档用 `MarkdownHeaderTextSplitter` 保留章节路径。
- 表格单独处理：转成 Markdown 表格文本整体成块，别把一行切两半。
- 每个 chunk 存上 `title + section`，检索结果才能给出"出自《XX手册》第 3 章"的引用。

## 3. 检索工具（混合检索 + 权限过滤）

```python
# app/tools/rag_tool.py
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig

@tool
def search_knowledge(query: str, config: RunnableConfig) -> str:
    """检索 EEQS 平台知识库（数据字典、指标说明、操作手册等）。
    输入：检索关键词或问题。返回：相关文档片段及出处。"""
    roles = (config.get("metadata") or {}).get("roles", ["viewer"])
    qvec = emb_model.encode(query, normalize_embeddings=True).tolist()

    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT title, section, content,
                   1 - (embedding <=> :qvec) AS score
            FROM kb_chunks
            WHERE acl_role = ANY(:roles)              -- 权限过滤（LLM08）
            ORDER BY embedding <=> :qvec
            LIMIT 8
        """), {"qvec": qvec, "roles": roles}).fetchall()

    if not rows or rows[0].score < 0.45:     # 相似度阈值：宁可说不知道
        return "知识库中未找到相关内容。"

    parts = [f"【来源：{r.title} · {r.section or '全文'}】\n{r.content}" for r in rows]
    return wrap_untrusted("\n\n---\n\n".join(parts))   # 05 篇的不可信标记
```

**效果升级路线**（按投入产出排序）：
1. **混合检索**：向量召回 + 关键词召回（BM25/trigram）各取 top-N 合并去重——专有名词、指标代码（如"NH3N"）靠关键词，语义问法靠向量。
2. **查询改写**：多轮对话中"它上个月怎么样？"这种指代问题，先让模型结合历史改写成完整查询再检索。
3. **Rerank**：召回 top-20 后用 bge-reranker-v2-m3 精排取 top-5，准确率显著提升，延迟 +100ms 左右。
4. **相似度阈值 + 拒答**：检索不到就明说，让模型回答"知识库暂无相关内容"而不是硬编——这是治幻觉的关键一票。

## 4. 回答生成：强制引用

在 system prompt 中加：
```
- 使用知识库内容回答时，必须在句末标注来源，格式：（来源：《文档名》章节名）。
- 检索结果不足以回答时，明确说"知识库中未找到"，禁止凭模型记忆编造平台专有信息。
```
前端可把引用渲染成可点击的出处卡片（08 篇）。

## 5. 入库治理（防 LLM04 数据投毒）

- 知识库**不是垃圾桶**：入库走"提交→审核→发布"流程，哪怕只是记录在 Excel 里的双人确认。
- 每篇文档记录来源、更新时间、负责人；定期清理过期文档（旧版指标限值之类最易误导）。
- 入库前跑一遍注入特征扫描（复用 05 篇 `check_input`），把"毒文档"拦在库外。

## 6. 评估：RAG 不是写完就完

用 **RAGAS** 框架或自建评测集（30~50 个"问题+标准答案+应引用的文档"）：
```
uv add ragas datasets
```
关注三个指标：
| 指标 | 含义 | 目标 |
|---|---|---|
| Context Recall | 该检到的检到了吗 | > 0.85 |
| Faithfulness | 回答是否忠于检索内容（不编） | > 0.9 |
| Answer Relevancy | 回答是否切题 | > 0.85 |

每次改 chunk 策略/换 embedding 模型/调 top-k 后重跑对比——RAG 优化是实验科学，没有评测集就是闭眼调参。

## 7. 常见坑

1. **把整篇文档塞进一个 chunk** —— 检索噪声巨大，回答质量崩。
2. **embedding 模型中英文错配** —— 中文业务用 OpenAI ada-002 效果差，BGE-M3 / 通义 embedding 明显更好。
3. **只做向量检索** —— 查"PM2.5 限值"里的"PM2.5"这种精确 token，向量可能漏，必须混合检索。
4. **知识库和业务数据混用** —— "最新监测值"应该走 Text2SQL 查库（04 篇），不该指望知识库；在 system prompt 里讲清两者的分工。
5. **忽视权限标签** —— 内部手册被普通用户检索出来引用，就是信息泄露事故。

---

## ✅ 本篇动手清单
- [ ] 选 5 篇真实文档（数据字典 + 操作手册）跑通入库流水线
- [ ] 用 10 个问题测试纯向量检索，记录 badcase
- [ ] 加上关键词混合检索和阈值拒答，对比 badcase 是否减少
- [ ] 建 30 题评测集，跑一次 RAGAS 得到基线分数
