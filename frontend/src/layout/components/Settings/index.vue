<template>
  <div class="drawer-container">
    <div>
      <div class="setting-drawer-content">
        <el-divider>导航栏模式</el-divider>
        <div class="setting-drawer-block-checbox">
          <el-tooltip effect="dark" content="左侧菜单模式" placement="bottom">
            <div class="setting-drawer-block-checbox-item" @click="handleMenuPosition(true)">
              <div class="setting-menu-type picker-left" />
              <div v-if="menuInLeft" class="setting-drawer-block-checbox-selectIcon" style="display: block;">
                <i aria-label="图标: check" class="anticon anticon-check">
                  <svg viewBox="64 64 896 896" data-icon="check" width="1em" height="1em" aria-hidden="true" focusable="false" class="">
                    <path d="M912 190h-69.9c-9.8 0-19.1 4.5-25.1 12.2L404.7 724.5 207 474a32 32 0 0 0-25.1-12.2H112c-6.7 0-10.4 7.7-6.3 12.9l273.9 347c12.8 16.2 37.4 16.2 50.3 0l488.4-618.9c4.1-5.1.4-12.8-6.3-12.8z" />
                  </svg>
                </i>
              </div>
            </div>
          </el-tooltip>
          <el-tooltip effect="dark" content="顶部菜单模式" placement="bottom">
            <div class="setting-drawer-block-checbox-item" @click="handleMenuPosition(false)">
              <div class="setting-menu-type picker-top" />
              <div v-if="!menuInLeft" class="setting-drawer-block-checbox-selectIcon" style="display: block;">
                <i aria-label="图标: check" class="anticon anticon-check">
                  <svg viewBox="64 64 896 896" data-icon="check" width="1em" height="1em" aria-hidden="true" focusable="false" class="">
                    <path d="M912 190h-69.9c-9.8 0-19.1 4.5-25.1 12.2L404.7 724.5 207 474a32 32 0 0 0-25.1-12.2H112c-6.7 0-10.4 7.7-6.3 12.9l273.9 347c12.8 16.2 37.4 16.2 50.3 0l488.4-618.9c4.1-5.1.4-12.8-6.3-12.8z" />
                  </svg>
                </i>
              </div>
            </div>
          </el-tooltip>
        </div>
        <el-divider>主题色</el-divider>
        <ul class="theme-color">
          <li v-for="(item, index) in themeColors" :key="index" :style="getThemeColorStyle(item.color)" @click="setLayoutThemeColor(item.themeColor)">
            <i v-if="item.themeColor === sideTheme" aria-label="图标: check" class="anticon anticon-check">
              <svg viewBox="64 64 896 896" data-icon="check" width="1em" height="1em" aria-hidden="true" focusable="false" class="svg-icon">
                <path :style="getPathColor" d="M912 190h-69.9c-9.8 0-19.1 4.5-25.1 12.2L404.7 724.5 207 474a32 32 0 0 0-25.1-12.2H112c-6.7 0-10.4 7.7-6.3 12.9l273.9 347c12.8 16.2 37.4 16.2 50.3 0l488.4-618.9c4.1-5.1.4-12.8-6.3-12.8z" />
              </svg>
            </i>
          </li>
        </ul>
        <el-button size="small" type="primary" plain icon="el-icon-document-add" @click="saveSetting">保存配置</el-button>
        <el-button size="small" plain icon="el-icon-refresh" @click="resetSetting">重置配置</el-button>
      </div>
    </div>
  </div></template>

<script>
import variables from '@/styles/variables.scss'
import { mapGetters } from 'vuex'

