/* Leotio – Lade-Animation der Startseite (Variante D4b „Zirkel“).
   Ein Lichtpunkt zieht das Quadrat, ein Zirkel konstruiert den Eckpunkt des L (Teilung 1 : √2),
   der Lichtpunkt zieht das L, dann wandert das Zeichen in die Kopfzeile und der Name erscheint.
   Läuft einmal pro Sitzung, nicht bei „Bewegung reduzieren“, Klick oder Taste überspringt.
   Erneut: Klick auf das Logo der Kopfzeile oder das große Zeichen (beim Darüberfahren zeigt es seine Hilfslinien) oder Adresse #intro. */
(function () {
  var root = document.documentElement, NS = 'http://www.w3.org/2000/svg', running = false;
  var logo = document.querySelector('.top .logo');
  var reduce = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
  function el(n, at, parent) { var e = document.createElementNS(NS, n); for (var k in at) e.setAttribute(k, at[k]); if (parent) parent.appendChild(e); return e; }
  if (!logo || !document.body.animate) { root.classList.remove('intro'); return; }

  // Großes Zeichen: Hilfslinien beim Darüberfahren, Klick spielt die Animation erneut
  var fig = document.querySelector('.hero .figure'), z = fig && fig.querySelector('.zeichen');
  if (z && !reduce) {
    var hint = el('g', { 'class': 'z-hint' });
    el('path', { d: 'M100,100 A100,100 0 0 1 29.29,70.71' }, hint);
    el('line', { x1: 29.29, y1: 70.71, x2: 100, y2: 0, 'stroke-dasharray': '2 2' }, hint);
    el('line', { x1: 29.29, y1: -12, x2: 29.29, y2: 112 }, hint);
    el('line', { x1: -12, y1: 70.71, x2: 112, y2: 70.71 }, hint);
    z.insertBefore(hint, z.firstChild);
    fig.classList.add('z-play');
    fig.setAttribute('role', 'button'); fig.setAttribute('tabindex', '0');
    fig.setAttribute('aria-label', document.documentElement.lang === 'de' ? 'Konstruktion des Zeichens zeigen' : 'Show how the mark is constructed');
    fig.addEventListener('click', function () { if (!running) { window.scrollTo(0, 0); run(); } });
    fig.addEventListener('keydown', function (e) { if ((e.key === 'Enter' || e.key === ' ') && !running) { e.preventDefault(); e.stopPropagation(); run(); } });
  }
  // Logo in der Kopfzeile: auf der Startseite spielt ein Klick die Animation statt neu zu laden
  var home = document.querySelector('.top .home-link');
  if (home && !reduce) home.addEventListener('click', function (e) {
    if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
    e.preventDefault(); if (!running) { window.scrollTo(0, 0); run(); }
  });
  if (location.hash === '#intro' && !reduce) root.classList.add('intro');
  if (root.classList.contains('intro')) run();

  function run() {
    root.classList.add('intro'); running = true;
    try { sessionStorage.setItem('leotio-intro', '1'); } catch (e) {}

    // Zeichen in Einheiten des Logos: Seite 161.8, Linie 6.375, L bei x 44.2 / y 111.2
    var A = 161.803, W = 6.375, IX = 44.204, IY = 111.225, PAD = 40;
    var overlay = document.createElement('div');
    overlay.className = 'intro-stage';
    overlay.setAttribute('aria-hidden', 'true');
    var svg = el('svg', { viewBox: (-PAD) + ' ' + (-PAD) + ' ' + (A + 2 * PAD) + ' ' + (A + 2 * PAD) });
    overlay.appendChild(svg);
    var gl = el('g', {}, svg);
    var g = el('g', {}, svg);
    // Konstruktion
    var pin = el('circle', { cx: A, cy: 0, r: 2.2, 'class': 'i-pin' }, gl);
    var rad = el('line', { x1: A, y1: 0, x2: A, y2: A, 'class': 'i-guide' }, gl);
    var arc = el('path', { d: 'M' + A + ',' + A + ' A' + A + ',' + A + ' 0 0 1 ' + (IX + W / 2) + ',' + (IY + W / 2), 'class': 'i-guide' }, gl);
    var diag = el('line', { x1: IX + W / 2, y1: IY + W / 2, x2: A, y2: 0, 'class': 'i-guide', 'stroke-dasharray': '3 3' }, gl);
    var mark = el('circle', { cx: IX + W / 2, cy: IY + W / 2, r: 3.6, 'class': 'i-guide' }, gl);
    var lv = el('line', { x1: IX + W / 2, y1: -24, x2: IX + W / 2, y2: A + 24, 'class': 'i-guide' }, gl);
    var lh = el('line', { x1: -24, y1: IY + W / 2, x2: A + 24, y2: IY + W / 2, 'class': 'i-guide' }, gl);
    // Linien in Zeichenreihenfolge: oben, rechts, unten, links, dann L senkrecht, L waagerecht
    var segs = [
      [0, 0, A, W, 'X', 'left'], [A - W, 0, W, A, 'Y', 'top'], [0, A - W, A, W, 'X', 'right'], [0, 0, W, A, 'Y', 'bottom'],
      [IX, 0, W, IY + W, 'Y', 'top'], [IX, IY, A - IX, W, 'X', 'left']
    ].map(function (s) {
      var r = el('rect', { x: s[0], y: s[1], width: s[2], height: s[3], fill: 'currentColor' }, g);
      r.style.transformBox = 'fill-box'; r.style.transformOrigin = s[5]; r.style.transform = 'scale' + s[4] + '(0)';
      return [r, s[4]];
    });
    var dot = el('circle', { r: 6.5, 'class': 'i-dot' }, g);
    document.body.appendChild(overlay);

    var anims = [], skip = false, finished = false;
    function an(node, kf, o) { var a = node.animate(kf, o); anims.push(a); return a; }

    var seg = 270, t0 = 200, t = t0, ends = [];
    segs.forEach(function (s, i) {
      if (i === 4) t += 2000;
      an(s[0], [{ transform: 'scale' + s[1] + '(0)' }, { transform: 'scale' + s[1] + '(1)' }], { duration: seg, delay: t, fill: 'both', easing: 'linear' });
      ends.push(t); t += seg;
    });
    var drawEnd = t, sqEnd = ends[3] + seg, h = W / 2, f = A - h, ix = IX + h, iy = IY + h;
    var span = drawEnd - t0, off = function (ms) { return (ms - t0) / span; };
    an(dot, [
      { transform: 'translate(' + h + 'px,' + h + 'px)', offset: 0 },
      { transform: 'translate(' + f + 'px,' + h + 'px)', offset: off(ends[1]) },
      { transform: 'translate(' + f + 'px,' + f + 'px)', offset: off(ends[2]) },
      { transform: 'translate(' + h + 'px,' + f + 'px)', offset: off(ends[3]) },
      { transform: 'translate(' + h + 'px,' + h + 'px)', offset: off(sqEnd) },
      { transform: 'translate(' + ix + 'px,' + h + 'px)', offset: off(ends[4]) },
      { transform: 'translate(' + ix + 'px,' + iy + 'px)', offset: off(ends[5]) },
      { transform: 'translate(' + f + 'px,' + iy + 'px)', offset: 1 }
    ], { duration: span, delay: t0, fill: 'both', easing: 'linear' });
    an(dot, [{ opacity: 0 }, { opacity: 1, offset: .05 }, { opacity: 1, offset: .9 }, { opacity: 0 }], { duration: sqEnd - t0 + 200, delay: t0 - 50, fill: 'backwards' });
    an(dot, [{ opacity: 0 }, { opacity: 1, offset: .08 }, { opacity: 1, offset: .92 }, { opacity: 0 }], { duration: drawEnd - ends[4] + 300, delay: ends[4] - 50, fill: 'forwards' });

    // Konstruktion einblenden, nach dem L wieder ausblenden
    var c0 = sqEnd + 100, fade = drawEnd + 250, op = .8, ease = 'cubic-bezier(.45,0,.2,1)';
    function show(e, at, dur) {
      an(e, [{ opacity: 0 }, { opacity: op }], { duration: dur || 250, delay: at, fill: 'backwards' });
      an(e, [{ opacity: op }, { opacity: 0 }], { duration: 450, delay: fade, fill: 'forwards' });
      e.style.opacity = op;
    }
    show(pin, c0); show(rad, c0);
    rad.style.transformBox = 'view-box'; rad.style.transformOrigin = A + 'px 0px';
    an(rad, [{ transform: 'rotate(0deg)' }, { transform: 'rotate(45deg)' }], { duration: 800, delay: c0 + 200, fill: 'both', easing: ease });
    // Strichlänge in SVG-Einheiten: ohne non-scaling-stroke, Linienstärke passend zur Bühne umgerechnet
    var k = svg.getBoundingClientRect().width / (A + 2 * PAD) || 1;
    arc.style.vectorEffect = 'none'; arc.style.strokeWidth = .8 / k;
    var L = arc.getTotalLength(); arc.style.strokeDasharray = L + ' ' + L; show(arc, c0 + 200, 1);
    an(arc, [{ strokeDashoffset: L }, { strokeDashoffset: 0 }], { duration: 800, delay: c0 + 200, fill: 'both', easing: ease });
    mark.style.transformBox = 'fill-box'; mark.style.transformOrigin = 'center'; show(mark, c0 + 1000, 1);
    an(mark, [{ transform: 'scale(2.5)' }, { transform: 'scale(1)' }], { duration: 300, delay: c0 + 1000, fill: 'both', easing: 'ease-out' });
    show(diag, c0 + 1050, 300);
    [[lv, 'Y', '50% 58%'], [lh, 'X', '35% 50%']].forEach(function (x) {
      x[0].style.transformBox = 'fill-box'; x[0].style.transformOrigin = x[2]; show(x[0], c0 + 1350, 1);
      an(x[0], [{ transform: 'scale' + x[1] + '(0)' }, { transform: 'scale' + x[1] + '(1)' }], { duration: 450, delay: c0 + 1350, fill: 'both', easing: 'cubic-bezier(.2,.7,.2,1)' });
    });

    // Zeichen wandert in die Kopfzeile
    var move = drawEnd + 150, moveDur = 650;
    var flyTimer = setTimeout(fly, move);
    function fly() {
      if (skip) return;
      var s = svg.getBoundingClientRect(), k = s.width / (A + 2 * PAD), l = logo.getBoundingClientRect();
      var sx = s.left + PAD * k, sy = s.top + PAD * k, side = A * k, scale = l.height / side;
      svg.style.transformOrigin = (PAD * k) + 'px ' + (PAD * k) + 'px';
      an(svg, [{ transform: 'none' }, { transform: 'translate(' + (l.left - sx) + 'px,' + (l.top - sy) + 'px) scale(' + scale + ')' }], { duration: moveDur, fill: 'forwards', easing: 'cubic-bezier(.6,0,.2,1)' });
      an(overlay, [{ backgroundColor: getComputedStyle(overlay).backgroundColor }, { backgroundColor: 'transparent' }], { duration: moveDur, fill: 'forwards', easing: 'ease-in' });
      setTimeout(finish, moveDur);
    }

    function finish() {
      if (finished) return; finished = true;
      if (overlay.parentNode) overlay.parentNode.removeChild(overlay);
      var letters = [].slice.call(logo.children, 6), rest = document.querySelectorAll('.lang, .hero, footer');
      letters.forEach(function (n, i) { n.animate([{ opacity: 0, transform: 'translateY(6px)' }, { opacity: 1, transform: 'none' }], { duration: 450, delay: skip ? 0 : i * 60, fill: 'backwards', easing: 'cubic-bezier(.2,.7,.2,1)' }); });
      [].forEach.call(rest, function (n) { n.animate([{ opacity: 0, transform: 'translateY(8px)' }, { opacity: 1, transform: 'none' }], { duration: 600, delay: skip ? 0 : 350, fill: 'backwards', easing: 'cubic-bezier(.2,.7,.2,1)' }); });
      done();
    }
    function done() { root.classList.remove('intro'); running = false; document.removeEventListener('keydown', onSkip); }
    function onSkip() {
      if (skip || finished) return; skip = true; clearTimeout(flyTimer);
      anims.forEach(function (a) { a.cancel(); });
      finish();
    }
    overlay.addEventListener('click', onSkip);
    document.addEventListener('keydown', onSkip);
  }
})();
