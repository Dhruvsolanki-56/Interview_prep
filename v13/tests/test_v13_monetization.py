import hashlib, hmac, json, os, sys, tempfile, time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
import monetization_engine as m


def setup_function(_):
    tmp=tempfile.NamedTemporaryFile(delete=False,suffix='.db');tmp.close()
    m.DB_PATH=tmp.name
    for k in [
        'MONETIZATION_ENABLED','MONETIZATION_ENFORCED','HOSTED_MODE','STRIPE_SECRET_KEY','STRIPE_WEBHOOK_SECRET',
        'STRIPE_PRICE_INTERVIEW_WEEK','STRIPE_PRICE_PRO_MONTHLY','STRIPE_PRICE_FOUNDING_ANNUAL','SUPABASE_URL','SUPABASE_SERVICE_ROLE_KEY'
    ]: os.environ.pop(k,None)


def test_monetization_off_does_not_break_existing_product():
    out=m.authorize('guest-a','takehome',consume=True)
    assert out['allowed'] is True
    assert out['reason']=='monetization_not_enforced'


def test_enforced_free_tier_blocks_premium_and_meters_mixed_mock():
    os.environ['MONETIZATION_ENABLED']='1';os.environ['MONETIZATION_ENFORCED']='1'
    assert m.authorize('guest-a','takehome')['allowed'] is False
    first=m.authorize('guest-a','mixed_mock',consume=True)
    second=m.authorize('guest-a','mixed_mock',consume=True)
    assert first['allowed'] is True
    assert second['allowed'] is False
    assert second['reason']=='free_limit_reached'


def test_interview_week_unlocks_premium_surfaces():
    os.environ['MONETIZATION_ENABLED']='1';os.environ['MONETIZATION_ENFORCED']='1'
    m.grant('guest-a','interview_week',days=10,source='test')
    out=m.authorize('guest-a','takehome')
    assert out['allowed'] is True
    assert out['billing']['plan']=='interview_week'


def test_checkout_cannot_charge_when_payments_disabled():
    os.environ['STRIPE_SECRET_KEY']='sk_test_fake';os.environ['STRIPE_PRICE_INTERVIEW_WEEK']='price_fake'
    out=m.checkout('guest-a','interview_week',base_url='http://localhost:8000')
    assert 'not enabled' in out['error'].lower()


def test_pro_checkout_requires_account_before_stripe_network_call():
    os.environ['MONETIZATION_ENABLED']='1';os.environ['STRIPE_SECRET_KEY']='sk_test_fake';os.environ['STRIPE_PRICE_PRO_MONTHLY']='price_fake'
    out=m.checkout('guest-a','pro',user=None,base_url='http://localhost:8000')
    assert out['requiresAuth'] is True
    assert 'Sign in' in out['error']


def test_webhook_signature_verification_and_idempotency():
    os.environ['STRIPE_WEBHOOK_SECRET']='whsec_test'
    event={'id':'evt_1','type':'checkout.session.completed','data':{'object':{
        'id':'cs_test_1','client_reference_id':m._hash('guest-a'),'metadata':{'subject_hash':m._hash('guest-a'),'plan':'interview_week'},
        'payment_status':'paid','mode':'payment','customer':'cus_1'
    }}}
    raw=json.dumps(event,separators=(',',':')).encode();t=int(time.time())
    sig=hmac.new(b'whsec_test',f'{t}.'.encode()+raw,hashlib.sha256).hexdigest()
    header=f't={t},v1={sig}'
    out=m.handle_webhook(raw,header)
    assert out['ok'] is True
    st=m.public_status('guest-a')
    assert st['premium'] is True and st['plan']=='interview_week'
    dup=m.handle_webhook(raw,header)
    assert dup['duplicate'] is True


def test_bad_webhook_signature_is_rejected():
    os.environ['STRIPE_WEBHOOK_SECRET']='whsec_test'
    raw=b'{"id":"evt_bad","type":"noop","data":{"object":{}}}'
    out=m.handle_webhook(raw,f't={int(time.time())},v1=bad')
    assert out['status']==400


def test_referral_reward_grants_48_hour_pass(monkeypatch):
    monkeypatch.setattr(m,'referral_progress',lambda subject:{'completed':2,'needed':2,'eligible':True})
    out=m.claim_referral_reward('guest-ref')
    assert out['ok'] is True
    st=m.public_status('guest-ref')
    assert st['plan']=='referral_pass' and st['premium'] is True


def test_dev_grant_disabled_when_hosted():
    os.environ['HOSTED_MODE']='1'
    out=m.dev_grant('guest-a')
    assert 'disabled' in out['error'].lower()


def test_schema_contains_server_managed_billing_table():
    schema=(ROOT/'supabase_schema.sql').read_text()
    assert 'billing_entitlements' in schema
    assert 'ENABLE ROW LEVEL SECURITY' in schema


def test_v13_assets_are_loaded():
    html=(ROOT/'static'/'index.html').read_text()
    assert '/v13.js' in html and '/v13.css' in html
    assert 'data-view="plans"' in html
