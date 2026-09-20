<template>
  <div class="ai-assistant-container">
    <!--
      ============================================
      头部区域
      ============================================
      设计说明:
      - 采用 Element UI 渐变头部风格，与项目整体视觉统一
      - 显示 AI 助手名称、在线状态、操作按钮
      - 状态指示灯使用 CSS 动画表示服务在线
    -->
    <div class="chat-header">
      <div class="header-left">
        <el-avatar :size="42" icon="el-icon-chat-dot-round" class="ai-avatar" />
        <div class="header-info">
          <div class="header-title">智能问答助手</div>
          <div class="header-subtitle">
            <span class="status-dot" />
            {{ apiStatus === 'connected' ? '服务在线' : '服务离线' }} · {{ llmModelName }}
          </div>
        </div>
      </div>
      <div class="header-actions">
        <el-button
          type="text"
          icon="el-icon-delete"
          class="clear-btn"
          @click="handleClearChat"
        >
          清空对话
        </el-button>
      </div>
    </div>

    <!--
      ============================================
      消息展示区域
      ============================================
      设计说明:
      - 使用 Element UI 的 el-scrollbar 组件实现平滑滚动
      - 支持自动滚动到最新消息
      - 消息列表为空时显示欢迎面板，引导用户使用
    -->
    <el-scrollbar ref="messageScrollbar" class="chat-messages" wrap-class="messages-wrapper">
      <!-- 欢迎面板：首次进入时展示 -->
      <div v-if="messageList.length === 0" class="welcome-panel">
        <div class="welcome-content">
          <el-avatar :size="80" icon="el-icon-chat-dot-round" class="welcome-avatar" />
          <h2 class="welcome-title">你好！我是你的智能助手</h2>
          <p class="welcome-desc">
            基于大语言模型技术，可以帮你解答水文气象、积雪动态、
            水资源预报等专业问题，也可以编写代码、分析数据
          </p>
          <div class="suggestion-list">
            <el-tag
              v-for="(item, index) in suggestionList"
              :key="index"
              class="suggestion-tag"
              effect="plain"
              @click="sendQuickMessage(item)"
            >
              {{ item }}
            </el-tag>
          </div>
        </div>
      </div>

      <!-- 消息列表：展示用户和助手的对话 -->
      <div v-else class="message-list">
        <div
          v-for="(msg, index) in messageList"
          :key="index"
          :class="['message-item', msg.role]"
        >
          <!-- 用户/助手头像 -->
          <el-avatar
            :size="36"
            :icon="msg.role === 'user' ? 'el-icon-user' : 'el-icon-chat-dot-round'"
            :class="['message-avatar', msg.role]"
          />

          <!-- 消息内容区 -->
          <div class="message-body">
            <div class="message-bubble" v-html="formatMessage(msg.content)" />
            <div class="message-meta">
              <span class="message-time">{{ msg.time }}</span>
              <el-button
                v-if="msg.role === 'assistant'"
                type="text"
                size="mini"
                class="copy-btn"
                @click="copyMessage(msg.content)"
              >
                <i class="el-icon-document-copy" /> 复制
              </el-button>
            </div>
          </div>
        </div>

        <!-- 加载中指示器：等待后端响应时显示 -->
        <div v-if="isLoading" class="message-item assistant">
          <el-avatar :size="36" icon="el-icon-chat-dot-round" class="message-avatar assistant" />
          <div class="message-body">
            <div class="typing-indicator">
              <span /><span /><span />
            </div>
          </div>
        </div>
      </div>
    </el-scrollbar>

    <!--
      ============================================
      输入区域
      ============================================
      设计说明:
      - 使用 Element UI el-input textarea 组件
      - 支持自动增高（maxRows=5）
      - Enter 发送，Shift+Enter 换行
      - 发送按钮带禁用状态和加载状态
    -->
    <div class="chat-input-area">
      <el-input
        v-model="inputMessage"
        type="textarea"
        :rows="1"
        :autosize="{ minRows: 1, maxRows: 5 }"
        placeholder="输入你的问题，按 Enter 发送，Shift+Enter 换行..."
        class="chat-input"
        resize="none"
        @keydown.native="handleKeyDown"
      />
      <el-button
        type="primary"
        :disabled="!inputMessage.trim() || isLoading"
        :loading="isLoading"
        class="send-btn"
        @click="sendMessage"
      >
        <i class="el-icon-s-promotion" />
      </el-button>
    </div>
  </div>
