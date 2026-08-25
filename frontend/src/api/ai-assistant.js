import request from '@/utils/request'

/**
 * 发送普通聊天消息（非流式）
 * @param {Object} data - 消息数据
 * @param {string} data.message - 用户消息内容
 * @param {Array} data.history - 对话历史记录
 */
export function sendChatMessage(data) {
  return request({
    url: '/ai/chat',
    method: 'post',
    data
  })
}

/**
 * 获取AI助手配置信息
 */
export function getAiConfig() {
  return request({
    url: '/ai/config',
    method: 'get'
  })
}

/**
 * 获取对话历史记录
 * @param {Object} params - 查询参数
 */
export function getChatHistory(params) {
  return request({
    url: '/ai/history',
    method: 'get',
    params
  })
}

/**
 * 保存对话记录
 * @param {Object} data - 对话数据
 */
export function saveChatSession(data) {
  return request({
    url: '/ai/save',
    method: 'post',
    data
  })
}
