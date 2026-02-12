const quest = {
  stage: 1,
  xp: 0,
  badges: new Set(),
  county: null,
  state: null,
}

const stagePanel = document.getElementById('stagePanel')
const questPath = document.getElementById('questPath')
const xpValue = document.getElementById('xpValue')
const badgeList = document.getElementById('badgeList')

let map
let geojsonData = null
let geoLayer = null
let countyChart = null
let stateChart = null
let compareChart = null

const stageLabels = {
  1: 'County Scout',
  2: 'State Explorer',
  3: 'Challenge Mode',
  4: 'Civic Strategist',
}

function addXp(amount) {
  quest.xp += amount
  renderStatus()
}

function addBadge(label) {
  if (!quest.badges.has(label)) {
    quest.badges.add(label)
    renderStatus()
  }
}

function setStage(stage) {
  quest.stage = stage
  renderStatus()
}

function renderStatus() {
  xpValue.textContent = `${quest.xp} XP`
  badgeList.innerHTML = [...quest.badges].map((b) => `<span class="badge">${b}</span>`).join('')
  const chips = questPath.querySelectorAll('span[data-stage]')
  chips.forEach((chip) => {
    if (Number(chip.dataset.stage) === quest.stage) chip.classList.add('active')
    else chip.classList.remove('active')
  })
}

function ensureMap() {
  if (map) return
  map = L.map('map').setView([39.5, -98.35], 4)
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors',
  }).addTo(map)
}

async function loadGeoJSON() {
  if (geojsonData) return geojsonData
  const res = await fetch('/data/counties.geojson')
  geojsonData = await res.json()
  return geojsonData
}

async function highlightCounty(fips) {
  ensureMap()
  const gj = await loadGeoJSON()
  const target = String(fips).padStart(5, '0')

  const feature = gj.features.find((f) => {
    const p = f.properties || {}
    const id = String(p.GEOID || p.geoid || '').padStart(5, '0')
    return id === target
  })

  if (!feature) return
  if (geoLayer) map.removeLayer(geoLayer)

  geoLayer = L.geoJSON(feature, {
    style: {
      color: '#0f6d5c',
      weight: 3,
      fillColor: '#34d399',
      fillOpacity: 0.25,
    },
  }).addTo(map)

  map.fitBounds(geoLayer.getBounds(), { padding: [20, 20] })
}

function fmtNum(value) {
  const n = Number(value || 0)
  return n.toLocaleString(undefined, { maximumFractionDigits: 1 })
}

function renderStage1() {
  setStage(1)
  stagePanel.innerHTML = `
    <h2>Stage 1: County Scout</h2>
    <p class="stage-note">Type your county and unlock your first civic clue.</p>
    <div class="search-wrap">
      <input id="countySearch" type="text" placeholder="Type county name or FIPS..." autocomplete="off" />
      <ul id="countySuggestions" class="suggestions"></ul>
    </div>
    <div id="countyResult"></div>
  `

  const input = document.getElementById('countySearch')
  const suggestions = document.getElementById('countySuggestions')
  let timer

  input.addEventListener('input', (event) => {
    clearTimeout(timer)
    const q = event.target.value.trim()
    timer = setTimeout(() => loadSuggestions(q, suggestions), 200)
  })

  suggestions.addEventListener('click', async (event) => {
    const item = event.target.closest('li[data-fips]')
    if (!item) return
    const fips = item.dataset.fips
    const county = await fetchCounty(fips)
    if (!county) return

    quest.county = county
    quest.state = county.state
    addXp(20)
    addBadge('Home County Discovered')
    renderCountyPanel(county)
    highlightCounty(county.fips)
    suggestions.innerHTML = ''
  })
}

async function loadSuggestions(query, container) {
  if (!query) {
    container.innerHTML = ''
    return
  }

  const data = await fetch(`/api/search?q=${encodeURIComponent(query)}`).then((r) => r.json())
  container.innerHTML = data
    .map((d) => `<li data-fips="${d.fips}">${d.display} | ${d.urbanicity} | pop ${fmtNum(d.population)}</li>`)
    .join('')
}

