---
name: kk-ranking-collector
description: 采集 KK 对战平台地图排行榜数据的技能。当用户需要采集 KK 对战平台榜单、获取地图热度排名、分析游戏地图排行榜变化、或需要定时爬取游戏排行榜数据时使用。触发词：KK对战平台、地图排行榜、热度榜、新图榜、飙升榜、游戏排行榜采集、榜单数据爬取。
---

# KK Ranking Collector

KK 对战平台地图排行榜定时采集与分析工具。

## When to Use

当用户有以下需求时使用此技能：

- 采集 KK 对战平台三个榜单数据（热度榜、新图榜、飙升榜）
- 获取游戏地图的排名、热度、评分等数据
- 分析排行榜变化趋势
- 设置定时任务自动采集榜单数据
- 对比历史排行榜数据

## Workflow

### 1. 数据采集

运行采集脚本获取三个榜单数据：

```bash
cd scripts
python3 collect_rankings.py
```

**输出位置**：`data/` 目录
- `kk_rankings_YYYYMMDD_HHMM.xlsx` — Excel 格式（含三个 Sheet）
- `kk_rankings_history.csv` — CSV 历史汇总文件

### 2. 变化分析

生成排行榜变化报告：

```bash
cd scripts
python3 analyze_changes.py
```

**输出位置**：`data/ranking_report_YYYYMMDD.txt`

### 3. 定时任务配置

推荐 cron 配置：

```bash
# 每日多时段采集（12,14,16,18,20,21,22,23,0点）
0 12,14,16,18,20,21,22,23 * * * cd /path/to/scripts && python3 collect_rankings.py
0 0 * * * cd /path/to/scripts && python3 collect_rankings.py

# 每日9:30生成变化报告
30 9 * * * cd /path/to/scripts && python3 analyze_changes.py
```

## Data Structure

采集字段：

| 字段 | 说明 |
|------|------|
| 地图ID / 地图名称 / 版本 | 基础标识信息 |
| 热度分数 / 新图分数 / 飙升分数 | 三榜单分数 |
| 热度 / 评分 / 评论数 | 用户互动指标 |
| 类型 / 作者 / 标签 | 分类信息 |

## Technical Details

- **数据来源**：https://www.kkdzpt.com/
- **技术方案**：Next.js SSR，数据从 `__NEXT_DATA__` 标签解析
- **依赖**：requests, beautifulsoup4, pandas, openpyxl

## Dependencies

```bash
pip install requests beautifulsoup4 pandas openpyxl
```

## Scripts Reference

| 脚本 | 用途 |
|------|------|
| `scripts/collect_rankings.py` | 主采集脚本，获取三榜单数据 |
| `scripts/analyze_changes.py` | 分析排行榜变化，生成报告 |
| `scripts/kk_crawler_v2.py` | 爬虫核心模块 |
