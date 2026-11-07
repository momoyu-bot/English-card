/* 小萌物 GIF 馆（gemini/小卡/gif-v2.html）馆长原创片场底稿
 *
 * 按 tools/手册/GIF馆.md「原创留底稿」要求存入馆同名文件夹。
 * 收录馆内 4 件原创展品的完整按秒绘制代码（严格遵循《小萌物画法》三页造型宪法）：
 *   - orig-07  No.07 守馆迎客铃（群戏版：StashYu、FetchMo、小粉）
 *   - orig-08  No.08 盲盒摇摇乐（群戏版：Clawd、小紫、小黑）
 *   - orig-16  No.16 顶樱桃蹦蹦星（单只版：小粉）
 *   - orig-17  No.17 月桂小夜灯（单只版：小黑）
 *
 * 重拍方法：运行同目录 node gemini/小卡/gif-v2/extract.js 即可重新编码全部 GIF 与 WebP 封面。
 */
(function (root) {
  'use strict';

  var TAU = Math.PI * 2;
  var SANS = '-apple-system,BlinkMacSystemFont,"PingFang SC","Hiragino Sans GB","Noto Sans CJK SC",sans-serif';
  var SERIF = '"Songti SC","STSong","Noto Serif CJK SC","SimSun",serif';
  var KAI = '"Kaiti SC","STKaiti","KaiTi","PingFang SC",serif';

  var ctx = null, S = 1, A = 1;
  var CAM = { x: 180, y: 180, z: 1 };
  var VIEW_CX = 180, VIEW_CY = 180;

  function bindTarget(targetCtx, pxW, pxH, vcx, vcy) {
    ctx = targetCtx;
    S = pxW / 360;
    VIEW_CX = vcx !== undefined ? vcx : (pxW / 2) / S;
    VIEW_CY = vcy !== undefined ? vcy : (pxH / 2) / S;
    A = 1;
  }
  function cam(x, y, z) { CAM.x = x; CAM.y = y; CAM.z = z; }
  function X(x) { return ((x - CAM.x) * CAM.z + VIEW_CX) * S; }
  function Y(y) { return ((y - CAM.y) * CAM.z + VIEW_CY) * S; }
  function worldT() {
    var z = CAM.z * S;
    ctx.setTransform(z, 0, 0, z, (VIEW_CX - CAM.x * CAM.z) * S, (VIEW_CY - CAM.y * CAM.z) * S);
  }
  function clamp(v) { return v < 0 ? 0 : v > 1 ? 1 : v; }
  function smooth(p) { p = clamp(p); return p * p * (3 - 2 * p); }
  function cyc(t, t0, list) {
    var tot = 0, i;
    for (i = 0; i < list.length; i++) tot += list[i][1];
    var u = ((t - t0) % tot + tot) % tot;
    for (i = 0; i < list.length; i++) { if (u < list[i][1]) return list[i][0]; u -= list[i][1]; }
    return list[0][0];
  }
  function blinkOn(t, per, off) { return ((t + off) % per) < 0.16; }

  function R(x, y, w, h, c, a) {
    var al = (a === undefined ? 1 : a) * A; if (al <= 0) return;
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.globalAlpha = al > 1 ? 1 : al; ctx.fillStyle = c;
    var x0 = Math.round(X(x)), y0 = Math.round(Y(y)), x1 = Math.round(X(x + w)), y1 = Math.round(Y(y + h));
    if (x1 > x0 && y1 > y0) ctx.fillRect(x0, y0, x1 - x0, y1 - y0);
    ctx.globalAlpha = 1;
  }
  function F(x, y, w, h, c, a) {
    var al = (a === undefined ? 1 : a) * A; if (al <= 0) return;
    worldT(); ctx.globalAlpha = al > 1 ? 1 : al; ctx.fillStyle = c; ctx.fillRect(x, y, w, h);
    ctx.globalAlpha = 1; ctx.setTransform(1, 0, 0, 1, 0, 0);
  }
  function roundPathOn(c, x, y, w, h, r) {
    r = Math.max(0, Math.min(r, w / 2, h / 2));
    c.moveTo(x + r, y); c.arcTo(x + w, y, x + w, y + h, r); c.arcTo(x + w, y + h, x, y + h, r);
    c.arcTo(x, y + h, x, y, r); c.arcTo(x, y, x + w, y, r); c.closePath();
  }
  function rrect(x, y, w, h, r, fill, a, stroke, lw) {
    a = (a === undefined ? 1 : a) * A; if (a <= 0) return;
    worldT(); ctx.globalAlpha = a > 1 ? 1 : a;
    ctx.beginPath(); roundPathOn(ctx, x, y, w, h, r);
    if (fill) { ctx.fillStyle = fill; ctx.fill(); }
    if (stroke) { ctx.strokeStyle = stroke; ctx.lineWidth = lw || 1; ctx.stroke(); }
    ctx.globalAlpha = 1; ctx.setTransform(1, 0, 0, 1, 0, 0);
  }
  function dot(x, y, r, c, a) {
    a = (a === undefined ? 1 : a) * A; if (a <= 0 || r <= 0) return;
    worldT(); ctx.globalAlpha = a > 1 ? 1 : a; ctx.fillStyle = c;
    ctx.beginPath(); ctx.arc(x, y, r, 0, TAU); ctx.fill();
    ctx.globalAlpha = 1; ctx.setTransform(1, 0, 0, 1, 0, 0);
  }
  function ell(x, y, rx, ry, c, a, stroke, lw, rot) {
    a = (a === undefined ? 1 : a) * A; if (a <= 0) return;
    worldT(); ctx.globalAlpha = a > 1 ? 1 : a;
    ctx.beginPath(); ctx.ellipse(x, y, rx, ry, rot || 0, 0, TAU);
    if (c) { ctx.fillStyle = c; ctx.fill(); }
    if (stroke) { ctx.strokeStyle = stroke; ctx.lineWidth = lw || 1; ctx.stroke(); }
    ctx.globalAlpha = 1; ctx.setTransform(1, 0, 0, 1, 0, 0);
  }
  function line(pts, c, lw, a) {
    a = (a === undefined ? 1 : a) * A; if (a <= 0) return;
    worldT(); ctx.globalAlpha = a > 1 ? 1 : a; ctx.strokeStyle = c; ctx.lineWidth = lw || 1;
    ctx.lineJoin = 'round'; ctx.lineCap = 'round';
    ctx.beginPath(); ctx.moveTo(pts[0], pts[1]);
    for (var i = 2; i < pts.length; i += 2) ctx.lineTo(pts[i], pts[i + 1]);
    ctx.stroke(); ctx.lineCap = 'butt';
    ctx.globalAlpha = 1; ctx.setTransform(1, 0, 0, 1, 0, 0);
  }
  function poly(pts, c, a) {
    a = (a === undefined ? 1 : a) * A; if (a <= 0) return;
    worldT(); ctx.globalAlpha = a > 1 ? 1 : a; ctx.fillStyle = c;
    ctx.beginPath(); ctx.moveTo(pts[0], pts[1]);
    for (var i = 2; i < pts.length; i += 2) ctx.lineTo(pts[i], pts[i + 1]);
    ctx.closePath(); ctx.fill();
    ctx.globalAlpha = 1; ctx.setTransform(1, 0, 0, 1, 0, 0);
  }
  function hexA(h, a) {
    var n = parseInt(h.slice(1), 16);
    return 'rgba(' + (n >> 16 & 255) + ',' + (n >> 8 & 255) + ',' + (n & 255) + ',' + clamp(a) + ')';
  }
  function glowAt(x, y, r, c, a) {
    a = (a === undefined ? 1 : a) * A; if (a <= 0 || r <= 0) return;
    worldT(); var g = ctx.createRadialGradient(x, y, 0, x, y, r);
    g.addColorStop(0, hexA(c, a)); g.addColorStop(0.45, hexA(c, a * 0.35)); g.addColorStop(1, hexA(c, 0));
    ctx.fillStyle = g; ctx.fillRect(x - r, y - r, 2 * r, 2 * r);
    ctx.setTransform(1, 0, 0, 1, 0, 0);
  }
  function grad(x, y, w, h, stops, a) {
    a = (a === undefined ? 1 : a) * A; if (a <= 0) return;
    worldT(); var g = ctx.createLinearGradient(0, y, 0, y + h);
    stops.forEach(function (s) { g.addColorStop(s[0], s[1]); });
    ctx.globalAlpha = a > 1 ? 1 : a; ctx.fillStyle = g; ctx.fillRect(x, y, w, h);
    ctx.globalAlpha = 1; ctx.setTransform(1, 0, 0, 1, 0, 0);
  }
  function drawSpark(x, y, s, c, a) { R(x - s / 2, y - s * 1.5, s, s * 3, c, a); R(x - s * 1.5, y - s / 2, s * 3, s, c, a); }
  function star4(x, y, r, c, a) {
    var p = [], k = r * 0.32;
    [[0, -r], [k, -k], [r, 0], [k, k], [0, r], [-k, k], [-r, 0], [-k, -k]].forEach(function (q) { p.push(x + q[0], y + q[1]); });
    poly(p, c, a);
  }
  function wt(s, x, y, o) {
    var a = (o.a === undefined ? 1 : o.a) * A; if (a <= 0 || !s) return;
    var size = o.size * CAM.z * S;
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.font = (o.wt || 400) + ' ' + size + 'px ' + (o.fam || SANS);
    ctx.fillStyle = o.c; ctx.globalAlpha = a > 1 ? 1 : a;
    ctx.textBaseline = 'alphabetic'; ctx.textAlign = o.al || 'left';
    ctx.fillText(s, X(x), Y(y));
    ctx.globalAlpha = 1;
  }
  function sfx(t, t0, d, s, x, y, o) {
    if (t < t0 || t >= t0 + d) return;
    o = o || {};
    var u = t - t0, pop = u < 0.1 ? 1.2 : 1, a = u > d - 0.28 ? (t0 + d - t) / 0.28 : 1;
    var rise = Math.floor(clamp((t - t0) / d) * 6) / 6 * (o.rise === undefined ? 8 : o.rise);
    wt(s, x, y - rise, { size: (o.size || 12) * pop, wt: 800, c: o.c || '#C87242', al: 'center', a: a, fam: o.fam || SANS });
  }

  /* ---------- 六只造型宪法严格实现 ---------- */
  var MC = 3, FR = 14, CK = 0.3;
  var CL_EYES = {
    bar: [[70, 78, 8, 21], [158, 78, 8, 21]],
    smile: [[62, 88, 8, 8], [70, 80, 8, 11], [78, 88, 8, 8], [150, 88, 8, 8], [158, 80, 8, 11], [166, 88, 8, 8]],
    shut: [[62, 86, 24, 8], [150, 86, 24, 8]]
  };
  function clawd(x, y, k, o) {
    o = o || {}; var la = o.la || 0, ra = o.ra || 0, C = '#d47f59', E = '#120d1d';
    var dy = o.crouch || 0, wk = o.walk || 0;
    function r(a, b, w, h, c) { R(x + a * k, y + b * k, w * k, h * k, c); }
    r(44, 50 + dy, 147, 98 - dy * 0.4, C);
    r(20, 99 + la + dy * 0.6, 24, 21, C); r(191, 99 + ra + dy * 0.6, 25, 21, C);
    var l0 = wk > 0 ? -10 : 0, l1 = wk < 0 ? -10 : 0, l2 = wk > 0 ? -10 : 0, l3 = wk < 0 ? -10 : 0;
    r(44, 148 + l0, 15, 21 - l0 * 0.3, C); r(68, 148 + l1, 15, 21 - l1 * 0.3, C);
    r(152, 148 + l2, 15, 21 - l2 * 0.3, C); r(176, 148 + l3, 15, 21 - l3 * 0.3, C);
    (CL_EYES[o.eyes || 'bar']).forEach(function (e) { r(e[0], e[1] + dy * 0.7, e[2], e[3], E); });
    if (o.blush) { r(48, 106 + dy * 0.6, 18, 10, '#e59a9a'); r(169, 106 + dy * 0.6, 18, 10, '#e59a9a'); }
  }
  function clawdAt(cx, foot, o) { clawd(cx - 118 * CK, foot - 169 * CK, CK, o); }

  /* 小脸蛋实测版宪法：正圆、sRGB 纯色、右窄左宽、-26.2° 反斜杠挖空眼缝 */
  var FACE = ['#FF309B', '#9159FE', '#000000'];
  function slit(cx, cy, w, h, deg) {
    ctx.save(); ctx.translate(cx, cy); ctx.rotate(deg * Math.PI / 180);
    roundPathOn(ctx, -w / 2, -h / 2, w, h, Math.min(w, h) / 2);
    ctx.restore();
  }
  function face(cx, cy, r, col, rot, bl, ringC, o) {
    o = o || {};
    var h = 0.418 * (1 - 0.8 * clamp(bl || 0)), sx = o.sx || 1, sy = o.sy || 1;
    worldT(); ctx.translate(cx, cy); ctx.scale(sx, sy); ctx.rotate((rot || 0) * Math.PI / 180);
    if (ringC) {
      ctx.beginPath(); ctx.arc(0, 0, r + 1.8, 0, TAU); ctx.arc(0, 0, r + 0.2, 0, TAU);
      ctx.fillStyle = ringC; ctx.fill('evenodd');
    }
    ctx.beginPath(); ctx.arc(0, 0, r, 0, TAU);
    slit(0.194 * r, -0.416 * r, 0.194 * r, h * r, -26.2);
    slit(0.626 * r, -0.497 * r, 0.129 * r, h * r, -26.5);
    ctx.fillStyle = col; ctx.fill('evenodd');
    ctx.beginPath(); ctx.setTransform(1, 0, 0, 1, 0, 0);
  }

  /* momoyu 20x13 像素格子与尾巴 DLC */
  var FOX = {
    rows: [
      ".D..........D.......", ".DM........MD.......", ".MCM......MCM...CC..",
      ".MMMMMMMMMMMM..CCCC.", ".MMEEMMMMEEMM..MMMM.", ".MMEEMMMMEEMM..MMMMM",
      "CCCCCCDDCCCCCC.MMMMM", "..CCCCCCCCCC..MMMMM.", "....MMCCMM...MMMMM..",
      "....MMCCMM..MMMMM...", "....MMMMMM.MMMMM....", "....DDMMDDMMMM......",
      "...................."
    ],
    pal: { M: '#E2552B', C: '#FFF3E3', D: '#3B2520' }, line: '#3B2520', eye: '#3B2520',
    eyes: [[3, 4], [9, 4]], blush: [[2, 6], [11, 6]], blushC: '#F59A8C'
  };
  var FOX_IN = [".D..........D.......", ".DM........MD.......", ".MCM......MCM..CC...", ".MMMMMMMMMMMM.CCCC..", ".MMEEMMMMEEMM.MMMM..", ".MMEEMMMMEEMM.MMMMM.", "CCCCCCDDCCCCCC.MMMMM", "..CCCCCCCCCC..MMMMM.", "....MMCCMM...MMMMM..", "....MMCCMM..MMMMM...", "....MMMMMM.MMMMM....", "....DDMMDDMMMM......", "...................."];
  var FOX_OUT = [".D..........D........", ".DM........MD........", ".MCM......MCM....CC..", ".MMMMMMMMMMMM...CCCC.", ".MMEEMMMMEEMM...MMMM.", ".MMEEMMMMEEMM...MMMMM", "CCCCCCDDCCCCCC.MMMMM.", "..CCCCCCCCCC..MMMMM..", "....MMCCMM...MMMMM...", "....MMCCMM..MMMMM....", "....MMMMMM.MMMMM.....", "....DDMMDDMMMM.......", "....................."];
  var FOX_WAG = [[FOX.rows, 0.22], [FOX_IN, 0.22], [FOX.rows, 0.22], [FOX_OUT, 0.22]];

  var CAT = {
    rows: [
      "....................", "........X........X..", ".......XXX......XXX.",
      "........MMMMMMMMMM..", ".......MMMMMMMMMMMM.", ".......MEEMMMMMMEEM.",
      ".....X.MEEMXXXXMEEM.", "....X..MMMMMXXMMMMM.", "....X...MMMMMMMMMM..",
      "....X...MMMMMMMMMM..", ".....X...MMMMMMMM...", "......XXXXXM..MXX...",
      "...................."
    ],
    pal: { M: '#F3E7D6', X: '#4E382E' }, line: '#4E382E', eye: '#79C0F0',
    eyes: [[8, 5], [16, 5]], blush: [[8, 7], [17, 7]], blushC: '#F2B8B0'
  };
  var CAT_UP = ["....................", "........X........X..", ".....X.XXX......XXX.", "....X...MMMMMMMMMM..", "....X..MMMMMMMMMMMM.", "....X..MEEMMMMMMEEM.", "....X..MEEMXXXXMEEM.", ".....X.MMMMMXXMMMMM.", "......X.MMMMMMMMMM..", ".......XMMMMMMMMMM..", "........XMMMMMMMM...", ".........XXM..MXX...", "...................."];

  var N4 = [[0, 0], [1, 0], [0, 1], [1, 1]];
  function eyeCells(e, i) {
    if (e === 'blink') return { c: [[0, 1], [1, 1]], k: 'L' };
    if (e === 'happy') return { c: [[-1, 1], [0, 0], [1, 0], [2, 1]], k: 'L' };
    if (e === 'wink') return i ? { c: [[-1, 1], [0, 0], [1, 0], [2, 1]], k: 'L' } : { c: N4, k: 'E' };
    return { c: N4, k: 'E' };
  }
  function momo(ch, x, y, cell, o) {
    o = o || {};
    var rows = o.rows || ch.rows, g = {}, r, c, k;
    function put(r0, c0, v) { (g[r0] || (g[r0] = {}))[c0] = v; }
    for (r = 0; r < rows.length; r++) for (c = 0; c < rows[r].length; c++) { k = rows[r][c]; if (k !== '.') put(r, c, k); }
    ch.eyes.forEach(function (p, i) {
      N4.forEach(function (q) { put(p[1] + q[1], p[0] + q[0], 'M'); });
      var e = eyeCells(o.eyes || 'normal', i);
      e.c.forEach(function (q) { put(p[1] + q[1], p[0] + q[0], e.k); });
    });
    if (o.blush) ch.blush.forEach(function (p) { put(p[1], p[0], 'B'); });
    function col(v) { return !v ? null : v === 'E' ? ch.eye : v === 'L' ? ch.line : v === 'B' ? ch.blushC : ch.pal[v]; }
    for (r = -2; r <= 13; r++) {
      var row = g[r]; if (!row) continue;
      c = -10;
      while (c <= 30) {
        var cc = col(row[c]); if (!cc) { c++; continue; }
        var c2 = c; while (c2 + 1 <= 30 && col(row[c2 + 1]) === cc) c2++;
        R(x + c * cell, y + r * cell, (c2 - c + 1) * cell, cell, cc);
        c = c2 + 1;
      }
    }
  }

  /* ---------- 原创片场公共道具（店铺背景、夜明珠、雕花锦匣） ---------- */
  var FLOOR = 446;
  function drawHallBg(t, night) {
    grad(0, 260, 360, FLOOR - 260, [[0, night > 0.35 ? '#20192B' : '#2B2232'], [1, '#3A2E40']]);
    F(0, FLOOR - 14, 360, 14, '#221A26');
    rrect(128, 300, 196, 98, 4, '#382822', 0.85, '#594034', 2);
    F(132, 346, 188, 3, '#594034');
    F(194, 304, 3, 42, '#594034'); F(258, 304, 3, 42, '#594034');
    ell(162, 330, 7, 10, '#7BA696', 0.85);
    rrect(212, 326, 28, 14, 2, '#8E352E', 0.85, '#C99A49', 1);
    dot(288, 332, 8, '#D97941', 0.8);
    R(0, FLOOR, 360, 160, '#5C4030');
    R(0, FLOOR, 360, 9, '#785540');
    R(0, FLOOR + 9, 360, 3, '#422C20');
    for (var i = 0; i < 4; i++) {
      rrect(22 + i * 84, FLOOR + 22, 68, 36, 3, '#4D3426', 1, '#3B261B', 1);
      rrect(48 + i * 84, FLOOR + 37, 16, 4, 2, '#C89D66');
    }
  }

  function drawPearl(x, y, r, t, glowScale) {
    var s = Math.floor(t * 6) / 6;
    var br = 0.82 + 0.18 * Math.sin(s * TAU / 1.4);
    if (glowScale > 0) {
      glowAt(x, y, r * 3.8 * glowScale * br, '#FFF5CC', 0.46 * glowScale);
      glowAt(x, y, r * 1.9 * glowScale, '#FFFFFF', 0.52 * glowScale);
    }
    dot(x, y, r, '#F7F3E6');
    dot(x - 0.15 * r, y - 0.15 * r, r * 0.82, '#FFFDF7');
    dot(x - 0.35 * r, y - 0.35 * r, r * 0.28, '#FFFFFF');
  }

  function drawCasket(cx, by, t, o) {
    o = o || {};
    var w = o.w || 68, h = o.h || 34, x = cx - w / 2, y = by - h;
    rrect(x + 4, y - 4, w - 8, 10, 3, '#17131C');
    rrect(x, y, w, h, 4, '#9E2A2B', 1, '#D4A24C', 1.8);
    R(x + 4, y + 5, w - 8, h - 10, '#822021');
    R(x, y + h / 2 - 3, w, 6, '#E0A94E');
    R(x + w / 2 - 4, y, 8, h, '#E0A94E');
    var sw = (Math.floor(t * 10) % 2 ? -1 : 1) * (o.bellShake || 1.5);
    [-1, 1].forEach(function (dir) {
      var bx = cx + dir * (w / 2 + 3), by0 = y + 9;
      line([cx + dir * (w / 2 - 1), y + 5, bx + sw, by0], '#D4A24C', 1.2);
      dot(bx + sw, by0 + 3, 4, '#F5C756');
    });
    for (var j = 0; j < 4; j++) star4(x + 12 + j * (w - 24) / 3, y + h / 2, 3.6, '#D7B8FF', 0.9);
    var openP = o.lidOpen || 0;
    worldT(); ctx.save();
    ctx.translate(cx, y - 6 - openP * 24); ctx.rotate(openP * -0.36);
    ctx.beginPath(); roundPathOn(ctx, -(w + 6) / 2, -6.5, w + 6, 13, 4);
    ctx.fillStyle = '#B03030'; ctx.fill();
    ctx.lineWidth = 1.6; ctx.strokeStyle = '#E6B450'; ctx.stroke();
    ctx.fillStyle = '#FF47A3';
    ctx.beginPath(); ctx.ellipse(-6, -8, 5.5, 3.2, -0.3, 0, TAU); ctx.fill();
    ctx.beginPath(); ctx.ellipse(6, -8, 5.5, 3.2, 0.3, 0, TAU); ctx.fill();
    ctx.beginPath(); ctx.arc(0, -8, 2.5, 0, TAU); ctx.fillStyle = '#FF85C2'; ctx.fill();
    ctx.beginPath(); ctx.restore(); ctx.setTransform(1, 0, 0, 1, 0, 0);
  }

  /* ========================================================================
     1. orig-07：守馆迎客铃（群戏版：StashYu, FetchMo, 小粉） dur = 2.6s
     ======================================================================== */
  function renderOrig07(u) {
    var su = Math.floor(u * 15) / 15;
    cam(180, 410, 1.85);
    drawHallBg(su, 0.25);
    rrect(92, FLOOR - 4, 176, 8, 3, '#9E2A2B', 1, '#E6B450', 1);
    var sw = Math.sin(su * TAU / 1.3) * 3;
    line([180, 314, 180 + sw, 346], '#D4A24C', 1.5);
    ell(180 + sw, 355, 12, 9, '#D94E34', 1, '#F5C756', 1.5);
    glowAt(180 + sw, 355, 34, '#FFE082', 0.42);
    wt('迎', 180 + sw, 358, { size: 8, wt: 700, c: '#FFF5CC', al: 'center', fam: KAI });

    momo(FOX, 100, FLOOR - 12 * MC - 2, MC, { rows: cyc(su, 0, FOX_WAG), eyes: 'happy', blush: true });
    var hopP = Math.abs(Math.sin(su * TAU / 1.3)) * -18;
    var sq = hopP > -3 ? 1.14 : 0.93;
    face(180, FLOOR - FR + hopP, FR, FACE[0], -10 + Math.sin(su * TAU / 1.3) * 5, blinkOn(su, 2.6, 0.4) ? 1 : 0, null, { sx: sq, sy: 2 - sq });
    var catBounce = Math.floor(su * 4) % 2 ? -3 : 0;
    momo(CAT, 200, FLOOR - 12 * MC + catBounce, MC, { rows: CAT_UP, eyes: 'wink', blush: true });
    drawSpark(152, 382, 2, '#FFF3B0', (Math.floor(su * 6) % 2) ? 0.95 : 0.4);
    drawSpark(212, 376, 2, '#FFF3B0', (Math.floor(su * 6) % 2) ? 0.4 : 0.95);
  }

  /* ========================================================================
     2. orig-08：盲盒摇摇乐（群戏版：Clawd, 小紫, 小黑） dur = 2.4s
     ======================================================================== */
  function renderOrig08(u) {
    var su = Math.floor(u * 15) / 15;
    cam(186, 410, 1.95);
    drawHallBg(su, 0.42);
    var pop = su >= 1.1 && su < 2.22;
    var closeBack = su >= 2.22 ? 1 - (su - 2.22) / 0.18 : 1;
    var shakeX = su < 1.1 ? (Math.floor(su * 14) % 2 ? -3 : 3) : 0;
    var bx = 160 + shakeX, by = FLOOR;

    var popH = pop ? smooth(clamp((su - 1.1) / 0.32)) * 22 * closeBack : 0;
    if (popH > 2) {
      face(bx - 13, by - 28 - popH, FR * 0.88, FACE[1], -8, 0);
      face(bx + 13, by - 28 - popH, FR * 0.88, FACE[2], -12, 0, 'rgba(255,248,225,0.45)');
      star4(bx - 26, by - 48 - popH * 0.6, 4.5, '#D7B8FF', 0.95);
      drawPearl(bx, by - 45 - popH * 0.8, 6.5, su, 0.95);
    }
    drawCasket(bx, by, su, {
      w: 68, h: 34,
      lidOpen: pop ? smooth(clamp((su - 1.05) / 0.32)) * closeBack : 0,
      bellShake: su < 1.1 ? 4.2 : 1.2
    });
    var wk = su < 1.1 ? (Math.floor(su * 10) % 2 ? 1 : -1) : 0;
    clawdAt(226, FLOOR, {
      la: su < 1.1 ? (Math.floor(su * 12) % 2 ? -18 : -6) : -22 * closeBack,
      walk: wk,
      eyes: pop ? 'smile' : 'bar',
      blush: pop
    });
    if (su < 1.05) sfx(su, 0.08, 0.92, '晃晃~', bx, by - 46, { c: '#F5C756', rise: 4 });
    else if (su < 2.2) sfx(su, 1.12, 1.05, '啵！', bx, by - 68, { c: '#FFB5D8', rise: 6 });
  }

  /* ========================================================================
     3. orig-16：顶樱桃蹦蹦星（单只版：小粉） dur = 2.4s
        严格遵循小脸蛋实测版宪法：正圆 #FF309B、-26.2° 右窄左宽挖空反斜杠眼缝、无嘴鼻腮红
     ======================================================================== */
  function renderOrig16(u) {
    var su = Math.floor(u * 15) / 15;
    cam(180, 180, 1);
    grad(0, 0, 360, 360, [[0, '#FFF8EE'], [1, '#FBE9DC']]);
    // 甜点铺彩色三角小挂旗
    line([0, 38, 360, 38], '#E2C9B0', 1.6);
    var flagCols = ['#FF85B3', '#FFD166', '#A992FA', '#7BD3B0', '#FF9F68', '#FF85B3', '#FFD166'];
    for (var i = 0; i < 7; i++) {
      var fx = 24 + i * 50;
      poly([fx - 13, 38, fx + 13, 38, fx, 60], flagCols[i]);
    }
    // 桌面与舒芙蕾软垫
    R(0, 286, 360, 74, '#E8D2B8');
    R(0, 286, 360, 7, '#F5E4CE');
    ell(180, 292, 86, 12, '#D7BE9E', 0.65);

    // 弹跳相位（周期 1.2s，2.4s 完整跳两轮：第一跳轻跳，第二跳高跳撞响金星）
    var cycP = (su % 2.4) / 2.4;
    var jumpY = 0, sx = 1, sy = 1, padSquash = 0;
    if (cycP < 0.14) {
      // 蓄力压软垫
      var k0 = Math.sin((cycP / 0.14) * Math.PI);
      sx = 1 + 0.18 * k0; sy = 1 - 0.16 * k0;
      jumpY = 6 * k0; padSquash = 5 * k0;
    } else if (cycP < 0.62) {
      // 高高跃起撞响小金星
      var p1 = (cycP - 0.14) / 0.48;
      var arc = 4 * p1 * (1 - p1);
      jumpY = -98 * arc;
      sx = 1 - 0.08 * arc; sy = 1 + 0.09 * arc;
    } else if (cycP < 0.76) {
      // 落回软垫 Q 弹缓冲
      var k2 = Math.sin(((cycP - 0.62) / 0.14) * Math.PI);
      sx = 1 + 0.15 * k2; sy = 1 - 0.14 * k2;
      jumpY = 5 * k2; padSquash = 4 * k2;
    } else {
      // 轻巧小颠一下
      var p3 = (cycP - 0.76) / 0.24;
      jumpY = -18 * 4 * p3 * (1 - p3);
    }

    // 舒芙蕾软垫随小粉起落呼吸变形
    rrect(112 - padSquash, 256 + padSquash, 136 + padSquash * 2, 34 - padSquash, 17, '#FFFDF9', 1, '#F2C6B6', 2);
    rrect(120 - padSquash, 252 + padSquash, 120 + padSquash * 2, 14, 7, '#FFE2EC');

    // 半空悬挂的八音盒小铃星
    var hit = cycP >= 0.34 && cycP <= 0.56;
    var starSwing = hit ? Math.sin((cycP - 0.34) * 36) * 6 : Math.sin(su * TAU / 2.4) * 2;
    var starY = hit ? 84 - Math.sin(((cycP - 0.34) / 0.22) * Math.PI) * 8 : 84;
    line([180, 0, 180 + starSwing, starY - 14], '#D9A441', 1.8);
    if (hit) glowAt(180 + starSwing, starY, 48, '#FFE066', 0.65);
    star4(180 + starSwing, starY, 17, '#F5B82E', 1);
    dot(180 + starSwing, starY, 5, '#FFF9DB');
    if (hit) {
      var ringR = 16 + ((cycP - 0.34) / 0.22) * 28;
      ell(180 + starSwing, starY, ringR, ringR, null, 1 - (cycP - 0.34) / 0.22, '#F5B82E', 2);
      star4(134, 92, 7, '#FF85B3', 0.9);
      star4(228, 96, 7, '#FFD166', 0.9);
      wt('叮♪', 228, 76, { size: 15, wt: 800, c: '#D97925', al: 'center', fam: KAI });
    }

    // 正圆小粉本体（半径 38，圆心默认 (180, 222)）
    var py = 220 + jumpY;
    var rot = -8 + Math.sin(su * TAU / 2.4) * 5;
    var bl = (cycP > 0.84 && cycP < 0.92) ? 1 : 0;
    face(180, py, 38, FACE[0], rot, bl, null, { sx: sx, sy: sy });

    // 头顶稳稳叠放的双生红樱桃（随小粉弹跳有一点轻巧惯性滞后）
    var chY = py - 38 * sy - 7 + (jumpY < -40 ? -3 : 0);
    line([172, chY, 182, chY - 18, 192, chY - 1], '#3B8754', 2.2);
    ell(188, chY - 18, 7, 3.8, '#4CAF6A', 1, null, 0, -0.35);
    dot(171, chY + 2, 8.5, '#E5384F');
    dot(168, chY - 1, 2.4, '#FFD6DD');
    dot(191, chY + 2, 8.5, '#D62839');
    dot(188, chY - 1, 2.4, '#FFD6DD');
  }

  /* ========================================================================
     4. orig-17：月桂小夜灯（单只版：小黑） dur = 2.8s
        最圆的小黑 #000000 守着头顶桂花夜明珠小灯，挖空眼缝透出窗边暖月光
     ======================================================================== */
  function renderOrig17(u) {
    var su = Math.floor(u * 15) / 15;
    cam(180, 180, 1);
    // 深夜窗景与柔和月光底板（让小黑挖空眼缝自然透出暖月光！）
    grad(0, 0, 360, 290, [[0, '#161B33'], [1, '#262D4D']]);
    // 圆月轩窗
    dot(180, 168, 118, '#38334C');
    grad(68, 56, 224, 224, [[0, '#232B4E'], [1, '#3D375E']]);
    // 窗内弯月与桂花枝
    dot(232, 108, 22, '#FFF2B8', 0.95);
    dot(224, 102, 18, '#282F52', 0.95);
    line([74, 96, 128, 112, 166, 104], '#4A372B', 3);
    line([128, 112, 148, 128], '#4A372B', 2);
    [[106, 104], [134, 108], [152, 126], [168, 102]].forEach(function (p) {
      dot(p[0], p[1], 3.5, '#F6C84C');
      dot(p[0] + 4, p[1] + 2, 3, '#FFE27A');
    });

    // 轩窗木框与窗台
    ell(180, 168, 114, 114, null, 1, '#5A3E2E', 9);
    R(0, 272, 360, 88, '#4B3427');
    R(0, 272, 360, 9, '#6E4E3A');

    // 月白蒲团软垫
    ell(180, 276, 68, 14, '#EDE3CE', 1, '#C9B898', 2);
    ell(180, 273, 56, 9, '#FAF4E6');

    // 头顶夜明珠散发的暖黄大光晕（正好衬在小黑背后与挖空眼缝后！）
    var breath = 0.88 + 0.12 * Math.sin(su * TAU / 2.8);
    glowAt(188, 198, 92 * breath, '#FFEAA0', 0.55);

    // 最圆的小黑（#000000，带一圈柔和米白贴纸边，轻微随节拍偏头眨眼）
    var tilt = -10 + Math.sin(su * TAU / 2.8) * 4;
    var bl = (su > 1.85 && su < 2.05) ? 1 : 0;
    face(180, 232, 40, FACE[2], tilt, bl, '#FFF6DC');

    // 头顶小金冠莲托与呼吸夜明珠
    var crownX = 180 + Math.sin(su * TAU / 2.8) * 2.5, crownY = 188;
    poly([crownX - 16, crownY + 5, crownX + 16, crownY + 5, crownX + 21, crownY - 3, crownX - 21, crownY - 3], '#E5B44B');
    drawPearl(crownX, crownY - 10, 11, su, 1.15);

    // 三瓣循环飘落的金桂花（相位错开保证 2.8s 首尾无缝衔接）
    [[118, 0.0], [218, 0.36], [156, 0.68]].forEach(function (item, idx) {
      var p = ((su / 2.8) + item[1]) % 1;
      var gx = item[0] + Math.sin(p * TAU) * 14;
      var gy = 108 + p * 162;
      var ga = p < 0.12 ? p / 0.12 : p > 0.88 ? (1 - p) / 0.12 : 1;
      star4(gx, gy, idx === 1 ? 5.5 : 4.5, '#FFD55A', ga * 0.95);
    });
  }

  var STUDIO_ITEMS = {
    'orig-07': { dur: 2.6, render: renderOrig07 },
    'orig-08': { dur: 2.4, render: renderOrig08 },
    'orig-16': { dur: 2.4, render: renderOrig16 },
    'orig-17': { dur: 2.8, render: renderOrig17 }
  };

  root.STUDIO = {
    items: STUDIO_ITEMS,
    render: function (key, t, canvas) {
      var spec = STUDIO_ITEMS[key];
      if (!spec || !canvas) return;
      var c = canvas.getContext('2d', { willReadFrequently: true });
      bindTarget(c, canvas.width, canvas.height);
      c.setTransform(1, 0, 0, 1, 0, 0);
      c.clearRect(0, 0, canvas.width, canvas.height);
      spec.render(t);
    }
  };
})(typeof window !== 'undefined' ? window : globalThis);
