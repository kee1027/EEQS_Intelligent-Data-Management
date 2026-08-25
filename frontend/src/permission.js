import router from './router'
import store from './store'
import { Message } from 'element-ui'
// const { Message } = ELEMENT
import NProgress from 'nprogress' // progress bar
import 'nprogress/nprogress.css' // progress bar style
import { getToken } from '@/utils/auth' // get token from cookie
import getPageTitle from '@/utils/get-page-title'

NProgress.configure({ showSpinner: false }) // NProgress Configuration

const whiteList = ['/login', '/is_mobile'] // no redirect whitelist
const is_mobile = /phone|pod|iPhone|iPod|ios|Android|Mobile|BlackBerry|IEMobile|MQQBrowser|JUC|Fennec|wOSBrowser|BrowserNG|WebOS|Symbian|Windows Phone/i.test(navigator.userAgent.toLowerCase())


router.afterEach(() => {
  // finish progress bar
  NProgress.done()
})
