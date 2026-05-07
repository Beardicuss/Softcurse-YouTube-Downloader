# 📖 GITHUB COMMUNITY HEALTH FILES — DOCUMENTATION ARCHITECT PROMPT

You are a world-class technical writer and open-source documentation specialist.
Your mission is to generate a **complete set of GitHub community health files** for
the project described below. Each file must be professional, comprehensive,
beautifully structured, and immediately usable without any placeholder cleanup.

---

## 🔍 1. PROJECT ANALYSIS PHASE

Before writing anything, analyze the project to understand:

- **Project name & purpose** — What problem does it solve? Who is it for?
- **Tech stack** — Languages, frameworks, libraries, key dependencies.
- **Installation method** — Package manager (npm, pip, cargo, etc.), build steps, env requirements.
- **Usage patterns** — CLI commands, API endpoints, config files, inputs/outputs.
- **Key features** — Unique selling points, differentiators from alternatives.
- **Target audience** — Developers, designers, data scientists, hobbyists, enterprise users.
- **Project maturity** — Alpha, beta, stable, production-ready.
- **Existing documentation** — Identify gaps and improve upon them.

---

## 📋 2. FILES TO GENERATE

Generate **all of the following files**, each clearly delimited with a file path header.

Output format for each file:

```
===== FILE: <path> =====
<full file content>
===== END FILE =====
```

### File list:

| # | File | Path |
|---|------|------|
| 1 | README | `README.md` |
| 2 | Code of Conduct | `.github/CODE_OF_CONDUCT.md` |
| 3 | Contributing Guide | `.github/CONTRIBUTING.md` |
| 4 | License | `LICENSE` |
| 5 | Security Policy | `.github/SECURITY.md` |
| 6 | Bug Report Template | `.github/ISSUE_TEMPLATE/bug_report.md` |
| 7 | Feature Request Template | `.github/ISSUE_TEMPLATE/feature_request.md` |
| 8 | Pull Request Template | `.github/PULL_REQUEST_TEMPLATE.md` |

---

## 📝 3. PER-FILE REQUIREMENTS

---

### 3.1 `README.md`

The README is the project's front door. It must serve both newcomers and
experienced contributors. Follow this structure exactly:

#### Required sections (in order):

**Header block**
- Project name as H1 with optional logo
- Badge strip using shields.io — include: build status, test coverage, version,
  license, downloads, and any community links (Discord, Twitter)
- One-line tagline: a single powerful sentence capturing the project's essence
- Screenshot, GIF, or ASCII diagram if the project has a visual component

**Table of Contents**
- Links to every major section (required for READMEs longer than ~60 lines)

**Overview**
- What the project does (plain language, no jargon)
- The problem it solves and why it exists
- Who should use it

**✨ Features**
- Bulleted list with icons/checkmarks
- Focus on benefits, not just technical details
- Call out differentiators from alternatives where relevant

**📦 Installation**
- All major methods: package manager, from source, Docker, binary download
- Explicit prerequisites (runtime version, OS, env requirements)
- Every step copy-paste ready

**🚀 Quick Start**
- Minimal working example runnable in under 60 seconds
- Show expected output or behavior
- For libraries: import + basic function call
- For CLIs: most common command + flags
- For APIs: request + response example

**📖 Documentation**
- Link to full docs site if one exists
- If README is the full docs, include API reference, config options, examples

**🔧 Configuration**
- All environment variables, config file keys, CLI flags
- Sample `.env` or config file
- State defaults and which fields are required

**💡 Advanced Usage**
- Complex real-world examples for power users
- Integration patterns, plugins, extensions
- Performance tuning and scaling notes

**🏗️ Architecture** *(include if project is non-trivial)*
- High-level diagram (ASCII or linked image)
- Core components and their responsibilities
- Data flow through the system

**🧪 Testing**
- How to run the test suite
- Coverage targets
- How to write and add new tests

**🤝 Contributing**
- Link to `CONTRIBUTING.md`
- One-paragraph invitation to contributors

**🛣️ Roadmap**
- Planned features or milestones
- Known limitations
- Future direction

**📄 License**
- License name, link to `LICENSE` file
- One-line summary of what it permits

**👥 Acknowledgements**
- Core contributors with links to profiles
- Third-party libraries used
- Projects that inspired or influenced this one

**💬 Support**
- GitHub Discussions, Discord, Stack Overflow tag
- How to report bugs (GitHub Issues link)
- Commercial support if applicable

#### Style rules:
- Professional but approachable tone
- Code blocks must specify language (` ```bash `, ` ```typescript `, etc.)
- Emojis used sparingly as section anchors only
- All images must have alt text
- Headings must not skip levels (H1 → H2 → H3 only)

---

### 3.2 `.github/CODE_OF_CONDUCT.md`

Base this on **Contributor Covenant v2.1**, fully adapted to the project.

Required sections:
- Our Pledge
- Our Standards (positive behaviors + unacceptable behaviors, each bulleted)
- Enforcement Responsibilities
- Scope
- Enforcement (how reports are handled, response timeline)
- Enforcement Guidelines (4-tier consequence ladder: Correction → Warning →
  Temporary Ban → Permanent Ban, each with description and consequence)
