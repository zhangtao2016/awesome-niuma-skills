
# Medical Imaging AI Literature Review Skill

A Claude Code skill for writing comprehensive literature reviews in medical imaging AI research.

## Overview

This skill provides a systematic workflow for writing survey papers, systematic reviews, and literature analyses on topics like segmentation, detection, and classification in CT, MRI, X-ray imaging.

## Features

- **Structured 7-phase workflow** for literature review writing
- **Domain-specific templates** covering multiple medical imaging domains
- **Standardized writing style** with hedging language and citation patterns
- **Quality checklists** ensuring completeness
- **Zotero integration** for reference management

## Installation

Copy this skill folder to your Claude Code skills directory:

```
~/.claude/skills/medical-imaging-review/
```

## Trigger Keywords

The skill automatically activates when detecting:
- "review paper"
- "survey"
- "literature review"
- "综述"
- Mentions of writing academic reviews on deep learning for medical imaging

## Files

| File | Description |
|------|-------------|
| `SKILL.md` | Main skill definition and quick reference |
| `WORKFLOW.md` | Detailed 7-phase workflow guide |
| `TEMPLATES.md` | Project file templates (CLAUDE.md, IMPLEMENTATION_PLAN.md) |
| `DOMAINS.md` | Domain-specific method categories and datasets |

## Supported Domains

- **Coronary Artery Analysis** (CCTA)
- **Lung Imaging** (CT/X-ray)
- **Brain Imaging** (MRI/CT)
- **Cardiac Imaging** (MRI/CT/Echo)
- **Pathology** (Whole Slide Images)
- **Retinal Imaging** (Fundus/OCT)
- **General Medical Image Segmentation**

## Workflow Phases

1. **Project Initialization** - Create project structure and templates
2. **Literature Collection** - Gather papers via Zotero/web search
3. **Outline Development** - Define section structure
4. **Section Writing** - Write each section with standard templates
5. **Tables and Figures** - Create comparison tables and figure placeholders
6. **Quality Assurance** - Structure, content, and language checks
7. **Incremental Updates** - Version control for new literature

## Standard Review Structure

```
# [Title]: State of the Art and Future Directions
## Key Points
## Abstract
## 1. Introduction
## 2. Datasets and Evaluation Metrics
## 3. Deep Learning Methods
## 4. Downstream Applications
## 5. Commercial Products & Clinical Translation
## 6. Discussion
## 7. Conclusion
## References
```

## Writing Guidelines

- Use **hedging language**: "may", "suggests", "appears to"
- Avoid absolute claims
- Every claim needs citation support
- Each method section needs a **Limitations** paragraph
- Include **comparison tables** for each major section
- Target **80-120 references** per review

## License

MIT License
