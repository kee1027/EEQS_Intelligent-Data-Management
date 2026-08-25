import request from '@/utils/request'

// 获取照片站点数据树形结构
export function getRawFileList(type) {
  return request({
    url: '/file',
    method: 'get',
    params: { type: type }
  })
}

export function getRawFileLibrary(fileType, categoryId, datetime, page, paginate_number) {
  return request({
    url: '/file',
    method: 'post',
    params: {
      page: page,
      paginate_number: paginate_number
    },
    data: {
      fileType: fileType,
      categoryId: categoryId,
      date: datetime
    }
  })
}
