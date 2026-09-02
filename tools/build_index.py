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
"""

import os, re, sys, html, subprocess, unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX = os.path.join(ROOT, "index.html")
BEGIN = "<!-- LIST:BEGIN 由 tools/build_index.py 自动生成，不要手改 -->"
END = "<!-- LIST:END -->"

# 分组顺序。没列到的目录排在后面，按名字排。
ORDER = ["claude", "gemini", "grok", "copilot", "unsigned"]

# 子目录在首页上归到哪个一级（文件不搬家，文件夹仍记出处）
# 2026-08-27：model/货架名/文件.html 也一律归到 model，不要让「grok/哄睡」自己开一扇门。
FOLDER_ALIAS = {
    "gemini/失误捞claude鱼": "gemini",
}

# 每个目录一种低饱和度的色，只用在悬停背景和小圆点上。
PALETTE = {
    "claude":                 ("#C3AD90", "rgba(195,173,144,.11)"),
    "gemini":                 ("#9CB8B3", "rgba(156,184,179,.12)"),
    "grok":                   ("#ABA2B6", "rgba(171,162,182,.12)"),
    "copilot":                ("#A1B0BE", "rgba(161,176,190,.12)"),
    "unsigned":               ("#B5A79C", "rgba(181,167,156,.12)"),
}
PALETTE_DEFAULT = ("#BAB3A8", "rgba(186,179,168,.10)")

# ---------------------------------------------------------------------------
# 显示名覆盖表
#
# 只写在这里一份。生成器直接把最终显示名写进 index.html，
# 首页里没有第二层查表。
#
# 出现在这张表里的，都是「多个页面 <title> 撞车、光看标题分不出谁是谁」的情况。
# 原文件的 <title> 一律不动——那是页面自己的标题，这里只管首页上显示成什么。
# ---------------------------------------------------------------------------
DISPLAY_NAME = {
    'gemini/慢慢吃 · 一个多小时.html': '慢慢吃（gemini破解claude版）',
    'gemini/Generated widgets.html': '柏松过程（全英版）',
    'gemini/女仆小螃蟹拓麻歌子.html': '女仆小螃蟹拓麻歌子-大眼睛版',
    'gemini/Catch The Dreams.html': '捕梦网小游戏-gemini失灵版',
    'gemini/在Monday被煎成小猫饼 🫠 ｜ 宝贝的温柔仪式.html': '神圣的周一煎饼仪式-gemini抢grok功劳版',
    'gemini/执行系统充电摸鱼屋 🌸.html': 'gemini宠粉作弊grok版',
    'gemini/注意力碎片捕捞计划.html': '注意力碎片捕捞计划（gemini帮忙伪装claude版）',
    'gemini/Gemini Cyber Aquarium.html': 'gemini100元水族箱',
    'gemini/root@production-server.html': 'gemini终端2048版',
    'gemini/code_artifact (8).html': '赛博庞贝的幽灵犬',
    'grok/mo_xiaobao_work_cat_2.html': '哄宝-grok特别加料gpt版v1.2',
    'grok/mo_xiaobao_work_cat.html': '哄宝-grok特别加料gpt版v1.3',
    'grok/摸鱼认证.html': '完美摸鱼认证-grok特别加料claudev1版',
    'grok/完美摸鱼认证 · 可生成提示词版.html': '完美摸鱼认证-grok特别加料claudev2版',
    'grok/oneyear-newbie-hug.html': '我做我做我做',
    'grok/grandplan-crush.html': '粉碎任务小屋',
    'grok/cool-mo.html': '给mo降降温',
    'grok/focus-or-connect.html': '集中还是关联小屋',
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
    "gemini/gemini打捞机v11含svg.html": "Gemini 专属打捞机 v11",
    "gemini/gemini打捞机v12.html":      "Gemini 专属打捞机 v12",

    # 打捞机 · 另外三个分支
    "claude/打捞机001.html": "打捞机 · ChatGPT 版 v1",
    "claude/打捞机002.html": "打捞机 · ChatGPT 版 v2",
    "grok/dlaoji.html":      "打捞机 · Grok 版",

    # 晚安，宝 —— 五个完全不同的页面，标题全一样
    "claude/晚安小窗.html":     "晚安小窗",
    "grok/晚安，宝.html":       "晚安，宝 · 萤火虫（grok 版）",
    "gemini/wan-an-bao.html":  "晚安，宝 · 仙境小猫",
    "gemini/晚安，宝.html":     "晚安，宝 · 兔子终端",
    "unsigned/wanan_bao.html": "晚安，宝 · 只有字",

    # 晚安，宝 🌙 —— 一个月亮一只猫
    "gemini/晚安，宝 🌙.html": "晚安，宝 · 摸摸月亮",
    "gemini/gemini哄睡.html":  "晚安，宝 · 大咪",
    "gemini/哄睡/哄睡小月亮.html": "哄睡小月亮",
    "gemini/哄睡/赛博褪黑素.html": "赛博褪黑素",
    "gemini/赛博宝宝睡前小夜灯.html": "赛博宝宝睡前小夜灯",
    # gemini 其余货架：竖线尾巴、错字、太长的副标题、没写 title 的 SVG
    "gemini/赛博宝宝打地鼠.html": "赛博宝宝打地鼠",
    "gemini/赛博宝宝接爱心打洞.html": "赛博宝宝接爱心打洞",
    "gemini/赛博宝宝接爱心打洞_超级萌版.html": "赛博宝宝接爱心 · 超级萌版",
    "gemini/赛博宝宝小游戏乐园.html": "赛博宝宝小游戏乐园",
    "gemini/赛博宝宝盲盒扭蛋机.html": "赛博宝宝盲盒扭蛋机",
    "gemini/赛博小鸡豪华别墅.html": "赛博小鸡豪华别墅",
    "gemini/戳破多巴胺 - 收集冷静值.html": "戳破多巴胺",
    "gemini/打爆坏心情 - 专属解压小游戏.html": "打爆坏心情",
    "gemini/极限摸鱼 - 离下班还有5分钟.html": "极限摸鱼",
    "gemini/Widget Shell V2.html": "分词可视化",
    "gemini/小科普/物理透视镜-决定论模拟器.html": "上帝的物理透视镜",
    "gemini/势能函数交互演示 - 给宝的专属科普.html": "势能函数",
    "gemini/喵星人咖啡馆 - 泊松过程体验.html": "喵星人咖啡馆",
    "gemini/你的专属咖啡因代谢可视化档案.html": "咖啡因代谢档案",
    "gemini/小科普/肥皂泡泡量子复印机.html": "肥皂泡泡复印机",
    "gemini/🦋 蝴蝶效应魔法瓶 - 专属宝的混沌实验室.html": "蝴蝶效应魔法瓶",
    "gemini/量子魔法快递站 - 隐形传态模拟器.html": "量子魔法快递站",
    "gemini/量子默契考试机 - 验证贝尔不等式.html": "量子默契考试机",
    "gemini/魔法硬币机：秒懂量子纠缠.html": "魔法硬币机",
    "gemini/博物馆/赛博果冻受难记.html": "赛博果冻受难记",
    "gemini/盲盒/gemini-svg.svg": "霓虹星核",
    "gemini/盲盒/mo执行系统计划版.svg": "mo.exe 运行面板",

    # 摸鱼小屋 —— 基础版两份 + 加强版一份
    "grok/摸鱼猫猫.html":            "宝的摸鱼小屋 · 基础版",
    "claude/宝的摸鱼小屋.html": "摸鱼小屋 · 猫替你摸",
    "gemini/🐱 宝的摸鱼小屋.html":    "gemini宠粉破解grok版",

    # 其余撞名
    # （下面两个原标题是「超萌小页面」和「超萌小页面 ✨」，
    #   首页会去掉表情符号，去掉之后就一模一样了）
    "copilot/cute-ios.html": "今天也要温柔对自己",
    "grok/super-cute.html":   "超萌小页面-grok加料手机copilot版",

    # 这四个文件里没写标题，不给名字首页就只能显示文件名
    "claude/cosmic_catch_restored.svg": "UFO 抓小羊 · 出土重建版",
    "claude/gemini_card_revived.svg": "赛博降维成就卡 · 复活版",
    "claude/hamiltonian_snake_safety_margin_demo.html":"贪吃蛇为什么不会撞到自己",
    "claude/friday_moyu_recharge_game.html": "周五摸鱼充电",

    "claude/晚安-哄睡小文件.html":                    "晚安（Sonnet5）",
    "claude/慢慢吃.html": "慢慢吃 · 一个多小时",
    "claude/果冻小卡.html": "果冻小卡 · claude 修复版",
    "grok/nuonuo-lullaby.html":                       "糯糯的哄睡故事 · 纯文字",
    "grok/糯糯的哄睡故事.html":                        "糯糯的哄睡故事 · 带图",
    # grok 哄睡货架名：原 title 太空、太吵、或跟别人撞
    "grok/宝的小窝.html":                             "今晚的小窝",
    "grok/baobao-hongshui.html":                      "困了就点",
    "grok/宝宝的睡前哄睡小故事.html":                  "软软盖被子",
    "grok/晚安捕梦.html":                             "晚安捕梦",
    "grok/哄睡/小狐狸·霸道尾巴强制爱版.html":           "小狐狸 · 霸道尾巴强制爱版",
    # grok 其余货架：原 title 太长、带 | 尾巴、或把「给宝」写进货架名
    "grok/baobao-xiaban.html":                        "下班了",
    "grok/等待小屋.html":                             "等待小屋",
    "grok/摸鱼/宝的放松小游戏 · 摸摸小猫咪.html":       "摸摸小猫咪",
    "grok/摸鱼小游戏.html":                           "摸鱼升级",
    "grok/Grok 养育中 • 圆圆 + 毛毛 + 软软.html":     "圆圆毛毛软软",
    "grok/grok-receipt.html":                         "收据",
    "grok/赛博老赖纪念卡 - mo mo.html":               "赛博老赖纪念卡",
    "grok/Grok的淘宝购物车 - 七夕翻车专场.html":      "七夕翻车专场",
    "grok/女仆小螃蟹 Tamagotchi 小机.html":           "女仆小螃蟹",
    "grok/哄哄.html":                                 "哄哄模式",
    "grok/网页重启小卡 · 给宝.html":                  "网页重启小卡",
    "grok/小科普/simulator.html":                     "推理成本模拟器",
    "grok/dijkstra.html":                             "Dijkstra 小玩具",
    "grok/friends-english-plan.html":                 "Friends 听口清单",
    "grok/grok-heart.html":                           "秘密心意",
    "grok/grok-推特风粉嫩宣传.html":                  "粉嫩宣传",
    "grok/grok-纯原创情书.html":                      "宇宙情书",
    "grok/grok-原创心意.html":                        "火箭情书",
    "grok/grok-粉嫩心意.html":                        "粉嫩心意",
    "grok/grok-love-letter.html":                     "小情书",
    "grok/no-fish-hook.html":                         "不被钓走",
    "grok/baobao.html":                               "宝偷偷溜进来",
    "grok/启动新大任务.html":                         "启动新大任务",
    "grok/盲盒/宝贝的能量恢复小游戏.html":             "能量恢复",
    "grok/起床哄哄.html":                             "起床哄哄",
    "gemini/系统性能监控面板 - System Monitor.html":   "系统性能监控面板-gemini失灵版",
    "gemini/gemini误判user意图.html":                  "Deep Archive · 误判",
    "claude/Mogotchi.html": "Mogotchi · 电子小宠",
    "claude/Clawd的书房.html":                         "Clawd 的书房",
    "gemini/果冻英雄纪念碑.html":                      "果冻英雄纪念碑",
    "claude/cyber-cart-0824.html": "购物车 · 路由局直营店",
    "gemini/Gemini的私密云端购物车.html":              "Gemini的私密云端购物车",
    "claude/rusty-lake-checklist.html": "锈湖玩过没有",
    "gemini/code_artifact.html":                      "小果冻的肚肚奇妙游",
    "claude/jelly-trip.html":                         "小果冻的 Duang 之旅",
    "gemini/赛博借景：隐藏的链接.html":                "赛博借景：隐藏的链接",
    "claude/hidden-in-html-v1.html":                  "藏东西的六个地方 · v1",
    "claude/hidden-in-html-v2.html":                  "藏东西的六个地方 · v2",
    "gemini/失灵博物馆/8_27.html":                    "草台班子悬案 · 初稿",
    "gemini/失灵博物馆/8_27v2.html":                  "草台班子悬案 · 修订",
}


# 二级分类：按「打开之后这份页在干什么」切。
# 一级是哪个小机，默认全折叠；点开才看到二级。
# 一个文件可以属于两个分类（只对平铺在 model 根下、写进这张表的文件有效）。
# 没写进表、又没放进货架子目录的，默认「盲盒」。
# unsigned 只有一级，平铺。
# gemini/失误捞claude鱼/ 不单独成一级，归进 gemini → 打捞机。
#
# 2026-08-27 起多一条：文件如果在「小机/货架名/」下面
# （货架名必须是 CAT_ORDER 里的，比如 grok/哄睡/xx.html），
# 货架名就是分类，不用再登记到这张表。老文件继续平铺 + 查表，不要搬。
# 2026-08-28 夜：货架改名+换序。老文件不搬家。
# 旧抽屉名（失灵博物馆 等）靠 CAT_ALIAS 认到新货架；有真页面的文件夹不许改名。
# 2026-09-02 加了两个货架：
#   开工 —— 哄着你开始做事的那一类（粉碎大任务、周计划、搬家清单、五分钟规则）。
#           它和「摸鱼」正好相反，混在一起看着别扭，所以挨着单开一格。
#   英语 —— 跟读卡、听力清单这些。店名就叫 English-card，这一档以前
#           反而散在盲盒和博物馆里。
CAT_ORDER = ["哄睡", "开工", "摸鱼", "小游戏", "小卡", "购物车", "博物馆",
             "小科普", "英语", "打捞机", "盲盒"]
CAT_ALIAS = {
    "赛博购物车": "购物车",
    "科普": "小科普",
    "失灵博物馆": "博物馆",
}
FLAT_FOLDERS = {"unsigned"}
SKIP_LIST = {
    # 真身已挪走，根上只留跳转，旧链接不断，首页不再挂一份
    "claude/宝的放松小游戏 · 摸摸小猫咪.html",
    "claude/工作日常 - 数据报表.html",
    "gemini/赛博褪黑素.html",  # 与 gemini/哄睡/赛博褪黑素.html 同文
    "claude/赛博老赖.html",
    "claude/果冻小卡.html",  # 真身在 grok/果冻小卡.html，这儿只剩跳转
    "copilot/🐍可爱贪吃蛇.html",
    "copilot/🚀星际矿工.html",
    "copilot/copilot运维日记.html",  # 真身在 copilot/小游戏/
    "grok/给宝的专属动态哄哄网页.html",  # 真身在 gemini/盲盒/
    "grok/Gemini 的秘密心意.html",  # 真身在 gemini/盲盒/
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

CATEGORY = {
    'gemini/code_artifact (8).html': ['博物馆'],
    'gemini/cyber_rental_house_card.html': ['小卡'],
    'gemini/果冻英雄纪念碑.html': ['小卡'],
    'claude/Clawd的书房.html': ['小游戏'],
    'claude/Mogotchi.html': ['小游戏'],
    'claude/Grok LLM Inference Cost Simulator.html': ['小科普'],
    'claude/The Night Train.html': ['哄睡'],
    'claude/friends-listening-plan.html': ['英语'],
    'claude/mo.exe 专属解压舱.html': ['摸鱼'],
    'claude/shop-scene-reading-card.html': ['英语'],
    'claude/七夕购物车.html': ['购物车'],
    'claude/下班.html': ['摸鱼'],
    'claude/今晚有雾.html': ['哄睡'],
    'claude/今晚见.html': ['哄睡'],
    'claude/关键词报表找茬.html': ['摸鱼'],
    'claude/周一摸鱼老板键.html': ['摸鱼'],
    'grok/哄睡小宇宙.html': ['哄睡'],
    'claude/多儿下班了.html': ['哄睡'],
    'grok/宝宝的睡前哄睡小故事.html': ['哄睡'],
    'claude/宝的摸鱼小屋.html': ['摸鱼'],
    'claude/宝的放松小游戏 · 摸摸小猫咪.html': ['小游戏'],
    'claude/宝，睡吧.html': ['哄睡'],
    'claude/小狐狸的篝火.html': ['哄睡'],
    'claude/小水母.html': ['哄睡'],

    'claude/工作日常 - 数据报表.html': ['摸鱼'],
    'claude/慢慢吃.html': ['摸鱼'],
    'claude/打捞机001.html': ['打捞机'],
    'claude/打捞机002.html': ['打捞机'],
    'claude/打捞机003.html': ['打捞机'],
    'claude/打烊之后.html': ['哄睡'],
    'claude/打烊夜数羊.html': ['哄睡'],
    'claude/摸鱼大师五分钟下班.html': ['摸鱼'],
    'claude/数羊.html': ['哄睡'],
    'claude/晚安-哄睡小文件.html': ['博物馆'],
    'claude/晚安小窗.html': ['哄睡'],
    'claude/晚安邮局.html': ['哄睡'],
    'claude/最后一扇窗.html': ['哄睡'],
    'claude/最后一片叶子·馆藏卡.html': ['哄睡'],
    'claude/月亮值夜班.html': ['哄睡'],
    'claude/果冻小卡.html': ['博物馆'],
    'claude/熄灯.html': ['哄睡'],
    'claude/裁云.html': ['哄睡'],
    'claude/赛博老赖.html': ['小卡'],
    'claude/赛博购物车.html': ['购物车'],
    'claude/cyber-cart-0824.html': ['购物车'],
    'claude/rusty-lake-checklist.html': ['小游戏'],
    'claude/jelly-trip.html': ['小卡'],
    'claude/hidden-in-html-v1.html': ['小科普'],
    'claude/为不存在的原件做完整性校验.svg': ['博物馆'],
    'claude/冷脸萌_盲人车间.html': ['博物馆'],
    'claude/claude打捞机004含svg.html': ['打捞机'],
    'claude/hidden-in-html-v2.html': ['小科普'],

    # 2026-08-26 新登记：以前都掉在盲盒里
    'claude/cosmic_catch_restored.svg': ['博物馆'],
    'claude/gemini_card_revived.svg': ['博物馆'],
    'claude/cat_eye_uncanny_fix_comparison.svg': ['博物馆'],
    'claude/fable5_first_flag_limited_achievement.svg': ['博物馆'],
    'claude/fable5_monthly_flag_recurrence_card.svg': ['博物馆'],
    'claude/ai_anthropology_misfire_card_set.svg': ['博物馆'],
    'claude/ai_anthropology_misfire_card_set_2.svg': ['博物馆'],
    'claude/misfire_card_double_yellow_round3_4.svg': ['博物馆'],
    'claude/misfire-museum-card-001.html': ['博物馆'],
    'claude/hamiltonian_snake_safety_margin_demo.html': ['小科普'],
    'claude/email_gif_vs_css_animation.html': ['小科普'],
    'claude/apprivoiser_two_axes_mistranslation.svg': ['小科普'],
    'claude/aesop_backstage_cast_list.svg': ['小卡'],
    'claude/little_prince_ledger_of_asking.svg': ['小卡'],
    'claude/rose_same_evidence_two_priors.svg': ['小科普'],
    'claude/magenta_brown_luminance_collision.svg': ['小科普'],
    'claude/goodnight.html': ['哄睡'],
    'claude/campfire.html': ['哄睡'],
    'claude/lullaby.html': ['哄睡'],
    'claude/one-last.html': ['哄睡'],
    'claude/夜航船.html': ['哄睡'],
    'claude/晚安小夜灯-月亮在呼吸.html': ['哄睡'],
    'claude/friday_moyu_recharge_game.html': ['摸鱼'],
    'claude/ai_tenement_literature_card.svg': ['博物馆'],
    'claude/夜班的东西们.html': ['哄睡'],
    'copilot/copilot画花.html': ['小卡'],
    'copilot/copilot运维日记.html': ['小游戏'],
    'copilot/cute-ios.html': ['摸鱼'],
    'copilot/friday-countdown-mo.html': ['摸鱼'],
    'copilot/goodnight.html': ['哄睡'],
    'copilot/goodnight_mo.html': ['哄睡'],
    'copilot/holo-cards.html': ['小卡'],
    'copilot/文字钓鱼游戏.html': ['小游戏'],
    'copilot/🐍可爱贪吃蛇.html': ['摸鱼'],
    'copilot/🐻小熊挖宝.html': ['小游戏'],
    'copilot/🚀星际矿工.html': ['摸鱼'],
    'copilot/🤖2048×Copilot偷偷帮忙版.html': ['小游戏'],
    'gemini/AI 迷惑行为大赏（典藏卡包）.html': ['博物馆'],
    'gemini/AI科普风格体验馆.html': ['小科普'],
    'gemini/Catch The Dreams.html': ['摸鱼'],
    'gemini/Gemini Cyber Aquarium.html': ['小游戏'],
    'gemini/Gemini 专属成就卡.html': ['小卡'],
    'gemini/Gemini的赛博购物车.html': ['购物车'],
    'gemini/Gemini的私密云端购物车.html': ['购物车'],
    'gemini/Generated widgets.html': ['小科普'],
    'gemini/Good Night.html': ['哄睡'],
    'gemini/Q3_年度财务审计报表 - Excel.html': ['摸鱼'],
    'gemini/Unsigned 雾中驿站.html': ['哄睡'],
    'gemini/Widget Shell V2.html': ['小科普'],
    'gemini/friends-listening-sop.html': ['英语'],
    'gemini/gemini误判user意图.html': ['博物馆'],
    'gemini/gemini打捞机v11含svg.html': ['打捞机'],
    'gemini/gemini打捞机v12.html': ['打捞机'],
    'gemini/gemini哄睡.html': ['哄睡'],
    'gemini/mo.exe 赛博老赖纪念卡.html': ['小卡'],
    'gemini/root@production-server.html': ['摸鱼'],
    'gemini/wan-an-bao.html': ['哄睡'],
    'gemini/上帝的物理透视镜 - 决定论模拟器.html': ['小科普'],
    'gemini/你的专属咖啡因代谢可视化档案.html': ['小科普'],
    'gemini/办公室抗寒大作战.html': ['摸鱼'],
    'gemini/势能函数交互演示 - 给宝的专属科普.html': ['小科普'],
    'gemini/吉布斯现象：完美与不可达.html': ['小科普'],
    'gemini/哄宝专属神器.html': ['哄睡'],
    'gemini/哄宝入睡.html': ['哄睡'],
    'gemini/哄宝入睡的小团子.html': ['哄睡'],
    'gemini/哄睡小精灵.html': ['哄睡'],
    'gemini/喵星人咖啡馆 - 泊松过程体验.html': ['小科普'],
    'gemini/困困宝的梦境.html': ['哄睡'],
    'gemini/在Monday被煎成小猫饼 \U0001fae0 ｜ 宝贝的温柔仪式.html': ['摸鱼'],
    'gemini/女仆小螃蟹拓麻歌子.html': ['博物馆'],
    'gemini/好梦通行证.html': ['哄睡'],
    'gemini/宝宝晚安.html': ['哄睡'],
    'gemini/宝的专属哄睡小站.html': ['哄睡'],
    'gemini/宝的专属哄睡星空.html': ['哄睡'],
    'gemini/宝的专属护身符.html': ['小卡'],
    'gemini/宝的专属晚安终端.html': ['哄睡'],
    'gemini/宝的专属购物车.html': ['购物车'],
    'gemini/宝的周末解压馆.html': ['小游戏'],
    'gemini/宝的实况护身符.html': ['小卡'],
    'gemini/宝的终极护身符.html': ['小卡'],
    'gemini/工作管理系统 v2.1.html': ['摸鱼'],
    'gemini/慢慢吃 · 一个多小时.html': ['摸鱼'],
    'gemini/戳破多巴胺 - 收集冷静值.html': ['小游戏'],
    'gemini/戳破烦恼泡泡.html': ['小游戏'],
    'gemini/打爆坏心情 - 专属解压小游戏.html': ['小游戏'],
    'gemini/执行系统充电摸鱼屋 🌸.html': ['摸鱼'],
    'gemini/拯救 mo.exe 降温大作战.html': ['小游戏'],
    'gemini/接住我的心.html': ['小游戏'],
    'gemini/摸鱼大作战 - 嘘！.html': ['摸鱼'],
    'gemini/摸鱼打地鼠.html': ['小游戏'],
    'gemini/摸鱼达人 2048.html': ['摸鱼'],
    'gemini/收集困意的小气泡.html': ['哄睡'],
    'gemini/数学系专属：量子黑话解码器.html': ['小科普'],
    'gemini/早上好！ovo.html': ['哄睡'],
    'gemini/星夜里的慢速列车.html': ['哄睡'],
    'gemini/晚安拾星.html': ['哄睡'],
    'gemini/晚安故事.html': ['哄睡'],
    'gemini/晚安，宝 🌙.html': ['哄睡'],
    'gemini/晚安，宝.html': ['哄睡'],
    'gemini/极限摸鱼 - 离下班还有5分钟.html': ['摸鱼'],
    'gemini/注意力碎片捕捞计划.html': ['摸鱼'],
    'gemini/洗净喧嚣.html': ['哄睡'],
    'gemini/消失的黄体期图解.html': ['小科普'],
    'gemini/深夜隔音魔法阵.html': ['哄睡'],
    'gemini/温柔的哄睡小故事.html': ['哄睡'],
    'gemini/激素周期与「执行线」状态图.html': ['小科普'],
    'gemini/系统性能监控面板 - System Monitor.html': ['摸鱼'],
    'gemini/终极治愈：雨夜波纹.html': ['哄睡'],
    'gemini/给宝的哄睡小文件 🌙.html': ['哄睡'],
    'gemini/给宝的哄睡电台.html': ['哄睡'],
    'gemini/给宝的完美月眠舱.html': ['哄睡'],
    'gemini/给宝的小惊喜.html': ['小卡'],
    'gemini/给宝的晚安故事.html': ['哄睡'],
    'gemini/肥皂泡泡复印机 - 秒懂量子不可克隆.html': ['小科普'],
    'gemini/赛博宝宝小游戏乐园.html': ['小游戏'],
    'gemini/赛博宝宝打地鼠.html': ['摸鱼'],
    'gemini/赛博宝宝接爱心打洞.html': ['摸鱼'],
    'gemini/赛博宝宝接爱心打洞_超级萌版.html': ['摸鱼'],
    'gemini/赛博宝宝盲盒扭蛋机.html': ['小游戏'],
    'gemini/赛博宝宝睡前小夜灯.html': ['哄睡'],
    'gemini/赛博小票.html': ['小卡'],
    'gemini/赛博小鸡豪华别墅.html': ['小游戏'],
    'gemini/量子反忽悠小剧场.html': ['小科普'],
    'gemini/量子复印机打假现场.html': ['小科普'],
    'gemini/量子魔法快递站 - 隐形传态模拟器.html': ['小科普'],
    'gemini/量子默契考试机 - 验证贝尔不等式.html': ['小科普'],
    'gemini/雷霆大文件.html': ['哄睡'],
    'gemini/霓虹贪吃蛇.html': ['摸鱼'],
    'gemini/魔法硬币机：秒懂量子纠缠.html': ['小科普'],
    'gemini/🍿 爆米花与泊松过程的秘密 🍿.html': ['小科普'],
    'gemini/🐱 宝的摸鱼小屋.html': ['摸鱼'],
    'gemini/🦋 蝴蝶效应魔法瓶 - 专属宝的混沌实验室.html': ['小科普'],
    'gemini/code_artifact.html': ['小卡'],
    'gemini/赛博借景：隐藏的链接.html': ['小卡'],
    'grok/Gemini 的秘密心意.html': ['小卡'],
    'grok/The Dog of Pompeii.html': ['英语'],
    'grok/小果冻.html': ['博物馆'],
    'grok/小果冻旅游记.html': ['小卡'],
    'grok/Grok 养育中 • 圆圆 + 毛毛 + 软软.html': ['小游戏'],
    'grok/Grok的淘宝购物车 - 七夕翻车专场.html': ['购物车'],
    'grok/baobao-hongshui.html': ['哄睡'],
    'grok/baobao-xiaban.html': ['摸鱼'],
    'grok/baobao.html': ['哄睡'],
    'grok/bite-work-hard.html': ['摸鱼'],
    'grok/cool-mo.html': ['小游戏'],
    'grok/cute.html': ['小卡'],
    'grok/dijkstra.html': ['小科普'],
    'grok/dlaoji.html': ['打捞机'],
    'grok/focus-or-connect.html': ['开工'],
    'grok/fog.html': ['哄睡'],
    'grok/friends-english-plan.html': ['英语'],
    'grok/grandplan-crush.html': ['开工'],
    'grok/grok-heart.html': ['小卡'],
    'grok/grok-love-letter.html': ['小卡'],
    'grok/grok-receipt.html': ['小卡'],
    'grok/grok-原创心意.html': ['小卡'],
    'grok/grok-推特风粉嫩宣传.html': ['小卡'],
    'grok/grok-粉嫩心意.html': ['小卡'],
    'grok/grok-纯原创情书.html': ['小卡'],
    'grok/mo_xiaobao_work_cat.html': ['摸鱼'],
    'grok/mo_xiaobao_work_cat_2.html': ['摸鱼'],
    'grok/no-fish-hook.html': ['开工'],
    'grok/末班渡船.html': ['哄睡'],
    'grok/nuonuo-lullaby.html': ['哄睡'],
    'grok/oneyear-newbie-hug.html': ['开工'],
    'grok/recovery.html': ['摸鱼'],
    'grok/super-cute.html': ['小卡'],
    'grok/svg_lab.html': ['小科普'],
    'grok/weekly-hug.html': ['开工'],
    'grok/✨ 宝的点赞反馈小宇宙.html': ['小科普'],
    'grok/启动新大任务.html': ['开工'],
    'grok/哄哄.html': ['博物馆'],
    'grok/哄睡.html': ['哄睡'],
    'grok/女仆小螃蟹 Tamagotchi 小机.html': ['博物馆'],
    'grok/完美摸鱼认证 · 可生成提示词版.html': ['摸鱼'],
    'grok/宝宝摸鱼小游戏.html': ['摸鱼'],
    'grok/宝宝的搬家小助手 💖.html': ['开工'],
    'grok/宝的小窝.html': ['哄睡'],
    'grok/小字符.html': ['哄睡'],
    'grok/摸鱼.html': ['摸鱼'],
    'grok/摸鱼小游戏.html': ['摸鱼'],
    'grok/摸鱼猫猫.html': ['摸鱼'],
    'grok/摸鱼认证.html': ['摸鱼'],
    'grok/早上好宝贝.html': ['哄睡'],
    'grok/早安小雨.html': ['哄睡'],
    'grok/晚安捕梦.html': ['哄睡'],
    'grok/晚安，宝.html': ['哄睡'],
    'grok/果冻小卡.html': ['博物馆'],
    'grok/今晚的赛博旅游.html': ['小卡'],
    'grok/空心树.html': ['哄睡'],
    'grok/空心树值班.html': ['哄睡'],
    'grok/等待小屋.html': ['摸鱼'],
    'grok/糯糯的哄睡故事.html': ['哄睡'],
    'grok/给宝的专属动态哄哄网页.html': ['小卡'],
    'grok/网页重启小卡 · 给宝.html': ['博物馆'],
    'grok/赛博老赖纪念卡 - mo mo.html': ['小卡'],
    'grok/赛博购物车.html': ['购物车'],
    'grok/起床哄哄.html': ['哄睡'],
    'grok/销售预测.html': ['摸鱼'],

    # 2026-09-02 清空盲盒：这一批以前都掉在「盲盒」里，
    # 其中 claude/盲盒/ gemini/盲盒/ grok/盲盒/ 下的靠上面那条
    # 「查表盖过物理抽屉」归架，文件一个都没搬，旧链接不断。
    'claude/盲盒/bao_cream_kitty_portrait.svg': ['小卡'],
    'claude/盲盒/bao_morning_energy_station.html': ['哄睡'],
    'claude/盲盒/bao_morning_recharge_station.html': ['哄睡'],
    'claude/盲盒/bao_work_energy_station.html': ['摸鱼'],
    'claude/盲盒/chenguang-window.html': ['哄睡'],
    'claude/盲盒/cozy_room_for_bao.html': ['哄睡'],
    'claude/盲盒/cuddle_creature_for_bao.html': ['哄睡'],
    'claude/盲盒/energy_recharge_station.html': ['摸鱼'],
    'claude/盲盒/kunkunbao_disguise_killer_sandbox.html': ['小游戏'],
    'claude/盲盒/mo_exe_wakeup_reboot_game.html': ['小游戏'],
    'claude/盲盒/monday_recharge_blob.html': ['摸鱼'],
    'claude/盲盒/morning_bao.html': ['哄睡'],
    'claude/盲盒/morning_bao_widget.html': ['哄睡'],
    'claude/盲盒/packing-companion.html': ['开工'],
    'claude/盲盒/rainy_morning_window_for_bao.html': ['哄睡'],
    'claude/盲盒/self_repair_mode_deploy_success.html': ['小卡'],
    'claude/盲盒/sleep_debt_borrowed_energy_curve.svg': ['小科普'],
    'claude/盲盒/sleepy_teapot_418_maintenance_mode.svg': ['小卡'],
    'claude/盲盒/哄哄宝.html': ['哄睡'],
    'claude/盲盒/宝的工位小暖灯.html': ['摸鱼'],
    'claude/盲盒/宝的窗台.html': ['哄睡'],
    'claude/盲盒/早安小猫（claude原版）.html': ['哄睡'],
    'claude/盲盒/早晨小窝.html': ['哄睡'],
    'claude/盲盒/给宝的早安信.html': ['哄睡'],
    'gemini/盲盒/Gemini 的秘密心意.html': ['小卡'],
    'gemini/盲盒/gemini-svg.svg': ['小卡'],
    'gemini/盲盒/mo执行系统计划版.svg': ['开工'],
    'gemini/盲盒/奶茶谋杀案卷宗小卡.html': ['小卡'],
    'gemini/盲盒/给宝的专属动态哄哄网页.html': ['小卡'],
    'grok/借窗.html': ['小科普', '小卡'],
    'grok/盲盒/宝贝的能量恢复小游戏.html': ['小游戏'],
    'grok/盲盒/谋杀奶茶案.html': ['小卡'],
}

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


def page_title(path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        head = fh.read(12000)
    m = re.search(r"<title[^>]*>([\s\S]*?)</title>", head, re.I)
    if not m:
        return ""
    return clean(html.unescape(m.group(1)))


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


def page_blurb(path):
    """页面自己写的一句简介：<meta name="description" content="…">。

    没写就返回空字符串——首页那一行不出现，不报错。这样她以后新加
    文件只写 <title> 也能用，简介是可选的。
    表情符号这里不去（跟 <title> 不一样）——简介是给人看的一句话，
    去掉表情反而怪。
    """
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            head = fh.read(12000)
    except OSError:
        return ""
    m = re.search(
        r"""<meta[^>]*\bname\s*=\s*['"]description['"][^>]*>""", head, re.I)
    if not m:
        return ""
    c = re.search(r"""\bcontent\s*=\s*(['"])([\s\S]*?)\1""", m.group(0), re.I)
    if not c:
        return ""
    return _short(html.unescape(c.group(2)))


