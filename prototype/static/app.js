const $ = id => document.getElementById(id)
const searchA = $('searchA')
const searchB = $('searchB')
const sugA = $('suggestionsA')
const sugB = $('suggestionsB')
const overviewA = $('overviewA')
const overviewB = $('overviewB')
let map, layerA, layerB, geojsonData, chartA, chartB
let currentA = null, currentB = null

async function loadGeoJSON(){
  if(geojsonData) return geojsonData
  try{
    const res = await fetch('/data/counties.geojson')
    geojsonData = await res.json()
    return geojsonData
  }catch(e){
    console.warn('Failed to load geojson', e)
    return null
  }
}

async function suggest(q, side){
  const sug = side==='A'?sugA:sugB
  if(!q) { sug.innerHTML = ''; return }
  const results = await fetch(`/api/search?q=${encodeURIComponent(q)}`).then(r=>r.json())
  sug.innerHTML = ''
  results.forEach(it=>{
    const li = document.createElement('li')
    li.textContent = `${it.display} (${it.population.toLocaleString()})`
    li.onclick = ()=> loadCounty(it.fips, side)
    sug.appendChild(li)
  })
}

let timerA, timerB
searchA.addEventListener('input', e=>{
  clearTimeout(timerA)
  timerA = setTimeout(()=> suggest(e.target.value.trim(), 'A'), 200)
})
searchB.addEventListener('input', e=>{
  clearTimeout(timerB)
  timerB = setTimeout(()=> suggest(e.target.value.trim(), 'B'), 200)
})

async function loadCounty(fips, side){
  const data = await fetch(`/api/county/${fips}`).then(r=>r.json())
  if(side==='A'){
    renderOverview(data, overviewA)
    renderChart(data, 'A')
    renderPolygon(data, 'A')
    currentA = data.fips
  }else{
    renderOverview(data, overviewB)
    renderChart(data, 'B')
    renderPolygon(data, 'B')
    currentB = data.fips
  }
}

function renderOverview(d, container){
  container.innerHTML = ''
  const cards = [
    {k:'population',t:'Population',v:d.population},
    {k:'civic_org_sum',t:'Civic Orgs',v:d.metrics.civic_org_sum},
    {k:'volunteer_sum',t:'Volunteer Index',v:d.metrics.volunteer_sum},
    {k:'events_sum',t:'Events',v:d.metrics.events_sum}
  ]
  cards.forEach(c=>{
    const el = document.createElement('div'); el.className='card'
    el.innerHTML = `<strong>${c.t}</strong><div>${(c.v||0).toLocaleString()}</div>`
    container.appendChild(el)
  })
}

function ensureMap(){
  if(map) return
  map = L.map('map').setView([39.5, -98.35], 4)
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{attribution:''}).addTo(map)
}

async function renderPolygon(d, side){
  ensureMap()
  const fips = d.fips
  const gj = await loadGeoJSON()
  if(!gj) return
  const feat = gj.features.find(f => {
    const p = f.properties || {}
    return (p.GEOID && String(p.GEOID).padStart(5,'0')===String(fips)) || (p.geoid && String(p.geoid).padStart(5,'0')===String(fips))
  })
  const styleA = {color:'#1f78b4', weight:2, fillOpacity:0.2}
  const styleB = {color:'#33a02c', weight:2, fillOpacity:0.2}
  // remove existing layer for side
  if(side==='A' && layerA){ map.removeLayer(layerA); layerA=null }
  if(side==='B' && layerB){ map.removeLayer(layerB); layerB=null }
  if(!feat) return
  // attach hover handlers to highlight
  const baseStyle = side==='A'?styleA:styleB
  function onEachFeature(feature, layer){
    layer.on('mouseover', function(){
      layer.setStyle({weight:5, fillOpacity:0.35})
      // if other side is same fips, highlight it too
      const other = side==='A'?layerB:layerA
      if(other && other.feature){
        const otherFips = (other.feature.properties.GEOID||other.feature.properties.geoid||'').toString().padStart(5,'0')
        const myFips = (feature.properties.GEOID||feature.properties.geoid||'').toString().padStart(5,'0')
        if(otherFips===myFips) other.setStyle({weight:5, fillOpacity:0.35})
      }
    })
    layer.on('mouseout', function(){
      layer.setStyle(baseStyle)
      const other = side==='A'?layerB:layerA
      if(other && other.feature){
        const otherFips = (other.feature.properties.GEOID||other.feature.properties.geoid||'').toString().padStart(5,'0')
        const myFips = (feature.properties.GEOID||feature.properties.geoid||'').toString().padStart(5,'0')
        if(otherFips===myFips) other.setStyle(side==='A'?styleB:styleA)
      }
    })
  }

  const layer = L.geoJSON(feat, {style: baseStyle, onEachFeature}).addTo(map)
  // fit to layer
  map.fitBounds(layer.getBounds(), {padding:[20,20]})
  if(side==='A') layerA = layer; else layerB = layer
}

function clearSide(side){
  if(side==='A'){
    if(layerA){ map.removeLayer(layerA); layerA=null }
    overviewA.innerHTML = ''
    if(chartA) { chartA.destroy(); chartA = null }
    currentA = null
    searchA.value = ''
    sugA.innerHTML = ''
  }else{
    if(layerB){ map.removeLayer(layerB); layerB=null }
    overviewB.innerHTML = ''
    if(chartB) { chartB.destroy(); chartB = null }
    currentB = null
    searchB.value = ''
    sugB.innerHTML = ''
  }
}

function swapSides(){
  // swap current fips and reload
  if(!currentA && !currentB) return
  const a = currentA, b = currentB
  if(a) loadCounty(a, 'B')
  if(b) loadCounty(b, 'A')
}

// wire up control buttons
document.addEventListener('DOMContentLoaded', ()=>{
  const btnA = document.getElementById('clearA')
  const btnB = document.getElementById('clearB')
  const btnSwap = document.getElementById('swap')
  if(btnA) btnA.addEventListener('click', ()=> clearSide('A'))
  if(btnB) btnB.addEventListener('click', ()=> clearSide('B'))
  if(btnSwap) btnSwap.addEventListener('click', swapSides)
})

function renderChart(d, side){
  const labels = d.org_types.map(x=>x.class)
  const data = d.org_types.map(x=>x.count)
  const ctx = side==='A'?$('orgChartA').getContext('2d'):$('orgChartB').getContext('2d')
  if(side==='A' && chartA) chartA.destroy()
  if(side==='B' && chartB) chartB.destroy()
  const cfg = {type:'bar', data:{labels, datasets:[{label:'Orgs',data,backgroundColor: side==='A'? '#1f78b4':'#33a02c'}]}}
  if(side==='A') chartA = new Chart(ctx, cfg)
  else chartB = new Chart(ctx, cfg)
}

// load geojson in background for snappy polygons
loadGeoJSON().catch(()=>{})
