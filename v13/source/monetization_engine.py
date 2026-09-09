import hashlib, hmac, json, os, secrets, sqlite3, time, urllib.parse, urllib.request, urllib.error
from datetime import datetime, timedelta, timezone

ROOT=os.path.dirname(os.path.abspath(__file__))
RUNTIME=os.path.join(ROOT,"runtime")
os.makedirs(RUNTIME,exist_ok=True)
DB_PATH=os.environ.get("BILLING_STORE_PATH",os.path.join(RUNTIME,"billing.db"))

PAID_PLANS={"interview_week","pro","founding_annual","referral_pass"}
PREMIUM_FEATURES={
    "jd_interview","panel_interview","interview_day","takehome","investigation",
    "optimization","data_model","metric_design","advanced_analytics","premium_voice"
}
METERED_FREE={
    "mixed_mock":("week",1),
    "advanced_drill":("day",3),
    "answer_coach":("day",2),
}


def _now_dt(): return datetime.now(timezone.utc)
def _now(): return _now_dt().isoformat()
def _truthy(name,default="0"): return os.environ.get(name,default).lower() in ("1","true","yes","on")
def _hash(value): return hashlib.sha256(str(value or "guest").encode()).hexdigest()[:32]
def _safe(value,limit=200): return str(value or "").strip()[:limit]

def _conn():
    con=sqlite3.connect(DB_PATH);con.row_factory=sqlite3.Row
    con.executescript("""
    CREATE TABLE IF NOT EXISTS billing_entitlements(
      subject_hash TEXT PRIMARY KEY,
      plan TEXT NOT NULL DEFAULT 'free',
      status TEXT NOT NULL DEFAULT 'active',
      valid_until TEXT,
      source TEXT,
      stripe_customer_id TEXT,
      stripe_subscription_id TEXT,
      updated_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS billing_pending(
      checkout_session_id TEXT PRIMARY KEY,
      subject_hash TEXT NOT NULL,
      plan TEXT NOT NULL,
      created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS billing_events(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      event_id TEXT UNIQUE,
      event_type TEXT,
      subject_hash TEXT,
      plan TEXT,
      payload_json TEXT,
      created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS feature_usage(
      subject_hash TEXT NOT NULL,
      feature TEXT NOT NULL,
      period_key TEXT NOT NULL,
      count INTEGER NOT NULL DEFAULT 0,
      updated_at TEXT NOT NULL,
      PRIMARY KEY(subject_hash,feature,period_key)
    );
    CREATE TABLE IF NOT EXISTS referral_rewards(
      subject_hash TEXT PRIMARY KEY,
      completed_referrals INTEGER NOT NULL DEFAULT 0,
      granted_at TEXT,
      valid_until TEXT,
      updated_at TEXT NOT NULL
    );
    """)
    con.commit();return con


def _service_config():
    return {"url":os.environ.get("SUPABASE_URL","").rstrip("/"),"key":os.environ.get("SUPABASE_SERVICE_ROLE_KEY","")}

def _service_request(method,table,payload=None,query="",prefer=None):
    c=_service_config()
    if not (c["url"] and c["key"]): return None
    data=None if payload is None else json.dumps(payload).encode()
    headers={"apikey":c["key"],"Authorization":"Bearer "+c["key"],"Content-Type":"application/json"}
    if prefer: headers["Prefer"]=prefer
    url=f"{c['url']}/rest/v1/{table}"+("?"+query if query else "")
    try:
        req=urllib.request.Request(url,data=data,headers=headers,method=method)
        with urllib.request.urlopen(req,timeout=8) as r:
            raw=r.read().decode(); return json.loads(raw) if raw else []
    except Exception:
        return None

def _mirror_entitlement(row):
    remote=dict(row)
    _service_request("POST","billing_entitlements",[remote],"on_conflict=subject_hash","resolution=merge-duplicates,return=minimal")

