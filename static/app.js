// ── Data ─────────────────────────────────────────────────────────────────────

const GROUPS = [
  { name: 'A', teams: [['🇲🇽','Mexico'],     ['🇰🇷','South Korea'],       ['🇿🇦','South Africa'],  ['🇨🇿','Czechia']] },
  { name: 'B', teams: [['🇨🇦','Canada'],     ['🇨🇭','Switzerland'],       ['🇶🇦','Qatar'],         ['🇧🇦','Bosnia & Herz.']] },
  { name: 'C', teams: [['🇧🇷','Brazil'],     ['🇲🇦','Morocco'],           ['🇭🇹','Haiti'],         ['🏴󠁧󠁢󠁳󠁣󠁴󠁿','Scotland']] },
  { name: 'D', teams: [['🇺🇸','USA'],        ['🇵🇾','Paraguay'],          ['🇦🇺','Australia'],     ['🇹🇷','Türkiye']] },
  { name: 'E', teams: [['🇩🇪','Germany'],    ['🇨🇼','Curaçao'],           ['🇨🇮','Ivory Coast'],   ['🇪🇨','Ecuador']] },
  { name: 'F', teams: [['🇳🇱','Netherlands'],['🇯🇵','Japan'],             ['🇸🇪','Sweden'],        ['🇹🇳','Tunisia']] },
  { name: 'G', teams: [['🇧🇪','Belgium'],    ['🇪🇬','Egypt'],             ['🇮🇷','Iran'],          ['🇳🇿','New Zealand']] },
  { name: 'H', teams: [['🇪🇸','Spain'],      ['🇨🇻','Cabo Verde'],        ['🇸🇦','Saudi Arabia'],  ['🇺🇾','Uruguay']] },
  { name: 'I', teams: [['🇫🇷','France'],     ['🇸🇳','Senegal'],           ['🇳🇴','Norway'],        ['🇮🇶','Iraq']] },
  { name: 'J', teams: [['🇦🇷','Argentina'],  ['🇩🇿','Algeria'],           ['🇦🇹','Austria'],       ['🇯🇴','Jordan']] },
  { name: 'K', teams: [['🇵🇹','Portugal'],   ['🇺🇿','Uzbekistan'],        ['🇨🇴','Colombia'],      ['🇨🇩','DR Congo']] },
  { name: 'L', teams: [['🏴󠁧󠁢󠁥󠁮󠁧󠁿','England'],   ['🇭🇷','Croatia'],           ['🇬🇭','Ghana'],         ['🇵🇦','Panama']] },
];

const FLAG = {};
GROUPS.forEach(g => g.teams.forEach(([f, n]) => { FLAG[n] = f; }));

const R32 = [
  { home:{type:'group',group:'A',pos:2}, away:{type:'group',group:'B',pos:2} },
  { home:{type:'group',group:'C',pos:1}, away:{type:'group',group:'F',pos:2} },
  { home:{type:'group',group:'E',pos:1}, away:{type:'third',rank:1}          },
  { home:{type:'group',group:'F',pos:1}, away:{type:'group',group:'C',pos:2} },
  { home:{type:'group',group:'E',pos:2}, away:{type:'group',group:'I',pos:2} },
  { home:{type:'group',group:'I',pos:1}, away:{type:'third',rank:2}          },
  { home:{type:'group',group:'A',pos:1}, away:{type:'third',rank:3}          },
  { home:{type:'group',group:'L',pos:1}, away:{type:'third',rank:4}          },
  { home:{type:'group',group:'G',pos:1}, away:{type:'third',rank:5}          },
  { home:{type:'group',group:'D',pos:1}, away:{type:'third',rank:6}          },
  { home:{type:'group',group:'H',pos:1}, away:{type:'group',group:'J',pos:2} },
  { home:{type:'group',group:'K',pos:2}, away:{type:'group',group:'L',pos:2} },
  { home:{type:'group',group:'B',pos:1}, away:{type:'third',rank:7}          },
  { home:{type:'group',group:'D',pos:2}, away:{type:'group',group:'G',pos:2} },
  { home:{type:'group',group:'J',pos:1}, away:{type:'group',group:'H',pos:2} },
  { home:{type:'group',group:'K',pos:1}, away:{type:'third',rank:8}          },
];

const R16_PAIRS = [[0,1],[2,3],[4,5],[6,7],[8,9],[10,11],[12,13],[14,15]];
const QF_PAIRS  = [[0,1],[2,3],[4,5],[6,7]];
const SF_PAIRS  = [[0,1],[2,3]];
const F_PAIRS   = [[0,1]];

const KO_ROUNDS = [
  { id:'r32', label:'Round of 32', pts:3,  count:16, pairs:null,     prevRound:null  },
  { id:'r16', label:'Round of 16', pts:5,  count:8,  pairs:R16_PAIRS,prevRound:'r32' },
  { id:'qf',  label:'Quarters',    pts:8,  count:4,  pairs:QF_PAIRS, prevRound:'r16' },
  { id:'sf',  label:'Semis',       pts:12, count:2,  pairs:SF_PAIRS, prevRound:'qf'  },
  { id:'f',   label:'Final',       pts:20, count:1,  pairs:F_PAIRS,  prevRound:'sf'  },
];

const ROUND_ORDER = ['r32','r16','qf','sf','f'];
const PAIRS_MAP   = { r16:R16_PAIRS, qf:QF_PAIRS, sf:SF_PAIRS, f:F_PAIRS };
const ROUND_LABELS = { r32:'Round of 32', r16:'Round of 16', qf:'Quarter-finals', sf:'Semi-finals', f:'Final' };

// Approximate WC 2026 KO kickoff times (UTC). Used only to gate picks until 72h before each match.
const KO_KICKOFFS = {
  r32: [
    '2026-06-28T16:00:00Z', '2026-06-28T19:00:00Z', '2026-06-28T22:00:00Z', '2026-06-29T01:00:00Z',
    '2026-06-29T16:00:00Z', '2026-06-29T19:00:00Z', '2026-06-29T22:00:00Z', '2026-06-30T01:00:00Z',
    '2026-06-30T16:00:00Z', '2026-06-30T19:00:00Z', '2026-06-30T22:00:00Z', '2026-07-01T01:00:00Z',
    '2026-07-01T16:00:00Z', '2026-07-01T19:00:00Z', '2026-07-01T22:00:00Z', '2026-07-02T01:00:00Z',
  ],
  r16: [
    '2026-07-04T16:00:00Z', '2026-07-04T20:00:00Z',
    '2026-07-05T16:00:00Z', '2026-07-05T20:00:00Z',
    '2026-07-06T16:00:00Z', '2026-07-06T20:00:00Z',
    '2026-07-07T16:00:00Z', '2026-07-07T20:00:00Z',
  ],
  qf: [
    '2026-07-09T20:00:00Z', '2026-07-10T20:00:00Z',
    '2026-07-11T20:00:00Z', '2026-07-11T23:00:00Z',
  ],
  sf: [
    '2026-07-14T20:00:00Z',
    '2026-07-15T20:00:00Z',
  ],
  f: [
    '2026-07-19T19:00:00Z',
  ],
};
const UNLOCK_HOURS_BEFORE = 72;

