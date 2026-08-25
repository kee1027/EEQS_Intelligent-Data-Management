<template>
  <forecast-flow-page period="ten-days" />
</template>

<script>
import ForecastFlowPage from './components/ForecastFlowPage.vue'

export default {
  name: 'WaterForecastTenDays',
  components: {
    ForecastFlowPage
  }
}
</script>
