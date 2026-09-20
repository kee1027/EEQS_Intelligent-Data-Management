import request from '@/utils/request'

export function getHydrologyData(params) {
  return request({
    url: '/hydrology-data',
    method: 'get',
    params
  })
}

// 手动重跑模型预测（操作员/管理员）
export function triggerHydrologyRun(data) {
  return request({
    url: '/hydrology-runs/',
    method: 'post',
    data
  })
}
