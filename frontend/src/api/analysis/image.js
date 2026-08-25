import request from '@/utils/request'

// 获取照片站点数据树形结构
export function getImageStationList(type) {
  return request({
    url: '/image',
    method: 'get',
    params: { type: type }
  })
}

// 刷新图片入库列表
export function refreshImageLibrary() {
  return request({
    url: '/image/refresh',
    method: 'get'
  })
}

export function getImageLibrary(type, datetime, data, page, paginate_number) {
  return request({
    url: '/image',
    method: 'post',
    params: {
      page: page,
      paginate_number: paginate_number
    },
    data: {
      date: datetime,
      type: type,
      params: data
    }
  })
}

export function downloadImage(datetime, zipParams) {
  return request({
    url: '/image/download',
    method: 'post',
    data: {
      date: datetime,
      zipParams: zipParams
    },
    responseType: 'blob'
  })
}
