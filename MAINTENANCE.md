# 只上传以后新增／修改的灯库

现有本地灯库不上传。这个仓库是增量更新源，不是备份仓库，也不包含 Modus 软件源码。

## 上传步骤
1. 将以后需要发布的 MA2 `.xml` / `.xmlp` 放进本仓库的 `fixtures/` 文件夹，可以使用子文件夹。
2. 在 GitHub Desktop 中确认变更文件，填写说明，点击 **Commit to main**，再点 **Push origin**。只放文件不点 Push 不会上传。
3. 仓库的 **Actions → Publish fixture updates** 自动解析文件，只发布厂家/型号/模式等 JSON 目录，并更新 `updates/catalog.json`，不再构建厂家 ZIP。无需另建 Token。
4. Actions 显示成功后，在 Modus 点击“更新目录”即可看见在线条目；浏览、搜索和选模式不会下载原文件。确认“下载并另存原文件”及目标位置后，只下载选中的文件并缓存。软件不删除或上传原有灯库。

Windows 维护者也可以在放好文件后双击仓库根目录的 `提交更新.cmd`：它只校验、提交和推送 `fixtures/`，不监控目录、不改全局Git设置，也不会上传项目源码。首次推送如果 Git 提示登录，只在 Git 的正常登录窗口授权；不要把密码或验证码写进文件。

也可以直接在 GitHub 的 `fixtures/` 目录使用 Add file → Upload files，提交到 main 后会触发同一流程。仓库公开，这里只放准备公开的灯库；不要放 Show、插件、压缩研究包、凭证或私人文件。

## 文件与版本
- 同一路径修改文件，下次 Push 会发布新版；新型号使用新文件。
- 删除仓库文件不代表删除用户已安装的文件。当前没有远程删除本地灯库的功能。
- 已经发布的 Release 不删除或覆盖。旧版已下载厂家包继续可用；新的逐文件下载固定到包含原文件的 Git commit，不使用可能变化的 main 文件地址。
- `updates/catalog.json` 是自动产物，不手改；数据版本由 Actions 生成，与软件 EXE 版本独立。
- 空 `fixtures/` 和没有灯库内容变化的 Push 不创建 Release。维护工具不会读取仓库外的本地灯库目录。
- XML/XMLP 解析通过不代表所有灯具和控台版本已实机验收。MA3/GDTF 不属于此 MA2 更新入口。

## 协议
固定公开索引：`https://raw.githubusercontent.com/wu271861748-jpg/library/main/updates/catalog.json`

`schema: 3`、`kind: fixture-updates`。厂家条目中的 `fixtures` 提供检索元数据、大小、SHA256 与指向当前仓库固定 commit 的 `downloadUrl`。这里只索引本仓库 `fixtures/` 中未来新增的更新，不是完整基础库；没有 ZIP 下载步骤，原字节不改写。

目录更新与文件缓存是独立状态：目录已是最新，不代表把所有在线文件下载过。地球图标表示在线来源，已缓存状态另行标记。原生配接/导入不由这个发布流程执行。