function koUnlockAt(round, idx) {
  const kickoffs = KO_KICKOFFS[round];
  if (!kickoffs || idx < 0 || idx >= kickoffs.length) return new Date(0);
  return new Date(new Date(kickoffs[idx]).getTime() - UNLOCK_HOURS_BEFORE * 3600 * 1000);
}
function koIsUnlocked(round, idx) {
  return Date.now() >= koUnlockAt(round, idx).getTime();
}
function formatKickoff(iso) {
  try {
    return new Intl.DateTimeFormat(undefined, {
      weekday: 'short', month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit',
    }).format(new Date(iso));
  } catch { return iso; }
}

// ── State ─────────────────────────────────────────────────────────────────────
let currentMode = '';
let playerEmail = '';
let playerName  = '';
let picks = { groups:{}, thirds_ranking:[], ko:{}, podium:{first:null,second:null,third:null} };
let wizardIdx = 0;
let koCursor = { r32: 0, r16: 0, qf: 0, sf: 0, f: 0 };
let lastChampionRequested = '';
let dragSourceIdx = null;
let actualResults = null;

const WIZARD_STEPS = buildWizardSteps();

function buildWizardSteps() {
  const steps = [
    { kind:'podium', slot:'first',  title:'Pick your champion', sub:'Who lifts the trophy?' },
    { kind:'podium', slot:'second', title:'Pick the runner-up', sub:'Who finishes second — i.e. who loses the final?' },
    { kind:'podium', slot:'third',  title:'Pick the 3rd place', sub:'Who wins the bronze game between the semi-final losers?' },
  ];
  GROUPS.forEach(g => {
    steps.push({ kind:'group', group:g.name, title:`Group ${g.name}`, sub:'Tap a team to cycle 1st → 2nd → 3rd → clear.' });
  });
  steps.push({ kind:'thirds', title:'Rank the third-place teams', sub:'Top 8 advance — order them by group-stage strength.' });
  KO_ROUNDS.forEach(r => {
    steps.push({ kind:'ko', round:r.id, title:r.label, sub:`Pick the winners of every ${r.label.toLowerCase()} match.` });
  });
  steps.push({ kind:'review', title:'Review &amp; submit', sub:'Double-check your picks, then save.' });
  return steps;
}

function qs(id) { return document.getElementById(id); }

// Windows doesn't render regional-indicator emoji as flags natively.
// Twemoji rewrites them to <img> tags from a CDN, scheduled on the next frame.
let _emojiParseScheduled = false;
function polyfillEmoji() {
  if (typeof twemoji === 'undefined' || !twemoji || !twemoji.parse) return;
  if (_emojiParseScheduled) return;
  _emojiParseScheduled = true;
  requestAnimationFrame(() => {
    _emojiParseScheduled = false;
    try {
      twemoji.parse(document.body, {
        folder: 'flags',
        ext: '.svg',
        base: '/static/',
        className: 'emoji',
      });
    } catch {}
  });
}

function showMessage(text, isError = false) {
  const el = qs(currentMode === 'simple' ? 'simpleSavedPill' : 'savedPill') || qs('savedPill');
  if (!el) return;
  el.textContent = text;
  el.className = 'saved-pill' + (isError ? ' error' : '');
  el.style.display = 'inline-block';
  setTimeout(() => { el.style.display = 'none'; }, 3000);
}

function normalizePicks() {
  if (!picks || typeof picks !== 'object') picks = {};
  if (!picks.groups || typeof picks.groups !== 'object') picks.groups = {};
  if (!Array.isArray(picks.thirds_ranking)) picks.thirds_ranking = [];
  if (!picks.ko || typeof picks.ko !== 'object') picks.ko = {};
  if (!picks.podium || typeof picks.podium !== 'object') picks.podium = {};
  for (const slot of ['first','second','third']) {
    if (typeof picks.podium[slot] !== 'string') picks.podium[slot] = null;
  }

  // Migrate legacy fields into podium.first
  if (!picks.podium.first && typeof picks.champion === 'string' && picks.champion) {
    picks.podium.first = picks.champion;
  }
  if (!picks.podium.first && picks.simple && Array.isArray(picks.simple.top5)) {
    const candidate = picks.simple.top5.find(t => typeof t === 'string' && t.trim());
    if (candidate) picks.podium.first = candidate.trim();
  }
  // Keep legacy mirror so /api/champion-latest etc. still work.
  picks.champion = picks.podium.first || null;
}

// ── Identity ──────────────────────────────────────────────────────────────────
async function submitIdentity() {
  const email = qs('emailInput').value.trim().toLowerCase();
  const name  = qs('nameInput').value.trim();
  const errEl = qs('identityError');

  if (!email || !email.includes('@') || !email.includes('.')) {
    errEl.textContent = 'Please enter a valid email address.';
    qs('emailInput').focus();
    return;
  }
  if (!name) {
    errEl.textContent = 'Please enter your display name.';
    qs('nameInput').focus();
    return;
  }
  errEl.textContent = '';

  playerEmail = email;
  playerName  = name;

  try {
    const res  = await fetch(`/api/picks/${encodeURIComponent(playerEmail)}`);
    const data = await res.json();
    if (data.ok && data.picks) {
      picks = data.picks;
      if (data.name) playerName = data.name;
      qs('nameInput').value = playerName;
    }
  } catch { /* offline */ }

  normalizePicks();
  await fetchActualResults();
  qs('nameScreen').style.display = 'none';
  showModeChooser();
}

function showModeChooser() {
  currentMode = '';
  qs('mainApp').style.display = 'none';
  qs('simpleApp').style.display = 'none';
  qs('modeScreen').style.display = 'flex';
  qs('modePlayerName').textContent = playerName;
  polyfillEmoji();
}

function startManualMode() {
  currentMode = 'manual';
  picks.mode = 'manual';
  qs('modeScreen').style.display = 'none';
  qs('simpleApp').style.display = 'none';
  qs('mainApp').style.display = 'block';
  qs('playerNameLabel').textContent = playerName;

  renderGroups();
  renderThirdsRanking();
  renderKO();
  refreshChampionCard('manualChampionCard');
}

