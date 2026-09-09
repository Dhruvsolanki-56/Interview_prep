/* V14 — weekly benchmark, application cockpit, outcome calibration and privacy-thresholded process intelligence. */
let weeklyState={overview:null,cockpit:null,selectedApplicationId:null};

function fmtDelta(n){if(n==null)return '—';return `${n>0?'+':''}${n} pts`}
function evidenceTone(x){return x==='stronger'?'green':x==='developing'?'blue':x==='early'?'amber':''}

const _v14SetView=setView;
setView=function(v){
  _v14SetView(v);
  if(v==='weekly'){
    $('#pageEyebrow').textContent='WEEKLY BENCHMARK';$('#pageTitle').textContent='Application cockpit';renderWeekly();
  }
};

async function renderWeekly(){
  const root=$('#view-weekly');if(!root)return;
  root.innerHTML='<div class="card empty">Building your application cockpit…</div>';
  const cockpit=await api('/api/cockpit');weeklyState.cockpit=cockpit;
  const apps=cockpit.applications||[];
  if(!weeklyState.selectedApplicationId&&apps.length)weeklyState.selectedApplicationId=apps[0].application?.applicationId;
  const selected=apps.find(x=>x.application?.applicationId===weeklyState.selectedApplicationId)||apps[0];
  const w=selected?.weekly||await api('/api/weekly/overview');weeklyState.overview=w;
  root.innerHTML=`
    <div class="cockpit-top card">
      <div><div class="kicker">${esc(w.weekKey||'THIS WEEK')}</div><h2>${selected?`${esc(selected.application.roleTitle)} · ${esc(selected.application.companyName)}`:'Weekly interview benchmark'}</h2><p>${selected?.daysToInterview==null?'Build repeatable evidence instead of relying on one good mock.':selected.daysToInterview<0?'Interview date has passed. Update the application or record the outcome.':`${selected.daysToInterview} day${selected.daysToInterview===1?'':'s'} until the interview.`}</p></div>
      <div class="cockpit-switch">${apps.length>1?`<label>Target application<select onchange="selectCockpitApplication(this.value)">${apps.map(x=>`<option value="${esc(x.application.applicationId)}" ${x===selected?'selected':''}>${esc(x.application.companyName)} · ${esc(x.application.roleTitle)}</option>`).join('')}</select></label>`:''}<span class="badge ${w.benchmarkDue?'amber':'green'}">${w.benchmarkDue?'BENCHMARK DUE':'WEEK COMPLETE'}</span></div>
    </div>
    <div class="cockpit-grid">
      ${nextActionCard(w)}
      ${benchmarkCard(w)}
      ${calibrationCard(w.calibration||{})}
      ${evidenceCard(w.readinessConfidence||{})}
    </div>
    <div class="cockpit-two">
      <div class="card"><div class="section-head"><h3>Comeback queue</h3><span class="label">WHAT TO FIX NEXT</span></div>${renderComeback(w.comebackQueue||[])}</div>
      <div class="card"><div class="section-head"><h3>Study-plan execution</h3><span class="label">FOLLOW-THROUGH</span></div>${renderAdherence(w.adherence||{})}</div>
    </div>
    ${selected?renderCompanyEvidence(selected.companyIntelligence,cockpit.globalIntelligence):''}
    <div class="section-head"><h3>Weekly benchmark history</h3><span class="label">LOCKED COMPARABLE SESSIONS</span></div>
    <div class="card">${renderBenchmarkHistory(w.history||[])}</div>`;
}

window.selectCockpitApplication=function(id){weeklyState.selectedApplicationId=id;renderWeekly()};

