# KuGouMusicApi 后端速查

> 源码：`backend/KuGouMusicApi/`　版本：1.6.3　License：MIT

## 一句话说明

非官方酷狗音乐 Node.js API，通过伪造请求头与签名调用官方接口，约 160 个接口模块，支持 HTTP 服务与编程式调用两种模式。

## 运行

```bash
cd backend/KuGouMusicApi
npm install
npm run dev      # 开发模式（热重载）
npm start        # 生产模式
```

默认端口 3000，监听 localhost。

### 概念版模式（本项目使用）

复制 `.env.example` 为 `.env`，把 `platform=''` 改为 `platform=lite`。
注意：**标准版与概念版的 token 不通用**。

### 常用环境变量

| 变量 | 说明 | 默认值 |
| --- | --- | --- |
| `platform` | `lite` = 概念版，空 = 标准版 | 空 |
| `PORT` | 服务端口 | 3000 |
| `HOST` | 监听地址 | localhost |
| `KUGOU_API_PROXY` | HTTP 代理 | 空 |
| `KUGOU_API_GUID` | 设备 GUID | 自动生成 |

## 请求约定

- GET / POST 都支持；POST 的 URL 必须带时间戳，否则会被缓存。
- 接口默认缓存 2 分钟；需实时结果时在 URL 加 `?timestamp=...`。
- Cookie 可通过查询参数、请求体或 `Authorization` 头传递。
- 登录接口不要频繁调用，可能触发风控。

## 目录结构

| 路径 | 说明 |
| --- | --- |
| `module/` | 约 160 个接口模块，文件名即路由（`_` 替换为 `/`） |
| `util/` | 签名、加密、请求封装、缓存、设备指纹 |
| `public/` | 登录验证码等前端页面（含 WASM） |
| `docs/` | 原始 Docsify 文档源 |
| `main.js` | 编程式调用入口 |
| `server.js` | Express 服务核心 |

## 签名机制

- 所有请求需签名，三种类型：Android（默认）、Web、Register。
- 标准版 `appid=1005` / `clientver=20489`；概念版 `appid=3116` / `clientver=11440`。
- 概念版还需行为指纹 SID/EDT（RSA-OAEP + AES-128-CBC）。

## 添加新接口

1. 在 `module/` 新建 `.js`，文件名即路由路径。
2. 导出 `(params, useAxios) => Promise`。
3. 细节见 `backend/KuGouMusicApi/CLAUDE.md`。

## 免责声明要点

仅供技术学习研究，尊重版权，禁止商业或非法用途，请在 24 小时内清除产生的版权数据。
