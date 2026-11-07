#!/usr/bin/env node
/* 小萌物 GIF 馆（gemini/小卡/gif-v2.html）真 GIF 与封面重拍脚本
 *
 * 按 tools/手册/GIF馆.md 规范编写：
 * - 只从本馆所属的 gemini/小卡/ 短片与同目录 studio.js 原创底稿取帧；
 * - 复用 tools/gifguan/gifenc.js（只读加载，不改动原工具）在真实浏览器画布中编码标准 GIF89a；
 * - 每件展品均将原片路径、起止秒、裁切框、画布尺寸写入 GIF 注释块，并在馆页完整展示。
 *
 * 用法：
 *   node gemini/小卡/gif-v2/extract.js            # 生成全部 22 件 .gif 与 .webp
 *   node gemini/小卡/gif-v2/extract.js 09 16      # 只重拍指定编号前缀的展品
 */
'use strict';

const { spawn } = require('child_process');
const fs = require('fs');
const http = require('http');
const os = require('os');
const path = require('path');
const { pathToFileURL } = require('url');

const OUT_DIR = __dirname;
const ROOT = path.resolve(OUT_DIR, '../../..');
const GIFENC_CODE = fs.readFileSync(path.join(ROOT, 'tools/gifguan/gifenc.js'), 'utf8');
const STUDIO_CODE = fs.readFileSync(path.join(OUT_DIR, 'studio.js'), 'utf8');

/* 锁死六只小萌物造型宪法标准色号，确保 GIF 调色板零偏色 */
const KEEP_COLORS = [
  0xd47f59, 0x120d1d, 0xe59a9a,           // Clawd 壳、眼、腮红
  0xff309b, 0x9159fe, 0x000000,           // 小粉、小紫、小黑（实测版 sRGB）
  0xe2552b, 0xfff3e3, 0x3b2520, 0xf59a8c, // StashYu 身、白尖、深棕、腮红
  0xf3e7d6, 0x4e382e, 0x79c0f0, 0xf2b8b0  // FetchMo 身、重点色、蓝眼、腮红
];

