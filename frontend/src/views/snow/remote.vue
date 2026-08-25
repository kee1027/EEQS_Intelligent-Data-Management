<template>
    <div class="snow-remote">
        <div class="map-wrapper">
            <div id="snow-map-container"></div>
            <div class="map-controls">
                <div class="north-arrow">N</div>
            </div>
        </div>
    </div>
</template>

<script>
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import 'leaflet.chinatmsproviders';
import proj4 from 'proj4';

// 定义 LCC 投影
proj4.defs('LCC', '+proj=lcc +lat_1=30 +lat_2=60 +lat_0=0 +lon_0=100 +x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs');

// 修复 Leaflet 默认图标路径问题
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
    iconRetinaUrl: require('leaflet/dist/images/marker-icon-2x.png'),
    iconUrl: require('leaflet/dist/images/marker-icon.png'),
    shadowUrl: require('leaflet/dist/images/marker-shadow.png'),
});

export default {
    name: 'SnowRemote',
    data() {
        return {
            map: null,
        };
    },
    mounted() {
        setTimeout(this.initMap, 100);
    },
    beforeDestroy() {
        if (this.map) {
            this.map.remove();
        }
    },
    methods: {
        async initMap() {
            this.map = L.map('snow-map-container', {
                center: [34.0, 108.0],
                zoom: 3,
                zoomControl: false,
            });

            // 使用高德卫星图作为底图
            L.tileLayer.chinaProvider('GaoDe.Satellite.Map', { maxZoom: 18, attribution: '高德地图' }).addTo(this.map);
            L.tileLayer.chinaProvider('GaoDe.Satellite.Annotion', { maxZoom: 18 }).addTo(this.map);

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

                // 将 LCC 投影坐标转换为 WGS84 经纬度
                data.features.forEach(feature => {
                    const coords = feature.geometry.coordinates[0];
                    const convertedCoords = coords.map(point => {
                        const [lon, lat] = proj4('LCC', 'WGS84', point);
                        return [lon, lat];
                    });
                    feature.geometry.coordinates[0] = convertedCoords;
                });

                const basinLayer = L.geoJSON(data, {
                    style: {
                        color: '#0EA5E9',
                        weight: 2,
                        opacity: 0.8,
                        fillColor: '#CBD5E1',
                        fillOpacity: 0.3
                    }
                }).addTo(this.map);

                this.$nextTick(() => {
                    this.map.fitBounds(basinLayer.getBounds(), { padding: [50, 50] });
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

                    L.geoJSON(data, {
                        pointToLayer: (feature, latlng) => {
                            const marker = L.marker(latlng, { icon: createIcon(type.icon, feature.properties.name) });

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
                            return marker;
                        }
                    }).addTo(this.map);

                } catch (error) {
                    console.error(`Error loading ${type.name} data:`, error);
                }
            });
        }
    }
}
</script>

<style scoped>
.snow-remote {
    padding: 20px;
    height: calc(100vh - 84px);
}

.map-wrapper {
    position: relative;
    width: 100%;
    height: 100%;
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

#snow-map-container {
    width: 100%;
    height: 100%;
    min-height: 600px;
}

.map-controls {
    position: absolute;
    top: 10px;
    right: 10px;
    z-index: 1000;
}

.north-arrow {
    width: 30px;
    height: 30px;
    background: white;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
}
</style>

<style>
/* 全局样式，用于 Leaflet 弹出框 */
.station-popup h4 {
    margin: 0 0 10px 0;
    color: #333;
    font-size: 14px;
}

.station-popup p {
    margin: 5px 0;
    font-size: 12px;
    color: #666;
}

.custom-div-icon {
    background: transparent;
    border: none;
}

.icon-container {
    display: flex;
    flex-direction: column;
    align-items: center;
}

.station-icon {
    width: 24px;
    height: 24px;
}

.station-name {
    font-size: 10px;
    color: #333;
    background: rgba(255, 255, 255, 0.8);
    padding: 2px 4px;
    border-radius: 3px;
    white-space: nowrap;
}
</style>