async function fetchCounty(fips) {
  try {
    const res = await fetch(`/api/county/${fips}`)
    if (!res.ok) return null
    return await res.json()
  } catch (err) {
    return null
  }
}

function renderCountyPanel(data) {
  const container = document.getElementById('countyResult')
  if (!container) return

  container.innerHTML = `
    <div class="summary">
      <strong>Unlocked clue:</strong> ${data.name}, ${data.state} is <strong>${data.urbanicity}</strong>.
      It has a civic opportunity score of <strong>${fmtNum(data.score)}</strong> and ranks <strong>#${data.state_rank}</strong> in-state.
    </div>
    <div class="grid2" style="margin-top:10px;">
      <div class="card"><strong>Civic Score</strong><span>${fmtNum(data.score)}</span></div>
      <div class="card"><strong>National Percentile</strong><span>${fmtNum(data.national_percentile)}%</span></div>
      <div class="card"><strong>Population</strong><span>${fmtNum(data.population)}</span></div>
      <div class="card"><strong>Total Nonprofits</strong><span>${fmtNum(data.metrics.total_nonprofits)}</span></div>
    </div>
    <div class="callout">Why this matters: counties with similar population type (${data.urbanicity}) can still have very different civic opportunity access.</div>
    <canvas id="countyChart"></canvas>
    <div class="actions">
      <button id="toState" class="primary">Learn About My State</button>
      <button id="toChallenges" class="challenge">Jump to Challenge Mode</button>
    </div>
  `

  const labels = ['Membership', 'Volunteer', 'Events', 'Take Action']
  const values = [
    data.metrics.membership_sum,
    data.metrics.volunteer_sum,
    data.metrics.events_sum,
    data.metrics.take_action_sum,
  ]

  if (countyChart) countyChart.destroy()
  countyChart = new Chart(document.getElementById('countyChart'), {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: 'County totals',
        data: values,
        backgroundColor: ['#0ea5e9', '#10b981', '#f59e0b', '#ef4444'],
      }],
    },
    options: {
      plugins: { legend: { display: false } },
      scales: { y: { beginAtZero: true } },
    },
  })

  document.getElementById('toState').addEventListener('click', () => {
    addXp(10)
    renderStage2()
  })

  document.getElementById('toChallenges').addEventListener('click', () => {
    addXp(10)
    renderStage3Menu()
  })
}

async function renderStage2() {
  if (!quest.state) return
  setStage(2)

  const stateData = await fetch(`/api/state/${quest.state}`).then((r) => r.json())
  const s = stateData.summary

  stagePanel.innerHTML = `
    <h2>Stage 2: State Explorer</h2>
    <p class="stage-note">Now you're zooming out from county to state.</p>
    <div class="grid2">
      <div class="card"><strong>State</strong><span>${s.state}</span></div>
      <div class="card"><strong>Avg Civic Score</strong><span>${fmtNum(s.avg_score)}</span></div>
      <div class="card"><strong>Counties</strong><span>${fmtNum(s.county_count)}</span></div>
      <div class="card"><strong>Top County</strong><span>${s.top_county}</span></div>
    </div>
    <div class="summary">Interpretation: in ${s.state}, the largest civic opportunity profile can differ strongly by urban/suburban/rural group.</div>
    <canvas id="stateChart"></canvas>
    <div class="actions">
      <button id="toCompare" class="challenge">Start Challenge Mode</button>
      <button id="backCounty" class="secondary">Back to County</button>
    </div>
  `

  if (stateChart) stateChart.destroy()
  stateChart = new Chart(document.getElementById('stateChart'), {
    type: 'bar',
    data: {
      labels: ['Urban', 'Suburban', 'Rural'],
      datasets: [{
        label: `${s.state} avg civic score`,
        data: [s.urban_avg, s.suburban_avg, s.rural_avg],
        backgroundColor: ['#2563eb', '#d97706', '#16a34a'],
      }],
    },
    options: {
      plugins: { legend: { display: false } },
      scales: { y: { beginAtZero: true } },
    },
  })

  addXp(20)
  addBadge('State Decoder')

  document.getElementById('toCompare').addEventListener('click', renderStage3Menu)
  document.getElementById('backCounty').addEventListener('click', renderStage1)
}

