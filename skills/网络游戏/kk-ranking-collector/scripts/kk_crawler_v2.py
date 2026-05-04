import requests
from bs4 import BeautifulSoup
import json
import pandas as pd
from datetime import datetime
import time
import random

class KKMapCrawlerV2:
    """KK对战平台地图爬虫 V2 - 支持多榜单"""
    
    BASE_URL = "https://www.kkdzpt.com"
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }
    
    # 地图类型映射
    MAP_TYPES = {
        1: "塔防",
        2: "防守", 
        3: "对抗",
        4: "角色扮演",
        5: "生存",
        7: "战役",
        8: "其他"
    }
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
        self.all_maps_cache = None
    
    def fetch_map_list(self, map_type=None):
        """获取地图列表"""
        url = f"{self.BASE_URL}/rpgarea"
        if map_type:
            url = f"{self.BASE_URL}/rpgarea/{map_type}"
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            next_data = soup.find('script', {'id': '__NEXT_DATA__'})
            if not next_data:
                raise Exception("未找到数据标签 __NEXT_DATA__")
            
            data = json.loads(next_data.string)
            map_data = data['props']['pageProps']['mapData']
            
            return {
                'total': map_data['total'],
                'maps': map_data['rows']
            }
            
        except Exception as e:
            print(f"请求失败: {e}")
            return {'total': 0, 'maps': []}
    
    def parse_map_info(self, map_item):
        """解析单个地图信息 - 包含榜单相关字段"""
        return {
            '地图ID': map_item.get('mapId'),
            '地图名称': map_item.get('mapName'),
            '版本': map_item.get('mapVersion'),
            '类型': self.MAP_TYPES.get(map_item.get('mapType'), '未知'),
            '类型ID': map_item.get('mapType'),
            '作者': map_item.get('authorName', '未知'),
            '作者ID': map_item.get('authorAccount'),
            
            # 热度相关
            '热度': map_item.get('hot', 0),
            '热度分数_daHotScore': map_item.get('daHotScore', 0),
            
            # 新图相关
            '新图分数_daNewMapScore': map_item.get('daNewMapScore', 0),
            '是否新图': map_item.get('newFlag', False),
            'popularNew': map_item.get('popularNew', 0),
            
            # 飙升相关
            '飙升分数_daSoarScore': map_item.get('daSoarScore', 0),
            
            # 评分相关
            '评分': map_item.get('score', 0),
            '评论数': map_item.get('commentCount', 0),
            '评分人数': map_item.get('scoreCount', 0),
            
            # 关注数（从详情页获取）
            '关注数': map_item.get('followerCount', 0),
            
            # 其他
            '宣传语': map_item.get('slogan', ''),
            '封面图': map_item.get('logo', ''),
            '创建时间': self._format_time(map_item.get('createTime')),
            '更新时间': self._format_time(map_item.get('updateTime')),
            '标签': ','.join(map_item.get('mapScoreTags', [])),
            '游戏引擎': 'Y3' if map_item.get('y3Map') else 'War3',
            
            # 游戏设置
            '玩家数': map_item.get('playerCount', ''),
            'VIP特权': map_item.get('vipPrivilege', False),
            '高清版': map_item.get('isHD', False),
            '红包活动': map_item.get('redPacketFlag', 0) > 0,
        }
    
    def _format_time(self, timestamp):
        """格式化时间戳"""
        if not timestamp:
            return ''
        try:
            if timestamp > 1000000000000:
                timestamp = timestamp / 1000
            return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
        except:
            return ''
    
    def get_all_maps(self, use_cache=True):
        """获取所有地图"""
        if use_cache and self.all_maps_cache:
            return self.all_maps_cache
        
        print("正在获取全部地图数据...")
        result = self.fetch_map_list()
        maps = [self.parse_map_info(m) for m in result['maps']]
        
        self.all_maps_cache = {
            'total': result['total'],
            'maps': maps
        }
        print(f"成功获取 {len(maps)} 张地图 (总计: {result['total']})")
        return self.all_maps_cache
    
    # ==================== 榜单功能 ====================
    
    def get_hot_score_ranking(self, limit=50):
        """
        热度榜 (算法版) - 基于 daHotScore 排序
        这个分数可能是平台综合算法计算的热度
        """
        print(f"正在生成热度分数榜 TOP {limit}...")
        result = self.get_all_maps()
        sorted_maps = sorted(result['maps'], key=lambda x: x['热度分数_daHotScore'], reverse=True)
        return sorted_maps[:limit]
    
    def get_new_map_ranking(self, limit=50):
        """
        新图榜 - 基于 daNewMapScore 排序
        """
        print(f"正在生成新图排行榜 TOP {limit}...")
        result = self.get_all_maps()
        # 过滤有新图分数的
        new_maps = [m for m in result['maps'] if m['新图分数_daNewMapScore'] > 0]
        sorted_maps = sorted(new_maps, key=lambda x: x['新图分数_daNewMapScore'], reverse=True)
        return sorted_maps[:limit]
    
    def get_soar_ranking(self, limit=50):
        """
        飙升榜 - 基于 daSoarScore 排序
        """
        print(f"正在生成飙升排行榜 TOP {limit}...")
        result = self.get_all_maps()
        sorted_maps = sorted(result['maps'], key=lambda x: x['飙升分数_daSoarScore'], reverse=True)
        return sorted_maps[:limit]