def _load_remote(subject_hash):
    rows=_service_request("GET","billing_entitlements",query=f"subject_hash=eq.{urllib.parse.quote(subject_hash)}&select=*&limit=1")
    if not rows:return None
    row=rows[0]
    try:
        con=_conn();con.execute("""INSERT INTO billing_entitlements(subject_hash,plan,status,valid_until,source,stripe_customer_id,stripe_subscription_id,updated_at)
        VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(subject_hash) DO UPDATE SET plan=excluded.plan,status=excluded.status,valid_until=excluded.valid_until,source=excluded.source,stripe_customer_id=excluded.stripe_customer_id,stripe_subscription_id=excluded.stripe_subscription_id,updated_at=excluded.updated_at""",
        (row.get("subject_hash"),row.get("plan") or "free",row.get("status") or "active",row.get("valid_until"),row.get("source"),row.get("stripe_customer_id"),row.get("stripe_subscription_id"),row.get("updated_at") or _now()));con.commit();con.close()
    except Exception:pass
    return row


def plans():
    return [
      {"id":"free","name":"Free","price":"$0","billing":"forever","description":"Learn the fundamentals and prove your baseline before paying.","features":["Readiness diagnostic","SQL Academy","Core SQL practice","Limited mixed mock","Basic analytics"]},
      {"id":"interview_week","name":"Interview Week","price":os.environ.get("INTERVIEW_WEEK_DISPLAY_PRICE","$7.99"),"billing":"one-time · 10 days","description":"For the week when the real interview is close.","popular":True,"features":["JD-specific interviews","Mock panel","Interview Day","Take-homes + investigations","Advanced labs","Answer Coach","Higher voice access"]},
      {"id":"pro","name":"Pro","price":os.environ.get("PRO_MONTHLY_DISPLAY_PRICE","$14.99"),"billing":"per month","description":"Ongoing adaptive preparation across applications.","features":["Everything in Interview Week","Unlimited target-job workspaces","Adaptive study plans","Full analytics history","All advanced labs","Priority AI/voice allowances"]},
      {"id":"founding_annual","name":"Founding Annual","price":os.environ.get("FOUNDING_ANNUAL_DISPLAY_PRICE","$49"),"billing":"per year","description":"Optional founding-user plan when enabled.","hidden":not bool(os.environ.get("STRIPE_PRICE_FOUNDING_ANNUAL")),"features":["Everything in Pro","Founding price lock while subscription remains active"]},
    ]


def config_status():
    return {
      "enabled":_truthy("MONETIZATION_ENABLED","0"),
      "enforced":_truthy("MONETIZATION_ENFORCED","0"),
      "stripeConfigured":bool(os.environ.get("STRIPE_SECRET_KEY") and (os.environ.get("STRIPE_PRICE_INTERVIEW_WEEK") or os.environ.get("STRIPE_PRICE_PRO_MONTHLY"))),
      "webhookConfigured":bool(os.environ.get("STRIPE_WEBHOOK_SECRET")),
      "currency":"USD",
    }


def _local_row(subject_hash):
    con=_conn();row=con.execute("SELECT * FROM billing_entitlements WHERE subject_hash=?",(subject_hash,)).fetchone();con.close()
    return dict(row) if row else None

def _active(row):
    if not row:return False
    if row.get("status") not in ("active","trialing","paid"):return False
    vu=row.get("valid_until")
    if not vu:return row.get("plan") in ("pro","founding_annual")
    try:return datetime.fromisoformat(vu.replace("Z","+00:00"))>_now_dt()
    except:return False

def _entitlement(subject):
    sh=_hash(subject);row=_local_row(sh)
    if not row: row=_load_remote(sh)
    if row and not _active(row):
        row=dict(row);row["status"]="expired";row["plan"]="free"
    return sh,row

def grant(subject,plan,days=None,source="manual",status="active",customer_id=None,subscription_id=None,valid_until=None):
    sh=_hash(subject)
    if valid_until is None and days: valid_until=(_now_dt()+timedelta(days=days)).isoformat()
    row={"subject_hash":sh,"plan":plan,"status":status,"valid_until":valid_until,"source":source,"stripe_customer_id":customer_id,"stripe_subscription_id":subscription_id,"updated_at":_now()}
    con=_conn();con.execute("""INSERT INTO billing_entitlements(subject_hash,plan,status,valid_until,source,stripe_customer_id,stripe_subscription_id,updated_at)
    VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(subject_hash) DO UPDATE SET plan=excluded.plan,status=excluded.status,valid_until=excluded.valid_until,source=excluded.source,stripe_customer_id=COALESCE(excluded.stripe_customer_id,billing_entitlements.stripe_customer_id),stripe_subscription_id=COALESCE(excluded.stripe_subscription_id,billing_entitlements.stripe_subscription_id),updated_at=excluded.updated_at""",tuple(row.values()));con.commit();con.close();_mirror_entitlement(row)
    return row

