# EEQS-RAG AI 智能问答 API 文档（前端用）

> 基础地址：`http://<host>:8000`
> 认证：HTTP Basic Auth 或 Django Session（与既有 API 一致）。未认证返回 `401`。
> 能力范围：自然语言查询站点/气象观测/水文预测数据（Text2SQL）。

## 1. 发起问答（SSE 流式）

`POST /api/ai/chat/`

请求体：

```json
{ "message": "HXC 站 2026 年 6 月的日均温度是多少？", "session_id": "可选，已有会话的 UUID" }
```

- 不传 `session_id` 则新建会话，会话标题自动取首条消息前 50 字。
- `message` 最长 2000 字，超长或为空返回 `400`。

响应：`Content-Type: text/event-stream`，逐帧推送，每帧格式：

```
data: {"type": "...", ...}

```

事件类型（按出现顺序）：

| type | 字段 | 含义 |
|---|---|---|
| `meta` | `session_id`, `title` | 第一帧，前端据此记录会话 ID（后续轮次带上） |
| `tool_start` | `tool` | AI 正在调用工具（如 `query_database`），可展示「正在查询数据库…」 |
| `tool_end` | `tool`, `preview` | 工具返回（preview 为结果前 200 字预览） |
| `token` | `content` | AI 回答的流式文本片段，逐帧追加渲染即可 |
| `final` | `content` | 最后一帧，完整回答全文（token 帧的拼接结果） |
| `error` | `message` | 出错（LLM 不可用等），此时不会有 final 帧 |

前端接收示例（浏览器原生 `fetch` + ReadableStream，EventSource 不支持 POST）：

```js
const resp = await fetch("/api/ai/chat/", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  credentials: "include",
  body: JSON.stringify({ message, session_id }),
});
const reader = resp.body.getReader();
const decoder = new TextDecoder();
let buffer = "";
while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  buffer += decoder.decode(value, { stream: true });
  const frames = buffer.split("\n\n");
  buffer = frames.pop();          // 末段可能不完整，留到下一轮
  for (const frame of frames) {
    if (!frame.startsWith("data: ")) continue;
    const event = JSON.parse(frame.slice(6));
    if (event.type === "token") appendToBubble(event.content);
    if (event.type === "final") finalizeBubble(event.content);
    if (event.type === "error") showError(event.message);
  }
}
```

## 2. 会话列表

`GET /api/ai/sessions/`

```json
[{ "id": "uuid", "title": "HXC 站最近温度如何？", "created_at": "...", "updated_at": "..." }]
```

## 3. 会话消息历史

`GET /api/ai/sessions/<id>/`

```json
{
  "id": "uuid",
  "title": "...",
  "messages": [
    { "id": 1, "role": "user", "content": "...", "created_at": "..." },
    { "id": 2, "role": "assistant", "content": "...", "created_at": "..." }
  ]
}
```

只能看到本人的会话，访问他人会话返回 `404`。

## 错误码

| 状态码 | 场景 |
|---|---|
| `200` | 成功（chat 为 SSE 流） |
| `400` | message 为空或超长 |
| `401` | 未认证 |
| `404` | 会话不存在或不属于当前用户 |

## 备注（与后端架构相关）

- 会话记忆保存在后端进程内存（LangGraph InMemorySaver），**服务重启后 AI 不再记得历史上下文**（但消息记录在数据库里，界面历史不受影响）。生产如需持久记忆，后续版本切换 PostgresSaver。
- 每次 Text2SQL 查询都会写审计日志（Admin 后台「AI 智能问答 → Ai audit logs」只读可查）。
