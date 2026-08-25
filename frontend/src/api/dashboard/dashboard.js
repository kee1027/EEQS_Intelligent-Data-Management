import request from '@/utils/request'

export function diagram(chartTitle, interval_time, index, type, data, reverse, min, max) {
  return request({
    url: '/dashboard',
    method: 'post',
    data: {
      chartTitle: chartTitle,
      intervalTime: interval_time,
      chartIndex: index,
      chartType: type,
      params: data,
      chartReverse: reverse,
      min: min,
      max: max
    }
  })
}

export function getData(type, index, querytype) {
  return request({
    url: '/dashboard',
    method: 'get',
    params: {
      chartType: type,
      chartIndex: index,
      queryType: querytype
    }
  })
}

// 获取照片数据
export function getImageDashboardList() {
  return request({
    url: '/image/dashboard',
    method: 'get'
  })
}
