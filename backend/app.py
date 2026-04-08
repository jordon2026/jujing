from flask import Flask, request, jsonify, send_file, session
from flask_cors import CORS
from functools import wraps
import jwt
import datetime
import json
import os
import shutil
import zipfile
import random
import string
import re
from PIL import Image, ImageDraw, ImageFont
import io
import hashlib
import time
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__, static_folder='static', static_url_path='/static')
CORS(app, supports_credentials=True)

# 安全配置
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'jujing-secret-key-' + str(random.randint(100000, 999999)))
app.config['JSON_AS_ASCII'] = False
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(hours=1)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 限制上传文件大小为16MB

# 登录失败限制
login_attempts = {}  # IP: {count, last_attempt, locked_until}
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION = 900  # 15分钟

# 验证码存储
captcha_store = {}  # captcha_id: {code, expires}

# 请求频率限制
request_limits = {}  # IP: {count, window_start}
RATE_LIMIT_WINDOW = 60  # 1分钟窗口
RATE_LIMIT_MAX = 100   # 每分钟最多100个请求

# 安全响应头
@app.after_request
def add_security_headers(response):
    """添加安全响应头"""
    # 防止点击劫持
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    # XSS保护
    response.headers['X-XSS-Protection'] = '1; mode=block'
    # 内容类型嗅探保护
    response.headers['X-Content-Type-Options'] = 'nosniff'
    # 引用策略
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    # 内容安全策略（基础版）
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; font-src 'self';"
    return response

# 请求频率限制检查
def check_rate_limit(ip):
    """检查请求频率限制"""
    now = time.time()
    if ip in request_limits:
        limit = request_limits[ip]
        # 检查是否在新的时间窗口
        if now - limit['window_start'] > RATE_LIMIT_WINDOW:
            request_limits[ip] = {'count': 1, 'window_start': now}
            return True, None
        # 增加计数
        limit['count'] += 1
        if limit['count'] > RATE_LIMIT_MAX:
            return False, '请求过于频繁，请稍后再试'
    else:
        request_limits[ip] = {'count': 1, 'window_start': now}
    return True, None

# 清理过期的限制记录
def cleanup_limits():
    """清理过期的限制记录"""
    now = time.time()
    # 清理登录尝试记录
    for ip in list(login_attempts.keys()):
        if login_attempts[ip].get('locked_until') and now > login_attempts[ip]['locked_until'] + LOCKOUT_DURATION:
            del login_attempts[ip]
    # 清理请求频率记录
    for ip in list(request_limits.keys()):
        if now - request_limits[ip]['window_start'] > RATE_LIMIT_WINDOW * 2:
            del request_limits[ip]
    # 清理过期验证码
    for captcha_id in list(captcha_store.keys()):
        if now > captcha_store[captcha_id]['expires']:
            del captcha_store[captcha_id]

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
os.makedirs(DATA_DIR, exist_ok=True)

BACKUP_DIR = os.path.join(os.path.dirname(__file__), 'backups')
os.makedirs(BACKUP_DIR, exist_ok=True)

# 默认管理员账号
ADMIN_USER = {
    'id': 1,
    'username': 'admin',
    'password': 'admin123',
    'name': '管理员'
}