def revoke(subject=None,subject_hash=None,source="stripe"):
    sh=subject_hash or _hash(subject)
    existing=_local_row(sh) or _load_remote(sh) or {}
    row={"subject_hash":sh,"plan":"free","status":"canceled","valid_until":_now(),"source":source,"stripe_customer_id":existing.get("stripe_customer_id"),"stripe_subscription_id":existing.get("stripe_subscription_id"),"updated_at":_now()}
    con=_conn();con.execute("""INSERT INTO billing_entitlements(subject_hash,plan,status,valid_until,source,stripe_customer_id,stripe_subscription_id,updated_at) VALUES(?,?,?,?,?,?,?,?)
    ON CONFLICT(subject_hash) DO UPDATE SET plan=excluded.plan,status=excluded.status,valid_until=excluded.valid_until,source=excluded.source,updated_at=excluded.updated_at""",tuple(row.values()));con.commit();con.close();_mirror_entitlement(row);return row


def _period_key(kind):
    now=_now_dt()
    if kind=="day": return now.strftime("%Y-%m-%d")
    y,w,_=now.isocalendar();return f"{y}-W{w:02d}"

def _usage(subject_hash,feature,kind):
    key=_period_key(kind);con=_conn();row=con.execute("SELECT count FROM feature_usage WHERE subject_hash=? AND feature=? AND period_key=?",(subject_hash,feature,key)).fetchone();con.close();return int(row["count"] if row else 0),key

def _consume(subject_hash,feature,kind):
    count,key=_usage(subject_hash,feature,kind);con=_conn();con.execute("""INSERT INTO feature_usage(subject_hash,feature,period_key,count,updated_at) VALUES(?,?,?,?,?) ON CONFLICT(subject_hash,feature,period_key) DO UPDATE SET count=count+1,updated_at=excluded.updated_at""",(subject_hash,feature,key,1,_now()));con.commit();con.close();return count+1


def referral_progress(subject):
    try:
        import beta_ops
        return beta_ops.referral_reward_progress(subject)
    except Exception:
        return {"completed":0,"needed":2,"eligible":False}

def claim_referral_reward(subject):
    sh=_hash(subject);p=referral_progress(subject)
    con=_conn();existing=con.execute("SELECT * FROM referral_rewards WHERE subject_hash=?",(sh,)).fetchone()
    if existing and existing["valid_until"]:
        try:
            if datetime.fromisoformat(existing["valid_until"].replace("Z","+00:00"))>_now_dt():
                con.close();return {"ok":True,"alreadyGranted":True,"validUntil":existing["valid_until"],"progress":p}
        except:pass
    if not p.get("eligible"):
        con.close();return {"error":f"{max(0,p.get('needed',2)-p.get('completed',0))} more completed referral(s) needed.","progress":p}
    until=(_now_dt()+timedelta(hours=int(os.environ.get("REFERRAL_REWARD_HOURS","48")))).isoformat()
    con.execute("""INSERT INTO referral_rewards(subject_hash,completed_referrals,granted_at,valid_until,updated_at) VALUES(?,?,?,?,?) ON CONFLICT(subject_hash) DO UPDATE SET completed_referrals=excluded.completed_referrals,granted_at=excluded.granted_at,valid_until=excluded.valid_until,updated_at=excluded.updated_at""",(sh,p.get("completed",0),_now(),until,_now()));con.commit();con.close()
    grant(subject,"referral_pass",source="referral",valid_until=until)
    return {"ok":True,"validUntil":until,"progress":p}


def public_status(subject,user=None):
    sh,row=_entitlement(subject);active_plan=row.get("plan") if row and _active(row) else "free"
    premium=active_plan in PAID_PLANS
    usage={}
    for feature,(kind,limit) in METERED_FREE.items():
        count,key=_usage(sh,feature,kind);usage[feature]={"used":count,"limit":limit,"remaining":max(0,limit-count),"period":kind,"periodKey":key}
    return {
      "config":config_status(),"plan":active_plan,"premium":premium,
      "status":row.get("status") if row else "active","validUntil":row.get("valid_until") if row else None,
      "source":row.get("source") if row else "free","authenticated":bool(user),
      "plans":[p for p in plans() if not p.get("hidden")],"usage":usage,"referrals":referral_progress(subject),
      "portalAvailable":bool(row and row.get("stripe_customer_id") and os.environ.get("STRIPE_SECRET_KEY")),
    }


