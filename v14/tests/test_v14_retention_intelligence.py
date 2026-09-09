import json
from datetime import datetime, timedelta
from pathlib import Path

import beta_ops, retention_engine, server


def test_process_intelligence_hides_small_groups(tmp_path, monkeypatch):
    beta_ops.PUBLIC_DB=str(tmp_path/'public.db')
    monkeypatch.delenv('SUPABASE_SERVICE_ROLE_KEY',raising=False)
    monkeypatch.setenv('PROCESS_INTELLIGENCE_MIN_SAMPLES','5')
    for i in range(4):
        out=beta_ops.save_process_report({'company':'Acme','role':'Data Analyst','roundType':'sql','outcome':'passed','difficulty':'medium','topics':['SQL','windows']},f'client-{i}')
        assert out['ok']
    intel=beta_ops.process_intelligence()
    assert intel['reportCount']==4
    assert intel['groups']==[]
    beta_ops.save_process_report({'company':'Acme','role':'Data Analyst','roundType':'case','outcome':'rejected','difficulty':'hard','topics':['metrics']},'client-5')
    intel=beta_ops.process_intelligence()
    assert len(intel['groups'])==1
    g=intel['groups'][0]
    assert g['samples']==5 and g['evidence']=='early'
    assert any(x['topic']=='SQL' for x in g['topTopics'])


def test_retention_calibration_requires_evidence():
    small=retention_engine.calibrate_mock_to_outcomes([
      {'mockScore':82,'outcome':'passed'},{'mockScore':64,'outcome':'rejected'}
    ])
    assert small['samples']==2 and small['evidence']=='insufficient'
    assert 'descriptiveBar' not in small
    bigger=retention_engine.calibrate_mock_to_outcomes([
      {'mockScore':84,'outcome':'passed'},{'mockScore':81,'outcome':'passed'},{'mockScore':77,'outcome':'passed'},
      {'mockScore':63,'outcome':'rejected'},{'mockScore':67,'outcome':'rejected'}
    ])
    assert bigger['samples']==5
    assert bigger['descriptiveBar'] is not None
    assert bigger['passedAvg']>bigger['failedAvg']


def test_weekly_overview_and_outcome_pairing(tmp_path, monkeypatch):
    monkeypatch.setattr(server,'APP_DB',str(tmp_path/'v14.db'));server.init_app_db()
    now=datetime.utcnow();interview=(now.date()+timedelta(days=10)).isoformat()
    con=server.connect_app()
    con.execute("INSERT INTO applications(application_id,company_name,role_title,interview_date,daily_minutes,profile_json,study_plan_json,status,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?)",('app1','Acme','Data Analyst',interview,45,'{}','{}','technical',now.isoformat(),now.isoformat()))
    sess_time=(now-timedelta(days=2)).isoformat();out_time=(now-timedelta(days=1)).isoformat();week=retention_engine.iso_week_key(now)
    con.execute("INSERT INTO sessions(session_id,application_id,started_at,completed_at,mode,strictness,interview_style,score,verdict) VALUES(?,?,?,?,?,?,?,?,?)",('s1','app1',sess_time,sess_time,'full','realistic','real',78,'PASS'))
    con.execute("INSERT INTO weekly_benchmarks(session_id,application_id,week_key,started_at,completed_at,score,verdict,skill_scores_json,readiness_json) VALUES(?,?,?,?,?,?,?,?,?)",('s1','app1',week,sess_time,sess_time,78,'PASS',json.dumps({'sql':80}),json.dumps([])))
    con.execute("INSERT INTO interview_outcomes(application_id,company_name,role_title,round_type,outcome,topics_json,created_at) VALUES(?,?,?,?,?,?,?)",('app1','Acme','Data Analyst','sql','passed',json.dumps(['SQL']),out_time))
    con.commit();con.close()
    w=server.weekly_overview('app1')
    assert w['benchmarkDue'] is False
    assert w['trend']['count']==1
    assert w['calibration']['samples']==1
    assert w['calibration']['pairs'][0]['mockScore']==78


def test_next_action_prioritizes_due_revision():
    action=retention_engine.choose_next_action({'interviewDate':(datetime.utcnow().date()+timedelta(days=8)).isoformat()},[],[{'concept':'window_rank','due':True}],{'overdue':0}, {'score':70})
    assert action['type']=='revision'
    assert action['concept']=='window_rank'


def test_v14_assets_exist():
    root=Path(__file__).parents[1]
    for rel in ['retention_engine.py','static/v14.js','static/v14.css']:
        assert (root/rel).exists()
    html=(root/'static/index.html').read_text()
    assert 'view-weekly' in html and '/v14.js' in html
