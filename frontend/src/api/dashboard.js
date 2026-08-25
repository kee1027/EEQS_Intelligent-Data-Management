import request from '@/utils/request'

/**
 * 查询站点列表
 * @returns {Promise<axios.AxiosResponse<any>>}
 */
export function getStations() {
  return request({
    url: '/stations/',
    method: 'get'
  })
}

/**
 * 查询气象数据
 * @param {object} params 查询参数
 * @param {object} config axios 配置（可传 signal 等）
 * @returns {Promise<axios.AxiosResponse<any>>}
 */
export function getWeatherData(params, config = {}) {
  return request({
    url: '/weatherdata/',
    method: 'get',
    params,
    ...config
  })
}
