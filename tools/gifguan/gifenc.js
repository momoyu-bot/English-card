/* 小萌物 GIF 馆的 GIF 编码器：在浏览器里跑，被 tools/gifguan/extract.js 塞进原片页面用。
 *
 * 不依赖任何外部库，也不需要 ffmpeg：画面从原片的 canvas 里直接取，在页面里编成 GIF89a，
 * 只把编好的字节交回 node 去写文件。
 *
 * 用法分两遍（画面是 render(t) 现画的，画两遍比把一百多格全攒在内存里省）：
 *   var h = GIFENC.hist();  每一格 h.add(rgba)          // 第一遍：数颜色
 *   var pal = GIFENC.palette(h);                         // 定 255 色的调色板（第 256 色留给透明）
 *   var e = GIFENC.encoder(w, h, pal, {comment: '…'});   // 第二遍：每一格 e.frame(rgba, 厘秒)
 *   var bytes = e.finish();                              // Uint8Array
 *
 * 店里的画大多是纯平色：出现得多的颜色原样进调色板（小萌物的身子、背景一格不偏色），
 * 剩下的渐变、光晕、字边用中位切分凑满。抖动只抖那些不在调色板里的颜色，纯色块不会起噪点。
 * 前后两格一样就把停顿加到上一格上；不一样就只写变了的那一块，没变的像素记成透明。
 * opt.lossy 给一个数（100～300），差得很少的颜色变化就当没变：画面几乎看不出，文件能小一半。
 */
