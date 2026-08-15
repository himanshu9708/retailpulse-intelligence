// E-Commerce Executive Dashboard — client-side app
// Works entirely off the pre-aggregated DATA object embedded in the HTML
// (see python/export_dashboard_data.py). No server, no fetch — opens
// directly as a local file.

const COLORS = ['#1FA2A6', '#10243E', '#E8A33D', '#C4544A', '#3C9D6B', '#6C5CE7', '#0984E3', '#B8860B'];
const fmtUSD = n => '$' + Number(n).toLocaleString('en-US', {maximumFractionDigits: 0});
const fmtUSD2 = n => '$' + Number(n).toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2});
const fmtNum = n => Number(n).toLocaleString('en-US');
const fmtPct = n => Number(n).toFixed(2) + '%';

let charts = {};
function renderChart(id, config) {
  if (charts[id]) charts[id].destroy();
  charts[id] = new Chart(document.getElementById(id).getContext('2d'), config);
}

// ---------------------------------------------------------------------
// Filter state. Country/Category/Channel are mutually exclusive (the
// underlying data is only pre-aggregated in 2D: month x category,
// month x country, month x channel — combining two of these at once
// isn't supported by the exported data without shipping full
// transaction-grain rows to the browser). Year combines with any one.
// ---------------------------------------------------------------------
const state = { year: 'all', country: 'all', category: 'all', channel: 'all' };

function populateFilterOptions() {
  const years = [...new Set(DATA.monthly_overall.map(r => r.year_month.slice(0, 4)))].sort();
  const countries = [...new Set(DATA.monthly_country.map(r => r.country))].sort();
  const categories = [...new Set(DATA.monthly_category.map(r => r.category))].sort();
  const channels = [...new Set(DATA.monthly_channel.map(r => r.channel))].sort();

  const fill = (selectId, values) => {
    const sel = document.getElementById(selectId);
    values.forEach(v => {
      const opt = document.createElement('option');
      opt.value = v; opt.textContent = v;
      sel.appendChild(opt);
    });
  };
  fill('filterYear', years);
  fill('filterCountry', countries);
  fill('filterCategory', categories);
  fill('filterChannel', channels);
}

function activeDimFilter() {
  // Returns {dim, value} for whichever of country/category/channel is active, or null.
  if (state.country !== 'all') return {dim: 'country', value: state.country};
  if (state.category !== 'all') return {dim: 'category', value: state.category};
  if (state.channel !== 'all') return {dim: 'channel', value: state.channel};
  return null;
}

function scopeLabel() {
  const parts = [];
  if (state.year !== 'all') parts.push('Year ' + state.year);
  const dim = activeDimFilter();
  if (dim) parts.push(dim.dim.charAt(0).toUpperCase() + dim.dim.slice(1) + ' = ' + dim.value);
  return parts.length ? parts.join(' · ') : 'All Data';
}

// Filtered monthly_overall-equivalent rows: revenue/orders aggregated
// according to current filters. If a dimension filter is active, source
// from that dimension's table (already also filterable by year); if not,
// source from monthly_overall directly (which alone carries distinct
// customer counts and units).
function filteredMonthly() {
  const dim = activeDimFilter();
  let rows;
  if (!dim) {
    rows = DATA.monthly_overall;
  } else if (dim.dim === 'country') {
    rows = DATA.monthly_country.filter(r => r.country === dim.value)
      .map(r => ({year_month: r.year_month, revenue: r.revenue, orders: r.orders}));
  } else if (dim.dim === 'category') {
    rows = DATA.monthly_category.filter(r => r.category === dim.value)
      .map(r => ({year_month: r.year_month, revenue: r.revenue, orders: null, units: r.units}));
  } else {
    rows = DATA.monthly_channel.filter(r => r.channel === dim.value)
      .map(r => ({year_month: r.year_month, revenue: r.revenue, orders: r.orders}));
  }
  if (state.year !== 'all') rows = rows.filter(r => r.year_month.startsWith(state.year));
  return rows;
}

