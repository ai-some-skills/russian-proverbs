# Russian Proverbs — Пословица к месту

**English** | [Русский](README.ru.md)

An Agent Skill for choosing Russian proverbs and sayings that fit the meaning, situation, and tone of a text. It explains figurative meanings and helps avoid expressions that sound forced, patronizing, or hurtful.

The skill instructions and corpus are in Russian. It is designed for Russian-language writing and conversation, including everyday colloquial speech. This English README introduces the skill to readers who work with Russian content; it does not turn it into an English-language proverb collection.

The corpus contains **228 expressions and 13 variants** selected from M. A. Rybnikova's *Русские пословицы и поговорки* (*Russian Proverbs and Sayings*, 1961). Entries include source pages, brief meanings, usage situations, tone, and cautions. The agent can also leave a text without a proverb when none fits.

## Installation

Search requires **Python 3.9+**. No additional packages or API services are needed for normal use.

### Through skills.sh

With Node.js installed, run:

```bash
npx skills add ai-some-skills/russian-proverbs
```

The CLI offers agent and installation-scope selection. See the [skills.sh documentation](https://skills.sh/docs). The [skills.sh directory](https://skills.sh) uses CLI installation events; publishing a GitHub repository alone does not guarantee immediate listing.

### Directly from GitHub

Ask Codex:

```text
Install the skill from https://github.com/ai-some-skills/russian-proverbs
```

Or clone it into your personal Codex skills directory:

```bash
git clone https://github.com/ai-some-skills/russian-proverbs.git \
  ~/.agents/skills/russian-proverbs
```

If the destination already exists, inspect it before installing. For Claude Code, use `~/.claude/skills/russian-proverbs` instead. `SKILL.md` must sit at the root of the skill directory.

## Usage

Keep requests and examples in Russian when working on Russian text:

| Russian request | Meaning and intended tone |
| --- | --- |
| «Подбери поговорку: команда долго готовится, пора попробовать простое обратимое решение» | Find a saying that encourages a small, reversible attempt rather than further preparation. |
| «Добавь одну уместную пословицу в этот текст, без назидания» | Add one fitting proverb without sounding preachy. |
| «Объясни смысл поговорки и проверь, не прозвучит ли она как упрёк» | Explain the meaning and check whether it might sound like a rebuke. |
| «Используй $russian-proverbs: поддержи человека после первой ошибки» | Use the skill to support someone after an early mistake. |

An ordinary request to write in Russian does not make the skill add proverbs to every response.

## How search works

The agent reads a short instruction file and runs a local search. The corpus stays on disk. By default, the script returns up to **five candidates within 5,000 characters in total**. The search script makes no network requests and uses no APIs or telemetry. These properties describe the bundled script, not the host AI agent or the skills.sh installer.

From the repository root:

```bash
python3 scripts/search.py 'сначала проверить решение которое трудно отменить' --limit 3
python3 scripts/search.py 'поддержать после первой ошибки' --tone supportive
python3 scripts/search.py --id ryb-0045 --details
```

The first query asks about checking a decision before an action that is hard to undo. In the tested version, the first result is **«Семь раз примерь, а один отрежь»**: check the fit repeatedly before making an irreversible cut. This is the wording recorded in the selected book entry.

The script returns JSON. `--details` adds the source form, variants, and verification information. Search is lexical, with lightweight word-form handling; a query sometimes needs rephrasing. Ranking does not establish appropriateness: the agent must assess each candidate against the context and entry cautions.

## Source and corpus limitations

M. A. Rybnikova. **Русские пословицы и поговорки**. Responsible editor: B. P. Kirdan. Moscow: Publishing House of the USSR Academy of Sciences, 1961. The source was a user-provided PDF of 230 pages. Its checksum is recorded in the [source manifest](data/sources.json).

The collection mainly reflects records from the 1930s. Inclusion in the book does not establish current frequency or suitability. Meanings, usage situations, tone, and cautions are this project's editorial annotations, not quotations from the compiler's explanations. When present, `source_note` separately identifies an explanation from the book.

All included wordings and variants were matched against the PDF text layer; four entries were additionally checked against the scan. A full visual proofread has not been completed. The source PDF, the complete book text, and the appendix of literary aphorisms are not distributed in this repository.

See the [corpus reference](references/corpus.md), written in Russian, for field definitions and maintenance guidance.

## Checks

From the repository root:

```bash
python3 scripts/validate.py
python3 -m unittest discover -s evals -p 'test_*.py' -v
```

The first version passed corpus validation and nine automated tests covering situation-based retrieval, variants, filters, empty matches, opposite sayings, output limits, and execution from another directory. The [agent evaluation prompts](evals/evals.json) also cover support after a mistake, preserving a precise technical requirement, and moving from preparation to a trial. These checks do not establish quality for every possible request.

Optional verification against the original PDF requires `pypdf`:

```bash
python3 scripts/validate.py --pdf /path/to/source.pdf
```

## License

Original instructions, code, tests, and editorial annotations are available under [MIT](LICENSE). This license does not cover the cited book or other third-party works and does not grant rights to republish them. Source-page references are retained for the expressions; the original provenance of every expression has not been independently researched.