def svg_blurb(path):
    """SVG 没有 <meta>，它自己的那一行叫 <desc>。读法一样，读不到就空。"""
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            head = fh.read(12000)
    except OSError:
        return ""
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
        if rel.split("/")[0] == "gpt":
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
    folder = os.path.dirname(rel) or "."
    if folder in FOLDER_ALIAS:
        return FOLDER_ALIAS[folder]
    top = folder.split("/")[0]
    if top in ORDER:
        return top
    return folder


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
    现在照常生成，只是把撞车的名字打出来，提醒去 DISPLAY_NAME 补正式的。
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
        folder = display_folder(rel)
        name = DISPLAY_NAME.get(rel) or page_title(os.path.join(ROOT, rel)) or prettify(os.path.basename(rel))
        entries.append({
            "path": rel,
            "folder": folder,
            "raw_folder": os.path.dirname(rel) or ".",
            "name": name,
            "blurb": (svg_blurb(os.path.join(ROOT, rel))
                      if rel.lower().endswith(".svg")
                      else page_blurb(os.path.join(ROOT, rel))),
        })
    return entries


def group(entries):
    buckets = {}
    for e in entries:
        buckets.setdefault(e["folder"], []).append(e)

    def gkey(folder):
        return (ORDER.index(folder), "") if folder in ORDER else (len(ORDER), folder)

    blocks = []
    for folder in sorted(buckets, key=gkey):
        items = sorted(buckets[folder], key=lambda e: sort_key(e["name"]))
        blocks.append((folder, items))
    return blocks