function startSimpleMode() {
  currentMode = 'simple';
  picks.mode = 'easy';
  wizardIdx = pickResumeStep();
  qs('modeScreen').style.display = 'none';
  qs('mainApp').style.display = 'none';
  qs('simpleApp').style.display = 'block';
  qs('simplePlayerNameLabel').textContent = playerName;
  renderWizard();
  refreshChampionCard('wizardChampionCard');
}

function pickResumeStep() {
  normalizePicks();
  if (!picks.podium.first) return 0;
  for (let i = 1; i < WIZARD_STEPS.length; i++) {
    if (!stepIsComplete(WIZARD_STEPS[i])) return i;
  }
  return WIZARD_STEPS.length - 1;
}

function stepIsComplete(step) {
  if (step.kind === 'podium') return Boolean(picks.podium && picks.podium[step.slot]);
  if (step.kind === 'champion') return Boolean(picks.podium && picks.podium.first);
  if (step.kind === 'group') {
    const g = picks.groups[step.group] || {};
    return Boolean(g.first && g.second && g.third);
  }
  if (step.kind === 'thirds') {
    const thirdsPicked = GROUPS.filter(g => (picks.groups[g.name] || {}).third).length;
    return thirdsPicked === 12 && (picks.thirds_ranking || []).length >= 12;
  }
  if (step.kind === 'ko') {
    const roundDef = KO_ROUNDS.find(r => r.id === step.round);
    const round = picks.ko[step.round] || {};
    for (let i = 0; i < roundDef.count; i++) {
      // All KO matches lock until 72h before kickoff — don't block the wizard on those.
      if (!koIsUnlocked(step.round, i)) continue;
      if (!(round[i] && round[i].winner)) return false;
    }
    return true;
  }
  return true;
}

// ── Tabs ──────────────────────────────────────────────────────────────────────
function showTab(id, btn) {
  document.querySelectorAll('.pane').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  qs(`pane-${id}`).classList.add('active');
  btn.classList.add('active');
  if (id === 'leaderboard') renderLeaderboard();
  if (id === 'thirds')      renderThirdsRanking();
  if (id === 'ko')          renderKO();
}

// ── Groups ────────────────────────────────────────────────────────────────────
function renderGroups() {
  renderPodiumPicker();
  const grid = qs('groupsGrid');
  grid.innerHTML = '';
  GROUPS.forEach(group => grid.appendChild(buildGroupCard(group)));
  polyfillEmoji();
}

function renderPodiumPicker() {
  const container = qs('podiumPicker');
  if (!container) return;
  if (!picks.podium) picks.podium = { first:null, second:null, third:null };

  const sortedTeams = allTeams().slice().sort();
  const slots = [
    { key:'first',  label:'🥇 Champion (10 pts)' },
    { key:'second', label:'🥈 Runner-up (6 pts)' },
    { key:'third',  label:'🥉 3rd place (4 pts)' },
  ];

  container.innerHTML = '';
  slots.forEach(slot => {
    const currentTeam = picks.podium[slot.key];
    const usedElsewhere = slots
      .filter(s => s.key !== slot.key)
      .map(s => picks.podium[s.key])
      .filter(Boolean);

    const row = document.createElement('div');
    row.className = 'podium-row';

    const label = document.createElement('label');
    label.className = 'podium-label';
    label.textContent = slot.label;

    const select = document.createElement('select');
    select.className = 'podium-select';
    const empty = document.createElement('option');
    empty.value = '';
    empty.textContent = '— choose country —';
    select.appendChild(empty);
    sortedTeams.forEach(team => {
      const opt = document.createElement('option');
      opt.value = team;
      opt.textContent = `${FLAG[team] || ''} ${team}`;
      opt.disabled = usedElsewhere.includes(team);
      select.appendChild(opt);
    });
    select.value = currentTeam || '';

    const display = document.createElement('span');
    display.className = 'podium-flag';
    display.innerHTML = currentTeam ? (FLAG[currentTeam] || '🏳️') : '';

    select.addEventListener('change', () => {
      picks.podium[slot.key] = select.value || null;
      if (slot.key === 'first') {
        picks.champion = picks.podium.first;
        refreshChampionCard('manualChampionCard');
      }
      renderPodiumPicker();
    });

    row.appendChild(label);
    row.appendChild(select);
    row.appendChild(display);
    container.appendChild(row);
  });
  polyfillEmoji();
}

function buildGroupCard(group) {
  const gp  = picks.groups[group.name] || {};
  const pos = name => gp.first===name ? 1 : gp.second===name ? 2 : gp.third===name ? 3 : 0;

  const card = document.createElement('div');
  card.className = 'group-card';
  card.innerHTML = `<div class="group-header">Group ${group.name}<span class="group-header-pts">3·2·1</span></div>`;

  group.teams.forEach(([flag, name]) => {
    const p   = pos(name);
    const cls = p===1?'first':p===2?'second':p===3?'third':'';
    const lbl = p===1?'1st':p===2?'2nd':p===3?'3rd':'·';
    const badgeCls = p===1?'pos-1':p===2?'pos-2':p===3?'pos-3':'pos-blank';
    const row = document.createElement('div');
    row.className = `team-item${cls?' '+cls:''}`;
    row.innerHTML = `
      <span class="team-flag">${flag}</span>
      <span class="team-name-text">${name}</span>
      <span class="pos-badge ${badgeCls}">${lbl}</span>
    `;
    row.addEventListener('click', () => cycleGroupPick(group.name, name));
    card.appendChild(row);
  });
  return card;
}

function cycleGroupPick(group, team) {
  if (!picks.groups[group]) picks.groups[group] = {};
  const g = picks.groups[group];

  if (g.first === team)       { g.first  = null; }
  else if (g.second === team) { g.second = null; }
  else if (g.third === team)  { removeFromThirdsRanking(team); g.third = null; }
  else if (!g.first)          { g.first  = team; }
  else if (!g.second)         { g.second = team; }
  else if (!g.third)          { g.third  = team; syncThirdsRanking(); }
  else {
    removeFromThirdsRanking(g.third);
    g.third = team;
    syncThirdsRanking();
  }

  invalidateKoIfGroupsChanged();
  if (currentMode === 'manual') renderGroups();
  if (currentMode === 'simple') renderWizard();
}

function invalidateKoIfGroupsChanged() {
  // No-op for now — KO picks remain by name, scoring matches name regardless.
}