function nextActionCard(w){const a=w.nextAction||{};return `<div class="card cockpit-card next"><div class="kicker">NEXT BEST ACTION</div><h3>${esc(a.title||'Take a mixed practice session')}</h3><p>${esc(a.why||'Keep building evidence across the interview loop.')}</p><div class="cockpit-card-foot"><span>${a.minutes||30} min</span><button class="btn primary" onclick="runNextAction('${esc(a.type||'mixed_practice')}','${esc(a.concept||'')}')">Do this now</button></div></div>`}
function benchmarkCard(w){const t=w.trend||{},b=w.currentBenchmark;return `<div class="card cockpit-card"><div class="kicker">WEEKLY BENCHMARK</div><div class="benchmark-score">${b?.completedAt?`${Math.round(b.score||0)}%`:'—'}</div><p>${b?.completedAt?`${esc(b.verdict||'')} · ${t.delta==null?'first locked benchmark':fmtDelta(t.delta)+' vs previous week'}`:'One comparable mixed interview per week. No hints, real-style scoring.'}</p><button class="btn ${w.benchmarkDue?'primary':''}" ${w.benchmarkDue?'':'disabled'} onclick="startWeeklyBenchmark()">${w.benchmarkDue?'Start this week’s benchmark':'Completed this week'}</button></div>`}
function calibrationCard(c){return `<div class="card cockpit-card"><div class="kicker">MOCK → REAL OUTCOME</div><div class="benchmark-score small">${c.samples||0}</div><p>${c.samples?`${esc(c.evidence||'insufficient')} evidence · ${c.passedAvg!=null?`passed-round mocks averaged ${c.passedAvg}%`:'more outcomes needed'}`:'Report real interview outcomes to calibrate your mocks against what actually happened.'}</p>${c.descriptiveBar!=null?`<div class="personal-bar"><span>Personal descriptive bar</span><b>${c.descriptiveBar}%</b></div>`:''}<small>${esc(c.note||'No predictive claim is made from sparse data.')}</small></div>`}
function evidenceCard(c){return `<div class="card cockpit-card"><div class="kicker">READINESS CONFIDENCE</div><div class="benchmark-score small">${c.score??0}%</div><p>${esc(c.label||'Low evidence')}</p><small>This is confidence in the amount of evidence behind your readiness score—not your chance of getting hired.</small></div>`}
function renderComeback(items){if(!items.length)return '<div class="empty-mini">Nothing urgent is due. Use the weekly benchmark or a mixed pressure drill.</div>';return `<div class="comeback-list">${items.map((x,i)=>`<div class="comeback-row"><span class="rank">${i+1}</span><div><b>${esc((x.concept||'practice').replaceAll('_',' '))}</b><small>${esc(x.reason||'')}</small></div><span class="badge">${esc(x.type)}</span></div>`).join('')}</div>`}
function renderAdherence(a){if(a.adherence==null)return '<div class="empty-mini">No due study-plan tasks yet.</div>';return `<div class="adherence-big">${a.adherence}%</div><div class="progress"><span style="width:${a.adherence}%"></span></div><div class="adherence-stats"><span><b>${a.completedDue||0}</b> completed</span><span><b>${a.overdue||0}</b> overdue</span><span><b>${a.onTime??'—'}${a.onTime!=null?'%':''}</b> on time</span></div>`}
function renderBenchmarkHistory(rows){const done=rows.filter(x=>x.completedAt);if(!done.length)return '<div class="empty-mini">Your first completed weekly benchmark will become the baseline.</div>';return `<div class="benchmark-history">${done.slice().reverse().map(x=>`<div><span>${esc(x.weekKey)}</span><b>${Math.round(x.score||0)}%</b><small>${esc(x.verdict||'')}</small></div>`).join('')}</div>`}
function renderCompanyEvidence(g,summary){if(!g)return `<div class="company-evidence card"><div><div class="kicker">COMMUNITY PROCESS INTELLIGENCE</div><h3>Not enough evidence yet</h3><p>${summary?.reportCount||0} structured interview reports exist overall. A company/role pattern only appears after the privacy threshold (${summary?.minSamples||5}+ matching reports) is met.</p></div><span class="badge">PRIVACY THRESHOLD</span></div>`;return `<div class="company-evidence card"><div><div class="kicker">COMMUNITY PROCESS INTELLIGENCE · ${esc(g.evidence.toUpperCase())}</div><h3>${esc(g.company)} · ${esc(g.role)}</h3><p>${g.samples} anonymous structured reports. These are observed process signals, not guaranteed future questions.</p><div class="intel-tags">${(g.topRounds||[]).map(x=>`<span>${esc(x.round.replaceAll('_',' '))} · ${x.n}</span>`).join('')}${(g.topTopics||[]).slice(0,5).map(x=>`<span>${esc(x.topic)} · ${x.n}</span>`).join('')}</div></div><span class="badge ${evidenceTone(g.evidence)}">${g.samples} REPORTS</span></div>`}

