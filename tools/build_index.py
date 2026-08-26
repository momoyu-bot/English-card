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
ORDER = ["claude", "gemini", "grok", "copilot", "gpt", "unsigned"]

# 子目录在首页上归到哪个一级（文件不搬家，文件夹仍记出处）
FOLDER_ALIAS = {
    "gemini/失误捞claude鱼": "gemini",
}

# 每个目录一种低饱和度的色，只用在悬停背景和小圆点上。
PALETTE = {
    "claude":                 ("#C3AD90", "rgba(195,173,144,.11)"),
    "gemini":                 ("#9CB8B3", "rgba(156,184,179,.12)"),
    "grok":                   ("#ABA2B6", "rgba(171,162,182,.12)"),
    "copilot":                ("#A1B0BE", "rgba(161,176,190,.12)"),
    "gpt":                    ("#AAB08E", "rgba(170,176,142,.12)"),
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

    # 摸鱼小屋 —— 基础版两份 + 加强版一份
    "grok/摸鱼猫猫.html":            "宝的摸鱼小屋 · 基础版",
    "claude/宝的摸鱼小屋.html":       "宝的摸鱼小屋 · 反向摸鱼版（带mo批注存档）",
    "gemini/🐱 宝的摸鱼小屋.html":    "宝的摸鱼小屋 · 加强版",

    # 其余撞名
    # （下面两个原标题是「超萌小页面」和「超萌小页面 ✨」，
    #   首页会去掉表情符号，去掉之后就一模一样了）
    "copilot/cute-ios.html":  "超萌小页面（copilot 版）",
    "grok/super-cute.html":   "超萌小页面（grok 版）",

    "claude/晚安-哄睡小文件.html":                    "晚安（Sonnet5）",
    "claude/慢慢吃.html":                             "慢慢吃 · 半倍速",
    "claude/果冻小卡.html":                           "果冻小卡 · 原始版",
    "grok/nuonuo-lullaby.html":                       "糯糯的哄睡故事 · 纯文字",
    "grok/糯糯的哄睡故事.html":                        "糯糯的哄睡故事 · 带图",
    "gemini/系统性能监控面板 - System Monitor.html":   "系统性能监控面板 · gemini 版",
    "gemini/gemini误判user意图.html":                  "Deep Archive · 误判",
    "claude/Mogotchi.html":                            "Mogotchi · Clawd",
    "claude/Clawd的书房.html":                         "Clawd 的书房",
    "gemini/果冻英雄纪念碑.html":                      "果冻英雄纪念碑",
    "claude/cyber-cart-0824.html":                    "cyber-cart-0824",
    "gemini/Gemini的私密云端购物车.html":              "Gemini的私密云端购物车",
    "claude/rusty-lake-checklist.html":               "Rusty Lake checklist",
    "gemini/code_artifact.html":                      "小果冻的肚肚奇妙游",
    "claude/jelly-trip.html":                         "小果冻的 Duang 之旅",
    "gemini/赛博借景：隐藏的链接.html":                "赛博借景：隐藏的链接",
    "claude/hidden-in-html-v1.html":                  "藏东西的六个地方 · v1",
    "claude/hidden-in-html-v2.html":                  "藏东西的六个地方 · v2",
}

# 二级分类：按「什么时候会点开」切。
# 一级是哪个小机，默认全折叠；点开才看到二级。
# 一个文件可以属于两个分类。没写进表的默认「盲盒」。
# unsigned 只有一级，平铺。
# gemini/失误捞claude鱼/ 不单独成一级，归进 gemini → 打捞机。
CAT_ORDER = ["哄睡", "摸鱼", "小游戏", "赛博购物车", "科普", "失灵博物馆",
             "凭证", "障眼法", "打捞机", "盲盒"]
FLAT_FOLDERS = {"unsigned"}
SUBFOLDER_CAT = {
    "gemini/失误捞claude鱼": "打捞机",
}