function sumBy(rows, key) {
  return rows.reduce((acc, r) => acc + (r[key] || 0), 0);
}

// ---------------------------------------------------------------------
// KPI row builder
// ---------------------------------------------------------------------
function kpiCard(label, value, opts = {}) {
  const deltaHtml = opts.delta !== undefined
    ? `<div class="delta ${opts.delta >= 0 ? 'up' : 'down'}">${opts.delta >= 0 ? '▲' : '▼'} ${Math.abs(opts.delta).toFixed(2)}%</div>`
    : '';
  return `<div class="kpi ${opts.warn ? 'warn' : ''}">
    <div class="label">${label}</div>
    <div class="value">${value}</div>
    ${deltaHtml}
  </div>`;
}

function renderOverviewKPIs() {
  const rows = filteredMonthly();
  const revenue = sumBy(rows, 'revenue');
  const orders = state.channel !== 'all' || state.country !== 'all'
    ? sumBy(rows, 'orders')
    : (state.year === 'all' && !activeDimFilter() ? DATA.kpi_summary.orders : sumBy(rows, 'orders'));
  const aov = orders ? revenue / orders : null;

  let growthHtml = '';
  if (state.year !== 'all' && !activeDimFilter()) {
    const yr = DATA.yearly_revenue_growth.find(r => String(r.year) === state.year);
    if (yr && yr.yoy_growth_pct !== null) growthHtml = kpiCard('Revenue YoY Growth', fmtPct(yr.yoy_growth_pct), {delta: yr.yoy_growth_pct});
  }

  const el = document.getElementById('ov-kpis');
  el.innerHTML =
    kpiCard('Total Revenue', fmtUSD(revenue)) +
    (orders ? kpiCard('Total Orders', fmtNum(orders)) : '') +
    (state.year === 'all' && !activeDimFilter() ? kpiCard('Total Customers', fmtNum(DATA.kpi_summary.customers)) : '') +
    (aov ? kpiCard('Avg Order Value', fmtUSD2(aov)) : '') +
    (growthHtml || (state.year === 'all' && !activeDimFilter() ? kpiCard('Repeat Purchase Rate', fmtPct(100 * DATA.repeat_vs_onetime.find(r => r.customer_type === 'Repeat').customers / DATA.kpi_summary.customers)) : ''));
}

