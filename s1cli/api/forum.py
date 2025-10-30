"""论坛版块和帖子列表 API"""
from typing import List, Optional
from bs4 import BeautifulSoup
from datetime import datetime
from s1cli.api.client import S1Client
from s1cli.models.forum import Forum
from s1cli.models.thread import Thread


class ForumAPI:
    """论坛 API"""
    
    def __init__(self, client: S1Client):
        """初始化论坛 API
        
        Args:
            client: HTTP 客户端
        """
        self.client = client
    
    def get_forum_list(self) -> List[Forum]:
        """获取论坛版块列表
        
        Returns:
            版块列表
        """
        try:
            # 访问主论坛页面 (gid=1)
            response = self.client.get("forum.php?gid=1")
            html = response.text
            soup = BeautifulSoup(html, 'lxml')
            
            forums = []
            import re
            
            # Stage1st 主论坛使用 <table class="fl_tb"> 结构
            table = soup.find('table', class_='fl_tb')
            
            if not table:
                return forums
            
            # 遍历表格的每一行
            trs = table.find_all('tr')
            for tr in trs:
                tds = tr.find_all('td')
                if len(tds) < 3:
                    continue
                
                try:
                    # TD 1: 版块名称、新帖数、描述
                    info_td = tds[1]
                    
                    # 查找所有版块链接（可能包含主版块和子版块）
                    forum_links = info_td.find_all('a', href=lambda x: x and 'forum-' in x)
                    if not forum_links:
                        continue
                    
                    # TD 2: 主题数/帖子数 (class='fl_i')
                    threads_count = 0
                    posts_count = 0
                    if len(tds) > 2:
                        stats_td = tds[2]
                        stats_text = stats_td.get_text(strip=True)
                        
                        # 解析格式如 "20万/861万" 或 "2599/151万"
                        stats_match = re.search(r'(\d+)万?\s*/\s*(\d+)万?', stats_text)
                        if stats_match:
                            threads_str = stats_match.group(1)
                            posts_str = stats_match.group(2)
                            
                            threads_count = int(threads_str)
                            posts_count = int(posts_str)
                            
                            # 检查是否有"万"字
                            threads_text = stats_text.split('/')[0]
                            posts_text = stats_text.split('/')[1] if '/' in stats_text else ''
                            
                            if '万' in threads_text:
                                threads_count *= 10000
                            if '万' in posts_text:
                                posts_count *= 10000
                    
                    # 提取新帖数（在 em 标签中，格式为 (数字)）
                    new_posts = 0
                    em_tag = info_td.find('em')
                    if em_tag:
                        em_text = em_tag.get_text(strip=True)
                        match = re.search(r'\((\d+)\)', em_text)
                        if match:
                            new_posts = int(match.group(1))
                    
                    # 提取描述（只对主版块有效）
                    desc_p = info_td.find('p', class_='xg2')
                    main_description = desc_p.get_text(strip=True) if desc_p else None
                    
                    # 处理每个版块链接（主版块和子版块）
                    for idx, forum_link in enumerate(forum_links):
                        forum_name = forum_link.get_text(strip=True)
                        forum_url = forum_link.get('href', '')
                        
                        # 提取版块 ID
                        forum_id = ''
                        if 'forum-' in forum_url:
                            forum_id = forum_url.split('forum-')[1].split('-')[0]
                        
                        if not forum_name or not forum_id:
                            continue
                        
                        # 第一个是主版块，其他的是子版块
                        is_subforum = idx > 0
                        description = None if is_subforum else main_description
                        
                        forum = Forum(
                            id=forum_id,
                            name=forum_name,
                            description=description,
                            threads_count=threads_count if not is_subforum else 0,
                            posts_count=posts_count if not is_subforum else 0,
                            new_posts=new_posts,
                            url=forum_url
                        )
                        forums.append(forum)
                    
                except Exception:
                    continue
            
            return forums
            
        except Exception as e:
            print(f"获取版块列表异常：{e}")
            return []
    
    def get_thread_list(
        self, 
        forum_name_or_id: str, 
        page: int = 1
    ) -> List[Thread]:
        """获取指定版块的帖子列表
        
        Args:
            forum_name_or_id: 版块名称或 ID
            page: 页码
            
        Returns:
            帖子列表
        """
        try:
            # 如果是名称，先查找对应的 ID
            forum_id = forum_name_or_id
            if not forum_name_or_id.isdigit():
                forums = self.get_forum_list()
                for forum in forums:
                    if forum.name == forum_name_or_id:
                        forum_id = forum.id
                        break
            
            # 构造版块 URL
            url = f"forum.php?mod=forumdisplay&fid={forum_id}&page={page}"
            
            response = self.client.get(url)
            html = response.text
            soup = BeautifulSoup(html, 'lxml')
            
            threads = []
            
            # 查找帖子列表
            # Discuz 帖子通常在 <tbody> 标签中
            thread_list = soup.find_all('tbody', id=lambda x: x and x.startswith('normalthread'))
            
            for tbody in thread_list:
                try:
                    # 提取帖子 ID
                    thread_id = tbody.get('id', '').replace('normalthread_', '')
                    
                    # 查找标题链接
                    title_link = tbody.find('a', class_='s xst') or tbody.find('a', class_='xst')
                    if not title_link:
                        continue
                    
                    title = title_link.get_text(strip=True)
                    thread_url = title_link.get('href', '')
                    
                    # 如果 ID 不在 tbody 中，从 URL 提取
                    if not thread_id and 'tid=' in thread_url:
                        thread_id = thread_url.split('tid=')[1].split('&')[0]
                    elif not thread_id and 'thread-' in thread_url:
                        thread_id = thread_url.split('thread-')[1].split('-')[0]
                    
                    # 提取作者和发布时间（第一个 class='by' 的 TD）
                    by_tds = tbody.find_all('td', class_='by')
                    author = ''
                    created_at = None
                    last_reply_author = None
                    last_reply_time = None
                    
                    if len(by_tds) >= 1:
                        # 第一个 by TD：作者和发布时间
                        first_by = by_tds[0]
                        cite = first_by.find('cite')
                        if cite:
                            author_a = cite.find('a')
                            author = author_a.get_text(strip=True) if author_a else cite.get_text(strip=True)
                        
                        # 发布时间
                        time_em = first_by.find('em')
                        if time_em:
                            time_span = time_em.find('span')
                            if time_span:
                                created_at = time_span.get_text(strip=True)
                    
                    if len(by_tds) >= 2:
                        # 第二个 by TD：最后回复者和时间
                        last_by = by_tds[1]
                        last_cite = last_by.find('cite')
                        if last_cite:
                            last_author_a = last_cite.find('a')
                            last_reply_author = last_author_a.get_text(strip=True) if last_author_a else last_cite.get_text(strip=True)
                        
                        # 最后回复时间
                        last_time_em = last_by.find('em')
                        if last_time_em:
                            last_time_span = last_time_em.find('span') or last_time_em.find('a')
                            if last_time_span:
                                last_reply_time = last_time_span.get_text(strip=True)
                    
                    # 提取回复数和查看数
                    num_td = tbody.find('td', class_='num')
                    replies = 0
                    views = 0
                    if num_td:
                        # 回复数在 <a class="xi2"> 标签中
                        reply_link = num_td.find('a', class_='xi2')
                        if reply_link:
                            try:
                                replies = int(reply_link.get_text(strip=True))
                            except:
                                pass
                        
                        # 查看数在 <em> 标签中
                        view_em = num_td.find('em')
                        if view_em:
                            try:
                                views = int(view_em.get_text(strip=True))
                            except:
                                pass
                    
                    # 检查是否置顶、精华等
                    is_sticky = 'class="icn stk"' in str(tbody) or 'sortnum' in tbody.get('class', [])
                    is_digest = 'class="icn dgt"' in str(tbody) or 'digest' in str(tbody).lower()
                    
                    if title and thread_id:
                        thread = Thread(
                            id=thread_id,
                            title=title,
                            author=author,
                            forum=forum_name_or_id,
                            forum_id=forum_id,
                            views=views,
                            replies=replies,
                            created_at=created_at,
                            last_reply_author=last_reply_author,
                            last_reply_time=last_reply_time,
                            is_sticky=is_sticky,
                            is_digest=is_digest
                        )
                        threads.append(thread)
                        
                except Exception as e:
                    # 跳过解析失败的帖子
                    continue
            
            return threads
            
        except Exception as e:
            print(f"获取帖子列表异常：{e}")
            return []