const CLIPS = [
  // ---- 原有 8 件馆藏（No.01 ~ No.08）----
  {
    slug: '01-tuizhuzuanhe', no: 'No.01', title: '退珠钻盒', mode: 'group',
    film: 'gemini/小卡/买椟还珠-gemini.html', t0: 81.0, t1: 95.4,
    segs: [[81.0, 84.4], [85.8, 87.4], [91.8, 95.4]], poster: 93.8,
    crop: [132, 286, 212, 212], size: 240, fps: 11
  },
  {
    slug: '02-ganghaozhuangxia', no: 'No.02', title: '刚好装下', mode: 'group',
    film: 'gemini/小卡/买椟还珠-gemini.html', t0: 108.8, t1: 116.0, poster: 114.6,
    crop: [136, 326, 140, 140], size: 240, fps: 12
  },
  {
    slug: '03-jijuxiezhanggui', no: 'No.03', title: '寄居蟹掌柜', mode: 'solo',
    film: 'gemini/小卡/买椟还珠-gemini.html', t0: 119.2, t1: 124.8, poster: 123.2,
    crop: [212, 332, 132, 132], size: 240, fps: 12
  },
  {
    slug: '04-hulibeizi', no: 'No.04', title: '狐狸被子', mode: 'solo',
    film: 'gemini/小卡/买椟还珠-gemini.html', t0: 104.2, t1: 108.8, poster: 107.6,
    crop: [6, 336, 128, 128], size: 240, fps: 12
  },
  {
    slug: '05-liangkeyuanzhuzi', no: 'No.05', title: '两颗圆珠子', mode: 'group',
    film: 'gemini/小卡/买椟还珠-gemini.html', t0: 151.6, t1: 169.4,
    segs: [[151.6, 154.8], [164.2, 169.4]], poster: 168.5,
    crop: [142, 248, 214, 214], size: 240, fps: 11
  },
  {
    slug: '06-mulandachuang', no: 'No.06', title: '木兰大床·晚安宝', mode: 'group',
    film: 'gemini/小卡/买椟还珠-gemini.html', t0: 182.8, t1: 190.4, poster: 188.0,
    crop: [24, 240, 312, 312], size: 240, fps: 11
  },
  {
    slug: '07-shouguanyingkeling', no: 'No.07', title: '守馆迎客铃', mode: 'group',
    studioKey: 'orig-07', dur: 2.6, poster: 0.35, size: 240, fps: 14
  },
  {
    slug: '08-mangheyaoyaole', no: 'No.08', title: '盲盒摇摇乐', mode: 'group',
    studioKey: 'orig-08', dur: 2.4, poster: 1.55, size: 240, fps: 14
  },

  // ---- 扩建新增单只版（No.09 ~ No.17）----
  {
    slug: '09-geinaozhonggaitanzi', no: 'No.09', title: '给闹钟盖毯子', mode: 'solo',
    film: 'gemini/小卡/周末懒床记（限定版）-gemini.html', t0: 15.4, t1: 24.6, poster: 23.8,
    crop: [8, 178, 152, 152], size: 240, fps: 11
  },
  {
    slug: '10-kachafencaomei', no: 'No.10', title: '咔嚓分草莓', mode: 'solo',
    film: 'gemini/小卡/小萌物生日会.html', t0: 20.2, t1: 26.8, poster: 26.0,
    crop: [70, 276, 220, 220], size: 240, fps: 12
  },
  {
    slug: '11-changtuertanhuilai', no: 'No.11', title: '长兔耳弹回来', mode: 'solo',
    film: 'gemini/小卡/守株待兔-argon.html', t0: 72.8, t1: 77.6, poster: 76.0,
    crop: [112, 366, 156, 156], size: 240, fps: 14
  },
  {
    slug: '12-yawaipingmudaodanchuang', no: 'No.12', title: '压歪屏幕倒弹窗', mode: 'solo',
    film: 'gemini/小卡/小脸蛋的电脑出问题了（限定版）-gemini.html', t0: 21.4, t1: 29.0, poster: 27.2,
    crop: [76, 204, 208, 208], size: 240, fps: 12
  },
  {
    slug: '13-zuiyuandedianjiaoshi', no: 'No.13', title: '最圆的垫脚石', mode: 'solo',
    film: 'gemini/小卡/八音盒响起来-gemini.html', t0: 51.8, t1: 57.6, poster: 54.8,
    crop: [56, 232, 166, 166], size: 240, fps: 12
  },
  {
    slug: '14-dangaodingchaxingzhu', no: 'No.14', title: '蛋糕顶插星烛', mode: 'solo',
    film: 'gemini/小卡/小萌物生日会.html', t0: 67.6, t1: 72.4, poster: 71.0,
    crop: [108, 326, 232, 232], size: 240, fps: 13
  },
  {
    slug: '15-kaopangdedaweiba', no: 'No.15', title: '烤胖的大尾巴', mode: 'solo',
    film: 'gemini/小卡/篝火夜-argon.html', t0: 100.8, t1: 110.4, poster: 104.6,
    crop: [54, 204, 244, 244], size: 240, fps: 11
  },
  {
    slug: '16-dingyingtaobengbengxing', no: 'No.16', title: '顶樱桃蹦蹦星', mode: 'solo',
    studioKey: 'orig-16', dur: 2.4, poster: 0.95, size: 240, fps: 15
  },
  {
    slug: '17-yueguixiaoyedeng', no: 'No.17', title: '月桂小夜灯', mode: 'solo',
    studioKey: 'orig-17', dur: 2.8, poster: 1.1, size: 240, fps: 13
  },

  // ---- 扩建新增群戏版（No.18 ~ No.22）----
  {
    slug: '18-zhuizheritoudingxiaozhen', no: 'No.18', title: '追着日头顶小枕', mode: 'group',
    film: 'gemini/小卡/周末懒床记（限定版）-gemini.html', t0: 32.8, t1: 41.4, poster: 40.5,
    crop: [164, 174, 180, 180], size: 240, fps: 11
  },
  {
    slug: '19-yaogunleduidahezou', no: 'No.19', title: '摇滚乐队大合奏', mode: 'group',
    film: 'gemini/小卡/试衣服argon.html', t0: 88.4, t1: 97.6, poster: 92.3,
    crop: [0, 152, 360, 360], size: 240, fps: 11
  },
  {
    slug: '20-jidingyizhuatongguan', no: 'No.20', title: '机顶一爪通关', mode: 'group',
    film: 'gemini/小卡/一币通关-gemini.html', t0: 187.5, t1: 200.8,
    segs: [[187.5, 191.8], [195.0, 200.6]], poster: 200.0,
    crop: [0, 168, 360, 360], size: 240, fps: 11
  },
  {
    slug: '21-lingdianzhuguangshouyuanwang', no: 'No.21', title: '零点烛光收愿望', mode: 'group',
    film: 'gemini/小卡/小萌物生日会.html', t0: 95.2, t1: 103.6, poster: 100.0,
    crop: [10, 250, 340, 340], size: 240, fps: 11
  },
  {
    slug: '22-daguodongruanzuodian', no: 'No.22', title: '大果冻软坐垫', mode: 'group',
    film: 'gemini/小卡/再软就变果冻了-gemini.html', t0: 112.0, t1: 123.2, poster: 122.4,
    crop: [6, 260, 348, 348], size: 240, fps: 11
  }
];

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

