<template>
  <div class="card-container center-map">
    <div id="map-container"></div>
    <div class="map-controls">
      <div class="north-arrow">N</div>
    </div>
  </div>
</template>

<script>
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import 'leaflet.chinatmsproviders';
import proj4 from 'proj4';

// 定义 LCC 投影 (WGS84 是 proj4 内置的，无需定义)
proj4.defs('LCC', '+proj=lcc +lat_1=30 +lat_2=60 +lat_0=0 +lon_0=100 +x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs');

// 修复 Leaflet 默认图标路径问题
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: require('leaflet/dist/images/marker-icon-2x.png'),
  iconUrl: require('leaflet/dist/images/marker-icon.png'),
  shadowUrl: require('leaflet/dist/images/marker-shadow.png'),
});

export default {
  name: 'CenterMap',
  data() {
    return {
      map: null,
    };
  },
  mounted() {
    // Delay map initialization to ensure container is ready
    setTimeout(this.initMap, 100);
  },
  beforeDestroy() {
    if (this.map) {
      this.map.remove();
    }
  },
  methods: {
    async initMap() {
      // 使用 Leaflet 初始化地图，设置初始视角为流域中心点
      this.map = L.map('map-container', {
        minZoom: 7,  // 切片的起始层级
        maxZoom: 14, // 切片的最大层级
        zoomControl: false
      }).setView([34.12, 102.45], 8);

      // 配置瓦片图层，使用 Django 后端提供的 XYZ 格式瓦片
      const tileUrl = '/api/tiles/default/{z}/{x}/{y}.png';
      L.tileLayer(tileUrl, {
        attribution: '© Basin Hydrology System'
      }).addTo(this.map);

      // 加载流域边界和站点数据
      await this.loadBasin();
      this.loadStations();

      L.control.scale({ position: 'bottomright' }).addTo(this.map);
      L.control.zoom({ position: 'topleft' }).addTo(this.map);
    },

    async loadBasin() {
      try {
        const response = await fetch('/json/output.geojson');
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();

        // 将 LCC 投影坐标转换为标准的 WGS84 经纬度
        data.features.forEach(feature => {
          const coords = feature.geometry.coordinates[0]; // 假设是单个多边形
          const convertedCoords = coords.map(point => {
            const [lon, lat] = proj4('LCC', 'WGS84', point);
            return [lon, lat]; // GeoJSON 标准格式是 [longitude, latitude]
          });
          feature.geometry.coordinates[0] = convertedCoords;
        });

        const basinLayer = L.geoJSON(data, {
          style: {
            color: '#000', // 边界改为黑色
            weight: 2,
            opacity: 0.8,
            fillColor: '#CBD5E1', // 浅灰地形底图
            fillOpacity: 0.3 // 恢复合理的填充透明度
          }
        }).addTo(this.map);

        // 确保图层渲染完成后再执行缩放，以避免时序问题
        this.$nextTick(() => {
          this.map.fitBounds(basinLayer.getBounds(), { padding: [50, 50] });
          // 在自动缩放后，获取当前缩放级别并减1，以达到"缩小一级"的效果
          const currentZoom = this.map.getZoom();
          this.map.setZoom(currentZoom - 1);
        });

      } catch (error) {
        console.error('Error loading basin GeoJSON:', error);
      }
    },

    loadStations() {
      const stationTypes = [
        { name: '水文站', url: '/json/水文站.geojson', icon: require('@/assets/水文站 - 已编辑.png') },
        { name: '水库', url: '/json/水库.geojson', icon: require('@/assets/水文站 - 已编辑.png') },
        { name: '积雪场', url: '/json/积雪场.geojson', icon: require('@/assets/水文站 - 已编辑.png') }
      ];

      const createIcon = (iconUrl, featureName) => {
        return L.divIcon({
          className: 'custom-div-icon',
          html: `<div class='icon-container'>
                   <img src='${iconUrl}' class='station-icon'/>
                   <span class='station-name'>${featureName}</span>
                 </div>`,
          iconSize: [80, 40],
          iconAnchor: [40, 40],
          popupAnchor: [0, -40]
        });
      };

      stationTypes.forEach(async (type) => {
        try {
          const response = await fetch(type.url);
          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }
          const data = await response.json();
          console.log(`Successfully fetched ${type.name} data:`, data);

          // Data is standard GeoJSON (WGS84), Leaflet handles it by default
          L.geoJSON(data, {
            pointToLayer: (feature, latlng) => {
              const marker = L.marker(latlng, { icon: createIcon(type.icon, feature.properties.name) });

              // Create popup content from feature properties
              const props = feature.properties;
              let popupContent = `<div class="station-popup"><h4>${props.NAME || type.name}</h4>`;
              for (const key in props) {
                if (Object.prototype.hasOwnProperty.call(props, key)) {
                  popupContent += `<p>${key}: ${props[key]}</p>`;
                }
              }
              popupContent += `</div>`;

              marker.bindPopup(popupContent);

              marker.on('mouseover', function () { this.openPopup(); });
              marker.on('mouseout', function () { this.closePopup(); });

              // 定义一个从站点名称到路由路径的映射
              const stationToRoute = {
                '库威积雪水文观测场': '/weather/sites/kuwei',
                '喀依尔综合观测系统': '/weather/sites/kayier',
                '金格观测系统': '/weather/sites/jinge',
                '阿克萨拉观测场': '/weather/sites/akesala',
                '可可托海滑雪场站': '/weather/sites/keketuohai',
                '可可苏里观测场': '/weather/sites/kekesuli',
                '森林站': '/weather/sites/senlin',
                // 预警站的路由
                "预警站1号": "/weather/sites/kuwei",
                "预警站2号": "/weather/sites/kayier",
                "预警站3号": "/weather/sites/jinge",
                "预警站4号": "/weather/sites/akesala",
              };

              // 为 marker 添加点击事件监听器
              marker.on('click', () => {
                const stationName = feature.properties.name;
                const routePath = stationToRoute[stationName];
                if (routePath) {
                  this.$router.push(routePath);
                } else {
                  console.warn(`No route found for station: ${stationName}`);
                }
              });

              return marker;
            }
          }).addTo(this.map);
        } catch (error) {
          console.error(`Error loading station GeoJSON for ${type.name}:`, error);
        }
      });
    },
  },
};
</script>

<style>
/* Using a global style tag as scoped styles can interfere with Leaflet popups */
.center-map {
  position: relative;
  overflow: hidden;
  /* Ensures child elements conform to rounded corners */
}

#map-container {
  width: 100%;
  height: 100%;
  background-color: #f5f2f0;
  /* A neutral background color */
}

.card-container {
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.08);
  padding: 0;
  /* Remove padding to make map fill the container */
}

.map-controls {
  position: absolute;
  top: 10px;
  left: 10px;
  z-index: 400;
  /* Above Leaflet layers */
}

.north-arrow {
  width: 30px;
  height: 30px;
  background-color: rgba(255, 255, 255, 0.8);
  border: 1px solid #ccc;
  border-radius: 4px;
  display: flex;
  justify-content: center;
  align-items: center;
  font-weight: bold;
}

.custom-div-icon {
  background: none;
  border: none;
}

.icon-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.station-icon {
  width: 25px;
  height: 25px;
}

.station-name {
  font-size: 12px;
  color: #fff;
  font-weight: bold;
  text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.7);
  white-space: nowrap;
}

.station-popup {
  font-family: sans-serif;
}

.station-popup h4 {
  margin: 0 0 8px;
  font-size: 14px;
}

.station-popup p {
  margin: 4px 0;
  font-size: 12px;
}
</style>
