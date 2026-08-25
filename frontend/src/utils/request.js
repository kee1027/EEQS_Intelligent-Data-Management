import axios from 'axios'
import { MessageBox, Message } from 'element-ui'
import store from '@/store'
import { getToken } from '@/utils/auth'

// 是否显示重新登录
export const isRelogin = { show: false }

// create an axios instance
const service = axios.create({
  baseURL: process.env.VUE_APP_BASE_API, // url = base url + request url
  timeout: 60 * 1000 // request timeout
  // withCredentials: true, // send cookies when cross-domain requests
})

// 请求拦截器：携带的token字段
service.interceptors.request.use(
  config => {
    // do something before request is sent

    if (store.getters.token) {
      // let each request carry token
      // ['X-Token'] is a custom headers key
      // please modify it according to the actual situation
      config.headers['Authorization'] = getToken()
    }
    return config
  },
  error => {
    // do something with request error
    console.log(error) // for debug
    return Promise.reject(error)
  }
)

// 响应拦截器
service.interceptors.response.use(res => {
  // 未设置状态码则默认成功状态
  const code = res.data.code
  // 获取错误信息
  // const msg = errorCode[code] || res.data.msg || errorCode['default']
  const msg = res.data.msg || '系统未知错误'
  // 二进制数据则直接返回
  if (res.request.responseType === 'blob' || res.request.responseType === 'arraybuffer') {
    return res
  }
  if (code === 401) {
    if (!isRelogin.show) {
      isRelogin.show = true
      MessageBox.confirm('登录状态已过期,您可以继续留在该页面,或者重新登录', '系统提示', {
        confirmButtonText: '重新登录',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(() => {
        isRelogin.show = false
        store.dispatch('user/logoutUnauthority').then(() => {
          location.href = '/'
        })
      }).catch(() => {
        isRelogin.show = false
      })
    }
    return Promise.reject('无效的会话,或者会话已过期,请重新登录。')
  } else if (code === 500) {
    Message({
      message: msg,
      type: 'error'
    })
    return Promise.reject(new Error(msg))
  } else if (code !== 200 && code !== undefined && code !== null) {
    Message({
      message: msg,
      type: 'error'
    })
    return Promise.reject('error')
  } else {
    return res
  }
},
error => {
  console.log('err' + error)
  let { message } = error
  if (message === 'Network Error') {
    message = '后端接口连接异常'
  } else if (message.includes('timeout')) {
    message = '系统接口请求超时'
  } else if (message.includes('Request failed with status code')) {
    message = '系统接口' + message.substr(message.length - 3) + '异常'
  }
  Message({
    message: message,
    type: 'error',
    duration: 5 * 1000
  })
  return Promise.reject(error)
}
)

export default service