function httpJson(url, method = 'GET') {
  return new Promise((resolve, reject) => {
    const req = http.request(url, { method }, res => {
      let d = '';
      res.on('data', c => d += c);
      res.on('end', () => { try { resolve(JSON.parse(d)); } catch { reject(new Error(d)); } });
    });
    req.on('error', reject);
    req.end();
  });
}

function findChromeBin() {
  const candidates = [
    process.env.CHROME_BIN,
    '/usr/bin/google-chrome',
    '/usr/bin/chromium',
    '/usr/bin/chromium-browser',
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
  ].filter(Boolean);
  for (const p of candidates) if (fs.existsSync(p)) return p;
  throw new Error('Chrome binary not found; set CHROME_BIN');
}

async function launchChrome() {
  const tmpProfile = fs.mkdtempSync(path.join(os.tmpdir(), 'gifguan-cdp-'));
  const proc = spawn(findChromeBin(), [
    '--headless=new',
    '--no-sandbox',
    '--disable-gpu',
    '--disable-dev-shm-usage',
    '--allow-file-access-from-files',
    '--remote-debugging-port=0',
    '--user-data-dir=' + tmpProfile,
    'about:blank'
  ], { stdio: ['ignore', 'ignore', 'pipe'] });

  let wsUrl = null;
  proc.stderr.setEncoding('utf8');
  proc.stderr.on('data', chunk => {
    const m = chunk.match(/DevTools listening on (ws:\/\/[^\s]+)/);
    if (m) wsUrl = m[1];
  });
  for (let i = 0; i < 100 && !wsUrl; i++) await sleep(50);
  if (!wsUrl) { proc.kill(); throw new Error('Failed to launch headless Chrome'); }

  return {
    port: new URL(wsUrl).port,
    close: () => {
      try { proc.kill('SIGKILL'); } catch {}
      try { fs.rmSync(tmpProfile, { recursive: true, force: true }); } catch {}
    }
  };
}

class CDPSession {
  constructor(wsUrl) {
    this.wsUrl = wsUrl;
    this.id = 0;
    this.pending = new Map();
  }
  async connect() {
    this.ws = new WebSocket(this.wsUrl);
    await new Promise((res, rej) => {
      this.ws.addEventListener('open', res, { once: true });
      this.ws.addEventListener('error', rej, { once: true });
    });
    this.ws.addEventListener('message', ev => {
      const msg = JSON.parse(String(ev.data));
      if (msg.id && this.pending.has(msg.id)) {
        const { resolve, reject } = this.pending.get(msg.id);
        this.pending.delete(msg.id);
        if (msg.error) reject(new Error(JSON.stringify(msg.error)));
        else resolve(msg.result);
      }
    });
  }
  send(method, params = {}) {
    const id = ++this.id;
    this.ws.send(JSON.stringify({ id, method, params }));
    return new Promise((resolve, reject) => this.pending.set(id, { resolve, reject }));
  }
  close() { try { this.ws.close(); } catch {} }
}