def authorize(subject,feature,consume=False,user=None):
    st=public_status(subject,user)
    if not st["config"]["enabled"] or not st["config"]["enforced"]:
        return {"allowed":True,"reason":"monetization_not_enforced","billing":st}
    if st["premium"]: return {"allowed":True,"reason":"premium","billing":st}
    if feature in PREMIUM_FEATURES:
        return {"allowed":False,"reason":"premium_required","feature":feature,"billing":st}
    if feature in METERED_FREE:
        kind,limit=METERED_FREE[feature];sh=_hash(subject);used,_=_usage(sh,feature,kind)
        if used>=limit:return {"allowed":False,"reason":"free_limit_reached","feature":feature,"billing":st}
        if consume:_consume(sh,feature,kind)
    return {"allowed":True,"reason":"free","billing":public_status(subject,user)}


def _stripe_request(path,params):
    key=os.environ.get("STRIPE_SECRET_KEY","")
    if not key:raise RuntimeError("Stripe is not configured.")
    encoded=urllib.parse.urlencode(params,doseq=True).encode()
    req=urllib.request.Request("https://api.stripe.com"+path,data=encoded,headers={"Authorization":"Bearer "+key,"Content-Type":"application/x-www-form-urlencoded"},method="POST")
    try:
        with urllib.request.urlopen(req,timeout=12) as r:return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        detail=e.read().decode(errors="replace")
        try:detail=json.loads(detail).get("error",{}).get("message") or detail
        except:pass
        raise RuntimeError(f"Stripe request failed ({e.code}): {str(detail)[:500]}")


def checkout(subject,plan,user=None,base_url=""):
    if not _truthy("MONETIZATION_ENABLED","0"): return {"error":"Payments are not enabled on this deployment."}
    if plan not in {"interview_week","pro","founding_annual"}:return {"error":"Unknown plan."}
    price_env={"interview_week":"STRIPE_PRICE_INTERVIEW_WEEK","pro":"STRIPE_PRICE_PRO_MONTHLY","founding_annual":"STRIPE_PRICE_FOUNDING_ANNUAL"}[plan]
    price=os.environ.get(price_env,"")
    if not price:return {"error":f"{price_env} is not configured."}
    if plan in ("pro","founding_annual") and not user:
        return {"error":"Sign in before starting a recurring plan so access follows your account across devices.","requiresAuth":True}
    sh=_hash(subject);mode="payment" if plan=="interview_week" else "subscription"
    base=(os.environ.get("PUBLIC_BASE_URL") or base_url or "http://localhost:8000").rstrip("/")
    params=[("success_url",base+"/?billing=success&session_id={CHECKOUT_SESSION_ID}"),("cancel_url",base+"/?billing=cancel"),("mode",mode),("line_items[0][price]",price),("line_items[0][quantity]","1"),("client_reference_id",sh),("allow_promotion_codes","true"),("metadata[subject_hash]",sh),("metadata[plan]",plan)]
    if user and user.get("email"):params.append(("customer_email",user["email"]))
    if mode=="payment":params.append(("customer_creation","always"))
    else:
        params.extend([("subscription_data[metadata][subject_hash]",sh),("subscription_data[metadata][plan]",plan)])
    try:out=_stripe_request("/v1/checkout/sessions",params)
    except Exception as e:return {"error":str(e)}
    sid=out.get("id")
    if sid:
        con=_conn();con.execute("INSERT OR REPLACE INTO billing_pending(checkout_session_id,subject_hash,plan,created_at) VALUES(?,?,?,?)",(sid,sh,plan,_now()));con.commit();con.close()
    return {"ok":True,"checkoutUrl":out.get("url"),"sessionId":sid,"plan":plan}


def portal(subject,base_url=""):
    sh,row=_entitlement(subject)
    customer=(row or {}).get("stripe_customer_id")
    if not customer:return {"error":"No Stripe customer is linked to this account yet."}
    base=(os.environ.get("PUBLIC_BASE_URL") or base_url or "http://localhost:8000").rstrip("/")
    try:out=_stripe_request("/v1/billing_portal/sessions",[("customer",customer),("return_url",base+"/?billing=return")])
    except Exception as e:return {"error":str(e)}
    return {"ok":True,"url":out.get("url")}


