import defaultSettings from '@/settings'
import variables from '@/styles/variables.scss'

const { sideTheme, showSettings, fixedHeader, sidebarLogo, menuInLeft } = defaultSettings

const storageSetting = JSON.parse(localStorage.getItem('layout-setting')) || ''
let menuInLeftFinal
if (storageSetting === '') {
  menuInLeftFinal = menuInLeft
} else {
  menuInLeftFinal = storageSetting.menuInLeft
  Object.keys(variables).forEach(key => {
    if (key.startsWith(storageSetting.sideTheme)) {
      const variableName = `${key.replace(storageSetting.sideTheme, '-')}`
      const variableValue = variables[key]
      document.documentElement.style.setProperty(variableName, variableValue)
    }
  })
}
const state = {
  showSettings: showSettings,
  fixedHeader: fixedHeader,
  sidebarLogo: sidebarLogo,
  menuInLeft: menuInLeftFinal,
  sideTheme: storageSetting.sideTheme || sideTheme,
  menuBg: getComputedStyle(document.documentElement).getPropertyValue('--menu-bg'),
  menuText: getComputedStyle(document.documentElement).getPropertyValue('--menu-text'),
  menuActiveText: getComputedStyle(document.documentElement).getPropertyValue('--menu-active-text')
}

const mutations = {
  CHANGE_SETTING: (state, { key, value }) => {
    if (Object.prototype.hasOwnProperty.call(state, key)) {
      state[key] = value
    }
  }
}

const actions = {
  // 修改布局设置
  changeSetting({ commit }, data) {
    Object.entries(data).forEach(([key, value]) => {
      commit('CHANGE_SETTING', { key, value })
    })
  }
}

export default {
  namespaced: true,
  state,
  mutations,
  actions
}

