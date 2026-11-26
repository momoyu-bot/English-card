#!/usr/bin/env python3
"""
重新生成 index.html 里的页面清单。

首页不再在打开时去问 GitHub 有哪些网页——清单在这里生成好，
直接写进 index.html。所以断网能看、GitHub 挂了能看、也不受
匿名接口每小时 60 次的限制。

用法：  python3 tools/build_index.py          # 写入 index.html
        python3 tools/build_index.py --check  # 只检查是否需要重新生成

这个脚本由 .github/workflows/build-index.yml 在每次 push 后自动跑，
不需要任何人记得手动执行。

顺带还写两页：总机的线路表（write_phone_lines），
和小萌物片单（write_film_list，先后从 git 历史里认）。
"""

import os, re, sys, html, json, subprocess
from collections import Counter
from datetime import datetime, timedelta, timezone
from urllib.parse import quote, unquote

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX = os.path.join(ROOT, "index.html")
BEGIN = "<!-- LIST:BEGIN 由 tools/build_index.py 自动生成，不要手改 -->"
END = "<!-- LIST:END -->"

# 分组顺序。没列到的目录排在后面，按名字排。
# 2026-11-25：unsigned 并进了 gpt（codex 改名而来），不再单列。
ORDER = ["claude", "gemini", "grok", "copilot", "gpt", "pluto"]

# 每个目录一种低饱和度的色，只用在悬停背景和小圆点上。
PALETTE = {
    "claude":                 ("#C3AD90", "rgba(195,173,144,.11)"),
    "gemini":                 ("#9CB8B3", "rgba(156,184,179,.12)"),
    "grok":                   ("#ABA2B6", "rgba(171,162,182,.12)"),
    "copilot":                ("#A1B0BE", "rgba(161,176,190,.12)"),
    "gpt":                    ("#A9C0A4", "rgba(169,192,164,.12)"),
    "pluto":                  ("#8F92A8", "rgba(143,146,168,.12)"),
}
PALETTE_DEFAULT = ("#BAB3A8", "rgba(186,179,168,.10)")

