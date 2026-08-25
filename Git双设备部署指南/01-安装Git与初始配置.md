# 01 · 安装 Git 与初始配置

> 本章在 **两台设备上都要执行**。完成后，每台设备都有一个可用的 Git，并已配置好你的身份。

---

## 1.1 Windows 安装

当前最新维护版：**Git 2.55.0**（2026-08-11 发布）。

**方式一：官网下载安装包（推荐）**

1. 打开 https://git-scm.com/downloads/win ，下载 `Git for Windows/x64 Setup`。
2. 双击安装包，安装向导中**全部保持默认**即可，重点确认以下几页：
   - **默认分支名**：建议选 `main`（Override the default branch name for new repositories → 填 `main`）。
   - **PATH 环境**：保持默认的 "Git from the command line and also from 3rd-party software"。
   - **SSH 可执行文件**：保持默认 "Use bundled OpenSSH"。
   - **换行符转换**：保持默认 "Checkout Windows-style, commit Unix-style line endings"（跨平台协作的关键，见 1.4 节）。
   - **凭证管理器**：保持默认 "Git Credential Manager"。
3. 安装完成后，桌面右键会出现 **Git Bash Here** 菜单项。

**方式二：winget 命令行安装**

在 PowerShell 中执行：

```powershell
winget install --id Git.Git -e --source winget
```

**验证**：打开 Git Bash（或 PowerShell），执行：

```bash
git --version
# 期望输出类似：git version 2.55.0.windows.1
```

---

## 1.2 macOS 安装

**方式一：Homebrew（推荐，方便日后升级）**

```bash
brew install git
```

**方式二：Xcode 命令行工具（系统自带入口）**

```bash
xcode-select --install
```

**验证**：

```bash
git --version
```

---

## 1.3 Linux 安装

按发行版对号入座：

```bash
# Debian / Ubuntu
sudo apt update && sudo apt install git

# Fedora
sudo dnf install git

# Arch
sudo pacman -S git
```

验证同上：`git --version`。

---

## 1.4 全局身份配置（两台设备都执行）

Git 每次提交都会记录"是谁改的"，必须先配置身份。**两台设备使用同一个用户名和邮箱**（与 GitHub 账号一致），这样两台设备的提交在历史上看起来都出自同一个人。

```bash
# 把引号内换成你自己的信息
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

再设置这几项**推荐配置**（解释见注释）：

```bash
# 新建仓库的默认分支叫 main
git config --global init.defaultBranch main

# pull 时只接受快进合并，避免意外的 merge commit（个人单分支工作流更安全）
git config --global pull.ff only

# 让命令行输出显示颜色，更易读
git config --global color.ui auto
```

**换行符配置（跨平台协作防坑，重要）**：

```bash
# Windows 设备执行：
git config --global core.autocrlf true

# macOS / Linux 设备执行：
git config --global core.autocrlf input
```

> 作用：Windows 与 macOS/Linux 的换行符不同（CRLF vs LF）。以上设置保证**提交进仓库的永远是 LF**，检出时按本机习惯转换，两台设备不会因换行符产生满屏的假改动。

**查看全部配置，确认无误**：

```bash
git config --global --list
# 应能看到 user.name / user.email / init.defaultbranch / core.autocrlf 等
```

---

## 1.5 本章检查清单

在每台设备上确认：

- [ ] `git --version` 能输出版本号（≥ 2.40 即可，建议 2.55.0）
- [ ] `git config --global user.name` 和 `user.email` 正确
- [ ] `core.autocrlf` 按平台设置（Windows = true，macOS/Linux = input）
- [ ] 两台设备的 user.name / user.email **完全一致**

完成后进入 `02-创建GitHub仓库与SSH密钥.md`。
