/**
 * @param {string} path
 * @returns {Boolean}
 */
export function isExternal(path) {
  return /^(https?:|mailto:|tel:)/.test(path)
}

// 检查用户名
export function validUserName(str) {
  const regUsername = /^[a-zA-Z][@a-zA-Z0-9-]{3,16}$/
  return regUsername.test(str)
}

// 检查用户名或邮箱
export function validUserInfo(str) {
  const regUsername = /^[a-zA-Z][@a-zA-Z0-9-]{3,16}$/
  const regEmail = /^([a-zA-Z0-9_-])+@([a-zA-Z0-9_-])+(\.[a-zA-Z0-9_-])+/
  return regUsername.test(str) || regEmail.test(str)
}

// 检查邮箱
export function validEmail(str) {
  const regEmail = /^([a-zA-Z0-9_-])+@([a-zA-Z0-9_-])+(\.[a-zA-Z0-9_-])+/
  return regEmail.test(str)
}

// 检查角色编码
export function validRoleCode(str) {
  const regRoleCode = /[a-zA-z]{2,10}$/
  return regRoleCode.test(str)
}

// 检查角色名
export function validRoleName(str) {
  const regRoleName = /^[\u4e00-\u9fa5]{3,10}/
  return regRoleName.test(str)
}
