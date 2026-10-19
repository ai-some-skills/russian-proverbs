---
name: russian-proverbs
description: Choose Russian proverbs and sayings that fit a situation, explain their meaning, and assess tone and appropriateness. Use when asked to find a saying, express an idea through a proverb, or add a suitable proverb to a text. An ordinary request to write in Russian does not call for proverbs in every response.
---

# Russian Proverbs

Choose a Russian proverb or saying that makes the user's intended meaning clearer. Match the situation, audience, and tone; leave the text without a proverb when none fits.

## Working language

Respond in natural Russian by default, including colloquial registers when appropriate. Follow an explicit request for another output language. The English entry point supports discovery; it does not request English output or translation of the Russian corpus.

## Workflow

Before selecting, explaining, or editing a proverb, read and follow the [Russian workflow](references/workflow.ru.md). It contains the complete selection process, editorial constraints, and source-handling rules. Paths to scripts and data in that workflow are relative to this skill's root directory.

Use the bundled local search script rather than loading the corpus into context. It returns up to five candidates and 5,000 characters by default. Search is lexical; candidate ranking does not establish suitability. Evaluate meaning and cautions before choosing an expression.

The source collection mainly reflects records from the 1930s. The corpus includes source pages and editorial annotations, but inclusion does not establish modern frequency. See the [corpus reference](references/corpus.md) when maintaining or auditing the data.

For installation, examples, and limitations, see the [English README](README.md) or [Russian README](README.ru.md).
