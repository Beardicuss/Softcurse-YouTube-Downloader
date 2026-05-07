# Contributing to Softcurse Media Downloader

Thank you for your interest in contributing! Every contribution helps make this
project better. Please read our [Code of Conduct](CODE_OF_CONDUCT.md) before
participating.

---

## Ways to Contribute

- 🐛 **Report bugs** — file detailed bug reports
- 💡 **Suggest features** — open a feature request issue
- 📖 **Improve docs** — fix typos, clarify instructions, add examples
- 🔧 **Submit code** — bug fixes, new features, optimizations
- 🧪 **Write tests** — improve coverage and reliability
- 🔍 **Triage issues** — reproduce bugs, ask clarifying questions

---

## Reporting Bugs

Use the [Bug Report template](ISSUE_TEMPLATE/bug_report.md) and include:

1. Steps to reproduce the issue
2. Expected behavior vs actual behavior
3. Your environment (OS, Python version, app version)
4. Screenshots or log output if applicable

---

## Suggesting Features

Use the [Feature Request template](ISSUE_TEMPLATE/feature_request.md) and include:

1. The problem or motivation
2. Your proposed solution
3. Alternatives you considered

---

## Development Setup

### 1. Fork and clone

```bash
git clone https://github.com/<your-username>/Softcurse-YouTube-Downloader.git
cd Softcurse-YouTube-Downloader
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

Optional dependencies for full functionality:

```bash
pip install mutagen pygame
```

### 3. Install ffmpeg

```bash
winget install ffmpeg
```

### 4. Run the app

```bash
python main.py
```

---

## Making Changes

### Branch naming

Use the format `type/short-description`:

- `feat/batch-queue` — new feature
- `fix/glitch-crash` — bug fix
- `docs/api-reference` — documentation
- `refactor/download-engine` — code improvement

### Commit messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add batch URL queue support
fix: resolve empty chars crash in glitch loop
docs: update installation instructions
chore: remove unused imports
refactor: extract color cache to utility
```

### Before committing

- Verify the app launches without errors: `python main.py`
- Check for unused imports and dead code
- Keep your fork in sync:

```bash
git remote add upstream https://github.com/Beardicuss/Softcurse-YouTube-Downloader.git
git fetch upstream
git rebase upstream/main
```

---

## Submitting a Pull Request

1. Push your branch to your fork
2. Open a PR against `main`
3. Fill out the PR template completely
4. Ensure your changes don't break the app

### PR checklist

- [ ] App launches and runs without errors
- [ ] No new linting warnings introduced
- [ ] Commit messages follow Conventional Commits
- [ ] Documentation updated if applicable

### What to expect

- Maintainers will review within 7 days
- Feedback will be constructive and specific
- Small PRs are reviewed faster than large ones

---

## Getting Help

- Open a [GitHub Discussion](https://github.com/Beardicuss/Softcurse-YouTube-Downloader/discussions)
- Visit [softcurse-website.pages.dev](https://softcurse-website.pages.dev/)
