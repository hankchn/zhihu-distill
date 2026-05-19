# zhihu-distill

知乎用户主页全量下载并 AI 蒸馏的 CodeBuddy Skill。输入知乎用户链接，自动下载全部回答、文章、想法，保存为 Markdown 文件，然后生成结构化的知识体系蒸馏报告。

## Features

- **全量下载**: 自动爬取知乎用户的全部回答、文章、想法(pins)，转为干净的 Markdown
- **主题筛选**: 内置投资/科技关键词库，支持自定义关键词，智能过滤相关内容
- **内容合并**: 按优先级（文章>回答>想法）合并为单一文档
- **AI 蒸馏**: 提供结构化 Prompt 模板，引导 AI 生成深度知识体系报告

## Installation

作为 CodeBuddy Skill 使用：

```bash
# 解压到用户 skill 目录
unzip zhihu-distill.zip -d ~/.codebuddy/skills/
```

或独立使用脚本：

```bash
pip install httpx markdownify beautifulsoup4
```

## Usage

### 1. 下载

```bash
python3 scripts/zhihu_download.py --user <user_token> --output ./data
```

其中 `user_token` 是知乎个人主页 URL 中的标识：`zhihu.com/people/<user_token>`

首次运行会提示输入知乎 Cookie（从浏览器开发者工具获取）。

### 2. 筛选

```bash
# 使用内置投资主题
python3 scripts/zhihu_filter.py --input ./data/raw --output ./data/filtered --topic invest

# 使用自定义关键词
python3 scripts/zhihu_filter.py --input ./data/raw --output ./data/filtered --keywords "AI,机器学习,大模型"
```

### 3. 合并

```bash
python3 scripts/zhihu_merge.py --input ./data/filtered --output ./data/merged.md
```

### 4. AI 蒸馏

将合并后的文件分批发送给 AI，使用 `references/prompt_templates.md` 中的模板生成蒸馏报告。

## File Structure

```
zhihu-distill/
├── SKILL.md                    # CodeBuddy Skill 定义
├── scripts/
│   ├── zhihu_download.py       # 下载脚本
│   ├── zhihu_filter.py         # 筛选脚本
│   └── zhihu_merge.py          # 合并脚本
├── references/
│   └── prompt_templates.md     # 蒸馏 Prompt 模板
├── .gitignore
└── README.md
```

## Notes

- 需要有效的知乎 Cookie（有效期有限，过期需重新获取）
- 脚本内置随机延迟（1.5-3秒）以避免触发反爬
- Cookie 文件（`cookie.txt`）已在 `.gitignore` 中排除，不会上传

## License

MIT
