#!/bin/bash
echo "正在启动开发服务器..."
echo "Node版本: $(node -v)"
echo "NPM版本: $(npm -v)"
if [ ! -d "node_modules" ]; then
    echo "首次运行，正在安装依赖..."
    npm install
fi
npm run dev