# 初始化数据文件
def init_data():
    files = {
        'hero.json': {
            'title': '专注网站建设',
            'subtitle': '平台系统开发10年',
            'description': '北京聚景科技有限公司，致力于互联网品牌建设与网络营销，专业领域包括网站建设、APP开发、微信开发、小程序定制开发、H5互动设计、VR应用开发、AI智能体开发、智能体本地化部署服务等，为客户提供综合性数字化创新服务。',
            'badge': '高新技术企业 · 华为云合作伙伴',
            'primaryBtn': '了解我们的服务',
            'secondaryBtn': '查看成功案例'
        },
        'stats.json': [
            {'value': '100+', 'label': '技术团队'},
            {'value': '10+', 'label': '年行业经验'},
            {'value': '500+', 'label': '服务客户'},
            {'value': '800+', 'label': '成功案例'}
        ],
        'services.json': [
            {'id': 1, 'icon': '🌐', 'title': '网站建设', 'description': '企业官网、电商平台、行业门户等全类型网站设计与开发，响应式布局，SEO友好，高效转化。', 'tags': ['企业官网', '电商平台', '响应式', 'SEO优化']},
            {'id': 2, 'icon': '📱', 'title': 'APP开发', 'description': 'iOS/Android原生及跨平台应用开发，覆盖资讯、电商、社交等多个垂直领域。', 'tags': ['iOS开发', 'Android', '原生开发', '跨平台']},
            {'id': 3, 'icon': '💬', 'title': '微信开发', 'description': '微信公众号、企业微信、微信商城等定制化开发，助力品牌触达亿级用户。', 'tags': ['公众号', '企业微信', '微信商城', 'H5互动']},
            {'id': 4, 'icon': '📲', 'title': '小程序定制开发', 'description': '微信、支付宝、抖音等多平台小程序定制开发，界面精美、体验流畅。', 'tags': ['微信小程序', '支付宝小程序', '抖音小程序', '跨平台']},
            {'id': 5, 'icon': '🎮', 'title': 'H5互动开发', 'description': '创意H5页面、互动游戏、营销活动页面开发，提升用户参与度和品牌传播效果。', 'tags': ['创意H5', '互动游戏', '营销活动', '品牌传播']},
            {'id': 6, 'icon': '🥽', 'title': 'VR应用开发', 'description': 'VR全景展示、虚拟现实应用开发，为企业打造沉浸式数字化体验。', 'tags': ['VR全景', '虚拟现实', '沉浸体验', '3D展示']},
            {'id': 7, 'icon': '📈', 'title': '关键词优化/SEO', 'description': '整站优化、关键词排名、全网营销推广，提升搜索引擎排名，精准获客。', 'tags': ['关键词优化', '整站优化', '全网营销', '推广账户管理']},
            {'id': 8, 'icon': '☁️', 'title': '平台系统开发', 'description': 'CRM、ERP、OA等企业管理系统定制开发，助力企业数字化转型。', 'tags': ['CRM系统', 'ERP系统', 'OA系统', '定制开发']},
            {'id': 9, 'icon': '🤖', 'title': 'AI智能体开发', 'description': '基于大语言模型的智能体定制开发，为企业提供智能客服、知识库问答、自动化办公等AI解决方案。', 'tags': ['智能客服', '知识库问答', '自动化办公', '大模型应用']},
            {'id': 10, 'icon': '💻', 'title': '智能体本地化部署', 'description': '为企业提供AI智能体私有化部署服务，数据安全可控，支持本地服务器、私有云等多种部署方案。', 'tags': ['私有化部署', '数据安全', '本地服务器', '私有云']}
        ],
        'cases.json': [
            {'id': 1, 'title': '深圳市公安局官方网站', 'category': 'website', 'description': '政府门户网站建设项目，提供全面的警务信息服务和便民功能。', 'icon': '🏛️', 'bgColor': 'linear-gradient(135deg,#0a1628,#1a3a5c)'},
            {'id': 2, 'title': '国家能源集团官方网站', 'category': 'website', 'description': '大型国有企业官网建设，展示企业形象和能源业务信息。', 'icon': '⚡', 'bgColor': 'linear-gradient(135deg,#0d1a2e,#1a4a3c)'},
            {'id': 3, 'title': '中国大唐集团官方网站', 'category': 'website', 'description': '电力企业官网开发，突出企业实力和绿色发展理念。', 'icon': '🔴', 'bgColor': 'linear-gradient(135deg,#0c1929,#3a2040)'},
            {'id': 4, 'title': '中国华能集团官方网站', 'category': 'website', 'description': '能源行业官网建设，专业大气的企业形象展示平台。', 'icon': '🔵', 'bgColor': 'linear-gradient(135deg,#0a1624,#204060)'},
            {'id': 5, 'title': '小程序-作业打卡-学习平台', 'category': 'miniapp', 'description': '教育类小程序，提供作业打卡、学习进度跟踪等功能。', 'icon': '📚', 'bgColor': 'linear-gradient(135deg,#0b1a2e,#2a4060)'},
            {'id': 6, 'title': '小程序-智慧景区', 'category': 'miniapp', 'description': '旅游景区导览小程序，提供景点介绍、路线规划、在线购票等服务。', 'icon': '🏞️', 'bgColor': 'linear-gradient(135deg,#0c1b30,#3a5030)'},
            {'id': 7, 'title': '善商建材共享平台', 'category': 'platform', 'description': '建材行业B2B共享平台，连接供应商与采购商，提升交易效率。', 'icon': '🏗️', 'bgColor': 'linear-gradient(135deg,#0a1628,#503020)'},
            {'id': 8, 'title': '小程序-养殖众筹平台-智慧农场', 'category': 'miniapp', 'description': '农业众筹小程序，连接城市消费者与农村养殖场，实现透明化养殖。', 'icon': '🌾', 'bgColor': 'linear-gradient(135deg,#0d1a2e,#405020)'},
            {'id': 9, 'title': '并读 - 新闻资讯APP', 'category': 'app', 'description': '个性化新闻推荐应用，智能算法推送用户感兴趣的内容。', 'icon': '📰', 'bgColor': 'linear-gradient(135deg,#0c1929,#602040)'},
            {'id': 10, 'title': '看看新闻', 'category': 'app', 'description': '视频新闻客户端，提供及时、全面的新闻资讯服务。', 'icon': '📺', 'bgColor': 'linear-gradient(135deg,#0a1624,#204050)'},
            {'id': 11, 'title': '瑜伽优课', 'category': 'wechat', 'description': '瑜伽健身类微信公众号，提供课程预约、健身指导等服务。', 'icon': '🧘', 'bgColor': 'linear-gradient(135deg,#0b1a2e,#502060)'},
            {'id': 12, 'title': '读书有范', 'category': 'wechat', 'description': '阅读分享类公众号，提供优质书籍推荐和读书心得分享。', 'icon': '📖', 'bgColor': 'linear-gradient(135deg,#0c1b30,#603020)'}
        ],
        'news.json': [
            {'id': 1, 'title': '喜讯!热烈祝贺北京聚景科技有限公司获得国家级高新技术企业认定!', 'date': '2021-03-11', 'tag': '企业网站建设', 'summary': '近期北京市怀柔区人民政府官网公布了高新技术企业认定通知，我司荣登榜单之中，正式迈入高新技术企业行列。', 'content': '近期北京市怀柔区人民政府官网公布了"北京市怀柔区科学技术委员会关于领取2020年第三、四批高新技术企业认定证书"的通知，我司作为一家综合性高科技企业，荣登榜单之中，这标志着我司在研发和创新方面得到国家相关部门的肯定与认可，由此正式迈入高新技术企业行列，可喜可贺。'},
            {'id': 2, 'title': '北京聚景科技有限公司正式成为华为云精英服务商，携手华为，共赢未来', 'date': '2020-08-27', 'tag': '企业网站建设', 'summary': '公司正式获评华为云精英服务商资质，与华为云建立深度合作关系。', 'content': '公司正式获评华为云精英服务商资质，与华为云建立深度合作关系，为客户提供更优质的云服务解决方案。'},
            {'id': 3, 'title': '喜报：北京聚景科技有限公司荣获小聚CMS网站管理系统计算机软件著作权', 'date': '2020-04-24', 'tag': '企业网站优化', 'summary': '小聚CMS网站管理软件获得计算机软件著作权认证，这是公司自主研发的核心产品之一。', 'content': '小聚CMS网站管理软件获得计算机软件著作权认证，这是公司自主研发的核心产品之一，针对企业主体、管理团队、运营人员、销售人员、人事，通过登录和使用Web平台，有效的管理客户信息、人员信息、订单信息。'},
            {'id': 4, 'title': '喜报：北京聚景科技有限公司荣获商会通系统计算机软件著作权', 'date': '2020-04-24', 'tag': '北京网站建设', 'summary': '商会通软件获得国家计算机软件著作权认证，为商会组织提供专业的信息化管理解决方案。', 'content': '商会通软件获得国家计算机软件著作权认证，为商会组织提供专业的信息化管理解决方案。'},
            {'id': 5, 'title': '喜报：北京聚景科技有限公司荣获景区移动导览系统计算机软件著作权', 'date': '2020-04-24', 'tag': '企业网站优化', 'summary': '景区移动导览软件获得国家计算机软件著作权认证，为旅游景区提供智能化的导览服务解决方案。', 'content': '景区移动导览软件获得国家计算机软件著作权认证，为旅游景区提供智能化的导览服务解决方案。'},
            {'id': 6, 'title': '喜报：北京聚景科技有限公司荣获微信管理小助手系统计算机软件著作权', 'date': '2020-04-24', 'tag': '北京网站建设', 'summary': '微信管理小助手软件获得计算机软件著作权认证，帮助企业高效管理微信公众号运营。', 'content': '微信管理小助手软件获得计算机软件著作权认证，帮助企业高效管理微信公众号运营。'}
        ],
        'about.json': {
            'companyName': '北京聚景科技有限公司',
            'description': '聚景科技自公司创立至今，始终坚持从事网站定制，信息系统开发。公司总部位于北京，秉承实现全网价值营销的理念，以数据为核心，结合营销、内容、技术、研发多维度为客户提供综合性数字化创新服务，帮助传统企业实现"互联网+"转型升级。',
            'address': '北京市昌平区龙德紫金2号楼',
            'phone': '010-84818211',
            'mobile': '131-4686-6478',
            'email': 'admin@jujingyun.com',
            'zipCode': '102218'
        },
        'timeline.json': [
            {'id': 1, 'year': '2017年', 'title': '公司成立', 'description': '北京聚景科技有限公司成立，开始从事高端精品策划设计'},
            {'id': 2, 'year': '2020年', 'title': '荣获多项软件著作权', 'description': '小聚CMS、商会通、景区移动导览、微信管理小助手等系统获得计算机软件著作权'},
            {'id': 3, 'year': '2020年', 'title': '成为华为云精英服务商', 'description': '正式获评华为云精英服务商资质，携手华为共赢未来'},
            {'id': 4, 'year': '2021年', 'title': '国家级高新技术企业', 'description': '获得国家级高新技术企业认定，正式迈入高新技术企业行列'}
        ],
        'contacts.json': [],
        'contact_id.txt': '0'
    }
    
    for filename, data in files.items():
        filepath = os.path.join(DATA_DIR, filename)
        if not os.path.exists(filepath):
            with open(filepath, 'w', encoding='utf-8') as f:
                if isinstance(data, (dict, list)):
                    json.dump(data, f, ensure_ascii=False, indent=2)
                else:
                    f.write(str(data))