export default {
  data() {
    return {
      menuInLeft: this.$store.state.settings.menuInLeft,
      themeColors: []
    }
  },
  computed: {
    ...mapGetters(['sideTheme']),
    getThemeColorStyle() {
      return (color) => {
        return {
          backgroundColor: color
        }
      }
    },
    getPathColor() {
      return {
        // 浅色主题下选中的主题色的对勾颜色为黑色
        fill: this.sideTheme === 'light' ? '#000' : '#fff'
      }
    }
  },
  created() {
    const themes = {}
    for (const key in variables) {
      const theme = key.split('-')[0]
      if (!themes[theme]) {
        themes[theme] = {
          color: variables[`${theme}-menu-bg`],
          themeColor: theme
        }
      }
    }
    this.themeColors = Object.values(themes)
  },
  methods: {
    setLayoutThemeColor(themeColor) {
      Object.keys(variables).forEach(key => {
        if (key.startsWith(themeColor)) {
          const variableName = `${key.replace(themeColor, '-')}`
          const variableValue = variables[key]
          document.documentElement.style.setProperty(variableName, variableValue)
        }
      })
      this.$store.dispatch('settings/changeSetting', {
        sideTheme: themeColor,
        menuBg: getComputedStyle(document.documentElement).getPropertyValue('--menu-bg'),
        menuText: getComputedStyle(document.documentElement).getPropertyValue('--menu-text'),
        menuActiveText: getComputedStyle(document.documentElement).getPropertyValue('--menu-active-text')
      })
    },
    handleMenuPosition(val) {
      this.$store.dispatch('settings/changeSetting', { menuInLeft: val })
      this.$store.dispatch('app/openSideBar', { withoutAnimation: true })
      this.menuInLeft = val
    },
    saveSetting() {
      this.$modal.loading('正在保存到本地，请稍候...')
      this.$cache.local.set(
        'layout-setting',
        `{
            "menuInLeft":${this.menuInLeft},
            "sideTheme":"${this.sideTheme}"
          }`
      )
      setTimeout(() => { this.$modal.closeLoading() }, 1000)
    },
    resetSetting() {
      this.$modal.loading('正在清除设置缓存并刷新，请稍候...')
      this.$cache.local.remove('layout-setting')
      setTimeout(() => { window.location.reload() }, 1000)
    }
  }
}
</script>

<style lang="scss" scoped>
  .setting-drawer-content {
    .setting-drawer-title {
      margin-bottom: 12px;
      color: rgba(0, 0, 0, .85);
      font-size: 14px;
      line-height: 22px;
      font-weight: bold;
    }

    .setting-drawer-block-checbox {
      display: flex;
      align-items: center;
      justify-content: center;
      margin-top: 10px;
      margin-bottom: 20px;

      .setting-menu-type {
        position: relative;
        width: 56px;
        height: 48px;
        margin-right: 16px;
        overflow: hidden;
        cursor: pointer;
        background-color: #f0f2f5;
        border-radius: 4px;
        box-shadow: 0 1px 2.5px #0000002e;
      }
      .setting-menu-type.picker-left:before {
        position: absolute;
        content: "";
        top: 0;
        left: 0;
        z-index: 1;
        width: 33%;
        height: 100%;
        background-color: #273352;
        border-radius: 4px 0 0 4px;
      }
      .setting-menu-type.picker-left:after {
        position: absolute;
        content: "";
        top: 0;
        left: 0;
        width: 100%;
        height: 25%;
        background-color: #fff;
      }
      .setting-menu-type.picker-top:after {
        position: absolute;
        content: "";
        top: 0;
        left: 0;
        width: 100%;
        height: 25%;
        background-color: #273352;
      }
      .setting-drawer-block-checbox-item {
        position: relative;
        margin-right: 16px;
        border-radius: 2px;
        cursor: pointer;

        .setting-drawer-block-checbox-selectIcon {
          position: absolute;
          top: 0;
          right: 0;
          width: 100%;
          height: 100%;
          padding-top: 15px;
          padding-left: 24px;
          color: #1890ff;
          font-weight: 700;
          font-size: 14px;
        }
      }
    }
  }
  .drawer-container {
    padding: 24px;
    font-size: 14px;
    line-height: 1.5;
    word-wrap: break-word;

    .drawer-title {
      margin-bottom: 12px;
      color: rgba(0, 0, 0, .85);
      font-size: 14px;
      line-height: 22px;
    }

    .drawer-item {
      color: rgba(0, 0, 0, .65);
      font-size: 14px;
      padding: 12px 0;
    }

    .drawer-switch {
      float: right
    }
  }
  .theme-color {
    display: flex;
    justify-content: center;
    width: 100%;
    height: 40px;
    padding: 0;

    li {
      float: left;
      width: 20px;
      height: 20px;
      margin-top: 8px;
      margin-right: 8px;
      font-weight: 700;
      text-align: center;
      cursor: pointer;
      border-radius: 2px;
      list-style-type: none;

      &:nth-child(2) {
        border: 1px solid #ddd;
      }
      .anticon-check .svg-icon path {
        fill: transparent;
      }
    }
  }
</style>
