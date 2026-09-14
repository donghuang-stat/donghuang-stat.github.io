# Dong Huang 的个人主页

网站：[donghuang-stat.github.io](https://donghuang-stat.github.io/)。日常更新只需要编辑 `content/` 里的 Markdown 文件，不需要写 HTML 或 JSON。页面布局、字体和配色由生成器统一处理。

本项目的本地工作集中在 `page/`；旧的上传与发布目录收纳在 `.local/archive/`，作为本地备份，不会发布到 GitHub。

## 改哪里

| 想修改的内容 | 文件 |
| --- | --- |
| 姓名、身份、个人简介、联系方式、照片和 CV 链接 | [content/profile.md](content/profile.md) |
| 首页 Selected research 的论文选择、顺序和说明 | [content/selected-research.md](content/selected-research.md) |
| 首页 Recent news 的标题和显示条数 | [content/recent-news.md](content/recent-news.md) |
| 全部新闻；首页自动取其中前几条 | [content/news.md](content/news.md) |
| Education | [content/education.md](content/education.md) |
| Selected awards | [content/awards.md](content/awards.md) |
| Research 页简介、论文分组和顺序 | [content/research.md](content/research.md) |
| 每篇论文的标题、作者、年份、发表信息和链接 | [content/papers/](content/papers/) 下的对应论文文件 |

同一篇论文只维护一份文件；Home 和 Research 会同步读取。`selected-research.md` 和 `research.md` 中的链接顺序，就是页面上的显示顺序。

文件中的 `#` 是板块或论文标题，`##` 是字段或条目。请保留 `## Biography`、`## Authors`、`## Papers` 等固定字段名的英文拼写，在它们下面修改内容。新闻、教育和奖项的 `##` 日期标题则可以按实际情况新增或修改。

正文可以直接写普通英文，也支持常用 Markdown：

```markdown
一段普通文字。段落之间空一行。

**加粗文字**，*斜体文字*，以及 [链接文字](https://example.com)。

- 第一项
- 第二项
```

本地链接相对于当前 Markdown 文件填写，普通 Markdown 预览也能直接打开。`content/profile.md` 中的照片写成 `![图片说明](../assets/portrait.jpg)`，CV 写成 `[CV (PDF)](../assets/CV_2608.pdf)`；`content/papers/` 下的论文要链接到 `assets/`，则使用 `../../assets/文件名`。论文目录中的链接沿用 `papers/论文编号.md`。

## 添加新闻

在 `content/news.md` 的 `# News` 后面、现有新闻之前加入一条，保持最新消息在最上面。下面是格式示例，请替换为自己的日期和消息：

```markdown
## September 2026

I will present our work at [Conference name](https://example.com).
```

日期使用完整英文月份和四位年份。首页展示前几条，由 `content/recent-news.md` 中 `## Display count` 下的数字决定。

## 添加或更新论文

修改现有论文时，直接打开对应的 `content/papers/编号.md`。例如 2601 的论文标题在 `content/papers/2601.13966.md` 第一行。

添加论文时，新建文件，例如 `content/papers/new-paper.md`，复制下面的模板并替换标题、作者、年份和链接：

```markdown
# Your paper title

## Authors

- Dong Huang
- Coauthor Name

## Year

2026

## Venue

Submitted

## Short venue

Manuscript

## Author order

Listed

## Links

- [arXiv](https://arxiv.org/abs/REPLACE_WITH_ID)
```

`Author order` 填 `Alphabetical` 会显示 α–β 标记，填 `Listed` 则按作者列表展示而不加标记。共同一作可增加 `## Equal contribution`，下面用 `- 作者姓名` 列出，姓名需与 Authors 一致。`## Note` 是 Research 页备注；`## Selected note` 是首页 Selected research 中的备注，两者都可省略。

然后在 `content/research.md` 的 `## Manuscripts` 或 `## Publications` 下添加：

```markdown
- [new-paper](papers/new-paper.md)
```

需要首页精选时，在 `content/selected-research.md` 的 `## Papers` 下也加入同一行。接收发表后，可以更新论文的 Venue 和 Short venue，并把它从 Manuscripts 列表移到 Publications 列表。这里只需要移动链接，不用复制论文文件。

新增海报放到 `assets/`，再在论文的 `## Links` 下加入 `- [Poster](../../assets/new-poster.pdf)`。发布脚本自动处理 `content/` 下的 Markdown，以及 `assets/`、`_pages/` 下的 PDF 和常见网页资源，无需修改发布清单。支持的资源扩展名是 `.pdf`、`.jpg`、`.jpeg`、`.png`、`.webp`、`.svg`、`.gif`、`.css`、`.js`、`.ico`、`.woff`、`.woff2`，包括这些文件的新增、修改和删除。

## 添加奖项或教育经历

在 `content/awards.md` 中复制一个条目，修改日期和正文；可以使用 Markdown 链接：

```markdown
## 2027

[Award name](https://example.com)
```

在 `content/education.md` 中，条目标题格式是 `日期 | 身份`，第一段是学校，第二段是详细说明：

```markdown
## 2027 – 2028 | Visiting Scholar

University name

Department name · Host: Prof. [Name](https://example.com)
```

奖项和教育经历按文件中的顺序显示。

## 本地检查、预览和发布

需要 Python 3.9 或更新版本，以及 Git；不需要安装额外 Python 包。从这个仓库的根目录运行：

```sh
python3 publish.py --check
python3 serve.py
```

打开 [本地预览](http://127.0.0.1:4173/)。`serve.py` 启动时会自动生成页面；之后保存 Markdown，刷新浏览器就会自动重建并显示修改，不需要每次重跑检查或重启预览。端口被占用时可用 `python3 serve.py --port 4174`。按 Control-C 停止预览。

`--check` 可用于发布前或不启动预览时的独立检查：只重建和检查页面、链接、锚点及资源，不会提交或上传。Markdown 格式有误时，预览服务会在终端提示，并保留上次成功生成的页面。确认预览后发布：

```sh
python3 publish.py -m "Update homepage content"
```

脚本会重建、检查、提交并推送到 `homepage-redesign` 分支。若远端有本地尚未包含的提交，或存在无关的已暂存文件，脚本会停止并说明原因，不会强制推送。出现 `Push succeeded` 后，在 [GitHub Actions](https://github.com/donghuang-stat/donghuang-stat.github.io/actions) 等待 Pages 部署成功，再刷新官网。

GitHub Pages 使用 `homepage-redesign` 分支的 `/(root)` 目录；`master` 保留旧站备份。在另一台电脑上使用时，可以克隆该分支：

```sh
git clone --branch homepage-redesign https://github.com/donghuang-stat/donghuang-stat.github.io.git
cd donghuang-stat.github.io
python3 publish.py --check
```

新电脑需要单独配置 GitHub 写入权限，才能发布。

## 照片、CV 和保留文件

CV 是独立 PDF，修改网页不会改变 PDF 内容。最方便的更新方法是直接替换 `assets/CV_2608.pdf`。如果换了文件名，把 `content/profile.md` 中的 CV 链接改为 `../assets/新文件名.pdf` 即可；导航、首页和 `/cv/` 跳转会跟随该链接。

照片同样可以替换 `assets/portrait.jpg`，或在 `content/profile.md` 中改为新图片路径。

`_pages/` 只保留当前论文引用的五份海报，以维持原链接。`/publications/`、`/news/` 和 `/cv/` 保留小型跳转页。`sources/` 是原官网内容的历史参考，不参与日常生成。

`index.html`、`research.html`、`news.html` 和跳转页都是自动生成的；日常内容请修改 Markdown。只有需要调整版式或功能时，才需要编辑 `build.py`、`assets/style.css` 或 `assets/site.js`。
