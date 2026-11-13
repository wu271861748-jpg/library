# 只上传以后新增／修改的灯库

现有本地灯库不上传。这个仓库是增量更新源，不是备份仓库，也不包含 Modus 软件源码。

## 上传步骤
1. 将以后需要发布的 MA2 `.xml` / `.xmlp` 放进本仓库的 `fixtures/` 文件夹，可以使用子文件夹。
2. 在 GitHub Desktop 中确认变更文件，填写说明，点击 **Commit to main**，再点 **Push origin**。只放文件不点 Push 不会上传。
3. 仓库的 **Actions → Publish fixture updates** 自动解析文件、构建变化厂家包、发布 Release 并更新 `updates/catalog.json`。无需另建 Token。
4. Actions 显示成功后，在 Modus 内检查并下载更新。软件把新增来源合并到本地，不删除或上传原有灯库。

Windows 维护者也可以在放好文件后双击仓库根目录的 `提交更新.cmd`：它只校验、提交和推送 `fixtures/`，不监控目录、不改全局Git设置，也不会上传项目源码。首次推送如果 Git 提示登录，只在 Git 的正常登录窗口授权；不要把密码或验证码写进文件。

也可以直接在 GitHub 的 `fixtures/` 目录使用 Add file → Upload files，提交到 main 后会触发同一流程。仓库公开，这里只放准备公开的灯库；不要放 Show、插件、压缩研究包、凭证或私人文件。

## 文件与版本
- 同一路径修改文件，下次 Push 会发布新版；新型号使用新文件。
- 删除仓库文件不代表删除用户已安装的文件。当前没有远程删除本地灯库的功能。
- 已经发布的 Release 不删除或覆盖：新索引可能引用旧版本中未变化的包。
- `updates/catalog.json` 是自动产物，不手改；数据版本由 Actions 生成，与软件 EXE 版本独立。
- 空 `fixtures/` 和没有灯库内容变化的 Push 不创建 Release。维护工具不会读取仓库外的本地灯库目录。
- XML/XMLP 解析通过不代表所有灯具和控台版本已实机验收。MA3/GDTF 不属于此 MA2 更新入口。

## 协议
固定公开索引：`https://raw.githubusercontent.com/wu271861748-jpg/library/main/updates/catalog.json`

`schema: 2`、`kind: fixture-updates`。这里只索引本仓库 `fixtures/` 中未来新增的更新，不是完整基础库。包与单文件均保留 SHA256，原字节不改写。