// ---------------------------------------------------------------------
// PAGE 1: Executive Overview
// ---------------------------------------------------------------------
function renderOverviewPage() {
  renderOverviewKPIs();

  const rows = filteredMonthly();
  const months = [...new Set(rows.map(r => r.year_month))].sort();
  const revByMonth = months.map(m => sumBy(rows.filter(r => r.year_month === m), 'revenue'));

  renderChart('ov-trend', {
    type: 'line',
    data: { labels: months, datasets: [{ label: 'Revenue (USD)', data: revByMonth, borderColor: COLORS[0], backgroundColor: COLORS[0] + '22', fill: true, tension: 0.25, pointRadius: 2 }] },
    options: { responsive: true, plugins: { legend: { display: false }, tooltip: { callbacks: { label: c => fmtUSD(c.parsed.y) } } }, scales: { y: { ticks: { callback: v => fmtUSD(v) } } } }
  });

  // Category breakdown, respecting Year filter (but showing all categories regardless of category filter, for context)
  let catRows = DATA.monthly_category;
  if (state.year !== 'all') catRows = catRows.filter(r => r.year_month.startsWith(state.year));
  const catTotals = {};
  catRows.forEach(r => { catTotals[r.category] = (catTotals[r.category] || 0) + r.revenue; });
  const catSorted = Object.entries(catTotals).sort((a, b) => b[1] - a[1]);
  renderChart('ov-category', {
    type: 'bar',
    data: { labels: catSorted.map(c => c[0]), datasets: [{ data: catSorted.map(c => c[1]), backgroundColor: COLORS[0] }] },
    options: { indexAxis: 'y', responsive: true, plugins: { legend: { display: false }, tooltip: { callbacks: { label: c => fmtUSD(c.parsed.x) } } }, scales: { x: { ticks: { callback: v => fmtUSD(v) } } } }
  });

  let countryRows = DATA.monthly_country;
  if (state.year !== 'all') countryRows = countryRows.filter(r => r.year_month.startsWith(state.year));
  const countryTotals = {};
  countryRows.forEach(r => { countryTotals[r.country] = (countryTotals[r.country] || 0) + r.revenue; });
  const countrySorted = Object.entries(countryTotals).sort((a, b) => b[1] - a[1]);
  renderChart('ov-country', {
    type: 'bar',
    data: { labels: countrySorted.map(c => c[0]), datasets: [{ data: countrySorted.map(c => c[1]), backgroundColor: COLORS[1] }] },
    options: { responsive: true, plugins: { legend: { display: false }, tooltip: { callbacks: { label: c => fmtUSD(c.parsed.y) } } }, scales: { y: { ticks: { callback: v => fmtUSD(v) } } } }
  });

  // Top products table — overall totals; only affected by Category filter (see note)
  let products = DATA.top_products;
  if (state.category !== 'all') products = products.filter(p => p.category === state.category);
  const tbl = document.getElementById('ov-topproducts');
  tbl.innerHTML = '<tr><th>Product</th><th>Category</th><th style="text-align:right">Revenue</th></tr>' +
    products.slice(0, 10).map(p => `<tr><td>${p.product}</td><td>${p.category}</td><td class="num">${fmtUSD(p.revenue)}</td></tr>`).join('');

  renderChart('ov-segments', {
    type: 'doughnut',
    data: { labels: DATA.rfm_segments.map(s => s.segment), datasets: [{ data: DATA.rfm_segments.map(s => s.customers), backgroundColor: COLORS }] },
    options: { responsive: true, plugins: { legend: { position: 'right', labels: { boxWidth: 10, font: { size: 10.5 } } } } }
  });
}

// ---------------------------------------------------------------------
// PAGE 2: Sales Performance
// ---------------------------------------------------------------------
function renderSalesPage() {
  const rows = filteredMonthly();
  const revenue = sumBy(rows, 'revenue');
  const el = document.getElementById('sp-kpis');
  el.innerHTML = kpiCard('Revenue (filtered)', fmtUSD(revenue)) + kpiCard('Total Units Sold', fmtNum(DATA.kpi_summary.units)) + kpiCard('Median-vs-Mean AOV Note', 'Mean ' + fmtUSD2(DATA.kpi_summary.aov), {warn: true});

  const months = [...new Set(rows.map(r => r.year_month))].sort();
  renderChart('sp-monthly', {
    type: 'bar',
    data: {
      labels: months,
      datasets: [
        { type: 'bar', label: 'Revenue', data: months.map(m => sumBy(rows.filter(r => r.year_month === m), 'revenue')), backgroundColor: COLORS[0], yAxisID: 'y' },
      ]
    },
    options: { responsive: true, plugins: { tooltip: { callbacks: { label: c => fmtUSD(c.parsed.y) } } }, scales: { y: { ticks: { callback: v => fmtUSD(v) } } } }
  });

  let catRows = DATA.monthly_category;
  if (state.year !== 'all') catRows = catRows.filter(r => r.year_month.startsWith(state.year));
  const catTotals = {};
  catRows.forEach(r => { catTotals[r.category] = (catTotals[r.category] || 0) + r.revenue; });
  const catSorted = Object.entries(catTotals).sort((a, b) => b[1] - a[1]);
  renderChart('sp-category', {
    type: 'bar',
    data: { labels: catSorted.map(c => c[0]), datasets: [{ data: catSorted.map(c => c[1]), backgroundColor: catSorted.map((c, i) => c[0] === state.category ? COLORS[2] : COLORS[0]) }] },
    options: {
      indexAxis: 'y', responsive: true, plugins: { legend: { display: false }, tooltip: { callbacks: { label: c => fmtUSD(c.parsed.x) } } },
      scales: { x: { ticks: { callback: v => fmtUSD(v) } } },
      onClick: (evt, elements) => {
        if (elements.length) {
          const label = catSorted[elements[0].index][0];
          document.getElementById('filterCategory').value = state.category === label ? 'all' : label;
          document.getElementById('filterCategory').dispatchEvent(new Event('change'));
        }
      }
    }
  });

  renderChart('sp-growth', {
    type: 'bar',
    data: {
      labels: DATA.yearly_revenue_growth.filter(r => r.yoy_growth_pct !== null).map(r => r.year),
      datasets: [{ data: DATA.yearly_revenue_growth.filter(r => r.yoy_growth_pct !== null).map(r => r.yoy_growth_pct), backgroundColor: DATA.yearly_revenue_growth.filter(r => r.yoy_growth_pct !== null).map(r => r.yoy_growth_pct >= 0 ? COLORS[4] : COLORS[3]) }]
    },
    options: { responsive: true, plugins: { legend: { display: false }, tooltip: { callbacks: { label: c => fmtPct(c.parsed.y) } } }, scales: { y: { ticks: { callback: v => v + '%' } } } }
  });

  let products = DATA.top_products;
  if (state.category !== 'all') products = products.filter(p => p.category === state.category);
  const tbl = document.getElementById('sp-products');
  tbl.innerHTML = '<tr><th>#</th><th>Product</th><th>Category</th><th style="text-align:right">Revenue</th><th style="text-align:right">Units</th></tr>' +
    products.map((p, i) => `<tr><td>${i + 1}</td><td>${p.product}</td><td>${p.category}</td><td class="num">${fmtUSD(p.revenue)}</td><td class="num">${fmtNum(p.units)}</td></tr>`).join('');
}

