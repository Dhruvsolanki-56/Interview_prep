// V13 — monetization + entitlements. Payments remain disabled until server configuration explicitly enables them.
let billingState=null;

window.handleProductError=function(r){
  if(r?.upgradeRequired){showUpgradeModal(r);return}
  alert(r?.error||'Something went wrong.');
};

async function loadBillingStatus(){
  billingState=await api('/api/billing/status');
  return billingState;
}

function billingPlanLabel(id){return ({free:'Free',interview_week:'Interview Week',pro:'Pro',founding_annual:'Founding Annual',referral_pass:'Referral Pass'})[id]||id}
function formatBillingDate(x){if(!x)return '';try{return new Date(x).toLocaleString()}catch{return x}}

async function renderPlans(){
  const root=$('#view-plans');if(!root)return;
  const b=await loadBillingStatus();
  const configured=b?.config?.stripeConfigured,enabled=b?.config?.enabled,enforced=b?.config?.enforced;
  const ref=b?.referrals||{};
  root.innerHTML=`
    <div class="billing-head card">
      <div><div class="kicker">ACCESS</div><h2>${esc(billingPlanLabel(b.plan||'free'))}</h2><p>${b.premium?'Premium interview surfaces are unlocked.':'The free tier remains useful. Upgrade only when a real interview is close or you want ongoing adaptive prep.'}</p>${b.validUntil?`<small>Access through ${esc(formatBillingDate(b.validUntil))}</small>`:''}</div>
      <div class="billing-state"><span class="badge ${b.premium?'green':'blue'}">${b.premium?'PREMIUM':'FREE'}</span><span>${enabled?(enforced?'Billing enforced':'Billing preview'):'Payments disabled'}</span></div>
    </div>
    ${!enabled?`<div class="billing-note"><b>Development mode:</b> monetization is intentionally disabled. Configure Stripe and set <code>MONETIZATION_ENABLED=1</code> when you are ready to test checkout.</div>`:''}
    <div class="pricing-grid">${(b.plans||[]).map(p=>planCard(p,b,configured&&enabled)).join('')}</div>
    <div class="billing-secondary">
      <div class="card referral-card"><div class="kicker">ZERO-COST UNLOCK</div><h3>Invite candidates who actually complete the diagnostic.</h3><p>${ref.completed||0} of ${ref.needed||2} completed referrals. When eligible, you can unlock a ${Number(window.__refHours||48)}-hour premium pass without paying.</p><div class="progress"><span style="width:${Math.min(100,100*(ref.completed||0)/Math.max(1,ref.needed||2))}%"></span></div><button class="btn ${ref.eligible?'primary':''}" ${ref.eligible?'':'disabled'} onclick="claimReferralPass()">${ref.eligible?'Claim 48-hour pass':'Keep sharing your diagnostic'}</button></div>
      <div class="card billing-usage"><div class="kicker">FREE-TIER PACING</div><h3>Practice limits</h3>${Object.entries(b.usage||{}).map(([k,v])=>`<div class="billing-usage-row"><span>${esc(k.replaceAll('_',' '))}</span><b>${v.used}/${v.limit} ${v.period}</b></div>`).join('')||'<p>No free-tier meters are active.</p>'}${b.portalAvailable?'<button class="btn" onclick="openBillingPortal()">Manage billing</button>':''}</div>
    </div>`;
  api('/api/event','POST',{name:'pricing_viewed',payload:{plan:b.plan||'free',billing_status:b.premium?'premium':'free'}}).catch(()=>{});
}

function planCard(p,b,canCheckout){
  const current=(b.plan||'free')===p.id;
  let action='';
  if(p.id==='free') action=`<button class="btn" disabled>${current?'Current plan':'Included'}</button>`;
  else if(current) action=`<button class="btn" disabled>Current access</button>`;
  else if(canCheckout) action=`<button class="btn ${p.popular?'primary':''}" onclick="startCheckout('${p.id}')">${p.id==='interview_week'?'Get Interview Week':'Choose '+esc(p.name)}</button>`;
  else action=`<button class="btn" disabled>${b.config?.enabled?'Stripe price not configured':'Not enabled yet'}</button>`;
  return `<article class="price-card ${p.popular?'popular':''}">${p.popular?'<div class="price-popular">BEST FOR A REAL INTERVIEW</div>':''}<div class="kicker">${esc(p.name.toUpperCase())}</div><div class="price-line"><strong>${esc(p.price)}</strong><span>${esc(p.billing)}</span></div><p>${esc(p.description)}</p><ul>${(p.features||[]).map(x=>`<li>${esc(x)}</li>`).join('')}</ul>${action}</article>`
}