</template>

<script>
/**
 * ==============================================================================
 * 智能问答助手组件 - API 需求说明文档
 * ==============================================================================
 *
 * 【设计背景】
 * 本组件实现一个类似 ChatGPT 的智能对话界面，核心需求是：
 * 1. 用户输入问题 → 前端发送到后端 → 后端调用 LLM 生成回答 → 前端展示
 * 2. 支持流式输出（SSE），实现"打字机"效果，提升用户体验
 * 3. 支持 Markdown 格式渲染（代码块、表格、列表等）
 * 4. 保持对话上下文，让 LLM 理解前文
 *
 * 【为什么用 SSE 而不是 WebSocket？】
 * - SSE（Server-Sent Events）：
 *   ✓ 单向通信（服务端→客户端），完全符合 LLM 生成场景
 *   ✓ 基于 HTTP，无需额外协议，穿透防火墙更容易
 *   ✓ 自动重连机制，断线恢复简单
 *   ✓ 大多数 LLM API（OpenAI、Claude、通义千问）原生支持流式 HTTP 响应
 *   ✗ 单向通信，如果需要心跳检测需要额外处理
 *
 * - WebSocket：
 *   ✓ 双向通信，适合实时互动场景
 *   ✗ LLM 生成是服务端单向推送，双向能力浪费
 *   ✗ 需要额外维护连接状态、心跳、重连逻辑
 *   ✗ 部分企业内网对 WebSocket 有限制
 *
 * 结论：LLM 流式输出场景下，SSE 是更轻量、更自然的选择
 *
 * 【为什么用 Fetch API 而不是 Axios？】
 * - Axios 不支持直接读取 response.body.getReader() 进行流式消费
 * - Fetch API 的 ReadableStream 是实现 SSE 流式输出的标准方式
 * - 但项目中已有 Axios 封装（request.js），非流式接口仍可使用
 * - 本组件中：流式接口用原生 Fetch，非流式接口可用 Axios
 *
 * ==============================================================================
 * 后端需要提供的服务 API（共 4 个）
 * ==============================================================================
 */

/**
 * API 1: POST /api/ai/chat
 * 功能：发送聊天消息，获取 LLM 回复
 * 支持模式：SSE 流式输出（默认）/ 普通 JSON 响应
 *
 * 请求体（JSON）：
 * {
 *   "message": "用户的提问内容",
 *   "history": [                    // 可选，对话历史记录
 *     { "role": "user", "content": "之前的问题" },
 *     { "role": "assistant", "content": "之前的回答" }
 *   ],
 *   "stream": true                  // 可选，是否启用流式输出
 * }
 *
 * 响应模式 A - SSE 流式（stream=true）：
 * Content-Type: text/event-stream
 * Cache-Control: no-cache
 *
 * data: {"content": "这是"}
 * data: {"content": "第一段"}
 * data: {"content": "回复内容"}
 * data: [DONE]                     // 结束标记
 *
 * 响应模式 B - 普通 JSON（stream=false）：
 * HTTP/1.1 200 OK
 * Content-Type: application/json
 *
 * {
 *   "code": 200,
 *   "data": {
 *     "content": "完整的回复内容",
 *     "timestamp": "2024-01-15T10:30:00Z"
 *   }
 * }
 *
 * 错误响应：
 * {
 *   "code": 500,
 *   "msg": "LLM 服务调用失败: timeout"
 * }
 *
 * 【为什么这样设计？】
 * - message: 必须字段，当前用户输入
 * - history: 可选字段，让后端可以构建完整的对话上下文传递给 LLM
 *   大多数 LLM API（OpenAI/Claude/通义千问）都需要 messages 数组格式
 * - stream: 控制输出模式，前端开发调试时可关闭流式直接看完整结果
 * - SSE 格式 data: {...} 是标准 SSE 协议，[DONE] 是 OpenAI 风格的结束标记
 */

