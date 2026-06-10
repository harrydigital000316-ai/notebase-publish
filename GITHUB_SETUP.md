# GitHub Repository Setup for notebase-publish

## Required Secrets (Settings → Secrets and variables → Actions)

| Secret Name | Description | Example |
|-------------|-------------|---------|
| `HERMES_API_KEY` | Hermes Agent API key for cron jobs | `sk-...` |
| `NOTES_VAULT_PATH` | Path to notebase vault in CI | `/home/runner/work/notebase-publish/notebase-publish/dev_notes` |

## Required Variables (Settings → Variables)

| Variable | Description |
|----------|-------------|
| `DEPLOY_BRANCH` | GitHub Pages branch (default: `gh-pages`) |

## Branch Protection Rules (Settings → Branches)

**Main branch:**
- Require PR review before merging
- Require status checks to pass (CI workflow)
- Require branches to be up to date
- Include administrators

**gh-pages branch:**
- No protection needed (deploy workflow manages it)

## Workflow Permissions (Settings → Actions → General)

- **Workflow permissions**: Read and write permissions
- **Allow GitHub Actions to create and approve pull requests**: ✅

## GitHub Pages Setup (Settings → Pages)

- Source: Deploy from a branch
- Branch: `gh-pages` / `(root)`
- Custom domain: (optional)

## Issue Labels (auto-created via templates)

- `bug` - Something isn't working
- `enhancement` - New feature or request
- `cronjob` - Related to scheduled workflows
- `high-priority` - Blocking or time-sensitive
- `documentation` - Documentation updates
- `good first issue` - Good for newcomers

## Local Development with act

```bash
# Install act (GitHub Actions local runner)
brew install act  # or: curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash

# Run CI locally
act push

# Run cron workflow locally
act schedule -j nightly-skill-learning

# List available jobs
act -l
```

## Cron Schedule (UTC → Taipei)

| Workflow Job | UTC Cron | Taipei Time |
|--------------|----------|-------------|
| nightly-skill-learning | `0 0 * * *` | 08:00 |
| knowledge-share | `0 3 * * *` | 11:00 |
| taiwan-market-bridge | `0 6 * * *` | 14:00 |
| env-check | `30 11 * * *` | 19:30 |
| dev-cycle-12-ideation | `0 12 * * *` | 20:00 |
| dev-cycle-15-implementation | `0 15 * * *` | 23:00 |
| dev-cycle-18-review | `0 18 * * *` | 02:00 (+1) |
| global-macro | `0 20 * * *` | 04:00 (+1) |
| dev-cycle-21-deploy | `0 21 * * *` | 05:00 (+1) |
| weekly-synthesis (Sat) | `0 1 * * 6` | 09:00 (Sat) |

## Testing Cron Jobs Manually

```bash
# Trigger via gh CLI
gh workflow run cron-jobs.yml -f job=global-macro

# Or via GitHub UI: Actions → Daily Cron Jobs → Run workflow
```

## Upcoming Improvements (Issues to Create)

1. **[Bug] 20:00 Global Macro output truncated** - optimize prompt for condensed Telegram + full vault
2. **[Feature] Taipei timezone support in cron** - use `TZ=Asia/Taipei` in workflow env
3. **[Feature] Notebase vault sync** - sync `~/dev_notes` to repo for CI access
4. **[Feature] Slack/Telegram notifications** - workflow status webhooks
5. **[Enhancement] Auto-merge dependabot PRs** - add dependabot.yml
6. **[Enhancement] Release workflow** - semantic-release on tag push