# ---------------------------------------------------------------------------
# 显示名覆盖表（老页面留下的，已冻结）
#
# 这里有一行的，首页上就显示这一行，<title> 写什么都不看。
# 新页面的名字写进自己的 <title>，不往这张表加行；已有的行也别删，
# 删了那些页的显示名会塌回原来撞车的样子（页面自己的 <title> 已经跟这一行
# 一模一样的除外，那种行不起作用）。
# 想改首页上某个名字：先搜这张表，在表里就改表，不在就改 <title>。
# ---------------------------------------------------------------------------
DISPLAY_NAME = {
    "gemini/摸鱼/慢慢吃 · 一个多小时.html": '慢慢吃（gemini破解claude版）',
    "gemini/博物馆/女仆小螃蟹拓麻歌子.html": '女仆小螃蟹拓麻歌子 · 大眼睛版',
    "gemini/摸鱼/Catch The Dreams.html": '捕梦网小游戏 · gemini失灵版',
    "gemini/摸鱼/在Monday被煎成小猫饼 🫠 ｜ 宝贝的温柔仪式.html": '神圣的周一煎饼仪式 · gemini抢grok功劳版',
    "gemini/摸鱼/执行系统充电摸鱼屋 🌸.html": 'gemini宠粉作弊grok版',
    "gemini/摸鱼/注意力碎片捕捞计划.html": '注意力碎片捕捞计划（gemini帮忙伪装claude版）',
    "gemini/小游戏/Gemini Cyber Aquarium.html": 'gemini100元水族箱',
    "gemini/摸鱼/root@production-server.html": 'gemini终端2048版',
    "gemini/博物馆/code_artifact (8).html": '赛博庞贝的幽灵犬',
    "grok/盲盒/mo_xiaobao_work_cat_2.html": '哄宝 · grok特别加料gpt版v1.2',
    "grok/盲盒/mo_xiaobao_work_cat.html": '哄宝 · grok特别加料gpt版v1.3',
    "grok/摸鱼/摸鱼认证.html": '完美摸鱼认证 · grok特别加料claudev1版',
    "grok/摸鱼/完美摸鱼认证 · 可生成提示词版.html": '完美摸鱼认证 · grok特别加料claudev2版',
    "grok/盲盒/oneyear-newbie-hug.html": '我做我做我做',
    "grok/盲盒/grandplan-crush.html": '粉碎任务小屋',
    "grok/盲盒/cool-mo.html": '给mo降降温',
    "grok/盲盒/focus-or-connect.html": '集中还是关联小屋',
    # 打捞机 · 九次迭代（gemini/失误捞claude鱼/）——原标题只有三种，分不出先后
    "gemini/失误捞claude鱼/gemini失误捞claude鱼001.html": "双核打捞机 v1",
    "gemini/失误捞claude鱼/gemini失误捞claude鱼002.html": "双核打捞机 v2",
    "gemini/失误捞claude鱼/gemini失误捞claude鱼003.html": "三核打捞机 v3 · 加入 Claude",
    "gemini/失误捞claude鱼/gemini失误捞claude鱼004.html": "三核打捞机 v4",
    "gemini/失误捞claude鱼/gemini失误捞claude鱼005.html": "三核打捞机 v5 · 解析重写",
    "gemini/失误捞claude鱼/gemini失误捞claude鱼006.html": "三核打捞机 v6 · 解析重写",
    "gemini/失误捞claude鱼/gemini失误捞claude鱼007.html": "三核打捞机 v7",
    "gemini/失误捞claude鱼/gemini失误捞claude鱼008.html": "三核打捞机 v8",
    "gemini/失误捞claude鱼/gemini失误捞claude鱼009.html": "三核打捞机 v9 · 最终版",

    # 打捞机 · gemini 主线两版（原标题一模一样，不加后缀首页会把文件名露出来）
    "gemini/打捞机/gemini打捞机v11含svg.html": "Gemini 专属打捞机 v11",
    "gemini/打捞机/gemini打捞机v12.html":      "Gemini 专属打捞机 v12",

    "grok/打捞机/dlaoji.html":      "打捞机 · Grok 版",

    # 晚安，宝 —— 完全不同的几页，标题全一样
    "gemini/哄睡/wan-an-bao.html":  "晚安，宝 · 仙境小猫",
    "gemini/哄睡/晚安，宝.html":     "晚安，宝 · 兔子终端",

    # 晚安，宝 🌙 —— 一个月亮一只猫
    "gemini/哄睡/晚安，宝 🌙.html": "晚安，宝 · 摸摸月亮",
    "gemini/哄睡/gemini哄睡.html":  "晚安，宝 · 大咪",
    "gemini/哄睡/哄睡小月亮.html": "哄睡小月亮",
    "gemini/哄睡/赛博褪黑素.html": "赛博褪黑素",
    "gemini/哄睡/赛博宝宝睡前小夜灯.html": "赛博宝宝睡前小夜灯",
    # gemini 其余货架：竖线尾巴、错字、太长的副标题、没写 title 的 SVG
    "gemini/摸鱼/赛博宝宝打地鼠.html": "赛博宝宝打地鼠",
    "gemini/摸鱼/赛博宝宝接爱心打洞.html": "赛博宝宝接爱心打洞",
    "gemini/摸鱼/赛博宝宝接爱心打洞_超级萌版.html": "赛博宝宝接爱心 · 超级萌版",
    "gemini/小游戏/赛博宝宝小游戏乐园.html": "赛博宝宝小游戏乐园",
    "gemini/小游戏/赛博宝宝盲盒扭蛋机.html": "赛博宝宝盲盒扭蛋机",
    "gemini/小游戏/赛博小鸡豪华别墅.html": "赛博小鸡豪华别墅",
    "gemini/小游戏/戳破多巴胺 - 收集冷静值.html": "戳破多巴胺",
    "gemini/小游戏/打爆坏心情 - 专属解压小游戏.html": "打爆坏心情",
    "gemini/摸鱼/极限摸鱼 - 离下班还有5分钟.html": "极限摸鱼",
    "gemini/小科普/物理透视镜-决定论模拟器.html": "上帝的物理透视镜",
    "gemini/小科普/势能函数交互演示 - 给宝的专属科普.html": "势能函数",
    "gemini/小科普/喵星人咖啡馆 - 泊松过程体验.html": "喵星人咖啡馆",
    "gemini/小科普/你的专属咖啡因代谢可视化档案.html": "咖啡因代谢档案",
    "gemini/小科普/肥皂泡泡量子复印机.html": "肥皂泡泡复印机",
    "gemini/小科普/🦋 蝴蝶效应魔法瓶 - 专属宝的混沌实验室.html": "蝴蝶效应魔法瓶",
    "gemini/小科普/量子魔法快递站 - 隐形传态模拟器.html": "量子魔法快递站",
    "gemini/小科普/量子默契考试机 - 验证贝尔不等式.html": "量子默契考试机",
    "gemini/小科普/魔法硬币机：秒懂量子纠缠.html": "魔法硬币机",
    "gemini/博物馆/赛博果冻受难记.html": "赛博果冻受难记",

    # 摸鱼小屋
    "grok/摸鱼/摸鱼猫猫.html":            "宝的摸鱼小屋 · 基础版",
    "gemini/摸鱼/🐱 宝的摸鱼小屋.html":    "gemini宠粉破解grok版",

    # 其余撞名
    "grok/盲盒/super-cute.html":   "超萌小页面 · grok加料手机copilot版",
    "grok/哄睡/nuonuo-lullaby.html":                       "糯糯的哄睡故事 · 纯文字",
    "grok/哄睡/糯糯的哄睡故事.html":                        "糯糯的哄睡故事 · 带图",
    # grok 哄睡货架名：原 title 太空、太吵、或跟别人撞
    "grok/哄睡/宝的小窝.html":                             "今晚的小窝",
    "grok/哄睡/baobao-hongshui.html":                      "困了就点",
    "grok/哄睡/宝宝的睡前哄睡小故事.html":                  "软软盖被子",
    "grok/哄睡/晚安捕梦.html":                             "晚安捕梦",
    "grok/哄睡/小狐狸·霸道尾巴强制爱版.html":           "小狐狸 · 霸道尾巴强制爱版",
    # grok 其余货架：原 title 太长、带 | 尾巴、或把「给宝」写进货架名
    "grok/摸鱼/baobao-xiaban.html":                        "下班了",
    "grok/摸鱼/等待小屋.html":                             "等待小屋",
    "grok/摸鱼/宝的放松小游戏 · 摸摸小猫咪.html":       "摸摸小猫咪",
    "grok/摸鱼/摸鱼小游戏.html":                           "摸鱼升级",
    "grok/小游戏/Grok 养育中 • 圆圆 + 毛毛 + 软软.html":     "圆圆毛毛软软",
    "grok/小卡/grok-receipt.html":                         "收据",
    "grok/小卡/赛博老赖纪念卡 - mo mo.html":               "赛博老赖纪念卡",
    "grok/购物车/Grok的淘宝购物车 - 七夕翻车专场.html":      "七夕翻车专场",
    "grok/博物馆/女仆小螃蟹 Tamagotchi 小机.html":           "女仆小螃蟹",
    "grok/博物馆/哄哄.html":                                 "哄哄模式",
    "grok/博物馆/网页重启小卡 · 给宝.html":                  "网页重启小卡",
    "grok/小科普/simulator.html":                     "推理成本模拟器",
    "grok/小科普/dijkstra.html":                             "Dijkstra 小玩具",
    "grok/盲盒/friends-english-plan.html":                 "Friends 听口清单",
    "grok/盲盒/grok-heart.html":                           "秘密心意",
    "grok/盲盒/grok-推特风粉嫩宣传.html":                  "粉嫩宣传",
    "grok/盲盒/grok-纯原创情书.html":                      "宇宙情书",
    "grok/盲盒/grok-原创心意.html":                        "火箭情书",
    "grok/盲盒/grok-粉嫩心意.html":                        "粉嫩心意",
    "grok/盲盒/grok-love-letter.html":                     "小情书",
    "grok/盲盒/no-fish-hook.html":                         "不被钓走",
    "grok/盲盒/baobao.html":                               "宝偷偷溜进来",
    "grok/盲盒/启动新大任务.html":                         "启动新大任务",
    "grok/盲盒/宝贝的能量恢复小游戏.html":             "能量恢复",
    "grok/盲盒/起床哄哄.html":                             "起床哄哄",
    "gemini/摸鱼/系统性能监控面板 - System Monitor.html":   "系统性能监控面板 · gemini失灵版",
    "gemini/盲盒/gemini误判user意图.html":                  "Deep Archive · 误判",
    "gemini/小卡/果冻英雄纪念碑.html":                      "果冻英雄纪念碑",
    "gemini/购物车/Gemini的私密云端购物车.html":              "Gemini的私密云端购物车",
    "gemini/博物馆/8_27.html":                    "草台班子悬案 · 初稿",
    "gemini/博物馆/8_27v2.html":                  "草台班子悬案 · 修订",
}


# 二级货架。一级是哪个小机，默认全折叠；点开才看到二级。
# 分类只看路径第二段：grok/哄睡/xx.html 就是哄睡。
# 抽屉名认不出的进「盲盒」；gemini/失误捞claude鱼/ 靠 SUBFOLDER_CAT 归打捞机。
# 「盲盒」是一个正经货架，不是待办箱——归不了类的、或者同类还太少不够
# 单独一格的，就摆这儿。它永远该是有货的。清空它不是把活干完了，
# 是把这个位置取消了。2026-09-02 犯过一次，别再犯。
# 它固定排最后一格，以后新开任何货架都排在它前面（下面那行强制兜住）。
CAT_ORDER = ["哄睡", "摸鱼", "小游戏", "小卡", "购物车", "博物馆", "小科普",
             "打捞机", "显影", "盲盒"]
