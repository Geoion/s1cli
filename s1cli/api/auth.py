"""登录认证和用户管理"""
import re
import logging
from typing import Dict, Any, Optional
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from s1cli.api.client import S1Client

logger = logging.getLogger(__name__)


class AuthAPI:
    """认证 API"""
    
    def __init__(self, client: S1Client):
        """初始化认证 API
        
        Args:
            client: HTTP 客户端
        """
        self.client = client
        self.config = client.config
    
    def login(self, username: str, password: str) -> bool:
        """登录 Stage1st
        
        Args:
            username: 用户名
            password: 密码
            
        Returns:
            是否登录成功
        """
        try:
            # 1. 获取登录页面，提取 formhash 和 loginhash
            login_page_response = self.client.get("member.php?mod=logging&action=login")
            login_page_html = login_page_response.text
            
            formhash, loginhash = self._extract_login_hashes(login_page_html)
            
            if not formhash:
                raise Exception("无法获取 formhash")
            
            # 2. 构造登录请求
            login_data = {
                "mod": "logging",
                "action": "login",
                "loginsubmit": "yes",
                "infloat": "yes",
                "lssubmit": "yes",
                "inajax": "1",
                "username": username,
                "password": password,
                "questionid": "0",
                "answer": "",
                "cookietime": "2592000",  # 30天
                "quickforward": "yes",
                "handlekey": f"ls{loginhash}" if loginhash else "ls",
            }
            
            # 3. 发送登录请求
            login_response = self.client.post(
                f"member.php?mod=logging&action=login&loginsubmit=yes&loginhash={loginhash}",
                data=login_data
            )
            
            # 4. 检查登录是否成功
            if login_response.status_code == 200:
                # 检查响应中是否包含成功标志
                response_text = login_response.text
                
                # Discuz 登录成功后会返回包含用户信息的页面或重定向
                if "succeedhandle" in response_text or "欢迎" in response_text:
                    # 保存用户信息
                    self.config.set_user_info(username)
                    return True
                elif "登录失败" in response_text or "密码错误" in response_text:
                    return False
                else:
                    # 尝试验证登录状态
                    return self.check_login()
            
            return False
            
        except Exception as e:
            logger.error("登录异常 user=%s: %s", username, e)
            raise
    
    def _extract_login_hashes(self, html: str) -> tuple[Optional[str], Optional[str]]:
        """从登录页面提取 formhash 和 loginhash
        
        Args:
            html: 登录页面 HTML
            
        Returns:
            (formhash, loginhash) 元组
        """
        soup = BeautifulSoup(html, 'lxml')
        
        formhash = None
        loginhash = None
        
        # 提取 formhash
        formhash_input = soup.find('input', {'name': 'formhash'})
        if formhash_input:
            formhash = formhash_input.get('value')
        
        # 提取 loginhash（可能在 URL 或隐藏字段中）
        login_form = soup.find('form', {'name': 'login'})
        if login_form:
            action = login_form.get('action', '')
            if 'loginhash=' in action:
                loginhash = action.split('loginhash=')[1].split('&')[0]
        
        # 备选方案：从脚本中提取
        if not loginhash:
            for script in soup.find_all('script'):
                script_text = script.string or ''
                if 'loginhash' in script_text:
                    match = re.search(r'loginhash[\'"]?\s*[:=]\s*[\'"]([a-zA-Z0-9]+)', script_text)
                    if match:
                        loginhash = match.group(1)
                        break
        
        return formhash, loginhash
    
    def check_login(self) -> bool:
        """检查是否已登录
        
        Returns:
            是否已登录
        """
        try:
            # 访问个人中心页面
            response = self.client.get("home.php?mod=space&do=profile")
            
            if response.status_code == 200:
                html = response.text
                soup = BeautifulSoup(html, 'lxml')
                
                # 检查是否包含用户名
                # Discuz 登录后会在页面中显示用户名
                user_info_div = soup.find('div', {'id': 'um'}) or soup.find('div', class_='vwmy')
                if user_info_div:
                    # 找到用户名
                    username_link = user_info_div.find('a', {'class': 'vwmy'}) or user_info_div.find('strong')
                    if username_link:
                        username = username_link.get_text(strip=True)
                        if username and username != '游客':
                            return True
                
                # 备选方案：检查是否有登录后才有的元素
                if '退出' in html or 'logout' in html.lower():
                    return True
            
            return False
            
        except Exception as e:
            logger.warning("检查登录状态异常：%s", e)
            return False
    
    def logout(self) -> bool:
        """登出
        
        Returns:
            是否登出成功
        """
        try:
            # 获取 formhash（Discuz 登出必须携带，否则请求会被拒绝）
            response = self.client.get("index.php")
            soup = BeautifulSoup(response.text, 'lxml')
            
            formhash_input = soup.find('input', {'name': 'formhash'})
            formhash = formhash_input.get('value') if formhash_input else ''
            
            if not formhash:
                raise ValueError("无法获取 formhash，可能未登录或页面结构已变更")
            
            # 发送登出请求
            self.client.get(f"member.php?mod=logging&action=logout&formhash={formhash}")
            
            # 清除本地会话
            self.config.clear_session()
            
            return True
            
        except Exception as e:
            logger.error("登出异常：%s", e)
            raise
    
    def get_user_info(self) -> Dict[str, Any]:
        """获取用户信息
        
        Returns:
            用户信息字典
        """
        try:
            # 从配置中获取保存的用户信息
            user_info = self.config.get_user_info()
            
            if not user_info:
                return {}
            
            # 可以选择从服务器获取最新信息
            response = self.client.get("home.php?mod=space&do=profile")
            if response.status_code == 200:
                html = response.text
                soup = BeautifulSoup(html, 'lxml')
                
                # 提取更多用户信息
                # 这里可以根据实际页面结构提取信息
                # 例如：积分、发帖数等
                
                # 简单示例
                profile_div = soup.find('div', class_='profile')
                if profile_div:
                    # 提取信息...
                    pass
            
            return user_info
            
        except Exception as e:
            logger.warning("获取用户信息异常，回退到本地缓存：%s", e)
            return self.config.get_user_info()
    
    def daily_checkin(self) -> Dict[str, Any]:
        """每日签到打卡
        
        判断逻辑：访问首页，检查右上角是否存在"打卡签到"按钮。
        - 存在该按钮 → 尚未签到，点击链接执行签到
        - 不存在该按钮 → 今天已经签到过了
        
        Returns:
            签到结果字典，包含：
            - success: 是否成功
            - already_checked: 是否已经签到过
            - message: 提示信息
            - reward: 奖励信息（如果有）
        """
        result = {
            'success': False,
            'already_checked': False,
            'message': '',
            'reward': None
        }
        
        try:
            # 1. 访问首页，检查是否存在"打卡签到"按钮
            index_response = self.client.get("index.php")
            if index_response.status_code != 200:
                result['message'] = "无法访问论坛首页"
                return result
            
            soup = BeautifulSoup(index_response.text, 'lxml')
            
            # 查找"打卡签到"链接（位于右上角头像附近）
            checkin_link = soup.find('a', string=lambda t: t and '打卡签到' in t)
            if checkin_link is None:
                # 也尝试通过 href 包含 daily_attendance 来查找
                checkin_link = soup.find('a', href=lambda x: x and 'daily_attendance' in str(x))
            
            if checkin_link is None:
                # 页面中没有"打卡签到"按钮，说明今天已经签到过了
                result['success'] = True
                result['already_checked'] = True
                result['message'] = "今天已经签到过了"
                return result
            
            # 2. 找到签到链接，提取签到 URL
            checkin_href = checkin_link.get('href', '')
            
            # href 可能是完整 URL 或相对路径，统一处理
            if checkin_href.startswith('http'):
                parsed = urlparse(checkin_href)
                checkin_path = parsed.path.lstrip('/')
                if parsed.query:
                    checkin_path += '?' + parsed.query
            else:
                checkin_path = checkin_href.lstrip('/')
            
            # 3. 发送签到请求
            checkin_response = self.client.get(checkin_path)
            
            if checkin_response.status_code != 200:
                result['message'] = f"签到请求失败，状态码：{checkin_response.status_code}"
                return result
            
            # 4. 解析签到结果
            response_html = checkin_response.text
            response_soup = BeautifulSoup(response_html, 'lxml')
            
            # 提取提示信息，只取第一个 <p> 段落，避免把"请点击此链接"等跳转文字一并带出
            msg_elem = (
                response_soup.find('div', id='messagetext') or
                response_soup.find('div', class_='c') or
                response_soup.find('div', class_='alert_info') or
                response_soup.find('div', class_='alert_right')
            )
            if msg_elem:
                first_p = msg_elem.find('p')
                msg_text = first_p.get_text(strip=True) if first_p else msg_elem.get_text(strip=True)
                # 去掉 Discuz 自动跳转提示语
                for noise in ('如果您的浏览器没有自动跳转，请点击此链接', '点击此处'):
                    msg_text = msg_text.replace(noise, '').strip()
            else:
                msg_text = ''
            
            if '签到成功' in response_html or '打卡成功' in response_html:
                result['success'] = True
                result['message'] = msg_text or "签到成功！"
                
                # 尝试提取奖励数值
                reward_info = {}
                coin_match = re.search(r'(\d+)\s*金币', msg_text)
                if coin_match:
                    reward_info['coins'] = int(coin_match.group(1))
                credit_match = re.search(r'(\d+)\s*积分', msg_text)
                if credit_match:
                    reward_info['credits'] = int(credit_match.group(1))
                if reward_info:
                    result['reward'] = reward_info
                    
            elif '已经签到' in response_html or '今天已签' in response_html or '重复签到' in response_html:
                result['success'] = True
                result['already_checked'] = True
                result['message'] = msg_text or "今天已经签到过了"
                
            elif '需要登录' in response_html or '请先登录' in response_html:
                result['message'] = "需要先登录"
                
            else:
                error_elem = response_soup.find('div', class_='alert_error') or \
                             response_soup.find('div', class_='error')
                if error_elem:
                    result['message'] = error_elem.get_text(strip=True)
                elif msg_text:
                    result['message'] = msg_text
                else:
                    result['message'] = "签到失败，原因未知"
            
            return result
            
        except Exception as e:
            logger.error("签到异常：%s", e)
            result['message'] = f"签到异常：{e}"
            return result




