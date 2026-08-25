import request from '@/utils/request'

// 获取站点树形列表
export function getStationList(searchObj) {
  return request({
    url: '/station',
    method: 'get',
    params: {
      name: searchObj
    }
  })
}

// 更新站点
export function update(params) {
  return request({
    url: `/station`,
    method: 'put',
    data: params
  })
}

// 无权限更新数据表别名
export function updateNoAuthorize(params) {
  return request({
    url: `/station/no-authorize`,
    method: 'put',
    data: params
  })
}

// 添加站点
export function add(params) {
  return request({
    url: '/station',
    method: 'post',
    data: params
  })
}

// 禁用站点
export function destroy(id) {
  return request({
    url: `/station/${id}`,
    method: 'delete'
  })
}

// 设置数采
export function setupDataLogger(setupForm) {
  return request({
    url: '/station/mqtt',
    method: 'post',
    data: setupForm
  })
}

// 设置CRNS-N0
export function setupCrnsN0(setupForm) {
  return request({
    url: '/station/crns',
    method: 'post',
    data: setupForm
  })
}

// 获取台站详情
export function details(id) {
  return request({
    url: `/station/setup/${id}`,
    method: 'get'
  })
}

// 获取台站详情
export function updateDetails(id, details) {
  return request({
    url: `/station/setup/${id}`,
    method: 'post',
    data: details
  })
}

// 删除档案资料
export function removeDocument(id, type) {
  return request({
    url: `/station/setup/${id}`,
    method: 'delete',
    data: type
  })
}