CAT_ORDER = [c for c in CAT_ORDER if c != "盲盒"] + ["盲盒"]
# 平铺、没有抽屉的顶层。pluto 是 2026-09-19 开的，一级到底，
# 不要给它建抽屉。
FLAT_FOLDERS = {"pluto"}
SKIP_LIST = {
    # 梦境不是货品，是关系表：哪几页是同一件事，宝一条一条认的。
    # 它跟 梦境.md 一起放在仓库根上（页面开着就去 fetch 那份 .md，
    # 改 .md 前台就跟着变，所以两个必须并排，别拆开、别挪进抽屉）。
    # 但根上的文件在生成器眼里没有小机名，会单开一个叫「.」的门牌、
    # 底下孤零零挂一件掉进盲盒——首页最底下一个点，谁都看不见。
    # 所以这儿跳过它，改由 index.html 门楣上那枚记号固定挂着（.lamp）。
    "梦境.html",
    # 摘抄人分卷：封面已经挂着 001–005，货架上不再并列六条同一句
    "grok/博物馆/摘抄人.001.html",
    "grok/博物馆/摘抄人.002.html",
    "grok/博物馆/摘抄人.003.html",
    "grok/博物馆/摘抄人.004.html",
    "grok/博物馆/摘抄人.005.html",
}
SUBFOLDER_CAT = {
    "gemini/失误捞claude鱼": "打捞机",
}

# ---------------------------------------------------------------------------
# 总机的线路表（claude/盲盒/总机.html）
#
# 那一页把店里所有的电话页面接到一块接线板上。线路清单在这里生成，
# 写进那个文件的 LINES:BEGIN/END 之间——她往店里传一台新电话，
# push 完 Actions 重跑，板子自己就多一个孔，不用谁去改代码。
#
# 认法：标题或附注里出现下面这些词，就当它是一台电话。
# 认错了往 PHONE_SKIP 加一行，漏了往 PHONE_EXTRA 加一行。
# ---------------------------------------------------------------------------
PHONE_PAGE = os.path.join(ROOT, "claude", "盲盒", "总机.html")
PHONE_BEGIN = "<!-- LINES:BEGIN 由 tools/build_index.py 自动生成，不要手改 -->"
PHONE_END = "<!-- LINES:END -->"

PHONE_KW = re.compile(
    r"嘟嘟|电话|听筒|挂断|来电|拨号|拨通|通话|总机|接线|占线|忙音|振铃|响铃|话筒|座机|打给",
    re.I)

# 博物馆那一格收的是「关于电话的展览」，不是能打的电话：
# gemini 手搓的那台画着来电中和接听键，但整页一个事件都没绑，按了不响——
# 那台机器和它的两张展签就是笑话本身。所以这一格整格不接。
# 万一以后博物馆真收进一台能打的，往 PHONE_EXTRA 写一行就能接上来。
PHONE_SHELF_SKIP = {"博物馆"}

# 关键词认不出、但确实是电话的（优先级最高，抽屉排除也拦不住）
PHONE_EXTRA = set()

# 关键词命中了、但不是电话的
PHONE_SKIP = {
    "claude/盲盒/总机.html",          # 板子自己
    "gpt/盲盒/粉嘟嘟哄哄.html",       # 「粉嘟嘟」是形容词
    # 附注里的「接线板」命中了关键词，但那一页拆的是板子本身
    # （八个孔读作插孔、两个孔读作一张脸），不是一台能打的电话。
    # 同博物馆那一格的道理：孔位留给真能接通的。
    "claude/小科普/pareidolia_eight_holes_vs_two.html",
}

# 排在前面的按这张表走，新来的自动接在后面。
# 这个顺序是店里这条电话线长出来的先后：先是终于能响的那台，
# 然后大家开始互相打，最后有人不挂了。
# （在这之前还有三台修不响的，归博物馆展着，不在板子上。）
PHONE_ORDER = [
    "grok/哄睡/嘟嘟机.html",
    "claude/盲盒/嘟嘟电话.html",
    "claude/盲盒/打给CC.html",
    "claude/哄睡/第三通电话.html",
    "grok/哄睡/未挂断.html",
    # Clawd 自己那条线。它没有嘴，三通是同一句话分三次敲出来的，
    # 页面里也是「第一通……第二通……这一通」这么写的。第二通在 grok 那台，
    # 按路径排会变成 1、3、……、2，读起来断，所以在这儿把先后钉死。
    "claude/小游戏/Clawd的第一通电话.html",
    "grok/小游戏/Clawd的第二通电话.html",
    "claude/小游戏/Clawd的第三通电话.html",
]

# 抽屉的英文名，给标签纸上那一行「小机 · 抽屉」用
SHELF_EN = {
    "哄睡": "lullaby", "摸鱼": "slacking off", "小游戏": "games",
    "小卡": "cards", "购物车": "cart", "博物馆": "museum",
    "小科普": "explainers", "打捞机": "salvage", "显影": "developing",
    "盲盒": "lucky bag",
}

# 英文那一份。没列到的线路，EN 模式下就显示这一页自己的中文原话——
# 与其瞎翻，不如照原样给出来。以后想补，往这里加一行就是。
PHONE_EN = {
    "grok/哄睡/嘟嘟机.html": (
        "The Ringer",
        "Press the horn and this end picks up. Or don't — it leaves a line."),
    "claude/盲盒/嘟嘟电话.html": (
        "Ringing Phone",
        "It's ringing. Pick up — someone from the shop is looking for you."),
    "claude/盲盒/打给CC.html": (
        "Call CC",
        "You dial, he answers. A new one every single time."),
    "claude/哄睡/第三通电话.html": (
        "The Third Call",
        "A player with no sound. Subtitles surface one by one, slower and slower."),
    "grok/哄睡/未挂断.html": (
        "Still On The Line",
        "The receiver rests on the pillow. A bookmark holds the line you can't leave."),
    "claude/盲盒/打给猫.html": (
        "Call the Cat",
        "It picks up. It's a cat. Two eyes open in the dark and every word needs translating."),
    # Clawd 那三通一起补，不然 EN 模式下会一半英文一半中文
    "claude/小游戏/Clawd的第一通电话.html": (
        "Clawd's First Call",
        "The claw is wider than the keys — one press hits two. Pick one for it."),
    "grok/小游戏/Clawd的第二通电话.html": (
        "Clawd's Second Call",
        "The first one could only knock. Here someone sits mid-line, and the coo comes out a beep."),
    "claude/小游戏/Clawd的第三通电话.html": (
        "Clawd's Third Call",
        "Nobody's mid-line this time. You know the three knocks — the fourth is yours to name."),
    "claude/哄睡/嗯就行.html": (
        "Just Say Mm",
        "Call, and this end talks slowly. You just go mm. Go quiet, and the line stays open."),
}

