# 酷狗flow — AI 知识库入口

本目录把 KuGouMusicApi 的在线文档本地化，供 AI 快速检索。

## 文件说明

| 文件 | 用途 | 何时读 |
| --- | --- | --- |
| `api-catalog.md` | **接口索引**，201 个接口按功能分类，附原始文档行号 | 找接口时先读这个 |
| `KuGouMusicApi-full.md` | **原始文档全文**，4185 行，含请求参数与返回示例 | 根据索引行号精确定位后读取 |
| `backend-guide.md` | **后端架构速查**：运行方式、概念版配置、签名机制 | 需要运行/改造后端时读 |
| `../Agent.md` | **项目技术约定** | 每次工作开始前读 |

## 使用流程

1. 在 `api-catalog.md` 中按功能分类找到目标接口，记下行号。
2. 读取 `KuGouMusicApi-full.md` 该行号附近内容（建议前后各 15 行）。
3. 若需改造后端，再读 `backend-guide.md` 与 `backend/KuGouMusicApi/CLAUDE.md`。

## 重要提示

- 本项目为「概念版」，后端需设置 `platform=lite`；不同平台的 token 不通用。
- 接口有 2 分钟缓存；需要实时结果时在 URL 加时间戳参数。
- 原始文档对应在线地址：`https://makcre.github.io/KuGouMusicApi/#/`
- 源码位置：`backend/KuGouMusicApi/`
