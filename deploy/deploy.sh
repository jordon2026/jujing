#!/bin/bash
# ==============================================================
# 聚景官网 一键部署脚本
# 适用: CentOS 7 / root 用户
# 用法: chmod +x deploy.sh && ./deploy.sh
# ==============================================================

set -e

# ---------- 配置项 ----------
APP_DIR="/var/www/jujingyun"
REPO_URL="https://github.com/jordon2026/jujing.git"
DOMAIN="www.jujingyun.com"
PYTHON_VER="3"

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  聚景官网 - 一键部署脚本${NC}"
echo -e "${GREEN}========================================${NC}"

# ---------- 1. 系统更新 & 安装依赖 ----------
echo -e "${YELLOW}[1/8] 安装系统依赖...${NC}"
yum install -y epel-release
yum install -y nginx git python3 python3-pip gcc

# ---------- 2. 配置 Python 虚拟环境 ----------
echo -e "${YELLOW}[2/8] 配置 Python 环境...${NC}"
if [ ! -f "${APP_DIR}/venv/bin/activate" ]; then
    python3 -m venv ${APP_DIR}/venv
fi
source ${APP_DIR}/venv/bin/activate

# ---------- 3. 拉取代码 ----------
echo -e "${YELLOW}[3/8] 拉取代码...${NC}"
if [ -d "${APP_DIR}/.git" ]; then
    cd ${APP_DIR}
    git pull origin main || git pull origin master
else
    git clone ${REPO_URL} ${APP_DIR}
    cd ${APP_DIR}
fi

# ---------- 4. 安装 Python 依赖 ----------
echo -e "${YELLOW}[4/8] 安装 Python 依赖...${NC}"
source ${APP_DIR}/venv/bin/activate
pip install --upgrade pip
pip install -r ${APP_DIR}/backend/requirements.txt
pip install gunicorn pillow

# ---------- 5. 配置 Nginx ----------
echo -e "${YELLOW}[5/8] 配置 Nginx...${NC}"
cp -f ${APP_DIR}/deploy/nginx.conf /etc/nginx/conf.d/jujingyun.conf

# 移除默认配置避免冲突
if [ -f /etc/nginx/nginx.conf ]; then
    # 确保包含 conf.d
    if ! grep -q "include.*conf.d" /etc/nginx/nginx.conf; then
        sed -i '/http {/a \    include /etc/nginx/conf.d/*.conf;' /etc/nginx/nginx.conf
    fi
fi

# ---------- 6. 配置 Systemd 服务 ----------
echo -e "${YELLOW}[6/8] 配置 Gunicorn Systemd 服务...${NC}"
mkdir -p /var/log/gunicorn

cat > /etc/systemd/system/jujingyun.service <<EOF
[Unit]
Description=Jujingyun Flask App
After=network.target

[Service]
Type=notify
User=root
Group=root
WorkingDirectory=${APP_DIR}/backend
Environment="PATH=${APP_DIR}/venv/bin"
Environment="SECRET_KEY=$(openssl rand -hex 32)"
ExecStart=${APP_DIR}/venv/bin/gunicorn -c gunicorn_config.py app:app
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable jujingyun
systemctl restart jujingyun

# ---------- 7. 配置防火墙 ----------
echo -e "${YELLOW}[7/8] 配置防火墙...${NC}"
if systemctl is-active --quiet firewalld; then
    firewall-cmd --permanent --add-service=http
    firewall-cmd --permanent --add-service=https
    firewall-cmd --reload
fi

# ---------- 8. 启动 Nginx ----------
echo -e "${YELLOW}[8/8] 启动 Nginx...${NC}"
nginx -t
systemctl enable nginx
systemctl restart nginx

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  部署完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "  网站地址: http://${DOMAIN}"
echo -e "  后台地址: http://${DOMAIN}/admin/"
echo ""
echo -e "  ${YELLOW}常用命令:${NC}"
echo -e "  查看后端状态:  systemctl status jujingyun"
echo -e "  查看后端日志:  journalctl -u jujingyun -f"
echo -e "  重启后端:      systemctl restart jujingyun"
echo -e "  查看Nginx状态: systemctl status nginx"
echo -e "  更新代码:      cd ${APP_DIR} && git pull && systemctl restart jujingyun"
echo ""
echo -e "  ${RED}重要提示:${NC}"
echo -e "  请确保域名 ${DOMAIN} 已解析到服务器 IP"
echo -e "  HTTPS 证书建议后续用 certbot --nginx 配置"
echo ""