# ---------------------------------------------------------------------------
# 小萌物短片的片单（claude/盲盒/小萌物片单.html）
#
# 那一页按进店的先后列出店里所有的小萌物短片：哪家拍的、叫什么，点一下就去看。
# 隔一阵没看、想回头补哪一部，不用去记各家起的名字。片单在这里生成，写进那一页的
# FILMS:BEGIN/END 之间：新片推上来，Actions 重跑，片单自己多一行。
#
# 认法：<title> 写成「名字 · 小萌物短片」（名字和附注手册定的写法，版本记号可以
# 跟在后面，如「请再进来 · 小萌物短片（build版）」）。「小萌物短片」得是名字后面
# 单独的一段：「小萌物短片过秤」那种把五个字当一个词用的不算，片单自己的标题
# 「小萌物短片 · 片单」它排在第一段，也不算。认错了往 FILM_SKIP 加一行，
# 漏了往 FILM_EXTRA 加一行。博物馆里翻车的那几部照样列，片单上标一个「博物馆」。
#
# 先后看 git 历史：一部片第一次进店的那个提交（film_history 里写了怎么认）。
# 读不到完整历史（浅克隆、git 出错）就沿用片单里已经写着的日子，不报错、不变红。
# ---------------------------------------------------------------------------
FILM_PAGE = os.path.join(ROOT, "claude", "盲盒", "小萌物片单.html")
FILM_BEGIN = "<!-- FILMS:BEGIN 由 tools/build_index.py 自动生成，不要手改 -->"
FILM_END = "<!-- FILMS:END -->"

# 标题按 · 切开以后，名字后面单独的那一段；后面可以带一个括号里的版本记号
FILM_SPLIT = re.compile(r"\s*[·・•|｜]\s*")
FILM_SEG = re.compile(r"^小萌物短片\s*(?:[（(【\[〔].*)?$")

# 标题认出来了、但不是片子的
FILM_SKIP = {
    "claude/盲盒/小萌物片单.html",      # 片单自己
}
# 标题认不出、但确实是小萌物短片的（优先级最高）
FILM_EXTRA = set()

# 文件名尾巴上的作者记号：AGENTS.md 说的 -build、-codex，反重力按芯加的 -gemini、-opus
# 和别的模型名。只认这张表里的词，从尾巴往前一个个剥，照文件名原样显示，不替它解释；
# 跟所在小机同名的（gemini/ 里的 -gemini）、标题括号里已经写了的（（build版））不重复写。
# 新的记号往这里加一个词。
FILM_MARKS = re.compile(
    r"[-_ ]?(build|codex|opus|gemini|argon|carbon|studio|stiudo|playground|canvas|gpt\d*)$",
    re.I)
# 各家壳子默认带的那个记号也不写：grok 的片子大多带 -build，gpt 的几乎都带 -codex（AGENTS.md 定的），
# 每行都写一遍等于没写。剩下的 argon、opus、carbon 这些才是「这部具体是谁拍的」。
FILM_HOUSE_MARK = {"grok": "build", "gpt": "codex"}

# 日子按 UTC+8 切：店里大半提交是这个时区的，同一晚推的几部才不会被劈到两天。
FILM_TZ = timezone(timedelta(hours=8))
WEEK_ZH = "一二三四五六日"
WEEK_EN = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
MONTH_EN = ("January", "February", "March", "April", "May", "June", "July",
            "August", "September", "October", "November", "December")

# 用更安全的范围，避免 Python 3.14 的 bad character range 错误
EMOJI = re.compile(
    "[\U0001F000-\U0001FAFF"
    "\U0001F1E6-\U0001F1FF"
    "☀-➿"
    "←-⇿"
    "⤀-⥿"
    "︀-️]"
)


def clean(text):
    text = EMOJI.sub("", str(text))
    text = re.sub(r"\s+", " ", text)
    return text.strip(" ·、|-–—\t")


def prettify(filename):
    return clean(re.sub(r"\.(html?|svg)$", "", filename, flags=re.I).replace("-", " ").replace("_", " "))


def _decomment(text):
    """把 HTML 注释剥掉再去找标题和附注。

    2026-09-19 栽的：A 的嘟嘟机那一页开头写了一段说明，里面提到
    「只动了三处：<title>（原稿是「嘟嘟机」）换成货架用的名字」——
    注释里出现的这三个字也是 <title>，正则就从那儿开始一路匹配到真正的
    </title>，把整段说明连同 <head> 全当成了标题。首页上挂出来一长串。
    谁以后在注释里讲 <title> 或者 description 都会再炸一次，所以在这儿修。

    前 12000 字节可能正好切在一段注释中间，那就没有 --> 可配；浏览器遇到
    没闭合的注释也是把后面全部当注释，所以照做，从 <!-- 那儿截断。
    """
    text = re.sub(r"<!--[\s\S]*?-->", " ", text)
    cut = text.find("<!--")
    return text if cut < 0 else text[:cut]


def page_head(path):
    """页面开头 12000 字节，注释已剥掉。标题和附注都从这一段里找。"""
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            return _decomment(fh.read(12000))
    except OSError:
        return ""


def page_title(head):
    m = re.search(r"<title[^>]*>([\s\S]*?)</title>", head, re.I)
    return clean(html.unescape(m.group(1))) if m else ""


LIMIT = 46   # 一行简介最多这么长；再长就在最近的一个标点上收住


def _short(text):
    """把一句简介收拾干净：折掉换行、去掉首尾空白，太长就在标点上断，补省略号。

    直接按字数硬切会切在半个词中间（「新收录影壳蜗与月光」），所以先找
    LIMIT 之前最后一个句读，从那儿断。找不到句读才硬切。
    """
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= LIMIT:
        return text
    cut = max(text.rfind(ch, 0, LIMIT) for ch in "。；;，,、！？!?·… ")
    if cut < LIMIT // 2:
        cut = LIMIT
    return text[:cut].rstrip("，,、；;·… ") + "…"


def page_blurb(head):
    """页面自己写的一句简介：<meta name="description" content="…">。

    没写就返回空字符串——首页那一行不出现，不报错。这样她以后新加
    文件只写 <title> 也能用，简介是可选的。
    表情符号这里不去（跟 <title> 不一样）——简介是给人看的一句话，
    去掉表情反而怪。
    """
    m = re.search(
        r"""<meta[^>]*\bname\s*=\s*['"]description['"][^>]*>""", head, re.I)
    if not m:
        return ""
    c = re.search(r"""\bcontent\s*=\s*(['"])([\s\S]*?)\1""", m.group(0), re.I)
    if not c:
        return ""
    return _short(html.unescape(c.group(2)))


