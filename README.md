# MY-SKILLS

Parsa's personal collection of 23 agent skills. Each directory contains a `SKILL.md` file and any supporting references, scripts, templates, or licenses.

## My skill selection

All 23 skills are selected for Codex. The 14 skills marked below are also selected for Claude Code. A dash means I have not selected that skill for Claude; it does not indicate incompatibility.

| Skill | Codex | Claude Code |
| --- | :---: | :---: |
| [codebase-design](codebase-design/SKILL.md) | Yes | Yes |
| [database-schema-designer](database-schema-designer/SKILL.md) | Yes | — |
| [find-skills](find-skills/SKILL.md) | Yes | — |
| [form-creation](form-creation/SKILL.md) | Yes | — |
| [frontend-design](frontend-design/SKILL.md) | Yes | — |
| [grilling](grilling/SKILL.md) | Yes | — |
| [gsap-core](gsap-core/SKILL.md) | Yes | Yes |
| [gsap-frameworks](gsap-frameworks/SKILL.md) | Yes | Yes |
| [gsap-performance](gsap-performance/SKILL.md) | Yes | Yes |
| [gsap-plugins](gsap-plugins/SKILL.md) | Yes | Yes |
| [gsap-react](gsap-react/SKILL.md) | Yes | Yes |
| [gsap-scrolltrigger](gsap-scrolltrigger/SKILL.md) | Yes | Yes |
| [gsap-timeline](gsap-timeline/SKILL.md) | Yes | Yes |
| [gsap-utils](gsap-utils/SKILL.md) | Yes | Yes |
| [humanizer](humanizer/SKILL.md) | Yes | Yes |
| [improve-codebase-architecture](improve-codebase-architecture/SKILL.md) | Yes | Yes |
| [nuqs-nextjs-v16](nuqs-nextjs-v16/SKILL.md) | Yes | — |
| [postgres-best-practices](postgres-best-practices/SKILL.md) | Yes | Yes |
| [review-visualizer](review-visualizer/SKILL.md) | Yes | — |
| [shadcn](shadcn/SKILL.md) | Yes | — |
| [supabase](supabase/SKILL.md) | Yes | — |
| [to-spec](to-spec/SKILL.md) | Yes | Yes |
| [to-tickets](to-tickets/SKILL.md) | Yes | Yes |

## Install with the skills CLI

Requires Node.js 22.20 or later and `npx`. These commands work in PowerShell and in macOS/Linux shells.

List the repository's skills without installing:

```sh
npx skills add Searedphantasm/MY-SKILLS --list
```

Choose skills interactively for an agent:

```sh
npx skills add Searedphantasm/MY-SKILLS --global --agent claude-code
```

`--global` makes skills available across your projects. For a project installation, run the command inside that project and omit `--global`. Installation applies to the current machine and user environment; Windows and WSL need separate setups.

### Codex: install all 23 skills

```sh
npx skills add Searedphantasm/MY-SKILLS --global --agent codex --skill '*' --copy --yes
```

### Claude Code: install my 14 selected skills

This command matches the Claude Code column above:

```sh
npx skills add Searedphantasm/MY-SKILLS --global --agent claude-code --skill codebase-design postgres-best-practices improve-codebase-architecture gsap-core gsap-frameworks gsap-performance gsap-plugins gsap-react gsap-scrolltrigger gsap-timeline gsap-utils humanizer to-spec to-tickets --copy --yes
```

### Cursor, GitHub Copilot, and Gemini CLI

I have not chosen a personal selection for these agents yet. To install one skill:

```sh
npx skills add Searedphantasm/MY-SKILLS --global --agent cursor --skill humanizer --copy --yes
npx skills add Searedphantasm/MY-SKILLS --global --agent github-copilot --skill humanizer --copy --yes
npx skills add Searedphantasm/MY-SKILLS --global --agent gemini-cli --skill humanizer --copy --yes
```

Replace `humanizer` with the skill you want. `--copy` creates independent copies; omit it to use the CLI's shared-link installation method. Copies do not sync automatically when this repository changes. `--yes` skips prompts, so review local edits before reinstalling skills.

See the [skills CLI reference](https://github.com/vercel-labs/skills/blob/main/docs/commands.md) for installation options.

## Installation paths

These are the destinations used by fresh installations through the skills CLI. `~` means your user directory; in PowerShell, use `$env:USERPROFILE` when building a path.

| Agent | `--agent` value | Global directory | Project directory |
| --- | --- | --- | --- |
| Claude Code | `claude-code` | `~/.claude/skills/` | `.claude/skills/` |
| Codex | `codex` | `~/.agents/skills/` | `.agents/skills/` |
| Cursor | `cursor` | `~/.cursor/skills/` | `.agents/skills/` |
| GitHub Copilot | `github-copilot` | `~/.copilot/skills/` | `.agents/skills/` |
| Gemini CLI | `gemini-cli` | `~/.gemini/skills/` | `.agents/skills/` |

Source: [CLI agent names and installation paths](https://github.com/vercel-labs/skills/blob/main/docs/agents.md). These paths describe CLI installation; check the agent's own documentation when installing manually.

For manual installation, copy a complete skill directory into the agent's destination, for example `~/.claude/skills/humanizer/SKILL.md`. Keep supporting files alongside it so references continue to work.

### My current setup: October 29, 2026

- **Codex:** all 23 skills are installed. Twenty existing installations live in `~/.codex/skills/`; `find-skills`, `frontend-design`, and `shadcn` live in `~/.agents/skills/`. Fresh CLI installations use the table above. Avoid duplicate installations when moving skills between locations.
- **Claude Code:** only the 14 selected skills are installed, as independent copies in `~/.claude/skills/`.
- Saving a skill in this repository does not install it into an agent automatically.

## Use and verify skills

List global installations for an agent:

```sh
npx skills list --global --agent claude-code
npx skills list --global --agent codex
```

In Claude Code, invoke a skill with `/humanizer` or `/to-spec`. In Codex, use `$humanizer` or `$to-spec`. Start a new session if a newly installed skill does not appear.

`to-spec`, `to-tickets`, and `improve-codebase-architecture` require explicit invocation. The first two need issue-tracker and label configuration; their instructions refer to the upstream `setup-matt-pocock-skills` skill, which is not included here. The architecture workflow also references `grilling` and `domain-modeling`: `grilling` is in this repository but is not selected for Claude, while `domain-modeling` can be obtained from [Matt Pocock's skills](https://github.com/mattpocock/skills) if needed.

For loading and invocation details, see [Claude Code skills](https://code.claude.com/docs/en/skills) and the [official Codex skills documentation](https://learn.chatgpt.com/docs/build-skills).

## Maintaining the collection

Keep each skill's supporting files and existing licenses together. This collection includes personal and third-party skills; check the license files within each directory for their terms. To recreate the setup on another machine, use the selection table and the relevant installation command above.
