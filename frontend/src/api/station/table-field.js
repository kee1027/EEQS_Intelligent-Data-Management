import request from '@/utils/request'

export function showField(id) {
  return request({
    url: `/station/table-field/${id}`,
    method: 'get'
  })
}

export function addField(item, parentId) {
  return request({
    url: '/station/table-field',
    method: 'post',
    data: { item, parentId }
  })
}

export function modifyField(item, tableId) {
  return request({
    url: '/station/table-field',
    method: 'put',
    data: { item, tableId }
  })
}

export function removeField(item, tableName, tableType, parentId) {
  return request({
    url: `/station/table-field`,
    method: 'delete',
    data: { item, tableName, tableType, parentId }
  })
}

export function updateField(item, id) {
  return request({
    url: `/station/table-field/${id}`,
    method: 'put',
    data: item
  })
}
