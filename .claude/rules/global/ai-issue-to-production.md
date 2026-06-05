# Claude Rule: AI Issue To Production

This Claude-only rule routes all issue, PR, CI/CD, release, deployment, and
rollback work for this secondary-development fork to the company
`ai-issue-to-production` skill instead of improvising a release process.

- All issue, PR, CI/CD, release, deployment, and rollback work uses the
  `ai-issue-to-production` skill. If the current framework cannot auto-load the
  skill, read it from the company skill source
  `company-ai-skills/skills/ai-issue-to-production/`.

- This project is `secondary_development` + `public` repo, governance level
  `L4`. Release source and PR target are `dev`; `main` is the upstream
  `ai-shifu/ai-shifu` sync baseline and is not the company production source.

- Production images are built only from `dev` and tagged with the full 40-char
  commit SHA. Never deploy `latest` or a short SHA.

- Keep company release/ops docs in `lmzj-docs/`, never in upstream `docs/`.
  Read `lmzj-docs/github-ai-build-release-flow.md` and
  `lmzj-docs/ai-devops-operating-handbook.md` before release or deploy work.

- Use `Refs #<issue>` in PR bodies; never use Closes/Fixes/Resolves. PR merge
  is not production deployment; production deploy requires explicit human
  confirmation of a specific full SHA via `lmzj-deploy-production`.

- Treat upstream sync, feature development, image build, and production deploy
  as separate gates. Do not modify upstream core when an extension, adapter, or
  config change is sufficient.
