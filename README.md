# library
灯库仓库

## Modus 灯库数据分发

本仓库只维护以后新增／修改的灯库及维护工具，不备份现有本地库，不包含 Modus 软件源码、Show、账号凭证或研究样本。

- 上传更新：把新文件放进 `fixtures/`，Commit → Push；GitHub Actions 自动生成 [Releases](https://github.com/wu271861748-jpg/library/releases) 和更新索引。
- Modus 从 `updates/catalog.json` 检查并下载更新，合并到本地基础库；用户不需要登录 GitHub。
- 下载成功后可离线浏览与另存 XML / XMLP 原文件，不自动导入控台。
- 普通访问者可以查看、下载或 Fork；修改原仓库仍需维护者写入权限。

维护说明见 [MAINTENANCE.md](MAINTENANCE.md)。灯库原文件保留其原始来源和权利归属；索引解析结果不是全部模式的实机兼容承诺。