// ── Thirds ranking helpers ─────────────────────────────────────────────────
function syncThirdsRanking() {
  const allThirds = GROUPS.map(g => (picks.groups[g.name]||{}).third).filter(Boolean);
  const valid     = (picks.thirds_ranking||[]).filter(t => allThirds.includes(t));
  const newOnes   = allThirds.filter(t => !valid.includes(t));
  picks.thirds_ranking = [...valid, ...newOnes];
}

function removeFromThirdsRanking(team) {
  picks.thirds_ranking = (picks.thirds_ranking||[]).filter(t => t !== team);
}

// ── Thirds pane ───────────────────────────────────────────────────────────────
function renderThirdsRanking() {
  syncThirdsRanking();
  const container = qs('thirdsContainer');
  if (!container) return;
  container.innerHTML = '';
  container.appendChild(buildThirdsList());
  polyfillEmoji();
}

function buildThirdsList() {
  const wrap = document.createElement('div');
  const thirds = picks.thirds_ranking;
  const totalPicked = GROUPS.filter(g => (picks.groups[g.name]||{}).third).length;

  if (totalPicked === 0) {
    const empty = document.createElement('div');
    empty.className = 'thirds-empty';
    empty.textContent = 'Pick 3rd-place teams in the Groups first — they\'ll appear here for ranking.';
    wrap.appendChild(empty);
    return wrap;
  }

  thirds.forEach((team, idx) => {
    const isTop8 = idx < 8;

    if (idx === 8) {
      const divider = document.createElement('div');
      divider.className = 'third-divider';
      divider.textContent = '── Below: do not advance ──';
      wrap.appendChild(divider);
    }

    const item = document.createElement('div');
    item.className = 'third-item';
    item.draggable = true;
    item.dataset.dragIdx = idx;
    item.innerHTML = `
      <div class="third-drag-handle" title="Drag to reorder">⠿</div>
      <div class="third-rank${isTop8?' top8':''}">${idx+1}</div>
      <div class="third-flag">${FLAG[team]||'🏳️'}</div>
      <div class="third-name">${team}</div>
      <div class="third-btns">
        <button class="rank-btn" data-idx="${idx}" data-dir="-1" ${idx===0?'disabled':''}>▲</button>
        <button class="rank-btn" data-idx="${idx}" data-dir="1"  ${idx===thirds.length-1?'disabled':''}>▼</button>
      </div>
    `;
    wrap.appendChild(item);
  });

  const hint = document.createElement('div');
  hint.className = 'thirds-hint';
  hint.textContent = 'Tip: drag any row to reorder, or use the ▲ ▼ buttons.';
  wrap.appendChild(hint);

  if (totalPicked < 12) {
    const note = document.createElement('div');
    note.className = 'thirds-note';
    note.textContent = `${12-totalPicked} group(s) still need a 3rd-place pick.`;
    wrap.appendChild(note);
  }

  wrap.querySelectorAll('.rank-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const idx = parseInt(btn.dataset.idx);
      const dir = parseInt(btn.dataset.dir);
      moveThird(idx, dir);
    });
  });

  wrap.querySelectorAll('.third-item').forEach(el => {
    el.addEventListener('dragstart', onThirdDragStart);
    el.addEventListener('dragover', onThirdDragOver);
    el.addEventListener('dragleave', onThirdDragLeave);
    el.addEventListener('drop', onThirdDrop);
    el.addEventListener('dragend', onThirdDragEnd);
  });
  return wrap;
}

function onThirdDragStart(e) {
  dragSourceIdx = parseInt(this.dataset.dragIdx);
  this.classList.add('dragging');
  if (e.dataTransfer) {
    e.dataTransfer.effectAllowed = 'move';
    try { e.dataTransfer.setData('text/plain', String(dragSourceIdx)); } catch {}
  }
}
function onThirdDragOver(e) {
  e.preventDefault();
  if (e.dataTransfer) e.dataTransfer.dropEffect = 'move';
  this.classList.add('drag-over');
}
function onThirdDragLeave() {
  this.classList.remove('drag-over');
}
function onThirdDrop(e) {
  e.preventDefault();
  this.classList.remove('drag-over');
  const targetIdx = parseInt(this.dataset.dragIdx);
  if (dragSourceIdx === null || Number.isNaN(targetIdx) || dragSourceIdx === targetIdx) return;
  const list = picks.thirds_ranking;
  if (dragSourceIdx < 0 || dragSourceIdx >= list.length) return;
  const [moved] = list.splice(dragSourceIdx, 1);
  list.splice(targetIdx, 0, moved);
  if (currentMode === 'manual') renderThirdsRanking();
  if (currentMode === 'simple') renderWizard();
}
function onThirdDragEnd() {
  document.querySelectorAll('.third-item').forEach(el => {
    el.classList.remove('dragging', 'drag-over');
  });
  dragSourceIdx = null;
}

function moveThird(idx, dir) {
  const t = picks.thirds_ranking;
  const n = idx + dir;
  if (n < 0 || n >= t.length) return;
  [t[idx], t[n]] = [t[n], t[idx]];
  if (currentMode === 'manual') renderThirdsRanking();
  if (currentMode === 'simple') renderWizard();
}

// ── KO bracket ────────────────────────────────────────────────────────────────

function resolveGroupTeam(group, pos) {
  const key = pos===1?'first':pos===2?'second':'third';
  const actual = actualResults && actualResults.groups && actualResults.groups[group];
  if (actual && actual[key]) return actual[key];
  const gp  = picks.groups[group] || {};
  return gp[key] || null;
}

function resolveThird(rank) {
  const actualList = actualResults && actualResults.thirds_advancing;
  if (Array.isArray(actualList) && actualList[rank - 1]) return actualList[rank - 1];
  return (picks.thirds_ranking||[])[rank-1] || null;
}

function resolveKOWinner(round, matchIdx) {
  const actual = actualResults && actualResults.ko && actualResults.ko[round]
    && actualResults.ko[round][matchIdx] && actualResults.ko[round][matchIdx].winner;
  if (actual) return actual;
  return ((picks.ko[round]||{})[matchIdx]||{}).winner || null;
}

async function fetchActualResults() {
  try {
    const res = await fetch('/api/results');
    const data = await res.json();
    if (data && data.ok && data.has_results && data.results && typeof data.results === 'object') {
      actualResults = data.results;
    } else {
      actualResults = null;
    }
  } catch {
    actualResults = null;
  }
}

function resolveSlot(slotDef) {
  if (slotDef.type === 'group') return resolveGroupTeam(slotDef.group, slotDef.pos);
  if (slotDef.type === 'third') return resolveThird(slotDef.rank);
  return null;
}