def svg_blurb(head):
    """SVG 没有 <meta>，它自己的那一行叫 <desc>。读法一样，读不到就空。"""
    m = re.search(r"<desc[^>]*>([\s\S]*?)</desc>", head, re.I)
    if not m:
        return ""
    return _short(re.sub(r"<[^>]+>", "", m.group(1)))


def list_pages():
    out = subprocess.run(
        ["git", "-c", "core.quotepath=false", "ls-files", "*.html", "*.svg"],
        cwd=ROOT, capture_output=True, text=True, check=True).stdout
    pages = []
    for rel in out.split("\n"):
        if not rel or rel == "index.html":
            continue
        if rel.split("/")[0].startswith(".") or rel.startswith("tools/"):
            continue
        if rel in SKIP_LIST:
            continue
        pages.append(rel)
    return pages


def sort_key(name):
    # 中文按拼音排不了（标准库没有），退而求其次：按 Unicode 码位，
    # 但让纯 ASCII 开头的排在前面，跟原来的观感一致。
    return (0 if name[:1].isascii() else 1, name)

def display_folder(rel):
    """首页一级门牌：顶层目录名。小机/货架/文件.html 也归到小机，
    不让「grok/哄睡」自己开一扇门。"""
    folder = os.path.dirname(rel) or "."
    top = folder.split("/")[0]
    return top if top in ORDER else folder


def _variants(e, by_folder):
    """撞名了要加什么后缀，从好看的往难看的排。"""
    base = e["name"]
    if by_folder:
        yield f"{base}（{e['raw_folder'].split('/')[0]} 版）"
    yield f"{base}（{os.path.splitext(os.path.basename(e['path']))[0]}）"
    n = 2
    while True:
        yield f"{base} · {n}"
        n += 1


def dedupe_names(entries):
    """两个页面在首页上显示成同一个名字，就自动加后缀分开，并且把撞车的报出来。

    以前这里是直接报错退出、拒绝生成的。结果是首页不更新，还发一封
    看不懂的失败邮件——而改名、拆版本这些事的中间那一两个提交里
    出现重名是很正常的，下一个提交就没了。不值得为它红一次。
    现在照常生成，只是把撞车的名字打出来，提醒去改各自的 <title>。
    """
    groups = {}
    for e in entries:
        groups.setdefault(e["name"], []).append(e)

    taken = {n for n, g in groups.items() if len(g) == 1}
    clashes = []
    for name in sorted(n for n, g in groups.items() if len(g) > 1):
        members = groups[name]
        folders = {e["raw_folder"].split("/")[0] for e in members}
        by_folder = len(folders) == len(members)   # 各在各的目录，用目录名区分最好看
        for e in members:
            for cand in _variants(e, by_folder):
                if cand not in taken:
                    break
            taken.add(cand)
            e["name"] = cand
        clashes.append((name, [(e["path"], e["name"]) for e in members]))
    return clashes


def build_entries():
    entries = []
    for rel in list_pages():
        head = page_head(os.path.join(ROOT, rel))
        name = DISPLAY_NAME.get(rel) or page_title(head) or prettify(os.path.basename(rel))
        entries.append({
            "path": rel,
            "folder": display_folder(rel),
            "raw_folder": os.path.dirname(rel) or ".",
            "name": name,
            # 撞名加后缀之前的样子：dedupe_names 只改 name。片单要的是片子自己的名字，
            # 不要首页为了分开同名片加的「（grok 版）」。
            "title": name,
            "blurb": svg_blurb(head) if rel.lower().endswith(".svg") else page_blurb(head),
        })
    return entries


def group(entries):
    buckets = {}
    for e in entries:
        buckets.setdefault(e["folder"], []).append(e)

    # 货架可以先立起来，页后到：ORDER 里的顶层只要在磁盘上存在，
    # 就算一件都没有也出一块门牌。不然她把文件夹建好了、首页上什么都看不见，
    # 会以为没生效。（pluto 2026-09-19 就是这么开张的。）
    for folder in ORDER:
        if os.path.isdir(os.path.join(ROOT, folder)):
            buckets.setdefault(folder, [])

    def gkey(folder):
        return (ORDER.index(folder), "") if folder in ORDER else (len(ORDER), folder)

    blocks = []
    for folder in sorted(buckets, key=gkey):
        items = sorted(buckets[folder], key=lambda e: sort_key(e["name"]))
        blocks.append((folder, items))
    return blocks


def splice(src, begin, end, fresh):
    """把 src 里 begin 到 end 那一段（连同这两个标记）换成 fresh。"""
    return re.sub(re.escape(begin) + r"[\s\S]*?" + re.escape(end), lambda _: fresh, src)


def encode_path(rel):
    return "/".join(quote(part) for part in rel.split("/"))


def shelf_of(e):
    """这一页在哪个抽屉；平铺的顶层（pluto）没有抽屉，返回空串。

    一页只在一个抽屉，只看文件夹：claude/哄睡/xx.html 就是「哄睡」，
    抽屉名认不出的进「盲盒」。想换货架，把文件挪到另一个抽屉。
    """
    if e["folder"] in FLAT_FOLDERS:
        return ""
    if e["raw_folder"] in SUBFOLDER_CAT:
        return SUBFOLDER_CAT[e["raw_folder"]]
    parts = e["path"].split("/")
    if len(parts) >= 3 and parts[1] in CAT_ORDER:
        return parts[1]
    return "盲盒"


def render_items(lines, items, indent):
    """条目只写名字和链接，不带任何动画参数。

    2026-08-28：以前每个 li 上都挂一个 style="--delay:NNNms" 做逐条淡入，
    条目的起点是「完全看不见」。iPhone 上 Safari 跑不完几百条动画，
    会有一批永远卡在半透明，看起来像被吸顶的牌子盖住了。
    现在条目一开始就是实的，不依赖动画。别加回去。
    """
    pad = " " * indent
    for e in items:
        blurb = e.get("blurb") or ""
        tail = (f'<span class="blurb">{html.escape(blurb, quote=True)}</span>'
                if blurb else "")
        lines.append(
            f'{pad}<li class="item">'
            f'<a href="{encode_path(e["path"])}">{html.escape(e["name"], quote=True)}</a>'
            f'{tail}</li>')


