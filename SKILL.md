---
name: zhihu-distill
description: "Download all content from a Zhihu user's profile (answers, articles, pins), filter by topic keywords, merge, and distill into a structured knowledge report using AI. Use when the user wants to extract, analyze, or distill a Zhihu user's content into a comprehensive knowledge system report."
---

# Zhihu User Content Distillation Skill

This skill enables downloading all content from a Zhihu (知乎) user's profile page, filtering by topic, and distilling it into a structured knowledge report.

## When to Use

This skill should be used when:
- A user wants to download all content from a specific Zhihu user
- A user wants to distill/extract a knowledge system from a Zhihu KOL's content
- A user mentions "知乎蒸馏", "知乎下载", or wants to analyze a Zhihu user's posts

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

### Stage 2: Topic Filtering

Run the filter script to select content relevant to a specific topic:

```bash
python3 {SKILL_DIR}/scripts/zhihu_filter.py --input <raw_dir> --output <filtered_dir> --topic <topic>
```

**Built-in topic keyword sets:**
- `invest` (投资): covers stocks, funds, technical indicators, trading terms, industries, famous investors
- `tech` (科技): AI, programming, internet, hardware, etc.
- `custom`: provide a comma-separated keyword list via `--keywords`

**Filtering logic:**
- Scans title + first 3000 characters of content
- Requires at least 2 keyword hits to qualify (reduces noise)
- Copies qualifying files to the filtered output directory
- Prints statistics: total vs. filtered count

### Stage 3: Merge Content

Run the merge script to combine filtered files into a single document:

```bash
python3 {SKILL_DIR}/scripts/zhihu_merge.py --input <filtered_dir> --output <merged_file>
```

**Merge order:** articles → answers → pins (prioritizes systematic content)

**Output:** A single merged `.md` file with `=====` separators between pieces.

### Stage 4: AI Distillation

Read the merged content in batches and generate a structured distillation report. Use the following approach:

1. **Batch reading**: Read 2000-3000 lines per batch (large files may exceed context window)
2. **Priority order**: articles first (most systematic), then answers, then pins
3. **Cross-reference**: Verify consistency of viewpoints across multiple pieces

**Distillation dimensions template** (customize per topic):
1. Author profile (identity, personality, experience years)
2. Core philosophy (beliefs, principles, formulas)
3. Methodology system (frameworks, decision processes)
4. Specific parameters (numbers, thresholds, rules)
5. Domain opinion map (bullish/bearish/cautious views)
6. Signature strategies (unique approaches)
7. Mistakes and reflections (equally important as successes)
8. Key quotes and expressions

**Distillation principles:**
- Cross-validate consistency across multiple pieces
- Preserve specific numbers and parameters
- Note temporal context for time-sensitive views
- Capture both the framework (logic) and parameters (numbers)
- Retain the author's original expression style

### Prompt Templates

Refer to `{SKILL_DIR}/references/prompt_templates.md` for ready-to-use prompts for filtering and distillation.

## Output Structure

```
<output_dir>/
├── raw/
│   ├── answers/          # Individual answer .md files
│   ├── articles/         # Individual article .md files
│   ├── pins/             # Individual pin .md files
│   └── meta.json         # Download statistics
├── filtered/             # Topic-filtered content
├── merged.md             # Combined filtered content
└── distilled/
    └── <user>_<topic>_distill.md  # Final distillation report
```
