/**
 * Created by PanJiaChen on 16/11/18.
 */

/**
 * Parse the time to string
 * @param {(Object|string|number)} time
 * @param {string} cFormat
 * @returns {string | null}
 */
export function parseTime(time, cFormat) {
  if (arguments.length === 0 || !time) {
    return null
  }
  const format = cFormat || '{y}-{m}-{d} {h}:{i}:{s}'
  let date
  if (typeof time === 'object') {
    date = time
  } else {
    if ((typeof time === 'string')) {
      if ((/^[0-9]+$/.test(time))) {
        // support "1548221490638"
        time = parseInt(time)
      } else {
        // support safari
        // https://stackoverflow.com/questions/4310953/invalid-date-in-safari
        time = time.replace(new RegExp(/-/gm), '/')
      }
    }

    if ((typeof time === 'number') && (time.toString().length === 10)) {
      time = time * 1000
    }
    date = new Date(time)
  }
  const formatObj = {
    y: date.getFullYear(),
    m: date.getMonth() + 1,
    d: date.getDate(),
    h: date.getHours(),
    i: date.getMinutes(),
    s: date.getSeconds(),
    a: date.getDay()
  }
  return format.replace(/{([ymdhisa])+}/g, (result, key) => {
    const value = formatObj[key]
    // Note: getDay() returns 0 on Sunday
    if (key === 'a') {
      return ['日', '一', '二', '三', '四', '五', '六'][value]
    }
    return value.toString().padStart(2, '0')
  })
}

/**
 * @param {number} time
 * @param {string} option
 * @returns {string}
 */
export function formatTime(time, option) {
  if (('' + time).length === 10) {
    time = parseInt(time) * 1000
  } else {
    time = +time
  }
  const d = new Date(time)
  const now = Date.now()

  const diff = (now - d) / 1000

  if (diff < 30) {
    return '刚刚'
  } else if (diff < 3600) {
    // less 1 hour
    return Math.ceil(diff / 60) + '分钟前'
  } else if (diff < 3600 * 24) {
    return Math.ceil(diff / 3600) + '小时前'
  } else if (diff < 3600 * 24 * 2) {
    return '1天前'
  }
  if (option) {
    return parseTime(time, option)
  } else {
    return (
      d.getMonth() +
      1 +
      '月' +
      d.getDate() +
      '日' +
      d.getHours() +
      '时' +
      d.getMinutes() +
      '分'
    )
  }
}

// 获得年月日时分秒
// 传入日期//例：2020-10-27T14:36:23
export function timeFormatSeconds(time) {
  const d = time ? new Date(time) : new Date()
  const year = d.getFullYear()
  let month = d.getMonth() + 1
  let day = d.getDate()
  let hours = d.getHours()
  let min = d.getMinutes()
  let seconds = d.getSeconds()

  if (month < 10) month = '0' + month
  if (day < 10) day = '0' + day
  if (hours < 0) hours = '0' + hours
  if (min < 10) min = '0' + min
  if (seconds < 10) seconds = '0' + seconds

  return (year + '-' + month + '-' + day + ' ' + hours + ':' + min + ':' + seconds)
}

/**
 * @param {string} url
 * @returns {Object}
 */
export function param2Obj(url) {
  const search = decodeURIComponent(url.split('?')[1]).replace(/\+/g, ' ')
  if (!search) {
    return {}
  }
  const obj = {}
  const searchArr = search.split('&')
  searchArr.forEach(v => {
    const index = v.indexOf('=')
    if (index !== -1) {
      const name = v.substring(0, index)
      const val = v.substring(index + 1, v.length)
      obj[name] = val
    }
  })
  return obj
}

/**
 * 构造树型结构数据
 * @param {*} data 数据源
 * @param {*} id id字段 默认 'id'
 * @param {*} parentId 父节点字段 默认 'parentId'
 * @param {*} children 孩子节点字段 默认 'children'
 */
export function handleTree(data, id, parentId, children) {
  const config = {
    id: id || 'id',
    parentId: parentId || 'parentId',
    childrenList: children || 'children'
  }

  const childrenListMap = {}
  const nodeIds = {}
  const tree = []

  for (const d of data) {
    const parentId = d[config.parentId]
    if (childrenListMap[parentId] == null) {
      childrenListMap[parentId] = []
    }
    nodeIds[d[config.id]] = d
    childrenListMap[parentId].push(d)
  }

  for (const d of data) {
    const parentId = d[config.parentId]
    if (nodeIds[parentId] == null) {
      tree.push(d)
    }
  }

  for (const t of tree) {
    adaptToChildrenList(t)
  }

  function adaptToChildrenList(o) {
    if (childrenListMap[o[config.id]] !== null) {
      o[config.childrenList] = childrenListMap[o[config.id]]
    }
    if (o[config.childrenList]) {
      for (const c of o[config.childrenList]) {
        adaptToChildrenList(c)
      }
    }
  }

  return tree
}

/**
 * @param {Function} func
 * @param {number} wait
 * @param {boolean} immediate
 * @return {*}
 */