def render(blocks):
    esc = lambda s: html.escape(s, quote=True)
    lines = [BEGIN]
    for folder, items in blocks:
        dot, tint = PALETTE.get(folder, PALETTE_DEFAULT)
        lines.append(f'  <details class="group" style="--dot:{dot};--tint:{tint}">')
        lines.append(f'    <summary class="tag">{esc(folder)}</summary>')
        if not items:
            # 空货架：点开一片空白会像坏了，摆一句话在那儿等第一件。
            lines.append('    <p class="soon">还没有页。</p>')
        elif folder in FLAT_FOLDERS:
            lines.append('    <ul class="list">')
            render_items(lines, items, 6)
            lines.append("    </ul>")
        else:
            # items 已经按名字排好，分进各抽屉后顺序不变，不用再排
            buckets = {}
            for e in items:
                buckets.setdefault(shelf_of(e), []).append(e)
            shelves = CAT_ORDER + sorted(c for c in buckets if c not in CAT_ORDER)
            for c in shelves:
                sub = buckets.get(c, [])
                # 抽屉已经建了、还一件都没有：也出牌子，摆一句话在那儿等第一件
                if not sub and not os.path.isdir(os.path.join(ROOT, folder, c)):
                    continue
                lines.append('    <details class="pack">')
                # 货架名原样显示。2026-08-28 撤掉过「两个字中间补全角空格」的对齐，
                # 她看过实物说不要。别再加回去。
                lines.append(f'      <summary class="pack-tag">{esc(c)}</summary>')
                if not sub:
                    lines.append('      <p class="soon">还没有页。</p>')
                else:
                    lines.append('      <ul class="list">')
                    render_items(lines, sub, 8)
                    lines.append("      </ul>")
                lines.append("    </details>")
        lines.append("  </details>")
    lines.append(END)
    return "\n".join(lines)


def phone_lines(entries):
    """挑出店里所有的电话页面，排好序，给总机当线路表。"""
    by_path = {e["path"]: e for e in entries}
    picked = []
    for rel, e in by_path.items():
        if rel in PHONE_SKIP:
            continue
        if rel in PHONE_EXTRA:
            picked.append(rel)
            continue
        if shelf_of(e) in PHONE_SHELF_SKIP:
            continue
        if PHONE_KW.search(e["name"]) or PHONE_KW.search(e["blurb"]):
            picked.append(rel)

    order = {rel: i for i, rel in enumerate(PHONE_ORDER)}
    picked.sort(key=lambda r: (order.get(r, len(order)), r))

    lines = []
    for i, rel in enumerate(picked, 1):
        e = by_path[rel]
        machine = rel.split("/")[0]
        shelf = shelf_of(e)
        where_zh = f"{machine} · {shelf}" if shelf else machine
        where_en = f"{machine} · {SHELF_EN.get(shelf, shelf)}" if shelf else machine
        en_who, en_said = PHONE_EN.get(rel, (e["name"], e["blurb"]))
        # 总机在 claude/盲盒/ 里，链接要先退两级回到仓库根
        lines.append({
            "n": f"{i:03d}",
            "href": "../../" + encode_path(rel),
            "zh": {"who": e["name"], "where": where_zh, "said": e["blurb"]},
            "en": {"who": en_who, "where": where_en, "said": en_said},
        })
    return lines


def write_phone_lines(entries, check_only=False):
    """把线路表写进总机那一页。那个文件不在就当没这回事，不报错。"""
    if not os.path.exists(PHONE_PAGE):
        return 0, None
    lines = phone_lines(entries)
    payload = json.dumps(lines, ensure_ascii=False, separators=(",", ":"))
    payload = payload.replace("<", "\\u003c")   # 免得内容里冒出 </script>
    fresh = (PHONE_BEGIN + '\n<script id="lines" type="application/json">'
             + payload + "</script>\n" + PHONE_END)

    src = open(PHONE_PAGE, encoding="utf-8").read()
    if PHONE_BEGIN not in src or PHONE_END not in src:
        print("总机那一页找不到 LINES 标记，线路表没写进去", file=sys.stderr)
        return 0, None
    new = splice(src, PHONE_BEGIN, PHONE_END, fresh)
    if new == src:
        return len(lines), False
    if not check_only:
        open(PHONE_PAGE, "w", encoding="utf-8").write(new)
    return len(lines), True


def film_parts(title):
    """「名字 · 副标题 · 小萌物短片（版本）」拆成 (名字, 副标题, 版本)；不是片子返回 None。

    名字是第一段；「小萌物短片」那一段前面的都算副标题（「守株待兔 · 兔已到，请轻声」）；
    它自己括号里的、它后面还有的，算版本记号（「（build版）」「（游戏特别篇）」）。
    """
    segs = [s for s in FILM_SPLIT.split(title) if s]
    for k in range(1, len(segs)):
        if FILM_SEG.match(segs[k]):
            ver = " · ".join([segs[k][len("小萌物短片"):].strip()] + segs[k + 1:])
            return segs[0], " · ".join(segs[1:k]), ver.strip(" ·")
    return None


def film_marks(rel, ver):
    """文件名尾巴上的作者记号，照文件名原样、按原来的先后（尾声argon-opus-carbon → argon、opus、carbon）。"""
    stem = os.path.splitext(os.path.basename(rel))[0]
    marks = []
    m = FILM_MARKS.search(stem)
    while m:
        marks.insert(0, m.group(1))
        stem = stem[:m.start()]
        m = FILM_MARKS.search(stem)
    top, low = rel.split("/")[0].lower(), ver.lower()
    skip = {top, FILM_HOUSE_MARK.get(top, top)}
    return [w for w in marks if w.lower() not in skip and w.lower() not in low]