// ---------------------------------------------------------------------
// PAGE 3: Customer Intelligence
// ---------------------------------------------------------------------
function renderCustomerPage() {
  const totalCustomers = DATA.kpi_summary.customers;
  const repeat = DATA.repeat_vs_onetime.find(r => r.customer_type === 'Repeat');
  const onetime = DATA.repeat_vs_onetime.find(r => r.customer_type === 'One-time');

  document.getElementById('ci-kpis').innerHTML =
    kpiCard('Purchasing Customers', fmtNum(totalCustomers)) +
    kpiCard('Repeat Customers', fmtNum(repeat.customers)) +
    kpiCard('Repeat Purchase Rate', fmtPct(100 * repeat.customers / totalCustomers)) +
    kpiCard('Historical CLV (Avg Spend)', fmtUSD2(DATA.kpi_summary.revenue_per_customer));

  renderChart('ci-segments', {
    type: 'bar',
    data: { labels: DATA.rfm_segments.map(s => s.segment), datasets: [{ label: 'Customers', data: DATA.rfm_segments.map(s => s.customers), backgroundColor: COLORS[0] }] },
    options: { indexAxis: 'y', responsive: true, plugins: { legend: { display: false } } }
  });

  renderChart('ci-newcust', {
    type: 'bar',
    data: { labels: DATA.new_customers_per_year.map(r => r.year), datasets: [{ data: DATA.new_customers_per_year.map(r => r.new_customers), backgroundColor: COLORS[1] }] },
    options: { responsive: true, plugins: { legend: { display: false } } }
  });

  const totalRev = DATA.kpi_summary.revenue;
  const tbl = document.getElementById('ci-segtable');
  tbl.innerHTML = '<tr><th>Segment</th><th style="text-align:right">Customers</th><th style="text-align:right">% Customers</th><th style="text-align:right">Revenue</th><th style="text-align:right">% Revenue</th><th style="text-align:right">Avg Spend</th></tr>' +
    DATA.rfm_segments.map(s => `<tr><td>${s.segment}</td><td class="num">${fmtNum(s.customers)}</td><td class="num">${(100 * s.customers / totalCustomers).toFixed(2)}%</td><td class="num">${fmtUSD(s.revenue)}</td><td class="num">${(100 * s.revenue / totalRev).toFixed(2)}%</td><td class="num">${fmtUSD2(s.revenue / s.customers)}</td></tr>`).join('');
}

