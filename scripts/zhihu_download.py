#!/usr/bin/env python3
"""
知乎用户主页内容批量下载工具
用法: python3 zhihu_download.py --user <user_token> --output <output_dir>
依赖: pip install httpx markdownify beautifulsoup4
"""

import os
import re
import json
import time
import random
import sys
import argparse
from pathlib import Path
from datetime import datetime

import httpx
from markdownify import markdownify as md
from bs4 import BeautifulSoup

BASE_URL = "https://www.zhihu.com/api/v4"


def get_cookie(output_dir):
    """从cookie.txt文件读取Cookie，或提示用户输入"""
    cookie_file = Path(output_dir) / "cookie.txt"
    if cookie_file.exists():
        return cookie_file.read_text().strip()

    print("=" * 60)
    print("需要知乎Cookie才能下载内容。")
    print("获取方法：")
    print("1. 在Chrome中打开 https://www.zhihu.com")
    print("2. 按F12打开开发者工具 → Network标签")
    print("3. 刷新页面，点击任意一个请求")
    print("4. 在Request Headers中找到 Cookie 字段")
    print("5. 复制整个Cookie值")
    print("=" * 60)
    cookie = input("请粘贴Cookie值: ").strip()
    cookie_file.write_text(cookie)
    print(f"Cookie已保存到 {cookie_file}")
    return cookie


def make_headers(cookie, user_token):
    """构造请求头"""
    return {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Referer": f"https://www.zhihu.com/people/{user_token}",
        "Origin": "https://www.zhihu.com",
        "Cookie": cookie,
        "x-requested-with": "fetch",
    }


def clean_filename(name, max_len=80):
    """清理文件名，移除不合法字符"""
    name = re.sub(r'[<>:"/\\|?*\n\r\t]', '', name)
    name = name.strip()[:max_len]
    return name or "untitled"


def zhihu_html_to_md(html_content):
    """将知乎HTML内容转换为Markdown"""
    if not html_content:
        return ""

    soup = BeautifulSoup(html_content, 'html.parser')

    # 1. 处理LaTeX公式
    for formula in soup.find_all('span', attrs={'data-formula': True}):
        f = formula.get('data-formula', '')
        if f:
            formula.replace_with(f' ${f}$ ')

    # 2. 处理图片懒加载
    for img in soup.find_all('img'):
        src = img.get('data-original') or img.get('data-actualsrc') or img.get('data-src') or img.get('src', '')
        if src:
            img['src'] = src

    # 3. 处理链接卡片
    for card in soup.find_all('a', class_='LinkCard'):
        href = card.get('data-href', card.get('href', ''))
        title = card.get_text().strip() or '链接'
        card.replace_with(f'[{title}]({href})')

    # 4. 转换为Markdown
    markdown = md(str(soup), heading_style="atx", bullets="-", strip=['script', 'style'])

    # 5. 清理多余空行
    markdown = re.sub(r'\n{3,}', '\n\n', markdown)
    return markdown.strip()


def fetch_all_items(client, headers, user_token, content_type):
    """
    获取用户的所有内容（回答/文章/想法）
    content_type: "answers" | "articles" | "pins"
    """
    url = f"{BASE_URL}/members/{user_token}/{content_type}"
    params = {
        "limit": 20,
        "offset": 0,
    }

    if content_type == "answers":
        params["include"] = "data[*].content,voteup_count,comment_count,created_time,updated_time,question.title"
        params["sort_by"] = "created"
    elif content_type == "articles":
        params["include"] = "data[*].content,voteup_count,comment_count,created,updated"
        params["sort_by"] = "created"
    elif content_type == "pins":
        params["include"] = "data[*].content"

    all_items = []
    page = 1
    use_params = True

    while True:
        try:
            print(f"  正在获取第 {page} 页...")

            if use_params:
                resp = client.get(url, params=params, headers=headers, timeout=30)
            else:
                resp = client.get(url, headers=headers, timeout=30)

            if resp.status_code == 403:
                print(f"  ⚠️  403 被拒绝访问，可能需要更新Cookie或触发了反爬")
                break
            elif resp.status_code == 401:
                print(f"  ⚠️  401 未授权，Cookie可能已过期")
                break
            elif resp.status_code != 200:
                print(f"  ⚠️  HTTP {resp.status_code}")
                break

            data = resp.json()
            items = data.get("data", [])
            if not items:
                break

            all_items.extend(items)
            print(f"  ✓ 获取到 {len(items)} 条，累计 {len(all_items)} 条")

            paging = data.get("paging", {})
            if paging.get("is_end", True):
                break

            next_url = paging.get("next")
            if next_url:
                # 知乎paging.next返回api.zhihu.com域名，需替换为www.zhihu.com
                next_url = next_url.replace("https://api.zhihu.com", "https://www.zhihu.com/api/v4")
                next_url = next_url.replace("http://api.zhihu.com", "https://www.zhihu.com/api/v4")
                url = next_url
                use_params = False
            else:
                break

            page += 1
            time.sleep(random.uniform(1.5, 3.0))

        except Exception as e:
            print(f"  ⚠️  请求失败: {e}")
            time.sleep(5)
            break

    return all_items