(function (root) {
  'use strict';

  var TRANSPARENT = 255;

  function Hist() { this.m = new Map(); this.n = 0; }
  /* step：隔几个像素数一次。数颜色不必每个都数，第一遍快一点 */
  Hist.prototype.add = function (d, step) {
    step = step || 1;
    var m = this.m, i, c, v, stride = 4 * step;
    for (i = 0; i < d.length; i += stride) {
      c = (d[i] << 16) | (d[i + 1] << 8) | d[i + 2];
      v = m.get(c);
      m.set(c, v === undefined ? 1 : v + 1);
    }
    this.n += Math.ceil(d.length / stride);
  };

  function dist2(a, b) {
    var dr = ((a >> 16) & 255) - ((b >> 16) & 255),
        dg = ((a >> 8) & 255) - ((b >> 8) & 255),
        db = (a & 255) - (b & 255);
    return 2 * dr * dr + 4 * dg * dg + 3 * db * db;
  }

  /* 中位切分：每次挑总误差最大的一盒，沿最长的那一轴在加权中位处切开 */
  function medianCut(cols, k) {
    if (!cols.length || k <= 0) return [];
    function stats(box) {
      var n = 0, sr = 0, sg = 0, sb = 0, qr = 0, qg = 0, qb = 0;
      var mnr = 255, mng = 255, mnb = 255, mxr = 0, mxg = 0, mxb = 0;
      for (var i = 0; i < box.length; i++) {
        var c = box[i][0], w = box[i][1], r = (c >> 16) & 255, g = (c >> 8) & 255, b = c & 255;
        n += w; sr += r * w; sg += g * w; sb += b * w; qr += r * r * w; qg += g * g * w; qb += b * b * w;
        if (r < mnr) mnr = r; if (r > mxr) mxr = r; if (g < mng) mng = g; if (g > mxg) mxg = g;
        if (b < mnb) mnb = b; if (b > mxb) mxb = b;
      }
      var err = 2 * (qr - sr * sr / n) + 4 * (qg - sg * sg / n) + 3 * (qb - sb * sb / n);
      var rr = 2 * (mxr - mnr), rg = 4 * (mxg - mng), rb = 3 * (mxb - mnb);
      return { items: box, n: n, err: box.length > 1 ? err : 0, axis: rr >= rg && rr >= rb ? 16 : rg >= rb ? 8 : 0,
               mean: (Math.round(sr / n) << 16) | (Math.round(sg / n) << 8) | Math.round(sb / n) };
    }
    var boxes = [stats(cols)];
    while (boxes.length < k) {
      var bi = -1, be = 0;
      for (var i = 0; i < boxes.length; i++) if (boxes[i].err > be) { be = boxes[i].err; bi = i; }
      if (bi < 0) break;
      var bx = boxes[bi], ax = bx.axis;
      var items = bx.items.slice().sort(function (p, q) { return ((p[0] >> ax) & 255) - ((q[0] >> ax) & 255); });
      var half = bx.n / 2, acc = 0, cut = 1;
      for (var j = 0; j < items.length - 1; j++) { acc += items[j][1]; if (acc >= half) { cut = j + 1; break; } cut = j + 1; }
      boxes.splice(bi, 1, stats(items.slice(0, cut)), stats(items.slice(cut)));
    }
    return boxes.map(function (b) { return b.mean; });
  }

  /* 调色板：
     1. opt.keep 里的颜色（小萌物的身子、眼睛、腮红）只要画面里出现了，一定原样留下；
     2. 再按出现的多少，把成片的纯色原样留下——跟已经留下的几乎一样的不算（渐变一行一个色，别让它挤占位子）；
     3. 剩下的位子给中位切分，管渐变、光晕和字边。 */
  function palette(h, opt) {
    opt = opt || {};
    var max = 255, all = [];
    h.m.forEach(function (w, c) { all.push([c, w]); });
    all.sort(function (a, b) { return b[1] - a[1]; });
    if (all.length <= max) return { colors: all.map(function (a) { return a[0]; }), exact: all.length };
    var exactMin = opt.exactMin || Math.max(12, Math.round(h.n * 1.5e-5));
    var maxExact = opt.maxExact || 160;
    var exact = [], rest = [], i, j;
    (opt.keep || []).forEach(function (c) { if (h.m.has(c) && exact.indexOf(c) < 0) exact.push(c); });
    for (i = 0; i < all.length; i++) {
      var c = all[i][0];
      if (exact.indexOf(c) >= 0) continue;
      var ok = exact.length < maxExact && all[i][1] >= exactMin;
      if (ok) for (j = 0; j < exact.length; j++) if (dist2(c, exact[j]) < 48) { ok = false; break; }
      if (ok) exact.push(c); else rest.push(all[i]);
    }
    /* 跟留下的纯色几乎一样的（字边、半透明的边），反正会落到那一格上，不占切分的位子 */
    var far = rest.filter(function (a) {
      for (var j = 0; j < exact.length; j++) if (dist2(a[0], exact[j]) < 90) return false;
      return true;
    });
    var cut = medianCut(far, max - exact.length);
    return { colors: exact.concat(cut), exact: exact.length };
  }

  var BAYER = [0, 8, 2, 10, 12, 4, 14, 6, 3, 11, 1, 9, 15, 7, 13, 5];

  function Mapper(pal, dither) {
    this.cols = pal.colors;
    this.exactSet = new Map();
    for (var i = 0; i < this.cols.length; i++) if (!this.exactSet.has(this.cols[i])) this.exactSet.set(this.cols[i], i);
    this.cache = new Map();
    this.dither = dither || 0;
  }
  Mapper.prototype.nearest = function (c) {
    var cols = this.cols, best = 0, bd = Infinity;
    for (var i = 0; i < cols.length; i++) { var d = dist2(c, cols[i]); if (d < bd) { bd = d; best = i; } }
    return best;
  };
  Mapper.prototype.map = function (d, w, h, out) {
    var ex = this.exactSet, cache = this.cache, dz = this.dither, p = 0, x, y, c, v, key, off, r, g, b;
    for (y = 0; y < h; y++) {
      for (x = 0; x < w; x++, p++) {
        var i4 = p * 4;
        c = (d[i4] << 16) | (d[i4 + 1] << 8) | d[i4 + 2];
        v = ex.get(c);
        if (v !== undefined) { out[p] = v; continue; }
        if (dz) {
          var bi = ((y & 3) << 2) | (x & 3);
          key = c * 16 + bi;
          v = cache.get(key);
          if (v === undefined) {
            off = (BAYER[bi] - 7.5) / 16 * dz;
            r = Math.max(0, Math.min(255, Math.round(((c >> 16) & 255) + off)));
            g = Math.max(0, Math.min(255, Math.round(((c >> 8) & 255) + off)));
            b = Math.max(0, Math.min(255, Math.round((c & 255) + off)));
            v = this.nearest((r << 16) | (g << 8) | b);
            cache.set(key, v);
          }
        } else {
          v = cache.get(c);
          if (v === undefined) { v = this.nearest(c); cache.set(c, v); }
        }
        out[p] = v;
      }
    }
  };

  /* ---------- 写字节 ---------- */
  function Bytes() { this.a = new Uint8Array(1 << 16); this.n = 0; }
  Bytes.prototype.grow = function (k) {
    if (this.n + k <= this.a.length) return;
    var len = this.a.length; while (len < this.n + k) len *= 2;
    var b = new Uint8Array(len); b.set(this.a.subarray(0, this.n)); this.a = b;
  };
  Bytes.prototype.byte = function (v) { this.grow(1); this.a[this.n++] = v & 255; };
  Bytes.prototype.u16 = function (v) { this.byte(v); this.byte(v >> 8); };
  Bytes.prototype.str = function (s) { for (var i = 0; i < s.length; i++) this.byte(s.charCodeAt(i)); };
  Bytes.prototype.bytes = function (arr) { this.grow(arr.length); this.a.set(arr, this.n); this.n += arr.length; };
  Bytes.prototype.done = function () { return this.a.slice(0, this.n); };

  /* GIF 的 LZW：码长从 9 位长到 12 位，表满了发一个清除码重来。
     码长什么时候加一位，跟解码器对齐的办法照老 compress 那套：发完一个码、下一个空号到了 2 的整次方就加。
     散列表的大小必须是质数，二次探测才走得遍 */
  var TABLE_SIZE = 16381;
  function lzw(px, out) {
    var minCode = 8, clear = 256, eoi = 257;
    var codeSize = 9, next = 258;
    var keys = new Int32Array(TABLE_SIZE), vals = new Int16Array(TABLE_SIZE);
    keys.fill(-1);
    var block = new Uint8Array(255), bn = 0, acc = 0, bits = 0;
    out.byte(minCode);
    function emit(code) {
      acc |= code << bits; bits += codeSize;
      while (bits >= 8) {
        block[bn++] = acc & 255; acc >>>= 8; bits -= 8;
        if (bn === 255) { out.byte(255); out.bytes(block); bn = 0; }
      }
    }
    function flushBits() {
      while (bits > 0) {
        block[bn++] = acc & 255; acc >>>= 8; bits = Math.max(0, bits - 8);
        if (bn === 255) { out.byte(255); out.bytes(block); bn = 0; }
      }
      if (bn) { out.byte(bn); out.bytes(block.subarray(0, bn)); bn = 0; }
      out.byte(0);
    }
    emit(clear);
    if (!px.length) { emit(eoi); flushBits(); return; }
    var prefix = px[0];
    for (var i = 1; i < px.length; i++) {
      var k = px[i], key = (prefix << 8) | k;
      var hsh = ((k << 12) ^ prefix) % TABLE_SIZE, step = hsh === 0 ? 1 : TABLE_SIZE - hsh, found = -1;
      while (keys[hsh] !== -1) {
        if (keys[hsh] === key) { found = vals[hsh]; break; }
        hsh -= step; if (hsh < 0) hsh += TABLE_SIZE;
      }
      if (found >= 0) { prefix = found; continue; }
      emit(prefix);
      if (next < 4096) {
        keys[hsh] = key; vals[hsh] = next;
        if (next === (1 << codeSize)) codeSize++;
        next++;
      } else {
        emit(clear);
        keys.fill(-1); codeSize = 9; next = 258;
      }
      prefix = k;
    }
    emit(prefix);
    if (next === (1 << codeSize) && codeSize < 12) codeSize++;   // 解码器读完最后这个码也会加表、加位
    emit(eoi);
    flushBits();
  }

  function Encoder(w, h, pal, opt) {
    opt = opt || {};
    this.w = w; this.h = h; this.pal = pal; this.map = new Mapper(pal, opt.dither); this.lossy = opt.lossy || 0;
    this.out = new Bytes();
    this.prev = null; this.pending = null; this.frames = 0; this.cs = 0;
    var o = this.out;
    o.str('GIF89a'); o.u16(w); o.u16(h);
    o.byte(0xF7); o.byte(0); o.byte(0);           // 全局调色板 256 色
    for (var i = 0; i < 256; i++) {
      var c = i < pal.colors.length ? pal.colors[i] : 0;
      o.byte((c >> 16) & 255); o.byte((c >> 8) & 255); o.byte(c & 255);
    }
    o.byte(0x21); o.byte(0xFF); o.byte(11); o.str('NETSCAPE2.0'); o.byte(3); o.byte(1); o.u16(opt.loop || 0); o.byte(0);
    if (opt.comment) {                              // 出处写进文件自己的注释块里
      var u = new TextEncoder().encode(opt.comment);
      o.byte(0x21); o.byte(0xFE);
      for (var s = 0; s < u.length; s += 255) { var part = u.subarray(s, s + 255); o.byte(part.length); o.bytes(part); }
      o.byte(0);
    }
    this.cur = new Uint8Array(w * h);
  }
  Encoder.prototype.frame = function (rgba, cs) {
    var w = this.w, h = this.h, cur = this.cur;
    this.map.map(rgba, w, h, cur);
    this.cs += cs;
    if (!this.prev) {
      this.prev = new Uint8Array(cur);
      this.pending = { x: 0, y: 0, w: w, h: h, px: new Uint8Array(cur), cs: cs, trans: false };
      return;
    }
    var prev = this.prev, x0 = w, y0 = h, x1 = -1, y1 = -1, x, y, p;
    /* lossy：新颜色跟屏幕上现在那一格差得很少，就当没变（果冻呼吸、光晕这种细碎闪动，省下一大截） */
    if (this.lossy) {
      var cols = this.pal.colors, lim = this.lossy;
      for (p = 0; p < cur.length; p++) if (cur[p] !== prev[p] && dist2(cols[cur[p]], cols[prev[p]]) <= lim) cur[p] = prev[p];
    }
    for (y = 0; y < h; y++) {
      p = y * w;
      for (x = 0; x < w; x++, p++) {
        if (cur[p] !== prev[p]) { if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y; }
      }
    }
    if (x1 < 0) { this.pending.cs += cs; return; }   // 跟上一格一样：上一格多停一会儿
    this.flush();
    var bw = x1 - x0 + 1, bh = y1 - y0 + 1, sub = new Uint8Array(bw * bh), q = 0;
    for (y = y0; y <= y1; y++) {
      p = y * w + x0;
      for (x = 0; x < bw; x++, p++) sub[q++] = cur[p] === prev[p] ? TRANSPARENT : cur[p];
    }
    for (y = y0; y <= y1; y++) prev.set(cur.subarray(y * w + x0, y * w + x0 + bw), y * w + x0);
    this.pending = { x: x0, y: y0, w: bw, h: bh, px: sub, cs: cs, trans: true };
  };
  Encoder.prototype.flush = function () {
    var f = this.pending; if (!f) return;
    var o = this.out, rest = f.cs;
    /* 一格最长 655.35 秒；店里用不到，照规矩拆开写 */
    var first = Math.min(rest, 65535);
    o.byte(0x21); o.byte(0xF9); o.byte(4);
    o.byte((1 << 2) | (f.trans ? 1 : 0));          // 处置方式 1：留在原处，下一格叠在上面
    o.u16(Math.max(2, first)); o.byte(f.trans ? TRANSPARENT : 0); o.byte(0);
    o.byte(0x2C); o.u16(f.x); o.u16(f.y); o.u16(f.w); o.u16(f.h); o.byte(0);
    lzw(f.px, o);
    this.frames++;
    this.pending = null;
  };
  Encoder.prototype.finish = function () {
    this.flush();
    this.out.byte(0x3B);
    return this.out.done();
  };

  root.GIFENC = {
    hist: function () { return new Hist(); },
    palette: palette,
    encoder: function (w, h, pal, opt) { return new Encoder(w, h, pal, opt); }
  };
})(typeof window !== 'undefined' ? window : this);
