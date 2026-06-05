# lmzj-docs

公司二开（lmzj-ai-shifu）专属流程与运维文档目录。

本目录与上游 `docs/` 隔离，**不写入上游 `docs/`**，以降低后续上游同步（rebase / merge）冲突。所有公司 AI Issue-to-Production 流程、发布、部署、回滚文档放在这里。

## 目录内容

- [`github-ai-build-release-flow.md`](github-ai-build-release-flow.md)：从 Issue 到生产的构建发布流程与 GitHub 治理配置。
- [`ai-devops-operating-handbook.md`](ai-devops-operating-handbook.md)：日常交付、部署前审查、生产部署、验证、回滚、分支清理运维手册。
- [`docker-compose.prod.sample.yml`](docker-compose.prod.sample.yml)：生产服务器使用的参数化、pull-only compose 样例。

## 分支与发布模型

| 维度 | 取值 |
|---|---|
| Project type | secondary_development |
| Repository visibility | public |
| Governance level | L4（GitHub 平台强制门禁） |
| Release source / PR target | `dev` |
| 生产镜像来源 | `dev`（仅完整 40 位 commit SHA） |
| 上游基线 | `main`（保留为 `ai-shifu/ai-shifu` 同步基线） |

上游同步、功能开发、镜像构建、生产部署是四个独立关口，不得合并。
