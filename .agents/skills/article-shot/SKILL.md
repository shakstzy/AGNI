---
name: article-shot
description: The article-shot adapter captures crystal clear, retina high-DPI screenshots of technical articles, research papers (arXiv, blogs, GitHub repos), and web documentation for embedding into articles, threads, and social posts.
---

# Web Article & Paper Screenshot CLI User Guide

The `article-shot` adapter captures crystal clear, retina high-DPI screenshots of technical articles, research papers (arXiv, blogs, GitHub repos), and web documentation for embedding into articles, threads, and social posts.

## Common Operations

### 1. Capture Research Paper or Article
```bash
# Capture crisp viewport screenshot (2x device scale)
article-shot "https://arxiv.org/abs/2406.09246" -o ./assets/openvla_paper.png

# Capture full scrollable page
article-shot "https://example.com/blog/ai" -o ./assets/full_article.png --full
```

### 2. Capture Specific Element / Diagram
```bash
# Capture paper abstract or main article container
article-shot "https://arxiv.org/abs/2406.09246" -s ".blockquote" -o ./assets/abstract.png

# Dark mode emulation
article-shot "https://github.com/shakstzy" -o ./assets/github_profile.png --dark
```

### 3. Python API Integration
```python
from workspaces.socials.article_shot import capture_url

# Capture screenshot directly
path = capture_url("https://arxiv.org/abs/2310.06770", output_path="./assets/swe_bench.png", wait_seconds=2)
```
