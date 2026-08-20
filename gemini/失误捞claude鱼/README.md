# Gemini 失误捞 Claude 鱼（事故现场）

这九份**不是** Gemini 做的小页面。
是 Gemini 试图给 Claude 的打捞机加核、结果越改越歪的九个版本。
编号不要改，改了就不知道该笑哪一份了。

| 编号 | 文件 | 当时以为自己是 | 真正好笑的地方 |
|---|---|---|---|
| 001 | gemini失误捞claude鱼001.html | 双核（Gemini + ChatGPT） | 找不到 JSON 就把整份 HTML 吞进去 |
| 002 | gemini失误捞claude鱼002.html | 同上，补了 `<br>` | 终于记得 Google 会把换行变成 br |
| 003 | gemini失误捞claude鱼003.html | 突然宣布三核 | 加了 Claude 的 `chat_messages`，自称支持 Claude |
| 004 | gemini失误捞claude鱼004.html | 开始抓 `<antArtifact>` | `isFullHtml` 把 jsx / svg 都算完整网页 |
| 005 | gemini失误捞claude鱼005.html | 更放宽 | `import React` 也算网页 |
| 006 | gemini失误捞claude鱼006.html | 默认改成「全部代码」 | `findArrayStart` 用超慢切片找 jsonData |
| 007 | gemini失误捞claude鱼007.html | Gemini 分支补换行 | 还是捞不出 Claude 的网页 |
| 008 | gemini失误捞claude鱼008.html | 见到第一个 `{` 就算对话 | Grok 那个 130MB 对象外壳刚好是 `{` |
| 009 | gemini失误捞claude鱼009.html | 收了一点 | 去掉 `source===claude` 一律当网页，Claude 还是空的 |

旁边 `gemini/` 根目录里那些有标题的，才是 Gemini 真正做出的小文件。
