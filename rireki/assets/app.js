/* =====================================================================
   Rireki UI runtime (mockup behaviour, no backend)
   - inline icon sprite            - i18n (5 languages) + language switcher
   - light/dark theme toggle       - sidebar, tabs, stepper, menus, modals
   - copy-to-clipboard + toasts    - bar charts with hover tooltips
   - viewer protection: watermark, blur on focus loss, blocked shortcuts
   ===================================================================== */
(function () {
  'use strict';

  /* ---------- helpers ---------- */
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  var store = {
    get: function (k) { try { return localStorage.getItem(k); } catch (e) { return null; } },
    set: function (k, v) { try { localStorage.setItem(k, v); } catch (e) {} }
  };
  var APP = document.documentElement.getAttribute('data-app') || 'tenant';
  var LANG_KEY = 'rireki.lang.' + (APP === 'viewer' ? 'viewer' : 'app');
  var THEME_KEY = 'rireki.theme';

  /* ---------- icon sprite (stroke icons, 24px grid) ---------- */
  var ICONS = {
    'home': '<path d="M3 10.5 12 3l9 7.5"/><path d="M5 9.5V21h14V9.5"/><path d="M10 21v-6h4v6"/>',
    'users': '<circle cx="9" cy="8" r="3.5"/><path d="M2.5 20a6.5 6.5 0 0 1 13 0"/><path d="M16 4.5a3.5 3.5 0 0 1 0 7"/><path d="M17.5 13.5a6.5 6.5 0 0 1 4 6.5"/>',
    'user': '<circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/>',
    'user-check': '<circle cx="9" cy="8" r="4"/><path d="M2 21a7 7 0 0 1 14 0"/><path d="m16 11 2 2 4-4"/>',
    'link': '<path d="M10 14a4 4 0 0 0 5.7 0l3-3a4 4 0 0 0-5.7-5.7l-1.5 1.5"/><path d="M14 10a4 4 0 0 0-5.7 0l-3 3a4 4 0 0 0 5.7 5.7l1.5-1.5"/>',
    'settings': '<circle cx="12" cy="12" r="3"/><path d="M12 2v2.5M12 19.5V22M2 12h2.5M19.5 12H22M4.9 4.9l1.8 1.8M17.3 17.3l1.8 1.8M4.9 19.1l1.8-1.8M17.3 6.7l1.8-1.8"/><circle cx="12" cy="12" r="7.5"/>',
    'shield': '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>',
    'file': '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6"/><path d="M8 13h8M8 17h8"/>',
    'file-plus': '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6"/><path d="M12 12v6M9 15h6"/>',
    'video': '<rect x="2" y="6" width="14" height="12" rx="2"/><path d="m16 10 6-3v10l-6-3z"/>',
    'upload': '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="m17 8-5-5-5 5"/><path d="M12 3v12"/>',
    'download': '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="m7 10 5 5 5-5"/><path d="M12 15V3"/>',
    'plus': '<path d="M12 5v14M5 12h14"/>',
    'search': '<circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3"/>',
    'bell': '<path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10.3 21a1.9 1.9 0 0 0 3.4 0"/>',
    'sun': '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
    'moon': '<path d="M21 12.8A9 9 0 1 1 11.2 3 7 7 0 0 0 21 12.8z"/>',
    'menu': '<path d="M4 6h16M4 12h16M4 18h16"/>',
    'chev-down': '<path d="m6 9 6 6 6-6"/>',
    'chev-right': '<path d="m9 6 6 6-6 6"/>',
    'chev-left': '<path d="m15 6-6 6 6 6"/>',
    'copy': '<rect x="9" y="9" width="12" height="12" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>',
    'eye': '<path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/>',
    'eye-off': '<path d="M17.9 17.9A10 10 0 0 1 12 19c-6.5 0-10-7-10-7a17 17 0 0 1 4.1-5.1"/><path d="M9.9 4.2A9.7 9.7 0 0 1 12 4c6.5 0 10 7 10 7a17 17 0 0 1-2 3"/><path d="M14.1 14.1a3 3 0 0 1-4.2-4.2"/><path d="m2 2 20 20"/>',
    'lock': '<rect x="4" y="11" width="16" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/>',
    'unlock': '<rect x="4" y="11" width="16" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 7.8-1"/>',
    'trash': '<path d="M3 6h18"/><path d="M8 6V4h8v2"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/><path d="M10 11v6M14 11v6"/>',
    'edit': '<path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4z"/>',
    'more': '<circle cx="5" cy="12" r="1.3" fill="currentColor"/><circle cx="12" cy="12" r="1.3" fill="currentColor"/><circle cx="19" cy="12" r="1.3" fill="currentColor"/>',
    'check': '<path d="m5 12 5 5L20 7"/>',
    'check-circle': '<circle cx="12" cy="12" r="9"/><path d="m8.5 12 2.5 2.5 4.5-5"/>',
    'x': '<path d="M18 6 6 18M6 6l12 12"/>',
    'alert': '<path d="M12 3 2 20h20z"/><path d="M12 10v4M12 17h.01"/>',
    'clock': '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    'globe': '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18"/>',
    'mail': '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 7 9 6 9-6"/>',
    'key': '<circle cx="8" cy="15" r="4"/><path d="m10.9 12.1 8.6-8.6"/><path d="m15 7 3 3M18 4l3 3"/>',
    'external': '<path d="M14 4h6v6"/><path d="M20 4 10 14"/><path d="M18 13v6a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h6"/>',
    'filter': '<path d="M3 5h18l-7 8v6l-4 2v-8z"/>',
    'calendar': '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M16 3v4M8 3v4M3 11h18"/>',
    'play': '<path d="M7 5v14l11-7z"/>',
    'image': '<rect x="3" y="4" width="18" height="16" rx="2"/><circle cx="9" cy="10" r="2"/><path d="m21 16-5-5-9 9"/>',
    'star': '<path d="m12 3 2.8 5.8 6.4.9-4.6 4.5 1.1 6.3L12 17.5l-5.7 3 1.1-6.3L2.8 9.7l6.4-.9z"/>',
    'activity': '<path d="M3 12h4l3-8 4 16 3-8h4"/>',
    'list': '<path d="M8 6h13M8 12h13M8 18h13"/><path d="M3 6h.01M3 12h.01M3 18h.01"/>',
    'help': '<circle cx="12" cy="12" r="9"/><path d="M9.5 9.5a2.5 2.5 0 1 1 3.5 2.3c-.7.3-1 .8-1 1.5"/><path d="M12 17h.01"/>',
    'logout': '<path d="m10 17 5-5-5-5"/><path d="M15 12H3"/><path d="M12 3h6a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-6"/>',
    'building': '<rect x="4" y="3" width="16" height="18" rx="1"/><path d="M8 7h2M14 7h2M8 11h2M14 11h2M8 15h2M14 15h2M10 21v-3h4v3"/>',
    'card': '<rect x="2" y="5" width="20" height="14" rx="2"/><path d="M2 10h20"/>',
    'refresh': '<path d="M21 12a9 9 0 0 1-15.5 6.3L3 16"/><path d="M3 21v-5h5"/><path d="M3 12a9 9 0 0 1 15.5-6.3L21 8"/><path d="M21 3v5h-5"/>',
    'send': '<path d="m22 2-7 20-4-9-9-4z"/><path d="M22 2 11 13"/>',
    'archive': '<rect x="3" y="4" width="18" height="4" rx="1"/><path d="M5 8v12h14V8"/><path d="M10 12h4"/>',
    'printer': '<path d="M6 9V3h12v6"/><rect x="3" y="9" width="18" height="8" rx="2"/><path d="M6 14h12v7H6z"/>',
    'camera-off': '<path d="m2 2 20 20"/><path d="M7 7H5a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h12"/><path d="M9 4h6l2 3h2a2 2 0 0 1 2 2v7"/><path d="M14.5 14.5a3 3 0 0 1-4-4"/>',
    'monitor': '<rect x="2" y="4" width="20" height="13" rx="2"/><path d="M8 21h8M12 17v4"/>',
    'phone': '<rect x="6" y="2" width="12" height="20" rx="2"/><path d="M12 18h.01"/>',
    'pin': '<path d="M12 22s7-6 7-12a7 7 0 0 0-14 0c0 6 7 12 7 12z"/><circle cx="12" cy="10" r="2.5"/>',
    'arrow-left': '<path d="M19 12H5"/><path d="m12 19-7-7 7-7"/>',
    'arrow-right': '<path d="M5 12h14"/><path d="m12 5 7 7-7 7"/>',
    'info': '<circle cx="12" cy="12" r="9"/><path d="M12 16v-4M12 8h.01"/>',
    'sparkles': '<path d="m12 3 1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8z"/><path d="m19 17 .8 2.2L22 20l-2.2.8L19 23l-.8-2.2L16 20l2.2-.8z"/>',
    'form': '<rect x="4" y="3" width="16" height="18" rx="2"/><path d="M8 8h8M8 12h8M8 16h5"/>',
    'layers': '<path d="m12 3 9 5-9 5-9-5z"/><path d="m3 12.5 9 5 9-5"/>',
    'ban': '<circle cx="12" cy="12" r="9"/><path d="m5.6 5.6 12.8 12.8"/>',
    'languages': '<path d="m5 8 6 6"/><path d="m4 14 6-6 2-3"/><path d="M2 5h12"/><path d="M7 2h1"/><path d="m22 22-5-10-5 10"/><path d="M14 18h6"/>',
    'hash': '<path d="M4 9h16M4 15h16M10 3 8 21M16 3l-2 18"/>',
    'qr': '<rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><path d="M14 14h3v3h-3zM20 14v3M17 20h4M14 20h.01"/>'
  };
  function injectSprite() {
    var svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('aria-hidden', 'true');
    svg.setAttribute('style', 'position:absolute;width:0;height:0;overflow:hidden');
    svg.innerHTML = Object.keys(ICONS).map(function (k) {
      return '<symbol id="i-' + k + '" viewBox="0 0 24 24">' + ICONS[k] + '</symbol>';
    }).join('');
    document.body.insertBefore(svg, document.body.firstChild);
  }

  /* ---------- i18n ---------- */
  var LANGS = [['en', 'English'], ['ja', '日本語'], ['vi', 'Tiếng Việt'], ['my', 'မြန်မာ'], ['id', 'Bahasa Indonesia']];
  var I18N = window.RIREKI_I18N || { en: {} };
  var MSG = {
    copied: { en: 'Copied', ja: 'コピーしました', vi: 'Đã sao chép', id: 'Disalin', my: 'ကူးယူပြီး' },
    blocked: { en: 'Not available on a view-only link', ja: '閲覧専用リンクでは利用できません', vi: 'Không khả dụng trên link chỉ xem', id: 'Tidak tersedia pada tautan hanya-lihat', my: 'ကြည့်ရုံသာလင့်ခ်တွင် မရနိုင်ပါ' },
    screenshot: { en: 'Screenshots are not permitted. This attempt was logged.', ja: 'スクリーンショットは禁止されています。この操作は記録されました。', vi: 'Không được chụp màn hình. Hành động này đã được ghi lại.', id: 'Tangkapan layar tidak diizinkan. Percobaan ini dicatat.', my: 'Screenshot ရိုက်ခွင့်မပြုပါ။ ဤကြိုးပမ်းမှုကို မှတ်တမ်းတင်ထားသည်။' },
    sent: { en: 'Sent to the sender', ja: '送出機関に送信しました', vi: 'Đã gửi cho bên gửi', id: 'Dikirim ke pengirim', my: 'ပို့သူထံ ပို့ပြီး' },
    saved: { en: 'Saved', ja: '保存しました', vi: 'Đã lưu', id: 'Tersimpan', my: 'သိမ်းပြီး' }
  };
  var currentLang = 'en';
  function t(key, lang) {
    lang = lang || currentLang;
    if (I18N[lang] && I18N[lang][key] != null) return I18N[lang][key];
    if (I18N.en && I18N.en[key] != null) return I18N.en[key];
    return null;
  }
  function msg(k) { var m = MSG[k]; return (m && (m[currentLang] || m.en)) || ''; }
  function applyLang(lang) {
    if (!LANGS.some(function (l) { return l[0] === lang; })) lang = 'en';
    currentLang = lang;
    document.documentElement.lang = lang;
    document.documentElement.setAttribute('data-lang', lang);
    $$('[data-i18n]').forEach(function (el) { var v = t(el.getAttribute('data-i18n'), lang); if (v != null) el.textContent = v; });
    $$('[data-i18n-placeholder]').forEach(function (el) { var v = t(el.getAttribute('data-i18n-placeholder'), lang); if (v != null) el.placeholder = v; });
    $$('select.lang-select').forEach(function (s) { s.value = lang; });
    store.set(LANG_KEY, lang);
  }
  function renderLangSwitchers() {
    $$('[data-lang-switch]').forEach(function (host) {
      host.className += ' lang-wrap';
      host.innerHTML = '<svg class="ic ic-sm"><use href="#i-globe"/></svg><select class="lang-select" aria-label="Language">' +
        LANGS.map(function (l) { return '<option value="' + l[0] + '">' + l[1] + '</option>'; }).join('') + '</select>';
      $('select', host).addEventListener('change', function (e) { applyLang(e.target.value); });
    });
  }

  /* ---------- theme ---------- */
  function effectiveTheme() {
    var set = document.documentElement.getAttribute('data-theme');
    if (set) return set;
    return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }
  function setThemeIcons() {
    var dark = effectiveTheme() === 'dark';
    $$('[data-theme-toggle] use').forEach(function (u) { u.setAttribute('href', dark ? '#i-sun' : '#i-moon'); });
  }
  function initTheme() {
    var saved = store.get(THEME_KEY);
    if (saved === 'dark' || saved === 'light') document.documentElement.setAttribute('data-theme', saved);
    setThemeIcons();
    $$('[data-theme-toggle]').forEach(function (b) {
      b.addEventListener('click', function () {
        var next = effectiveTheme() === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', next);
        store.set(THEME_KEY, next);
        setThemeIcons();
      });
    });
  }

  /* ---------- toasts ---------- */
  function toast(text, kind) {
    var host = $('#toasts');
    if (!host) { host = document.createElement('div'); host.className = 'toasts'; host.id = 'toasts'; document.body.appendChild(host); }
    var el = document.createElement('div');
    el.className = 'toast' + (kind === 'warn' ? ' warn' : '');
    el.setAttribute('role', 'status');
    el.innerHTML = '<svg class="ic ic-sm"><use href="#' + (kind === 'warn' ? 'i-ban' : 'i-check-circle') + '"/></svg><span></span>';
    $('span', el).textContent = text;
    host.appendChild(el);
    setTimeout(function () { el.style.opacity = '0'; el.style.transition = 'opacity .25s'; }, 2400);
    setTimeout(function () { if (el.parentNode) el.parentNode.removeChild(el); }, 2700);
  }

  /* ---------- shell: sidebar, menus, modals ---------- */
  function initShell() {
    $$('[data-nav-toggle]').forEach(function (b) { b.addEventListener('click', function () { document.body.classList.toggle('sidebar-open'); }); });
    $$('[data-nav-close]').forEach(function (b) { b.addEventListener('click', function () { document.body.classList.remove('sidebar-open'); }); });
    document.addEventListener('click', function (e) {
      $$('details.menu[open]').forEach(function (d) { if (!d.contains(e.target)) d.removeAttribute('open'); });
    });
    $$('[data-modal-open]').forEach(function (b) {
      b.addEventListener('click', function () { var m = document.getElementById(b.getAttribute('data-modal-open')); if (m) { m.hidden = false; var f = $('input,textarea,select', m); if (f) f.focus(); } });
    });
    $$('[data-modal-close]').forEach(function (b) {
      b.addEventListener('click', function () { var m = b.closest('.modal-backdrop'); if (m) m.hidden = true; });
    });
    $$('.modal-backdrop').forEach(function (m) { m.addEventListener('click', function (e) { if (e.target === m) m.hidden = true; }); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') $$('.modal-backdrop').forEach(function (m) { m.hidden = true; }); });
  }

  /* ---------- tabs ---------- */
  function initTabs() {
    $$('[data-tabs]').forEach(function (group) {
      var tabs = $$('[data-tab]', group);
      function activate(id, push) {
        if (!tabs.some(function (tb) { return tb.getAttribute('data-tab') === id; })) return;
        tabs.forEach(function (tb) { tb.classList.toggle('active', tb.getAttribute('data-tab') === id); });
        $$('[data-tab-panel]').forEach(function (p) { p.hidden = p.getAttribute('data-tab-panel') !== id; });
        if (group.hasAttribute('data-tabs-hash') && push) { try { history.replaceState(null, '', '#' + id); } catch (e) {} }
      }
      tabs.forEach(function (tb) { tb.addEventListener('click', function (e) { if (tb.tagName === 'A') e.preventDefault(); activate(tb.getAttribute('data-tab'), true); }); });
      group._activate = activate;
      var h = (location.hash || '').replace('#', '');
      if (h) activate(h, false);
    });
    $$('[data-tab-link]').forEach(function (a) {
      a.addEventListener('click', function (e) { e.preventDefault(); var g = $('[data-tabs]'); if (g && g._activate) g._activate(a.getAttribute('data-tab-link'), true); });
    });
  }

  /* ---------- stepper ---------- */
  function initSteppers() {
    $$('[data-stepper]').forEach(function (st) {
      var steps = $$('.step[data-step]', st);
      var panels = $$('[data-step-panel]');
      var cur = 1;
      function go(n) {
        n = Math.max(1, Math.min(steps.length, n)); cur = n;
        steps.forEach(function (s) { var i = +s.getAttribute('data-step'); s.classList.toggle('done', i < n); s.classList.toggle('active', i === n); });
        panels.forEach(function (p) { p.hidden = +p.getAttribute('data-step-panel') !== n; });
        var first = panels.filter(function (p) { return !p.hidden; })[0];
        if (first) { var top = first.getBoundingClientRect().top + window.pageYOffset - 80; if (top < window.pageYOffset) window.scrollTo({ top: top, behavior: 'smooth' }); }
      }
      steps.forEach(function (s) { s.addEventListener('click', function () { go(+s.getAttribute('data-step')); }); });
      $$('[data-step-go]').forEach(function (b) {
        b.addEventListener('click', function () {
          var v = b.getAttribute('data-step-go');
          go(v === 'next' ? cur + 1 : v === 'prev' ? cur - 1 : +v);
        });
      });
    });
  }

  /* ---------- copy, select-all, password, subdomain ---------- */
  function copyText(text) {
    var done = function () { toast(msg('copied')); };
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(done, function () { fallbackCopy(text); done(); });
    } else { fallbackCopy(text); done(); }
  }
  function fallbackCopy(text) {
    var ta = document.createElement('textarea'); ta.value = text; ta.setAttribute('readonly', ''); ta.style.position = 'fixed'; ta.style.opacity = '0';
    document.body.appendChild(ta); ta.select(); try { document.execCommand('copy'); } catch (e) {} document.body.removeChild(ta);
  }
  function initControls() {
    $$('[data-copy]').forEach(function (b) { b.addEventListener('click', function (e) { e.preventDefault(); copyText(b.getAttribute('data-copy')); }); });
    $$('[data-select-all]').forEach(function (master) {
      var table = master.closest('table');
      master.addEventListener('change', function () {
        $$('tbody input[type=checkbox]', table).forEach(function (c) { c.checked = master.checked; });
        updateCount();
      });
      $$('tbody input[type=checkbox]', table).forEach(function (c) { c.addEventListener('change', updateCount); });
      function updateCount() { var n = $$('tbody input[type=checkbox]:checked', table).length; var out = $('#selCount'); if (out) out.textContent = n; var bar = $('#bulkBar'); if (bar) bar.hidden = n === 0; }
    });
    $$('[data-pw-toggle]').forEach(function (b) {
      b.addEventListener('click', function () {
        var inp = document.getElementById(b.getAttribute('data-pw-toggle')); if (!inp) return;
        var show = inp.type === 'password'; inp.type = show ? 'text' : 'password';
        var u = $('use', b); if (u) u.setAttribute('href', show ? '#i-eye-off' : '#i-eye');
      });
    });
    var src = $('[data-subdomain-source]'), sub = $('[data-subdomain-input]');
    if (src && sub) {
      var touched = false;
      sub.addEventListener('input', function () { touched = true; showSub(); });
      src.addEventListener('input', function () {
        if (touched) return;
        sub.value = src.value.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/đ/g, 'd').replace(/\b(jsc|co|ltd|company|manpower|corp|inc)\b/g, '').replace(/[^a-z0-9]+/g, '').slice(0, 24);
        showSub();
      });
      function showSub() { var h = $('#subHint'); if (h && sub.value) { h.textContent = 'https://' + sub.value + '.rireki.app'; h.style.color = 'var(--success)'; } }
    }
    var ib = $('#interestBtn');
    if (ib) ib.addEventListener('click', function () { ib.classList.toggle('btn-primary'); ib.classList.toggle('btn-soft'); toast(msg('sent')); });
    $$('form').forEach(function (f) { if (!f.getAttribute('onsubmit')) f.addEventListener('submit', function (e) { e.preventDefault(); toast(msg('saved')); }); });
  }

  /* ---------- bar chart (single series, hover tooltip) ---------- */
  function niceMax(v) {
    if (v <= 5) return 5; if (v <= 10) return 10; if (v <= 20) return 20; if (v <= 25) return 25; if (v <= 50) return 50;
    var p = Math.pow(10, Math.floor(Math.log10(v))); return Math.ceil(v / p) * p;
  }
  function renderBarChart(el) {
    var values = el.getAttribute('data-values').split(',').map(Number);
    var labels = (el.getAttribute('data-labels') || '').split(',');
    var hlFrom = el.hasAttribute('data-highlight-from') ? +el.getAttribute('data-highlight-from') : 0;
    var compact = el.getAttribute('data-compact') === 'true';
    var unit = el.getAttribute('data-unit') || '';
    var W = 640, H = compact ? 130 : 220, padL = compact ? 26 : 34, padR = 10, padT = 14, padB = compact ? 22 : 26;
    var top = niceMax(Math.max.apply(null, values));
    var plotW = W - padL - padR, plotH = H - padT - padB;
    var band = plotW / values.length, bw = Math.min(24, band * 0.62), r = 4;
    var maxI = values.indexOf(Math.max.apply(null, values));
    var s = '<svg viewBox="0 0 ' + W + ' ' + H + '" role="img">';
    for (var g = 0; g <= 4; g++) {
      var y = padT + plotH - (g / 4) * plotH;
      s += '<line class="grid-line" x1="' + padL + '" x2="' + (W - padR) + '" y1="' + y.toFixed(1) + '" y2="' + y.toFixed(1) + '"/>';
      s += '<text class="axis-text" x="' + (padL - 6) + '" y="' + (y + 4).toFixed(1) + '" text-anchor="end">' + Math.round(top * g / 4) + '</text>';
    }
    var every = values.length > 16 ? 2 : 1;
    values.forEach(function (v, i) {
      var x = padL + i * band + (band - bw) / 2, h = (v / top) * plotH, y0 = padT + plotH - h;
      var cls = 'bar' + (i < hlFrom ? ' dim' : '');
      var d = h > r ? 'M' + x.toFixed(1) + ',' + (y0 + r).toFixed(1) + ' a' + r + ',' + r + ' 0 0 1 ' + r + ',-' + r + ' h' + (bw - 2 * r).toFixed(1) + ' a' + r + ',' + r + ' 0 0 1 ' + r + ',' + r + ' v' + (h - r).toFixed(1) + ' h-' + bw.toFixed(1) + ' z'
        : 'M' + x.toFixed(1) + ',' + y0.toFixed(1) + ' h' + bw.toFixed(1) + ' v' + h.toFixed(1) + ' h-' + bw.toFixed(1) + ' z';
      s += '<path class="' + cls + '" d="' + d + '"/>';
      if (i === maxI || i === values.length - 1) s += '<text class="value-text" x="' + (x + bw / 2).toFixed(1) + '" y="' + (y0 - 5).toFixed(1) + '" text-anchor="middle">' + v + '</text>';
      if (i % every === 0) s += '<text class="axis-text" x="' + (x + bw / 2).toFixed(1) + '" y="' + (H - 8) + '" text-anchor="middle">' + (labels[i] || '') + '</text>';
      s += '<rect class="hit" data-i="' + i + '" x="' + (padL + i * band).toFixed(1) + '" y="' + padT + '" width="' + band.toFixed(1) + '" height="' + plotH + '"/>';
    });
    s += '</svg><div class="chart-tip" role="tooltip"></div>';
    el.innerHTML = s;
    var tip = $('.chart-tip', el), svg = $('svg', el);
    $$('.hit', el).forEach(function (hit) {
      hit.addEventListener('mouseenter', function () {
        var i = +hit.getAttribute('data-i'), sb = svg.getBoundingClientRect(), cb = el.getBoundingClientRect();
        var scale = sb.width / W, x = padL + i * band + band / 2, h = (values[i] / top) * plotH, y = padT + plotH - h;
        tip.textContent = (labels[i] ? labels[i] + ': ' : '') + values[i] + (unit ? ' ' + unit : '');
        tip.style.left = ((sb.left - cb.left) + x * scale) + 'px'; tip.style.top = ((sb.top - cb.top) + y * scale) + 'px';
        tip.classList.add('show');
      });
      hit.addEventListener('mouseleave', function () { tip.classList.remove('show'); });
    });
  }

  /* ---------- watermark ---------- */
  function renderWatermarks() {
    $$('[data-watermark]').forEach(function (wm) {
      var host = wm.parentNode, w = host.offsetWidth, h = host.offsetHeight;
      if (!w || !h) return;
      var now = new Date(), stamp = now.getFullYear() + '-' + ('0' + (now.getMonth() + 1)).slice(-2) + '-' + ('0' + now.getDate()).slice(-2) + ' ' + ('0' + now.getHours()).slice(-2) + ':' + ('0' + now.getMinutes()).slice(-2);
      var text = wm.getAttribute('data-watermark') + ' · ' + stamp;
      var out = '', row = 0;
      for (var y = 30; y < h + 60; y += 96, row++) {
        for (var x = (row % 2 ? -160 : -20); x < w + 200; x += 340) {
          out += '<span style="left:' + x + 'px;top:' + y + 'px' + (wm.hasAttribute('data-wm-light') ? ';color:rgba(255,255,255,.22)' : '') + '">' + text.replace(/</g, '&lt;') + '</span>';
        }
      }
      wm.innerHTML = out;
    });
  }

  /* ---------- viewer protection ---------- */
  function initProtection() {
    if (document.body.getAttribute('data-protected') !== 'true') return;
    var lastToast = 0;
    function warn(k) { var n = Date.now(); if (n - lastToast > 1200) { toast(msg(k), 'warn'); lastToast = n; } }
    document.addEventListener('contextmenu', function (e) { e.preventDefault(); warn('blocked'); });
    document.addEventListener('dragstart', function (e) { e.preventDefault(); });
    document.addEventListener('copy', function (e) { e.preventDefault(); warn('blocked'); });
    document.addEventListener('cut', function (e) { e.preventDefault(); });
    document.addEventListener('keydown', function (e) {
      var k = (e.key || '').toLowerCase();
      if ((e.ctrlKey || e.metaKey) && ['s', 'p', 'u', 'c', 'a', 'x'].indexOf(k) >= 0) { e.preventDefault(); warn('blocked'); }
      if (k === 'printscreen' || ((e.metaKey && e.shiftKey && ['3', '4', '5'].indexOf(k) >= 0))) {
        e.preventDefault(); document.body.classList.add('is-inactive'); warn('screenshot');
        setTimeout(function () { document.body.classList.remove('is-inactive'); }, 1800);
      }
      if (k === 'f12') e.preventDefault();
    });
    function hide() { document.body.classList.add('is-inactive'); }
    function show() { document.body.classList.remove('is-inactive'); }
    window.addEventListener('blur', hide);
    window.addEventListener('focus', show);
    document.addEventListener('visibilitychange', function () { if (document.hidden) hide(); else show(); });
    $$('.blur-shield').forEach(function (s) { s.addEventListener('click', function () { show(); window.focus(); }); });
  }

  /* ---------- boot ---------- */
  function boot() {
    injectSprite();
    renderLangSwitchers();
    var saved = store.get(LANG_KEY);
    var htmlLang = document.documentElement.getAttribute('lang') || 'en';
    applyLang(saved || htmlLang);
    initTheme();
    initShell();
    initTabs();
    initSteppers();
    initControls();
    $$('[data-bar-chart]').forEach(renderBarChart);
    renderWatermarks();
    initProtection();
    var rt; window.addEventListener('resize', function () { clearTimeout(rt); rt = setTimeout(renderWatermarks, 150); });
    setInterval(renderWatermarks, 60000);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot); else boot();

  window.RirekiUI = { toast: toast, applyLang: applyLang, t: t };
})();
