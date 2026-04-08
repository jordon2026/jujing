# 聚景官网 - 云服务器部署指南

## 📋 项目信息

| 项目 | 值 |
|------|------|
| GitHub 仓库 | https://github.com/jordon2026/jujing |
| 服务器 IP | 8.130.37.209 |
| 域名 | www.jujingyun.com |
| 系统 | CentOS 7 |
| 部署方案 | Nginx + Gunicorn |

## 🏗️ 架构说明

```
用户浏览器
    │
    ▼
Nginx (端口 80/443)
    ├── /           → 前端静态文件 (frontend/)
    ├── /admin/     → 管理后台 (admin/)
    ├── /api/       → 反向代理 → Gunicorn (127.0.0.1:5000)
    ├── /upload/    → 反向代理 → Gunicorn
    └── /static/    → 反向代理 → Gunicorn (后端静态资源)
```

## 📁 项目结构

```
jujingyun/
├── frontend/          # 前端静态页面
│   └── index.html     # 官网首页
├── admin/             # 管理后台（已构建）
├── backend/           # Flask 后端 API
│   ├── app.py
│   ├── requirements.txt
│   ├── gunicorn_config.py  # Gunicorn 配置
│   ├── static/        # 上传的图片等静态资源
│   └── data/          # JSON 数据文件
├── deploy/            # 部署相关
│   ├── deploy.sh      # 一键部署脚本
│   └── nginx.conf     # Nginx 配置文件
└── .gitignore
```

---

## 🚀 部署步骤

### 第一步：本地推送到 GitHub

在本地 Windows 电脑上执行：

```bash
# 1. 进入项目目录
cd "d:\聚景科技\2026\jujingyun"

# 2. 初始化 Git 仓库（如果还没有）
git init
git branch -M main

# 3. 添加远程仓库
git remote add origin https://github.com/jordon2026/jujing.git

# 4. 添加所有文件并提交
git add .
git commit -m "feat: 初始化聚景官网项目，配置部署文件"

# 5. 推送到 GitHub
git push -u origin main
```

> 如果远程仓库已有内容，可能需要先 `git pull origin main --allow-unrelated-histories`

### 第二步：SSH 登录服务器

```bash
ssh root@8.130.37.209
```

### 第三步：在服务器上一键部署

```bash
# 1. 安装 git（如果未安装）
yum install -y git

# 2. 克隆仓库
git clone https://github.com/jordon2026/jujing.git /var/www/jujingyun

# 3. 执行一键部署脚本
cd /var/www/jujingyun
chmod +x deploy/deploy.sh
./deploy/deploy.sh
```

部署脚本会自动完成：
- ✅ 安装 Nginx、Python3、pip
- ✅ 创建 Python 虚拟环境
- ✅ 安装 Flask 依赖 + Gunicorn + Pillow
- ✅ 配置 Nginx 反向代理
- ✅ 配置 Systemd 服务（开机自启）
- ✅ 启动所有服务

### 第四步：配置域名解析

在域名服务商（阿里云/腾讯云等）添加 DNS 解析：

| 类型 | 主机记录 | 记录值 |
|------|---------|--------|
| A | www | 8.130.37.209 |
| A | @ | 8.130.37.209 |

### 第五步（可选）：配置 HTTPS

```bash
# 安装 certbot
yum install -y certbot python2-certbot-nginx

# 自动配置 SSL 证书
certbot --nginx -d www.jujingyun.com -d jujingyun.com
```

---

## 📝 日常维护命令

```bash
# 查看后端运行状态
systemctl status jujingyun

# 查看后端日志（实时）
journalctl -u jujingyun -f

# 重启后端服务
systemctl restart jujingyun

# 查看 Nginx 状态
systemctl status nginx

# 重新加载 Nginx 配置（不中断服务）
nginx -s reload

# 更新代码并重启
cd /var/www/jujingyun && git pull && systemctl restart jujingyun

# 查看 Gunicorn 日志
tail -f /var/log/gunicorn/jujingyun_error.log
```

---

## ⚠️ 注意事项

1. **前端 API 地址**：已从 `http://localhost:5000` 修改为相对路径 `''`，通过 Nginx 反向代理访问 API
2. **本地开发**：如需本地开发，请将 `API_BASE` 改回 `'http://localhost:5000'`
3. ** SECRET_KEY**：部署脚本会自动生成随机密钥，也可在 Systemd 服务文件中手动设置
4. **防火墙**：确保云服务器安全组放行了 80 和 443 端口
5. **数据目录**：`backend/data/` 和 `backend/static/` 包含重要数据，建议定期备份

## 🔧 故障排查

| 问题 | 解决方案 |
|------|---------|
| 502 Bad Gateway | `systemctl status jujingyun` 检查后端是否运行 |
| 静态资源 404 | 检查 Nginx 配置中的 root 路径是否正确 |
| API 返回 500 | `journalctl -u jujingyun -f` 查看后端错误日志 |
| 权限问题 | `chown -R nginx:nginx /var/www/jujingyun` |
| 端口被占用 | `netstat -tlnp \| grep :80` 检查端口占用 |