function renderStage3Menu() {
  setStage(3)
  stagePanel.innerHTML = `
    <h2>Stage 3: Challenge Mode</h2>
    <p class="stage-note">Choose your mission.</p>
    <div class="actions">
      <button id="stateVsState" class="challenge">Compare State vs State</button>
      <button id="countyVsCounty" class="challenge">Compare County vs County</button>
      <button id="countyPeers" class="challenge">Compare County vs Similar Counties</button>
    </div>
    <div id="challengeArea"></div>
  `

  document.getElementById('stateVsState').addEventListener('click', renderStateComparison)
  document.getElementById('countyVsCounty').addEventListener('click', renderCountyComparison)
  document.getElementById('countyPeers').addEventListener('click', renderPeerComparison)
}

async function renderStateComparison() {
  const area = document.getElementById('challengeArea')
  const statePayload = await fetch('/api/states').then((r) => r.json())
  const states = statePayload.states || []
  const options = states.map((s) => `<option value="${s}">${s}</option>`).join('')

  area.innerHTML = `
    <div class="summary">State Challenge: compare your state to another state.</div>
    <div class="grid2" style="margin-top:10px;">
      <div>
        <strong>Your state</strong>
        <select id="stateA"><option value="${quest.state || ''}">${quest.state || 'Select'}</option>${options}</select>
      </div>
      <div>
        <strong>Other state</strong>
        <select id="stateB"><option value="">Select a state</option>${options}</select>
      </div>
    </div>
    <div class="actions"><button id="runStateCompare" class="primary">Run Comparison</button></div>
    <div id="stateCompareResult"></div>
  `

  document.getElementById('stateA').value = quest.state || ''

  document.getElementById('runStateCompare').addEventListener('click', async () => {
    const a = document.getElementById('stateA').value
    const b = document.getElementById('stateB').value
    if (!a || !b || a === b) return

    const data = await fetch(`/api/compare/state?state_a=${a}&state_b=${b}`).then((r) => r.json())
    const g = data.gaps

    document.getElementById('stateCompareResult').innerHTML = `
      <div class="callout">Biggest gap clue: urban difference is <strong>${fmtNum(g.urban_gap)}</strong> points; rural difference is <strong>${fmtNum(g.rural_gap)}</strong> points.</div>
      <canvas id="compareChart"></canvas>
      <div class="actions"><button id="finishQuest" class="primary">Finish Quest</button></div>
    `

    if (compareChart) compareChart.destroy()
    compareChart = new Chart(document.getElementById('compareChart'), {
      type: 'bar',
      data: {
        labels: ['Urban gap', 'Suburban gap', 'Rural gap', 'Overall gap'],
        datasets: [{
          label: `${a} minus ${b}`,
          data: [g.urban_gap, g.suburban_gap, g.rural_gap, g.avg_score_gap],
          backgroundColor: ['#1d4ed8', '#a16207', '#15803d', '#7c3aed'],
        }],
      },
      options: {
        scales: { y: { beginAtZero: true } },
      },
    })

    addXp(30)
    addBadge('Cross-State Challenger')

    document.getElementById('finishQuest').addEventListener('click', renderFinalStage)
  })
}