/**
 * API 2: GET /api/ai/config
 * 功能：获取 AI 助手配置信息（页面加载时调用）
 *
 * 响应：
 * {
 *   "code": 200,
 *   "data": {
 *     "model": "qwen-turbo",           // 当前使用的模型名称
 *     "modelDisplay": "通义千问 Turbo", // 模型显示名称
 *     "streaming": true,               // 是否支持流式输出
 *     "maxHistory": 20,                // 最大历史记录条数
 *     "features": ["markdown", "code_highlight", "tables"],
 *     "systemPrompt": "你是水文气象专家..."  // 系统提示词（可选）
 *   }
 * }
 *
 * 【为什么这样设计？】
 * - 前端需要知道后端配置了哪种模型，用于显示在界面上
 * - maxHistory 可以让前端控制发送到后端的历史长度，避免 Token 超限
 * - 系统提示词可以让后端统一管理 LLM 的 behavior，前端无需关心
 */

/**
 * API 3: GET /api/ai/history?page=1&page_size=20
 * 功能：获取历史对话记录（分页查询）
 *
 * 响应：
 * {
 *   "code": 200,
 *   "data": {
 *     "list": [
 *       {
 *         "id": "uuid",
 *         "title": "关于积雪融化的讨论",
 *         "lastMessage": "积雪融化受哪些因素影响？",
 *         "messageCount": 12,
 *         "createdAt": "2024-01-15T09:00:00Z",
 *         "updatedAt": "2024-01-15T10:30:00Z"
 *       }
 *     ],
 *     "total": 100,
 *     "page": 1,
 *     "page_size": 20
 *   }
 * }
 *
 * 【为什么这样设计？】
 * - 支持会话列表管理（类似 ChatGPT 的左侧历史列表）
 * - 分页查询避免一次性加载大量数据
 * - 每个会话包含摘要信息，方便用户快速定位
 * - 当前版本为简化版，未实现会话切换功能，但 API 预留了扩展空间
 */

/**
 * API 4: POST /api/ai/save
 * 功能：保存当前对话记录
 *
 * 请求体：
 * {
 *   "sessionId": "uuid",              // 可选，新会话留空
 *   "messages": [
 *     { "role": "user", "content": "..." },
 *     { "role": "assistant", "content": "..." }
 *   ],
 *   "title": "自动生成的标题"          // 可选
 * }
 *
 * 响应：
 * {
 *   "code": 200,
 *   "data": {
 *     "sessionId": "uuid"
 *   }
 * }
 *
 * 【为什么这样设计？】
 * - 当前版本对话存储在前端内存中，刷新页面会丢失
 * - 后端需要持久化存储，支持用户跨会话查看历史
 * - 可以扩展为自动保存（每次对话结束后自动调用）
 * - title 可以让后端用 LLM 自动生成会话标题（"用一句话总结这段对话"）
 */

/**
 * ==============================================================================
 * LLM 流式输出数据处理说明
 * ==============================================================================
 *
 * 不同 LLM 提供商的流式输出格式：
 *
 * 【OpenAI】
 * 格式: data: {"choices":[{"delta":{"content":"文字"}}]}
 * 结束: data: [DONE]
 *
 * 【通义千问（DashScope）】
 * 格式: data: {"output":{"choices":[{"message":{"content":"文字"}}]}}
 * 结束: 连接关闭
 *
 * 【Claude（Anthropic）】
 * 格式: data: {"type":"content_block_delta","delta":{"text":"文字"}}
 * 结束: data: {"type":"message_stop"}
 *
 * 【通用适配策略】
 * 后端应统一封装，无论调用哪种 LLM，对外都输出统一格式：
 *   data: {"content": "文字片段"}
 *   data: [DONE]
 * 这样前端无需关心底层 LLM 的差异
 */

import Cookies from 'js-cookie'

