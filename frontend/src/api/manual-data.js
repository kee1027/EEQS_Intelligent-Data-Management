import Cookies from 'js-cookie'
import request from '@/utils/request'

function getCsrfToken() {
  return Cookies.get('csrftoken') || Cookies.get('csrfToken') || ''
}

export function createManualData(data) {
  const csrfToken = getCsrfToken()
  return request({
    url: '/manual-data/',
    method: 'post',
    withCredentials: true,
    headers: csrfToken ? { 'X-CSRFToken': csrfToken } : {},
    data: data
  })
}

export function voidManualData(id) {
  const csrfToken = getCsrfToken()
  return request({
    url: `/manual-data/${id}/void/`,
    method: 'post',
    withCredentials: true,
    headers: csrfToken ? { 'X-CSRFToken': csrfToken } : {}
  })
}

export function listManualData() {
  const csrfToken = getCsrfToken()
  return request({
    url: '/manual-data/',
    method: 'get',
    withCredentials: true,
    headers: csrfToken ? { 'X-CSRFToken': csrfToken } : {}
  })
}
