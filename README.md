# Dong Huang 的个人主页

[官网](https://donghuang-stat.github.io/)的内容只维护根目录下的 **三个 Markdown 文件**。组织方式借鉴 AcademicPages 的「内容与固定模板分离」思路；当前使用自己的静态页面生成器，无需 Jekyll 或额外 Python 依赖。

| 修改内容 | 打开文件 |
| --- | --- |
| 个人介绍、照片、CV、首页精选论文、近期新闻条数、Education、Awards | [home.md](home.md) |
| 全部论文、作者、发表信息、链接、分组和顺序 | [research.md](research.md) |
| 全部新闻；首页自动读取前几条 | [news.md](news.md) |

## 直接在 GitHub 更新

网页编辑是最方便的更新方式，不需要在本地运行 Python：

1. 打开[网站仓库](https://github.com/donghuang-stat/donghuang-stat.github.io)；默认分支是 `homepage-redesign`。
2. 打开 `home.md`、`research.md` 或 `news.md`，点击铅笔按钮修改。
3. 点击 **Commit changes**，直接提交到 `homepage-redesign`；也可以创建 PR，合并到这个分支后再发布。
4. 在 [GitHub Actions](https://github.com/donghuang-stat/donghuang-stat.github.io/actions) 等待构建和部署任务变绿，再刷新官网。浏览器可能缓存旧页面约 10 分钟；看不到更新时可强制刷新。

提交 Markdown 后，GitHub Actions 会自动生成 HTML、检查链接并部署。不要手动修改生成的 HTML。如果 Markdown 格式或链接有误，构建会失败并保留上次成功发布的网站；打开失败任务的日志即可查看需要修改的位置。

## 编辑方式

直接修改 Markdown 中的文字。`#` 是页面标题，`##` 是板块，`###` 是论文、教育经历或奖项条目；正文支持 `[链接文字](https://example.com)`、`**加粗**`、`*斜体*` 和列表。请保留现有板块名称及论文字段名称的英文拼写。新增内容时复制同类条目最方便。

`home.md` 和 `research.md` 开头两个 `---` 之间是简短的页面设置，每行写 `字段名: 内容`。字段名保持不变，冒号后的值可以直接修改，不需要加引号。例如：

```text
cv: assets/CV_2608.pdf
cv_updated: 2026/08
photo: assets/portrait.jpg
selected_papers: 2602.08173, 2601.13966, 2510.25289, 2406.05428
recent_news_count: 3
```

`selected_papers` 填写 `research.md` 中论文的 ID，用逗号分隔，顺序就是首页的展示顺序。`recent_news_count` 控制首页显示 `news.md` 的前几条。姓名、学校身份和访问情况等正文在设置之后直接编辑。

### 添加论文

在 `research.md` 的 `## Manuscripts` 或 `## Publications` 下复制一篇论文，并替换内容。以下是格式模板：

```markdown
### Your paper title

- ID: new-paper
- Authors: Dong Huang; Coauthor Name
- Year: 2026
- Venue: Submitted
- Short venue: Manuscript
- Author order: Listed

- [arXiv](https://arxiv.org/abs/REPLACE_WITH_ID)
- [Poster](assets/new-poster.pdf)
```

ID 必须唯一；作者姓名用分号分隔。`Author order` 填 `Alphabetical` 显示 α–β，填 `Listed` 不显示该标记。可选字段 `- Equal contribution: Name; Name` 标记共同一作，`- Note: 备注` 显示在 Research。作者和论文顺序都以文件中的排列为准。

首页精选中的已发表论文默认显示与 Research 相同的 Venue；需要首页专用说明时，可用 `- Selected note: 说明` 覆盖。字段内需要明确换行时，在行末加反斜杠 `\`，下一行缩进两个空格，例如：

```markdown
- Venue: IEEE Transactions on Information Theory, 2025 (long version)\
  The 37th Conference on Learning Theory (COLT), 2024 (short version)
```

论文标题或链接只需修改一次，首页精选会同步更新。论文被接收后，更新 Venue 和 Short venue，并把整条记录移动到 Publications。要加入首页精选，把该论文 ID 加到 `home.md` 的 `selected_papers`。

### 添加新闻、教育经历或奖项

新闻在 `news.md` 中使用 `## 英文月份 年份`，最新一条放在最上面；保留自己的第一人称叙述：

```markdown
## September 2026

I will present our work at [Conference name](https://example.com).
```

教育经历放在 `home.md` 的 `## Education` 下。`###` 后写 `日期 | 身份`，第一段是学校，第二段是说明：

```markdown
### 2027 – 2028 | Visiting Scholar

University name

Department name · Host: Prof. [Name](https://example.com)
```

奖项放在 `home.md` 的 `## Selected awards` 下，格式如下：

```markdown
### 2027

[Award name](https://example.com)
```

## 本地预览和发布

也可以在本地编辑，需要 Python 3.9 或更新版本及 Git。混合使用网页和本地编辑时，每次开始本地修改前，先保存并处理已有修改，确认工作区干净，再在仓库目录同步远端：

```sh
git pull --ff-only origin homepage-redesign
```

启动本地预览：

```sh
python3 serve.py
```

打开 [本地预览](http://127.0.0.1:4173/)。启动时自动生成页面，之后保存 Markdown、刷新浏览器即可看到修改。端口被占用时使用 `python3 serve.py --port 4174`；按 Control-C 停止预览。

独立检查和正式发布分别运行：

```sh
python3 publish.py --check
python3 publish.py -m "Update homepage content"
```

`--check` 只重建和检查内容、链接及资源。发布命令会重建、检查、提交并推送；远端有尚未合入的更新时会停止，不会强制覆盖。推送后由同一个 GitHub Actions 工作流自动构建和部署，等待任务成功即可。

`homepage-redesign` 是仓库默认分支。GitHub Pages 的发布来源是 **GitHub Actions**，仅发布这个分支；`master` 保留旧站备份。当前电脑直接在 `page/` 中更新即可，换电脑后需配置 GitHub 写入权限。

## 照片、PDF 和模板

CV 是独立 PDF，网页修改不会改变 PDF 内容。替换 `assets/CV_2608.pdf` 最方便；使用新文件名时，更新 `home.md` 的 `cv`，并用 `cv_updated` 设置首页显示的更新月份；只有“CV ↗”是 PDF 链接，更新日期是普通文字。照片同理，替换文件或修改 `photo`。正文中的本地链接相对于这三个根目录 Markdown 文件填写，例如 `[Poster](assets/new-poster.pdf)`。

`assets/`、`_pages/` 中的 PDF、常见图片、CSS、JavaScript、图标和字体资源会自动纳入发布。`_pages/` 保留正在使用的五份海报，以维持原链接；旧网址 `/publications/`、`/news/`、`/cv/` 保留跳转。

生成的 HTML 不需要手动编辑。`build.py`、`content.py`、`assets/style.css` 和 `assets/site.js` 是固定模板、解析与样式代码；[.github/workflows/pages.yml](.github/workflows/pages.yml) 负责 GitHub 上的自动构建和部署。只有调整设计或功能时才需要修改这些文件。旧版 Markdown、历史资料和上传目录已归档到 `.local/archive/`，只在本地保留，不会发布。