window.runNextAction=function(type,concept){
  if(type==='weekly_benchmark')return startWeeklyBenchmark();
  if(type==='recover_plan')return setView('planner');
  if(type==='revision'||type==='weakness'){setView('weaknesses');return}
  goSetup('full');
};

window.startWeeklyBenchmark=async function(){
  const out=await api('/api/weekly/start','POST',{applicationId:weeklyState.selectedApplicationId||null});
  if(out.error){handleProductError(out);return}
  config={...config,...(out.config||{}),weeklyBenchmark:true};
  session={id:out.sessionId,questions:out.questions||[],remaining:[...(out.questions||[])],answered:[],scores:[],review:[],targetDifficulty:2,profileAnalysis:out.profileAnalysis||null,interviewPlan:out.interviewPlan||null,panel:null,lastPanelist:null,weeklyBenchmark:out.benchmark};
  elapsed=0;currentIndex=0;clearInterval(timer);timer=setInterval(()=>{elapsed++;const el=$('#liveTimer');if(el)el.textContent=fmtTime(elapsed)},1000);setView('interview');pickNextQuestion();
};

const _v14RenderApplicationDetail=renderApplicationDetail;
renderApplicationDetail=function(a){const base=_v14RenderApplicationDetail(a);return base.replace('<div style="display:flex;gap:7px;flex-wrap:wrap;margin:12px 0">',`<div class="application-cockpit-link"><span>Weekly evidence, outcome calibration and next action</span><button class="btn" onclick="weeklyState.selectedApplicationId='${esc(a.applicationId)}';setView('weekly')">Open cockpit</button></div><div style="display:flex;gap:7px;flex-wrap:wrap;margin:12px 0">`)};

window.toggleOutcomeForm=function(id){const slot=$(`#outcomeForm-${id}`);if(!slot)return;if(slot.innerHTML.trim()){slot.innerHTML='';return}slot.innerHTML=`<div class="robustness-panel"><b>Report a real interview outcome</b><p class="field-note">Your private notes stay in your account. If you opt in below, only structured process fields are contributed anonymously—never exact questions or answers.</p><div class="two-col"><div class="field"><label>ROUND</label><select id="outcomeRound"><option value="recruiter">Recruiter</option><option value="sql">SQL / technical</option><option value="excel">Excel</option><option value="analytics">Analytics</option><option value="statistics">Statistics</option><option value="case">Case</option><option value="hiring_manager">Hiring manager</option><option value="panel">Panel</option><option value="take_home">Take-home</option><option value="final">Final</option></select></div><div class="field"><label>OUTCOME</label><select id="outcomeValue"><option value="passed">Passed</option><option value="rejected">Rejected</option><option value="offer">Offer</option><option value="withdrew">Withdrew</option></select></div></div><div class="two-col"><div class="field"><label>DIFFICULTY</label><select id="outcomeDifficulty"><option value="unspecified">Not sure</option><option value="easy">Easy</option><option value="medium">Medium</option><option value="hard">Hard</option><option value="mixed">Mixed</option></select></div><div class="field"><label>DURATION</label><select id="outcomeDuration"><option>unspecified</option><option>under 30 min</option><option>30–45 min</option><option>45–60 min</option><option>60+ min</option></select></div></div><div class="field"><label>TOPICS (comma separated)</label><input id="outcomeTopics" placeholder="SQL, windows, metrics, experimentation"></div><div class="field"><label>PRIVATE NOTES</label><textarea id="outcomeNotes" placeholder="High-level notes for your own future preparation."></textarea></div><label class="process-optin"><input id="outcomeContribute" type="checkbox"> Contribute company, role, round, outcome, difficulty, duration bucket and topic labels to anonymous aggregate interview-process intelligence.</label><button class="btn primary" onclick="saveOutcomeV14('${id}')">Save outcome</button></div>`};
window.saveOutcomeV14=async function(id){const a=applicationsState.items.find(x=>x.applicationId===id),topics=$('#outcomeTopics').value.split(',').map(x=>x.trim()).filter(Boolean);const payload={applicationId:id,companyName:a?.companyName||'',roleTitle:a?.roleTitle||'',roundType:$('#outcomeRound').value,outcome:$('#outcomeValue').value,topics,notes:$('#outcomeNotes').value};const r=await api('/api/outcome/save','POST',payload);if(r.error)return alert(r.error);if($('#outcomeContribute')?.checked){const x=await api('/api/process/report','POST',{company:a?.companyName||'',role:a?.roleTitle||'',roundType:$('#outcomeRound').value,outcome:$('#outcomeValue').value,difficulty:$('#outcomeDifficulty').value,durationBucket:$('#outcomeDuration').value,topics});if(x.error)alert('Outcome saved privately, but aggregate contribution failed: '+x.error)}alert('Outcome saved. Your mock-to-real calibration will update as evidence accumulates.');toggleOutcomeForm(id);};

