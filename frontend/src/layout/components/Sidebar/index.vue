<template>
  <div :class="{'has-logo':showLogo}">
    <logo v-if="showLogo" :collapse="isCollapse" />
    <el-scrollbar wrap-class="scrollbar-wrapper">
      <el-menu
        :default-active="activeMenu"
        :background-color="backgroundColor"
        :text-color="menuText"
        :active-text-color="activeTextColor"
        :collapse="isCollapse"
        :unique-opened="true"
        :collapse-transition="false"
        mode="vertical"
      >
        <sidebar-item v-for="route in routes" :key="route.path" :item="route" :base-path="route.path" />
      </el-menu>
    </el-scrollbar>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'
import Logo from './Logo'
import SidebarItem from './SidebarItem'

export default {
  components: { SidebarItem, Logo },
  computed: {
    ...mapGetters(['sidebar', 'resultAllRoutes']),
    routes() {
      return this.$router.options.routes
    },
    activeMenu() {
      const route = this.$route
      const { meta, path } = route
      if (meta.activeMenu) {
        return meta.activeMenu
      }
      return path
    },
    showLogo() {
      return this.$store.state.settings.sidebarLogo
    },
    isCollapse() {
      return !this.sidebar.opened
    },
    backgroundColor() {
      return this.$store.state.settings.menuBg
    },
    menuText() {
      return this.$store.state.settings.menuText
    },
    activeTextColor() {
      return this.$store.state.settings.menuActiveText
    }
  },
  mounted() {
    const observer = new MutationObserver(() => {
      this.$forceUpdate()
    })
    observer.observe(document.documentElement, { attributes: true })
  }
}
</script>
