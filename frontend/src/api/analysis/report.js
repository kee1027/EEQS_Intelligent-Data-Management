import request from '@/utils/request'

// 获取报表列表
export function getReportList(page, limit) {
  return request({
    url: '/report',
    method: 'get',
    params: {
      page: page,
      paginate_number: limit
    }
  })
}

export function getFieldsList(categoriesId, isAdd, reportId) {
  return request({
    url: '/report/report-field-list',
    method: 'get',
    params: {
      categoriesId: categoriesId,
      isAdd: isAdd,
      reportId: reportId
    }
  })
}

export function add(list) {
  return request({
    url: '/report',
    method: 'post',
    data: list
  })
}

export function update(list) {
  return request({
    url: '/report',
    method: 'put',
    data: list
  })
}

export function remove(item) {
  return request({
    url: '/report',
    method: 'delete',
    data: item
  })
}

export function getReportAutoList(page, limit, id) {
  return request({
    url: `/report/auto/${id}`,
    method: 'get',
    params: {
      page: page,
      paginate_number: limit
    }
  })
}
