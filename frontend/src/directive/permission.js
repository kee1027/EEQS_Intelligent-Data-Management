// v-permission 指令：按角色控制元素显隐（仅体验层，安全边界在后端）
// 用法：v-permission="['operator', 'admin']" —— 角色不在列表中则移除元素
// 管理员（admin）始终放行
import store from '@/store'

export default {
  inserted(el, binding) {
    const roles = binding.value
    if (!Array.isArray(roles) || roles.length === 0) return

    const role = store.getters.role
    if (role === 'admin') return
    if (!roles.includes(role)) {
      el.parentNode && el.parentNode.removeChild(el)
    }
  }
}
