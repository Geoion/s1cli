"""登录认证和用户管理"""
from typing import Dict, Any, Optional
from bs4 import BeautifulSoup
from s1cli.api.client import S1Client


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
            print(f"登录异常：{e}")
            return False
    
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
            scripts = soup.find_all('script')
            for script in scripts:
                script_text = script.string or ''
                if 'loginhash' in script_text:
                    # 简单的字符串匹配
                    import re
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
            print(f"检查登录状态异常：{e}")
            return False
    
    def logout(self) -> bool:
        """登出
        
        Returns:
            是否登出成功
        """
        try:
            # 获取 formhash
            response = self.client.get("index.php")
            html = response.text
            soup = BeautifulSoup(html, 'lxml')
            
            formhash_input = soup.find('input', {'name': 'formhash'})
            formhash = formhash_input.get('value') if formhash_input else ''
            
            # 发送登出请求
            self.client.get(f"member.php?mod=logging&action=logout&formhash={formhash}")
            
            # 清除本地会话
            self.config.clear_session()
            
            return True
            
        except Exception as e:
            print(f"登出异常：{e}")
            return False
    
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
            print(f"获取用户信息异常：{e}")
            return self.config.get_user_info()



