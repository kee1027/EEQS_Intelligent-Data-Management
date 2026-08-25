import request from '@/utils/request'

export function getPointCloudTreeList(type) {
  return request({
    url: '/point-cloud',
    method: 'get',
    params: { type: type }
  })
}

export function getFileLibrary(categoryId, datetime, page, paginate_number) {
  return request({
    url: '/point-cloud',
    method: 'post',
    params: {
      page: page,
      paginate_number: paginate_number
    },
    data: {
      categoryId: categoryId,
      date: datetime
    }
  })
}

export function diagram(categoryId, datetime) {
  return request({
    url: '/point-cloud/diagram',
    method: 'post',
    data: {
      categoryId: categoryId,
      date: datetime
    }
  })
}

export function pointCloudHandler() {
  return request({
    url: '/point-cloud/handler',
    method: 'get'
  })
}
