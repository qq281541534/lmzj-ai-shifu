# GitHub AI 构建发布流程

本文是 lmzj-ai-shifu 二开项目从需求到生产的可审计交付链路执行源。配套 skill 为 `ai-issue-to-production`。

## 交付链路

```text
Issue (#)
  -> 从 dev 创建 feature/* | fix/* | docs/* | chore/* 分支
  -> 实现并本地验证
  -> PR 到 dev（Refs #<issue>）
  -> lmzj-pr-check 通过
  -> 人工审核并合并
  -> lmzj-build-images 从 dev 构建不可变完整 SHA 镜像
  -> 部署前 artifact 与生产 manifest 审查
  -> 人类明确确认生产部署
  -> lmzj-deploy-production 手动触发，服务器只拉取镜像
  -> 生产验证与回滚准备
  -> 人类明确指令后关闭 Issue
  -> 清理 AI 短期工作分支
```

## 分支模型

| 分支 | 角色 | 规则 |
|---|---|---|
| `main` | 上游 `ai-shifu/ai-shifu` 同步基线 | 不作公司生产发布源；上游同步单独走关口 |
| `dev` | 公司集成与发布源 | feature 分支 base、PR target、生产镜像来源 |
| `feature/* fix/* docs/* chore/*` | AI 短期工作分支 | 从 `dev` 创建，合并后清理 |

## 工作流职责

| Workflow | 触发 | 职责 |
|---|---|---|
| `lmzj-pr-check.yml` | `pull_request` 到 `dev` | change scope 检测 → process-check（PR body lint）→ 条件 runtime-check → 稳定 final check `lmzj-pr-check` |
| `lmzj-build-images.yml` | `push` 到 `dev` / 手动 | 校验 commit 来源于已合并 PR；non-runtime 跳过；构建仅完整 SHA 镜像 |
| `lmzj-deploy-production.yml` | 手动 `workflow_dispatch` | 校验完整 40 位 SHA、拒绝 latest/短 SHA；`production` environment；SSH pull-only 部署 |

上游既有的 `build-latest.yml`、`build-on-release.yml`、`prepare-release.yml` 属上游机制，**不是公司生产镜像来源**，保留不动。

## 变更分类与镜像构建

| Change scope | 示例 | 镜像行为 |
|---|---|---|
| `docs-only` | `*.md`、`docs/**`、`lmzj-docs/**` | 不 login / build / push |
| `process-only` | `AGENTS.md`、`CLAUDE.md`、`.claude/**`、`.cursor/**`、PR 模板、process/audit 脚本 | 不 login / build / push |
| `release-governance` | `lmzj-*` workflow、`deploy-images.sh` | 单独变化不构建应用镜像，需严格 review |
| `runtime` | `src/**`、Dockerfile、`docker/**`、依赖锁文件、迁移 | 构建受影响镜像 |
| `unknown` | 分类器无法识别 | 保守构建全部 |

分类逻辑由 `scripts/classify_change_scope.py` 统一实现，PR check 与 build images 共用。

## 镜像与 registry

- 公司镜像名默认：`lmzj-ai-shifu-api`、`lmzj-ai-shifu-cook-web`。
- registry / namespace 由 GitHub Variables 提供，凭据由 Secrets 提供（见下）。
- 生产镜像 tag **只用完整 40 位 commit SHA**，不使用 `latest` 或短 SHA。

## 需要人类在 GitHub 配置的 L4 平台门禁

本仓库为 public，治理级别 L4，以下必须由人类在 GitHub UI / 设置中配置，agent 无法替代：

### Branch protection / ruleset（`dev`）

- Require a pull request before merging。
- Require approvals ≥ 1（human）。
- Dismiss stale approvals when new commits are pushed。
- Required status checks（required status checks to pass）：`lmzj-pr-check`。
- 限制直接 push `dev`。

### Environment：`production`

- Required reviewers（部署审批人）。
- Prevent self-review。
- Deployment branches 仅允许 `dev`。
- 生产 secrets 只放入 `production` environment。

### Repository Secrets / Variables

| 类型 | 名称 | 用途 |
|---|---|---|
| Variable | `LMZJ_REGISTRY` | 镜像 registry host |
| Variable | `LMZJ_IMAGE_NAMESPACE` | 镜像 namespace |
| Secret | `LMZJ_REGISTRY_USERNAME` | registry 用户名 |
| Secret | `LMZJ_REGISTRY_PASSWORD` | registry 密码/token |
| Secret | `PROD_SSH_HOST` | 生产服务器地址 |
| Secret | `PROD_SSH_PORT` | SSH 端口 |
| Secret | `PROD_SSH_USER` | SSH 用户 |
| Secret | `PROD_SSH_KEY` | SSH 私钥 |
| Secret | `PROD_DEPLOY_PATH` | 服务器部署目录（含 `docker-compose.prod.yml` 与 `scripts/deploy-images.sh`） |

凭据缺失时 `lmzj-build-images` 自动降级为 build-only（不 push），便于在配置完成前先验证构建。

## 硬规则

1. 不直接 push `dev`，改动走 PR。
2. PR merge ≠ 生产部署。
3. 没有人类明确确认不触发生产部署。
4. 生产服务器只拉取镜像，绝不构建。
5. 生产只用完整 40 位 commit SHA。
6. non-runtime 变更不构建或 push 生产镜像。
7. PR 用 `Refs #<issue>`，不用自动关闭关键词。
8. Issue 不由 PR 自动关闭；验证与回滚准备齐全后按人类指令关闭。