def save_answer(item, index, output_dir):
    """保存单个回答为md文件"""
    answers_dir = Path(output_dir) / "raw" / "answers"
    answers_dir.mkdir(parents=True, exist_ok=True)

    question = item.get("question", {})
    question_title = question.get("title", "未知问题")
    content_html = item.get("content", "")
    voteup = item.get("voteup_count", 0)
    comment = item.get("comment_count", 0)
    created = item.get("created_time", 0)
    updated = item.get("updated_time", 0)
    answer_id = item.get("id", "")

    created_str = datetime.fromtimestamp(created).strftime("%Y-%m-%d") if created else "未知"
    updated_str = datetime.fromtimestamp(updated).strftime("%Y-%m-%d") if updated else ""

    content_md = zhihu_html_to_md(content_html)

    md_content = f"""# {question_title}

> **类型**: 回答 | **赞同**: {voteup} | **评论**: {comment}
> **创建时间**: {created_str} | **更新时间**: {updated_str}
> **链接**: https://www.zhihu.com/question/{question.get('id', '')}/answer/{answer_id}

---

{content_md}
"""

    filename = clean_filename(f"{created_str}_{question_title}")
    filepath = answers_dir / f"{filename}.md"
    if filepath.exists():
        filepath = answers_dir / f"{filename}_{index}.md"

    filepath.write_text(md_content, encoding="utf-8")
    return filepath


def save_article(item, index, output_dir):
    """保存单个文章为md文件"""
    articles_dir = Path(output_dir) / "raw" / "articles"
    articles_dir.mkdir(parents=True, exist_ok=True)

    title = item.get("title", "未知标题")
    content_html = item.get("content", "")
    voteup = item.get("voteup_count", 0)
    comment = item.get("comment_count", 0)
    created = item.get("created", 0)
    updated = item.get("updated", 0)
    article_id = item.get("id", "")

    created_str = datetime.fromtimestamp(created).strftime("%Y-%m-%d") if created else "未知"
    updated_str = datetime.fromtimestamp(updated).strftime("%Y-%m-%d") if updated else ""

    content_md = zhihu_html_to_md(content_html)

    md_content = f"""# {title}

> **类型**: 文章 | **赞同**: {voteup} | **评论**: {comment}
> **创建时间**: {created_str} | **更新时间**: {updated_str}
> **链接**: https://zhuanlan.zhihu.com/p/{article_id}

---

{content_md}
"""

    filename = clean_filename(f"{created_str}_{title}")
    filepath = articles_dir / f"{filename}.md"
    if filepath.exists():
        filepath = articles_dir / f"{filename}_{index}.md"

    filepath.write_text(md_content, encoding="utf-8")
    return filepath


