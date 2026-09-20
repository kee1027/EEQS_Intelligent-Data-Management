// 用户登录态与角色（Session 认证：token Cookie 仅作为「已登录」标记，
// 真正的凭据是后端下发的 sessionid Cookie，随请求自动携带）
import { getToken, setToken, removeToken } from '@/utils/auth'
import { login, logout, getMe } from '@/api/auth'
import { resetRouter } from '@/router'

const getDefaultState = () => {
  return {
    token: getToken(),
    name: '',
    avatar: '',
    role: '',
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
    state.name = data.username || ''
    state.role = data.role || ''
    state.permissions = data.groups || []
  }
}

const actions = {
  async login({ commit }, loginForm) {
    const { username, password } = loginForm
    const { data } = await login({ username: username.trim(), password })
    commit('SET_USERINFO', data)
    // Session 认证下 token 只是登录标记，内容为占位符
    commit('SET_TOKEN', 'session')
    setToken('session')
    return data
  },

  async getInfo({ commit }) {
    const { data } = await getMe()
    commit('SET_USERINFO', data)
    return data
  },

  async logout({ commit }) {
    try {
      await logout()
    } finally {
      removeToken()
      resetRouter()
      commit('RESET_STATE')
    }
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
