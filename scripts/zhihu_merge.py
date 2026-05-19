#!/usr/bin/env python3
"""
知乎内容合并工具
用法: python3 zhihu_merge.py --input <filtered_dir> --output <merged_file>
"""

import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="知乎筛选内容合并工具")
    parser.add_argument("--input", required=True, help="筛选后的内容目录（包含 answers/articles/pins 子目录）")
    parser.add_argument("--output", required=True, help="合并输出文件路径（.md）")
    args = parser.parse_args()

    input_dir = Path(args.input)
    output_file = Path(args.output)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    SEPARATOR = "\n\n" + "=" * 60 + "\n\n"

    # 合并顺序：文章 > 回答 > 想法（优先系统性内容）
    merge_order = ["articles", "answers", "pins"]

    all_parts = []
    stats = {}

    for subdir_name in merge_order:
        src_dir = input_dir / subdir_name
        if not src_dir.exists():
            continue

        files = sorted(src_dir.glob("*.md"))
        stats[subdir_name] = len(files)

        for md_file in files:
            try:
                content = md_file.read_text(encoding="utf-8").strip()
                if content:
                    all_parts.append(content)
            except Exception as e:
                print(f"  ⚠️  读取失败: {md_file.name}: {e}")

    if not all_parts:
        print("⚠️  没有找到任何内容")
        return

    # 写入合并文件
    merged_content = SEPARATOR.join(all_parts)
    output_file.write_text(merged_content, encoding="utf-8")

    # 统计
    total = sum(stats.values())
    file_size_kb = output_file.stat().st_size / 1024

    print(f"✅ 合并完成:")
    for name, count in stats.items():
        print(f"   {name}: {count} 篇")
    print(f"   总计: {total} 篇")
    print(f"   文件大小: {file_size_kb:.1f} KB")
    print(f"   输出: {output_file}")


if __name__ == "__main__":
    main()
