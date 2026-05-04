#!/usr/bin/env python3
"""
KK对战平台 - 定时数据采集器
采集热度分数榜、新图分数榜、飙升分数榜前10
存储到Excel文件
"""

import requests
from bs4 import BeautifulSoup
import json
import pandas as pd
from datetime import datetime
import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kk_crawler_v2 import KKMapCrawlerV2

class KKDataCollector:
    """KK对战平台数据采集器"""
    
    def __init__(self, output_dir="./data"):
        self.crawler = KKMapCrawlerV2()
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def collect_all_rankings(self):
        """采集所有榜单前10"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        date_str = datetime.now().strftime("%Y%m%d")
        time_str = datetime.now().strftime("%H%M")
        
        print(f"[{timestamp}] 开始采集数据...")
        
        # 采集三个榜单
        rankings = {
            '热度分数榜': self.crawler.get_hot_score_ranking(10),
            '新图分数榜': self.crawler.get_new_map_ranking(10),
            '飙升分数榜': self.crawler.get_soar_ranking(10)
        }
        
        # 准备Excel数据
        excel_data = {}
        summary_data = []
        
        for rank_name, maps in rankings.items():
            if not maps:
                continue
            
            # 榜单数据
            df_data = []
            for i, m in enumerate(maps, 1):
                df_data.append({
                    '排名': i,
                    '地图ID': m['地图ID'],
                    '地图名称': m['地图名称'],
                    '热度分数': m.get('热度分数_daHotScore', 0),
                    '新图分数': m.get('新图分数_daNewMapScore', 0),
                    '飙升分数': m.get('飙升分数_daSoarScore', 0),
                    '热度': m['热度'],
                    '评分': m['评分'],
                    '类型': m['类型'],
                    '作者': m['作者']
                })
            
            excel_data[rank_name] = pd.DataFrame(df_data)
            
            # 汇总数据（用于对比）
            for m in maps:
                summary_data.append({
                    '采集时间': timestamp,
                    '榜单': rank_name,
                    '排名': maps.index(m) + 1,
                    '地图ID': m['地图ID'],
                    '地图名称': m['地图名称'],
                    '分数': m.get('热度分数_daHotScore', 0) or m.get('新图分数_daNewMapScore', 0) or m.get('飙升分数_daSoarScore', 0),
                    '热度': m['热度'],
                    '评分': m['评分']
                })
        
        # 保存到Excel
        filename = f"kk_rankings_{date_str}_{time_str}.xlsx"
        filepath = os.path.join(self.output_dir, filename)
        
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            for sheet_name, df in excel_data.items():
                df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        print(f"[{timestamp}] 数据已保存到: {filepath}")
        
        # 同时保存汇总CSV（用于历史对比）
        summary_file = os.path.join(self.output_dir, "kk_rankings_history.csv")
        df_summary = pd.DataFrame(summary_data)
        
        if os.path.exists(summary_file):
            df_summary.to_csv(summary_file, mode='a', header=False, index=False, encoding='utf-8-sig')
        else:
            df_summary.to_csv(summary_file, index=False, encoding='utf-8-sig')
        
        print(f"[{timestamp}] 汇总数据已追加到: {summary_file}")
        
        return filepath, summary_data


def main():
    """主函数"""
    collector = KKDataCollector(output_dir="/root/.openclaw/workspace/kk_map_crawler/data")
    filepath, data = collector.collect_all_rankings()
    print(f"\n✅ 采集完成: {filepath}")
    return filepath


if __name__ == "__main__":
    main()