export function debounce(func, wait, immediate) {
  let timeout, args, context, timestamp, result

  const later = function() {
    // 据上一次触发时间间隔
    const last = +new Date() - timestamp

    // 上次被包装函数被调用时间间隔 last 小于设定时间间隔 wait
    if (last < wait && last > 0) {
      timeout = setTimeout(later, wait - last)
    } else {
      timeout = null
      // 如果设定为immediate===true，因为开始边界已经调用过了此处无需调用
      if (!immediate) {
        result = func.apply(context, args)
        if (!timeout) context = args = null
      }
    }
  }

  return function(...args) {
    context = this
    timestamp = +new Date()
    const callNow = immediate && !timeout
    // 如果延时不存在，重新设定延时
    if (!timeout) timeout = setTimeout(later, wait)
    if (callNow) {
      result = func.apply(context, args)
      context = args = null
    }

    return result
  }
}

/**
 * 设置时间选择器默认时间
 */
export function defaultDate(day) {
  const d = new Date()
  let curr_date = d.getDate()
  let curr_month = d.getMonth() + 1
  const curr_year = d.getFullYear()
  String(curr_month).length < 2
    ? (curr_month = '0' + curr_month)
    : curr_month
  String(curr_date).length < 2 ? (curr_date = '0' + curr_date) : curr_date

  const myDate = new Date() // 当前日期
  const dd = new Date(myDate)
  let befor_date = dd.setDate(dd.getDate() - day) // 当前日期减day天
  String(befor_date).length < 2
    ? (befor_date = '0' + befor_date)
    : befor_date
  const begin = dateTimeFormat(befor_date, 'Y-m-d')
  const end = curr_year + '-' + curr_month + '-' + curr_date
  return [begin, end] // 将值设置给插件绑定的数据
}

/**
 * 格式化时间
 */
export function addOneDay(date) {
  const dd = new Date(date)
  return dateTimeFormat(dd.setDate(dd.getDate() + 1), 'Y-m-d')
}

/**
 * 格式化日期时间
 */
export function dateTimeFormat(time, format) {
  const t = new Date(time)
  const year = t.getFullYear()
  // 由于 getMonth 返回值会比正常月份小 1
  let month = t.getMonth() + 1
  let day = t.getDate()
  let hours = t.getHours()
  let minutes = t.getMinutes()
  let seconds = t.getSeconds()
  month = month > 9 ? month : `0${month}`
  day = day > 9 ? day : `0${day}`
  hours = hours > 9 ? hours : `0${hours}`
  minutes = minutes > 9 ? minutes : `0${minutes}`
  seconds = seconds > 9 ? seconds : `0${seconds}`
  const hash = {
    Y: year,
    m: month,
    d: day,
    h: hours,
    i: minutes,
    s: seconds
  }
  return format.replace(/\w/g, (o) => {
    return hash[o]
  })
}

/**
 * 格式化时间
 */
// export function timeFormat(time) {
//   const t = new Date(time)
//   // 日期格式
//   const format = 'h:i'
//   const year = t.getFullYear()
//   // 由于 getMonth 返回值会比正常月份小 1
//   let month = t.getMonth() + 1
//   let day = t.getDate()
//   let hours = t.getHours()
//   let minutes = t.getMinutes()
//   let seconds = t.getSeconds()
//   month = month > 9 ? month : `0${month}`
//   day = day > 9 ? day : `0${day}`
//   hours = hours > 9 ? hours : `0${hours}`
//   minutes = minutes > 9 ? minutes : `0${minutes}`
//   seconds = seconds > 9 ? seconds : `0${seconds}`
//   const hash = {
//     Y: year,
//     m: month,
//     d: day,
//     h: hours,
//     i: minutes,
//     s: seconds
//   }
//   return format.replace(/\w/g, (o) => {
//     return hash[o]
//   })
// }

/**
 * 系统分类颜色
 */
export function classificationColorHandler(id) {
  switch (id) {
    case 1:
      return {
        color: '#626c91',
        backgroundColor: '#f4f4f5',
        borderColor: '#e9e9eb',
        marginRight: '5px'
      }
    case 2:
      return {
        color: '#3fb1e3',
        backgroundColor: '#ecf5ff',
        borderColor: '#d9ecff',
        marginRight: '5px'
      }
    case 3:
      return {
        color: '#d95850',
        backgroundColor: '#fdf6ec',
        borderColor: '#faecd8',
        marginRight: '5px'
      }
    case 4:
      return {
        color: '#a0a7e6',
        backgroundColor: '#f1ebf9',
        borderColor: '#eae9eb',
        marginRight: '5px'
      }
    case 5:
      return {
        color: '#82cc54',
        backgroundColor: '#f0f9eb',
        borderColor: '#e1f3d8',
        marginRight: '5px'
      }
    case 6:
      return {
        color: '#60bbda',
        backgroundColor: '#f0fbfe',
        borderColor: '#e2f7fd',
        marginRight: '5px'
      }
    case 7:
      return {
        color: '#2676b7',
        backgroundColor: '#eef9ff',
        borderColor: '#f7f9fa',
        marginRight: '5px'
      }
    case 8:
      return {
        color: '#4e70dc',
        backgroundColor: '#f3f4f6',
        borderColor: '#e2e8fd',
        marginRight: '5px'
      }
  }
}

