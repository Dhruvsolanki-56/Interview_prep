from datetime import datetime, timezone

PASS_OUTCOMES={"passed","offer","advanced","final","hired"}
FAIL_OUTCOMES={"rejected","failed","no_offer"}


def iso_week_key(dt=None):
    dt=dt or datetime.now(timezone.utc)
    y,w,_=dt.isocalendar()
    return f"{y}-W{w:02d}"


def evidence_label(n):
    n=int(n or 0)
    if n<5:return "insufficient"
    if n<12:return "early"
    if n<30:return "developing"
    return "stronger"


def confidence_from_evidence(attempts=0,outcomes=0,benchmark_count=0):
    score=min(100,attempts*4+outcomes*14+benchmark_count*10)
    if score<30:return {"score":score,"label":"Low evidence"}
    if score<60:return {"score":score,"label":"Growing evidence"}
    if score<85:return {"score":score,"label":"Useful evidence"}
    return {"score":score,"label":"Strong personal evidence"}


def calibrate_mock_to_outcomes(records):
    """records: [{mockScore, outcome, daysBefore?}]. Never claims prediction with tiny samples."""
    clean=[]
    for r in records or []:
        try:s=float(r.get("mockScore"))
        except:continue
        o=str(r.get("outcome") or "").lower()
        if o not in PASS_OUTCOMES|FAIL_OUTCOMES:continue
        clean.append({"score":s,"passed":o in PASS_OUTCOMES})
    if not clean:return {"samples":0,"evidence":"insufficient","note":"No mock-to-real-interview pairs yet."}
    passed=[x["score"] for x in clean if x["passed"]];failed=[x["score"] for x in clean if not x["passed"]]
    out={"samples":len(clean),"evidence":evidence_label(len(clean)),"passCount":len(passed),"failCount":len(failed),
         "passedAvg":round(sum(passed)/len(passed)) if passed else None,"failedAvg":round(sum(failed)/len(failed)) if failed else None}
    if len(clean)<5:
        out["note"]="Too little evidence for a benchmark. Treat this as personal history, not a prediction."
        return out
    if passed and failed:
        out["personalSeparation"] = round((sum(passed)/len(passed))-(sum(failed)/len(failed)))
        out["descriptiveBar"] = round(((sum(passed)/len(passed))+(sum(failed)/len(failed)))/2)
    elif passed:
        out["descriptiveBar"]=round(min(passed))
    else:
        out["descriptiveBar"]=None
    out["note"]="This bar summarizes your own reported outcomes. It is not a market benchmark or pass probability."
    return out


def weekly_trend(rows):
    rows=sorted(rows or [],key=lambda x:x.get("weekKey") or "")
    if not rows:return {"count":0,"delta":None,"latest":None,"previous":None,"direction":"none"}
    latest=rows[-1];prev=rows[-2] if len(rows)>1 else None
    delta=round(float(latest.get("score") or 0)-float(prev.get("score") or 0)) if prev else None
    direction="up" if delta is not None and delta>2 else "down" if delta is not None and delta<-2 else "flat" if delta is not None else "new"
    return {"count":len(rows),"delta":delta,"latest":latest,"previous":prev,"direction":direction}


def choose_next_action(application, mastery, revision_queue, adherence=None, last_benchmark=None):
    app=application or {};mastery=mastery or [];revision_queue=revision_queue or []
    adherence=adherence or {}
    if app.get("interviewDate"):
        try:
            days=(datetime.fromisoformat(str(app["interviewDate"])[:10]).date()-datetime.now(timezone.utc).date()).days
        except: days=None
    else: days=None
    due=[x for x in revision_queue if x.get("due")]
    weak=sorted(mastery,key=lambda x:float(x.get("mastery") or 0))[:4]
    if days is not None and days<=1:
        return {"type":"light_review","priority":"high","title":"Light review only","why":"Your interview is within 24 hours. Avoid cramming new concepts.","minutes":25}
    if adherence.get("overdue",0)>=2:
        return {"type":"recover_plan","priority":"high","title":"Recover overdue study work","why":f"{adherence.get('overdue')} planned tasks are overdue.","minutes":min(60,20+10*adherence.get("overdue",0))}
    if due:
        x=due[0];return {"type":"revision","priority":"high","title":f"Revisit {x.get('concept') or 'weak concept'}","why":"This concept is due in your spaced-repetition queue.","concept":x.get("concept"),"minutes":25}
    if not last_benchmark:
        return {"type":"weekly_benchmark","priority":"high","title":"Take your weekly benchmark","why":"You do not have a locked benchmark for the current preparation cycle yet.","minutes":30}
    if weak and float(weak[0].get("mastery") or 0)<70:
        return {"type":"weakness","priority":"medium","title":f"Strengthen {weak[0].get('concept')}","why":f"Current mastery is {round(float(weak[0].get('mastery') or 0))}%.","concept":weak[0].get("concept"),"minutes":30}
    return {"type":"mixed_practice","priority":"normal","title":"Run a mixed pressure drill","why":"No urgent overdue task or severe weakness is dominating your plan.","minutes":30}


def public_process_aggregate(reports,min_samples=5):
    """Returns only thresholded aggregates. Individual report rows never leave the server through this function."""
    groups={}
    for r in reports or []:
        company=(r.get("company") or "").strip();role=(r.get("role") or "").strip();
        if not company or not role:continue
        key=(company.lower(),role.lower());g=groups.setdefault(key,{"company":company,"role":role,"n":0,"rounds":{},"topics":{},"difficulty":{},"outcomes":{}})
        g["n"]+=1
        rd=(r.get("round") or "unknown").strip();g["rounds"][rd]=g["rounds"].get(rd,0)+1
        d=(r.get("difficulty") or "unspecified").strip();g["difficulty"][d]=g["difficulty"].get(d,0)+1
        o=(r.get("outcome") or "unknown").strip();g["outcomes"][o]=g["outcomes"].get(o,0)+1
        for t in r.get("topics") or []:
            t=str(t).strip()
            if t:g["topics"][t]=g["topics"].get(t,0)+1
    out=[]
    for g in groups.values():
        if g["n"]<min_samples:continue
        top_rounds=sorted(g["rounds"].items(),key=lambda kv:(-kv[1],kv[0]))[:5]
        top_topics=sorted(g["topics"].items(),key=lambda kv:(-kv[1],kv[0]))[:8]
        out.append({"company":g["company"],"role":g["role"],"samples":g["n"],"evidence":evidence_label(g["n"]),
                    "topRounds":[{"round":k,"n":v} for k,v in top_rounds],"topTopics":[{"topic":k,"n":v} for k,v in top_topics],
                    "difficulty":g["difficulty"],"outcomes":g["outcomes"]})
    return sorted(out,key=lambda x:(-x["samples"],x["company"].lower(),x["role"].lower()))