function getTeam(round, matchIdx, side) {
  if (round === 'r32') {
    const slot = side==='home' ? R32[matchIdx].home : R32[matchIdx].away;
    return resolveSlot(slot);
  }
  const roundDef = KO_ROUNDS.find(r => r.id === round);
  const prevMatchIdx = roundDef.pairs[matchIdx][side==='home'?0:1];
  return resolveKOWinner(roundDef.prevRound, prevMatchIdx);
}

function getPlaceholder(round, matchIdx, side) {
  if (round === 'r32') {
    const slot = side==='home' ? R32[matchIdx].home : R32[matchIdx].away;
    if (slot.type === 'group') {
      const p = slot.pos===1?'1st':slot.pos===2?'2nd':'3rd';
      return `Group ${slot.group} ${p}`;
    }
    return `3rd Place #${slot.rank}`;
  }
  const roundDef = KO_ROUNDS.find(r => r.id === round);
  const prevMatchIdx = roundDef.pairs[matchIdx][side==='home'?0:1];
  return `Winner M${prevMatchIdx+1}`;
}

function renderKO() {
  const container = qs('koContainer');
  if (!container) return;
  container.innerHTML = '';

  KO_ROUNDS.forEach(roundDef => {
    const col = document.createElement('div');
    col.className = 'ko-col';
    col.innerHTML = `<div class="ko-col-title">${roundDef.label}<span class="ko-pts-tag">${roundDef.pts}pts</span></div>`;
    for (let i = 0; i < roundDef.count; i++) {
      col.appendChild(buildKoMatchCard(roundDef.id, i));
    }
    container.appendChild(col);
  });

  wireKoCard(container);
  polyfillEmoji();
}

function buildKoMatchCard(roundId, matchIdx) {
  const matchPick  = (picks.ko[roundId]||{})[matchIdx] || {};
  const homeTeam   = getTeam(roundId, matchIdx, 'home');
  const awayTeam   = getTeam(roundId, matchIdx, 'away');
  const homeLabel  = homeTeam || getPlaceholder(roundId, matchIdx, 'home');
  const awayLabel  = awayTeam || getPlaceholder(roundId, matchIdx, 'away');
  const homeFlag   = homeTeam ? (FLAG[homeTeam]||'🏳️') : '🏳️';
  const awayFlag   = awayTeam ? (FLAG[awayTeam]||'🏳️') : '🏳️';
  const winner     = matchPick.winner || null;
  const homeScore  = matchPick.homeScore ?? '';
  const awayScore  = matchPick.awayScore ?? '';
  const homePicked = winner && winner === homeTeam;
  const awayPicked = winner && winner === awayTeam;
  const unlocked   = koIsUnlocked(roundId, matchIdx);

  const matchup = document.createElement('div');
  matchup.className = 'ko-matchup' + (unlocked ? '' : ' locked');

  if (!unlocked) {
    const unlockISO = koUnlockAt(roundId, matchIdx).toISOString();
    matchup.innerHTML = `
      <div class="ko-team locked tbd">
        <span class="ko-flag">${homeFlag}</span>
        <span class="ko-name">${homeLabel}</span>
      </div>
      <div class="ko-lock-banner">🔒 Opens ${formatKickoff(unlockISO)}</div>
      <div class="ko-team locked tbd">
        <span class="ko-flag">${awayFlag}</span>
        <span class="ko-name">${awayLabel}</span>
      </div>
    `;
    return matchup;
  }

  const homeTbd = !homeTeam;
  const awayTbd = !awayTeam;

  matchup.innerHTML = `
    <div class="ko-team ${homePicked?'picked':''} ${homeTbd?'tbd':''}"
         data-round="${roundId}" data-match="${matchIdx}" data-side="home">
      <span class="ko-flag">${homeFlag}</span>
      <span class="ko-name">${homeLabel}</span>
      ${homePicked?'<span class="ko-check">✓</span>':''}
    </div>
    <div class="score-row">
      <input class="score-input" type="number" min="0" max="30" placeholder="-"
        value="${homeScore}"
        data-round="${roundId}" data-match="${matchIdx}" data-score="home">
      <span class="score-sep">:</span>
      <input class="score-input" type="number" min="0" max="30" placeholder="-"
        value="${awayScore}"
        data-round="${roundId}" data-match="${matchIdx}" data-score="away">
    </div>
    <div class="ko-team ${awayPicked?'picked':''} ${awayTbd?'tbd':''}"
         data-round="${roundId}" data-match="${matchIdx}" data-side="away">
      <span class="ko-flag">${awayFlag}</span>
      <span class="ko-name">${awayLabel}</span>
      ${awayPicked?'<span class="ko-check">✓</span>':''}
    </div>
  `;
  return matchup;
}

function wireKoCard(container) {
  container.querySelectorAll('.ko-team').forEach(el => {
    if (el.classList.contains('tbd')) return;
    el.addEventListener('click', () => {
      pickKOWinner(el.dataset.round, parseInt(el.dataset.match), el.dataset.side);
    });
  });
  container.querySelectorAll('.score-input').forEach(el => {
    el.addEventListener('click', e => e.stopPropagation());
    el.addEventListener('change', () => {
      setKOScore(el.dataset.round, parseInt(el.dataset.match), el.dataset.score, el.value);
    });
  });
}

function pickKOWinner(round, matchIdx, side) {
  if (!koIsUnlocked(round, matchIdx)) {
    showMessage(`Locked until ${formatKickoff(koUnlockAt(round, matchIdx).toISOString())}`, true);
    return;
  }
  const team = getTeam(round, matchIdx, side);
  if (!team) { showMessage('Complete the previous round first', true); return; }

  if (!picks.ko[round]) picks.ko[round] = {};
  if (!picks.ko[round][matchIdx]) picks.ko[round][matchIdx] = {};

  const current = picks.ko[round][matchIdx].winner;
  if (current === team) {
    picks.ko[round][matchIdx].winner = null;
    invalidateDownstream(round, matchIdx);
  } else {
    picks.ko[round][matchIdx].winner = team;
    invalidateDownstream(round, matchIdx);
  }

  if (currentMode === 'manual') renderKO();
  if (currentMode === 'simple') renderWizard();
}

function invalidateDownstream(round, matchIdx) {
  const nextRound = ROUND_ORDER[ROUND_ORDER.indexOf(round) + 1];
  if (!nextRound || !PAIRS_MAP[nextRound]) return;

  PAIRS_MAP[nextRound].forEach((pair, nextMatchIdx) => {
    if (pair[0] === matchIdx || pair[1] === matchIdx) {
      if (picks.ko[nextRound]?.[nextMatchIdx]) {
        delete picks.ko[nextRound][nextMatchIdx];
      }
      invalidateDownstream(nextRound, nextMatchIdx);
    }
  });
}