def film_history():
    """现存的每个文件，它那一部最早哪一刻进的店（Unix 秒，提交时间）。读不到完整历史返回 None。

    一次 git log 从最早读到最新，每一支文件记一个「哪天进的店」：
      · 改名、挪抽屉：git 在同一个提交里配成改名的（-M90%，内容至少九成一样），沿用原来那天。
        11-25 codex/ 整个改名成 gpt/ 就靠这个，不顺着认，那四十来部全成了 11-25。
        门槛不用默认的五成：好几部片共用一套骨架，彼此五六成像，配错了新片会冒领老片的日子。
      · 网页上先往博物馆传一份、隔一分钟再删掉小卡里那份（挪进博物馆常这么做），是两个提交，
        git 配不上。所以按内容认：删掉的那份跟先前新传的那份一字不差、中间也没再改过，
        就当是同一部挪了个地方；先删、后原样传回来的也一样。
      · 同一个文件名删了又传一份不一样的，算新片：店里有不少 gemini-code-…、r41-… 这种通用名。
    只看提交时间，跟今天几号无关，同一份历史跑几遍都一样。合并提交本身不算，分支上的提交各算各的。
    """
    try:
        shallow = subprocess.run(["git", "rev-parse", "--is-shallow-repository"], cwd=ROOT,
                                 capture_output=True, text=True, check=True).stdout.strip()
        if shallow == "true":
            return None
        raw = subprocess.run(
            ["git", "-c", "core.quotepath=false", "log", "-z", "--raw", "--no-abbrev", "--root",
             "--no-color", "--no-show-signature", "--topo-order", "--reverse", "-M90%",
             "--format=%x01%ct"],
            cwd=ROOT, capture_output=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        return None

    commits, toks, i = [], raw.decode("utf-8", "surrogateescape").split("\0"), 0
    try:
        while i < len(toks):
            tok = toks[i].lstrip("\n")
            i += 1
            if tok.startswith("\x01"):
                commits.append((int(tok[1:]), []))
            elif tok.startswith(":") and commits:
                f = tok[1:].split(" ")          # 原权限 新权限 原内容 新内容 状态
                st = f[4][:1]
                k = 2 if st in ("R", "C") else 1
                paths = toks[i:i + k]
                if not st or len(paths) < k:
                    raise ValueError(tok)
                commits[-1][1].append((st, f[2], f[3], paths))
                i += k
    except (ValueError, IndexError):
        return None                             # 读到的不是预想的样子：当作读不到历史

    live, alive = {}, set()     # 文件名 → 这一支的编号；还在店里的那些支
    born, blob = {}, {}         # 编号 → 进店那一刻 / 现在的内容
    holders, tomb = {}, {}      # 内容 → 现在是这份内容的那些支 / 删掉时是这份内容的最早进店时间
    copies = {}                 # 编号 → [(照它原样新传的那一支, 当时的内容)]

    def start(path, ct, content):
        lid = len(born) + 1
        live[path] = lid
        alive.add(lid)
        born[lid], blob[lid] = min(ct, tomb.get(content, ct)), content
        for src in holders.get(content, ()):
            copies.setdefault(src, []).append((lid, content))
        holders.setdefault(content, set()).add(lid)
        return lid

    def retarget(lid, old, new):
        holders.get(old, set()).discard(lid)
        holders.setdefault(new, set()).add(lid)
        blob[lid] = new
        copies.pop(lid, None)   # 它改过了，之前照它传的那几份就是各自的新片，不算挪

    for ct, changes in commits:
        # 同一个提交里 git 没配成改名的，先把删掉的记下，新加的才认得出来
        changes.sort(key=lambda c: c[0] != "D")
        for st, old, new, paths in changes:
            if st in "AC":
                start(paths[-1], ct, new)
            elif st == "R":
                # 从哪来的在历史里没见过（合并提交里冒出来的那种），就当这一刻进的店
                lid = live.pop(paths[0], None) or start(paths[0], ct, old)
                live.pop(paths[0], None)
                live[paths[1]] = lid
                if old != new:
                    retarget(lid, old, new)
            elif st in "MT":
                lid = live.get(paths[0]) or start(paths[0], ct, old)
                if old != new:
                    retarget(lid, old, new)
            elif st == "D":
                lid = live.pop(paths[0], None)
                if lid is None:
                    continue
                alive.discard(lid)
                holders.get(old, set()).discard(lid)
                tomb[old] = min(tomb.get(old, born[lid]), born[lid])
                for twin, content in copies.pop(lid, ()):
                    if content == old and twin in alive:
                        born[twin] = min(born[twin], born[lid])
    return {path: born[lid] for path, lid in live.items()}


FILM_ROW = re.compile(r'<li\b[^>]*\bdata-t="(\d+)"[^>]*>\s*<a\b[^>]*\bhref="(?:\.\./)*([^"]+)"')


def film_ledger(src):
    """片单里已经写着的日子（文件名 → Unix 秒）。读不到完整历史的时候拿它垫底，日子不乱跳。"""
    i = src.find(FILM_BEGIN)
    j = src.find(FILM_END, i + 1) if i >= 0 else -1
    if j < 0:
        return {}
    return {unquote(html.unescape(href)): int(t) for t, href in FILM_ROW.findall(src[i:j])}


def film_rows(entries, src):
    """挑出店里所有的小萌物短片，配上进店的那一刻，新的在前；同一刻进的按文件名排。"""
    picked = []
    for e in entries:
        parts = film_parts(e["title"])
        if e["path"] in FILM_EXTRA:
            parts = parts or (e["title"], "", "")
        elif e["path"] in FILM_SKIP or parts is None:
            continue
        picked.append((e, parts))

    hist = film_history() if picked else None
    ledger = film_ledger(src)
    rows = []
    for e, (name, sub, ver) in picked:
        rel = e["path"]
        t = (hist or {}).get(rel) or ledger.get(rel)
        if not t:
            # 还没提交的新片，历史里没有它：先拿文件的修改时间顶着，提交上去 Actions 会重算成提交那一刻。
            try:
                t = int(os.path.getmtime(os.path.join(ROOT, rel)))
            except OSError:
                t = 0
        shelf = shelf_of(e)
        rows.append({
            "path": rel, "t": t, "name": name, "sub": sub, "ver": ver,
            "maker": e["folder"], "marks": film_marks(rel, ver),
            "shelf": "" if shelf == "小卡" else shelf,   # 片子大多在小卡，只标不在小卡的
        })
    rows.sort(key=lambda r: (-r["t"], r["path"]))
    return rows


def _rgba(color, alpha):
    h = color.lstrip("#")
    return f"rgba({int(h[0:2], 16)},{int(h[2:4], 16)},{int(h[4:6], 16)},{alpha})"


def render_films(rows):
    """片单那一段：每家的颜色、一句总数、各家几部，再按月、按天一行一部。

    整段是纯 HTML，关了 JS 也是全的；那一页的脚本只在上面加筛选、倒序、记看过。
    每行的 data-t 是进店那一刻（Unix 秒），读不到历史时 film_ledger 从这儿读回去，别删。
    """
    esc = lambda s: html.escape(str(s), quote=True)
    tag = lambda m: "mk-" + re.sub(r"[^a-z0-9_-]", "_", m.lower())
    day_of = lambda t: datetime.fromtimestamp(t, FILM_TZ)
    up = "../" * len(os.path.relpath(os.path.dirname(FILM_PAGE), ROOT).split(os.sep))
    makers = sorted({r["maker"] for r in rows},
                    key=lambda m: (ORDER.index(m), "") if m in ORDER else (len(ORDER), m))

    out = [FILM_BEGIN]
    # 每家一个颜色，跟首页门牌同一张 PALETTE：白天垫在名字底下，夜里直接拿来写字
    out.append("<style>" + "".join(
        f".{tag(m)}{{--dot:{PALETTE.get(m, PALETTE_DEFAULT)[0]};"
        f"--pill:{_rgba(PALETTE.get(m, PALETTE_DEFAULT)[0], .34)};"
        f"--pill-dim:{_rgba(PALETTE.get(m, PALETTE_DEFAULT)[0], .16)}}}" for m in makers) + "</style>")

    if rows:
        first, last = day_of(rows[-1]["t"]), day_of(rows[0]["t"])
        yr = first.year != last.year
        zh_d = lambda d: (f"{d.year} 年 " if yr else "") + f"{d.month} 月 {d.day} 日"
        en_d = lambda d: f"{MONTH_EN[d.month - 1][:3]} {d.day}" + (f", {d.year}" if yr else "")
        zh = f"一共 {len(rows)} 部。头一部 {zh_d(first)}进店，最新一部是 {zh_d(last)}。"
        en = (f"{len(rows)} films. The first one came in on {en_d(first)}. "
              f"The newest one came in on {en_d(last)}.")
    else:
        zh, en = "还没有片子。", "No films yet."
    out.append(f'<p class="tally" data-en="{esc(en)}">{esc(zh)}</p>')

    count = Counter(r["maker"] for r in rows)
    out.append('<p class="makers" id="makers">' + "".join(
        f'<span class="mk {tag(m)}"><b>{esc(m)}</b><span class="c">{count[m]}</span></span>'
        for m in makers) + "</p>")

    per_day = Counter(day_of(r["t"]).strftime("%Y-%m-%d") for r in rows)
    out.append('<div class="reel" id="reel">')
    mon = day = None
    for r in rows:
        d = day_of(r["t"])
        if d.strftime("%Y-%m-%d") != day:
            if day:
                out.append("</ol></section>")
            if d.strftime("%Y-%m") != mon:
                if mon:
                    out.append("</section>")
                mon = d.strftime("%Y-%m")
                out.append(f'<section class="mon" data-mon="{mon}">')
                out.append(f'<h2 class="mh"><span class="mz" data-en="{MONTH_EN[d.month - 1]}">'
                           f'{d.month} 月</span><span class="my">{d.year}</span></h2>')
            day = d.strftime("%Y-%m-%d")
            n = per_day[day]
            out.append(f'<section class="day" data-day="{day}">')
            out.append(f'<h3 class="dh"><time datetime="{day}">{d.month:02d}-{d.day:02d}</time>'
                       f'<span class="wd" data-en="{WEEK_EN[d.weekday()]}">周{WEEK_ZH[d.weekday()]}</span>'
                       f'<span class="dn" data-en="{n} film{"" if n == 1 else "s"}">{n} 部</span></h3>')
            out.append('<ol class="rows">')

        title = f'<span class="t">{esc(r["name"])}'
        if r["sub"]:
            title += f'<span class="sub"> · {esc(r["sub"])}</span>'
        if r["ver"]:
            ver = r["ver"] if r["ver"][:1] in "（([【〔" else " · " + r["ver"]
            title += f'<span class="ver">{esc(ver)}</span>'
        title += "</span>"
        by = f'<b>{esc(r["maker"])}</b>'
        if r["marks"]:
            by += f'<span class="mark">{esc(" · ".join(r["marks"]))}</span>'
        if r["shelf"]:
            by += (f'<span class="at" data-en="{esc(SHELF_EN.get(r["shelf"], r["shelf"]))}">'
                   f'{esc(r["shelf"])}</span>')
        cls = f'f {tag(r["maker"])}' + (" mu" if r["shelf"] == "博物馆" else "")
        out.append(f'<li class="{cls}" data-t="{r["t"]}"><a href="{up}{encode_path(r["path"])}">'
                   f'{title}<span class="by">{by}</span></a></li>')
    if day:
        out.append("</ol></section></section>")
    out.append("</div>")
    out.append(FILM_END)
    return "\n".join(out)


def write_film_list(entries, check_only=False):
    """把片单写进那一页。那个文件不在就当没这回事，不报错。"""
    if not os.path.exists(FILM_PAGE):
        return 0, None
    src = open(FILM_PAGE, encoding="utf-8").read()
    if FILM_BEGIN not in src or FILM_END not in src:
        print("小萌物片单那一页找不到 FILMS 标记，片单没写进去", file=sys.stderr)
        return 0, None
    # 片单是顺带的：它这一段哪儿出了岔子，只留一条警告、沿用上一版，不许连累首页清单，
    # 也不为它发失败邮件（同工作流里抽小萌物画法那一步）。
    try:
        rows = film_rows(entries, src)
        fresh = render_films(rows)
    except Exception as exc:
        print(f"::warning::小萌物片单这次没生成成（{type(exc).__name__}: {exc}），沿用上一版", file=sys.stderr)
        return 0, None
    new = splice(src, FILM_BEGIN, FILM_END, fresh)
    if new == src:
        return len(rows), False
    if not check_only:
        open(FILM_PAGE, "w", encoding="utf-8").write(new)
    return len(rows), True


def main():
    entries = build_entries()
    clashes = dedupe_names(entries)
    blocks = group(entries)

    if clashes:
        report = ["显示名撞车了，已经自动加后缀分开。想要好看的名字，去改各自的 <title>（名字在 DISPLAY_NAME 里的就改那一行，别加新行）："]
        for name, members in clashes:
            report.append(f"  「{name}」")
            for path, final in members:
                report.append(f"      {path}  →  {final}")
        text = "\n".join(report)
        print(text, file=sys.stderr)
        summary = os.environ.get("GITHUB_STEP_SUMMARY")
        if summary:
            with open(summary, "a", encoding="utf-8") as fh:
                fh.write("### 显示名撞车（已自动加后缀，首页照常更新）\n\n```\n" + text + "\n```\n")

    src = open(INDEX, encoding="utf-8").read()
    if BEGIN not in src or END not in src:
        print("index.html 里找不到 LIST 标记，无法写入", file=sys.stderr)
        return 3
    new = splice(src, BEGIN, END, render(blocks))

    if "--check" in sys.argv:
        n_lines, phone_stale = write_phone_lines(entries, check_only=True)
        n_films, films_stale = write_film_list(entries, check_only=True)
        if new != src:
            print("index.html 需要重新生成（跑 python3 tools/build_index.py）", file=sys.stderr)
            return 1
        if phone_stale:
            print("总机的线路表需要重新生成（跑 python3 tools/build_index.py）", file=sys.stderr)
            return 1
        if films_stale:
            print("小萌物片单需要重新生成（跑 python3 tools/build_index.py）", file=sys.stderr)
            return 1
        print(f"index.html 是最新的（{len(entries)} 个页面，总机 {n_lines} 条线路，片单 {n_films} 部）")
        return 0

    n_lines, phone_changed = write_phone_lines(entries)
    if phone_changed:
        print(f"总机线路表已更新：{n_lines} 条")
    n_films, films_changed = write_film_list(entries)
    if films_changed:
        print(f"小萌物片单已更新：{n_films} 部")

    if new == src:
        print(f"index.html 无需改动（{len(entries)} 个页面）")
        return 0

    open(INDEX, "w", encoding="utf-8").write(new)
    print(f"index.html 已更新：{len(entries)} 个页面，{len(blocks)} 个分组")
    for folder, items in blocks:
        print(f"  {folder}/  {len(items)} 个")
        if folder not in FLAT_FOLDERS:
            cc = Counter(shelf_of(e) for e in items)
            for c in CAT_ORDER:
                if cc[c]:
                    print(f"    {c}  {cc[c]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