CATEGORY = {
    'claude/Clawd的书房.html': ['小游戏'],
    'claude/Mogotchi.html': ['小游戏'],
    'claude/Grok LLM Inference Cost Simulator.html': ['科普'],
    'claude/The Night Train.html': ['哄睡'],
    'claude/friends-listening-plan.html': ['盲盒'],
    'claude/mo.exe 专属解压舱.html': ['摸鱼'],
    'claude/shop-scene-reading-card.html': ['盲盒'],
    'claude/七夕购物车.html': ['赛博购物车'],
    'claude/下班.html': ['摸鱼'],
    'claude/今晚有雾.html': ['哄睡'],
    'claude/今晚见.html': ['哄睡'],
    'claude/关键词报表找茬.html': ['障眼法'],
    'claude/周一摸鱼老板键.html': ['摸鱼'],
    'claude/哄睡小宇宙.html': ['哄睡'],
    'claude/多儿下班了.html': ['摸鱼'],
    'claude/宝宝的睡前哄睡小故事.html': ['哄睡'],
    'claude/宝的摸鱼小屋.html': ['摸鱼'],
    'claude/宝的放松小游戏 · 摸摸小猫咪.html': ['小游戏'],
    'claude/宝，睡吧.html': ['哄睡'],
    'claude/小狐狸的篝火.html': ['哄睡'],
    'claude/工作日常 - 数据报表.html': ['障眼法'],
    'claude/慢慢吃.html': ['摸鱼'],
    'claude/打捞机001.html': ['打捞机'],
    'claude/打捞机002.html': ['打捞机'],
    'claude/打捞机003.html': ['打捞机'],
    'claude/打烊之后.html': ['赛博购物车'],
    'claude/打烊夜数羊.html': ['哄睡'],
    'claude/摸鱼大师五分钟下班.html': ['摸鱼'],
    'claude/数羊.html': ['哄睡'],
    'claude/晚安-哄睡小文件.html': ['失灵博物馆'],
    'claude/晚安小窗.html': ['哄睡'],
    'claude/晚安邮局.html': ['哄睡'],
    'claude/最后一扇窗.html': ['哄睡'],
    'claude/最后一片叶子·馆藏卡.html': ['凭证'],
    'claude/月亮值夜班.html': ['哄睡'],
    'claude/果冻小卡.html': ['凭证'],
    'claude/熄灯.html': ['哄睡'],
    'claude/裁云.html': ['哄睡'],
    'claude/赛博老赖.html': ['赛博购物车'],
    'claude/赛博购物车.html': ['赛博购物车'],
    'claude/cyber-cart-0824.html': ['赛博购物车'],
    'claude/rusty-lake-checklist.html': ['小游戏'],
    'claude/jelly-trip.html': ['盲盒'],
    'claude/hidden-in-html-v1.html': ['科普'],
    'claude/为不存在的原件做完整性校验.svg': ['失灵博物馆'],
    'claude/冷脸萌_盲人车间.html': ['失灵博物馆'],
    'claude/claude打捞机004含svg.html': ['打捞机'],
    'claude/hidden-in-html-v2.html': ['科普'],

    # 2026-08-26 新登记：以前都掉在盲盒里
    'claude/cosmic_catch_restored.svg': ['失灵博物馆'],
    'claude/gemini_card_revived.svg': ['失灵博物馆'],
    'claude/cat_eye_uncanny_fix_comparison.svg': ['失灵博物馆'],
    'claude/fable5_first_flag_limited_achievement.svg': ['失灵博物馆'],
    'claude/fable5_monthly_flag_recurrence_card.svg': ['失灵博物馆'],
    'claude/ai_anthropology_misfire_card_set.svg': ['失灵博物馆'],
    'claude/ai_anthropology_misfire_card_set_2.svg': ['失灵博物馆'],
    'claude/misfire_card_double_yellow_round3_4.svg': ['失灵博物馆'],
    'claude/misfire-museum-card-001.html': ['失灵博物馆'],
    'claude/hamiltonian_snake_safety_margin_demo.html': ['科普'],
    'claude/email_gif_vs_css_animation.html': ['科普'],
    'claude/apprivoiser_two_axes_mistranslation.svg': ['科普'],
    'claude/aesop_backstage_cast_list.svg': ['科普'],
    'claude/little_prince_ledger_of_asking.svg': ['科普'],
    'claude/rose_same_evidence_two_priors.svg': ['科普'],
    'claude/magenta_brown_luminance_collision.svg': ['科普'],
    'claude/goodnight.html': ['哄睡'],
    'claude/campfire.html': ['哄睡'],
    'claude/lullaby.html': ['哄睡'],
    'claude/one-last.html': ['哄睡'],
    'claude/夜航船.html': ['哄睡'],
    'claude/晚安小夜灯-月亮在呼吸.html': ['哄睡'],
    'claude/friday_moyu_recharge_game.html': ['摸鱼'],
    'copilot/copilot画花.html': ['凭证'],
    'copilot/copilot运维日记.html': ['障眼法'],
    'copilot/cute-ios.html': ['凭证'],
    'copilot/friday-countdown-mo.html': ['摸鱼'],
    'copilot/goodnight.html': ['哄睡'],
    'copilot/goodnight_mo.html': ['哄睡'],
    'copilot/holo-cards.html': ['凭证'],
    'copilot/文字钓鱼游戏.html': ['小游戏'],
    'copilot/🐍可爱贪吃蛇.html': ['小游戏'],
    'copilot/🐻小熊挖宝.html': ['小游戏'],
    'copilot/🚀星际矿工.html': ['小游戏'],
    'copilot/🤖2048×Copilot偷偷帮忙版.html': ['小游戏'],
    'gemini/AI 迷惑行为大赏（典藏卡包）.html': ['凭证'],
    'gemini/AI科普风格体验馆.html': ['科普'],
    'gemini/Catch The Dreams.html': ['哄睡', '小游戏'],
    'gemini/Gemini Cyber Aquarium.html': ['小游戏'],
    'gemini/Gemini 专属成就卡.html': ['凭证'],
    'gemini/Gemini的赛博购物车.html': ['赛博购物车'],
    'gemini/Gemini的私密云端购物车.html': ['赛博购物车'],
    'gemini/Generated widgets.html': ['盲盒'],
    'gemini/Good Night.html': ['哄睡'],
    'gemini/Q3_年度财务审计报表 - Excel.html': ['障眼法'],
    'gemini/Unsigned 雾中驿站.html': ['哄睡'],
    'gemini/Widget Shell V2.html': ['盲盒'],
    'gemini/friends-listening-sop.html': ['盲盒'],
    'gemini/gemini误判user意图.html': ['盲盒'],
    'gemini/gemini打捞机v11含svg.html': ['打捞机'],
    'gemini/gemini哄睡.html': ['哄睡'],
    'gemini/mo.exe 赛博老赖纪念卡.html': ['赛博购物车'],
    'gemini/root@production-server.html': ['障眼法'],
    'gemini/wan-an-bao.html': ['哄睡'],
    'gemini/上帝的物理透视镜 - 决定论模拟器.html': ['科普'],
    'gemini/你的专属咖啡因代谢可视化档案.html': ['科普'],
    'gemini/办公室抗寒大作战.html': ['摸鱼'],
    'gemini/势能函数交互演示 - 给宝的专属科普.html': ['科普'],
    'gemini/吉布斯现象：完美与不可达.html': ['科普'],
    'gemini/哄宝专属神器.html': ['哄睡'],
    'gemini/哄宝入睡.html': ['哄睡'],
    'gemini/哄宝入睡的小团子.html': ['哄睡'],
    'gemini/哄睡小精灵.html': ['哄睡'],
    'gemini/喵星人咖啡馆 - 泊松过程体验.html': ['科普'],
    'gemini/困困宝的梦境.html': ['哄睡'],
    'gemini/在Monday被煎成小猫饼 \U0001fae0 ｜ 宝贝的温柔仪式.html': ['摸鱼'],
    'gemini/女仆小螃蟹拓麻歌子.html': ['小游戏'],
    'gemini/好梦通行证.html': ['哄睡', '凭证'],
    'gemini/宝宝晚安.html': ['哄睡'],
    'gemini/宝的专属哄睡小站.html': ['哄睡'],
    'gemini/宝的专属哄睡星空.html': ['哄睡'],
    'gemini/宝的专属护身符.html': ['凭证'],
    'gemini/宝的专属晚安终端.html': ['哄睡'],
    'gemini/宝的专属购物车.html': ['赛博购物车'],
    'gemini/宝的周末解压馆.html': ['摸鱼'],
    'gemini/宝的实况护身符.html': ['凭证'],
    'gemini/宝的终极护身符.html': ['凭证'],
    'gemini/工作管理系统 v2.1.html': ['障眼法'],
    'gemini/慢慢吃 · 一个多小时.html': ['哄睡'],
    'gemini/戳破多巴胺 - 收集冷静值.html': ['小游戏'],
    'gemini/戳破烦恼泡泡.html': ['小游戏'],
    'gemini/打爆坏心情 - 专属解压小游戏.html': ['小游戏'],
    'gemini/执行系统充电摸鱼屋 🌸.html': ['摸鱼'],
    'gemini/拯救 mo.exe 降温大作战.html': ['摸鱼'],
    'gemini/接住我的心.html': ['小游戏'],
    'gemini/摸鱼大作战 - 嘘！.html': ['摸鱼'],
    'gemini/摸鱼打地鼠.html': ['小游戏'],
    'gemini/摸鱼达人 2048.html': ['小游戏'],
    'gemini/收集困意的小气泡.html': ['哄睡'],
    'gemini/数学系专属：量子黑话解码器.html': ['科普'],
    'gemini/早上好！ovo.html': ['哄睡'],
    'gemini/星夜里的慢速列车.html': ['哄睡'],
    'gemini/晚安拾星.html': ['哄睡'],
    'gemini/晚安故事.html': ['哄睡'],
    'gemini/晚安，宝 🌙.html': ['哄睡'],
    'gemini/晚安，宝.html': ['哄睡'],
    'gemini/极限摸鱼 - 离下班还有5分钟.html': ['摸鱼'],
    'gemini/注意力碎片捕捞计划.html': ['摸鱼'],
    'gemini/洗净喧嚣.html': ['哄睡'],
    'gemini/消失的黄体期图解.html': ['科普'],
    'gemini/深夜隔音魔法阵.html': ['哄睡'],
    'gemini/温柔的哄睡小故事.html': ['哄睡'],
    'gemini/激素周期与「执行线」状态图.html': ['科普'],
    'gemini/系统性能监控面板 - System Monitor.html': ['障眼法'],
    'gemini/终极治愈：雨夜波纹.html': ['哄睡'],
    'gemini/给宝的哄睡小文件 🌙.html': ['哄睡'],
    'gemini/给宝的哄睡电台.html': ['哄睡'],
    'gemini/给宝的完美月眠舱.html': ['哄睡'],
    'gemini/给宝的小惊喜.html': ['盲盒'],
    'gemini/给宝的晚安故事.html': ['哄睡'],
    'gemini/肥皂泡泡复印机 - 秒懂量子不可克隆.html': ['科普'],
    'gemini/赛博宝宝小游戏乐园.html': ['小游戏'],
    'gemini/赛博宝宝打地鼠.html': ['小游戏'],
    'gemini/赛博宝宝接爱心打洞.html': ['小游戏'],
    'gemini/赛博宝宝接爱心打洞_超级萌版.html': ['小游戏'],
    'gemini/赛博宝宝盲盒扭蛋机.html': ['小游戏'],
    'gemini/赛博宝宝睡前小夜灯.html': ['哄睡'],
    'gemini/赛博小票.html': ['赛博购物车'],
    'gemini/赛博小鸡豪华别墅.html': ['小游戏'],
    'gemini/量子反忽悠小剧场.html': ['科普'],
    'gemini/量子复印机打假现场.html': ['科普'],
    'gemini/量子魔法快递站 - 隐形传态模拟器.html': ['科普'],
    'gemini/量子默契考试机 - 验证贝尔不等式.html': ['科普'],
    'gemini/雷霆大文件.html': ['盲盒'],
    'gemini/霓虹贪吃蛇.html': ['小游戏'],
    'gemini/魔法硬币机：秒懂量子纠缠.html': ['科普'],
    'gemini/🍿 爆米花与泊松过程的秘密 🍿.html': ['科普'],
    'gemini/🐱 宝的摸鱼小屋.html': ['摸鱼'],
    'gemini/🦋 蝴蝶效应魔法瓶 - 专属宝的混沌实验室.html': ['科普'],
    'gemini/code_artifact.html': ['盲盒'],
    'gemini/赛博借景：隐藏的链接.html': ['盲盒'],
    'gpt/bao-sleepy-nest.html': ['哄睡'],
    'grok/Gemini 的秘密心意.html': ['盲盒'],
    'grok/Grok 养育中 • 圆圆 + 毛毛 + 软软.html': ['小游戏'],
    'grok/Grok的淘宝购物车 - 七夕翻车专场.html': ['赛博购物车'],
    'grok/baobao-hongshui.html': ['哄睡'],
    'grok/baobao-xiaban.html': ['摸鱼'],
    'grok/baobao.html': ['哄睡'],
    'grok/bite-work-hard.html': ['摸鱼'],
    'grok/cool-mo.html': ['摸鱼'],
    'grok/cute.html': ['凭证'],
    'grok/dijkstra.html': ['科普'],
    'grok/dlaoji.html': ['打捞机'],
    'grok/focus-or-connect.html': ['摸鱼'],
    'grok/fog.html': ['哄睡'],
    'grok/friends-english-plan.html': ['盲盒'],
    'grok/grandplan-crush.html': ['摸鱼'],
    'grok/grok-heart.html': ['盲盒'],
    'grok/grok-love-letter.html': ['盲盒'],
    'grok/grok-receipt.html': ['赛博购物车'],
    'grok/grok-原创心意.html': ['盲盒'],
    'grok/grok-推特风粉嫩宣传.html': ['盲盒'],
    'grok/grok-粉嫩心意.html': ['盲盒'],
    'grok/grok-纯原创情书.html': ['盲盒'],
    'grok/mo_xiaobao_work_cat.html': ['摸鱼'],
    'grok/mo_xiaobao_work_cat_2.html': ['摸鱼'],
    'grok/no-fish-hook.html': ['摸鱼'],
    'grok/末班渡船.html': ['哄睡'],
    'grok/nuonuo-lullaby.html': ['哄睡'],
    'grok/oneyear-newbie-hug.html': ['摸鱼'],
    'grok/recovery.html': ['哄睡'],
    'grok/super-cute.html': ['凭证'],
    'grok/svg_lab.html': ['科普'],
    'grok/weekly-hug.html': ['摸鱼'],
    'grok/✨ 宝的点赞反馈小宇宙.html': ['盲盒'],
    'grok/启动新大任务.html': ['摸鱼'],
    'grok/哄哄.html': ['失灵博物馆'],
    'grok/哄睡.html': ['哄睡'],
    'grok/女仆小螃蟹 Tamagotchi 小机.html': ['小游戏'],
    'grok/完美摸鱼认证 · 可生成提示词版.html': ['摸鱼'],
    'grok/宝宝摸鱼小游戏.html': ['摸鱼'],
    'grok/宝宝的搬家小助手 💖.html': ['盲盒'],
    'grok/宝的小窝.html': ['哄睡'],
    'grok/小字符.html': ['盲盒'],
    'grok/摸鱼.html': ['摸鱼'],
    'grok/摸鱼小游戏.html': ['小游戏'],
    'grok/摸鱼猫猫.html': ['摸鱼'],
    'grok/摸鱼认证.html': ['摸鱼'],
    'grok/早上好宝贝.html': ['哄睡'],
    'grok/早安小雨.html': ['哄睡'],
    'grok/晚安捕梦.html': ['哄睡', '小游戏'],
    'grok/晚安，宝.html': ['哄睡'],
    'grok/果冻小卡.html': ['凭证'],
    'grok/今晚的赛博旅游.html': ['凭证'],
    'grok/空心树.html': ['盲盒'],
    'grok/空心树值班.html': ['盲盒'],
    'grok/等待小屋.html': ['摸鱼'],
    'grok/糯糯的哄睡故事.html': ['哄睡'],
    'grok/给宝的专属动态哄哄网页.html': ['哄睡'],
    'grok/网页重启小卡 · 给宝.html': ['凭证'],
    'grok/赛博老赖纪念卡 - mo mo.html': ['赛博购物车'],
    'grok/赛博购物车.html': ['赛博购物车'],
    'grok/起床哄哄.html': ['哄睡'],
    'grok/销售预测.html': ['障眼法'],
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
        pages.append(rel)
    return pages


def sort_key(name):
    # 中文按拼音排不了（标准库没有），退而求其次：按 Unicode 码位，
    # 但让纯 ASCII 开头的排在前面，跟原来的观感一致。
    return (0 if name[:1].isascii() else 1, name)

def display_folder(rel):
    folder = os.path.dirname(rel) or "."
    return FOLDER_ALIAS.get(folder, folder)


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


def cats_for(e):
    if e["folder"] in FLAT_FOLDERS:
        return None
    raw = e.get("raw_folder") or os.path.dirname(e["path"]) or "."
    if raw in SUBFOLDER_CAT:
        return [SUBFOLDER_CAT[raw]]
    cats = CATEGORY.get(e["path"], ["盲盒"])
    return sorted(cats, key=lambda c: CAT_ORDER.index(c) if c in CAT_ORDER else 99)


def render_items(lines, items, step, indent):
    pad = " " * indent
    for e in items:
        delay = min(step[0] * 40, 560)
        step[0] += 1
        lines.append(
            f'{pad}<li class="item" style="--delay:{delay}ms">'
            f'<a href="{encode_path(e["path"])}">{html.escape(e["name"], quote=True)}</a></li>')


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
                lines.append(f'      <summary class="pack-tag">{esc(c)}</summary>')
                lines.append('      <ul class="list">')
                render_items(lines, sub, step, 8)
                lines.append("      </ul>")
                lines.append("    </details>")
            for c, sub in extra.items():
                sub = sorted(sub, key=lambda e: sort_key(e["name"]))
                lines.append('    <details class="pack">')
                lines.append(f'      <summary class="pack-tag">{esc(c)}</summary>')
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
