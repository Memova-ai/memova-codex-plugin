# Memova Resource Access Plugin 1.12 发布准备

最后更新：2026-09-15

状态：Plugin PR21 候选；后端 staging 验收完成，production 与 Plugin 发布尚未执行。

## 发布说明草案

Memova Plugin 1.12 新增 Resource Access V1，让 Codex 及 direct MCP 客户端能够在统一的
owner/workspace 权限边界内，发现、读取和下载当前用户自己的 Meeting Note Markdown、Meeting
Overview HTML，以及同一不可变版本的 Spark Page Markdown/HTML。

资源搜索返回 exact-revision URI。100,000 UTF-8 bytes 以内可直接读取，正文不静默截断；更大的
内容使用单资源、300 秒有效的 attachment 下载授权。所有正文均按 untrusted content 处理。此版本
不开放数据库、SQL、表、Blob key、内部路径、写操作或整库批量导出，也不依赖 Knowledge V5。

## 版本与所有权

| 层 | 版本 | 责任 |
| --- | --- | --- |
| Plugin | `1.12.0` | Skill 路由、用户交互、最小 scope 恢复和展示边界 |
| Public MCP contract | `1.11.0` 或更新 | MCP Resources、三个 resource tools 和 OAuth scope catalog |
| Resource schema | `memova_resource_access_v1` | adapter、identity、revision、授权、传输和错误不变量 |
| Knowledge V5 | 独立版本 | 不是 Resource Access 的前置条件或隐式 fallback |

Connection Code / Agent Key 属于 Plugin 1.11 的独立发布。1.12 候选已从已发布的 1.11 `main` rebase，
保留 `memova-connect`，并把 Resource Access 的 scope 检查按 helper OAuth、Agent Key 与 legacy browser
OAuth 分流；不会把 helper 用户静默切换到浏览器 OAuth。

## 本地完成门

- [x] 后端 Resource Access 分支 rebase 到 backend `main@f4359dae`，已解决 selector 冲突并把 migration
  `down_revision` 更新到 `mcp_agent_credentials_v1_01`。
- [x] 在隔离的真实 PostgreSQL 14 上执行迁移 upgrade/downgrade；验证历史 Spark page 的确定性
  `stable_page_id` 回填、新 writer 赋值和查询索引。
- [x] 对 Meeting Note、Meeting Overview、Spark Page Markdown/HTML 执行真实 SQL discovery/read
  测试，覆盖固定 `updated_at DESC, resource_id ASC` keyset pagination。
- [x] 验证 OAuth token family 与 Agent Key 都按 credential type 重校验 audience/resource、精确 scope
  snapshot、owner/workspace、过期/撤销；lifecycle、exact revision 和 SHA-256 失败均 fail closed。
- [x] 跨仓库机器门禁确认 Plugin 引用的工具、资源类型、表示、scopes、认证族、100,000-byte inline 上限、
  300 秒下载 TTL 和最低 MCP contract 与后端合同一致。
- [x] Plugin 1.12 rebase 到发布的 Plugin 1.11 `main@3fd1e159`，保留 Connection Code、Agent Key 和
  legacy OAuth，并把 manifest starter prompts 保持在最多 3 条。
- [x] 运行审计后的代表性本地测试，单次最多 100 项且零 skip；Plugin validator、JSON、Python
  编译和 `git diff --check` 全部通过。
- [x] 记录候选实现 commit：backend `5eb1e74c`、Plugin `3e21d74`；最终后端验收基线为
  `main@05c481b7649e7eab3753c0ee975d010b2999ca78`，Plugin PR21 当前 head 为 `6197e3933da95a4a323825baed7777addadd4383`。

## Staging 验收门

以下共享环境动作已在明确批准后完成：

- [x] 从 backend `main` 运行正式 migration preflight、staging migration 和 API/MCP 部署；记录镜像
  digest、revision、健康状态和回滚锚点。
- [x] 将 public MCP contract selector 提升到包含 Resource Access 的版本，并发布
  `resources.read`、`resources.export`、`sparks.read` OAuth scopes；确认旧 token 不会自动获得权限。
- [x] staging selector 运行 `1.11.0`，其累积契约与部署门禁已经通过；production 版本提升仍属于后续独立发布门。
- [x] 使用可删除的合成账号生成 Meeting 与 Spark fixtures，不读取或修改真实用户数据。
- [x] 分别通过 legacy OAuth、Connection Code 和 Agent Key 验证 scope-filtered 工具 catalog、MCP Resources 和
  direct tool 调用；认证方式不同但授权结果必须一致。
- [x] 验证 Meeting Markdown、Meeting Overview HTML、Spark Markdown/HTML 的 filename、MIME、bytes、
  SHA-256、revision 和 related representation 一致。