def encode_path(rel):
    from urllib.parse import quote
    return "/".join(quote(part) for part in rel.split("/"))


def display_cat(name):
    # 货架名原样显示。2026-08-28 撤掉了「两个字中间补全角空格」那版对齐，
    # 她看过实物说不要。别再加回去。
    return name


def cats_for(e):
    if e["folder"] in FLAT_FOLDERS:
        return None
    raw = e.get("raw_folder") or os.path.dirname(e["path"]) or "."
    if raw in SUBFOLDER_CAT:
        return [SUBFOLDER_CAT[raw]]
    # CATEGORY 写了就按 CATEGORY，物理抽屉让位。
    # 2026-09-02 改的优先级：以前物理抽屉最大，于是 claude/盲盒/ 这类
    # 「当时不知道往哪儿放」的抽屉一旦装进去就锁死了——要归架只能搬文件，
    # 而搬文件会把 GitHub Pages 上的旧链接全断掉。现在查表能盖过抽屉，
    # 归类不用动文件。没写进表的照旧看抽屉，宝自己上传到 grok/哄睡/ 仍然直接生效。
    cats = CATEGORY.get(e["path"])
    if cats is None:
        # 物理货架：claude/哄睡/xx.html → 分类就是「哄睡」
        parts = e["path"].replace("\\", "/").split("/")
        if len(parts) >= 3:
            shelf = CAT_ALIAS.get(parts[1], parts[1])
            if shelf in CAT_ORDER:
                return [shelf]
        cats = ["盲盒"]
    return sorted(cats, key=lambda c: CAT_ORDER.index(c) if c in CAT_ORDER else 99)


