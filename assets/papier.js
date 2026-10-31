/* Leotio – Startseite „Papier und Licht“.
   Die Seite ist ein Bogen Baumwollpapier (WebGL). Das Zeichen ist vertieft geprägt (Tiefdruck), das Licht steht
   schräg oben links und folgt Maus oder Finger. Auftakt einmal pro Sitzung: Bleistift zeichnet die Konstruktion
   (Außenkontur, Zirkel 1 : √2, Lote, Innenkonturen), das Zeichen wird ins Papier gedrückt, dann erscheint der Druck.
   Klick oder Taste überspringt, Klick auf das kleine Logo oben links spielt erneut (nur hier auf der Startseite), ebenso Adresse #intro.
   Ohne WebGL2 bleibt die CSS-Prägung, bei „Bewegung reduzieren“ entfällt der Auftakt. */
(function () {
  var root = document.documentElement;
  var fig = document.querySelector('.hero .figure'), z = fig && fig.querySelector('.zeichen');
  function plain() { root.classList.remove('intro', 'papier'); }
  if (!z) { plain(); return; }
  var cv = document.createElement('canvas');
  cv.className = 'papier-bg'; cv.setAttribute('aria-hidden', 'true');
  var gl = cv.getContext('webgl2', { antialias: false, premultipliedAlpha: false });
  if (!gl) { plain(); return; }
  var reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  var darkQ = matchMedia('(prefers-color-scheme: dark)');

  // ---------- Shader ----------
  var vs = '#version 300 es\nin vec2 p;void main(){gl_Position=vec4(p,0.,1.);}';
  var fs = '#version 300 es\nprecision highp float;\n' +
    'uniform sampler2D uH;uniform vec4 uTex;uniform vec2 uVp;uniform vec3 uL;uniform float uI,uNight,uDpr,uP;out vec4 o;\n' +
    'float h2(vec2 p){p=fract(p*vec2(123.34,456.21));p+=dot(p,p+45.32);return fract(p.x*p.y);}\n' +
    'float vn(vec2 p){vec2 i=floor(p),f=fract(p);f=f*f*(3.-2.*f);return mix(mix(h2(i),h2(i+vec2(1,0)),f.x),mix(h2(i+vec2(0,1)),h2(i+vec2(1,1)),f.x),f.y);}\n' +
    // Baumwollpapier: weiche Wolken, Fasern, feines Korn
    'float paper(vec2 q){vec2 p=q/uDpr;float n=vn(p*.02)*.5+vn(p*.06)*.25;\n' +
    '  float fib=vn(vec2(p.x*1.4,p.y*.18)+vn(p*.04)*7.)*.5+vn(vec2(p.y*1.2,p.x*.15)+3.)*.5;\n' +
    '  return n*.35+fib*.22+vn(p*1.6)*.16+vn(p*.45)*.1;}\n' +
    'vec4 T(vec2 q){vec2 u=(q-uTex.xy)/uTex.zw;if(u.x<0.||u.y<0.||u.x>1.||u.y>1.)return vec4(0.);return texture(uH,u);}\n' +
    // Höhe: R = Zeichen (vertieft), A = breite Mulde, die dicker Karton beim Prägen bildet
    'float Ht(vec2 q){vec4 t=T(q);return -smoothstep(.02,.9,t.r)*3.6*uP-t.a*.35*uP;}\n' +
    'float H(vec2 q){return paper(q)*.42+Ht(q);}\n' +
    'void main(){vec2 q=gl_FragCoord.xy;vec4 t=T(q);\n' +
    '  float hx=H(q+vec2(1,0))-H(q-vec2(1,0)),hy=H(q+vec2(0,1))-H(q-vec2(0,1));\n' +
    '  vec3 N=normalize(vec3(-hx*.9/uDpr,-hy*.9/uDpr,1.));\n' +
    '  vec3 Lv=vec3(uL.xy-q,uL.z);float d=length(Lv);vec3 L=Lv/d;\n' +
    '  float diff=max(dot(N,L),0.),flat0=max(L.z,.05);\n' +
    '  float att=1./(1.+pow(d/(max(uVp.x,uVp.y)*.7),2.));\n' +
    '  vec3 Hh=normalize(L+vec3(0,0,1));\n' +
    '  vec3 paperC=mix(vec3(.953,.937,.906),vec3(.105,.108,.118),uNight);\n' +
    '  float rel=min(diff/flat0,1.25);float amb=mix(.74,.16,uNight);\n' +
    '  float lit=amb+(1.-amb)*att*uI*mix(1.,2.6,uNight);\n' +
    '  vec3 col=paperC*(lit*mix(1.,.3+.7*rel,.8*uI+.2));\n' +
    // Schlagschatten in der Vertiefung: die dem Licht zugewandte Kante wirft Schatten auf den Grund
    '  vec2 ld=normalize(uL.xy-q+1e-3);float sl=uL.z/max(length(uL.xy-q),1.);float h0=Ht(q),occ=0.;\n' +
    '  for(int i=1;i<=6;i++){float dd=float(i)*1.6*uDpr;occ=max(occ,Ht(q+ld*dd)-h0-sl*dd*.8/uDpr);}\n' +
    '  col*=1.-.5*smoothstep(0.,1.2,occ)*uI;\n' +
    '  col*=1.-.22*smoothstep(.02,.9,t.r)*uP;\n' +
    '  col+=pow(max(dot(N,Hh),0.),30.)*mix(.05,.12,uNight)*att*uI;\n' +
    '  col+=(h2(q)-.5)/255.*2.;o=vec4(col,1.);}';
  function sh(type, src) { var x = gl.createShader(type); gl.shaderSource(x, src); gl.compileShader(x); if (!gl.getShaderParameter(x, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(x)); return x; }
  var pr;
  try {
    pr = gl.createProgram(); gl.attachShader(pr, sh(gl.VERTEX_SHADER, vs)); gl.attachShader(pr, sh(gl.FRAGMENT_SHADER, fs));
    gl.linkProgram(pr); if (!gl.getProgramParameter(pr, gl.LINK_STATUS)) throw new Error('link');
  } catch (e) { plain(); return; }
  gl.useProgram(pr);
  var buf = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, buf);
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW);
  var loc = gl.getAttribLocation(pr, 'p'); gl.enableVertexAttribArray(loc); gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);
  var U = {}; ['uH', 'uTex', 'uVp', 'uL', 'uI', 'uNight', 'uDpr', 'uP'].forEach(function (n) { U[n] = gl.getUniformLocation(pr, n); });
  gl.uniform1i(U.uH, 0);

  document.body.insertBefore(cv, document.body.firstChild);
  root.classList.add('papier');

  // ---------- Zeichen-Geometrie (wie das SVG: Linie 0,0394, Teilung 1 : √2) ----------
  var Q = Math.SQRT1_2, B = 1 - Q, SWR = 0.0394;
  function markQ(c, x, y, s, sw) {
    c.rect(x, y, s, sw); c.rect(x, y + s - sw, s, sw); c.rect(x, y, sw, s); c.rect(x + s - sw, y, sw, s);
    c.rect(x + s * B - sw / 2, y, sw, s * Q + sw / 2); c.rect(x + s * B - sw / 2, y + s * Q - sw / 2, s - s * B + sw / 2, sw);
  }
  function blur(a, w, h, r) { // dreifacher Box-Blur, nähert eine Gauß-Kurve an
    var t = new Float32Array(a.length), pass, x, y, acc, row;
    for (pass = 0; pass < 3; pass++) {
      for (y = 0; y < h; y++) { acc = 0; row = y * w; for (x = -r; x <= r; x++) acc += a[row + Math.min(w - 1, Math.max(0, x))];
        for (x = 0; x < w; x++) { t[row + x] = acc / (2 * r + 1); acc += a[row + Math.min(w - 1, x + r + 1)] - a[row + Math.max(0, x - r)]; } }
      for (x = 0; x < w; x++) { acc = 0; for (y = -r; y <= r; y++) acc += t[Math.min(h - 1, Math.max(0, y)) * w + x];
        for (y = 0; y < h; y++) { a[y * w + x] = acc / (2 * r + 1); acc += t[Math.min(h - 1, y + r + 1) * w + x] - t[Math.max(0, y - r) * w + x]; } }
    }
  }

  // ---------- Aufbau: Leinwand über die ganze Seite, Höhenkarte nur um das Zeichen ----------
  var W = 0, H = 0, dpr = 1, box = null, tex = null, texRect = [0, 0, 1, 1];
  function build() {
    dpr = Math.min(window.devicePixelRatio || 1, 2);
    var cw = document.documentElement.clientWidth;
    cv.style.height = '0px'; stift.setAttribute('height', '0');
    var ch = Math.max(document.documentElement.scrollHeight, window.innerHeight);
    W = Math.round(cw * dpr); H = Math.round(ch * dpr);
    cv.width = W; cv.height = H; cv.style.width = cw + 'px'; cv.style.height = ch + 'px';
    var r = z.getBoundingClientRect();
    box = { x: r.left + window.scrollX, y: r.top + window.scrollY, s: r.width };
    var m = box.s * 0.12, side = Math.max(8, Math.round((box.s + 2 * m) * dpr));
    var c = document.createElement('canvas'); c.width = side; c.height = side;
    var x = c.getContext('2d'); x.fillStyle = '#000'; x.fillRect(0, 0, side, side); x.fillStyle = '#fff';
    var k = side / (box.s + 2 * m); x.scale(k, k); x.beginPath(); markQ(x, m, m, box.s, box.s * SWR); x.fill('nonzero');
    var d = x.getImageData(0, 0, side, side).data, n = side * side, emb = new Float32Array(n), i;
    for (i = 0; i < n; i++) emb[i] = d[i * 4] / 255;
    blur(emb, side, side, Math.max(2, Math.round(box.s * 0.006 * dpr)));
    var wide = new Float32Array(emb); blur(wide, side, side, Math.max(4, Math.round(box.s * 0.022 * dpr)));
    var px = new Float32Array(n * 4);
    for (i = 0; i < n; i++) { px[i * 4] = emb[i]; px[i * 4 + 3] = wide[i]; }
    if (tex) gl.deleteTexture(tex);
    tex = gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D, tex);
    gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, true);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA16F, side, side, 0, gl.RGBA, gl.FLOAT, px);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    texRect = [(box.x - m) * dpr, H - (box.y + box.s + m) * dpr, side, side];
    gl.viewport(0, 0, W, H);
    stift.setAttribute('width', cw); stift.setAttribute('height', ch); stift.setAttribute('viewBox', '0 0 ' + cw + ' ' + ch);
  }

  // ---------- Bleistift ----------
  var NS = 'http://www.w3.org/2000/svg';
  var stift = document.createElementNS(NS, 'svg');
  stift.setAttribute('class', 'papier-stift'); stift.setAttribute('aria-hidden', 'true'); stift.setAttribute('focusable', 'false');
  stift.innerHTML = '<defs><filter id="graphit" x="-2%" y="-2%" width="104%" height="104%">' +
    '<feTurbulence type="fractalNoise" baseFrequency=".7" numOctaves="2" seed="4" result="n"/>' +
    '<feDisplacementMap in="SourceGraphic" in2="n" scale="1.6" xChannelSelector="R" yChannelSelector="G" result="d"/>' +
    '<feTurbulence type="fractalNoise" baseFrequency="1.9" numOctaves="1" seed="11" result="g"/>' +
    '<feColorMatrix in="g" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  3 0 0 0 -.75" result="ga"/>' +
    '<feComposite in="d" in2="ga" operator="in"/></filter></defs><g filter="url(#graphit)"></g>';
  document.body.insertBefore(stift, cv.nextSibling);
  var pg = stift.querySelector('g'), anims = [];
  function pencil() {
    pg.innerHTML = ''; anims.forEach(function (a) { a.cancel(); }); anims = [];
    if (!box || !pg.animate) return;
    var x0 = box.x, y0 = box.y, S = box.s, T = SWR, X = .07;
    var P = function (a, b) { return (x0 + a * S).toFixed(1) + ',' + (y0 + b * S).toFixed(1); };
    var gw = Math.max(.7, S * .0018), cw = Math.max(1.1, S * .0028), ez = 'cubic-bezier(.4,0,.3,1)';
    function add(d, w, op, at, dur, dash) {
      var e = document.createElementNS(NS, 'path'); e.setAttribute('d', d); e.style.strokeWidth = w; e.style.opacity = op;
      if (dash) { e.style.strokeDasharray = dash; anims.push(e.animate([{ opacity: 0 }, { opacity: op }], { duration: dur, delay: at, fill: 'both' })); }
      else { e.setAttribute('pathLength', '1'); e.style.strokeDasharray = '1 1';
        anims.push(e.animate([{ strokeDashoffset: 1 }, { strokeDashoffset: 0 }], { duration: dur, delay: at, fill: 'both', easing: ez })); }
      pg.appendChild(e);
    }
    // Hilfslinien: Kanten des Quadrats, über die Ecken hinaus
    add('M' + P(-X, 0) + ' L' + P(1 + X, 0), gw, .5, 200, 420); add('M' + P(1, -X) + ' L' + P(1, 1 + X), gw, .5, 330, 420);
    add('M' + P(1 + X, 1) + ' L' + P(-X, 1), gw, .5, 460, 420); add('M' + P(0, 1 + X) + ' L' + P(0, -X), gw, .5, 590, 420);
    // Außenkontur
    add('M' + P(0, 0) + ' L' + P(1, 0) + ' L' + P(1, 1) + ' L' + P(0, 1) + ' Z', cw, .85, 720, 700);
    // Zirkel: Einstich oben rechts, Radius = Seite, Bogen bis zur Diagonalen
    var c = document.createElementNS(NS, 'circle'); c.setAttribute('cx', (x0 + S).toFixed(1)); c.setAttribute('cy', y0.toFixed(1));
    c.setAttribute('r', Math.max(2.5, S * .008)); c.style.strokeWidth = gw; pg.appendChild(c);
    anims.push(c.animate([{ opacity: 0 }, { opacity: .6 }], { duration: 200, delay: 1400, fill: 'both' }));
    add('M' + P(1, 1) + ' A' + S.toFixed(1) + ',' + S.toFixed(1) + ' 0 0 1 ' + P(B, Q), gw, .55, 1500, 850);
    add('M' + P(1, 0) + ' L' + P(B, Q), gw, .45, 2250, 300, (S * .012).toFixed(1) + ' ' + (S * .012).toFixed(1));
    // Lote durch den Schnittpunkt = Mittellinien des L
    add('M' + P(B, -X) + ' L' + P(B, 1 + X), gw, .45, 2400, 420); add('M' + P(-X, Q) + ' L' + P(1 + X, Q), gw, .45, 2480, 420);
    // Innenkonturen beidseits der Mittellinien
    add('M' + P(T, T) + ' L' + P(B - T / 2, T) + ' L' + P(B - T / 2, Q + T / 2) + ' L' + P(1 - T, Q + T / 2) + ' L' + P(1 - T, 1 - T) + ' L' + P(T, 1 - T) + ' Z', cw, .85, 2800, 650);
    add('M' + P(B + T / 2, T) + ' L' + P(1 - T, T) + ' L' + P(1 - T, Q - T / 2) + ' L' + P(B + T / 2, Q - T / 2) + ' Z', cw, .85, 3000, 500);
    // Bleistift verblasst, während das Zeichen ins Papier sinkt
    anims.push(pg.animate([{ opacity: 1 }, { opacity: 0 }], { duration: 1000, delay: 3700, fill: 'both' }));
  }

  // ---------- Ablauf ----------
  var PRESS = 3700, PRESS_DUR = 900, REVEAL = 4800, DONE = 6000;
  var iS = -1e9, playing = false, revealed = true;
  function clamp(v) { return Math.max(0, Math.min(1, v)); }
  function play() {
    try { sessionStorage.setItem('leotio-intro', '1'); } catch (e) {}
    if (reduce) { finish(); return; }
    root.classList.add('intro'); revealed = false; playing = true; iS = performance.now(); pencil(); kick();
  }
  function reveal() { if (!revealed) { revealed = true; root.classList.remove('intro'); } }
  function finish() { playing = false; iS = -1e9; anims.forEach(function (a) { a.finish(); }); reveal(); kick(); }

  // ---------- Licht ----------
  var tx = null, ty = null, lx = 0, ly = 0, night = darkQ.matches ? 1 : 0, raf = 0, first = true;
  function rest() { return [box.x - 0.36 * box.s, box.y - 0.26 * box.s]; }   // schräg oben links, etwa 45 Grad
  function kick() { if (!raf) raf = requestAnimationFrame(frame); }
  function frame(now) {
    raf = 0; if (!box) return;
    var e = playing ? now - iS : DONE + 1, more = false, I = 1, Pp = 1, kp;
    if (playing) {
      if (e >= REVEAL) reveal();
      if (e >= DONE) playing = false; else more = true;
      I = Math.min(1, .25 + e / 3200);
      kp = clamp((e - PRESS) / PRESS_DUR); Pp = kp * kp * (3 - 2 * kp);
    }
    var r = rest(), ax = r[0], ay = r[1];
    if (!playing && tx !== null) { ax = tx; ay = ty; }
    if (first) { lx = ax; ly = ay; first = false; }
    var f = reduce ? 1 : .12; lx += (ax - lx) * f; ly += (ay - ly) * f;
    var nt = darkQ.matches ? 1 : 0; night += (nt - night) * (reduce ? 1 : .08);
    if (Math.abs(ax - lx) + Math.abs(ay - ly) > .3 || Math.abs(nt - night) > .002) more = true;
    var vw = window.innerWidth * dpr, vh = window.innerHeight * dpr;
    gl.uniform4f(U.uTex, texRect[0], texRect[1], texRect[2], texRect[3]);
    gl.uniform2f(U.uVp, vw, vh);
    gl.uniform3f(U.uL, lx * dpr, H - ly * dpr, Math.max(Math.min(vw, vh) * .42, Math.max(vw, vh) * .3));
    gl.uniform1f(U.uI, I); gl.uniform1f(U.uNight, night); gl.uniform1f(U.uDpr, dpr); gl.uniform1f(U.uP, Pp);
    gl.drawArrays(gl.TRIANGLES, 0, 3);
    if (more) kick();
  }
  function pt(ev) { tx = ev.pageX; ty = ev.pageY; kick(); }
  window.addEventListener('pointermove', pt, { passive: true });
  window.addEventListener('pointerdown', pt, { passive: true });
  document.addEventListener('mouseleave', function () { tx = ty = null; kick(); });
  if (darkQ.addEventListener) darkQ.addEventListener('change', kick);

  // Überspringen und erneut abspielen
  document.addEventListener('click', function (ev) { if (playing) { ev.preventDefault(); ev.stopPropagation(); finish(); } }, true);
  document.addEventListener('keydown', function () { if (playing) finish(); });
  if (!reduce) {
    var home = document.querySelector('.top .home-link');
    if (home) home.addEventListener('click', function (e) {
      if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey || playing) return;
      e.preventDefault(); window.scrollTo(0, 0); play();
    });
  }

  var rt; window.addEventListener('resize', function () { clearTimeout(rt); rt = setTimeout(function () { build(); if (playing) pencil(); kick(); }, 150); });
  var started = false;
  function go() {
    if (started) return; started = true;
    build();
    if ((root.classList.contains('intro') || location.hash === '#intro') && !reduce) play(); else finish();
  }
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(go, go);
  setTimeout(go, 1500);
})();
