#!/usr/bin/env node
/* 小萌物 GIF 馆的取帧机：把馆藏清单里的每一件做成真的 GIF。
 *
 * 馆在 claude/小卡/小萌物GIF馆.html，藏品清单就写在那一页里
 * （<script type="application/json" id="cang"> 那一段），GIF 和封面放在旁边的 claude/小卡/小萌物GIF馆/。
 *
 * 用法（云端 node 自带 playwright；别的电脑先 npm i -g playwright，Chromium 用它自带的）：
 *   node tools/gifguan/extract.js                 只做还没有 GIF 的藏品（新加进清单的）
 *   node tools/gifguan/extract.js 7 12            只（重）做编号 7 和 12
 *   node tools/gifguan/extract.js --all           全部重做
 *   node tools/gifguan/extract.js --sheet 7       给编号 7 出一张取景小样（红框是裁切框），不写 GIF
 *   node tools/gifguan/extract.js --look claude/小卡/某部.html 50 62 [0.5]
 *                                                 还没进清单的时候先看片：50 到 62 秒，每 0.5 秒一格
 *   小样存在系统临时目录，路径会打印出来，拿去看图就行。
 *
 * 加一件新藏品（以后的 cc 照这个来）：
 *   1. 先用 --look 看片，挑起止秒和裁切框（片子的坐标是 360×640，左上角是原点）。
 *   2. 在清单最后加一条，编号接着往下排，已有的编号别改、别重排、别回收：
 *        {"no": 下一个号, "id": "英文小名", "name": "展品名", "who": ["FetchMo"],
 *         "from": {"film": "claude/小卡/某部.html", "t0": 55.6, "t1": 61.0},
 *         "crop": [x, y, 宽, 高], "note": "展签上那段话"}
 *      原创的不写 from，写 "studio": "片场里的名字"（片场在 tools/gifguan/studio.html，新原创先在那里画好）。
 *      可选：scale（几倍画，默认 2）、fps（默认 20）、hold（最后一格多停几秒）、poster（封面取第几秒）、
 *      dither（渐变多、色带明显时给 10～16）、lossy（画面里有细碎闪动、文件太大时给 100～300）、
 *      subs（true 就把原片字幕一起压进画面，默认不压）、
 *      hidden（true 是隐藏款，馆里不直接摆出来）。
 *   3. --sheet 看一眼取景，再不带参数跑一遍：工具会做出 GIF 和封面，
 *      把片名、场次、那几秒里的字幕、尺寸帧数大小这些「量出来的」字段写回清单——这些别手填。
 *   4. 开馆页看一眼，跑店里那三项检查，提交。
 *
 * 取帧走的是原片自己留的「导视频用的口子」window.FILM：setup(宽) 定清晰度，render(t) 画第 t 秒。
 * 原片文件一个字都不改；只是在载入时把字幕那一个画笔换成空的（subs 为 true 时不换），画面里就没有字幕条，
 * 字幕原话由工具从原片的字幕本里抄出来，写在展签上。
 */
'use strict';
const fs = require('fs');
const os = require('os');
const path = require('path');
const { pathToFileURL } = require('url');
const { chromium } = require('playwright');

const ROOT = path.resolve(__dirname, '..', '..');
const PAGE = path.join(ROOT, 'claude', '小卡', '小萌物GIF馆.html');
const OUT = path.join(ROOT, 'claude', '小卡', '小萌物GIF馆');
const STUDIO = path.join(__dirname, 'studio.html');
const ENC = path.join(__dirname, 'gifenc.js');
const BEGIN = '<script type="application/json" id="cang">';
const END = '</script>';

/* 小萌物自己的颜色：只要画面里有，调色板里一定原样留着，不许被量化挪偏 */
const KEEP = ['d47f59', '120d1d', 'ff309b', '9159fe', '000000', 'e2552b', 'fff3e3', '3b2520',
  'f3e7d6', '4e382e', '79c0f0', 'f59a8c', 'f2b8b0', 'ffffff'].map(h => parseInt(h, 16));

/* 计算出来、写回清单的字段：手写的那几样排前面，这些排后面 */
const KEY_ORDER = ['no', 'id', 'name', 'who', 'hall', 'hidden', 'from', 'studio', 'crop', 'scale', 'fps', 'hold',
  'poster', 'dither', 'lossy', 'subs', 'note', 'file', 'cover', 'gif'];

