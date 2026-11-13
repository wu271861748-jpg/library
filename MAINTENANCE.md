# 灯库数据维护

这是独立的数据分发仓库，不是 Modus 软件源码仓库。用户无需 GitHub 登录即可下载 Release 数据。

## 新增或更新灯库
1. 在维护机的灯库资料目录导入 XML/XMLP，并使用维护端索引脚本生成 `_index/manufacturers.json` 和各厂家 `manifest.json`。原文件字节、来源、大小、SHA256 必须与索引一致；不要直接手改版本或伪造格式。
2. 从上一版 Release 下载 `catalog.json`，保存为 `previous.json`。首版不需要此文件。
3. 使用 Python 3 标准库构建新数据版本，例如：

```sh
python tools/build_release.py --source ./fixture-data --output ./release-assets --version 2026.11.13.2 --previous ./previous.json
```

`--source` 是维护端资料目录，不会上传。`--output` 必须在资料目录之外。生成的 `upload-files.txt` 列出了本版需要上传的 ZIP 和 `catalog.json`；没有变化的厂家沿用旧 Release URL，不重复上传。ZIP 文件名只是该版的编号，厂家与包的对应关系、完整 hash 在 `catalog.json` 中。

4. 在 GitHub Releases 创建新版本，Tag 必须是 `library-` 加上上述数据版本，例如 `library-2026.11.13.2`。
5. 只附加 `upload-files.txt` 列出的文件，等待全部上传完成，再发布为最新正式 Release。不要勾选 Pre-release。软件中的“检查更新 → 下载更新”会拉取新数据，不需要发布新的软件 EXE。

## 保持可重复下载
- 已发布的版本和 ZIP 不覆盖；修改时使用新的数据版本。
- 不删除旧 Release：新索引可能继续引用其中没有变化的厂家包。
- 不上传 `upload-files.txt`、`build-summary.json` 或整个源目录。它们只是维护端辅助文件。
- `_sources`、`_review`、原始未解析压缩包、Show、插件、软件源码、凭证与日志均不属于分发内容。
- 构建器只收录索引明确指向的 XML/XMLP 和经过字段筛选的厂家清单；逐文件校验大小和 SHA256，不改写灯库原字节。

## 下载协议
最新索引固定入口：

`https://github.com/wu271861748-jpg/library/releases/latest/download/catalog.json`

索引 `schema: 1`，软件按厂家 ZIP SHA256 检查变化。每个包使用确定版本的 Release URL，并附带包大小/hash、厂家清单 hash。软件在本地完成全部包和文件校验后才切换活动索引；下载失败保留上一份灯库，成功下载后可以离线浏览与另存。

解析通过不代表所有灯具模式和控台版本均已实机验收。此仓库不自动导入控台，不包含登录凭证。
