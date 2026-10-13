# 示例详细设计：登录服务

## 架构与边界

Auth Service 对 API Gateway 暴露 `/login` 与 `/logout`。信任边界在网关 TLS 终结之后。

## 数据设计

- 表 `sessions`：session_id, user_id, expires_at
- 状态：active → expired | revoked

## 接口或契约

- POST /login — 对应 REQ-1
- POST /logout — 对应 REQ-2

## 异常与可靠性

- 登录接口幂等键：Idempotency-Key 可选
- 超时 3s，不自动重试写路径

## 权限

单角色终端用户；管理端不在本期。