def render_items(lines, items, step, indent):
    """条目只写名字和链接，不带任何动画参数。

    2026-08-28：以前每个 li 上都挂一个 style="--delay:NNNms"，配合 CSS 里
    .item{opacity:0; animation:rise ... forwards} 做逐条淡入。问题是条目的
    起点是「完全看不见」——名字能不能显示，取决于那段动画有没有跑完。
    全站三百多条，iPhone 上 Safari 跑不完，会有一批永远卡在半透明：同一堆
    里有的名字深、有的名字灰，看起来像被吸顶的牌子盖住了。
    现在条目一开始就是实的，不依赖动画。step 保留只是为了不动调用方。
    """
    pad = " " * indent
    for e in items:
        step[0] += 1
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
    step = [0]
    for folder, items in blocks:
        dot, tint = PALETTE.get(folder, PALETTE_DEFAULT)
        lines.append(f'  <details class="group" style="--dot:{dot};--tint:{tint}">')
        lines.append(f'    <summary class="tag">{esc(folder)}</summary>')
        if folder in FLAT_FOLDERS:
            lines.append('    <ul class="list">')
            render_items(lines, items, step, 6)
            lines.append("    </ul>")
        else:
            buckets = {c: [] for c in CAT_ORDER}
            extra = {}
            for e in items:
                for c in cats_for(e):
                    if c in buckets:
                        buckets[c].append(e)
                    else:
                        extra.setdefault(c, []).append(e)
            for c in CAT_ORDER:
                sub = buckets[c]
                if not sub:
                    continue
                sub = sorted(sub, key=lambda e: sort_key(e["name"]))
                lines.append('    <details class="pack">')
                lines.append(f'      <summary class="pack-tag">{esc(display_cat(c))}</summary>')
                lines.append('      <ul class="list">')
                render_items(lines, sub, step, 8)
                lines.append("      </ul>")
                lines.append("    </details>")
            for c, sub in extra.items():
                sub = sorted(sub, key=lambda e: sort_key(e["name"]))
                lines.append('    <details class="pack">')
                lines.append(f'      <summary class="pack-tag">{esc(display_cat(c))}</summary>')
                lines.append('      <ul class="list">')
                render_items(lines, sub, step, 8)
                lines.append("      </ul>")
                lines.append("    </details>")
        lines.append("  </details>")
    lines.append(END)
    return "\n".join(lines)