const _v14RenderAnalytics=renderAnalytics;
renderAnalytics=function(){_v14RenderAnalytics();const d=analyticsData||{},w=d.weeklyBenchmark||{},c=d.outcomeCalibration||{},g=d.aggregateProcessIntelligence||{};$('#view-analytics').insertAdjacentHTML('beforeend',`<div class="section-head"><h3>Outcome-calibrated preparation</h3><span class="label">V14</span></div><div class="analytics-grid"><div class="analytics-card"><h3>Weekly benchmark</h3><p>Comparable mixed interview sessions create a cleaner trend than random practice scores.</p><div class="concept-row"><div><b>Completed benchmarks</b></div><strong>${w.trend?.count||0}</strong></div><div class="concept-row"><div><b>Latest change</b></div><strong>${fmtDelta(w.trend?.delta)}</strong></div><button class="btn" onclick="setView('weekly')">Open application cockpit</button></div><div class="analytics-card"><h3>Mock → real outcome calibration</h3><p>${esc(c.note||'Report real outcomes to create personal evidence.')}</p><div class="concept-row"><div><b>Paired outcomes</b></div><strong>${c.samples||0}</strong></div><div class="concept-row"><div><b>Passed-round mock avg</b></div><strong>${c.passedAvg==null?'—':c.passedAvg+'%'}</strong></div><div class="concept-row"><div><b>Rejected-round mock avg</b></div><strong>${c.failedAvg==null?'—':c.failedAvg+'%'}</strong></div></div><div class="analytics-card"><h3>Aggregate interview-process evidence</h3><p>Only groups above the ${g.minSamples||5}-report privacy threshold are shown.</p><div class="concept-row"><div><b>Structured reports</b></div><strong>${g.reportCount||0}</strong></div><div class="concept-row"><div><b>Visible company/role groups</b></div><strong>${(g.groups||[]).length}</strong></div></div></div>`)};

const _v14RenderDashboard=renderDashboard;
renderDashboard=function(){_v14RenderDashboard();api('/api/weekly/overview').then(w=>{const head=$('#view-dashboard .dashboard-head');if(!head)return;head.insertAdjacentHTML('afterend',`<div class="weekly-strip"><div><span class="kicker">THIS WEEK</span><b>${esc(w.nextAction?.title||'Build interview evidence')}</b><small>${esc(w.nextAction?.why||'')}</small></div><div><span>${w.currentBenchmark?.completedAt?`${Math.round(w.currentBenchmark.score||0)}% benchmark`:'Benchmark due'}</span><button class="text-action" onclick="setView('weekly')">Open cockpit</button></div></div>`)})};

const _v14RenderInterview=renderInterview;
renderInterview=function(){_v14RenderInterview();if(config.weeklyBenchmark){const main=$('#view-interview .interview-main');if(main)main.insertAdjacentHTML('afterbegin',`<div class="weekly-benchmark-banner"><b>Weekly benchmark · ${esc(session?.weeklyBenchmark?.weekKey||'current week')}</b><span>Comparable real-style session · no score shown until the end · one locked benchmark per week</span></div>`)}};
const _v14RenderResults=renderResults;
renderResults=function(){_v14RenderResults();if(config.weeklyBenchmark&&session?.result){$('#view-results').insertAdjacentHTML('afterbegin',`<div class="weekly-result card"><div><div class="kicker">WEEKLY BENCHMARK RECORDED</div><h3>${session.result.score}% · ${esc(session.result.verdict)}</h3><p>This score is now part of your comparable weekly trend. Use targeted practice between benchmarks rather than retaking the same weekly checkpoint.</p></div><button class="btn" onclick="setView('weekly')">Open cockpit</button></div>`)}};