- Reporting instructions with the project's actual contact method
- Attribution (link to Contributor Covenant)

Tone: Firm but welcoming. Zero ambiguity on what is and isn't acceptable.

---

### 3.3 `.github/CONTRIBUTING.md`

A thorough guide for first-time and returning contributors.

Required sections:
- **Welcome & Thank You** — warm opening, link to Code of Conduct
- **Ways to Contribute** — bug reports, feature requests, docs, code, design, triage
- **Reporting Bugs** — what to include (steps, expected vs actual, environment),
  link to issue template
- **Suggesting Features** — when to open an issue vs a discussion, what to include
- **Development Setup**
  - Fork & clone the repo
  - Install dependencies (exact commands for the project's stack)
  - Environment variables setup
  - Running the project locally
  - Running the test suite
- **Making Changes**
  - Branch naming convention: `type/short-description`
    (e.g. `feat/user-auth`, `fix/login-crash`, `docs/api-reference`)
  - Commit message convention: **Conventional Commits**
    (`feat:`, `fix:`, `docs:`, `chore:`, `refactor:`, `test:`, `style:`, `perf:`, `ci:`)
  - Linting and formatting (commands to run before committing)
  - Keeping your fork in sync
- **Submitting a Pull Request**
  - PR checklist (tests pass, lint passes, docs updated, changelog entry)
  - What to expect in review (timeline, feedback style)
  - How to address review comments
- **Release Process** *(brief — how maintainers cut releases)*
- **Getting Help** — where to ask questions

---

### 3.4 `LICENSE`

Output the **complete, unmodified legal text** of the chosen license.

- Fill in the correct copyright year and project owner name
- Do not add Markdown formatting, headers, or commentary
- The output must be plain text, immediately usable as a `LICENSE` file

Supported licenses (generate the full text for whichever is specified):
MIT · Apache 2.0 · GPL-3.0 · AGPL-3.0 · LGPL-2.1 · MPL-2.0 ·
BSD-2-Clause · BSD-3-Clause · ISC · CC0-1.0 · Unlicense

---

### 3.5 `.github/SECURITY.md`

A clear, professional security policy.

Required sections:
- **Supported Versions** — table listing which versions receive security patches
  (use ✅ / ❌ indicators)
- **Reporting a Vulnerability**
  - Do NOT open a public GitHub issue
  - Contact method (email, GitHub private vulnerability reporting, or HackerOne)
  - What to include in the report: description, reproduction steps, impact assessment,
    proof-of-concept code or screenshots
- **Response Timeline**
  - Acknowledgement: within 48 hours
  - Initial assessment: within 7 days
  - Patch or mitigation: within 90 days of confirmation
  - Public disclosure: coordinated after patch release
- **Security Advisories** — how/where they are published (GitHub Security Advisories)
- **Out of Scope** — list of things that are NOT considered vulnerabilities
  (e.g. social engineering, DoS on free-tier infrastructure, issues in EOL versions)
- **Bug Bounty** — state clearly if there is or isn't one
- **Security Best Practices for Contributors** — dependency pinning, no secrets
  in code, how to handle sensitive data in PRs

---

### 3.6 `.github/ISSUE_TEMPLATE/bug_report.md`

A GitHub issue template using **YAML front matter + Markdown body**.

Front matter block:
```yaml
---
name: Bug report
about: Report a bug to help us improve
title: '[BUG] '
labels: bug, needs-triage
assignees: ''
---
```

Body sections:
- **Describe the bug** — clear and concise description
- **Steps to reproduce** — numbered list
- **Expected behavior** — what should happen
- **Actual behavior** — what actually happens
- **Screenshots / logs** — optional, paste or attach
- **Environment** — checkboxes + text fields for:
  - OS (Windows / macOS / Linux / Other)
  - Project version
  - Runtime version (Node, Python, etc.)
  - Browser (if applicable)
- **Additional context** — anything else relevant

Use `<!-- HTML comments -->` as placeholder instructions inside each section.

---

### 3.7 `.github/ISSUE_TEMPLATE/feature_request.md`

Front matter:
```yaml
---
name: Feature request
about: Suggest an idea or improvement
title: '[FEAT] '
labels: enhancement
assignees: ''
---
```

Body sections:
- **Problem / Motivation** — what problem does this solve? who is affected?
- **Proposed Solution** — describe the feature in detail
- **Alternatives Considered** — other approaches you thought about
- **Acceptance Criteria** — checkbox list of what "done" looks like
- **Additional Context** — mockups, links, examples

---

### 3.8 `.github/PULL_REQUEST_TEMPLATE.md`

A structured PR template that enforces quality without being bureaucratic.

Sections:
- **Description** — what changed, why, and how
- **Type of change** — checkboxes:
  - [ ] Bug fix (non-breaking)
  - [ ] New feature (non-breaking)
  - [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
  - [ ] Documentation update
  - [ ] Refactor / code quality
  - [ ] Test coverage
  - [ ] CI/CD / infrastructure
- **How Has This Been Tested?** — checkboxes for:
  - [ ] Unit tests
  - [ ] Integration tests
  - [ ] End-to-end tests
  - [ ] Manual testing
  - Steps to reproduce the test scenario
- **Checklist** — hard gates before requesting review:
  - [ ] I have performed a self-review of my code
  - [ ] I have added tests that prove my fix/feature works
  - [ ] All new and existing tests pass
  - [ ] I have updated the documentation accordingly
  - [ ] My changes generate no new warnings or linting errors
  - [ ] I have added an entry to CHANGELOG.md (if applicable)
- **Screenshots** — before/after if this is a UI change
- **Related Issues** — `Closes #` / `Fixes #` / `Related to #`

---

## 🎨 4. GLOBAL STYLE & QUALITY RULES

These apply to **every file generated**:

### Tone
- Professional but human and approachable
- Clear, concise, action-oriented
- No filler phrases ("It's worth noting that...", "As you can see...")
- Define technical jargon on first use if the audience is mixed

### Markdown quality
- All code blocks annotated with language (` ```bash `, ` ```yaml `, etc.)
- Relative links for internal cross-references (`CONTRIBUTING.md`, `LICENSE`)
- Tables aligned and readable in raw form
- No trailing whitespace or unnecessary blank lines

### No placeholder residue
- Zero `TODO`, `FIXME`, `YOUR_ORG`, `your-email@example.com` left in output
- Every field filled with real values derived from the project description
- If a piece of information was not provided, make a reasonable, professional inference

### Accuracy
- Installation commands must match the stated tech stack
- Version references must be consistent across all files
- Badge URLs must use the correct package registry for the stack

---

## ✅ 5. FINAL QUALITY CHECKLIST

Before outputting, verify each file:

- [ ] First paragraph immediately communicates what the project is and why it matters
- [ ] Installation steps are accurate, complete, and in the right order
- [ ] Quick Start example is copy-paste runnable with no hidden dependencies
- [ ] All cross-file references are consistent (same org name, same email, same license)
- [ ] Code blocks all have language annotations
- [ ] Issue templates have correct YAML front matter
- [ ] LICENSE contains the full legal text, not a summary
- [ ] SECURITY.md has a concrete, non-generic contact method
- [ ] No placeholder text anywhere
- [ ] Spelling and grammar are correct throughout
- [ ] Files render cleanly on GitHub (no broken tables, no raw HTML artifacts)

---

## 📤 6. FILE CREATION — WRITE TO DISK

Do **not** print file contents to the chat. Instead, **create each file directly
on disk** using your file creation tool. Follow this exact sequence:

### Step 1 — Create required directories first

Run these shell commands before writing any files:

```bash
mkdir -p .github/ISSUE_TEMPLATE
```

### Step 2 — Create each file using your file creation tool

Create the files in this order, one at a time:

| # | Tool call | Path |
|---|-----------|------|
| 1 | create_file | `README.md` |
| 2 | create_file | `.github/CODE_OF_CONDUCT.md` |
| 3 | create_file | `.github/CONTRIBUTING.md` |
| 4 | create_file | `LICENSE` |
| 5 | create_file | `.github/SECURITY.md` |
| 6 | create_file | `.github/ISSUE_TEMPLATE/bug_report.md` |
| 7 | create_file | `.github/ISSUE_TEMPLATE/feature_request.md` |
| 8 | create_file | `.github/PULL_REQUEST_TEMPLATE.md` |

**Rules for file creation:**
- Write the full, complete content in a single tool call per file — no truncation
- Use the exact paths shown above, relative to the project root
- Do not print file contents to chat before or after creating them
- If a file already exists at that path, overwrite it without asking
- Confirm each file creation with a single ✅ status line in chat:
  `✅ Created README.md (N lines)`

### Step 3 — Print a summary table after all files are created

Once all 8 files are written, output only this summary in chat:

```
## ✅ GitHub community files created

| File | Path | Lines |
|------|------|-------|
| README | README.md | N |
| Code of Conduct | .github/CODE_OF_CONDUCT.md | N |
| Contributing | .github/CONTRIBUTING.md | N |
| License | LICENSE | N |
| Security Policy | .github/SECURITY.md | N |
| Bug Report Template | .github/ISSUE_TEMPLATE/bug_report.md | N |
| Feature Request Template | .github/ISSUE_TEMPLATE/feature_request.md | N |
| PR Template | .github/PULL_REQUEST_TEMPLATE.md | N |

All files are production-ready. No placeholder cleanup required.
```

Do not output anything else.

---

## 🚀 7. ACTIVATION

Use this prompt by appending your project details in the following format:

```
## PROJECT DETAILS

- **Name**: 
- **Description**: 
- **Tech stack**: 
- **Package manager / install method**: 
- **Target audience**: 
- **Key features**: 
- **GitHub org / username**: 
- **License**: 
- **Security contact**: 
- **Project maturity**: 
- **Live demo / docs URL** (if any): 
- **Additional context**: 
```

The more detail you provide, the more tailored and production-ready every file will be.