function renderCountyComparison() {
  const area = document.getElementById('challengeArea')
  if (!quest.county) {
    area.innerHTML = '<div class="callout">Pick your home county first in Stage 1.</div>'
    return
  }

  area.innerHTML = `
    <div class="summary">County Challenge: compare your county with another county.</div>
    <div class="search-wrap" style="margin-top:10px;">
      <input id="countyBSearch" type="text" placeholder="Type other county name or FIPS" autocomplete="off" />
      <ul id="countyBSuggestions" class="suggestions"></ul>
    </div>
    <div id="countyCompareResult"></div>
  `

  const input = document.getElementById('countyBSearch')
  const suggestions = document.getElementById('countyBSuggestions')
  let timer

  input.addEventListener('input', (event) => {
    clearTimeout(timer)
    const q = event.target.value.trim()
    timer = setTimeout(() => loadSuggestions(q, suggestions), 200)
  })

  suggestions.addEventListener('click', async (event) => {
    const item = event.target.closest('li[data-fips]')
    if (!item) return
    const other = await fetchCounty(item.dataset.fips)
    if (!other) return

    const base = quest.county
    const delta = (Number(base.score) - Number(other.score)).toFixed(2)

    document.getElementById('countyCompareResult').innerHTML = `
      <div class="grid2" style="margin-top:10px;">
        <div class="card"><strong>${base.name}, ${base.state}</strong><span>${fmtNum(base.score)}</span></div>
        <div class="card"><strong>${other.name}, ${other.state}</strong><span>${fmtNum(other.score)}</span></div>
      </div>
      <div class="callout">Comparison clue: score difference is <strong>${delta}</strong> points (${base.name} minus ${other.name}).</div>
      <div class="actions"><button id="finishQuest" class="primary">Finish Quest</button></div>
    `

    addXp(30)
    addBadge('County Duelist')
    document.getElementById('finishQuest').addEventListener('click', renderFinalStage)
  })
}

function renderPeerComparison() {
  const area = document.getElementById('challengeArea')
  if (!quest.county) {
    area.innerHTML = '<div class="callout">Pick your home county first in Stage 1.</div>'
    return
  }

  const peers = quest.county.peers || []
  if (!peers.length) {
    area.innerHTML = '<div class="callout">No similar-county peers were found in this state.</div>'
    return
  }

  const list = peers
    .slice(0, 5)
    .map((p, idx) => `<li>${idx + 1}. ${p.name}, ${p.state} (${p.urbanicity}) - score ${fmtNum(p.score)}</li>`)
    .join('')

  area.innerHTML = `
    <div class="summary">Peer Challenge: counties in your state with the same type (${quest.county.urbanicity}).</div>
    <ol>${list}</ol>
    <div class="callout">Interpretation clue: compare these peers to see whether your county over- or under-performs for its county type.</div>
    <div class="actions"><button id="finishQuest" class="primary">Finish Quest</button></div>
  `

  addXp(30)
  addBadge('Urban-Rural Analyst')
  document.getElementById('finishQuest').addEventListener('click', renderFinalStage)
}

function renderFinalStage() {
  setStage(4)
  const countyLine = quest.county
    ? `${quest.county.name}, ${quest.county.state} is ${quest.county.urbanicity} with civic score ${fmtNum(quest.county.score)}.`
    : 'No county chosen.'

  stagePanel.innerHTML = `
    <h2>Stage 4: Civic Strategist</h2>
    <p class="stage-note">Quest complete. Here is your learning summary.</p>
    <div class="summary">
      <p><strong>County insight:</strong> ${countyLine}</p>
      <p><strong>State explored:</strong> ${quest.state || 'N/A'}</p>
      <p><strong>Final XP:</strong> ${quest.xp}</p>
      <p><strong>Badges:</strong> ${[...quest.badges].join(', ') || 'None yet'}</p>
    </div>
    <div class="actions">
      <button id="restart" class="primary">Start New Quest</button>
    </div>
  `

  addBadge('Civic Strategist')

  document.getElementById('restart').addEventListener('click', () => {
    quest.stage = 1
    quest.xp = 0
    quest.badges = new Set()
    quest.county = null
    quest.state = null
    if (geoLayer && map) {
      map.removeLayer(geoLayer)
      geoLayer = null
    }
    renderStatus()
    renderStage1()
  })
}

function start() {
  ensureMap()
  renderStatus()
  renderStage1()
}

start()
