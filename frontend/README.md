# EEQS 前端项目

**额尔齐斯河流域上游水资源预报管理系统**

## 简介

本项目为额尔齐斯河流域上游水资源预报管理系统的前端工程，提供气象观测、积雪动态监测、水文观测、水资源预报、洪水预警等功能模块。

## 技术栈

- Vue 2.6.14
- Vue CLI 4.4.4
- Vue Router 3.0.6
- Vuex 3.1.0
- Element UI 2.15.14
- ECharts 6.0.0
- Leaflet 1.9.4

## 开发环境要求

- Node.js >= 14.0.0
- npm >= 3.0.0

## 快速开始

```bash
# 安装依赖
npm install

# 启动开发服务器（推荐在 VSCode / CMD / PowerShell 终端中执行）
npm run dev
```

> ⚠️ **重要提示**：本项目在 **Git Bash** 环境下启动开发服务器存在已知兼容性问题：
> - `&` 后台运行不生效，进程会被随命令结束而终止
> - 管道 `|` 会阻塞进程（如 `tee`）
> - `npx` 可能不在 PATH 中
> - 路径 `/c/` 与 `C:\` 混用导致问题
>
> **解决方案**：请优先使用 **VSCode 内置终端**、**Windows CMD** 或 **PowerShell** 执行 `npm run dev`。如必须使用 Git Bash，参考下方「Git Bash 兼容方案」。

## 常用命令速查

| 命令 | 说明 | 推荐终端 |
|------|------|----------|
| `npm run dev` | 启动开发服务器（端口 9528） | VSCode / CMD / PowerShell |
| `npm run build` | 生产环境构建 | 任意 |
| `npm run lint` | 运行 ESLint 代码检查 | 任意 |
| `npm run preview` | 预览生产构建 | 任意 |
| `npm run svgo` | 优化 SVG 图标 | 任意 |

## Git Bash 兼容方案

如必须在 Git Bash 中操作，请使用以下方式：

```bash
# 启动开发服务器（Git Bash 专用）
bash start-dev.sh

# 或直接调用 node（当 npx/npm 不可用时）
node ./node_modules/@vue/cli-service/bin/vue-cli-service.js serve

# 构建（Git Bash 专用）
node ./node_modules/@vue/cli-service/bin/vue-cli-service.js build

# 代码检查（Git Bash 专用）
node ./node_modules/eslint/bin/eslint.js --ext .js,.vue src
```

## 项目结构

```
src/
  api/          - API 接口封装
  assets/       - 静态资源
  components/   - 公共组件
  icons/        - SVG 图标
  layout/       - 页面布局
  router/       - 路由配置
  store/        - 状态管理
  styles/       - 全局样式
  utils/        - 工具函数
  views/        - 页面视图
    dashboard/         - 仪表盘
    hydrology/         - 水文观测
    sites/             - 站点详情（七站合一）
    water-forecast/    - 水资源预报
    weather/           - 气象模块
    ...
```

## 主要功能模块

- **首页仪表盘** - 综合数据展示
- **气象观测** - 7个站点实时气象数据（库威、喀依尔、金格、阿克萨拉、可可托海、可可苏里、森林站）
- **积雪动态** - 积雪站点监测与遥感分析
- **水文观测** - 团结桥、LSW水库、BEJ大桥水文数据
- **水资源预报** - 十天/月/年径流预测
- **洪水预警** - 预警信息展示
- **数据录入** - 人工数据录入

## 开发注意事项

### 1. 终端环境选择
- **推荐**：VSCode 内置终端、Windows CMD、PowerShell
- **避免**：Git Bash（存在后台进程、路径、管道等兼容性问题）

### 2. 代理配置
开发服务器代理配置在 `vue.config.js` 中：
```
/api -> http://10.16.13.46:8000
```

### 3. 实况图片配置
站点实况图存放于 `src/assets/站点实况图/`，在 `src/views/sites/station-config.js` 中通过 `import` 引入并映射到对应站点。图片命名规则：
- `库威气象站.jpg` → KW
- `库威水文站.jpg` → KYE
- `可可苏里气象站.jpg` → KKS
- `可可苏里降雪站.jpg` → KKSLS
- `可可托海滑雪场.jpg` → KKTH

### 4. 性能优化要点
- 使用 `timestamp__gte` / `timestamp__lte` 按需加载数据，避免全量查询
- 前端缓存 `dataCache` + `loadedRange`，重复范围直接过滤渲染
- `AbortController` 取消未完成请求，防止竞态
- 图表初始化后统一 `resize`，确保 transition 后尺寸正确

## 许可证

MIT
