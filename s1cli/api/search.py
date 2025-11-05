"""搜索功能 API"""
from typing import List, Optional
from bs4 import BeautifulSoup
from s1cli.api.client import S1Client
from s1cli.models.thread import Thread


class SearchAPI:
    """搜索 API"""
    
    def __init__(self, client: S1Client):
        """初始化搜索 API
        
        Args:
            client: HTTP 客户端
        """
        self.client = client
    
    def search(
        self,
        keyword: str,
        forum: Optional[str] = None,
        page: int = 1
    ) -> List[Thread]:
        """搜索帖子
        
        Args:
            keyword: 搜索关键词
            forum: 限定的版块（可选）
            page: 页码
            
        Returns:
            帖子列表
        """
        try:
            # Discuz 搜索 URL
            search_params = {
                'mod': 'forum',
                'srchtxt': keyword,
                'searchsubmit': 'yes',
                'source': 'hotsearch',
            }
            
            if forum:
                # 如果指定了版块，添加版块参数
                # 这里需要先将版块名转换为 ID
                # 简化处理，直接传入
                search_params['forum'] = forum
            
            response = self.client.get('search.php', params=search_params)
            
            # 检查是否需要重定向到结果页
            if 'searchid=' in response.url:
                # 已经在结果页
                html = response.text
            else:
                # 可能需要二次请求获取结果
                html = response.text
                soup = BeautifulSoup(html, 'lxml')
                
                # 查找结果链接
                result_link = soup.find('a', href=lambda x: x and 'searchid=' in x)
                if result_link:
                    result_url = result_link.get('href')
                    response = self.client.get(result_url)
                    html = response.text
            
            # 解析搜索结果
            soup = BeautifulSoup(html, 'lxml')
            results = []
            
            # 查找结果列表
            # Discuz 搜索结果通常在特定的列表中
            result_items = soup.find_all('li', class_='pbw') or soup.find_all('tbody', id=lambda x: x and 'normalthread' in x)
            
            for item in result_items:
                try:
                    # 提取标题和链接
                    title_link = item.find('a', class_='s xst') or item.find('a', class_='xst')
                    if not title_link:
                        continue
                    
                    title = title_link.get_text(strip=True)
                    thread_url = title_link.get('href', '')
                    
                    # 提取帖子 ID
                    thread_id = ''
                    if 'tid=' in thread_url:
                        thread_id = thread_url.split('tid=')[1].split('&')[0]
                    elif 'thread-' in thread_url:
                        thread_id = thread_url.split('thread-')[1].split('-')[0]
                    
                    # 提取作者
                    author_elem = item.find('cite') or item.find('a', class_='xi2')
                    author = ''
                    if author_elem:
                        if author_elem.name == 'cite':
                            author_link = author_elem.find('a')
                            author = author_link.get_text(strip=True) if author_link else ''
                        else:
                            author = author_elem.get_text(strip=True)
                    
                    # 提取版块信息
                    forum_elem = item.find('a', class_='xi2') or item.find('em', class_='xg1')
                    forum_name = ''
                    if forum_elem and 'forum' in str(forum_elem.get('href', '')):
                        forum_name = forum_elem.get_text(strip=True)
                    
                    # 提取查看数和回复数
                    num_elem = item.find('td', class_='num')
                    views = 0
                    replies = 0
                    if num_elem:
                        nums = num_elem.find_all('em')
                        if len(nums) >= 2:
                            try:
                                replies = int(nums[0].get_text(strip=True))
                                views = int(nums[1].get_text(strip=True))
                            except:
                                pass
                    
                    if title and thread_id:
                        thread = Thread(
                            id=thread_id,
                            title=title,
                            author=author,
                            forum=forum_name,
                            views=views,
                            replies=replies
                        )
                        results.append(thread)
                        
                except Exception as e:
                    # 跳过解析失败的项
                    continue
            
            return results
            
        except Exception as e:
            print(f"搜索异常：{e}")
            return []