async function openFilmPage(port, filmRel) {
  const target = await httpJson(`http://127.0.0.1:${port}/json/new?about:blank`, 'PUT');
  const cdp = new CDPSession(target.webSocketDebuggerUrl);
  await cdp.connect();
  await cdp.send('Page.enable');
  await cdp.send('Runtime.enable');

  const fullPath = path.join(ROOT, filmRel);
  let html = fs.readFileSync(fullPath, 'utf8');
  if (html.includes('function caption(')) {
    html = html.replace('function caption(', 'function caption(){}\nfunction __caption_orig(');
  }
  const targetHref = pathToFileURL(fullPath).href;
  await cdp.send('Fetch.enable', { patterns: [{ urlPattern: '*' }] });
  cdp.ws.addEventListener('message', async ev => {
    const msg = JSON.parse(String(ev.data));
    if (msg.method === 'Fetch.requestPaused') {
      const reqUrl = msg.params.request.url.split('#')[0];
      if (decodeURIComponent(reqUrl) === decodeURIComponent(targetHref)) {
        await cdp.send('Fetch.fulfillRequest', {
          requestId: msg.params.requestId,
          responseCode: 200,
          responseHeaders: [{ name: 'Content-Type', value: 'text/html; charset=utf-8' }],
          body: Buffer.from(html, 'utf8').toString('base64')
        });
      } else {
        await cdp.send('Fetch.continueRequest', { requestId: msg.params.requestId });
      }
    }
  });

  await cdp.send('Page.navigate', { url: targetHref });
  for (let i = 0; i < 60; i++) {
    const r = await cdp.send('Runtime.evaluate', {
      expression: 'Boolean(window.FILM && window.FILM.render)',
      returnByValue: true
    });
    if (r.result && r.result.value) break;
    await sleep(100);
  }
  await cdp.send('Runtime.evaluate', { expression: GIFENC_CODE });
  return cdp;
}

async function openStudioPage(port) {
  const target = await httpJson(`http://127.0.0.1:${port}/json/new?about:blank`, 'PUT');
  const cdp = new CDPSession(target.webSocketDebuggerUrl);
  await cdp.connect();
  await cdp.send('Page.enable');
  await cdp.send('Runtime.enable');
  await cdp.send('Runtime.evaluate', { expression: GIFENC_CODE });
  await cdp.send('Runtime.evaluate', { expression: STUDIO_CODE });
  return cdp;
}

async function encodeFilmClip(cdp, clip) {
  const expr = `(() => {
    const clip = ${JSON.stringify(clip)};
    const keep = ${JSON.stringify(KEEP_COLORS)};
    if (FILM.pause) FILM.pause();
    const W = FILM.W || 360, H = FILM.H || 640;
    if (FILM.setup) FILM.setup(720);
    const scale = FILM.canvas.width / W;
    const [cx, cy, cw, ch] = clip.crop;
    const outSize = clip.size || 240;

    const dst = document.createElement('canvas');
    dst.width = outSize; dst.height = outSize;
    const dctx = dst.getContext('2d', { willReadFrequently: true });
    dctx.imageSmoothingEnabled = true;
    dctx.imageSmoothingQuality = 'high';

    const dt = 1 / clip.fps;
    const cs = Math.max(4, Math.round(100 / clip.fps));
    const segs = clip.segs || [[clip.t0, clip.t1]];
    const ts = [];
    for (const [a, b] of segs) {
      for (let t = a; t < b - 1e-6; t += dt) ts.push(Math.round(t * 1000) / 1000);
    }

    function snapAt(t) {
      FILM.render(t);
      dctx.drawImage(FILM.canvas, cx * scale, cy * scale, cw * scale, ch * scale, 0, 0, outSize, outSize);
      return dctx.getImageData(0, 0, outSize, outSize).data;
    }

    const hist = GIFENC.hist();
    for (const t of ts) hist.add(snapAt(t), 2);
    const pal = GIFENC.palette(hist, { keep });
    const comment = clip.film + ' @ ' + clip.t0 + '-' + clip.t1 + 's crop=' + clip.crop.join(',') + ' canvas=' + W + 'x' + H;
    const enc = GIFENC.encoder(outSize, outSize, pal, { dither: 5, lossy: 160, comment });
    for (const t of ts) enc.frame(snapAt(t), cs);
    const bytes = enc.finish();

    snapAt(clip.poster !== undefined ? clip.poster : ts[0]);
    const webp = dst.toDataURL('image/webp', 0.88).split(',')[1];

    let bin = '';
    for (let i = 0; i < bytes.length; i += 8192) {
      bin += String.fromCharCode.apply(null, bytes.subarray(i, i + 8192));
    }
    return { gifB64: btoa(bin), webpB64: webp, frames: enc.frames, rawFrames: ts.length };
  })()`;
  const res = await cdp.send('Runtime.evaluate', { expression: expr, returnByValue: true });
  return res.result.value;
}

