<template>
  <div class="navbar" :style="topBackgroundColor">
    <hamburger v-if="menuInLeft" :is-active="sidebar.opened" class="hamburger-container" @toggleClick="toggleSideBar" />
    <breadcrumb v-if="menuInLeft" class="breadcrumb-container" />
    <div class="right-menu">
      <el-badge :value="warnLog" :hidden="warnLog === 0">
        <el-button size="mini" plain :type="warnLog === 0 ? 'primary' : 'danger'" circle icon="el-icon-message-solid" @click="jump()" />
      </el-badge>
      <el-dropdown>
        <div class="avatar-container">
          <img src="../../assets/truwel_logo.png" class="user-avatar">
          <span :style="dashboardText">mini</span>
          <i class="el-icon-arrow-down" />
        </div>
        <el-dropdown-menu slot="dropdown" class="user-dropdown">
          <router-link to="/">
            <el-dropdown-item>首页</el-dropdown-item>
          </router-link>
<!--          <el-dropdown-item divided @click.native="setting = true">-->
<!--            <span style="display:block;">布局设置</span>-->
<!--          </el-dropdown-item>-->
          <el-dropdown-item divided @click.native="logout">
            <span style="display:block;">退出登录</span>
          </el-dropdown-item>
        </el-dropdown-menu>
      </el-dropdown>
    </div>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'
import Breadcrumb from '@/components/Breadcrumb'
import Hamburger from '@/components/Hamburger'

export default {
  components: {
    Breadcrumb,
    Hamburger
  },
  computed: {
    ...mapGetters(['sidebar', 'avatar', 'nickname', 'warnLog']),
    // 获取menuInLeft值
    menuInLeft() {
      return this.$store.state.settings.menuInLeft
    },
    topBackgroundColor() {
      return {
        backgroundColor: this.$store.state.settings.menuInLeft ? '' : 'var(--menu-bg)'
      }
    },
    dashboardText() {
      return {
        fontSize: '14px',
        padding: '0 8px',
        fontFamily: 'PingFang SC, sans-serif',
        color: this.$store.state.settings.menuInLeft ? 'black' : 'var(--menu-text)'
      }
    },
    setting: {
      get() {
        return this.$store.state.settings.showSettings
      },
      set(val) {
        this.$store.dispatch('settings/changeSetting', { showSettings: val })
      }
    }
  },
  methods: {
    jump() {
      this.$router.push('/log/warning')
    },
    toggleSideBar() {
      this.$store.dispatch('app/toggleSideBar')
    },
    async logout() {
      await this.$store.dispatch('user/logout')
      // this.$router.push(`/login?redirect=${this.$route.fullPath}`)
      this.$router.push('/login')
      location.reload()
    },
    rightPanel() {

    }
  }
}
</script>

<style lang="scss" scoped>
.navbar {
  height: 56px;
  overflow: hidden;
  position: relative;
  background-color: #ffffff;
  border-bottom: 1px solid #eaedf2;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.03);

  .hamburger-container {
    line-height: 46px;
    height: 100%;
    float: left;
    cursor: pointer;
    transition: background 0.3s;
    -webkit-tap-highlight-color: transparent;

    &:hover {
      background: rgba(0, 0, 0, 0.025);
    }
  }

  .breadcrumb-container {
    float: left;
  }

  .header-bar {
    float: left;
    display: flex;
    width: 85%;
  }
  .right-menu {
    float: right;
    width: fit-content;
    height: 100%;
    display: flex;
    align-items: center;
    &:focus {
      outline: none;
    }
    .el-badge {
      margin: auto;
    }
    .right-menu-item {
      display: inline-block;
      padding: 0 8px;
      height: 100%;
      font-size: 18px;
      color: #5a5e66;
      vertical-align: text-bottom;

      &.hover-effect {
        cursor: pointer;
        transition: background 0.3s;

        &:hover {
          background: rgba(0, 0, 0, 0.025);
        }
      }
    }

    .el-dropdown {
      height: 100%;
      padding: 0 20px;

      &:hover {
        background: rgba(155, 158, 159, .1);
      }

      .avatar-container {
        height: 100%;
        cursor: pointer;
        display: flex;
        align-items: center;

        .user-avatar {
          cursor: pointer;
          width: 30px;
          height: 30px;
          border-radius: 50%;
        }
      }
    }
  }
}
</style>