function readSpec() {
  const s = fs.readFileSync(PAGE, 'utf8');
  /* 认最后一个：清单在页面最底下。页面开头的说明里万一抄了这一行，也不会认错地方 */
  const a = s.lastIndexOf(BEGIN);
  if (a < 0) throw new Error('馆页里找不到藏品清单：' + BEGIN);
  const b = s.indexOf(END, a + BEGIN.length);
  const body = s.slice(a + BEGIN.length, b);
  if (!/^\s*\[/.test(body)) throw new Error('藏品清单那一段不是一个 JSON 数组，先别动，去馆页里看看');
  return { s, a: a + BEGIN.length, b, list: JSON.parse(body) };
}

function fmtJSON(list) {
  const one = v => JSON.stringify(v).replace(/</g, '\\u003c');
  return '\n[\n' + list.map(ex => {
    const keys = Object.keys(ex).sort((p, q) => {
      const i = KEY_ORDER.indexOf(p), j = KEY_ORDER.indexOf(q);
      return (i < 0 ? 99 : i) - (j < 0 ? 99 : j);
    });
    return '  {\n' + keys.map(k => '    ' + one(k) + ': ' + one(ex[k])).join(',\n') + '\n  }';
  }).join(',\n') + '\n]\n';
}

function writeSpec(spec) {
  const s = spec.s.slice(0, spec.a) + fmtJSON(spec.list) + spec.s.slice(spec.b);
  fs.writeFileSync(PAGE, s);
}

function pad3(n) { return String(n).padStart(3, '0'); }
function fileOf(ex) { return pad3(ex.no) + '-' + ex.id + '.gif'; }
function coverOf(ex) { return pad3(ex.no) + '-' + ex.id + '.webp'; }
function clock(t) { const s = Math.floor(t + 1e-6); return Math.floor(s / 60) + ':' + String(s % 60).padStart(2, '0'); }

/* 开一个原片（或者片场），字幕画笔按需换成空的，再把编码器塞进去 */
async function openSource(browser, ex) {
  const page = await browser.newPage({ viewport: { width: 400, height: 760 } });
  let file, hash = '';
  if (ex.studio) { file = STUDIO; hash = '#' + encodeURIComponent(ex.studio); }
  else file = path.join(ROOT, ex.from.film);
  if (!fs.existsSync(file)) throw new Error('找不到原片：' + file);
  let html = fs.readFileSync(file, 'utf8');
  if (!ex.subs && !ex.studio) {
    if (html.indexOf('function caption(') < 0) throw new Error('这部片子没有 caption() 画笔，加 "subs": true 或者另想办法：' + file);
    html = html.replace('function caption(', 'function caption(){}\nfunction __caption_kept(');
  }
  const href = pathToFileURL(file).href;
  await page.route('**/*', async route => {
    const url = route.request().url().split('#')[0];
    if (url === href || decodeURIComponent(url) === decodeURIComponent(href)) {
      return route.fulfill({ body: html, contentType: 'text/html; charset=utf-8' });
    }
    return route.continue();
  });
  const errors = [];
  page.on('pageerror', e => errors.push(String(e)));
  await page.goto(href + hash);
  await page.waitForFunction(() => window.FILM && window.FILM.render, null, { timeout: 15000 });
  await page.addScriptTag({ path: ENC });
  return { page, errors };
}

/* 原片的字幕本：片名、第 t0 秒在哪一场、[t0,t1] 里出现过哪几句 */
async function readBook(page, t0, t1) {
  return page.evaluate(([t0, t1]) => {
    let start = 0; const lines = []; let scene = null;
    document.querySelectorAll('.sc').forEach(el => {
      const dur = +el.dataset.dur;
      if (t0 >= start && t0 < start + dur) scene = [el.dataset.card || '', el.dataset.sub || ''].filter(Boolean).join(' · ');
      el.querySelectorAll('p[data-t]').forEach(p => {
        const a = p.dataset.t.split('-').map(Number), g0 = start + a[0], g1 = start + a[1];
        if (g1 > t0 + .15 && g0 < t1 - .15) {
          const o = { t: Math.round(g0 * 10) / 10, s: p.textContent.trim() };
          if (p.dataset.say) o.say = p.dataset.say;
          lines.push(o);
        }
      });
      start += dur;
    });
    return { title: document.title, scene, lines, total: Math.round(start * 10) / 10 };
  }, [t0, t1]);
}

/* 两遍：先数颜色定调色板，再逐格编码。画面一直在页面里，只把编好的字节交回来 */
async function encode(page, ex, comment) {
  return page.evaluate(async ({ ex, keep, comment }) => {
    const sc = ex.scale || 2, fps = ex.fps || 20;
    FILM.setup(FILM.W * sc);
    const k = FILM.canvas.width / FILM.W;
    const c = ex.crop || [0, 0, FILM.W, FILM.H];
    const X = Math.round(c[0] * k), Y = Math.round(c[1] * k), w = Math.round(c[2] * k), h = Math.round(c[3] * k);
    const t0 = ex.from ? ex.from.t0 : (ex.t0 || 0), t1 = ex.from ? ex.from.t1 : (ex.t1 || FILM.TOTAL);
    const n = Math.max(1, Math.round((t1 - t0) * fps));
    const ctx = FILM.canvas.getContext('2d');
    const grab = t => { FILM.render(t); return ctx.getImageData(X, Y, w, h).data; };
    const hist = GIFENC.hist();
    for (let i = 0; i < n; i++) hist.add(grab(t0 + i / fps), 2);
    const pal = GIFENC.palette(hist, { keep });
    const enc = GIFENC.encoder(w, h, pal, { comment, dither: ex.dither || 0, lossy: ex.lossy || 0 });
    for (let i = 0; i < n; i++) {
      let cs = Math.round(100 * (i + 1) / fps) - Math.round(100 * i / fps);
      if (i === n - 1) cs += Math.round((ex.hold || 0) * 100);
      enc.frame(grab(t0 + i / fps), cs);
    }
    const gif = enc.finish();
    /* 封面：同一个裁切框里的一格，存 WebP（同样大小，PNG 要十倍）。馆里格子上摆的是它，点开才换成 GIF */
    const pt = ex.poster !== undefined ? ex.poster : (t0 + t1) / 2;
    FILM.render(pt);
    const cv = document.createElement('canvas'); cv.width = w; cv.height = h;
    cv.getContext('2d').drawImage(FILM.canvas, X, Y, w, h, 0, 0, w, h);
    const cover = cv.toDataURL('image/webp', .9).split(',')[1];
    let bin = '';
    for (let i = 0; i < gif.length; i += 0x8000) bin += String.fromCharCode.apply(null, gif.subarray(i, i + 0x8000));
    const total = Math.round(100 * n / fps) + Math.round((ex.hold || 0) * 100);
    return { gif: btoa(bin), cover, w, h, frames: enc.frames, ms: total * 10, colors: pal.colors.length };
  }, { ex, keep: KEEP, comment });
}

/* 取景小样：一排排小格，红框是裁切框 */
async function contactSheet(page, o) {
  const png = await page.evaluate(o => {
    FILM.setup(360);
    const k = FILM.canvas.width / FILM.W, cw = FILM.canvas.width / 2, ch = FILM.canvas.height / 2, cols = o.cols || 8, lab = 16;
    const ts = []; for (let t = o.t0; t <= o.t1 + 1e-6; t += o.step) ts.push(Math.round(t * 1000) / 1000);
    const rows = Math.ceil(ts.length / cols);
    const sh = document.createElement('canvas'); sh.width = cols * (cw + 4); sh.height = rows * (ch + lab + 4);
    const c = sh.getContext('2d'); c.fillStyle = '#fff'; c.fillRect(0, 0, sh.width, sh.height);
    ts.forEach((t, i) => {
      FILM.render(t);
      const x = (i % cols) * (cw + 4), y = Math.floor(i / cols) * (ch + lab + 4) + lab;
      c.drawImage(FILM.canvas, x, y, cw, ch);
      if (o.crop) { c.strokeStyle = '#f00'; c.lineWidth = 2; c.strokeRect(x + o.crop[0] * k / 2, y + o.crop[1] * k / 2, o.crop[2] * k / 2, o.crop[3] * k / 2); }
      c.fillStyle = (o.in && (t < o.in[0] || t > o.in[1])) ? '#999' : '#000';
      c.font = 'bold 13px sans-serif'; c.fillText(t.toFixed(2), x + 3, y - 3);
    });
    return sh.toDataURL('image/png').split(',')[1];
  }, o);
  return Buffer.from(png, 'base64');
}

async function main() {
  const args = process.argv.slice(2);
  const browser = await chromium.launch();
  try {
    if (args[0] === '--look') {
      const [film, a, b, st] = args.slice(1);
      const ex = { from: { film, t0: +a, t1: +b } };
      const { page } = await openSource(browser, ex);
      const out = path.join(os.tmpdir(), 'gifguan-look.png');
      fs.writeFileSync(out, await contactSheet(page, { t0: +a, t1: +b, step: +(st || .5) }));
      console.log('小样：' + out);
      return;
    }
    const spec = readSpec();
    if (args[0] === '--sheet') {
      const ex = spec.list.find(e => e.no === +args[1]);
      if (!ex) throw new Error('清单里没有编号 ' + args[1]);
      const { page } = await openSource(browser, ex);
      const t0 = ex.from ? ex.from.t0 : 0;
      const t1 = ex.from ? ex.from.t1 : await page.evaluate(() => FILM.TOTAL);
      const out = path.join(os.tmpdir(), 'gifguan-sheet-' + ex.no + '.png');
      fs.writeFileSync(out, await contactSheet(page, { t0: Math.max(0, t0 - 1), t1: t1 + 1, step: .25, crop: ex.crop, in: [t0, t1] }));
      console.log('小样：' + out);
      return;
    }
    const all = args.includes('--all');
    const pick = args.filter(a => /^\d+$/.test(a)).map(Number);
    fs.mkdirSync(OUT, { recursive: true });
    const seen = new Set();
    for (const ex of spec.list) {
      if (seen.has(ex.no)) throw new Error('编号重复：' + ex.no);
      seen.add(ex.no);
      if (!/^[a-z0-9-]+$/.test(ex.id || '')) throw new Error('编号 ' + ex.no + ' 的 id 只用小写英文、数字和短横');
    }
    let done = 0;
    for (const ex of spec.list) {
      const want = all || pick.includes(ex.no) || (!pick.length && !fs.existsSync(path.join(OUT, fileOf(ex))));
      if (!want) continue;
      const { page, errors } = await openSource(browser, ex);
      let comment;
      if (ex.from) {
        const book = await readBook(page, ex.from.t0, ex.from.t1);
        ex.from.title = book.title;
        ex.from.scene = book.scene;
        ex.from.lines = book.lines;
        ex.from.total = book.total;
        comment = '小萌物 GIF 馆 No.' + pad3(ex.no) + ' ' + ex.name + ' — 出自《' + book.title + '》' +
          (book.scene ? book.scene + ' ' : '') + clock(ex.from.t0) + '–' + clock(ex.from.t1) +
          '（' + ex.from.t0 + 's–' + ex.from.t1 + 's），' + ex.from.film + ' · 画面逐格取自原片 · cc';
      } else {
        comment = '小萌物 GIF 馆 No.' + pad3(ex.no) + ' ' + ex.name + ' — 馆里原创 · cc';
      }
      const r = await encode(page, ex, comment);
      if (errors.length) throw new Error('编号 ' + ex.no + ' 渲染时报错：' + errors.join(' | '));
      fs.writeFileSync(path.join(OUT, fileOf(ex)), Buffer.from(r.gif, 'base64'));
      fs.writeFileSync(path.join(OUT, coverOf(ex)), Buffer.from(r.cover, 'base64'));
      ex.file = fileOf(ex);
      ex.cover = coverOf(ex);
      const bytes = fs.statSync(path.join(OUT, ex.file)).size;
      ex.gif = { w: r.w, h: r.h, frames: r.frames, ms: r.ms, kb: Math.round(bytes / 1024) };
      await page.close();
      done++;
      console.log('No.' + pad3(ex.no) + ' ' + ex.name + '：' + r.w + '×' + r.h + '，' + r.frames + ' 格，' +
        (r.ms / 1000).toFixed(2) + ' 秒，' + r.colors + ' 色，' + ex.gif.kb + ' KB');
    }
    writeSpec(spec);
    console.log(done ? '做好了 ' + done + ' 件，清单已写回馆页。' : '没有要做的（加新藏品，或者带编号重做）。');
  } finally {
    await browser.close();
  }
}

main().catch(e => { console.error(String(e && e.message || e)); process.exit(1); });
