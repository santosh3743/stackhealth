# 03 — Scoring Methodology

> **This is the most important document in the project.** It is the open formula. Everything StackHealth promises depends on this file being clear, defensible, and versioned.

## Formula version: **v1.0**

Each scan stores the formula version it was computed under. Old scans keep their original score forever. New formula versions (v1.1, v2.0) are introduced via a public RFC process documented in `13-LAUNCH-AND-GROWTH.md`.

---

## Overall Score

```
overall = round(
    0.30 * security_score +
    0.25 * quality_score +
    0.25 * hygiene_score +
    0.20 * community_score
)
```

All four sub-scores are on a 0–100 scale. Overall is also 0–100.

### Letter grade mapping

| Score | Grade |
|-------|-------|
| 95–100 | A+ |
| 90–94 | A |
| 85–89 | A- |
| 80–84 | B+ |
| 75–79 | B |
| 70–74 | B- |
| 65–69 | C+ |
| 60–64 | C |
| 55–59 | C- |
| 50–54 | D |
| 0–49 | F |

The thresholds are picked to give a normal distribution of "good" OSS projects in the B+/A- range, with A and A+ reserved for genuinely excellent repos. Calibration will be revisited at v1.1 once we have data from ~1000 scans.

---

## 1. Security score (30% of overall)

```
security_score = round(
    0.40 * scorecard_normalized +
    0.40 * semgrep_score +
    0.20 * dependency_score
)
```

### 1a. Scorecard normalized (40% of security, 12% of overall)

OpenSSF Scorecard returns a 0–10 aggregate score across ~18 checks (Branch Protection, Code Review, CI Tests, Dangerous Workflow, Dependency Update Tool, Pinned Dependencies, SAST, Vulnerabilities, etc.). We fetch this from `https://api.scorecard.dev/projects/github.com/{owner}/{name}` when available, else run Scorecard locally.

```
scorecard_normalized = scorecard.aggregate_score * 10   # 0-10 → 0-100
```

If Scorecard is unavailable for the repo (rare — Scorecard runs against most public repos), we run it ourselves and cache the result for 7 days.

### 1b. Semgrep score (40% of security, 12% of overall)

Run Semgrep with the `p/security-audit` ruleset (OSS) against the cloned repo. Findings have severity: ERROR, WARNING, INFO.

```
penalty = 8 * error_count + 3 * warning_count + 1 * info_count
semgrep_score = max(0, 100 - penalty / (loc / 1000 + 1))
```

The `loc / 1000 + 1` normaliser scales by codebase size — a 100-finding repo at 1M LoC is healthier than a 100-finding repo at 1k LoC.

### 1c. Dependency score (20% of security, 6% of overall)

Run `trivy fs --scanners vuln` against the repo to get dependency CVEs.

```
penalty = 20 * critical + 8 * high + 3 * medium + 1 * low
dependency_score = max(0, 100 - penalty)
```

Why simple subtraction here and not LoC-normalized? Because dependency vulnerabilities are absolute risks regardless of project size — one critical CVE in a 100-line project is still a critical CVE.

---

## 2. Quality score (25% of overall)

```
quality_score = round(
    0.30 * complexity_score +
    0.25 * lint_density_score +
    0.20 * duplication_score +
    0.15 * test_signal_score +
    0.10 * file_size_score
)
```

### 2a. Complexity score (30% of quality, 7.5% of overall)

Run `radon cc` (Python), `eslint --rule complexity` (JS/TS), `lizard` (multi-lang fallback). Aggregate cyclomatic complexity per function.

```
avg_complexity = mean(complexity per function)
complexity_score = max(0, 100 - (avg_complexity - 5) * 8)
# Avg complexity ≤ 5 → 100. Each point above 5 costs 8.
```

### 2b. Lint density score (25% of quality, 6.25% of overall)

Run language-appropriate linters: `ruff` (Python), `eslint` (JS/TS), `golangci-lint` (Go), `clippy` (Rust). Sum lint issues, normalise by LoC.

```
issues_per_kloc = total_lint_issues / (loc / 1000)
lint_density_score = max(0, 100 - issues_per_kloc * 2)
```

### 2c. Duplication score (20% of quality, 5% of overall)

Run `jscpd` (multi-language copy-paste detector).

```
duplication_score = max(0, 100 - duplication_percent * 5)
# 0% dup → 100. 20% dup → 0.
```

### 2d. Test signal score (15% of quality, 3.75% of overall)

We do not run tests (too expensive, too varied). We look for *test presence* signals:

- `tests/`, `test/`, `__tests__/`, `*_test.go`, `*.test.ts` etc. directories or files: +40
- `pytest`, `jest`, `mocha`, `go test`, `cargo test` in CI config: +30
- Coverage badge in README or coverage report in repo: +20
- A `codecov.yml` / `coverage.xml` artifact: +10

Sum, capped at 100.

### 2e. File size score (10% of quality, 2.5% of overall)

Penalize repos with files that are too long. From `cloc` output:

```
mega_files = count(files with > 1000 LoC)
file_size_score = max(0, 100 - mega_files * 5)
```

---

## 3. Hygiene score (25% of overall)

Pure binary checklist. Each item is worth its listed points. Total = hygiene_score.

