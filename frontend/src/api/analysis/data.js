import request from '@/utils/request'

export function diagram(type, datetime, data, page, paginate_number) {
  return request({
    url: '/diagram',
    timeout: 90 * 1000,
    method: 'post',
    params: {
      page: page,
      paginate_number: paginate_number
    },
    data: {
      date: datetime,
      chartType: type,
      params: data
    }
  })
}
// 获取站点数据树形结构
export function getStationList(type) {
  return request({
    url: '/diagram',
    method: 'get',
    params: { type: type }
  })
}

// 获取数据下载模块树形结构
export function getDownloadStationList() {
  return request({
    url: '/diagram/download',
    method: 'get'
  })
}

// // 获取SD60树形结构-不包含tablefield
// export function getSD601List() {
//     return request({
//         url: '/diagram/noTableField',
//         method: 'get'
//     })
// }
// // 获取SD60树形结构-按土壤参数进行分类
// export function getSD601classifyList() {
//     return request({
//         url: '/sd601classify',
//         method: 'get'
//     })
// }

export function getCSVFile(type, datetime, datas, page, paginate_number, zipparams, value1) {
  return request({
    url: '/diagram',
    method: 'post',
    params: {
      page: page,
      paginate_number: paginate_number
    },
    data: {
      date: datetime,
      type: type,
      params: datas,
      // page: page,
      // paginate_number: paginate_number,
      zipparams: zipparams,
      classify: value1
    },
    responseType: 'blob'
  })
}

// 获取站点数据树形结构
export function getLatestData(tableId) {
  return request({
    url: '/diagram/real-data',
    method: 'get',
    params: {
      tableId: tableId
    }
  })
}

export function getGridDiagramData(type, index, queryType, categoriesId, tableName) {
  return request({
    url: '/diagram/grid-diagram',
    method: 'get',
    params: {
      chartType: type,
      chartIndex: index,
      queryType: queryType,
      categoriesId: categoriesId,
      tableName: tableName
    }
  })
}

export function getGridDiagramUserInfo(tableId) {
  return request({
    url: '/diagram/grid-diagram/info',
    method: 'get',
    params: {
      tableId: tableId
    }
  })
}

export function gridDiagramSetup(interval_time, index, type, data, categoriesId, tableName, reverse, min, max) {
  return request({
    url: '/diagram/grid-diagram',
    method: 'post',
    data: {
      intervalTime: interval_time,
      chartIndex: index,
      chartType: type,
      params: data,
      categoriesId: categoriesId,
      tableName: tableName,
      chartReverse: reverse,
      min: min,
      max: max
    }
  })
}

export function uploadMerge(uniqueIdentifier, name, offset, tableName, radio) {
  return request({
    url: '/upload/merge',
    method: 'post',
    data: {
      identifier: uniqueIdentifier,
      filename: name,
      totalChunks: offset,
      tableInfo: tableName,
      uploadType: radio
    }
  })
}

// 清空数据
export function clearData(tableIds) {
  return request({
    url: '/data',
    method: 'delete',
    data: tableIds
  })
}
