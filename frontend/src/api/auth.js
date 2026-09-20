import Cookies from 'js-cookie'
import request from '@/utils/request'

function csrfHeaders() {
  const token = Cookies.get('csrftoken') || ''
  return token ? { 'X-CSRFToken': token } : {}
}

// 应用启动时调用：让后端下发 csrftoken Cookie（Session 写请求需要）
export function fetchCsrf() {
  return request({
    url: '/auth/csrf/',
    method: 'get',
    withCredentials: true
  })
}

export function login(data) {
  return request({
    url: '/auth/login/',
    method: 'post',
    withCredentials: true,
    headers: csrfHeaders(),
    data
  })
}

export function logout() {
  return request({
    url: '/auth/logout/',
    method: 'post',
    withCredentials: true,
    headers: csrfHeaders()
  })
}

export function getMe() {
  return request({
    url: '/auth/me/',
    method: 'get',
    withCredentials: true
  })
}