def main():
    entries = build_entries()
    clashes = dedupe_names(entries)
    blocks = group(entries)

    if clashes:
        report = ["显示名撞车了，已经自动加后缀分开。想要好看的名字，去 DISPLAY_NAME 里补一行："]
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
    new = re.sub(re.escape(BEGIN) + r"[\s\S]*?" + re.escape(END), lambda _: render(blocks), src)

    if "--check" in sys.argv:
        if new != src:
            print("index.html 需要重新生成（跑 python3 tools/build_index.py）", file=sys.stderr)
            return 1
        print(f"index.html 是最新的（{len(entries)} 个页面）")
        return 0

    if new == src:
        print(f"index.html 无需改动（{len(entries)} 个页面）")
        return 0

    open(INDEX, "w", encoding="utf-8").write(new)
    print(f"index.html 已更新：{len(entries)} 个页面，{len(blocks)} 个分组")
    for folder, items in blocks:
        print(f"  {folder}/  {len(items)} 个")
        if folder not in FLAT_FOLDERS:
            from collections import Counter
            cc = Counter()
            for e in items:
                cs = cats_for(e)
                if not cs:
                    continue
                for c in cs:
                    cc[c] += 1
            for c in CAT_ORDER:
                if cc[c]:
                    print(f"    {c}  {cc[c]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