def _stripe_get(path):
    key=os.environ.get("STRIPE_SECRET_KEY","")
    if not key: raise RuntimeError("Stripe is not configured.")
    req=urllib.request.Request("https://api.stripe.com"+path,headers={"Authorization":"Bearer "+key},method="GET")
    try:
        with urllib.request.urlopen(req,timeout=12) as r:return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        detail=e.read().decode(errors="replace")
        try:detail=json.loads(detail).get("error",{}).get("message") or detail
        except:pass
        raise RuntimeError(f"Stripe request failed ({e.code}): {str(detail)[:500]}")

def confirm_checkout(subject,session_id):
    sid=_safe(session_id,160)
    if not sid.startswith("cs_"):return {"error":"Invalid checkout session."}
    try:obj=_stripe_get("/v1/checkout/sessions/"+urllib.parse.quote(sid,safe=""))
    except Exception as e:return {"error":str(e)}
    sh=_hash(subject)
    if obj.get("client_reference_id")!=sh:return {"error":"This checkout session does not belong to the current account/browser."}
    plan=_plan_from_obj(obj)
    paid=(obj.get("payment_status") in ("paid","no_payment_required")) or (obj.get("mode")=="subscription" and obj.get("status")=="complete")
    if not paid:return {"error":"Checkout is not complete yet."}
    _grant_hash(sh,plan,"active",source="stripe_confirm",customer=obj.get("customer"),subscription=obj.get("subscription"))
    return {"ok":True,"plan":plan,"billing":public_status(subject)}

def verify_webhook(raw,signature):
    secret=os.environ.get("STRIPE_WEBHOOK_SECRET","")
    if not secret:return False,"Webhook secret is not configured."
    parts={}
    for item in str(signature or "").split(","):
        if "=" in item:
            k,v=item.split("=",1);parts.setdefault(k,[]).append(v)
    try:t=int((parts.get("t") or ["0"])[0])
    except:return False,"Invalid Stripe signature timestamp."
    if abs(int(time.time())-t)>int(os.environ.get("STRIPE_WEBHOOK_TOLERANCE_SECONDS","300")):return False,"Stripe signature timestamp is outside tolerance."
    signed=f"{t}.".encode()+raw
    expected=hmac.new(secret.encode(),signed,hashlib.sha256).hexdigest()
    if not any(hmac.compare_digest(expected,v) for v in parts.get("v1",[])):return False,"Invalid Stripe signature."
    return True,None


def _subject_from_obj(obj):
    md=(obj or {}).get("metadata") or {};sh=md.get("subject_hash") or (obj or {}).get("client_reference_id")
    if not sh and (obj or {}).get("id"):
        con=_conn();r=con.execute("SELECT subject_hash,plan FROM billing_pending WHERE checkout_session_id=?",((obj or {}).get("id"),)).fetchone();con.close()
        if r:return r["subject_hash"]
    return _safe(sh,64)

def _plan_from_obj(obj):
    md=(obj or {}).get("metadata") or {};p=md.get("plan")
    if p:return p
    if (obj or {}).get("id"):
        con=_conn();r=con.execute("SELECT plan FROM billing_pending WHERE checkout_session_id=?",((obj or {}).get("id"),)).fetchone();con.close()
        if r:return r["plan"]
    return "pro"

def _grant_hash(sh,plan,status="active",valid_until=None,source="stripe",customer=None,subscription=None):
    if not sh:return
    if plan=="interview_week" and not valid_until:valid_until=(_now_dt()+timedelta(days=int(os.environ.get("INTERVIEW_WEEK_DAYS","10")))).isoformat()
    if plan in ("pro","founding_annual") and not valid_until:valid_until=(_now_dt()+timedelta(days=31 if plan=="pro" else 366)).isoformat()
    row={"subject_hash":sh,"plan":plan,"status":status,"valid_until":valid_until,"source":source,"stripe_customer_id":customer,"stripe_subscription_id":subscription,"updated_at":_now()}
    con=_conn();con.execute("""INSERT INTO billing_entitlements(subject_hash,plan,status,valid_until,source,stripe_customer_id,stripe_subscription_id,updated_at) VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(subject_hash) DO UPDATE SET plan=excluded.plan,status=excluded.status,valid_until=excluded.valid_until,source=excluded.source,stripe_customer_id=COALESCE(excluded.stripe_customer_id,billing_entitlements.stripe_customer_id),stripe_subscription_id=COALESCE(excluded.stripe_subscription_id,billing_entitlements.stripe_subscription_id),updated_at=excluded.updated_at""",tuple(row.values()));con.commit();con.close();_mirror_entitlement(row)

