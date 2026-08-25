// 获取token|设置token|删除token的函数
import { getToken, setToken, removeToken } from '@/utils/auth'
// 路由模块当中重置路由的方法
import { resetRouter } from '@/router'
import { Message } from 'element-ui'
import router from '@/router'

const getDefaultState = () => {
  return {
    token: getToken(),
    name: '',
    avatar: '',
    role: [],
    permissions: []
  }
}

const state = getDefaultState()

const mutations = {
  RESET_STATE: (state) => {
    Object.assign(state, getDefaultState())
  },
  SET_TOKEN: (state, token) => {
    state.token = token
  },
  SET_USERINFO: (state, data) => {
    state.name = data.userName || data.name || '管理员'
    state.avatar = data.avatar || ''
    state.role = data.role || []
    state.permissions = data.permissions || []
  }
}

const actions = {
  async login({ commit }, loginForm) {
    const { userInfo, password } = loginForm
    // 简化登录逻辑，直接模拟登录成功
    // 实际项目中应调用后端登录接口
    const token = 'admin-token-' + Date.now()
    commit('SET_TOKEN', token)
    setToken(token)
    return true
  },

  async getInfo({ commit, state }) {
    // 简化获取用户信息逻辑
    commit('SET_USERINFO', {
      userName: '管理员',
      name: '管理员',
      avatar: '',
      role: ['admin'],
      permissions: ['*']
    })
  },

  async logout({ commit }) {
    removeToken()
    resetRouter()
    commit('RESET_STATE')
  },

  async logoutUnauthority({ commit }) {
    removeToken()
    resetRouter()
    commit('RESET_STATE')
  },

  resetToken({ commit }) {
    return new Promise(resolve => {
      removeToken()
      commit('RESET_STATE')
      resolve()
    })
  }
}

export default {
  namespaced: true,
  state,
  mutations,
  actions
}