function setKOScore(round, matchIdx, scoreType, value) {
  if (!picks.ko[round]) picks.ko[round] = {};
  if (!picks.ko[round][matchIdx]) picks.ko[round][matchIdx] = {};
  const val = value === '' ? null : parseInt(value, 10);
  if (val !== null && (Number.isNaN(val) || val < 0 || val > 30)) {
    picks.ko[round][matchIdx][scoreType === 'home' ? 'homeScore' : 'awayScore'] = null;
    showMessage('Scores must be between 0 and 30', true);
    if (currentMode === 'manual') renderKO();
    if (currentMode === 'simple') renderWizard();
    return;
  }
  picks.ko[round][matchIdx][scoreType === 'home' ? 'homeScore' : 'awayScore'] = val;
}

// ── Wizard (Easy mode) ────────────────────────────────────────────────────────
function allTeams() {
  return GROUPS.flatMap(group => group.teams.map(([, name]) => name));
}

function renderWizard() {
  const step = WIZARD_STEPS[wizardIdx];
  const total = WIZARD_STEPS.length;
  qs('wizardStepCounter').textContent = `Step ${wizardIdx + 1} of ${total}`;
  qs('wizardTitle').innerHTML = step.title;
  qs('wizardProgressFill').style.width = `${((wizardIdx + 1) / total) * 100}%`;
  qs('wizardBack').disabled = wizardIdx === 0;
  qs('wizardNext').disabled = !stepIsComplete(step) && step.kind !== 'review';
  qs('wizardNext').textContent = wizardIdx === total - 1 ? 'Save &amp; finish' : 'Next →';

  const body = qs('wizardContent');
  body.innerHTML = '';

  const helper = document.createElement('div');
  helper.className = 'wizard-help';
  helper.textContent = step.sub || '';
  body.appendChild(helper);

  if (step.kind === 'podium')       renderWizardPodium(body, step.slot);
  else if (step.kind === 'champion')renderWizardPodium(body, 'first');
  else if (step.kind === 'group')   renderWizardGroup(body, step.group);
  else if (step.kind === 'thirds')  renderWizardThirds(body);
  else if (step.kind === 'ko')      renderWizardKoRound(body, step.round);
  else if (step.kind === 'review')  renderWizardReview(body);

  polyfillEmoji();
}

const PODIUM_LABEL = { first: 'champion', second: 'runner-up', third: '3rd place' };

function renderWizardPodium(body, slot) {
  const grid = document.createElement('div');
  grid.className = 'champion-grid';
  const current = (picks.podium && picks.podium[slot]) || null;
  const usedElsewhere = new Set(
    ['first','second','third']
      .filter(s => s !== slot)
      .map(s => picks.podium && picks.podium[s])
      .filter(Boolean)
  );
  const sortedTeams = allTeams().slice().sort();
  sortedTeams.forEach(team => {
    const btn = document.createElement('button');
    const isCurrent = current === team;
    const isUsed = usedElsewhere.has(team) && !isCurrent;
    btn.className = 'champion-btn' + (isCurrent ? ' selected' : '') + (isUsed ? ' disabled' : '');
    btn.disabled = isUsed;
    btn.innerHTML = `<span class="champion-flag">${FLAG[team] || '🏳️'}</span><span class="champion-name">${team}</span>`;
    btn.addEventListener('click', () => {
      if (isUsed) return;
      picks.podium[slot] = team;
      if (slot === 'first') {
        picks.champion = team;
        refreshChampionCard('wizardChampionCard');
      }
      renderWizard();
    });
    grid.appendChild(btn);
  });
  body.appendChild(grid);

  const help = document.createElement('div');
  help.className = 'wizard-subtle';
  if (current) {
    help.textContent = `You picked ${current} for ${PODIUM_LABEL[slot]}. Each podium slot needs a different country.`;
  } else if (slot === 'first') {
    help.textContent = 'This also sets up your dashboard to show your champion\'s most recent match.';
  } else {
    help.textContent = `Pick the country you think finishes in ${PODIUM_LABEL[slot]}. Countries you've already used for another slot are disabled.`;
  }
  body.appendChild(help);
}

function renderWizardGroup(body, groupName) {
  const group = GROUPS.find(g => g.name === groupName);
  const card = buildGroupCard(group);
  card.classList.add('wizard-group-card');
  body.appendChild(card);

  const gp = picks.groups[groupName] || {};
  const tally = ['first','second','third'].filter(k => gp[k]).length;
  const status = document.createElement('div');
  status.className = 'wizard-subtle';
  const withFlag = t => t ? `${FLAG[t] || '🏳️'} ${t}` : '—';
  if (tally === 3) {
    status.innerHTML = `Locked in: 1) ${withFlag(gp.first)}  ·  2) ${withFlag(gp.second)}  ·  3) ${withFlag(gp.third)}`;
  } else {
    status.textContent = `Pick all three positions to continue (${tally}/3 done).`;
  }
  body.appendChild(status);
}

function renderWizardThirds(body) {
  const totalPicked = GROUPS.filter(g => (picks.groups[g.name] || {}).third).length;
  if (totalPicked < 12) {
    const warn = document.createElement('div');
    warn.className = 'wizard-warn';
    warn.textContent = `${12 - totalPicked} group(s) still need a 3rd-place pick. Use the Back button to finish them first.`;
    body.appendChild(warn);
    return;
  }
  body.appendChild(buildThirdsList());
}

