'use strict'
const path = require('path')
const CompressionPlugin = require('compression-webpack-plugin')
const productionGzipExtensions = ['js', 'css', 'html', 'woff', 'ttf', 'eot']
const webpack = require('webpack')
const LodashModuleReplacementPlugin = require('lodash-webpack-plugin')
const BundleAnalyzerPlugin = require('webpack-bundle-analyzer').BundleAnalyzerPlugin

function resolve(dir) {
  return path.join(__dirname, dir)
}

const name = process.env.VUE_APP_TITLE || '额尔齐斯河流域上游水资源预报管理系统'
const port = process.env.port || process.env.npm_config_port || 9528

module.exports = {
  publicPath: '/',
  outputDir: 'dist',
  assetsDir: 'static',
  lintOnSave: process.env.NODE_ENV === 'development',
  productionSourceMap: false,
  devServer: {
    port: port,
    open: true,
    overlay: {
      warnings: false,
      errors: true
    },
    proxy: {
      '/api': {
        // 本地开发环境：代理到本机 Django 后端
        // 如需改为局域网其他设备，设置环境变量 BACKEND_URL
        target: process.env.BACKEND_URL || 'http://localhost:8000',
        changeOrigin: true,
        pathRewrite: {
          '^/api': '/api'
        }
      }
    }
      '/api': {
        target: 'http://10.16.13.46:8000',
        changeOrigin: true,
        pathRewrite: {
          '^/api': '/api'
        }
      }
    }
  },
  css: {
    loaderOptions: {
      sass: {
        prependData: `$env: ${process.env.VUE_APP_MODE};`
      }
    }
  },
  configureWebpack: config => {
    const webpackConfig = {
      externals: {
        'vue-awesome-swiper': 'VueAwesomeSwiper',
        'core-js': 'core-js'
      },
      plugins: []
    }
    if (process.env.NODE_ENV !== 'development') {
      webpackConfig.name = name
      webpackConfig.output = {
        filename: `[name].[hash:8].js`,
        chunkFilename: `[name].[hash:8].js`
      }
      webpackConfig.plugins.push(new CompressionPlugin({
        algorithm: 'gzip',
        test: new RegExp('\\.(' + productionGzipExtensions.join('|') + ')$'),
        threshold: 10240,
        minRatio: 0.8,
        deleteOriginalAssets: true
      }))
      webpackConfig.plugins.push(new webpack.optimize.MinChunkSizePlugin({
        minChunkSize: 1000000
      }))
      webpackConfig.plugins.push(new BundleAnalyzerPlugin({
        analyzerMode: 'disabled',
        generateStatsFile: true,
        statsFilename: '../stats.json'
      }))
    }
    return webpackConfig
  },
  chainWebpack(config) {
    config.plugin('preload').tap(() => [{
      rel: 'preload',
      fileBlacklist: [/\.map$/, /hot-update\.js$/, /runtime\..*\.js$/],
      include: 'initial'
    }])
    config.plugins.delete('prefetch')

    config.module
      .rule('svg')
      .exclude.add(resolve('src/icons'))
      .end()
    config.module
      .rule('icons')
      .test(/\.svg$/)
      .include.add(resolve('src/icons'))
      .end()
      .use('svg-sprite-loader')
      .loader('svg-sprite-loader')
      .options({
        symbolId: 'icon-[name]'
      })
      .end()
    
    const excludedFiles = [
      './src/views/analysis/data/wind-rose/index_bak.vue',
      './src/views/analysis/station/baidu-map-native.vue',
      './src/views/analysis/station/gaode-map.vue',
      './src/views/analysis/station/leaflet-map.vue',
      './src/views/analysis/updownload/index_bak.vue',
      './src/views/dashboard/indexV2.vue',
      './src/views/dashboard/index.vue',
      './src/views/dashboard/xaut.vue',
      './src/views/dashboard/xiLinHot.vue',
      './src/views/login/index-v1.vue',
      './src/views/login/index-latest.vue'
    ]
    const excludeRule = config.module.rule('vue').test(/\.vue$/)
    excludedFiles.forEach(file => { excludeRule.exclude.add(path.resolve(__dirname, file)).end() })
    config
      .when(process.env.NODE_ENV !== 'development',
        config => {
          config
            .plugin('ScriptExtHtmlWebpackPlugin')
            .after('html')
            .use('script-ext-html-webpack-plugin', [{
              inline: /runtime\..*\.js$/
            }])
            .end()
          config
            .optimization.splitChunks({
              chunks: 'all',
              cacheGroups: {
                libs: {
                  name: 'chunk-libs',
                  test: /[\\/]node_modules[\\/]/,
                  priority: 10,
                  chunks: 'initial'
                },
                elementUI: {
                  name: 'chunk-elementUI',
                  priority: 20,
                  test: /[\\/]node_modules[\\/]_?element-ui(.*)/
                },
                commons: {
                  name: 'chunk-commons',
                  test: resolve('src/components'),
                  minChunks: 3,
                  priority: 5,
                  reuseExistingChunk: true
                }
              }
            })
          config.optimization.minimizer('terser').tap((args) => {
            args[0].terserOptions.compress.drop_console = true
            args[0].terserOptions.compress.drop_debugger = true
            args[0].terserOptions.compress.pure_funcs = ['console.log']
            args[0].terserOptions.output = {
              comments: false
            }
            return args
          })
          config.optimization.runtimeChunk('single')
        }
      )

    config
      .plugin('loadshReplace')
      .use(new LodashModuleReplacementPlugin())
  }
}