def handle_webhook(raw,signature):
    ok,err=verify_webhook(raw,signature)
    if not ok:return {"error":err,"status":400}
    try:event=json.loads(raw.decode())
    except:return {"error":"Invalid webhook JSON.","status":400}
    eid=_safe(event.get("id"),120);etype=_safe(event.get("type"),120);obj=((event.get("data") or {}).get("object") or {})
    con=_conn()
    if eid and con.execute("SELECT 1 FROM billing_events WHERE event_id=?",(eid,)).fetchone():con.close();return {"ok":True,"duplicate":True}
    sh=_subject_from_obj(obj);plan=_plan_from_obj(obj)
    if etype=="checkout.session.completed":
        paid=(obj.get("payment_status") in ("paid","no_payment_required")) or obj.get("mode")=="subscription"
        if paid:_grant_hash(sh,plan,"active",source="stripe_checkout",customer=obj.get("customer"),subscription=obj.get("subscription"))
    elif etype in ("customer.subscription.created","customer.subscription.updated"):
        md=obj.get("metadata") or {};sh=md.get("subject_hash") or sh;plan=md.get("plan") or plan;status=obj.get("status") or "active";end=obj.get("current_period_end");until=datetime.fromtimestamp(end,tz=timezone.utc).isoformat() if end else None
        if status in ("active","trialing"):_grant_hash(sh,plan,status,until,"stripe_subscription",obj.get("customer"),obj.get("id"))
        elif sh:_grant_hash(sh,"free",status,_now(),"stripe_subscription",obj.get("customer"),obj.get("id"))
    elif etype=="customer.subscription.deleted":
        md=obj.get("metadata") or {};sh=md.get("subject_hash") or sh
        if sh:_grant_hash(sh,"free","canceled",_now(),"stripe_subscription",obj.get("customer"),obj.get("id"))
    elif etype=="invoice.payment_failed":
        sub=obj.get("subscription")
        if sub:
            r=con.execute("SELECT subject_hash,plan,stripe_customer_id FROM billing_entitlements WHERE stripe_subscription_id=?",(sub,)).fetchone()
            if r:_grant_hash(r["subject_hash"],r["plan"],"past_due",_now(),"stripe_invoice",r["stripe_customer_id"],sub)
    payload={"object_id":obj.get("id"),"status":obj.get("status"),"payment_status":obj.get("payment_status")}
    try:con.execute("INSERT INTO billing_events(event_id,event_type,subject_hash,plan,payload_json,created_at) VALUES(?,?,?,?,?,?)",(eid,etype,sh,plan,json.dumps(payload),_now()));con.commit()
    except sqlite3.IntegrityError:pass
    con.close();return {"ok":True,"eventType":etype,"plan":plan}


def admin_summary():
    con=_conn();rows=[dict(r) for r in con.execute("SELECT plan,status,COUNT(*) n FROM billing_entitlements GROUP BY plan,status").fetchall()];events=con.execute("SELECT event_type,COUNT(*) n FROM billing_events GROUP BY event_type").fetchall();con.close()
    remote=_service_request("GET","billing_entitlements",query="select=plan,status&limit=5000")
    if remote is not None:
        counts={}
        for r in remote:
            key=(r.get("plan") or "free",r.get("status") or "active");counts[key]=counts.get(key,0)+1
        rows=[{"plan":k[0],"status":k[1],"n":v} for k,v in sorted(counts.items())]
    active=sum(r["n"] for r in rows if r["plan"] in PAID_PLANS and r["status"] in ("active","trialing","paid"))
    return {"activePaid":active,"entitlements":rows,"stripeEvents":{r["event_type"]:r["n"] for r in events}}


def dev_grant(subject,plan="interview_week"):
    if _truthy("HOSTED_MODE","0"):return {"error":"Development grants are disabled in hosted mode."}
    days=10 if plan=="interview_week" else 31
    return {"ok":True,"entitlement":grant(subject,plan,days=days,source="dev")}