| Check | Points | How |
|-------|--------|-----|
| README.md exists and > 300 chars | 15 | File check + size |
| LICENSE file exists | 15 | File check |
| LICENSE is OSI-approved | 5 | Match against [OSI list](https://opensource.org/licenses), via GitHub's SPDX or local body sniffing |
| CONTRIBUTING.md exists | 8 | File check |
| CODE_OF_CONDUCT.md exists | 5 | File check |
| SECURITY.md exists | 7 | File check |
| `.github/workflows/` or `.gitlab-ci.yml` exists | 10 | CI present |
| At least one workflow runs on pull_request | 5 | YAML parse |
| Tests directory exists | 10 | Directory check at root and one level into common monorepo workspaces (apps/*, packages/*, services/*, libs/*) |
| `.gitignore` exists | 3 | File check |
| Repo has a description on GitHub | 5 | GitHub API |
| Repo has topics/tags on GitHub | 5 | GitHub API |
| Last commit within 365 days | 7 | GitHub API |

**Total: 100 points possible.**

This category is intentionally generous — most well-run repos should score 70+ here. It rewards basic discipline.

---

## 4. Community score (20% of overall)

```
community_score = round(
    0.35 * activity_score +
    0.25 * contributor_score +
    0.20 * popularity_score +
    0.20 * responsiveness_score
)
```

### 4a. Activity score (35% of community, 7% of overall)

```
days_since_last_commit = (today - last_commit_date).days
commits_last_90d        = commits in last 90 days

if days_since_last_commit > 365:
    activity_score = 0
elif days_since_last_commit > 180:
    activity_score = 30
else:
    activity_score = min(100, 40 + commits_last_90d * 2)
```

Recent activity matters more than total commits — a dormant 10k-commit repo is less healthy than a 100-commit repo with weekly activity.

### 4b. Contributor score (25% of community, 5% of overall)

```
contributors = unique authors in last 365 days
contributor_score = min(100, log2(contributors + 1) * 25)
# 1 → 25, 3 → 50, 7 → 75, 15 → 100
```

Log scale so a 50-contributor repo doesn't trivially dominate a 5-contributor one.

### 4c. Popularity score (20% of community, 4% of overall)

```
popularity_score = min(100, log10(stars + 1) * 25)
# 10 stars → 25, 100 → 50, 1000 → 75, 10000 → 100
```

Popularity is included but capped at 20% of community (4% of overall) so a repo cannot get an A just by being popular.

### 4d. Responsiveness score (20% of community, 4% of overall)

GitHub API: `median_issue_response_time` for issues opened in last 90 days.

```
median_hours = median time-to-first-response in hours
if median_hours < 24:     responsiveness_score = 100
elif median_hours < 72:   responsiveness_score = 80
elif median_hours < 168:  responsiveness_score = 60   # 1 week
elif median_hours < 720:  responsiveness_score = 30   # 30 days
else:                     responsiveness_score = 0
```

Repos with zero issues in 90 days → 70 (neutral, not penalized).

---

## What we do NOT score

These are intentionally excluded from v1.0 to keep the formula defensible:

- **Code aesthetics** (no AI prose review)
- **Documentation depth** (only README presence, not quality)
- **Performance** (no runtime benchmarks)
- **Stars growth rate** (gameable)
- **Author identity** (no "trusted author" bonus)
- **Language choice** (no Go > Python prejudice)

---

## Worked example — `expressjs/express`

A hypothetical scan output (numbers illustrative):

```
Security:        82
  Scorecard:     8.5 → 85
  Semgrep:       91 (low finding density)
  Dependencies:  62 (a few medium CVEs)

Quality:         78
  Complexity:    74
  Lint density:  82
  Duplication:   88
  Test signal:   90
  File size:     75

Hygiene:         91
  All checks pass except CONTRIBUTING (-8)
  and SECURITY.md (-7), plus minor

Community:       89
  Activity:      82
  Contributors:  100 (large project)
  Popularity:    100 (>10k stars)
  Responsiveness: 70

OVERALL = 0.30*82 + 0.25*78 + 0.25*91 + 0.20*89
       = 24.6 + 19.5 + 22.75 + 17.8
       = 84.65 → 85 → A-
```

---

## Reproducibility guarantee

Every scan stores:

- `formula_version` (e.g., `"v1.0"`)
- Tool versions (`semgrep@1.x`, `trivy@0.x`, `scorecard@5.x`, `cloc@1.x`)
- Repo commit SHA scanned
- Raw outputs (JSON) in object storage with public read

Anyone can fetch the raw outputs and recompute the score using the published formula. If the score doesn't match, that is a bug we will fix.

---

## How the formula evolves

- Patch versions (v1.0 → v1.0.1): bug fixes only. Same inputs → same score.
- Minor versions (v1.0 → v1.1): threshold tweaks, new optional engines. Old scans NOT re-scored automatically; users can opt in.
- Major versions (v1 → v2): structural changes. Always preceded by a 30-day public RFC.

All formula changes are PRs against the `stackhealth/formula` GitHub repo. Anyone can propose. We merge after review and a public comment window.

---

## A note on gaming

The formula is open, which means it is gameable. We accept this trade-off because:

1. The alternative — a closed formula — is also gameable (people reverse-engineer it).
2. Most gaming techniques (adding a CONTRIBUTING.md, fixing lint issues) make the repo *actually better*. That's a win.
3. We will publish gaming patterns we detect and adjust the formula in minor versions.

We will not name-and-shame, but we reserve the right to add anti-gaming penalties (e.g., README that consists of a single auto-generated badge wall) in future versions.
