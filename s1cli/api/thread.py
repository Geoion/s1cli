"""帖子相关 API"""
import re
import logging
from typing import List, Optional
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from datetime import datetime
from s1cli.api.client import S1Client
from s1cli.models.thread import Thread, Post
from s1cli.utils import get_signature

logger = logging.getLogger(__name__)

_URL_PATTERN = re.compile(r'(https?://[^\s\u200b]+)')


class ThreadAPI:
    """帖子 API"""
    
    def __init__(self, client: S1Client):
        self.client = client

    @staticmethod
    def _process_content_elem(elem) -> str:
        """提取帖子/回复内容，替换链接为可读格式"""
        for quote in elem.find_all('div', class_='quote'):
            quote.decompose()
        for sign in elem.find_all('div', id=lambda x: x and 'sign_' in x):
            sign.decompose()

        for link in elem.find_all('a'):
            href = link.get('href', '')
            if href and ('http://' in href or 'https://' in href):
                link.replace_with(href)

        text = elem.get_text(separator='\n', strip=True)

        def _replace_url(match):
            url = match.group(1).rstrip('\u200b\u200c\u200d')
            try:
                domain = urlparse(url).netloc.lstrip('www.')
                return f'[link={url}]【跳转至{domain}】[/link]'
            except Exception:
                return url

        return _URL_PATTERN.sub(_replace_url, text)
    
    def get_thread(self, thread_id: str, page: int = 1) -> Thread:
        """获取帖子详情
        
        Args:
            thread_id: 帖子 ID
            page: 页码
            
        Returns:
            帖子对象
            
        Raises:
            Exception: 网络请求失败或页面解析失败时抛出
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
                    except ValueError as e:
                        logger.debug("解析查看/回复数失败：%s", e)
            
            # 提取楼主内容
            first_post = soup.find('td', id=lambda x: x and x.startswith('postmessage_'))
            content = ''
            if first_post:
                content = self._process_content_elem(first_post)
            
            # 提取总页数信息
            total_pages = 1
            current_page = page
            page_info = soup.find('span', title=lambda x: x and '共' in str(x) and '页' in str(x))
            if page_info:
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
            logger.error("获取帖子详情异常 tid=%s page=%s: %s", thread_id, page, e)
            raise
    
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
                        except ValueError:
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
                    content = self._process_content_elem(content_elem)
                
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
                logger.debug("解析回复失败，已跳过 post_div id=%s: %s",
                             post_div.get('id', '?'), e)
                continue
        
        return posts
    
    def create_thread(
        self, 
        forum_id: str, 
        title: str, 
        content: str,
        **kwargs
    ) -> str:
        """发布新帖
        
        Args:
            forum_id: 版块 ID
            title: 帖子标题
            content: 帖子内容
            **kwargs: 其他参数（如分类、标签等）
            
        Returns:
            新帖子的 ID
            
        Raises:
            Exception: 发帖失败时抛出
        """
        try:
            # 在内容末尾添加签名
            content_with_signature = content + get_signature()
            
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
                'message': content_with_signature,
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
                match = re.search(r'tid=(\d+)', response_html)
                if match:
                    return match.group(1)
                match = re.search(r'thread-(\d+)-', response_html)
                if match:
                    return match.group(1)

            raise RuntimeError("发帖请求已提交但无法提取帖子 ID，请检查论坛页面")
            
        except Exception as e:
            logger.error("发帖异常 fid=%s title=%s: %s", forum_id, title, e)
            raise
    
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
            新回复的 ID（部分情况下论坛不返回 ID，此时为 None）
            
        Raises:
            Exception: 回复失败时抛出
        """
        try:
            # 在内容末尾添加签名
            content_with_signature = content + get_signature()
            
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
                'message': content_with_signature,
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
                match = re.search(r'pid=(\d+)', response_html)
                if match:
                    return match.group(1)
            
            return None
            
        except Exception as e:
            logger.error("回复异常 tid=%s: %s", thread_id, e)
            raise

    def favorite_thread(self, thread_id: str) -> dict:
        """收藏帖子

        Args:
            thread_id: 帖子 ID

        Returns:
            结果字典，包含：
            - success: 是否成功
            - already_favorited: 是否已收藏过
            - message: 提示信息

        Raises:
            Exception: 网络请求失败时抛出
        """
        result = {'success': False, 'already_favorited': False, 'message': ''}

        try:
            # 1. 从首页获取 formhash
            index_resp = self.client.get("index.php")
            soup = BeautifulSoup(index_resp.text, 'lxml')
            fh_input = soup.find('input', {'name': 'formhash'})
            formhash = fh_input.get('value', '') if fh_input else ''

            if not formhash:
                raise ValueError("无法获取 formhash，请确认已登录")

            # 2. 发送收藏请求
            url = (
                f"home.php?mod=spacecp&ac=favorite&type=thread"
                f"&id={thread_id}&formhash={formhash}"
            )
            resp = self.client.get(url)
            html = resp.text

            # 3. 解析结果
            resp_soup = BeautifulSoup(html, 'lxml')
            msg_elem = (
                resp_soup.find('div', id='messagetext') or
                resp_soup.find('div', class_='c') or
                resp_soup.find('div', class_='alert_info')
            )
            msg_text = msg_elem.get_text(strip=True) if msg_elem else ''

            if '已经收藏' in html or '重复收藏' in html or '已收藏' in html:
                result['success'] = True
                result['already_favorited'] = True
                result['message'] = msg_text or "该帖子已在收藏夹中"
            elif '收藏成功' in html or '添加收藏' in html or 'succeed' in html.lower():
                result['success'] = True
                result['message'] = msg_text or "收藏成功！"
            elif '需要登录' in html or '请先登录' in html:
                result['message'] = "需要先登录"
            else:
                result['message'] = msg_text or "收藏失败，原因未知"

            return result

        except Exception as e:
            logger.error("收藏帖子异常 tid=%s: %s", thread_id, e)
            raise

