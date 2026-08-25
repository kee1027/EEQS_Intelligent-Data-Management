import kwPhoto from '@/assets/站点实况图/库威气象站.jpg'
import kyePhoto from '@/assets/站点实况图/库威水文站.jpg'
import kksPhoto from '@/assets/站点实况图/可可苏里气象站.jpg'
import kkslsPhoto from '@/assets/站点实况图/可可苏里降雪站.jpg'
import kkthPhoto from '@/assets/站点实况图/可可托海滑雪场.jpg'

export const STATION_CONFIG = {
  KW: {
    name: '库威积雪水文观测场',
    altitude: 1475,
    type: '综合观测场',
    longitude: 89.39,
    latitude: 47.21,
    apiName: 'KW',
    fields: 'standard',
    photo: kwPhoto
  },
  KYE: {
    name: '喀依尔综合观测系统',
    altitude: 1800,
    type: '综合观测场',
    longitude: 89.44,
    latitude: 47.42,
    apiName: 'KYE',
    fields: 'standard',
    photo: kyePhoto
  },
  JG: {
    name: '金格观测系统',
    altitude: 1600,
    type: '综合观测场',
    longitude: 89.30,
    latitude: 47.35,
    apiName: 'JG',
    fields: 'standard'
  },
  AKS: {
    name: '阿克萨拉观测场',
    altitude: 1550,
    type: '观测场',
    longitude: 89.25,
    latitude: 47.25,
    apiName: 'AKS',
    fields: 'standard'
  },
  KKTH: {
    name: '可可托海滑雪场站',
    altitude: 1200,
    type: '滑雪场站',
    longitude: 89.50,
    latitude: 47.50,
    apiName: 'KKTH',
    fields: 'standard',
    photo: kkthPhoto
  },
  KKS: {
    name: '可可苏里气象站',
    altitude: 1350,
    type: '气象站',
    longitude: 89.20,
    latitude: 47.10,
    apiName: 'KKSLM',
    fields: 'standard',
    photo: kksPhoto
  },
  KKSLS: {
    name: '可可苏里降雪站',
    altitude: 1350,
    type: '降雪站',
    longitude: 89.20,
    latitude: 47.10,
    apiName: 'KKSLS',
    fields: 'snow',
    photo: kkslsPhoto
  },
  SL: {
    name: '森林站',
    altitude: 1600,
    type: '观测场',
    longitude: 89.35,
    latitude: 47.30,
    apiName: 'SL',
    fields: 'standard'
  }
}

export const STANDARD_FIELDS = [
  { key: 'snow_depth', label: '积雪深度', unit: 'cm' },
  { key: 'ta', label: '气温', unit: '°C' },
  { key: 'snow_density', label: '雪密度', unit: 'kg/m³' },
  { key: 'swe', label: '雪水当量', unit: 'mm' }
]

export const SNOW_FIELDS = [
  { key: 'ush9_snow_depth', label: 'USH-9雪深', unit: 'cm' },
  { key: 'oblique_ice_content', label: '斜向观测带冰含量', unit: '%' },
  { key: 'oblique_water_content', label: '斜向观测带水含量', unit: '%' },
  { key: 'oblique_snow_density', label: '斜向观测带雪密度', unit: 'kg/m³' },
  { key: 'horizontal_ice_content', label: '水平观测带冰含量', unit: '%' },
  { key: 'horizontal_water_content', label: '水平观测带水含量', unit: '%' },
  { key: 'horizontal_snow_density', label: '水平观测带雪密度', unit: 'kg/m³' },
  { key: 'snow_drift_flux_100cm', label: '100cm风吹雪平均通量', unit: 'g/(m²·s)' },
  { key: 'snow_drift_flux_200cm', label: '200cm风吹雪平均通量', unit: 'g/(m²·s)' },
  { key: 'wind_speed_100cm', label: '100cm平均风速', unit: 'm/s' },
  { key: 'wind_speed_200cm', label: '200cm平均风速', unit: 'm/s' }
]

export const STANDARD_CHARTS = [
  { ref: 'airTempChart', title: '气温 (°C)', field: 'ta', color: '#2c7be5' },
  { ref: 'airHumidityChart', title: '空气相对湿度 (%)', field: 'rh', color: '#00d27a' },
  { ref: 'windSpeedChart', title: '风速 (m/s)', field: 'ws', color: '#f5a623' },
  { ref: 'soilMoistureChart', title: '土壤水分 (%)', multi: true, fields: ['vwc_soil_10cm', 'vwc_soil_20cm', 'vwc_soil_40cm', 'vwc_soil_60cm', 'vwc_soil_100cm'], colors: ['#00d27a', '#00b87a', '#009f7a', '#00856a', '#006a5a'] },
  { ref: 'soilTempChart', title: '土壤温度 (°C)', multi: true, fields: ['t_soil_10cm', 't_soil_20cm', 't_soil_40cm', 't_soil_60cm', 't_soil_100cm'], colors: ['#e63757', '#d63055', '#c62845', '#b62035', '#a61825'] }
]

export const SNOW_CHARTS = [
  { ref: 'ush9Chart', title: 'USH-9雪深 (cm)', field: 'ush9_snow_depth', color: '#2c7be5' },
  { ref: 'obliqueIceChart', title: '斜向观测带冰含量 (%)', field: 'oblique_ice_content', color: '#00d27a' },
  { ref: 'obliqueWaterChart', title: '斜向观测带水含量 (%)', field: 'oblique_water_content', color: '#f5a623' },
  { ref: 'horizontalIceChart', title: '水平观测带冰含量 (%)', field: 'horizontal_ice_content', color: '#e63757' },
  { ref: 'horizontalWaterChart', title: '水平观测带水含量 (%)', field: 'horizontal_water_content', color: '#6b5ce7' },
  { ref: 'snowDriftFluxChart', title: '风吹雪平均通量', multi: true, fields: ['snow_drift_flux_100cm', 'snow_drift_flux_200cm'], colors: ['#2c7be5', '#00d27a'] },
  { ref: 'windSpeedChart', title: '平均风速 (m/s)', multi: true, fields: ['wind_speed_100cm', 'wind_speed_200cm'], colors: ['#f5a623', '#e63757'] }
]
