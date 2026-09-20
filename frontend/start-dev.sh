#!/bin/bash
# 本项目为 webpack 4（@vue/cli-service 4.x），推荐使用 Node 16：
#   nvm install 16.20.2 && nvm use 16.20.2
# Node 17+ 的 OpenSSL 3 与 webpack 4 不兼容，且部分新版 Node 已移除 --openssl-legacy-provider
NPM=$(command -v npm || command -v npm.cmd)
echo "正在启动开发服务器..."
echo "Node版本: $(node -v)"
if [ ! -d "node_modules" ]; then
    echo "首次运行，正在安装依赖..."
    "$NPM" install
fi
"$NPM" run dev
