import hasRole from './permission/hasRole'
import hasPermi from './permission/hasPermi'
import Vue from 'vue'

const install = function(Vue) {
  Vue.directive('hasRole', hasRole)
  Vue.directive('hasPermi', hasPermi)
  Vue.directive('lazy', {
    bind: function(el, binding) {
      const lazyLoadObserve = new IntersectionObserver((entries, observer) => {
        entries.forEach((entry, index) => {
          const lazyItem = entry.target
          if (entry.isIntersecting || entry.intersectionRatio > 0) {
            binding.value.getData(binding.value.id, lazyLoadObserve, lazyItem)
          }
        })
      })
      lazyLoadObserve.observe(el)
    }
  })
}

if (window.Vue) {
  window['hasRole'] = hasRole
  window['hasPermi'] = hasPermi
    Vue.use(install); // eslint-disable-line
}

export default install
