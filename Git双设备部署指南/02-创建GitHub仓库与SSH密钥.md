# 02 · 创建 GitHub 仓库与 SSH 密钥

> 本章目标：在 GitHub 上建好远程仓库，并让**两台设备各自拥有一把 SSH 密钥**绑定到同一个 GitHub 账号。
>
> 为什么用 SSH 而不是 HTTPS：SSH 一次配置、永久免密，push/pull 不需要反复输入账号密码或 Token，双设备场景下省心得多。

---

## 2.1 注册 / 登录 GitHub

1. 打开 https://github.com ，注册账号（邮箱建议与 01 章 `user.email` 一致）。
2. 登录后记住你的 **用户名**（下文以 `<你的用户名>` 代指）。

> 国内网络访问 GitHub 偶尔不稳定。如果后续 clone/push 经常超时，可改用国内平台 **Gitee**（https://gitee.com）或 **GitCode**，本章所有操作（创建仓库、添加 SSH 公钥）完全同构，只是域名不同。

---

## 2.2 创建远程仓库（只做一次）

1. 点击 GitHub 右上角 **+** → **New repository**。
2. 填写：
   - **Repository name**：项目名，例如 `my-project`
   - **Private / Public**：个人项目建议选 **Private**
   - **不要勾选** "Add a README file" 等初始化选项（先建一个空仓库，后面由本地推送首个提交，避免两端历史不一致）
3. 点击 **Create repository**。
4. 创建后页面会显示仓库地址，**复制 SSH 格式的地址**，形如：

```
git@github.com:<你的用户名>/my-project.git
```

---

## 2.3 生成 SSH 密钥（两台设备各自执行一遍）

**每台设备生成自己独立的密钥对**，不要把私钥从一台拷到另一台——这样某台设备丢失时，只需在 GitHub 上删掉对应的公钥即可，不影响另一台。

在设备 A 的终端（Windows 用 Git Bash，macOS/Linux 用终端）执行：

```bash
# 邮箱换成你的 GitHub 邮箱；-C 后面的注释建议带上设备名，方便日后区分
ssh-keygen -t ed25519 -C "you@example.com-设备A"
```

- 一路回车即可（默认保存到 `~/.ssh/id_ed25519`）。
-  passphrase 可以留空（方便），也可以设置（更安全，每次使用需输入）。

> 如果是很老的系统不支持 ed25519，改用：`ssh-keygen -t rsa -b 4096 -C "you@example.com-设备A"`

**查看并复制公钥**（注意是 `.pub` 结尾的公钥，私钥 `id_ed25519` 永远不要外传）：

```bash
cat ~/.ssh/id_ed25519.pub
```

复制输出的完整一行（以 `ssh-ed25519` 开头、以你的注释结尾）。

在设备 B 上**重复以上全部步骤**，注释改为 `-设备B`。

---

## 2.4 把两把公钥都绑定到 GitHub

1. GitHub 网页右上角头像 → **Settings** → 左侧 **SSH and GPG keys** → **New SSH key**。
2. 填写：
   - **Title**：设备标识，如 `设备A-办公电脑`
   - **Key type**：保持 `Authentication Key`
   - **Key**：粘贴设备 A 的公钥
3. 保存。然后用同样方法**再添加设备 B 的公钥**。

最终你的 GitHub 账号下应有两条 SSH key 记录，分别对应两台设备。

---

## 2.5 验证连接（两台设备各自执行）

```bash
ssh -T git@github.com
```

- 首次连接会提示 `Are you sure you want to continue connecting (yes/no/[fingerprint])?`，输入 `yes` 回车（这一步是把 GitHub 的服务器指纹加入信任列表）。
- 看到如下输出即成功：

```
Hi <你的用户名>! You've successfully authenticated, but GitHub does not provide shell access.
```

> 如果提示 `Permission denied (publickey)`：按顺序排查——
> 1. 公钥是否真的添加到了 GitHub（Settings → SSH keys 里能看到）；
> 2. `cat ~/.ssh/id_ed25519.pub` 的内容与 GitHub 上是否一致；
> 3. 本地是否有多把密钥导致选错，可执行 `ssh -vT git@github.com` 看详细日志。

---

## 2.6 本章检查清单

- [ ] GitHub 上已创建空仓库，拿到 SSH 地址 `git@github.com:<用户名>/<仓库名>.git`
- [ ] 设备 A 和设备 B **各自**生成了独立的 ed25519 密钥对
- [ ] 两把**公钥**都添加到了 GitHub 账号
- [ ] 两台设备执行 `ssh -T git@github.com` 都返回成功问候语

完成后进入 `03-首次克隆与提交工作流.md`。