/**
 * Check if an element has a class
 * @param {HTMLElement} ele
 * @param {string} cls
 * @returns {boolean}
 */
export function hasClass(ele, cls) {
  return !!ele.className.match(new RegExp('(\\s|^)' + cls + '(\\s|$)'))
}

/**
 * Add class to element
 * @param {HTMLElement} ele
 * @param {string} cls
 */
export function addClass(ele, cls) {
  if (!hasClass(ele, cls)) ele.className += ' ' + cls
}

/**
 * Remove class from element
 * @param {HTMLElement} ele
 * @param {string} cls
 */
export function removeClass(ele, cls) {
  if (hasClass(ele, cls)) {
    const reg = new RegExp('(\\s|^)' + cls + '(\\s|$)')
    ele.className = ele.className.replace(reg, ' ')
  }
}

// 判断早中晚
export function checkLoginTime() {
  let loginTime
  const d = new Date()
  const time = d.getHours()
  if (time >= 0 && time < 6) {
    loginTime = '凌晨'
  } else if (time >= 6 && time < 12) {
    loginTime = '上午'
  } else if (time >= 12 && time < 13) {
    loginTime = '中午'
  } else if (time >= 13 && time < 18) {
    loginTime = '下午'
  } else {
    loginTime = '晚上'
  }
  return loginTime
}

export function strToHTML(str) {
  const dom = document.createElement('div')
  dom.innerHTML = str
  return dom.getElementsByClassName('viewerContent')[0].innerText
}

// 数据合并
export function mergeRecursive(source, target) {
  for (const p in target) {
    try {
      if (target[p].constructor === Object) {
        source[p] = mergeRecursive(source[p], target[p])
      } else {
        source[p] = target[p]
      }
    } catch (e) {
      source[p] = target[p]
    }
  }
  return source
}

export function splitDiagramMap(data) {
  const result = []
  data.forEach((item) => {
    const keys = Object.keys(item[0])
    if (keys.length > 2) {
      const index = result.length
      for (let i = 0; i < keys.length - 1; i++) {
        result.push([])
      }
      item.forEach((obj) => {
        let obj_index = 0
        keys.forEach((key) => {
          if (key !== 'tmstamp') {
            const newObj = {
              tmstamp: obj.tmstamp
            }
            newObj[key] = obj[key]
            result[index + obj_index].push(newObj)
            obj_index++
          }
        })
      })
    } else {
      result.push(item)
    }
  })
  return result
}

export function gradientHandler(data) {
  const paramsNameList = []
  const result = []
  data.data.forEach((item, index) => {
    item.forEach((obj) => {
      const objList = []
      const keys = Object.keys(obj)
      keys.forEach((key) => {
        if (key !== 'tmstamp') {
          const newObj = {}
          newObj.height = key.match(/\d+/g).join('.')
          newObj[obj.tmstamp] = obj[key]
          objList.push(newObj)
        }
      })
      paramsNameList.push(data.params[index] + '_' + obj.tmstamp)
      result.push(objList)
    })
  })
  return [result, paramsNameList]
}

export function formatDateTime(dateTimeString) {
  const date = new Date(dateTimeString)

  const month = (date.getMonth() + 1).toString().padStart(2, '0')
  const day = date.getDate().toString().padStart(2, '0')
  const hours = date.getHours().toString().padStart(2, '0')
  const minutes = date.getMinutes().toString().padStart(2, '0')

  return `${month}-${day} ${hours}:${minutes}`
}

export function convertKeysToLowerCase(array) {
  return array.map(obj => {
    return Object.keys(obj).reduce((result, key) => {
      result[key.toLowerCase()] = obj[key]
      return result
    }, {})
  })
}

export function linearCorrelation(arr) {
  // 初始化变量
  const n = arr.length
  let sum1 = 0
  let sum2 = 0
  let sum1Sq = 0
  let sum2Sq = 0
  let productSum = 0

  // 计算均值和平方和
  for (let i = 0; i < n; i++) {
    sum1 += arr[i][0]
    sum2 += arr[i][1]
    sum1Sq += arr[i][0] * arr[i][0]
    sum2Sq += arr[i][1] * arr[i][1]
    productSum += arr[i][0] * arr[i][1]
  }

  // 计算标准差
  const stdDev1 = Math.sqrt((sum1Sq - (sum1 * sum1) / n) / (n - 1))
  const stdDev2 = Math.sqrt((sum2Sq - (sum2 * sum2) / n) / (n - 1))

  // 计算协方差
  const covariance = (productSum - sum1 * sum2 / n) / (n - 1)

  // 计算皮尔逊相关系数（r）
  const correlation = covariance / (stdDev1 * stdDev2)

  // 计算R²值
  const rSquared = correlation * correlation

  return { correlation, rSquared }
}
