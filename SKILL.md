---
name: zhihu-distill
description: "Download all content from a Zhihu user's profile (answers, articles, pins), optionally filter by topic, merge, and distill into a structured knowledge report using AI. Supports any domain — investment, tech, education, health, design, etc. Use when the user wants to extract, analyze, or distill a Zhihu user's content into a comprehensive knowledge system report."
---

# Zhihu User Content Distillation Skill

This skill enables downloading all content from a Zhihu (知乎) user's profile page, optionally filtering by any topic, and distilling it into a structured knowledge report. It is domain-agnostic — works for investment KOLs, tech bloggers, medical professionals, educators, designers, or any other field.

## When to Use

This skill should be used when:
- A user wants to download all content from a specific Zhihu user
- A user wants to distill/extract a knowledge system from any Zhihu creator's content
- A user mentions "知乎蒸馏", "知乎下载", or wants to analyze a Zhihu user's posts
- A user provides a Zhihu profile link and wants a structured summary

## Complete Workflow

The distillation process follows four stages:

### Stage 1: Download All Content

Run the download script to fetch all content from the target Zhihu user:

```bash
python3 {SKILL_DIR}/scripts/zhihu_download.py --user <user_token> --output <output_dir>
```

**Prerequisites:**
- A valid Zhihu cookie is required. Obtain it from Chrome DevTools (F12 → Network → any request → Cookie header)
- Save the cookie to a `cookie.txt` file in the output directory, or the script will prompt for it
- Install dependencies: `pip install httpx markdownify beautifulsoup4`

**What it does:**
- Downloads all answers, articles, and pins (想法) from the user
- Converts HTML to clean Markdown with metadata (vote count, date, link)
- Saves each piece as an individual `.md` file
- Creates a `meta.json` with download statistics

**Important notes:**
- The `user_token` is the slug in the Zhihu profile URL: `zhihu.com/people/<user_token>`
- Some users have hash-based tokens (e.g., `884c8e36c6cbbb30caf79345b660b227`) instead of readable names
- Random delays (1.5-3s) are built in to avoid rate limiting
- Cookie validity is limited; if you get 401 errors, refresh the cookie

### Stage 2: Topic Filtering (Optional)

If the user's content spans multiple domains and only a subset is needed, run the filter script:

```bash
python3 {SKILL_DIR}/scripts/zhihu_filter.py --input <raw_dir> --output <filtered_dir> --topic <topic>
```

**Built-in topic keyword sets:**
- `invest` (投资): stocks, funds, technical indicators, trading terms, industries
- `tech` (科技): AI, programming, internet, hardware, software
- `edu` (教育): 教学, 学习方法, 考试, 课程, 教育理念
- `health` (健康): 医学, 健身, 营养, 心理健康, 疾病
- `design` (设计): UI, UX, 交互设计, 视觉, 品牌
- `custom`: provide any comma-separated keyword list via `--keywords "关键词1,关键词2,..."`

**Skip this step** if the user's content is already highly focused on one topic (e.g., a single-domain creator), or if a full distillation of all content is desired.

**Filtering logic:**
- Scans title + first 3000 characters of content
- Requires at least 2 keyword hits to qualify (configurable via `--min-hits`)
- Copies qualifying files to the filtered output directory

### Stage 3: Merge Content

Run the merge script to combine files into a single document:

```bash
python3 {SKILL_DIR}/scripts/zhihu_merge.py --input <filtered_dir_or_raw_dir> --output <merged_file>
```

**Merge order:** articles → answers → pins (prioritizes systematic content)

**Output:** A single merged `.md` file with `=====` separators between pieces.

### Stage 4: AI Distillation

Read the merged content in batches and generate a structured distillation report.

**Batch reading strategy:**
1. Read 2000-3000 lines per batch (large files may exceed context window)
2. Priority order: articles first (most systematic), then answers, then pins
3. After each batch, record key information points
4. After all batches, synthesize into a unified report

**Adaptive distillation dimensions:**

Based on the author's domain, select and customize the appropriate dimensions. The core framework is:

1. **Author Profile** — identity, background, expertise years, personality traits
2. **Core Philosophy** — fundamental beliefs, first principles, guiding values
3. **Knowledge Framework** — how they organize and structure their domain knowledge
4. **Methodology** — specific methods, processes, workflows they advocate
5. **Key Parameters** — concrete numbers, thresholds, criteria they use
6. **Domain Opinion Map** — their stance on major topics/debates in the field
7. **Signature Approaches** — unique or distinctive methods they've developed
8. **Evolution & Reflections** — how their views changed over time, mistakes acknowledged
9. **Practical Recommendations** — actionable advice they give to others
10. **Key Quotes** — memorable expressions in their original voice

**Domain-specific dimension examples** (add on top of core framework):

| Domain | Additional Dimensions |
|--------|----------------------|
| Investment | 选股体系, 仓位管理, 技术分析框架, 行业观点, ETF配置, 持仓方向 |
| Tech/Programming | 技术栈偏好, 架构理念, 工具链, 代码哲学, 项目经验 |
| Education | 教学方法, 学习路径设计, 评估方式, 学生画像, 课程设计理念 |
| Health/Medical | 诊疗思路, 循证态度, 生活方式建议, 误区纠正, 专科观点 |
| Design | 设计原则, 审美倾向, 工作流程, 工具偏好, 案例分析方法 |
| Writing/Content | 写作方法论, 选题策略, 读者洞察, 风格特征, 内容结构模式 |

**Distillation principles (universal):**
- Cross-validate consistency across multiple pieces
- Preserve specific numbers, parameters, and concrete examples
- Note temporal context — mark when views evolved or changed
- Capture both the framework (logic/reasoning) and details (specifics)
- Retain the author's original expression style and voice
- Mistakes, failures, and reflections are equally important as successes
- Distinguish between strongly-held beliefs vs. tentative opinions

### Prompt Templates

Refer to `{SKILL_DIR}/references/prompt_templates.md` for ready-to-use prompts adaptable to any domain.

## Output Structure

```
<output_dir>/
├── raw/
│   ├── answers/          # Individual answer .md files
│   ├── articles/         # Individual article .md files
│   ├── pins/             # Individual pin .md files
│   └── meta.json         # Download statistics
├── filtered/             # Topic-filtered content (if filtering was applied)
├── merged.md             # Combined content for distillation
└── distilled/
    └── <user>_<topic>_distill.md  # Final distillation report
```
