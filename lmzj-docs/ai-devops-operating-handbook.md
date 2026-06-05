# AI DevOps 运维手册

lmzj-ai-shifu 二开项目日常交付与生产运维执行手册。配套 skill 为 `ai-issue-to-production`。

## 日常交付（operate）

```text
1. 创建或复用 Issue（#）。
2. git fetch origin && 从 dev 创建工作分支。
3. 实现，保持范围小，优先复用既有模式。
4. 本地验证：先跑最小相关检查，再按风险扩大。
5. 推送分支，开 PR 到 dev，PR body 用 Refs #<issue> 并填全部小节。
6. 等待 lmzj-pr-check 通过，交人工审核。
7. 人工合并后确认 merge commit 完整 SHA。
8. 观察 lmzj-build-images 结果，记录完整 SHA 镜像 tag。
9. 部署前审查（见下）。
10. 人类明确确认后触发 lmzj-deploy-production。
11. 验证生产、报告回滚就绪。
12. 人类明确指令后关闭 Issue，附证据。
13. 清理 AI 短期工作分支。
```

## 部署前审查（image_built ≠ 可部署）

镜像构建成功不代表可部署。触发部署前必须确认：

### Artifact / 镜像

- 完整 SHA tag 与 digest。
- 镜像压缩 / 解压体积。
- 生产机磁盘余量是否够 pull、解压、启动并保留回滚空间。
- 是否误带生产不需要的 heavy optional dependencies（`all` / `full` / `dev` / `gpu` / `cuda` profile）。

### 生产 manifest

- `docker-compose.prod.yml` 使用不可变完整 SHA 镜像，无 `build:`、无 `latest`、无短 SHA。
- secrets、env、volumes、ports、healthcheck、restart policy 适合生产。
- 部署路径是生产路径，不会覆盖错误目录。
- 服务器实际使用的是审查过的 manifest 版本。

审查失败或 unresolved 时，**不得**请求生产部署确认。

## 生产部署

- 仅手动触发 `lmzj-deploy-production`，输入完整 40 位 commit SHA。
- workflow 校验并拒绝 `latest` 与短 SHA。
- `production` environment 的 required reviewers 提供人工审批关口。
- 服务器执行 `scripts/deploy-images.sh`：登录 registry → `docker pull` → `docker compose -f docker-compose.prod.yml up -d --no-build`。
- 服务器**只拉取**，绝不 `docker compose build`。

### 服务器准备

`PROD_DEPLOY_PATH` 目录需包含：

```text
docker-compose.prod.yml   # 参数化 pull-only compose（样例见 docker-compose.prod.sample.yml）
.env                      # 生产环境变量
scripts/deploy-images.sh  # 部署脚本（随仓库或单独同步）
```

## 验证

部署后验证并记录：

- health endpoint 成功。
- public URL 状态正确。
- 关键业务流程正常。
- 实际 deployed 镜像 tag。

长耗时 workflow 中断或会话恢复后，必须重新查询 run conclusion、job logs 与 health check 证据；无证据只能标记 unresolved，不得报告“部署成功”。

## 回滚

- 重新触发 `lmzj-deploy-production`，输入**上一版完整 SHA**。
- 回滚镜像来源是 registry 中的不可变完整 SHA 镜像，不依赖服务器本地历史镜像。
- 若发布含破坏性数据库迁移，按 PR 迁移计划恢复预部署数据库备份。

## 镜像清理（项目级收敛）

- 只清理本项目（label `ai-shifu.project=lmzj-ai-shifu`）的旧镜像。
- **禁止** `docker system prune -a --volumes`，禁止清理 volume 或其他项目镜像。

## Issue 关闭

- PR **不**自动关闭 Issue（用 `Refs`，不用 `Closes/Fixes/Resolves`）。
- 生产部署、验证、回滚准备证据齐全后，AI 可按人类明确指令关闭 Issue，并在关闭评论记录：Issue、PR、merge SHA、build run、deploy run、验证结果、rollback tag。

## AI 短期分支清理

- 仅在 PR 已合并、`dev` 已同步、工作区干净后执行。
- 本地分支清理：已合并的本地分支用 `git branch -d <branch>` 安全删除。
- 远端 PR 分支清理：默认 `git push origin --delete <branch>`；GitHub 已自动删除则记录 already gone。
- 不删除 `main`、`dev`、`release/*`、`hotfix/*`、`upstream/*`、未合并分支、仍有 open PR 的分支、归属不清分支。
