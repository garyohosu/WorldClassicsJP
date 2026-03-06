
# SPEC.md
WorldClassicsJP Specification

---

# 1. Overview

WorldClassicsJP is an automated publishing system that translates public domain world literature into Japanese and publishes it as a static website.

The system retrieves texts from public domain sources (such as Project Gutenberg), translates them into Japanese using AI, and publishes them on GitHub Pages.

The goal is to build an AI-powered literature publishing platform where classic works from around the world become accessible to Japanese readers.

---

# 2. Goals

Primary goals:

- Translate public domain world literature into Japanese
- Publish translated works automatically
- Support both short works and long-form serialized works
- Create author-based navigation
- Enrich content using public domain images
- Generate advertising revenue using Google AdSense

---

# 3. Key Design Principles

1. Full automation
2. Static site publishing
3. Reusable architecture
4. AI-agent driven workflow
5. Low operational cost
6. Mobile-first user experience

---

# 4. System Architecture

Pipeline:

Source Text
↓
Fetcher
↓
Preprocessor (Local LLM)
↓
Translator (Codex CLI)
↓
Publisher
↓
GitHub Pages

Automation is triggered by OpenClaw cron execution.

---

# 5. Execution Environment

Automation is executed by OpenClaw.

OpenClaw responsibilities:

- run scheduled jobs via cron
- orchestrate AI agents
- execute translation commands
- commit and push results to GitHub

---

# 6. Scheduling

Execution frequency: once per day.

Cron execution is handled by OpenClaw.

Example:

0 3 * * *

This triggers the full translation pipeline.

---

# 7. Translation Engine

Translation is executed using Codex CLI.

Important requirement:

Codex CLI must run in non-interactive execution mode.

Example:

codex exec translate_prompt.md

The Codex CLI flat-rate plan is used to control translation cost.

---

# 8. Local LLM Usage

Local LLMs should assist with:

- paragraph segmentation
- text cleanup
- metadata generation
- summaries
- title normalization

Local models may run using Ollama or similar systems.

Advantages:

- reduce API token usage
- enable offline processing
- faster preprocessing

---

# 9. Source Data

Primary sources:

- Project Gutenberg
- Internet Archive
- other public domain literature repositories

Each work must include:

- title
- author
- source URL
- public domain confirmation

---

# 10. Work Classification

Works are classified by length.

short
medium
long

Example thresholds:

short: < 30,000 characters
medium: 30,000–150,000 characters
long: > 150,000 characters

---

# 11. Publication Unit

Short works:

Published in a single execution.

Long works:

Published in serialized parts.

Preferred segmentation:

- chapter boundaries
- paragraph blocks if chapters exceed daily limit

---

# 12. Daily Translation Limit

To control cost and execution time:

Maximum translation volume per day must be defined.

Example:

max_chars_per_day = 12000

If a chapter exceeds this limit, it must be subdivided.

---

# 13. Serialization Policy

If a long work begins:

The system must continue publishing subsequent parts until the work is complete.

Do not switch works during serialization unless explicitly configured.

---

# 14. Site Structure

Example:

/
index.html
authors/
works/
assets/
rss.xml
sitemap.xml
robots.txt

Example work structure:

/works/<work-slug>/index.html
/works/<work-slug>/part-001/index.html
/works/<work-slug>/part-002/index.html

---

# 15. Author Pages

Author navigation is mandatory.

Structure:

/authors/index.html
/authors/<author-slug>/index.html

Author pages include:

- author portrait
- biography summary
- list of translated works
- progress for serialized works

Example:

Mark Twain
Tom Sawyer (In Progress)
Jumping Frog (Complete)

---

# 16. Author Metadata

Required fields:

author_name
author_slug
birth_year
death_year
description

---

# 17. Public Domain Image Policy

Public domain images should be used whenever possible.

Sources:

- Wikimedia Commons
- Wikipedia
- Project Gutenberg illustrations
- historical archives

Images improve:

- visual quality
- reading experience
- SEO performance

---

# 18. Author Portrait Support

Author pages must include portraits when available.

Portraits should be retrieved from Wikimedia Commons.

Example:

/assets/images/authors/mark-twain.jpg

---

# 19. Illustration Support

Original illustrations should be preserved when available.

Placement:

between paragraphs or section boundaries.

---

# 20. Image Storage

Images stored locally:

/assets/images/authors/
/assets/images/illustrations/
/assets/images/decorative/

---

# 21. Image Metadata

Each image includes metadata:

source
author
license
year

---

# 22. Mobile Compatibility

Mobile-first responsive design required.

Requirements:

- readable typography
- responsive images
- simple navigation
- fast loading pages

Images:

max-width: 100%
lazy loading enabled

---

# 23. Navigation Requirements

Work pages must include:

Previous
Next
Table of Contents
Author Page

---

# 24. Advertising Integration

Google AdSense must appear on all pages.

Pages include:

- homepage
- author pages
- work pages
- serialized pages

Recommended placements:

header
mid-article
footer

Advertising must not disrupt reading.

---

# 25. State Management

System state tracked in:

state.json

Example:

next_work_id
current_part
current_work_status
last_processed_date

Statuses:

active
paused
exhausted

---

# 26. Error Handling

If translation fails:

- do not update state
- log error
- retry next cycle

If publishing fails:

- abort commit
- preserve previous state

---

# 27. Repository

Repository:

https://github.com/garyohosu/WorldClassicsJP

Deployment target:

GitHub Pages

---

# 28. SEO Strategy

SEO improvements:

- author pages
- image alt text
- structured metadata
- RSS feed
- sitemap

---

# 29. Long-term Vision

WorldClassicsJP is an AI-driven world literature archive.

Future possibilities:

- multilingual translation
- author timeline pages
- literature discovery tools
- cross-language literary datasets

The platform aims to become a global public domain literature hub.