window.startCheckout=async function(plan){
  const b=billingState||await loadBillingStatus();
  if((plan==='pro'||plan==='founding_annual')&&!b.authenticated){
    alert('Sign in first for a recurring plan so paid access follows your account across devices.');renderAccount();setView('account');return;
  }
  const out=await api('/api/billing/checkout','POST',{plan});
  if(out.error){if(out.requiresAuth){renderAccount();setView('account')}else alert(out.error);return}
  if(out.checkoutUrl) location.href=out.checkoutUrl;
};
window.openBillingPortal=async function(){const out=await api('/api/billing/portal','POST',{});if(out.error)return alert(out.error);if(out.url)location.href=out.url};
window.claimReferralPass=async function(){const out=await api('/api/billing/referral-reward','POST',{});if(out.error)return alert(out.error);await renderPlans();alert('Premium referral access unlocked.')};

window.showUpgradeModal=function(data={}){
  let el=$('#upgradeOverlay');if(!el){document.body.insertAdjacentHTML('beforeend','<div id="upgradeOverlay" class="feedback-overlay hidden"></div>');el=$('#upgradeOverlay')}
  const b=data.billing||billingState||{};
  el.classList.remove('hidden');el.innerHTML=`<div class="feedback-modal upgrade-modal"><button class="modal-x" onclick="closeUpgradeModal()">×</button><div class="kicker">INTERVIEW WEEK / PRO</div><h3>This drill is outside the free allowance.</h3><p>${esc(data.reason==='free_limit_reached'?'You used the current free practice allowance. Your diagnostic and SQL Academy remain available.':'This is one of the high-intent interview surfaces reserved for paid access.')}</p><div class="upgrade-actions"><button class="btn" onclick="closeUpgradeModal()">Not now</button><button class="btn primary" onclick="closeUpgradeModal();renderPlans();setView('plans')">See plans</button></div></div>`;
};
window.closeUpgradeModal=function(){$('#upgradeOverlay')?.classList.add('hidden')};

const _v13RenderAccount=window.renderAccount;
window.renderAccount=function(){_v13RenderAccount();setTimeout(async()=>{const root=$('#view-account');if(!root)return;const b=await loadBillingStatus();root.insertAdjacentHTML('beforeend',`<div class="card account-card billing-account"><div class="kicker">PLAN</div><div class="account-status"><div><h3>${esc(billingPlanLabel(b.plan||'free'))}</h3><p>${b.premium?'Premium access is active.':'Free access is active.'}${b.validUntil?` Expires ${esc(formatBillingDate(b.validUntil))}.`:''}</p></div><button class="btn" onclick="renderPlans();setView('plans')">Plans & billing</button></div></div>`)},0)};

const _v13SetView=setView;
setView=function(v){_v13SetView(v);if(v==='plans'){document.querySelector('#pageEyebrow').textContent='ACCESS';document.querySelector('#pageTitle').textContent='Plans & billing';renderPlans()}};

const _v13RenderDashboard=renderDashboard;
renderDashboard=function(){_v13RenderDashboard();loadBillingStatus().then(b=>{const hero=$('#view-dashboard .dashboard-head')||$('#view-dashboard .hero');if(!hero)return;hero.insertAdjacentHTML('afterend',`<div class="plan-strip"><span><b>${esc(billingPlanLabel(b.plan||'free'))}</b>${b.premium&&b.validUntil?` · through ${esc(new Date(b.validUntil).toLocaleDateString())}`:''}</span><button class="text-action" onclick="renderPlans();setView('plans')">${b.premium?'Manage':'Plans'}</button></div>`)})};

(function(){const q=new URLSearchParams(location.search);const state=q.get('billing'),sid=q.get('session_id');if(!state)return;history.replaceState({},'',location.pathname);setTimeout(async()=>{if(state==='success'&&sid){const c=await api('/api/billing/confirm','POST',{sessionId:sid});if(c.error)console.warn(c.error)}await loadBillingStatus();renderPlans();setView('plans');if(state==='success')api('/api/event','POST',{name:'checkout_returned',payload:{status:'success',plan:billingState?.plan||'free'}}).catch(()=>{});},250)})();