export default {
  name: 'AiAssistant',

  data() {
    return {
      // 用户输入框内容
      inputMessage: '',

      // 是否正在等待后端响应
      isLoading: false,

      // API 连接状态: 'connected' | 'disconnected' | 'connecting'
      apiStatus: 'connecting',

      // 当前使用的 LLM 模型显示名称
      llmModelName: '加载中...',

      // 对话消息列表
      // 结构: { role: 'user'|'assistant', content: '消息内容', time: '10:30' }
      messageList: [],

      // 当前会话 ID（首轮问答后由后端 meta 事件下发，用于多轮记忆）
      sessionId: null,

      // 快捷问题推荐列表（引导用户使用）
      suggestionList: [
        '额尔齐斯河流域的气候特点是什么？',
        '如何根据积雪数据预测春季径流量？',
        '帮我写一个Python读取水文数据的脚本',
        '解释一下SWAT水文模型的基本原理'
      ]
    }
  },

  mounted() {
    // 页面加载时获取 AI 配置
    this.fetchAiConfig()
    // 聚焦输入框
    this.$nextTick(() => {
      const inputEl = this.$el.querySelector('.chat-input textarea')
      if (inputEl) inputEl.focus()
    })
  },

  methods: {
    // ==========================================================================
    // 1. 获取 AI 配置（页面初始化时调用）
    // 调用 API: GET /api/ai/config
    // ==========================================================================
    async fetchAiConfig() {
      try {
        const response = await fetch(
          process.env.VUE_APP_BASE_API + '/ai/config/',
          {
            method: 'GET',
            credentials: 'include',
            headers: { 'Content-Type': 'application/json' }
          }
        )

        if (response.ok) {
          const result = await response.json()
          this.llmModelName = result.model || '智能模型'
          this.apiStatus = 'connected'
          return
        }
        throw new Error('获取配置失败')
      } catch (error) {
        console.warn('AI 配置获取失败，使用默认设置:', error)
        this.llmModelName = '智能模型'
        this.apiStatus = 'disconnected'
      }
    },

    // ==========================================================================
    // 2. 发送消息（核心方法）
    // 调用 API: POST /api/ai/chat (SSE 流式)
    // ==========================================================================
    async sendMessage() {
      const text = this.inputMessage.trim()
      if (!text || this.isLoading) return

      // 添加用户消息到界面
      this.addMessage('user', text)
      this.inputMessage = ''

      this.isLoading = true
      try {
        await this.sendStreamRequest(text)
      } catch (error) {
        console.error('请求失败:', error)
        this.addMessage('assistant',
          '抱歉，与服务器的连接出现了问题。\n\n' +
          '可能的原因：\n' +
          '1. 后端服务未启动\n' +
          '2. 网络连接异常\n' +
          '3. LLM 服务响应超时\n\n' +
          '错误信息：' + error.message
        )
      } finally {
        this.isLoading = false
        this.scrollToBottom()
      }
    },

    // ==========================================================================
    // 3. SSE 流式请求（核心通信逻辑）
    // 使用原生 Fetch API + ReadableStream 实现 SSE 流式消费
    // ==========================================================================
    async sendStreamRequest(text) {
      // 后端通过 session_id + thread_id 维护多轮记忆，无需前端回传历史
      // 添加空的助手消息占位（用于流式填充）
      this.addMessage('assistant', '')
      const assistantIndex = this.messageList.length - 1

      // 使用原生 Fetch API（Axios 不支持流式读取）
      // Session 认证：credentials: 'include' 携带 sessionid Cookie，POST 需带 CSRF 头
      const response = await fetch(
        process.env.VUE_APP_BASE_API + '/ai/chat/',
        {
          method: 'POST',
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': Cookies.get('csrftoken') || ''
          },
          body: JSON.stringify({
            message: text,
            session_id: this.sessionId || undefined
          })
        }
      )

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      // 使用 ReadableStream 读取 SSE 流
      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let accumulatedContent = ''
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        // SSE 帧可能跨 chunk：用 buffer 拼接，只处理完整的行
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop()

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          const data = line.slice(6).trim()
          if (!data || data === '[DONE]') continue

          let parsed
          try {
            parsed = JSON.parse(data)
          } catch (e) {
            continue // 非 JSON 帧忽略
          }

          // 后端事件协议：meta / token / tool_start / tool_end / final / error
          switch (parsed.type) {
            case 'meta':
              this.sessionId = parsed.session_id
              break
            case 'token':
              accumulatedContent += parsed.content || ''
              this.$set(this.messageList, assistantIndex, {
                ...this.messageList[assistantIndex],
                content: accumulatedContent
              })
              this.scrollToBottom()
              break
            case 'tool_start':
              if (!accumulatedContent) {
                this.$set(this.messageList, assistantIndex, {
                  ...this.messageList[assistantIndex],
                  content: '⏳ 正在查询数据库…'
                })
              }
              break
            case 'tool_end':
              if (accumulatedContent === '' || this.messageList[assistantIndex].content === '⏳ 正在查询数据库…') {
                this.$set(this.messageList, assistantIndex, {
                  ...this.messageList[assistantIndex],
                  content: accumulatedContent
                })
              }
              break
            case 'final':
              // final 是完整回答：直接替换，避免与 token 流重复拼接
              if (parsed.content) {
                accumulatedContent = parsed.content
                this.$set(this.messageList, assistantIndex, {
                  ...this.messageList[assistantIndex],
                  content: accumulatedContent
                })
                this.scrollToBottom()
              }
              break
            case 'error':
              throw new Error(parsed.message || 'AI 服务错误')
          }
        }
      }
    },

    // ==========================================================================
    // 4. 添加消息到列表
    // ==========================================================================
    addMessage(role, content) {
      const now = new Date()
      const time = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`
      this.messageList.push({ role, content, time })
      this.$nextTick(() => {
        this.scrollToBottom()
      })
    },

    // ==========================================================================
    // 5. 发送快捷消息
    // ==========================================================================
    sendQuickMessage(text) {
      this.inputMessage = text
      this.$nextTick(() => {
        this.sendMessage()
      })
    },

    // ==========================================================================
    // 6. 格式化消息内容（Markdown 渲染）
    // ==========================================================================
    // 为什么不用 marked.js 等库？
    // - 项目当前没有引入 marked，减少额外依赖
    // - LLM 输出的 Markdown 相对简单（标题、列表、代码块、表格）
    // - 自己实现可以更精细控制样式，与 Element UI 风格统一
    // - 如果需要完整 Markdown 支持，后续可以引入 marked + highlight.js
    formatMessage(content) {
      if (!content) return ''

      let html = this.escapeHtml(content)

      // 代码块 ```language\ncode\n```
      html = html.replace(/```(\w+)?\n([\s\S]*?)```/g, (match, lang, code) => {
        return `<pre class="code-block">` +
          `<div class="code-header">` +
            `<span>${lang || 'code'}</span>` +
            `<button class="copy-code-btn" onclick="window.copyCodeToClipboard(this)">复制</button>` +
          `</div>` +
          `<code>${code}</code>` +
        `</pre>`
      })

      // 行内代码 `code`
      html = html.replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>')

      // 粗体 **text**
      html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')

      // 斜体 *text*
      html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>')

      // 标题 ### ## #
      html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>')
      html = html.replace(/^## (.*$)/gim, '<h2>$1</h2>')
      html = html.replace(/^# (.*$)/gim, '<h1>$1</h1>')

      // 无序列表
      html = html.replace(/^\- (.*$)/gim, '<li>$1</li>')
      html = html.replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>')

      // 引用块
      html = html.replace(/^&gt; (.*$)/gim, '<blockquote>$1</blockquote>')

      // 表格
      html = this.parseTables(html)

      // 换行
      html = html.replace(/\n/g, '<br>')

      return html
    },

    parseTables(html) {
      const lines = html.split('\n')
      let result = []
      let inTable = false
      let tableContent = []

      for (let line of lines) {
        if (line.trim().startsWith('|') && line.trim().endsWith('|')) {
          if (!inTable) {
            inTable = true
            tableContent = []
          }
          tableContent.push(line)
        } else {
          if (inTable) {
            result.push(this.buildTable(tableContent))
            inTable = false
          }
          result.push(line)
        }
      }
      if (inTable) {
        result.push(this.buildTable(tableContent))
      }
      return result.join('\n')
    },

    buildTable(lines) {
      if (lines.length < 2) return lines.join('\n')
      let html = '<table class="md-table">'
      // 表头
      const headers = lines[0].split('|').map(h => h.trim()).filter(h => h)
      html += '<thead><tr>'
      headers.forEach(h => { html += `<th>${this.escapeHtml(h)}</th>` })
      html += '</tr></thead>'
      // 表体（跳过第二行分隔符）
      html += '<tbody>'
      for (let i = 2; i < lines.length; i++) {
        const cells = lines[i].split('|').map(c => c.trim()).filter(c => c)
        html += '<tr>'
        cells.forEach(c => { html += `<td>${this.escapeHtml(c)}</td>` })
        html += '</tr>'
      }
      html += '</tbody></table>'
      return html
    },

    escapeHtml(text) {
      const div = document.createElement('div')
      div.textContent = text
      return div.innerHTML
    },

    // ==========================================================================
    // 7. 键盘事件处理
    // ==========================================================================
    handleKeyDown(e) {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault()
        this.sendMessage()
      }
    },

    // ==========================================================================
    // 8. 滚动到底部
    // ==========================================================================
    scrollToBottom() {
      this.$nextTick(() => {
        const scrollbar = this.$refs.messageScrollbar
        if (scrollbar && scrollbar.wrap) {
          scrollbar.wrap.scrollTop = scrollbar.wrap.scrollHeight
        }
      })
    },

    // ==========================================================================
    // 9. 复制消息内容
    // ==========================================================================
    copyMessage(content) {
      navigator.clipboard.writeText(content).then(() => {
        this.$message.success('已复制到剪贴板')
      }).catch(() => {
        this.$message.error('复制失败')
      })
    },

    // ==========================================================================
    // 10. 清空对话
    // ==========================================================================
    handleClearChat() {
      if (this.messageList.length === 0) return
      this.$confirm('确定要清空所有对话记录吗？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(() => {
        this.messageList = []
        this.$message.success('对话已清空')
      }).catch(() => {})
    }
  }
}

// 全局复制代码函数（供代码块复制按钮调用）
window.copyCodeToClipboard = function(btn) {
  const code = btn.closest('.code-block').querySelector('code').textContent
  navigator.clipboard.writeText(code).then(() => {
    btn.textContent = '已复制!'
    setTimeout(() => btn.textContent = '复制', 2000)
  })
}
</script>

<style lang="scss" scoped>
// ==============================================================================
// 样式设计说明
// ==============================================================================
// 1. 使用 Element UI 的主题色（#409EFF）作为主色调，与项目风格统一
// 2. 用户消息使用渐变蓝色背景，助手消息使用白色卡片
// 3. 代码块采用深色主题，与 VS Code 风格类似
// 4. 所有间距使用 4px 倍数，保持视觉节奏感
// ==============================================================================

.ai-assistant-container {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 84px);  // 减去顶部导航栏高度
  background: #f8f9fa;
}

/* 头部 */
.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  background: linear-gradient(90deg, #409EFF 0%, #5cadff 100%);
  color: #fff;

  .header-left {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .ai-avatar {
    background: #fff;
    color: #409EFF;
    font-size: 20px;
  }

  .header-title {
    font-size: 18px;
    font-weight: 600;
  }

  .header-subtitle {
    font-size: 12px;
    opacity: 0.85;
    display: flex;
    align-items: center;
    gap: 6px;
    margin-top: 2px;

    .status-dot {
      width: 8px;
      height: 8px;
      background: #67C23A;
      border-radius: 50%;
      animation: pulse 2s infinite;
    }
  }

  .clear-btn {
    color: #fff;
    opacity: 0.8;
    &:hover { opacity: 1; }
  }
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

/* 消息区域 */
.chat-messages {
  flex: 1;
  overflow: hidden;

  ::v-deep .messages-wrapper {
    padding: 24px;
  }
}

/* 欢迎面板 */
.welcome-panel {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;

  .welcome-content {
    text-align: center;
    max-width: 500px;
  }

  .welcome-avatar {
    background: linear-gradient(135deg, #409EFF, #5cadff);
    color: #fff;
    font-size: 40px;
    margin-bottom: 20px;
  }

  .welcome-title {
    font-size: 24px;
    color: #303133;
    margin-bottom: 8px;
    font-weight: 600;
  }

  .welcome-desc {
    font-size: 14px;
    color: #909399;
    margin-bottom: 24px;
  }

  .suggestion-list {
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: 8px;

    .suggestion-tag {
      cursor: pointer;
      border-radius: 16px;
      padding: 0 16px;
      height: 32px;
      line-height: 30px;
      font-size: 13px;
      transition: all 0.2s;

      &:hover {
        color: #409EFF;
        border-color: #409EFF;
        background: #ecf5ff;
      }
    }
  }
}

/* 消息列表 */
.message-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.message-item {
  display: flex;
  gap: 10px;
  max-width: 85%;
  animation: messageIn 0.3s ease;

  &.user {
    align-self: flex-end;
    flex-direction: row-reverse;
    margin-left: auto;
  }

  &.assistant {
    align-self: flex-start;
  }
}

@keyframes messageIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

.message-avatar {
  flex-shrink: 0;

  &.user {
    background: linear-gradient(135deg, #409EFF, #5cadff);
    color: #fff;
  }

  &.assistant {
    background: #e4e7ed;
    color: #606266;
  }
}

.message-body {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.message-bubble {
  padding: 12px 16px;
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.7;
  word-break: break-word;

  // Markdown 渲染样式
  ::v-deep {
    h1, h2, h3 { margin: 8px 0 4px; color: #303133; }
    h1 { font-size: 18px; }
    h2 { font-size: 16px; }
    h3 { font-size: 14px; }
    p { margin: 6px 0; }
    ul, ol { padding-left: 20px; margin: 6px 0; }
    li { margin: 2px 0; }
    blockquote {
      border-left: 4px solid #409EFF;
      padding: 8px 12px;
      margin: 8px 0;
      background: #f4f4f5;
      border-radius: 0 8px 8px 0;
      color: #606266;
    }

    .inline-code {
      background: #f4f4f5;
      padding: 2px 6px;
      border-radius: 4px;
      font-family: 'Courier New', monospace;
      font-size: 13px;
      color: #f56c6c;
    }

    .code-block {
      background: #1a1a2e;
      border-radius: 10px;
      padding: 16px;
      margin: 10px 0;
      overflow-x: auto;
      position: relative;

      .code-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
        padding-bottom: 8px;
        border-bottom: 1px solid rgba(255,255,255,0.1);

        span { color: #a0a0a0; font-size: 12px; }

        .copy-code-btn {
          background: rgba(255,255,255,0.1);
          border: 1px solid rgba(255,255,255,0.2);
          color: #e9ecef;
          padding: 2px 10px;
          border-radius: 4px;
          font-size: 12px;
          cursor: pointer;
          &:hover { background: rgba(255,255,255,0.2); }
        }
      }

      code {
        color: #e9ecef;
        font-family: 'Courier New', monospace;
        font-size: 13px;
        line-height: 1.6;
        white-space: pre;
      }
    }

    .md-table {
      border-collapse: collapse;
      width: 100%;
      margin: 10px 0;
      font-size: 13px;

      th, td {
        border: 1px solid #dcdfe6;
        padding: 8px 12px;
        text-align: left;
      }
      th { background: #f5f7fa; font-weight: 600; }
      tr:nth-child(even) { background: #fafafa; }
    }
  }
}

.message-item.user .message-bubble {
  background: linear-gradient(135deg, #409EFF, #5cadff);
  color: #fff;
  border-bottom-right-radius: 4px;
}

.message-item.assistant .message-bubble {
  background: #fff;
  color: #303133;
  border-bottom-left-radius: 4px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}

.message-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 11px;

  .message-time { color: #c0c4cc; }
  .copy-btn {
    padding: 0;
    font-size: 11px;
    color: #c0c4cc;
    &:hover { color: #409EFF; }
  }
}

.message-item.user .message-meta {
  justify-content: flex-end;
}

/* 打字机指示器 */
.typing-indicator {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 12px 16px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);

  span {
    width: 8px;
    height: 8px;
    background: #c0c4cc;
    border-radius: 50%;
    animation: typingBounce 1.4s infinite ease-in-out both;
    &:nth-child(1) { animation-delay: -0.32s; }
    &:nth-child(2) { animation-delay: -0.16s; }
  }
}

@keyframes typingBounce {
  0%, 80%, 100% { transform: scale(0.4); }
  40% { transform: scale(1); }
}

/* 输入区域 */
.chat-input-area {
  display: flex;
  gap: 12px;
  padding: 16px 24px;
  background: #fff;
  border-top: 1px solid #e4e7ed;
  align-items: flex-end;

  .chat-input {
    flex: 1;

    ::v-deep textarea {
      border-radius: 10px;
      padding: 10px 14px;
      font-size: 14px;
      line-height: 1.5;

      &:focus {
        border-color: #409EFF;
        box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.15);
      }
    }
  }

  .send-btn {
    width: 44px;
    height: 44px;
    border-radius: 10px;
    padding: 0;
    font-size: 18px;

    &:disabled { opacity: 0.5; }
    &:not(:disabled):hover { transform: scale(1.05); }
  }
}
</style>
