"""帖子相关 API"""
from typing import List, Optional
from bs4 import BeautifulSoup
from datetime import datetime
from s1cli.api.client import S1Client
from s1cli.models.thread import Thread, Post


class ThreadAPI:
    """帖子 API"""
    
    def __init__(self, client: S1Client):
        """初始化帖子 API
        
        Args:
            client: HTTP 客户端
        """
        self.client = client
    
    def get_thread(self, thread_id: str, page: int = 1) -> Optional[Thread]:
        """获取帖子详情
        
        Args:
            thread_id: 帖子 ID
            page: 页码
            
        Returns:
            帖子对象
        """
        try:
            url = f"thread-{thread_id}-{page}-1.html"
            response = self.client.get(url)
            html = response.text
            soup = BeautifulSoup(html, 'lxml')
            
            # 提取帖子标题
            title_elem = soup.find('span', id='thread_subject') or soup.find('h1', class_='ts')
            title = title_elem.get_text(strip=True) if title_elem else "未知标题"
            
            # 提取作者信息和发帖时间
            author_elem = soup.find('div', class_='authi')
            author = ''
            created_time = None
            if author_elem:
                author_link = author_elem.find('a', class_='xw1')
                author = author_link.get_text(strip=True) if author_link else ''
            
            # 提取发帖时间（楼主的时间）
            first_post_div = soup.find('div', id=lambda x: x and x.startswith('post_'))
            if first_post_div:
                time_elem = first_post_div.find('em', id=lambda x: x and x.startswith('authorposton'))
                if time_elem:
                    time_text = time_elem.get_text(strip=True)
                    if '发表于' in time_text:
                        created_time = time_text.replace('发表于', '').strip()
                    else:
                        created_time = time_text
            
            # 提取浏览数和回复数
            # 格式: <span class="xg1">查看:</span> <span class="xi1">38628</span><span class="pipe">|</span><span class="xg1">回复:</span> <span class="xi1">280</span>
            views = 0
            replies = 0
            
            # 找到包含统计信息的区域
            stats_div = soup.find('div', class_='hm ptn')
            if stats_div:
                # 找到所有 xi1 标签（包含数字）
                xi1_spans = stats_div.find_all('span', class_='xi1')
                if len(xi1_spans) >= 2:
                    try:
                        views = int(xi1_spans[0].get_text(strip=True))
                        replies = int(xi1_spans[1].get_text(strip=True))
                    except:
                        pass
            
            # 提取楼主内容
            first_post = soup.find('td', id=lambda x: x and x.startswith('postmessage_'))
            content = ''
            if first_post:
                # 移除引用和签名
                for quote in first_post.find_all('div', class_='quote'):
                    quote.decompose()
                for sign in first_post.find_all('div', id=lambda x: x and 'sign_' in x):
                    sign.decompose()
                
                # 收集所有链接（从 <a> 标签获取完整 URL）
                url_map = {}  # 存储 text -> href 的映射
                for link in first_post.find_all('a'):
                    href = link.get('href', '')
                    if href and ('http://' in href or 'https://' in href):
                        # 获取链接的文本（可能被省略）
                        link_text = link.get_text(strip=True)
                        url_map[link_text] = href
                        # 将链接替换为完整 URL 文本
                        link.replace_with(href)
                
                # 使用 separator 参数保留换行
                content = first_post.get_text(separator='\n', strip=True)
                
                # 处理所有 URL（包括 <a> 标签中的和纯文本的）
                import re
                from urllib.parse import urlparse
                
                # 匹配 http:// 或 https:// 开头的 URL
                url_pattern = r'(https?://[^\s\u200b]+)'
                
                def replace_url(match):
                    url = match.group(1)
                    # 移除末尾的特殊字符和零宽空格
                    url = url.rstrip('​​​')
                    try:
                        parsed = urlparse(url)
                        domain = parsed.netloc
                        if domain.startswith('www.'):
                            domain = domain[4:]
                        return f'[link={url}]【跳转至{domain}】[/link]'
                    except:
                        return url
                
                content = re.sub(url_pattern, replace_url, content)
            
            # 提取总页数信息
            total_pages = 1
            current_page = page
            page_info = soup.find('span', title=lambda x: x and '共' in str(x) and '页' in str(x))
            if page_info:
                import re
                match = re.search(r'共\s*(\d+)\s*页', page_info.get('title', ''))
                if match:
                    total_pages = int(match.group(1))
            
            # 创建 Thread 对象
            thread = Thread(
                id=thread_id,
                title=title,
                author=author,
                content=content,
                views=views,
                replies=replies,
                created_at=created_time,  # 添加发帖时间
                current_page=current_page,
                total_pages=total_pages
            )
            
            # 提取回复列表
            posts = self._extract_posts(soup, thread_id)
            thread.posts = posts
            
            return thread
            
        except Exception as e:
            print(f"获取帖子详情异常：{e}")
            return None
    
    def _extract_posts(self, soup: BeautifulSoup, thread_id: str) -> List[Post]:
        """从页面提取回复列表
        
        Args:
            soup: BeautifulSoup 对象
            thread_id: 帖子 ID
            
        Returns:
            回复列表
        """
        posts = []
        
        # 查找所有回复
        post_divs = soup.find_all('div', id=lambda x: x and x.startswith('post_'))
        
        for post_div in post_divs:
            try:
                # 提取回复 ID
                post_id = post_div.get('id', '').replace('post_', '')
                
                # 提取楼层号 - 楼层号在 <a id="postnumXXX"> 内的 <em> 标签中
                floor = 0
                postnum_link = post_div.find('a', id=lambda x: x and x.startswith('postnum'))
                if postnum_link:
                    floor_em = postnum_link.find('em')
                    if floor_em:
                        floor_text = floor_em.get_text(strip=True)
                        try:
                            floor = int(floor_text)
                        except:
                            # 可能是 "沙发"、"板凳" 等
                            floor_map = {"沙发": 2, "板凳": 3, "地板": 4}
                            floor = floor_map.get(floor_text, 0)
                    elif '楼主' in postnum_link.get_text():
                        floor = 1
                
                # 提取作者
                author_elem = post_div.find('div', class_='authi')
                author = ''
                if author_elem:
                    author_link = author_elem.find('a', class_='xw1')
                    author = author_link.get_text(strip=True) if author_link else ''
                
                # 提取回复时间
                post_time_elem = post_div.find('em', id=lambda x: x and x.startswith('authorposton'))
                post_time = None
                if post_time_elem:
                    time_text = post_time_elem.get_text(strip=True)
                    # 解析时间格式 "发表于 2025-6-5 10:19"
                    if '发表于' in time_text:
                        post_time = time_text.replace('发表于', '').strip()
                    else:
                        post_time = time_text
                
                # 提取回复内容
                content_elem = post_div.find('td', id=lambda x: x and x.startswith('postmessage_'))
                content = ''
                if content_elem:
                    # 移除引用和签名
                    for quote in content_elem.find_all('div', class_='quote'):
                        quote.decompose()
                    for sign in content_elem.find_all('div', id=lambda x: x and 'sign_' in x):
                        sign.decompose()
                    
                    # 收集所有链接（从 <a> 标签获取完整 URL）
                    url_map = {}  # 存储 text -> href 的映射
                    for link in content_elem.find_all('a'):
                        href = link.get('href', '')
                        if href and ('http://' in href or 'https://' in href):
                            # 获取链接的文本（可能被省略）
                            link_text = link.get_text(strip=True)
                            url_map[link_text] = href
                            # 将链接替换为完整 URL 文本
                            link.replace_with(href)
                    
                    # 使用 separator 参数保留换行
                    content = content_elem.get_text(separator='\n', strip=True)
                    
                    # 处理所有 URL（包括 <a> 标签中的和纯文本的）
                    import re
                    from urllib.parse import urlparse
                    
                    # 匹配 http:// 或 https:// 开头的 URL
                    url_pattern = r'(https?://[^\s\u200b]+)'
                    
                    def replace_url(match):
                        url = match.group(1)
                        # 移除末尾的特殊字符和零宽空格
                        url = url.rstrip('​​​')
                        try:
                            parsed = urlparse(url)
                            domain = parsed.netloc
                            if domain.startswith('www.'):
                                domain = domain[4:]
                            return f'[link={url}]【跳转至{domain}】[/link]'
                        except:
                            return url
                    
                    content = re.sub(url_pattern, replace_url, content)
                
                if post_id and floor > 1:  # 跳过楼主（楼层1），只保留回复
                    post = Post(
                        id=post_id,
                        thread_id=thread_id,
                        floor=floor,
                        author=author,
                        content=content,
                        post_time=post_time
                    )
                    posts.append(post)
                    
            except Exception as e:
                # 跳过解析失败的回复
                continue
        
        return posts
    
    def create_thread(
        self, 
        forum_id: str, 
        title: str, 
        content: str,
        **kwargs
    ) -> Optional[str]:
        """发布新帖
        
        Args:
            forum_id: 版块 ID
            title: 帖子标题
            content: 帖子内容
            **kwargs: 其他参数（如分类、标签等）
            
        Returns:
            新帖子的 ID，失败返回 None
        """
        try:
            # 1. 获取发帖页面，提取 formhash
            post_page_url = f"forum.php?mod=post&action=newthread&fid={forum_id}"
            response = self.client.get(post_page_url)
            html = response.text
            soup = BeautifulSoup(html, 'lxml')
            
            # 提取 formhash
            formhash_input = soup.find('input', {'name': 'formhash'})
            formhash = formhash_input.get('value') if formhash_input else ''
            
            if not formhash:
                raise Exception("无法获取 formhash")
            
            # 2. 构造发帖数据
            post_data = {
                'formhash': formhash,
                'posttime': str(int(datetime.now().timestamp())),
                'wysiwyg': '1',
                'subject': title,
                'message': content,
                'topicsubmit': 'yes',
                'save': '',
            }
            
            # 添加其他参数
            post_data.update(kwargs)
            
            # 3. 提交发帖请求
            post_response = self.client.post(
                f"forum.php?mod=post&action=newthread&fid={forum_id}&extra=&topicsubmit=yes",
                data=post_data
            )
            
            # 4. 从响应中提取新帖子 ID
            if post_response.status_code == 200:
                # 检查是否有重定向或成功标志
                response_html = post_response.text
                
                # 尝试从 URL 或页面中提取帖子 ID
                if 'tid=' in response_html:
                    import re
                    match = re.search(r'tid=(\d+)', response_html)
                    if match:
                        return match.group(1)
                elif 'thread-' in response_html:
                    import re
                    match = re.search(r'thread-(\d+)-', response_html)
                    if match:
                        return match.group(1)
            
            return None
            
        except Exception as e:
            print(f"发帖异常：{e}")
            return None
    
    def reply_thread(
        self,
        thread_id: str,
        content: str,
        quote_post_id: Optional[str] = None
    ) -> Optional[str]:
        """回复帖子
        
        Args:
            thread_id: 帖子 ID
            content: 回复内容
            quote_post_id: 引用的回复 ID（可选）
            
        Returns:
            新回复的 ID，失败返回 None
        """
        try:
            # 1. 获取回复页面，提取 formhash
            reply_url = f"forum.php?mod=post&action=reply&tid={thread_id}"
            if quote_post_id:
                reply_url += f"&repquote={quote_post_id}"
            
            response = self.client.get(reply_url)
            html = response.text
            soup = BeautifulSoup(html, 'lxml')
            
            # 提取 formhash
            formhash_input = soup.find('input', {'name': 'formhash'})
            formhash = formhash_input.get('value') if formhash_input else ''
            
            if not formhash:
                raise Exception("无法获取 formhash")
            
            # 2. 构造回复数据
            reply_data = {
                'formhash': formhash,
                'posttime': str(int(datetime.now().timestamp())),
                'wysiwyg': '1',
                'message': content,
                'replysubmit': 'yes',
                'save': '',
            }
            
            if quote_post_id:
                reply_data['noticeauthor'] = ''
                reply_data['noticetrimstr'] = ''
                reply_data['noticeauthormsg'] = ''
                reply_data['reppid'] = quote_post_id
                reply_data['reppost'] = quote_post_id
            
            # 3. 提交回复请求
            reply_response = self.client.post(
                f"forum.php?mod=post&action=reply&tid={thread_id}&replysubmit=yes",
                data=reply_data
            )
            
            # 4. 检查回复是否成功
            if reply_response.status_code == 200:
                response_html = reply_response.text
                
                # 尝试提取回复 ID
                if 'pid=' in response_html:
                    import re
                    match = re.search(r'pid=(\d+)', response_html)
                    if match:
                        return match.group(1)
            
            return None
            
        except Exception as e:
            print(f"回复异常：{e}")
            return None