function renderWizardKoRound(body, roundId) {
  const roundDef = KO_ROUNDS.find(r => r.id === roundId);
  const total = roundDef.count;
  let idx = (koCursor[roundId] ?? 0);
  if (idx < 0 || idx >= total) idx = 0;
  koCursor[roundId] = idx;

  const nav = document.createElement('div');
  nav.className = 'wizard-r32-nav';
  nav.innerHTML = `
    <button class="wizard-mini-btn" id="koPrev" ${idx === 0 ? 'disabled' : ''}>← Prev match</button>
    <div class="wizard-r32-counter">Match ${idx + 1} of ${total}</div>
    <button class="wizard-mini-btn" id="koNext" ${idx === total - 1 ? 'disabled' : ''}>Next match →</button>
  `;
  body.appendChild(nav);

  const kickoff = (KO_KICKOFFS[roundId] || [])[idx];
  const unlocked = koIsUnlocked(roundId, idx);
  const matchPicked = ((picks.ko[roundId] || {})[idx] || {}).winner;

  const meta = document.createElement('div');
  meta.className = 'wizard-r32-meta';
  meta.innerHTML = `
    <span class="wizard-r32-kickoff">Kick-off: ${kickoff ? formatKickoff(kickoff) : 'TBD'}</span>
    <span class="wizard-r32-status ${unlocked ? 'open' : 'locked'}">
      ${unlocked ? '🔓 Picks open' : `🔒 Opens ${formatKickoff(koUnlockAt(roundId, idx).toISOString())}`}
    </span>
  `;
  body.appendChild(meta);

  if (!unlocked) {
    const lock = document.createElement('div');
    lock.className = 'wizard-lock-card';
    lock.innerHTML = `
      <div class="lock-title">Picks unlock 72 hours before kickoff</div>
      <div class="lock-sub">
        The opponents in this ${roundDef.label} match depend on earlier results that aren't in yet.
        Come back closer to kickoff to lock in your pick.
      </div>
    `;
    body.appendChild(lock);
  } else {
    const card = buildKoMatchCard(roundId, idx);
    card.classList.add('wizard-ko-card', 'wizard-ko-card-solo');
    body.appendChild(card);
    wireKoCard(card);
  }

  let openCount = 0;
  let pickedCount = 0;
  for (let i = 0; i < total; i++) {
    if (koIsUnlocked(roundId, i)) openCount += 1;
    if (((picks.ko[roundId] || {})[i] || {}).winner) pickedCount += 1;
  }
  const summary = document.createElement('div');
  summary.className = 'wizard-r32-summary';
  summary.textContent = `${pickedCount} of ${total} matches picked · ${openCount} currently unlocked`;
  body.appendChild(summary);

  const note = document.createElement('div');
  note.className = 'wizard-subtle';
  note.innerHTML = '⚽ Enter the <strong>final score after penalties</strong> if the match goes to a shoot-out — the team that won on PKs gets the higher score.';
  body.appendChild(note);

  if (matchPicked && unlocked && idx < total - 1) {
    const nextBtn = document.createElement('button');
    nextBtn.className = 'wizard-mini-btn primary';
    nextBtn.textContent = 'Continue to next match →';
    nextBtn.style.marginTop = '8px';
    nextBtn.addEventListener('click', () => {
      koCursor[roundId] = idx + 1;
      renderWizard();
    });
    body.appendChild(nextBtn);
  }

  qs('koPrev').addEventListener('click', () => {
    koCursor[roundId] = Math.max(0, idx - 1);
    renderWizard();
  });
  qs('koNext').addEventListener('click', () => {
    koCursor[roundId] = Math.min(total - 1, idx + 1);
    renderWizard();
  });
}

function renderWizardReview(body) {
  const sections = [];

  const podiumRow = (slot, label) => {
    const t = picks.podium && picks.podium[slot];
    return `<div class="review-row"><strong>${label}:</strong> ${t ? `${FLAG[t] || '🏳️'} ${t}` : '<em>not picked</em>'}</div>`;
  };
  sections.push(`
    <div class="review-section">
      <div class="review-title">Podium prediction</div>
      ${podiumRow('first', '🥇 Champion')}
      ${podiumRow('second', '🥈 Runner-up')}
      ${podiumRow('third', '🥉 3rd place')}
    </div>
  `);

  const groupRows = GROUPS.map(g => {
    const gp = picks.groups[g.name] || {};
    const list = ['first','second','third']
      .map((k, idx) => gp[k] ? `${idx+1}) ${FLAG[gp[k]] || ''} ${gp[k]}` : `${idx+1}) —`)
      .join(' · ');
    return `<div class="review-row"><strong>Group ${g.name}</strong> ${list}</div>`;
  }).join('');
  sections.push(`<div class="review-section"><div class="review-title">Group placements</div>${groupRows}</div>`);

  const thirds = picks.thirds_ranking || [];
  const thirdsRows = thirds.length
    ? thirds.map((t,i) => `<div class="review-row">${i+1}) ${FLAG[t] || ''} ${t}${i===7?' <span class="review-line">— line</span>':''}</div>`).join('')
    : '<div class="review-row"><em>none ranked yet</em></div>';
  sections.push(`<div class="review-section"><div class="review-title">3rd-place ranking</div>${thirdsRows}</div>`);

  const withFlag = team => team ? `${FLAG[team] || '🏳️'} ${team}` : '—';
  KO_ROUNDS.forEach(round => {
    const rp = picks.ko[round.id] || {};
    const rows = [];
    for (let i = 0; i < round.count; i++) {
      const m = rp[i] || {};
      const home = withFlag(getTeam(round.id, i, 'home'));
      const away = withFlag(getTeam(round.id, i, 'away'));
      const winner = m.winner ? `${FLAG[m.winner] || '🏳️'} ${m.winner}` : '<em>no pick</em>';
      const score = (m.homeScore != null && m.awayScore != null) ? ` (${m.homeScore}–${m.awayScore})` : '';
      rows.push(`<div class="review-row">${home} vs ${away} → <strong>${winner}</strong>${score}</div>`);
    }
    sections.push(`<div class="review-section"><div class="review-title">${round.label}</div>${rows.join('')}</div>`);
  });

  body.innerHTML += sections.join('');
}

function moveWizard(delta) {
  if (delta === 1 && wizardIdx === WIZARD_STEPS.length - 1) {
    saveAndShowDone();
    return;
  }
  wizardIdx = Math.min(WIZARD_STEPS.length - 1, Math.max(0, wizardIdx + delta));
  // When entering any KO round, jump to the first unlocked, unpicked match for convenience.
  const step = WIZARD_STEPS[wizardIdx];
  if (step && step.kind === 'ko') {
    const roundId = step.round;
    const total = KO_ROUNDS.find(r => r.id === roundId).count;
    let landed = false;
    for (let i = 0; i < total; i++) {
      const picked = ((picks.ko[roundId] || {})[i] || {}).winner;
      if (koIsUnlocked(roundId, i) && !picked) { koCursor[roundId] = i; landed = true; break; }
    }
    if (!landed) {
      for (let i = 0; i < total; i++) {
        if (koIsUnlocked(roundId, i)) { koCursor[roundId] = i; landed = true; break; }
      }
    }
    if (!landed) koCursor[roundId] = 0;
  }
  window.scrollTo({ top: 0, behavior: 'smooth' });
  renderWizard();
}

async function saveAndShowDone() {
  await savePicks();
  showMessage('All picks saved');
}

async function wizardSaveAndPause() {
  await savePicks();
  showMessage('Saved — come back any time');
}

