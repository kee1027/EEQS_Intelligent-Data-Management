import Vue from 'vue'
import 'normalize.css/normalize.css'
import VueCompositionAPI from '@vue/composition-api'
import ElementUI from 'element-ui'
import 'element-ui/lib/theme-chalk/index.css'
import locale from 'element-ui/lib/locale/lang/zh-CN'
import '@/styles/index.scss'
import App from './App'
import store from './store'
import router from './router'
import '@/icons'
import '@/permission'
import API from '@/api'
import plugins from './plugins'
import permission from '@/directive/permission'
import { fetchCsrf } from '@/api/auth'

Vue.use(VueCompositionAPI)
Vue.use(ElementUI, { locale })
Vue.use(plugins)
Vue.directive('permission', permission)
Vue.prototype.$API = API
Vue.config.productionTip = false

// 启动时先取 CSRF Cookie（Session 写请求需要 X-CSRFToken 头）
fetchCsrf().catch(() => {})

new Vue({
  el: '#app',
  router,
  store,
  render: h => h(App)
})