def save_pin(item, index, output_dir):
    """保存单个想法为md文件"""
    pins_dir = Path(output_dir) / "raw" / "pins"
    pins_dir.mkdir(parents=True, exist_ok=True)

    created = item.get("created", 0)
    created_str = datetime.fromtimestamp(created).strftime("%Y-%m-%d %H:%M") if created else "未知"
    date_str = datetime.fromtimestamp(created).strftime("%Y-%m-%d") if created else "未知"

    content_list = item.get("content", [])
    content_parts = []

    if isinstance(content_list, list):
        for part in content_list:
            if isinstance(part, dict):
                part_type = part.get("type", "")
                if part_type == "text":
                    content_parts.append(part.get("content", ""))
                elif part_type == "image":
                    url = part.get("url", "")
                    content_parts.append(f"![图片]({url})")
                elif part_type == "link":
                    url = part.get("url", "")
                    title = part.get("title", url)
                    content_parts.append(f"[{title}]({url})")
                elif part_type == "video":
                    content_parts.append("[视频]")
                else:
                    content_parts.append(str(part.get("content", "")))
            elif isinstance(part, str):
                content_parts.append(part)
    elif isinstance(content_list, str):
        content_parts.append(content_list)

    text = "\n\n".join(content_parts) if content_parts else str(content_list)

    if "<" in text and ">" in text:
        text = zhihu_html_to_md(text)

    pin_id = item.get("id", "")
    short_text = text[:50].replace('\n', ' ') if text else "想法"

    md_content = f"""# 想法: {short_text}...

> **类型**: 想法 | **时间**: {created_str}
> **链接**: https://www.zhihu.com/pin/{pin_id}

---

{text}
"""

    filename = clean_filename(f"{date_str}_pin_{index}")
    filepath = pins_dir / f"{filename}.md"
    filepath.write_text(md_content, encoding="utf-8")
    return filepath


def main():
    parser = argparse.ArgumentParser(description="知乎用户主页内容批量下载工具")
    parser.add_argument("--user", required=True, help="知乎用户URL token（zhihu.com/people/<token>中的token部分）")
    parser.add_argument("--output", default=".", help="输出目录（默认当前目录）")
    args = parser.parse_args()

    user_token = args.user
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"🎯 目标用户: {user_token}")
    print(f"📁 保存目录: {output_dir}")
    print()

    cookie = get_cookie(output_dir)
    headers = make_headers(cookie, user_token)

    stats = {"answers": 0, "articles": 0, "pins": 0}

    with httpx.Client(follow_redirects=True) as client:
        # 验证Cookie
        print("🔐 验证Cookie...")
        test_resp = client.get(f"{BASE_URL}/me", headers=headers, timeout=10)
        if test_resp.status_code == 200:
            me = test_resp.json()
            print(f"✓ Cookie有效，当前登录用户: {me.get('name', '未知')}")
        else:
            print(f"⚠️  Cookie验证失败 (HTTP {test_resp.status_code})，尝试继续...")
        print()

        # 1. 下载回答
        print("📝 正在下载回答...")
        answers = fetch_all_items(client, headers, user_token, "answers")
        for i, item in enumerate(answers):
            try:
                save_answer(item, i, output_dir)
            except Exception as e:
                print(f"  ⚠️  保存回答 {i} 失败: {e}")
        stats["answers"] = len(answers)
        print(f"✅ 回答下载完成: {len(answers)} 篇\n")

        time.sleep(2)

        # 2. 下载文章
        print("📄 正在下载文章...")
        articles = fetch_all_items(client, headers, user_token, "articles")
        for i, item in enumerate(articles):
            try:
                save_article(item, i, output_dir)
            except Exception as e:
                print(f"  ⚠️  保存文章 {i} 失败: {e}")
        stats["articles"] = len(articles)
        print(f"✅ 文章下载完成: {len(articles)} 篇\n")

        time.sleep(2)

        # 3. 下载想法
        print("💡 正在下载想法...")
        pins = fetch_all_items(client, headers, user_token, "pins")
        for i, item in enumerate(pins):
            try:
                save_pin(item, i, output_dir)
            except Exception as e:
                print(f"  ⚠️  保存想法 {i} 失败: {e}")
        stats["pins"] = len(pins)
        print(f"✅ 想法下载完成: {len(pins)} 条\n")

    # 打印统计
    print("=" * 50)
    print(f"📊 下载完成统计:")
    print(f"   回答: {stats['answers']} 篇")
    print(f"   文章: {stats['articles']} 篇")
    print(f"   想法: {stats['pins']} 条")
    print(f"   总计: {sum(stats.values())} 条内容")
    print("=" * 50)

    # 保存统计信息
    raw_dir = output_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    meta = {
        "user_token": user_token,
        "download_time": datetime.now().isoformat(),
        "stats": stats
    }
    (raw_dir / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2))
    print(f"\n📋 元信息已保存到 {raw_dir / 'meta.json'}")


if __name__ == "__main__":
    main()