async function encodeStudioClip(cdp, clip) {
  const expr = `(() => {
    const clip = ${JSON.stringify(clip)};
    const keep = ${JSON.stringify(KEEP_COLORS)};
    const outSize = clip.size || 240;
    const hi = document.createElement('canvas');
    hi.width = outSize * 2; hi.height = outSize * 2;
    const dst = document.createElement('canvas');
    dst.width = outSize; dst.height = outSize;
    const dctx = dst.getContext('2d', { willReadFrequently: true });
    dctx.imageSmoothingEnabled = true;
    dctx.imageSmoothingQuality = 'high';

    const dt = 1 / clip.fps;
    const cs = Math.max(4, Math.round(100 / clip.fps));
    const ts = [];
    for (let t = 0; t < clip.dur - 1e-6; t += dt) ts.push(Math.round(t * 1000) / 1000);

    function snapAt(t) {
      STUDIO.render(clip.studioKey, t, hi);
      dctx.clearRect(0, 0, outSize, outSize);
      dctx.drawImage(hi, 0, 0, outSize, outSize);
      return dctx.getImageData(0, 0, outSize, outSize).data;
    }

    const hist = GIFENC.hist();
    for (const t of ts) hist.add(snapAt(t), 2);
    const pal = GIFENC.palette(hist, { keep });
    const comment = 'original: gemini/小卡/gif-v2/studio.js#' + clip.studioKey + ' dur=' + clip.dur + 's';
    const enc = GIFENC.encoder(outSize, outSize, pal, { dither: 4, lossy: 120, comment });
    for (const t of ts) enc.frame(snapAt(t), cs);
    const bytes = enc.finish();

    snapAt(clip.poster !== undefined ? clip.poster : 0);
    const webp = dst.toDataURL('image/webp', 0.88).split(',')[1];

    let bin = '';
    for (let i = 0; i < bytes.length; i += 8192) {
      bin += String.fromCharCode.apply(null, bytes.subarray(i, i + 8192));
    }
    return { gifB64: btoa(bin), webpB64: webp, frames: enc.frames, rawFrames: ts.length };
  })()`;
  const res = await cdp.send('Runtime.evaluate', { expression: expr, returnByValue: true });
  return res.result.value;
}

async function main() {
  const filterArgs = process.argv.slice(2);
  const todo = filterArgs.length
    ? CLIPS.filter(c => filterArgs.some(f => c.slug.startsWith(f) || c.no.includes(f)))
    : CLIPS;

  const chrome = await launchChrome();
  try {
    const byFilm = new Map();
    const originals = [];
    for (const c of todo) {
      if (c.studioKey) originals.push(c);
      else {
        if (!byFilm.has(c.film)) byFilm.set(c.film, []);
        byFilm.get(c.film).push(c);
      }
    }

    for (const [film, list] of byFilm.entries()) {
      const cdp = await openFilmPage(chrome.port, film);
      for (const clip of list) {
        const out = await encodeFilmClip(cdp, clip);
        const gifBuf = Buffer.from(out.gifB64, 'base64');
        const webpBuf = Buffer.from(out.webpB64, 'base64');
        fs.writeFileSync(path.join(OUT_DIR, clip.slug + '.gif'), gifBuf);
        fs.writeFileSync(path.join(OUT_DIR, clip.slug + '.webp'), webpBuf);
        console.log(`${clip.no} ${clip.title} -> ${clip.slug}.gif (${(gifBuf.length / 1024).toFixed(1)} KB, ${out.frames} frames)`);
      }
      cdp.close();
    }

    if (originals.length) {
      const cdp = await openStudioPage(chrome.port);
      for (const clip of originals) {
        const out = await encodeStudioClip(cdp, clip);
        const gifBuf = Buffer.from(out.gifB64, 'base64');
        const webpBuf = Buffer.from(out.webpB64, 'base64');
        fs.writeFileSync(path.join(OUT_DIR, clip.slug + '.gif'), gifBuf);
        fs.writeFileSync(path.join(OUT_DIR, clip.slug + '.webp'), webpBuf);
        console.log(`${clip.no} ${clip.title} [原创] -> ${clip.slug}.gif (${(gifBuf.length / 1024).toFixed(1)} KB, ${out.frames} frames)`);
      }
      cdp.close();
    }
  } finally {
    chrome.close();
  }
}

if (require.main === module) {
  main().catch(err => { console.error(err); process.exit(1); });
}
