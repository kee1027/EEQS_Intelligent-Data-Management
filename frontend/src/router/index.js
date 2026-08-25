import Vue from 'vue'
import Router from 'vue-router'

Vue.use(Router)

import Layout from '@/layout'

export const constantRoutes = [
  {
    path: '/',
    component: Layout,
    redirect: '/dashboard',
    children: [{
      path: 'dashboard',
      name: 'Dashboard',
      component: () => import('@/views/monitoring-dashboard/index.vue'),
      meta: { title: '首页', icon: 'dashboard' }
    }]
  },
  {
    path: '/login',
    component: () => import('@/views/login/index.vue'),
    hidden: true
  },
  {
    path: '/weather',
    component: Layout,
    redirect: '/weather/sites',
    name: 'Weather',
    meta: { title: '气象', icon: 'weather' },
    children: [
      {
        path: 'sites',
        name: 'WeatherSites',
        component: { render: h => h('router-view') },
        redirect: '/weather/sites/kuwei',
        meta: { title: '站点', icon: 'station', alwaysShow: true },
        children: [
          { path: 'kuwei', name: 'WeatherKuwei', component: () => import('@/views/sites/StationDetail.vue'), meta: { title: '库威积雪水文观测场', stationId: 'KW' } },
          { path: 'kayier', name: 'WeatherKayier', component: () => import('@/views/sites/StationDetail.vue'), meta: { title: '喀依尔综合观测系统', stationId: 'KYE' } },
          { path: 'jinge', name: 'WeatherJinge', component: () => import('@/views/sites/StationDetail.vue'), meta: { title: '金格观测系统', stationId: 'JG' } },
          { path: 'akesala', name: 'WeatherAkesala', component: () => import('@/views/sites/StationDetail.vue'), meta: { title: '阿克萨拉观测场', stationId: 'AKS' } },
          { path: 'keketuohai', name: 'WeatherKeketuohai', component: () => import('@/views/sites/StationDetail.vue'), meta: { title: '可可托海滑雪场站', stationId: 'KKTH' } },
          { path: 'kekesuli', name: 'WeatherKekesuli', component: () => import('@/views/sites/StationDetail.vue'), meta: { title: '可可苏里气象站', stationId: 'KKSLM' } },
          { path: 'senlin', name: 'WeatherSenlin', component: () => import('@/views/sites/StationDetail.vue'), meta: { title: '森林站', stationId: 'SL' } }
        ]
      },
      {
        path: 'history',
        name: 'WeatherHistory',
        component: () => import('@/views/weather/history.vue'),
        meta: { title: '历史', icon: 'history' }
      },
      {
        path: 'forecast',
        name: 'WeatherForecast',
        component: () => import('@/views/weather/forecast.vue'),
        meta: { title: '预报', icon: 'analysis' }
      }
    ]
  },
  {
    path: '/snow',
    component: Layout,
    redirect: '/snow/sites',
    name: 'Snow',
    meta: { title: '积雪动态', icon: 'snow' },
    children: [
      {
        path: 'sites',
        name: 'SnowSites',
        component: { render: h => h('router-view') },
        redirect: '/snow/sites/kuwei',
        meta: { title: '站点', icon: 'station', alwaysShow: true },
        children: [
          { path: 'kuwei', name: 'SnowKuwei', component: () => import('@/views/sites/StationDetail.vue'), meta: { title: '库威积雪水文观测场', stationId: 'KW' } },
          { path: 'kayier', name: 'SnowKayier', component: () => import('@/views/sites/StationDetail.vue'), meta: { title: '喀依尔综合观测系统', stationId: 'KYE' } },
          { path: 'jinge', name: 'SnowJinge', component: () => import('@/views/sites/StationDetail.vue'), meta: { title: '金格观测系统', stationId: 'JG' } },
          { path: 'akesala', name: 'SnowAkesala', component: () => import('@/views/sites/StationDetail.vue'), meta: { title: '阿克萨拉观测场', stationId: 'AKS' } },
          { path: 'keketuohai', name: 'SnowKeketuohai', component: () => import('@/views/sites/StationDetail.vue'), meta: { title: '可可托海滑雪场站', stationId: 'KKTH' } },
          { path: 'kekesuli', name: 'SnowKekesuli', component: () => import('@/views/sites/StationDetail.vue'), meta: { title: '可可苏里降雪站', stationId: 'KKSLS' } },
          { path: 'senlin', name: 'SnowSenlin', component: () => import('@/views/sites/StationDetail.vue'), meta: { title: '森林站', stationId: 'SL' } }
        ]
      },
      {
        path: 'remote',
        name: 'SnowRemote',
        component: () => import('@/views/snow/remote.vue'),
        meta: { title: '遥感', icon: 'earth' }
      }
    ]
  },
  {
    path: '/hydrology',
    component: Layout,
    children: [{
      path: 'index',
      component: () => import('@/views/hydrology/index.vue'),
      meta: { title: '实时水文' }
    }]
  },
  {
    path: '/water-forecast',
    component: Layout,
    redirect: '/water-forecast/ten-days',
    name: 'WaterForecast',
    meta: { title: '水资源预报', icon: 'analysis' },
    children: [
      { path: 'ten-days', name: 'WaterForecastTenDays', component: () => import('@/views/water-forecast/ten-days.vue'), meta: { title: '十天', icon: 'calendar' } },
      { path: 'month', name: 'WaterForecastMonth', component: () => import('@/views/water-forecast/month.vue'), meta: { title: '月', icon: 'calendar' } },
      { path: 'year', name: 'WaterForecastYear', component: () => import('@/views/water-forecast/year.vue'), meta: { title: '年', icon: 'calendar' } }
    ]
  },
  {
    path: '/flood-warning',
    component: Layout,
    children: [{
      path: '',
      name: 'FloodWarning',
      component: () => import('@/views/flood-warning/index.vue'),
      meta: { title: '洪水预警', icon: 'warning' }
    }]
  },
  {
    path: '/manual-data',
    component: Layout,
    children: [{
      path: '',
      name: 'ManualData',
      component: () => import('@/views/manual-data/index.vue'),
      meta: { title: '数据录入', icon: 'el-icon-edit' }
    }]
  },
  {
    path: '/ai-assistant',
    component: Layout,
    children: [{
      path: '',
      name: 'AiAssistant',
      component: () => import('@/views/ai-assistant/index.vue'),
      meta: { title: '智能问答', icon: 'el-icon-chat-dot-round' }
    }]
  },
  {
    path: '/404',
    component: () => import('@/views/404'),
    hidden: true
  },
  {
    path: '/is_mobile',
    component: () => import('@/views/is-mobile'),
    hidden: true
  }
]

export const anyRoutes = { path: '*', redirect: '/404', hidden: true }

const createRouter = () => new Router({
  scrollBehavior: () => ({ y: 0 }),
  routes: constantRoutes
})

const router = createRouter()

export function resetRouter() {
  const newRouter = createRouter()
  router.matcher = newRouter.matcher
}

router.$addRoutes = (params) => {
  router.matcher = new Router({ mode: 'hash' }).matcher
  router.addRoutes(params)
}
export default router