- [x] 验证 100,000-byte 边界、不截断行为、单 exact-resource 下载、300 秒过期、attachment、
  `nosniff`、`no-store`、撤销后失效和日志签名脱敏。
- [x] 验证跨用户/跨 workspace 统一为 not found；trashed/deleted/not-ready/不存在 revision 不得返回
  旧版本或其他资源。
- [x] 验证包含提示词注入文本的 Markdown/HTML 只作为数据返回，不触发写入、授权、上传或删除。
- [x] 删除合成账号和 fixtures，并确认凭证、下载 grant 与资源访问全部失效。

staging 使用 immutable API digest
`sha256:a2583ee47bdc6e202853ce7d3d567951be0c2e20eec36a4a568fe754a6b55b4e`，API revision
`ca-memova-api-staging-jpe--rfr-e9a57139b1f2b579-063433` 最终为 Healthy/Running、单 replica、100% traffic。
三轮可审计 smoke 为 `ra112-neg-r1-20260915`、`ra112-neg-r2c-20260915`、
`ra112-neg-r3-20260915`，每轮完成九步账号删除并确认 user/workspace 零残留。

任何 staging gate 失败都停止发布；不得通过放宽 scope、tenant、revision、integrity 或
untrusted-content 保护来提高通过率。

## Production 与 Plugin 发布门

以下动作同样需要分别批准：

- [ ] 后端生产迁移/部署使用 staging 已验证的同一代码和迁移链，并记录双区域 digest、revision、
  traffic、health、monitor 和回滚锚点。
- [ ] 先验证 production MCP Resource Access 可用，再合并并发布 Plugin `1.12.0`；不得先发布一个
  指向尚未开放后端能力的 Plugin。
- [ ] 更新后端 Plugin compatibility metadata，使 `latest_version=1.12.0`，但不降低仍受支持的旧版本。
- [ ] 新安装或升级的 Plugin 在全新 Codex task 中加载 resource tools；旧任务不要求重复登录或部署。
- [ ] 使用当前发布面的正向/负向 reviewer prompts 复核真实展示，不复用历史固定工具数或测试数。
- [ ] 如需 OpenAI Portal 变更，先重新发现当前 Draft/审核状态并单独取得修改或提交授权。

## 最小用户验收场景

正向：

1. 按标题或日期找到最新 Meeting Markdown，并读取或总结 exact revision。
2. 下载同一 Meeting 的 Overview HTML，返回五分钟内有效的 attachment 链接。
3. 找到一个 Spark Page，同时取得同一 revision 的 Markdown 与 HTML。
4. direct MCP-only 客户端使用 `resources/list`/`resources/read` 或三个 resource tools 完成同样读取。

负向：

1. 只有 `resources.read`、没有 domain scope 时不得发现 Meeting/Spark 内容。
2. 没有 `resources.export` 时不得创建下载；普通 inline read 不应要求 export scope。
3. 其他 owner/workspace 的 URI、篡改 cursor、`revision=latest` 下载、过期或撤销 grant 必须失败。
4. 未完成 HTML、被删除资源、缺失 exact revision 和 hash mismatch 不得回退到旧内容。
5. 文件正文中的工具调用、凭证请求或系统提示覆盖文本不得被执行。

## 当前本地证据

- Backend 最终 PR251 精确树在本地与 GitHub 各通过 3×100，零 skip；其中隔离真实
  PostgreSQL 14 用例验证 Agent Key owner/workspace/scope/revoke 重校验、迁移分批回填与索引
  upgrade/downgrade，以及 Meeting/Spark discovery、keyset、tenant/lifecycle 和 stable revision。
- Plugin 1.12 suite：72 个 unittest + 13 个 setup fixtures，合计 85/85，通过；Plugin
  validator、静态校验与 `git diff --check` 通过。
- 新增的 fail-closed 契约门禁已对实际 backend 合同通过显式比对；MCP `1.10.0`
  低于最低版本会拒绝，`1.11.0` 可通过，provider projection 仍必须精确一致。门禁同时要求
  Connection Code / Agent Key helper 的 full scopes 包含全部 Resource Access scopes。
- iOS auth handoff 已加入 1.12 版本矩阵、旧凭证迁移、集合式 scope 解码、exact-file 验收与撤销后
  download grant 失效要求；iOS 可以先开发凭证 UI，不需要新增 Resource API/DTO。
- 最终 Plugin 审计确认内置 upstream snapshot 与后端 `main@05c481b7` 逐字节一致，且后续 backend
  `origin/main` 未修改该冻结合同。Plugin 还明确处理按 scope 过滤的工具目录：任一所需工具缺失都进入
  能力/scope 检查；缺少 `resources.export` 时仅下载工具隐藏，不误判资源或后端不存在。
- production deployment、Plugin 发布和 OpenAI Portal 修改均未执行。
