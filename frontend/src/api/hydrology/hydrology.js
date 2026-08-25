import request from '@/utils/request'

export function getHydrologyData(params) {
  return request({
    url: '/hydrology-data',
    method: 'get',
    params
  })
}
