#!/usr/bin/env python3
"""
KK对战平台 - 每日排行变化分析器
分析前一日排行变化，生成报告
"""

import pandas as pd
from datetime import datetime, timedelta
import os
import json

def analyze_ranking_changes():
    """
    分析前一日排行变化
    包含：前五变化、新入榜、出榜
    """
    data_dir = "/root/.openclaw/workspace/kk_map_crawler/data"
    history_file = os.path.join(data_dir, "kk_rankings_history.csv")
    
    if not os.path.exists(history_file):
        return "暂无历史数据，无法生成报告"
    
    # 读取历史数据
    df = pd.read_csv(history_file, encoding='utf-8-sig')
    df['采集时间'] = pd.to_datetime(df['采集时间'])
    
    # 获取日期
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    
    # 筛选昨日和今日数据
    df['日期'] = df['采集时间'].dt.date
    yesterday_data = df[df['日期'] == yesterday]
    today_data = df[df['日期'] == today]
    
    if yesterday_data.empty:
        return f"暂无 {yesterday} 的数据，无法生成对比报告"
    
    if today_data.empty:
        return f"暂无 {today} 的数据，无法生成对比报告"
    
    # 获取每个榜单的最新数据
    report = []
    report.append(f"📊 KK对战平台排行变化报告 ({yesterday} → {today})")
    report.append("=" * 60)
    
    for rank_type in ['热度分数榜', '新图分数榜', '飙升分数榜']:
        report.append(f"\n🏆 {rank_type}")
        report.append("-" * 40)
        
        # 昨日和今日数据
        yest_rank = yesterday_data[yesterday_data['榜单'] == rank_type].sort_values('采集时间').groupby('排名').last().reset_index()
        today_rank = today_data[today_data['榜单'] == rank_type].sort_values('采集时间').groupby('排名').last().reset_index()
        
        if yest_rank.empty or today_rank.empty:
            report.append("  数据不足，无法对比")
            continue
        
        # 1. 前五名变化
        report.append("\n  📈 前五名变化:")
        for i in range(1, 6):
            yest_map = yest_rank[yest_rank['排名'] == i]
            today_map = today_rank[today_rank['排名'] == i]
            
            if yest_map.empty or today_map.empty:
                continue
            
            yest_name = yest_map.iloc[0]['地图名称']
            today_name = today_map.iloc[0]['地图名称']
            
            if yest_name != today_name:
                # 查找今日排名
                today_pos = today_rank[today_rank['地图名称'] == yest_name]
                if today_pos.empty:
                    new_pos = "出榜"
                else:
                    new_pos = f"第{today_pos.iloc[0]['排名']}名"
                
                report.append(f"    第{i}名: {yest_name} → {today_name} (原第{i}名现{new_pos})")
            else:
                report.append(f"    第{i}名: {today_name} (保持)")
        
        # 2. 新入榜地图
        yest_maps = set(yest_rank['地图名称'].tolist())
        today_maps = set(today_rank['地图名称'].tolist())
        
        new_entries = today_maps - yest_maps
        if new_entries:
            report.append(f"\n  🆕 新入榜地图:")
            for map_name in list(new_entries)[:5]:  # 最多显示5个
                map_data = today_rank[today_rank['地图名称'] == map_name]
                if not map_data.empty:
                    rank = map_data.iloc[0]['排名']
                    report.append(f"    第{rank}名: {map_name}")
        else:
            report.append(f"\n  🆕 新入榜地图: 无")
        
        # 3. 出榜地图
        dropped = yest_maps - today_maps
        if dropped:
            report.append(f"\n  📉 出榜地图:")
            for map_name in list(dropped)[:5]:
                report.append(f"    {map_name}")
        else:
            report.append(f"\n  📉 出榜地图: 无")
    
    report.append("\n" + "=" * 60)
    report.append(f"报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    return "\n".join(report)


def main():
    """主函数"""
    report = analyze_ranking_changes()
    print(report)
    
    # 保存报告
    report_file = f"/root/.openclaw/workspace/kk_map_crawler/data/ranking_report_{datetime.now().strftime('%Y%m%d')}.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n✅ 报告已保存到: {report_file}")
    return report


if __name__ == "__main__":
    main()