// ── Champion latest match card ────────────────────────────────────────────────
async function refreshChampionCard(targetId) {
  const el = qs(targetId);
  if (!el) return;
  if (!picks.champion) { el.style.display = 'none'; return; }

  const team = picks.champion;
  el.style.display = 'block';
  el.innerHTML = `
    <div class="champion-card-header">
      <span class="champion-flag-lg">${FLAG[team] || '🏳️'}</span>
      <div>
        <div class="champion-card-eyebrow">Your champion</div>
        <div class="champion-card-team">${team}</div>
      </div>
    </div>
    <div class="champion-card-body">Loading latest match…</div>
  `;
  polyfillEmoji();

  if (lastChampionRequested === team) {
    /* still refresh to keep it current */
  }
  lastChampionRequested = team;

  try {
    const res = await fetch(`/api/champion-latest?team=${encodeURIComponent(team)}`);
    const data = await res.json();
    const body = el.querySelector('.champion-card-body');
    if (!data.ok) {
      body.innerHTML = `<em>Couldn't reach the match-data API — try again later.</em>`;
      return;
    }
    if (!data.match) {
      body.innerHTML = `<em>No recent match data found for ${team}'s national team.</em>`;
      return;
    }
    const m = data.match;
    // Sanity check: if the API returned a match that doesn't involve the country, treat it as unmatched.
    const lc = s => (s || '').toLowerCase();
    const tc = lc(team);
    if (lc(m.home) !== tc && lc(m.away) !== tc &&
        lc(data.match.team_resolved) !== tc) {
      body.innerHTML = `<em>No recent national-team match data found for ${team}.</em>`;
      return;
    }
    const scoreText = (m.homeScore != null && m.awayScore != null) ? `${m.homeScore}–${m.awayScore}` : 'vs';
    const when = [m.date, m.time].filter(Boolean).join(' ');
    body.innerHTML = `
      <div class="champion-match">
        <div class="champion-match-when">${when || ''} · ${m.league || ''}</div>
        <div class="champion-match-teams">
          <strong>${m.home || '?'}</strong>
          <span class="champion-match-score">${scoreText}</span>
          <strong>${m.away || '?'}</strong>
        </div>
        ${m.venue ? `<div class="champion-match-venue">${m.venue}</div>` : ''}
      </div>
    `;
  } catch {
    const body = el.querySelector('.champion-card-body');
    if (body) body.innerHTML = '<em>Couldn\'t load latest match (network).</em>';
  }
  polyfillEmoji();
}

// ── Leaderboard ───────────────────────────────────────────────────────────────
async function renderLeaderboard() {
  const content = qs('lbContent');
  content.innerHTML = '<div class="lb-loading">Loading…</div>';

  try {
    const [lbRes, resultsRes] = await Promise.all([
      fetch('/api/leaderboard'),
      fetch('/api/results'),
    ]);
    const lb = await lbRes.json();
    const results = await resultsRes.json();

    // Keep the bracket renderers in sync with the latest official results.
    if (results && results.ok && results.has_results && results.results && typeof results.results === 'object') {
      actualResults = results.results;
    } else {
      actualResults = null;
    }

    let banner = '';
    if (results.ok && !results.has_results) {
      banner = '<div class="lb-banner">No results recorded yet — every score is currently 0 until matches are played.</div>';
    } else if (results.ok && results.updated_at) {
      banner = `<div class="lb-banner lb-banner-ok">Latest results refresh: ${results.updated_at}</div>`;
    }

    if (!lb.ok || !lb.entries || lb.entries.length === 0) {
      content.innerHTML = banner + '<div class="lb-empty">No entries yet — make your picks and save.</div>';
      return;
    }

    let html = banner;
    lb.entries.forEach((entry, idx) => {
      const isYou    = entry.email === playerEmail;
      const initials = entry.name.split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2);
      const rankCls  = idx===0?'gold':idx===1?'silver':idx===2?'bronze':'';
      html += `
        <div class="lb-row${isYou?' lb-you-row':''}">
          <div class="lb-rank ${rankCls}">${idx+1}</div>
          <div class="lb-avatar">${initials}</div>
          <div class="lb-name">${entry.name}${isYou?'<span class="lb-you">you</span>':''}</div>
          <div class="lb-score-col">
            <div class="lb-pts-num">${entry.score}</div>
            <div class="lb-pts-lbl">pts</div>
          </div>
        </div>
      `;
    });
    content.innerHTML = html;
  } catch {
    content.innerHTML = '<div class="lb-empty">Could not load leaderboard.</div>';
  }
}

// ── Save ──────────────────────────────────────────────────────────────────────
async function savePicks() {
  if (!playerEmail) return;
  const btn = qs(currentMode === 'simple' ? 'simpleSaveButton' : 'saveButton');
  if (btn) btn.disabled = true;

  if (currentMode === 'manual') syncThirdsRanking();
  normalizePicks();

  try {
    const res  = await fetch('/api/save', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ email: playerEmail, name: playerName, picks }),
    });
    const data = await res.json();
    if (!res.ok || !data.ok) {
      showMessage(data.error || 'Save failed', true);
    } else {
      showMessage('Saved');
    }
  } catch {
    showMessage('Save failed — check your connection', true);
  } finally {
    if (btn) btn.disabled = false;
  }

  // Pull the latest actual results so the bracket reflects real teams once they're in.
  await fetchActualResults();
  if (currentMode === 'manual') {
    renderGroups();
    renderThirdsRanking();
    renderKO();
  } else if (currentMode === 'simple') {
    renderWizard();
  }
}

// ── Init ──────────────────────────────────────────────────────────────────────
function init() {
  qs('goButton').addEventListener('click', submitIdentity);
  ['emailInput','nameInput'].forEach(id => {
    qs(id).addEventListener('keydown', e => { if (e.key === 'Enter') submitIdentity(); });
  });

  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => showTab(btn.dataset.tab, btn));
  });

  qs('simpleModeButton').addEventListener('click', startSimpleMode);
  qs('manualModeButton').addEventListener('click', startManualMode);
  qs('manualModeBackButton').addEventListener('click', showModeChooser);
  qs('simpleModeBackButton').addEventListener('click', showModeChooser);
  qs('saveButton').addEventListener('click', savePicks);
  qs('simpleSaveButton').addEventListener('click', savePicks);
  qs('refreshLeaderboard').addEventListener('click', renderLeaderboard);

  qs('wizardBack').addEventListener('click', () => moveWizard(-1));
  qs('wizardNext').addEventListener('click', () => moveWizard(1));
  qs('wizardSaveAndExit').addEventListener('click', wizardSaveAndPause);

  // Render flags on initial load — Twemoji may not be ready yet, so try a few times.
  polyfillEmoji();
  setTimeout(polyfillEmoji, 200);
  setTimeout(polyfillEmoji, 1000);
  window.addEventListener('load', polyfillEmoji);
}

init();
