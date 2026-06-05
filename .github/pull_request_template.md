Refs #<issue>

<!--
公司 AI Issue-to-Production 交付契约：
- 使用 `Refs #<issue>`，禁止 Closes/Fixes/Resolves 自动关闭关键词。
- 生产相关 PR 必须填写以下全部小节，lmzj-pr-check 会校验。
-->

## 摘要

- <改了什么>
- <为什么改>

## 变更范围

- <区域 1>
- <区域 2>

## 验证

- `<command>` -> passed
- `<command>` -> passed

## 部署影响

- Change scope: <docs-only | process-only | release-governance | runtime | unknown | mixed>
- 是否需要重建镜像: yes/no
- 是否新增 secrets 或 variables: yes/no
- 是否需要数据库迁移: yes/no
- 是否现在需要生产部署: yes/no

## 回滚

- 部署上一版不可变完整 SHA 镜像。
