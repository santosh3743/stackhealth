<!--
Thanks for opening a PR! A few quick things to help review go fast:

- One concern per PR. Tiny PRs are easier to merge than big ones.
- Make sure CI is green before requesting review.
- Add screenshots for any visible UI change.
- See CONTRIBUTING.md for code style, commit format, and the formula
  change process if relevant.
-->

## Summary

<!-- 1–3 sentences on what this PR does and why. -->

## Related issue

<!-- e.g. Closes #123, Fixes #456, Relates to #789 -->

## Type of change

<!-- Check what applies. Multiple is fine. -->

- [ ] 🐛 Bug fix (non-breaking change that fixes an issue)
- [ ] ✨ New feature (non-breaking change that adds capability)
- [ ] 🚨 Breaking change (changes API shape or persisted format)
- [ ] 📖 Documentation only
- [ ] 🧪 Tests only
- [ ] ♻️ Refactor / internal cleanup
- [ ] 🔬 **Scoring formula change** — please see "Formula changes" below

## How I tested this

<!--
- New / updated tests (link to file:line)
- Manual steps you ran
- For UI: screenshots before/after, mobile + desktop
- For API: example request/response or curl command
-->

## Formula changes

<!-- Only fill this out if you ticked the "scoring formula change" box. -->

- [ ] Updated `apps/api/stackhealth/formula/v1.py`
- [ ] Updated `docs/03-SCORING-METHODOLOGY.md`
- [ ] Updated `packages/formula-spec/v1.0.md`
- [ ] Updated `apps/api/tests/test_formula.py` with the new examples
- [ ] Noted the change in `CHANGELOG.md` under the right version tier
- [ ] Calibration data (a few worked examples showing the score shift):

      <!-- e.g.
      pallets/click:    76 → 78  (semgrep weight up 5pp)
      fastapi/fastapi:  84 → 85
      tiangolo/typer:   69 → 71
      -->

## Checklist

- [ ] `uv run ruff check .` and `uv run ruff format --check .` pass
- [ ] `uv run pytest -q` passes
- [ ] `pnpm typecheck` and `pnpm lint` and `pnpm build` pass
- [ ] Commit messages follow Conventional Commits
- [ ] I've read the
  [Contributing guide](https://github.com/santosh3743/stackhealth/blob/main/CONTRIBUTING.md)
