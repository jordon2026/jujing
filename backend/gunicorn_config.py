"""Gunicorn 配置文件"""
import multiprocessing

bind = "127.0.0.1:5000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
timeout = 120
keepalive = 5

# 日志
accesslog = "/var/log/gunicorn/jujingyun_access.log"
errorlog = "/var/log/gunicorn/jujingyun_error.log"
loglevel = "info"

# 进程命名
proc_name = "jujingyun"