init_data()

def read_json(filename):
    filepath = os.path.join(DATA_DIR, filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def write_json(filename, data):
    filepath = os.path.join(DATA_DIR, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # 请求频率限制
        client_ip = get_client_ip()
        allowed, message = check_rate_limit(client_ip)
        if not allowed:
            return jsonify({'code': 429, 'message': message}), 429
        
        # 清理过期记录
        cleanup_limits()
        
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(' ')[1]
            except IndexError:
                return jsonify({'code': 401, 'message': 'Token格式错误'}), 401
        
        if not token:
            return jsonify({'code': 401, 'message': '缺少Token'}), 401
        
        try:
            payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            # 将用户信息存入请求上下文
            request.current_user = payload
        except jwt.ExpiredSignatureError:
            return jsonify({'code': 401, 'message': 'Token已过期'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'code': 401, 'message': '无效的Token'}), 401
        
        return f(*args, **kwargs)
    return decorated

def success(data=None, message='成功'):
    return jsonify({'code': 200, 'message': message, 'data': data})

def error(message='失败', code=500):
    return jsonify({'code': code, 'message': message}), code

# 获取客户端IP
def get_client_ip():
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    return request.remote_addr

# 密码强度验证
def validate_password_strength(password):
    """验证密码强度
    要求：至少8位，包含大小写字母、数字
    """
    if len(password) < 8:
        return False, '密码长度至少8位'
    if not re.search(r'[A-Z]', password):
        return False, '密码必须包含大写字母'
    if not re.search(r'[a-z]', password):
        return False, '密码必须包含小写字母'
    if not re.search(r'\d', password):
        return False, '密码必须包含数字'
    return True, None

# 操作日志
operation_logs = []
MAX_LOGS = 1000

def add_operation_log(action, target_type, target_id=None, details=None):
    """添加操作日志"""
    global operation_logs
    log = {
        'id': len(operation_logs) + 1,
        'timestamp': datetime.datetime.now().isoformat(),
        'ip': get_client_ip(),
        'action': action,
        'target_type': target_type,
        'target_id': target_id,
        'details': details,
        'user': getattr(request, 'current_user', {}).get('user_id', 'anonymous')
    }
    operation_logs.append(log)
    # 限制日志数量
    if len(operation_logs) > MAX_LOGS:
        operation_logs = operation_logs[-MAX_LOGS:]
    
    # 同时写入文件
    log_file = os.path.join(DATA_DIR, 'operation_logs.json')
    try:
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(operation_logs, f, ensure_ascii=False, indent=2)
    except:
        pass

# 检查登录限制
def check_login_limit(ip):
    now = time.time()
    if ip in login_attempts:
        attempt = login_attempts[ip]
        # 检查是否还在锁定期间
        if attempt.get('locked_until') and now < attempt['locked_until']:
            remaining = int(attempt['locked_until'] - now)
            return False, f'登录失败次数过多，请{remaining//60}分钟后再试'
        # 超过15分钟重置计数
        if now - attempt.get('last_attempt', 0) > LOCKOUT_DURATION:
            login_attempts[ip] = {'count': 0, 'last_attempt': now}
    else:
        login_attempts[ip] = {'count': 0, 'last_attempt': now}
    return True, None

# 记录登录失败
def record_login_failure(ip):
    if ip not in login_attempts:
        login_attempts[ip] = {'count': 0, 'last_attempt': time.time()}
    login_attempts[ip]['count'] += 1
    login_attempts[ip]['last_attempt'] = time.time()
    
    if login_attempts[ip]['count'] >= MAX_LOGIN_ATTEMPTS:
        login_attempts[ip]['locked_until'] = time.time() + LOCKOUT_DURATION

# 生成验证码
def generate_captcha_code(length=4):
    """生成随机验证码"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def create_captcha_image(code):
    """生成验证码图片"""
    width, height = 120, 40
    image = Image.new('RGB', (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(image)
    
    # 添加干扰线
    for _ in range(5):
        x1 = random.randint(0, width)
        y1 = random.randint(0, height)
        x2 = random.randint(0, width)
        y2 = random.randint(0, height)
        draw.line([(x1, y1), (x2, y2)], fill=(random.randint(100, 200), random.randint(100, 200), random.randint(100, 200)), width=1)
    
    # 添加干扰点
    for _ in range(30):
        x = random.randint(0, width)
        y = random.randint(0, height)
        draw.point((x, y), fill=(random.randint(100, 200), random.randint(100, 200), random.randint(100, 200)))
    
    # 绘制文字
    try:
        font = ImageFont.truetype("arial.ttf", 24)
    except:
        font = ImageFont.load_default()
    
    for i, char in enumerate(code):
        x = 20 + i * 25 + random.randint(-3, 3)
        y = 8 + random.randint(-3, 3)
        color = (random.randint(0, 100), random.randint(0, 100), random.randint(0, 100))
        draw.text((x, y), char, font=font, fill=color)
    
    return image

# 验证码相关API
@app.route('/api/auth/captcha', methods=['GET'])
def get_captcha():
    """获取验证码"""
    captcha_id = hashlib.md5(str(time.time() + random.random()).encode()).hexdigest()[:16]
    code = generate_captcha_code()
    
    # 存储验证码，5分钟有效
    captcha_store[captcha_id] = {
        'code': code.upper(),
        'expires': time.time() + 300
    }
    
    # 生成图片
    image = create_captcha_image(code)
    buffer = io.BytesIO()
    image.save(buffer, format='PNG')
    buffer.seek(0)
    
    response = send_file(buffer, mimetype='image/png')
    response.headers['X-Captcha-ID'] = captcha_id
    return response

@app.route('/api/auth/captcha/verify', methods=['POST'])
def verify_captcha():
    """验证验证码"""
    data = request.get_json()
    captcha_id = data.get('captchaId')
    captcha_code = data.get('captchaCode', '').upper()
    
    if not captcha_id or not captcha_code:
        return error('验证码不能为空', 400)
    
    if captcha_id not in captcha_store:
        return error('验证码已过期，请重新获取', 400)
    
    stored = captcha_store[captcha_id]
    if time.time() > stored['expires']:
        del captcha_store[captcha_id]
        return error('验证码已过期，请重新获取', 400)
    
    if stored['code'] != captcha_code:
        return error('验证码错误', 400)
    
    # 验证成功后删除
    del captcha_store[captcha_id]
    return success(message='验证码正确')

# 认证相关
@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    captcha_id = data.get('captchaId')
    captcha_code = data.get('captchaCode', '').upper()
    
    # 检查登录限制
    client_ip = get_client_ip()
    allowed, message = check_login_limit(client_ip)
    if not allowed:
        return error(message, 429)
    
    # 验证验证码
    if not captcha_id or not captcha_code:
        return error('请输入验证码', 400)
    
    if captcha_id not in captcha_store:
        return error('验证码已过期，请重新获取', 400)
    
    stored = captcha_store[captcha_id]
    if time.time() > stored['expires']:
        del captcha_store[captcha_id]
        return error('验证码已过期，请重新获取', 400)
    
    if stored['code'] != captcha_code:
        record_login_failure(client_ip)
        return error('验证码错误', 400)
    
    # 验证码正确，删除
    del captcha_store[captcha_id]
    
    # 验证用户名密码
    if username == ADMIN_USER['username'] and password == ADMIN_USER['password']:
        # 清除登录失败记录
        if client_ip in login_attempts:
            del login_attempts[client_ip]
        
        token = jwt.encode(
            {'user_id': ADMIN_USER['id'], 'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=8)},
            app.config['SECRET_KEY'],
            algorithm='HS256'
        )
        return success({
            'token': token,
            'user': {'id': ADMIN_USER['id'], 'username': ADMIN_USER['username'], 'name': ADMIN_USER['name']}
        })
    
    record_login_failure(client_ip)
    remaining = MAX_LOGIN_ATTEMPTS - login_attempts[client_ip]['count']
    return error(f'用户名或密码错误，还剩{remaining}次机会', 401)

@app.route('/api/auth/info', methods=['GET'])
@token_required
def get_user_info():
    return success({'id': ADMIN_USER['id'], 'username': ADMIN_USER['username'], 'name': ADMIN_USER['name']})

@app.route('/api/auth/change-password', methods=['POST'])
@token_required
def change_password():
    data = request.get_json()
    old_password = data.get('oldPassword')
    new_password = data.get('newPassword')
    
    global ADMIN_USER
    if old_password != ADMIN_USER['password']:
        add_operation_log('password_change_failed', 'user', ADMIN_USER['id'], {'reason': '原密码错误'})
        return error('原密码错误', 400)
    
    # 验证新密码强度
    valid, msg = validate_password_strength(new_password)
    if not valid:
        return error(msg, 400)
    
    # 检查新密码是否与旧密码相同
    if new_password == old_password:
        return error('新密码不能与旧密码相同', 400)
    
    ADMIN_USER['password'] = new_password
    add_operation_log('password_changed', 'user', ADMIN_USER['id'])
    return success(message='密码修改成功')

# Hero管理
@app.route('/api/hero', methods=['GET'])
@token_required
def get_hero():
    return success(read_json('hero.json'))

@app.route('/api/hero', methods=['PUT'])
@token_required
def update_hero():
    data = request.get_json()
    write_json('hero.json', data)
    return success(message='保存成功')

@app.route('/api/hero/stats', methods=['GET'])
@token_required
def get_stats():
    return success(read_json('stats.json'))

@app.route('/api/hero/stats', methods=['PUT'])
@token_required
def update_stats():
    data = request.get_json()
    write_json('stats.json', data)
    return success(message='保存成功')

# 服务管理
@app.route('/api/services', methods=['GET'])
@token_required
def get_services():
    return success(read_json('services.json'))

@app.route('/api/services', methods=['POST'])
@token_required
def create_service():
    data = request.get_json()
    services = read_json('services.json')
    new_id = max([s['id'] for s in services], default=0) + 1
    data['id'] = new_id
    services.append(data)
    write_json('services.json', services)
    return success(data, '创建成功')

@app.route('/api/services/<int:id>', methods=['PUT'])
@token_required
def update_service(id):
    data = request.get_json()
    services = read_json('services.json')
    for i, s in enumerate(services):
        if s['id'] == id:
            data['id'] = id
            services[i] = data
            write_json('services.json', services)
            return success(data, '更新成功')
    return error('服务不存在', 404)

@app.route('/api/services/<int:id>', methods=['DELETE'])
@token_required
def delete_service(id):
    services = read_json('services.json')
    services = [s for s in services if s['id'] != id]
    write_json('services.json', services)
    return success(message='删除成功')

# 案例管理
@app.route('/api/cases', methods=['GET'])
@token_required
def get_cases():
    category = request.args.get('category', '')
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('pageSize', 10))
    
    cases = read_json('cases.json')
    if category:
        cases = [c for c in cases if c['category'] == category]
    
    total = len(cases)
    start = (page - 1) * page_size
    end = start + page_size
    cases = cases[start:end]
    
    return success({'list': cases, 'total': total})

@app.route('/api/cases', methods=['POST'])
@token_required
def create_case():
    data = request.get_json()
    cases = read_json('cases.json')
    new_id = max([c['id'] for c in cases], default=0) + 1
    data['id'] = new_id
    cases.append(data)
    write_json('cases.json', cases)
    return success(data, '创建成功')

@app.route('/api/cases/<int:id>', methods=['PUT'])
@token_required
def update_case(id):
    data = request.get_json()
    cases = read_json('cases.json')
    for i, c in enumerate(cases):
        if c['id'] == id:
            data['id'] = id
            cases[i] = data
            write_json('cases.json', cases)
            return success(data, '更新成功')
    return error('案例不存在', 404)

@app.route('/api/cases/<int:id>', methods=['DELETE'])
@token_required
def delete_case(id):
    cases = read_json('cases.json')
    cases = [c for c in cases if c['id'] != id]
    write_json('cases.json', cases)
    return success(message='删除成功')

@app.route('/api/cases/categories', methods=['GET'])
@token_required
def get_categories():
    return success([
        {'value': 'website', 'label': '网站建设'},
        {'value': 'app', 'label': 'APP开发'},
        {'value': 'wechat', 'label': '微信开发'},
        {'value': 'miniapp', 'label': '小程序'},
        {'value': 'platform', 'label': '平台开发'}
    ])

# 新闻管理
@app.route('/api/news', methods=['GET'])
@token_required
def get_news():
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('pageSize', 10))
    
    news = read_json('news.json')
    total = len(news)
    start = (page - 1) * page_size
    end = start + page_size
    news = news[start:end]
    
    return success({'list': news, 'total': total})

@app.route('/api/news', methods=['POST'])
@token_required
def create_news():
    data = request.get_json()
    news = read_json('news.json')
    new_id = max([n['id'] for n in news], default=0) + 1
    data['id'] = new_id
    news.append(data)
    write_json('news.json', news)
    return success(data, '创建成功')

@app.route('/api/news/<int:id>', methods=['PUT'])
@token_required
def update_news(id):
    data = request.get_json()
    news = read_json('news.json')
    for i, n in enumerate(news):
        if n['id'] == id:
            data['id'] = id
            news[i] = data
            write_json('news.json', news)
            return success(data, '更新成功')
    return error('新闻不存在', 404)

@app.route('/api/news/<int:id>', methods=['DELETE'])
@token_required
def delete_news(id):
    news = read_json('news.json')
    news = [n for n in news if n['id'] != id]
    write_json('news.json', news)
    return success(message='删除成功')

# 关于我们
@app.route('/api/about', methods=['GET'])
@token_required
def get_about():
    return success(read_json('about.json'))

@app.route('/api/about', methods=['PUT'])
@token_required
def update_about():
    data = request.get_json()
    write_json('about.json', data)
    return success(message='保存成功')

@app.route('/api/about/timeline', methods=['GET'])
@token_required
def get_timeline():
    return success(read_json('timeline.json'))

@app.route('/api/about/timeline', methods=['POST'])
@token_required
def create_timeline():
    data = request.get_json()
    timeline = read_json('timeline.json')
    new_id = max([t['id'] for t in timeline], default=0) + 1
    data['id'] = new_id
    timeline.append(data)
    write_json('timeline.json', timeline)
    return success(data, '创建成功')

@app.route('/api/about/timeline/<int:id>', methods=['PUT'])
@token_required
def update_timeline(id):
    data = request.get_json()
    timeline = read_json('timeline.json')
    for i, t in enumerate(timeline):
        if t['id'] == id:
            data['id'] = id
            timeline[i] = data
            write_json('timeline.json', timeline)
            return success(data, '更新成功')
    return error('历程不存在', 404)

@app.route('/api/about/timeline/<int:id>', methods=['DELETE'])
@token_required
def delete_timeline(id):
    timeline = read_json('timeline.json')
    timeline = [t for t in timeline if t['id'] != id]
    write_json('timeline.json', timeline)
    return success(message='删除成功')

# 联系咨询
@app.route('/api/contacts', methods=['GET'])
@token_required
def get_contacts():
    status = request.args.get('status', '')
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('pageSize', 10))
    
    contacts = read_json('contacts.json')
    if status:
        contacts = [c for c in contacts if c['status'] == status]
    
    # 按时间倒序
    contacts = sorted(contacts, key=lambda x: x.get('created_at', ''), reverse=True)
    
    total = len(contacts)
    start = (page - 1) * page_size
    end = start + page_size
    contacts = contacts[start:end]
    
    return success({'list': contacts, 'total': total})

@app.route('/api/contacts/stats', methods=['GET'])
@token_required
def get_contact_stats():
    contacts = read_json('contacts.json')
    pending = len([c for c in contacts if c.get('status') == 'pending'])
    return success({'pending': pending, 'total': len(contacts)})

@app.route('/api/contacts/<int:id>/status', methods=['PUT'])
@token_required
def update_contact_status(id):
    data = request.get_json()
    contacts = read_json('contacts.json')
    for c in contacts:
        if c['id'] == id:
            c['status'] = data.get('status', 'pending')
            write_json('contacts.json', contacts)
            return success(message='更新成功')
    return error('记录不存在', 404)

@app.route('/api/contacts/<int:id>', methods=['DELETE'])
@token_required
def delete_contact(id):
    contacts = read_json('contacts.json')
    contacts = [c for c in contacts if c['id'] != id]
    write_json('contacts.json', contacts)
    return success(message='删除成功')

# 公开API - 接收客户咨询
@app.route('/api/contact/submit', methods=['POST'])
def submit_contact():
    data = request.get_json()
    
    contacts = read_json('contacts.json')
    
    # 读取并更新ID
    id_file = os.path.join(DATA_DIR, 'contact_id.txt')
    with open(id_file, 'r') as f:
        current_id = int(f.read().strip())
    new_id = current_id + 1
    with open(id_file, 'w') as f:
        f.write(str(new_id))
    
    contact = {
        'id': new_id,
        'name': data.get('name', ''),
        'phone': data.get('phone', ''),
        'company': data.get('company', ''),
        'service': data.get('service', ''),
        'description': data.get('description', ''),
        'status': 'pending',
        'created_at': datetime.datetime.now().isoformat()
    }
    
    contacts.append(contact)
    write_json('contacts.json', contacts)
    
    return success(message='提交成功')

# 公开API - 获取网站数据（无需认证）
@app.route('/api/public/hero', methods=['GET'])
def get_hero_public():
    return success(read_json('hero.json'))

@app.route('/api/public/hero/stats', methods=['GET'])
def get_stats_public():
    return success(read_json('stats.json'))

@app.route('/api/public/services', methods=['GET'])
def get_services_public():
    return success(read_json('services.json'))

@app.route('/api/public/cases', methods=['GET'])
def get_cases_public():
    category = request.args.get('category', '')
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('pageSize', 10))
    
    cases = read_json('cases.json')
    if category:
        cases = [c for c in cases if c['category'] == category]
    
    total = len(cases)
    start = (page - 1) * page_size
    end = start + page_size
    cases = cases[start:end]
    
    return success({'list': cases, 'total': total})

@app.route('/api/public/news', methods=['GET'])
def get_news_public():
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('pageSize', 10))
    
    news = read_json('news.json')
    total = len(news)
    start = (page - 1) * page_size
    end = start + page_size
    news = news[start:end]
    
    return success({'list': news, 'total': total})

@app.route('/api/public/about', methods=['GET'])
def get_about_public():
    return success(read_json('about.json'))

@app.route('/api/public/about/timeline', methods=['GET'])
def get_timeline_public():
    return success(read_json('timeline.json'))

# 数据库备份管理
@app.route('/api/backup', methods=['GET'])
@token_required
def get_backups():
    backups = []
    for filename in os.listdir(BACKUP_DIR):
        if filename.endswith('.zip'):
            filepath = os.path.join(BACKUP_DIR, filename)
            stat = os.stat(filepath)
            backups.append({
                'filename': filename,
                'size': format_file_size(stat.st_size),
                'created_at': datetime.datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
            })
    # 按时间倒序排列
    backups.sort(key=lambda x: x['created_at'], reverse=True)
    return success(backups)

@app.route('/api/backup', methods=['POST'])
@token_required
def create_backup():
    try:
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f'backup_{timestamp}.zip'
        backup_path = os.path.join(BACKUP_DIR, backup_filename)
        
        # 创建ZIP压缩文件
        with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(DATA_DIR):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, DATA_DIR)
                    zipf.write(file_path, arcname)
        
        return success({
            'filename': backup_filename,
            'message': '备份创建成功'
        })
    except Exception as e:
        return error(f'备份失败: {str(e)}')

@app.route('/api/backup/<filename>', methods=['DELETE'])
@token_required
def delete_backup(filename):
    try:
        # 安全检查：防止目录遍历攻击
        if '..' in filename or '/' in filename or '\\' in filename:
            return error('非法文件名', 400)
        
        filepath = os.path.join(BACKUP_DIR, filename)
        if not os.path.exists(filepath):
            return error('备份文件不存在', 404)
        
        os.remove(filepath)
        return success(message='删除成功')
    except Exception as e:
        return error(f'删除失败: {str(e)}')

@app.route('/api/backup/download/<filename>', methods=['GET'])
def download_backup(filename):
    try:
        # 从查询参数获取token
        token = request.args.get('token')
        if not token:
            return error('缺少Token', 401)
        
        try:
            jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            return error('Token已过期', 401)
        except jwt.InvalidTokenError:
            return error('无效的Token', 401)
        
        # 安全检查
        if '..' in filename or '/' in filename or '\\' in filename:
            return error('非法文件名', 400)
        
        filepath = os.path.join(BACKUP_DIR, filename)
        if not os.path.exists(filepath):
            return error('备份文件不存在', 404)
        
        return send_file(filepath, as_attachment=True, download_name=filename)
    except Exception as e:
        return error(f'下载失败: {str(e)}')

@app.route('/api/backup/restore/<filename>', methods=['POST'])
@token_required
def restore_backup(filename):
    try:
        # 安全检查：防止目录遍历攻击
        if '..' in filename or '/' in filename or '\\' in filename:
            return error('非法文件名', 400)
        
        filepath = os.path.join(BACKUP_DIR, filename)
        if not os.path.exists(filepath):
            return error('备份文件不存在', 404)
        
        # 备份当前数据
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        pre_restore_backup = f'pre_restore_{timestamp}.zip'
        pre_restore_path = os.path.join(BACKUP_DIR, pre_restore_backup)
        
        with zipfile.ZipFile(pre_restore_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(DATA_DIR):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, DATA_DIR)
                    zipf.write(file_path, arcname)
        
        # 清空DATA_DIR目录
        for item in os.listdir(DATA_DIR):
            item_path = os.path.join(DATA_DIR, item)
            if os.path.isfile(item_path):
                os.remove(item_path)
            elif os.path.isdir(item_path):
                import shutil
                shutil.rmtree(item_path)
        
        # 解压备份文件到DATA_DIR
        with zipfile.ZipFile(filepath, 'r') as zipf:
            zipf.extractall(DATA_DIR)
        
        return success({
            'message': '恢复成功',
            'pre_restore_backup': pre_restore_backup
        })
    except Exception as e:
        return error(f'恢复失败: {str(e)}')

def format_file_size(size_bytes):
    """格式化文件大小"""
    if size_bytes < 1024:
        return f'{size_bytes} B'
    elif size_bytes < 1024 * 1024:
        return f'{size_bytes / 1024:.2f} KB'
    else:
        return f'{size_bytes / (1024 * 1024):.2f} MB'

@app.route('/upload/<path:filename>')
def serve_upload(filename):
    """提供上传的图片文件访问"""
    return send_file(os.path.join('static', 'uploads', filename))

# ==================== 栏目管理 ====================
def init_columns():
    """初始化栏目数据"""
    filepath = os.path.join(DATA_DIR, 'columns.json')
    if not os.path.exists(filepath):
        default_columns = [
            {
                'id': 1,
                'name': '首页Banner',
                'code': 'hero',
                'type': 'single',
                'description': '首页顶部展示区域',
                'sort': 1,
                'isShow': True,
                'createdAt': datetime.datetime.now().isoformat()
            },
            {
                'id': 2,
                'name': '数据统计',
                'code': 'stats',
                'type': 'single',
                'description': '首页数据统计展示',
                'sort': 2,
                'isShow': True,
                'createdAt': datetime.datetime.now().isoformat()
            },
            {
                'id': 3,
                'name': '服务介绍',
                'code': 'services',
                'type': 'list',
                'description': '公司提供的服务项目',
                'sort': 3,
                'isShow': True,
                'createdAt': datetime.datetime.now().isoformat()
            },
            {
                'id': 4,
                'name': '案例展示',
                'code': 'cases',
                'type': 'list',
                'description': '成功案例展示',
                'sort': 4,
                'isShow': True,
                'createdAt': datetime.datetime.now().isoformat()
            },
            {
                'id': 5,
                'name': '新闻动态',
                'code': 'news',
                'type': 'list',
                'description': '公司新闻和行业动态',
                'sort': 5,
                'isShow': True,
                'createdAt': datetime.datetime.now().isoformat()
            },
            {
                'id': 6,
                'name': '关于我们',
                'code': 'about',
                'type': 'single',
                'description': '公司介绍和发展历程',
                'sort': 6,
                'isShow': True,
                'createdAt': datetime.datetime.now().isoformat()
            },
            {
                'id': 7,
                'name': '联系我们',
                'code': 'contact',
                'type': 'single',
                'description': '联系方式和咨询表单',
                'sort': 7,
                'isShow': True,
                'createdAt': datetime.datetime.now().isoformat()
            }
        ]
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(default_columns, f, ensure_ascii=False, indent=2)

# 初始化栏目数据
init_columns()

@app.route('/api/columns', methods=['GET'])
@token_required
def get_columns():
    """获取栏目列表"""
    columns = read_json('columns.json')
    # 按排序号排序
    columns.sort(key=lambda x: x.get('sort', 0))
    return success(columns)

@app.route('/api/columns', methods=['POST'])
@token_required
def create_column():
    """创建栏目"""
    data = request.get_json()
    
    # 验证必填字段
    if not data.get('name') or not data.get('code'):
        return error('栏目名称和编码不能为空', 400)
    
    columns = read_json('columns.json')
    
    # 检查编码是否已存在
    if any(c['code'] == data['code'] for c in columns):
        return error('栏目编码已存在', 400)
    
    # 生成新ID
    new_id = max([c['id'] for c in columns], default=0) + 1
    
    new_column = {
        'id': new_id,
        'name': data['name'],
        'code': data['code'],
        'type': data.get('type', 'single'),
        'description': data.get('description', ''),
        'sort': data.get('sort', new_id),
        'isShow': data.get('isShow', True),
        'createdAt': datetime.datetime.now().isoformat(),
        'updatedAt': datetime.datetime.now().isoformat()
    }
    
    columns.append(new_column)
    write_json('columns.json', columns)
    return success(new_column, '创建成功')

@app.route('/api/columns/<int:id>', methods=['PUT'])
@token_required
def update_column(id):
    """更新栏目"""
    data = request.get_json()
    columns = read_json('columns.json')
    
    for i, col in enumerate(columns):
        if col['id'] == id:
            # 检查编码是否与其他栏目冲突
            if data.get('code') and data['code'] != col['code']:
                if any(c['code'] == data['code'] and c['id'] != id for c in columns):
                    return error('栏目编码已存在', 400)
            
            # 更新字段
            col['name'] = data.get('name', col['name'])
            col['code'] = data.get('code', col['code'])
            col['type'] = data.get('type', col['type'])
            col['description'] = data.get('description', col.get('description', ''))
            col['sort'] = data.get('sort', col.get('sort', col['id']))
            col['isShow'] = data.get('isShow', col.get('isShow', True))
            col['updatedAt'] = datetime.datetime.now().isoformat()
            
            write_json('columns.json', columns)
            return success(col, '更新成功')
    
    return error('栏目不存在', 404)

@app.route('/api/columns/<int:id>', methods=['DELETE'])
@token_required
def delete_column(id):
    """删除栏目"""
    columns = read_json('columns.json')
    
    # 查找要删除的栏目
    column_to_delete = None
    for col in columns:
        if col['id'] == id:
            column_to_delete = col
            break
    
    if not column_to_delete:
        return error('栏目不存在', 404)
    
    # 检查是否为系统内置栏目（保护关键栏目）
    protected_codes = ['hero', 'about', 'contact']
    if column_to_delete['code'] in protected_codes:
        return error('系统内置栏目不能删除', 400)
    
    columns = [c for c in columns if c['id'] != id]
    write_json('columns.json', columns)
    return success(message='删除成功')

@app.route('/api/columns/<int:id>/toggle', methods=['POST'])
@token_required
def toggle_column_status(id):
    """切换栏目显示状态"""
    columns = read_json('columns.json')
    
    for col in columns:
        if col['id'] == id:
            col['isShow'] = not col.get('isShow', True)
            col['updatedAt'] = datetime.datetime.now().isoformat()
            write_json('columns.json', columns)
            return success(col, '状态更新成功')
    
    return error('栏目不存在', 404)

@app.route('/api/columns/sort', methods=['POST'])
@token_required
def sort_columns():
    """批量更新栏目排序"""
    data = request.get_json()
    sort_data = data.get('sortData', [])
    
    if not sort_data:
        return error('排序数据不能为空', 400)
    
    columns = read_json('columns.json')
    
    for item in sort_data:
        for col in columns:
            if col['id'] == item['id']:
                col['sort'] = item['sort']
                col['updatedAt'] = datetime.datetime.now().isoformat()
                break
    
    write_json('columns.json', columns)
    return success(message='排序更新成功')

# 操作日志查询
@app.route('/api/logs', methods=['GET'])
@token_required
def get_operation_logs():
    """获取操作日志"""
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('pageSize', 20))
    action = request.args.get('action', '')
    
    logs = operation_logs[:]
    
    # 筛选
    if action:
        logs = [log for log in logs if action in log.get('action', '')]
    
    # 按时间倒序
    logs.reverse()
    
    total = len(logs)
    start = (page - 1) * page_size
    end = start + page_size
    logs = logs[start:end]
    
    return success({'list': logs, 'total': total})

# 安全概览
@app.route('/api/security/overview', methods=['GET'])
@token_required
def get_security_overview():
    """获取安全概览数据"""
    # 统计登录失败次数
    failed_logins = sum(1 for log in operation_logs if 'password_change_failed' in log.get('action', ''))
    
    # 统计当前被锁定的IP
    locked_ips = [ip for ip, data in login_attempts.items() if data.get('locked_until') and time.time() < data['locked_until']]
    
    # 今日操作数
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    today_ops = sum(1 for log in operation_logs if log.get('timestamp', '').startswith(today))
    
    return success({
        'failedLogins': failed_logins,
        'lockedIPs': len(locked_ips),
        'lockedIPList': locked_ips,
        'todayOperations': today_ops,
        'totalLogs': len(operation_logs),
        'rateLimitWindow': RATE_LIMIT_WINDOW,
        'rateLimitMax': RATE_LIMIT_MAX
    })

# 公开API - 获取栏目列表（用于前端展示）
@app.route('/api/public/columns', methods=['GET'])
def get_columns_public():
    """获取启用的栏目列表（公开接口）"""
    columns = read_json('columns.json')
    # 只返回启用的栏目
    columns = [c for c in columns if c.get('isShow', True)]
    # 按排序号排序
    columns.sort(key=lambda x: x.get('sort', 0))
    # 只返回必要字段
    result = [{
        'id': c['id'],
        'name': c['name'],
        'code': c['code'],
        'type': c['type'],
        'description': c.get('description', '')
    } for c in columns]
    return success(result)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