// ---------------------------------------------------------------------
// PAGE 4: Retention
// ---------------------------------------------------------------------
function renderRetentionPage() {
  const totalCustomers = DATA.kpi_summary.customers;
  const repeat = DATA.repeat_vs_onetime.find(r => r.customer_type === 'Repeat');
  const month1 = DATA.cohort_retention_curve.find(r => r.month === 1);

  document.getElementById('rt-kpis').innerHTML =
    kpiCard('Repeat Purchase Rate<br><span style="font-weight:400;font-size:10px;">(ever returned, any time)</span>', fmtPct(100 * repeat.customers / totalCustomers)) +
    kpiCard('Customer Retention — Cohort Month 1<br><span style="font-weight:400;font-size:10px;">(returned within 1 month)</span>', fmtPct(month1.avg_retention_pct), {warn: true});

  renderChart('rt-curve', {
    type: 'line',
    data: {
      labels: DATA.cohort_retention_curve.map(r => 'M' + r.month),
      datasets: [{ label: '% of cohort active', data: DATA.cohort_retention_curve.map(r => r.avg_retention_pct), borderColor: COLORS[0], backgroundColor: COLORS[0] + '22', fill: true, tension: 0.3, pointRadius: 3 }]
    },
    options: { responsive: true, plugins: { legend: { display: false }, tooltip: { callbacks: { label: c => c.parsed.y + '%' } } }, scales: { y: { beginAtZero: true, ticks: { callback: v => v + '%' } } } }
  });

  const atRiskSegs = ['At Risk', "Can't Lose Them", 'Lost', 'About To Sleep'];
  const rows = DATA.rfm_segments.filter(s => atRiskSegs.includes(s.segment));
  const totalRev = DATA.kpi_summary.revenue;
  document.getElementById('rt-atrisk').innerHTML = '<tr><th>Segment</th><th style="text-align:right">Customers</th><th style="text-align:right">Revenue at Stake</th><th style="text-align:right">% of Total Revenue</th></tr>' +
    rows.map(s => `<tr><td>${s.segment}</td><td class="num">${fmtNum(s.customers)}</td><td class="num">${fmtUSD(s.revenue)}</td><td class="num">${(100 * s.revenue / totalRev).toFixed(2)}%</td></tr>`).join('');
}

// ---------------------------------------------------------------------
// Navigation + filter wiring
// ---------------------------------------------------------------------
function renderAll() {
  document.getElementById('scopeChip').textContent = 'Showing: ' + scopeLabel();
  renderOverviewPage();
  renderSalesPage();
  renderCustomerPage();
  renderRetentionPage();
}

document.querySelectorAll('nav.tabs button').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('nav.tabs button').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById('page-' + btn.dataset.page).classList.add('active');
  });
});

['filterYear', 'filterCountry', 'filterCategory', 'filterChannel'].forEach(id => {
  document.getElementById(id).addEventListener('change', (e) => {
    const key = id.replace('filter', '').toLowerCase();
    state[key] = e.target.value;
    // Enforce mutual exclusivity among country/category/channel (see note in activeDimFilter)
    if (key !== 'year' && e.target.value !== 'all') {
      ['country', 'category', 'channel'].forEach(k => {
        if (k !== key) {
          state[k] = 'all';
          document.getElementById('filter' + k.charAt(0).toUpperCase() + k.slice(1)).value = 'all';
        }
      });
    }
    renderAll();
  });
});

document.getElementById('resetFilters').addEventListener('click', () => {
  state.year = state.country = state.category = state.channel = 'all';
  ['filterYear', 'filterCountry', 'filterCategory', 'filterChannel'].forEach(id => document.getElementById(id).value = 'all');
  renderAll();
});

populateFilterOptions();
renderAll();
