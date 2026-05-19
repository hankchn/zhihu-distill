#!/usr/bin/env python3
"""
知乎内容主题筛选工具
用法: python3 zhihu_filter.py --input <raw_dir> --output <filtered_dir> --topic invest
      python3 zhihu_filter.py --input <raw_dir> --output <filtered_dir> --keywords "AI,机器学习,深度学习"
"""

import re
import shutil
import argparse
from pathlib import Path

# 预置主题关键词库
TOPIC_KEYWORDS = {
    "invest": (
        r'投资|理财|股票|基金|债券|银行|A股|港股|美股|ETF|指数|'
        r'PE|PB|ROE|ROA|EPS|市盈率|市净率|净资产|分红|股息|'
        r'BOLL|RSI|MACD|KDJ|MA\d+|均线|K线|'
        r'买入|卖出|建仓|加仓|减仓|清仓|止损|止盈|定投|'
        r'牛市|熊市|涨停|跌停|震荡|横盘|回撤|'
        r'房产|房价|贷款|利率|按揭|首付|'
        r'新能源|光伏|芯片|半导体|白酒|医药|消费|科技|'
        r'茅台|腾讯|阿里|宁德|比亚迪|中国平安|'
        r'巴菲特|芒格|格雷厄姆|彼得林奇|索罗斯|'
        r'期货|期权|黄金|白银|比特币|数字货币|'
        r'仓位|持仓|浮盈|浮亏|收益率|年化|复利|'
        r'价值投资|成长投资|趋势投资|量化|套利'
    ),
    "tech": (
        r'AI|人工智能|机器学习|深度学习|大模型|GPT|LLM|'
        r'编程|代码|Python|Java|算法|数据结构|'
        r'互联网|SaaS|云计算|区块链|Web3|'
        r'芯片|半导体|操作系统|数据库|'
        r'产品经理|技术架构|微服务|DevOps|'
        r'开源|GitHub|API|SDK|框架'
    ),
    "edu": (
        r'教育|教学|学习|教师|学生|课程|'
        r'高考|考研|留学|培训|辅导|'
        r'教育理念|素质教育|应试|学科|'
        r'教材|教案|备课|课堂|作业|考试|'
        r'学习方法|记忆|思维导图|笔记|'
        r'幼儿教育|小学|中学|大学|研究生|'
        r'在线教育|网课|知识付费|终身学习'
    ),
    "health": (
        r'医学|医生|医院|诊断|治疗|'
        r'健身|运动|减脂|增肌|跑步|'
        r'营养|饮食|蛋白质|维生素|碳水|'
        r'心理|焦虑|抑郁|情绪|心理健康|'
        r'疾病|症状|药物|手术|康复|'
        r'中医|西医|循证医学|临床|'
        r'睡眠|压力|亚健康|体检|养生'
    ),
    "design": (
        r'设计|UI|UX|交互|视觉|'
        r'用户体验|界面|原型|Figma|Sketch|'
        r'品牌|logo|字体|排版|配色|'
        r'产品设计|工业设计|平面设计|'
        r'设计思维|设计系统|组件库|'
        r'审美|创意|灵感|作品集|'
        r'动效|插画|图标|响应式'
    ),
    "writing": (
        r'写作|文案|内容|创作|'
        r'公众号|自媒体|博客|专栏|'
        r'选题|标题|开头|结尾|结构|'
        r'读者|粉丝|阅读量|传播|'
        r'故事|叙事|修辞|文风|'
        r'出版|编辑|投稿|签约|'
        r'小说|散文|非虚构|评论'
    ),
}

# 最低命中数阈值
MIN_HITS = 2


def load_keywords(topic=None, custom_keywords=None):
    """加载关键词正则"""
    if custom_keywords:
        pattern = "|".join(re.escape(k.strip()) for k in custom_keywords.split(","))
    elif topic and topic in TOPIC_KEYWORDS:
        pattern = TOPIC_KEYWORDS[topic]
    else:
        raise ValueError(f"未知主题: {topic}。可选: {list(TOPIC_KEYWORDS.keys())} 或使用 --keywords")

    return re.compile(pattern, re.IGNORECASE)


def is_relevant(filepath, keyword_re, min_hits=MIN_HITS):
    """判断文件是否与主题相关"""
    try:
        content = filepath.read_text(encoding="utf-8")
    except Exception:
        return False

    # 取标题（第一行）+ 正文前3000字符
    lines = content.split("\n")
    title = lines[0] if lines else ""
    body = content[:3000]
    text_to_check = f"{title}\n{body}"

    # 找到所有匹配的不同关键词
    matches = set(keyword_re.findall(text_to_check))
    return len(matches) >= min_hits


def main():
    parser = argparse.ArgumentParser(description="知乎内容主题筛选工具")
    parser.add_argument("--input", required=True, help="原始内容目录（包含 answers/articles/pins 子目录）")
    parser.add_argument("--output", required=True, help="筛选结果输出目录")
    parser.add_argument("--topic", default=None, help=f"预置主题: {list(TOPIC_KEYWORDS.keys())}")
    parser.add_argument("--keywords", default=None, help="自定义关键词，逗号分隔")
    parser.add_argument("--min-hits", type=int, default=MIN_HITS, help=f"最低命中数阈值（默认{MIN_HITS}）")
    args = parser.parse_args()

    if not args.topic and not args.keywords:
        parser.error("必须指定 --topic 或 --keywords")

    input_dir = Path(args.input)
    output_dir = Path(args.output)
    keyword_re = load_keywords(args.topic, args.keywords)

    # 统计
    total = 0
    filtered = 0
    stats_by_type = {}

    # 遍历 answers/articles/pins 子目录
    for subdir_name in ["answers", "articles", "pins"]:
        src_dir = input_dir / subdir_name
        if not src_dir.exists():
            continue

        dst_dir = output_dir / subdir_name
        dst_dir.mkdir(parents=True, exist_ok=True)

        type_total = 0
        type_filtered = 0

        for md_file in sorted(src_dir.glob("*.md")):
            type_total += 1
            total += 1

            if is_relevant(md_file, keyword_re, args.min_hits):
                shutil.copy2(md_file, dst_dir / md_file.name)
                type_filtered += 1
                filtered += 1

        stats_by_type[subdir_name] = (type_filtered, type_total)
        print(f"  {subdir_name}: {type_filtered}/{type_total} 篇通过筛选")

    print(f"\n{'=' * 50}")
    print(f"📊 筛选完成:")
    print(f"   总内容: {total} 条")
    print(f"   通过筛选: {filtered} 条 ({filtered/total*100:.1f}%)" if total > 0 else "   无内容")
    print(f"   输出目录: {output_dir}")
    print(f"{'=' * 50}")


if __name__ == "__main__":
    main()
