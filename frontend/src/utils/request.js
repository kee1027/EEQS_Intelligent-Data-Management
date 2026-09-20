import axios from 'axios'
import Cookies from 'js-cookie'
import { Message } from 'element-ui'
import store from '@/store'
import router from '@/router'

// 是否显示重新登录
export const isRelogin = { show: false }

// create an axios instance
const service = axios.create({
  baseURL: process.env.VUE_APP_BASE_API, // url = base url + request url
  timeout: 60 * 1000, // request timeout
  withCredentials: true // Session 认证：始终携带 sessionid / csrftoken Cookie
})

// 请求拦截器：非 GET 请求自动附带 CSRF 头（Django Session 认证强制校验）
service.interceptors.request.use(
  config => {
    const method = (config.method || 'get').toLowerCase()
    if (method !== 'get') {
      const csrfToken = Cookies.get('csrftoken')
      if (csrfToken && !config.headers['X-CSRFToken']) {
        config.headers['X-CSRFToken'] = csrfToken
      }
    }
    return config
  },
  error => {
    console.log(error) // for debug
    return Promise.reject(error)
  }
)

// 响应拦截器：DRF 直接返回数据（无 code 包装），2xx 即成功；
// 401 → 回登录页；403 → 提示无权限；其余错误提取 detail 展示
service.interceptors.response.use(
  res => res,
  error => {
    const response = error.response
    const status = response ? response.status : 0
    const detail = (response && response.data && (response.data.detail || response.data.message)) || ''

    if (status === 401) {
      // 未登录或 Session 过期：清理本地状态并回登录页（登录页自身发起的 401 除外）
      if (router.currentRoute.path !== '/login') {
        store.dispatch('user/resetToken').then(() => {
          router.push(`/login?redirect=${router.currentRoute.path}`)
        })
      }
    } else if (status === 403) {
      Message({
        message: detail || '没有执行该操作的权限',
        type: 'error',
        duration: 5 * 1000
      })
    } else if (!status) {
      Message({
        message: error.message === 'Network Error' ? '后端接口连接异常' : error.message,
        type: 'error',
        duration: 5 * 1000
      })
    }
    // 其余状态码（400/404/409/500 等）交给调用方自行处理
    return Promise.reject(error)
  }
)

export default service
