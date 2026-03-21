import streamlit as st
import requests
import math
import time
import json
from datetime import date

st.set_page_config(
    page_title="⚽ BetAnalyst Pro",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ═══════════════════════════════════════════════════════════
# CSS — Modern Dark UI
# ═══════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif}

/* Hero */
.hero{background:linear-gradient(135deg,#060d1a 0%,#0d1f3c 50%,#071428 100%);
border:1px solid #1e3a5f;border-radius:16px;padding:2rem 2.5rem;
margin-bottom:1.5rem;text-align:center}
.hero h1{color:#fff;margin:0;font-size:2rem;font-weight:700;letter-spacing:-1px}
.hero h1 span{color:#3b82f6}
.hero p{color:#64748b;margin:.5rem 0 0;font-size:.85rem}

/* Sidebar guide */
.guide{background:#0f172a;border:1px solid #1e293b;border-left:3px solid #3b82f6;
border-radius:8px;padding:.9rem 1rem;font-size:.8rem;color:#94a3b8;
line-height:1.9;margin-bottom:.8rem}
.guide a{color:#60a5fa}.guide b{color:#e2e8f0}

/* Maç kartı */
.match-card{background:linear-gradient(135deg,#0f172a,#111827);
border:1px solid #1e293b;border-radius:14px;padding:1.4rem 1.6rem;
margin-bottom:1rem;transition:border-color .2s}
.match-card:hover{border-color:#3b82f6}
.match-vs{font-size:1.15rem;font-weight:600;color:#f1f5f9;
display:flex;align-items:center;gap:.8rem;margin-bottom:.5rem}
.match-vs .league{font-size:.75rem;color:#64748b;font-weight:400}
.match-vs .time{font-size:.8rem;color:#3b82f6;font-weight:500}

/* Stat chips */
.chip{display:inline-flex;align-items:center;gap:4px;
background:#1e293b;border:1px solid #334155;color:#cbd5e1;
padding:3px 10px;border-radius:20px;font-size:.75rem;margin:2px 3px 2px 0}
.chip.green{background:#052e16;border-color:#166534;color:#86efac}
.chip.red{background:#450a0a;border-color:#991b1b;color:#fca5a5}
.chip.blue{background:#0c1a2e;border-color:#1d4ed8;color:#93c5fd}
.chip.yellow{background:#1c1a00;border-color:#854d0e;color:#fde68a}
.chip.purple{background:#1e0a3c;border-color:#6d28d9;color:#c4b5fd}

/* Analiz raporu */
.report-wrap{background:#060d1a;border:1px solid #1e3a5f;border-radius:12px;
padding:0;overflow:hidden;margin-top:.8rem}
.report-header{background:linear-gradient(90deg,#0d1f3c,#0f2847);
padding:.8rem 1.2rem;border-bottom:1px solid #1e3a5f;
display:flex;justify-content:space-between;align-items:center}
.report-header span{color:#60a5fa;font-size:.8rem;font-weight:600;letter-spacing:.05em}
.report-body{padding:1.4rem 1.6rem;font-size:.83rem;color:#e2e8f0;
line-height:1.9;white-space:pre-wrap;max-height:900px;overflow-y:auto;
font-family:'Courier New',monospace}

/* Skor kutuları */
.score-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(85px,1fr));
gap:6px;margin:8px 0}
.score-box{background:#0f172a;border:1px solid #1e293b;border-radius:8px;
padding:8px 6px;text-align:center;cursor:default}
.score-box:hover{border-color:#3b82f6;background:#0d1f3c}
.score-box .score{font-size:1rem;font-weight:700;color:#f1f5f9}
.score-box .prob{font-size:.7rem;color:#64748b;margin-top:2px}
.score-box.top1{border-color:#f59e0b;background:#1c1500}
.score-box.top1 .score{color:#fbbf24}
.score-box.top2{border-color:#3b82f6;background:#0c1a2e}
.score-box.top2 .score{color:#60a5fa}

/* Progress bar */
.pbar-wrap{margin:3px 0}
.pbar-label{display:flex;justify-content:space-between;
font-size:.75rem;color:#94a3b8;margin-bottom:2px}
.pbar{height:6px;border-radius:3px;background:#1e293b;overflow:hidden}
.pbar-fill{height:100%;border-radius:3px;
background:linear-gradient(90deg,#1d4ed8,#3b82f6);transition:width .3s}

/* Combo tablo */
.combo-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:5px;margin:8px 0}
.combo-cell{background:#0f172a;border:1px solid #1e293b;border-radius:6px;
padding:6px 8px;text-align:center}
.combo-cell .key{font-size:.85rem;font-weight:700;color:#e2e8f0}
.combo-cell .val{font-size:.7rem;color:#64748b}
.combo-cell.hot{border-color:#f59e0b;background:#1c1500}
.combo-cell.hot .key{color:#fbbf24}
.combo-cell.warm{border-color:#3b82f6;background:#0c1a2e}
.combo-cell.warm .key{color:#60a5fa}

/* Karar kartları */
.decision-grid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;margin:10px 0}
.decision-card{border-radius:10px;padding:12px 14px}
.decision-card.banko{background:linear-gradient(135deg,#052e16,#064e1b);border:1px solid #166534}
.decision-card.orta{background:linear-gradient(135deg,#0c1a2e,#0d2240);border:1px solid #1d4ed8}
.decision-card.surpriz{background:linear-gradient(135deg,#1e0a3c,#2a0f54);border:1px solid #6d28d9}
.decision-card .dtag{font-size:.7rem;font-weight:700;letter-spacing:.1em;margin-bottom:5px}
.decision-card.banko .dtag{color:#86efac}
.decision-card.orta .dtag{color:#93c5fd}
.decision-card.surpriz .dtag{color:#c4b5fd}
.decision-card .dpick{font-size:.95rem;font-weight:700;color:#f1f5f9;margin:3px 0}
.decision-card .dwhy{font-size:.74rem;color:#94a3b8;line-height:1.5}

/* Risk badge */
.risk{display:inline-block;padding:3px 12px;border-radius:20px;
font-size:.75rem;font-weight:600}
.risk.low{background:#052e16;color:#86efac;border:1px solid #166534}
.risk.mid{background:#1c1500;color:#fde68a;border:1px solid #854d0e}
.risk.high{background:#450a0a;color:#fca5a5;border:1px solid #991b1b}

/* Tab style */
.stTabs [data-baseweb="tab-list"]{gap:4px;background:#0f172a;
border-radius:8px;padding:4px}
.stTabs [data-baseweb="tab"]{border-radius:6px;color:#64748b;
font-size:.82rem;padding:6px 14px}
.stTabs [aria-selected="true"]{background:#1e293b!important;color:#e2e8f0!important}

div[data-testid="stExpander"]{border:1px solid #1e293b!important;
border-radius:10px!important;background:#0f172a!important}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
  <h1>⚽ Bet<span>Analyst</span> Pro</h1>
  <p>football-data.org + Groq Llama 3.3 70B · Maça Özel Derin Analiz · Tamamen Ücretsiz</p>
</div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 🔑 API Anahtarları")
    st.markdown("""<div class="guide">
<b style="color:#60a5fa">Groq API — ÜCRETSİZ</b><br>
→ <a href="https://console.groq.com" target="_blank">console.groq.com</a><br>
→ Google ile giriş → API Keys → Create Key<br>
→ <b>gsk_</b> ile başlar · 500K token/gün<br><br>
<b style="color:#60a5fa">football-data.org — ÜCRETSİZ</b><br>
→ <a href="https://www.football-data.org/client/register" target="_blank">football-data.org/client/register</a><br>
→ E-posta kayıt → Key mail'e gelir
</div>""", unsafe_allow_html=True)

    groq_key = st.text_input("Groq API Key", type="password", placeholder="gsk_...")
    fd_key   = st.text_input("football-data.org Key", type="password", placeholder="Mail'den gelen key...")

    if groq_key and groq_key.startswith("gsk_"):
        st.success("✅ Groq aktif — Llama 3.3 70B")
    elif groq_key:
        st.warning("⚠️ Key 'gsk_' ile başlamalı")

    st.divider()
    LEAGUES = {
        "Premier League 🏴󠁧󠁢󠁥󠁮󠁧󠁿": "PL",  "La Liga 🇪🇸": "PD",
        "Bundesliga 🇩🇪": "BL1",           "Serie A 🇮🇹": "SA",
        "Ligue 1 🇫🇷": "FL1",              "Eredivisie 🇳🇱": "DED",
        "Primeira Liga 🇵🇹": "PPL",         "Champions League ⭐": "CL",
        "Europa League 🌍": "EL",
    }
    sel_label = st.selectbox("Lig", list(LEAGUES.keys()))
    sel_code  = LEAGUES[sel_label]
    sel_date  = st.date_input("Tarih", value=date.today())
    max_match = st.slider("Maks Maç", 1, 15, 8)
    n_form    = st.slider("Form Maç Sayısı", 5, 12, 8)
    n_h2h     = st.slider("H2H Maç Sayısı", 4, 10, 6)
    groq_model= st.selectbox("Groq Model", ["llama-3.3-70b-versatile","llama3-70b-8192"])
    debug     = st.checkbox("🐛 Debug", value=False)
    st.caption("500K token/gün ücretsiz · ~10-15 maç/gün")

# ═══════════════════════════════════════════════════════════
# API KATMANI
# ═══════════════════════════════════════════════════════════
BASE = "https://api.football-data.org/v4"

def fd_get(path, key, params=None):
    try:
        r = requests.get(f"{BASE}{path}", headers={"X-Auth-Token": key},
                         params=params or {}, timeout=15)
        if r.status_code == 429:
            st.warning("⏳ Rate limit — 65sn bekleniyor..."); time.sleep(66)
            r = requests.get(f"{BASE}{path}", headers={"X-Auth-Token": key},
                             params=params or {}, timeout=15)
        if debug: st.caption(f"🐛 {path} → {r.status_code}")
        return r.json() if r.status_code == 200 else {}
    except Exception as e:
        st.error(f"API hatası: {e}"); return {}

def api_matches(key, code, dt, lim):
    d = fd_get(f"/competitions/{code}/matches", key,
               {"dateFrom": dt, "dateTo": dt, "status": "SCHEDULED,TIMED,POSTPONED"})
    return d.get("matches", [])[:lim]

def api_team_matches(key, tid, n):
    return fd_get(f"/teams/{tid}/matches", key,
                  {"status": "FINISHED", "limit": n}).get("matches", [])

def api_h2h(key, mid, n):
    return fd_get(f"/matches/{mid}/head2head", key, {"limit": n}).get("matches", [])

def api_standings(key, code):
    try: return fd_get(f"/competitions/{code}/standings", key)["standings"][0]["table"]
    except: return []

def api_scorers(key, code):
    return fd_get(f"/competitions/{code}/scorers", key, {"limit": 20}).get("scorers", [])

# ═══════════════════════════════════════════════════════════
# VERİ İŞLEME
# ═══════════════════════════════════════════════════════════

def parse_form(matches, tid):
    if not matches: return {}
    ms_r, ht_r = [], []
    gf, gc, htgf, htgc = [], [], [], []
    h_gf=h_gc=h_n=a_gf=a_gc=a_n = 0

    for m in matches:
        hid = m["homeTeam"]["id"]
        fh  = m["score"]["fullTime"]["home"] or 0
        fa  = m["score"]["fullTime"]["away"] or 0
        hh  = (m["score"].get("halfTime") or {}).get("home") or 0
        ha  = (m["score"].get("halfTime") or {}).get("away") or 0
        if hid == tid:
            my_f,op_f,my_h,op_h = fh,fa,hh,ha
            h_gf+=fh; h_gc+=fa; h_n+=1
        else:
            my_f,op_f,my_h,op_h = fa,fh,ha,hh
            a_gf+=fa; a_gc+=fh; a_n+=1
        ms_r.append("G" if my_f>op_f else "B" if my_f==op_f else "M")
        ht_r.append("G" if my_h>op_h else "B" if my_h==op_h else "M")
        gf.append(my_f); gc.append(op_f)
        htgf.append(my_h); htgc.append(op_h)

    n = len(ms_r)
    if n == 0: return {}
    pts5 = sum({"G":3,"B":1,"M":0}[r] for r in ms_r[:5])
    tot_gf  = sum(gf)
    tot_htgf= sum(htgf)
    ht_pct  = round(tot_htgf / tot_gf * 100, 1) if tot_gf > 0 else 45.0
    st_gf   = [f - h for f,h in zip(gf, htgf)]
    st_gc   = [c - h for c,h in zip(gc, htgc)]

    # Seri
    sr = ms_r[0]; sn = 0
    for r in ms_r:
        if r == sr: sn += 1
        else: break

    # Son skorlar listesi
    ms_scores = [f"{f}-{c}" for f,c in zip(gf[:6],gc[:6])]
    ht_scores = [f"{h}-{a}" for h,a in zip(htgf[:6],htgc[:6])]

    return {
        "n": n,
        "form_str":  "-".join(ms_r[:6]),
        "ht_form":   "-".join(ht_r[:5]),
        "pts5": pts5, "pts_pct": round(pts5/15*100,1),
        "avg_gf": round(sum(gf)/n,2),  "avg_gc": round(sum(gc)/n,2),
        "ht_avg_gf": round(sum(htgf)/n,2), "ht_avg_gc": round(sum(htgc)/n,2),
        "st_avg_gf": round(sum(st_gf)/n,2),"st_avg_gc": round(sum(st_gc)/n,2),
        "ht_pct": ht_pct, "st_pct": round(100-ht_pct,1),
        "h_avg_gf": round(h_gf/h_n,2) if h_n else 0,
        "h_avg_gc": round(h_gc/h_n,2) if h_n else 0, "h_n": h_n,
        "a_avg_gf": round(a_gf/a_n,2) if a_n else 0,
        "a_avg_gc": round(a_gc/a_n,2) if a_n else 0, "a_n": a_n,
        "btts":  sum(1 for f,c in zip(gf,gc) if f>0 and c>0),
        "o15":   sum(1 for f,c in zip(gf,gc) if f+c>1),
        "o25":   sum(1 for f,c in zip(gf,gc) if f+c>2),
        "o35":   sum(1 for f,c in zip(gf,gc) if f+c>3),
        "cs":    sum(1 for c in gc if c==0),
        "fts":   sum(1 for f in gf if f==0),
        "streak": f"{sn} maç {'galibiyet' if sr=='G' else 'beraberlik' if sr=='B' else 'mağlubiyet'} serisi",
        "ms_scores": ms_scores,
        "ht_scores": ht_scores,
        "raw_gf": gf, "raw_gc": gc,
        "raw_htgf": htgf, "raw_htgc": htgc,
    }

def parse_h2h(matches, home_id):
    if not matches: return {}
    hw=aw=dr=ht_hw=ht_aw=ht_dr=rev21=rev12=revx1=revx2=btts=o25=o35 = 0
    gl, ms_sc, ht_sc = [], [], []

    for m in matches:
        hid = m["homeTeam"]["id"]
        fh  = m["score"]["fullTime"]["home"] or 0
        fa  = m["score"]["fullTime"]["away"] or 0
        hh  = (m["score"].get("halfTime") or {}).get("home") or 0
        ha  = (m["score"].get("halfTime") or {}).get("away") or 0
        if hid == home_id:
            my_f,op_f,my_h,op_h = fh,fa,hh,ha
        else:
            my_f,op_f,my_h,op_h = fa,fh,ha,hh

        if my_f>op_f: hw+=1
        elif my_f<op_f: aw+=1
        else: dr+=1
        if my_h>op_h: ht_hw+=1
        elif my_h<op_h: ht_aw+=1
        else: ht_dr+=1

        if my_h<op_h and my_f>op_f: rev21+=1
        if my_h>op_h and my_f<op_f: rev12+=1
        if my_h==op_h and my_f>op_f: revx1+=1
        if my_h==op_h and my_f<op_f: revx2+=1

        tot = my_f+op_f
        if my_f>0 and op_f>0: btts+=1
        if tot>2: o25+=1
        if tot>3: o35+=1
        gl.append(tot)
        ms_sc.append(f"{my_f}-{op_f}")
        ht_sc.append(f"{my_h}-{op_h}")

    n = len(matches)
    def p(x): return round(x/n*100,1)
    return {
        "n":n, "hw":hw,"dr":dr,"aw":aw,
        "hw_pct":p(hw),"dr_pct":p(dr),"aw_pct":p(aw),
        "ht_hw":ht_hw,"ht_dr":ht_dr,"ht_aw":ht_aw,
        "ht_hw_pct":p(ht_hw),"ht_dr_pct":p(ht_dr),"ht_aw_pct":p(ht_aw),
        "rev21":rev21,"rev21_pct":p(rev21),
        "rev12":rev12,"rev12_pct":p(rev12),
        "revx1":revx1,"revx1_pct":p(revx1),
        "revx2":revx2,"revx2_pct":p(revx2),
        "avg_goals":round(sum(gl)/n,2),
        "o25":o25,"o25_pct":p(o25),
        "o35":o35,"o35_pct":p(o35),
        "btts":btts,"btts_pct":p(btts),
        "ms_scores":ms_sc, "ht_scores":ht_sc,
    }

def find_standing(table, tid):
    for r in table:
        if r.get("team",{}).get("id")==tid: return r
    return {}

def find_scorer(scorers, tid):
    for s in scorers:
        if s.get("team",{}).get("id")==tid:
            p=s.get("player",{})
            return {"name":p.get("name","?"),"goals":s.get("goals",0),
                    "assists":s.get("assists",0),"played":s.get("playedMatches",0)}
    return {}

# ═══════════════════════════════════════════════════════════
# POISSON MODELİ
# ═══════════════════════════════════════════════════════════

def poi(lam, k):
    lam = max(lam, 0.01)
    return math.exp(-lam) * (lam**k) / math.factorial(k)

def calc_xg(tf, of, is_home):
    base = tf.get("avg_gf", 1.2)
    loc  = tf.get("h_avg_gf" if is_home else "a_avg_gf", base) or base
    opp  = of.get("avg_gc", 1.2) if of else 1.2
    return max(0.30, round(base*0.30 + loc*0.40 + opp*0.30, 3))

def calc_ht_xg(f, full_xg):
    raw = f.get("ht_avg_gf", full_xg*0.43) if f else full_xg*0.43
    return max(0.18, round(raw, 3))

def score_mat(hx, ax, mx=6):
    return {(h,a): round(poi(hx,h)*poi(ax,a)*100, 3)
            for h in range(mx+1) for a in range(mx+1)}

def compute_stats(ms_mat, ht_mat):
    p1 =round(sum(v for(h,a),v in ms_mat.items() if h>a),1)
    px =round(sum(v for(h,a),v in ms_mat.items() if h==a),1)
    p2 =round(100-p1-px,1)
    iy1=round(sum(v for(h,a),v in ht_mat.items() if h>a),1)
    iyx=round(sum(v for(h,a),v in ht_mat.items() if h==a),1)
    iy2=round(100-iy1-iyx,1)
    combos={}
    for ir,ip in [("1",iy1),("X",iyx),("2",iy2)]:
        for mr,mp in [("1",p1),("X",px),("2",p2)]:
            combos[f"{ir}/{mr}"]=round(ip*mp/100,2)
    cs = sorted(combos.items(), key=lambda x:-x[1])
    u25=round(sum(v for(h,a),v in ms_mat.items() if h+a>2),1)
    u35=round(sum(v for(h,a),v in ms_mat.items() if h+a>3),1)
    u45=round(sum(v for(h,a),v in ms_mat.items() if h+a>4),1)
    kg =round(sum(v for(h,a),v in ms_mat.items() if h>0 and a>0),1)
    return {
        "p1":p1,"px":px,"p2":p2,
        "iy1":iy1,"iyx":iyx,"iy2":iy2,
        "combos":cs,
        "u25":u25,"alt25":round(100-u25,1),
        "u35":u35,"alt35":round(100-u35,1),
        "u45":u45,"kg":kg,"kgy":round(100-kg,1),
        "rev21":round(iy2*p1/100,2),
        "rev12":round(iy1*p2/100,2),
    }

# ═══════════════════════════════════════════════════════════
# MAÇA ÖZEL KARAKTER ÇIKARIMI ← Bu anahtar fark
# ═══════════════════════════════════════════════════════════

def extract_match_character(h, a, hf, af, h2h, hxg, axg, h_htxg, a_htxg, stats, h_stand, a_stand, h_sc, a_sc):
    """
    Her maçın kendine özgü hikayesini çıkar.
    Groq bu karakteri kullanarak jenerik değil, bu maça özel analiz yapar.
    """
    chars = []

    # 1. Güç dengesi
    xg_diff = round(hxg - axg, 2)
    if xg_diff > 0.5:
        chars.append(f"EV SAHİBİ AÇIK FAVORİ: xG farkı {xg_diff} (ev {hxg} vs dep {axg})")
    elif xg_diff < -0.5:
        chars.append(f"DEPLASMAN FAVORİ: xG farkı {abs(xg_diff)} (dep {axg} vs ev {hxg})")
    elif abs(xg_diff) <= 0.2:
        chars.append(f"DENGE MAÇI: xG neredeyse eşit ({hxg} vs {axg}), beraberlik ihtimali yüksek")
    else:
        chars.append(f"HAFİF FAVORİ {'ev sahibi' if xg_diff>0 else 'deplasman'}: xG {hxg} vs {axg}")

    # 2. Form trendi
    h_pts = hf.get("pts5",0) if hf else 0
    a_pts = af.get("pts5",0) if af else 0
    if h_pts >= 12: chars.append(f"{h} ÇOK İYİ FORMDA ({h_pts}/15), son 5 maçta dominant")
    elif h_pts <= 4: chars.append(f"{h} KÖTÜ FORMDA ({h_pts}/15), güven kaybı yaşıyor")
    if a_pts >= 12: chars.append(f"{a} ÇOK İYİ FORMDA ({a_pts}/15), deplasmanda güçlü geliy")
    elif a_pts <= 4: chars.append(f"{a} KÖTÜ FORMDA ({a_pts}/15), savunma sorunları var")

    # 3. Savunma/hücum karakteri
    if hf:
        if hf.get("cs",0) >= 3: chars.append(f"{h} SAĞLAM SAVUNMA: son {hf['n']} maçta {hf['cs']} kuru kaldı")
        if hf.get("fts",0) >= 3: chars.append(f"{h} HOL SORUNU: son {hf['n']} maçta {hf['fts']} kez gol atamadı")
        if hf.get("avg_gf",0) >= 2.2: chars.append(f"{h} GOL MAKİNESİ: maç başı {hf['avg_gf']} gol atıyor")
        if hf.get("avg_gc",0) >= 2.0: chars.append(f"{h} SAVUNMA DELIĞI: maç başı {hf['avg_gc']} gol yiyor")
    if af:
        if af.get("cs",0) >= 3: chars.append(f"{a} SAĞLAM SAVUNMA: son {af['n']} maçta {af['cs']} kuru kaldı")
        if af.get("fts",0) >= 3: chars.append(f"{a} HOL SORUNU: son {af['n']} maçta {af['fts']} kez gol atamadı")
        if af.get("avg_gf",0) >= 2.0: chars.append(f"{a} ETKİLİ HÜCUM: maç başı {af['avg_gf']} gol atıyor")
        if af.get("avg_gc",0) >= 2.0: chars.append(f"{a} SAVUNMA DELIĞI: maç başı {af['avg_gc']} gol yiyor")

    # 4. Gol zamanlama — 2/1 & 1/2 için KRİTİK
    h_ht = hf.get("ht_pct",45) if hf else 45
    h_st = hf.get("st_pct",55) if hf else 55
    a_ht = af.get("ht_pct",45) if af else 45
    a_st = af.get("st_pct",55) if af else 55

    if h_st >= 60:
        chars.append(f"{h} 2Y TAKIM: gollerinin %{h_st}'ini 2Y'de atıyor → 2/1 & X/1 için zemin")
    if a_st >= 60:
        chars.append(f"{a} 2Y TAKIM: gollerinin %{a_st}'ini 2Y'de atıyor → 1/2 & X/2 için zemin")
    if h_ht >= 58:
        chars.append(f"{h} ERKEN BASAN TAKIM: gollerinin %{h_ht}'ini İY'de atıyor → İY erken gol bekle")
    if a_ht >= 58:
        chars.append(f"{a} ERKEN BASAN TAKIM: gollerinin %{a_ht}'ini İY'de atıyor")

    # 5. H2H karakteri
    if h2h and h2h.get("n",0) >= 3:
        if h2h.get("hw_pct",0) >= 60:
            chars.append(f"H2H EV ÜSTÜNLÜĞÜ: {h} bu ikilidе {h2h['hw_pct']}% kazanıyor")
        if h2h.get("aw_pct",0) >= 60:
            chars.append(f"H2H DEP ÜSTÜNLÜĞÜ: {a} bu ikilidе {h2h['aw_pct']}% kazanıyor")
        if h2h.get("dr_pct",0) >= 50:
            chars.append(f"H2H BERABERLİK MAÇI: bu ikili %{h2h['dr_pct']} beraberlikle bitiyor")
        if h2h.get("rev21_pct",0) >= 25:
            chars.append(f"H2H 2/1 PATTERN: bu ikilide %{h2h['rev21_pct']} dönüş yaşandı ({h2h['rev21']}/{h2h['n']} maç)")
        if h2h.get("rev12_pct",0) >= 25:
            chars.append(f"H2H 1/2 PATTERN: bu ikilide %{h2h['rev12_pct']} dönüş yaşandı ({h2h['rev12']}/{h2h['n']} maç)")
        if h2h.get("o25_pct",0) >= 70:
            chars.append(f"H2H GOL ZIYAFETI: bu ikili %{h2h['o25_pct']} 2.5 üst bitiriyor")
        if h2h.get("btts_pct",0) >= 65:
            chars.append(f"H2H KG VAR: bu ikili %{h2h['btts_pct']} oranında KG VAR bitiyor")

    # 6. Puan durumu motivasyonu
    if h_stand and a_stand:
        h_pos = h_stand.get("position",10)
        a_pos = a_stand.get("position",10)
        h_pts_total = h_stand.get("points",0)
        a_pts_total = a_stand.get("points",0)
        if h_pos <= 4 and a_pos > 10:
            chars.append(f"MOTİVASYON FARKI: {h} (sıra:{h_pos}) ligin tepesinde, {a} (sıra:{a_pos}) orta grupta")
        if h_pos >= 16:
            chars.append(f"DÜŞME KORKUSU: {h} sıra {h_pos} — ev maçında 3 puan zorunluluğu var")
        if a_pos >= 16:
            chars.append(f"DÜŞME KORKUSU: {a} sıra {a_pos} — deplasmanda direniş beklenir")

    # 7. Golcü etkisi
    if h_sc and h_sc.get("goals",0) >= 10:
        chars.append(f"GOLCÜ GÜÇ: {h_sc['name']} sezonda {h_sc['goals']} gol attı — tehlike unsuru")
    if a_sc and a_sc.get("goals",0) >= 10:
        chars.append(f"GOLCÜ GÜÇ: {a_sc['name']} sezonda {a_sc['goals']} gol attı — deplasmanda tehhlike")

    # 8. Toplam xG değerlendirmesi
    total_xg = round(hxg + axg, 2)
    if total_xg >= 3.2:
        chars.append(f"YÜKSEK xG MAÇI: Toplam xG {total_xg} → Çok gollü maç bekleniyor, 2.5 Üst %{stats['u25']}")
    elif total_xg <= 1.8:
        chars.append(f"DÜŞÜK xG MAÇI: Toplam xG {total_xg} → Sıkışık, az gollü maç bekleniyor")

    return chars

# ═══════════════════════════════════════════════════════════
# GROQ ANALİZ — MAÇA ÖZEL PROMPT
# ═══════════════════════════════════════════════════════════

def build_groq_prompt(h, a, hf, af, h2h, hxg, axg, h_htxg, a_htxg,
                      stats, h_stand, a_stand, h_sc, a_sc, top_ms, top_ht):
    """Bu maça özgü, veriye dayalı prompt oluştur."""

    match_chars = extract_match_character(
        h, a, hf, af, h2h, hxg, axg, h_htxg, a_htxg,
        stats, h_stand, a_stand, h_sc, a_sc
    )

    def fv(d, k, dv=0): return d.get(k, dv) if d else dv
    def pct(x, n): return round(x/n*100, 1) if n else 0

    stand_h = h_stand or {}
    stand_a = a_stand or {}

    prompt = f"""Sen dünyanın en iyi futbol bahis analistlerinden birisin.
Bu maç için SADECE verilen verilere dayanarak, her maça ÖZEL bir analiz yap.
Genel klişe cümleler YASAK. Her cümle bu maçın verisine dayalı olmalı.
Türkçe yaz. Tüm tahminler yüzdeli olmalı.

═══════════════════════════════════════════
MAÇIN TEMEL KARAKTERİ — ÖNCE BU VERİYİ OKU
═══════════════════════════════════════════
{''.join(f"▶ {c}" + chr(10) for c in match_chars)}

═══════════════════════════════════════════
SAYISAL VERİ PAKETİ
═══════════════════════════════════════════

MAÇ: {h} (Ev) vs {a} (Dep)

PUAN DURUMU:
  {h}: Sıra {stand_h.get('position','?')} | {stand_h.get('playedGames','?')} maç | {stand_h.get('won','?')}G {stand_h.get('draw','?')}B {stand_h.get('lost','?')}M | Gol {stand_h.get('goalsFor','?')}-{stand_h.get('goalsAgainst','?')} | {stand_h.get('points','?')} puan
  {a}: Sıra {stand_a.get('position','?')} | {stand_a.get('playedGames','?')} maç | {stand_a.get('won','?')}G {stand_a.get('draw','?')}B {stand_a.get('lost','?')}M | Gol {stand_a.get('goalsFor','?')}-{stand_a.get('goalsAgainst','?')} | {stand_a.get('points','?')} puan

GOL KRALLERİ:
  {h}: {h_sc.get('name','?') if h_sc else '?'} — {h_sc.get('goals',0) if h_sc else 0} gol / {h_sc.get('assists',0) if h_sc else 0} asist ({h_sc.get('played',0) if h_sc else 0} maç)
  {a}: {a_sc.get('name','?') if a_sc else '?'} — {a_sc.get('goals',0) if a_sc else 0} gol / {a_sc.get('assists',0) if a_sc else 0} asist ({a_sc.get('played',0) if a_sc else 0} maç)

{h} FORM (son {fv(hf,'n')} maç):
  MS Seri: {fv(hf,'form_str','?')} | İY Seri: {fv(hf,'ht_form','?')}
  Son MS Skorlar: {' | '.join((hf.get('ms_scores',[]) if hf else [])[:5])}
  Son İY Skorlar: {' | '.join((hf.get('ht_scores',[]) if hf else [])[:5])}
  Genel gol: {fv(hf,'avg_gf')} attı / {fv(hf,'avg_gc')} yedi
  İç saha: {fv(hf,'h_avg_gf')} attı / {fv(hf,'h_avg_gc')} yedi ({fv(hf,'h_n')} maç)
  İY gol: {fv(hf,'ht_avg_gf')} attı / {fv(hf,'ht_avg_gc')} yedi
  2Y gol: {fv(hf,'st_avg_gf')} attı / {fv(hf,'st_avg_gc')} yedi
  GOL ZAMANI: %{fv(hf,'ht_pct',45)} İY — %{fv(hf,'st_pct',55)} 2Y
  KG VAR: {fv(hf,'btts')}/{fv(hf,'n')} | 2.5Üst: {fv(hf,'o25')}/{fv(hf,'n')} | CS: {fv(hf,'cs')}/{fv(hf,'n')} | Gol Atamadı: {fv(hf,'fts')}/{fv(hf,'n')}

{a} FORM (son {fv(af,'n')} maç):
  MS Seri: {fv(af,'form_str','?')} | İY Seri: {fv(af,'ht_form','?')}
  Son MS Skorlar: {' | '.join((af.get('ms_scores',[]) if af else [])[:5])}
  Son İY Skorlar: {' | '.join((af.get('ht_scores',[]) if af else [])[:5])}
  Genel gol: {fv(af,'avg_gf')} attı / {fv(af,'avg_gc')} yedi
  Deplasman: {fv(af,'a_avg_gf')} attı / {fv(af,'a_avg_gc')} yedi ({fv(af,'a_n')} maç)
  İY gol: {fv(af,'ht_avg_gf')} attı / {fv(af,'ht_avg_gc')} yedi
  2Y gol: {fv(af,'st_avg_gf')} attı / {fv(af,'st_avg_gc')} yedi
  GOL ZAMANI: %{fv(af,'ht_pct',45)} İY — %{fv(af,'st_pct',55)} 2Y
  KG VAR: {fv(af,'btts')}/{fv(af,'n')} | 2.5Üst: {fv(af,'o25')}/{fv(af,'n')} | CS: {fv(af,'cs')}/{fv(af,'n')} | Gol Atamadı: {fv(af,'fts')}/{fv(af,'n')}

H2H (son {h2h.get('n',0)} maç):
  MS: {h} {h2h.get('hw',0)}G-{h2h.get('dr',0)}B-{h2h.get('aw',0)}M (%{h2h.get('hw_pct',0)}/%{h2h.get('dr_pct',0)}/%{h2h.get('aw_pct',0)})
  İY: {h} {h2h.get('ht_hw',0)}G-{h2h.get('ht_dr',0)}B-{h2h.get('ht_aw',0)}M (%{h2h.get('ht_hw_pct',0)}/%{h2h.get('ht_dr_pct',0)}/%{h2h.get('ht_aw_pct',0)})
  Son MS: {' | '.join(h2h.get('ms_scores',[])[:6])}
  Son İY: {' | '.join(h2h.get('ht_scores',[])[:6])}
  Gol ort: {h2h.get('avg_goals','?')} | 2.5Üst: %{h2h.get('o25_pct',0)} | KGVAR: %{h2h.get('btts_pct',0)}
  2/1 DÖNÜŞ: {h2h.get('rev21',0)}/{h2h.get('n',0)} maç (%{h2h.get('rev21_pct',0)})
  1/2 DÖNÜŞ: {h2h.get('rev12',0)}/{h2h.get('n',0)} maç (%{h2h.get('rev12_pct',0)})
  X/1 DÖNÜŞ: {h2h.get('revx1',0)}/{h2h.get('n',0)} maç (%{h2h.get('revx1_pct',0)})
  X/2 DÖNÜŞ: {h2h.get('revx2',0)}/{h2h.get('n',0)} maç (%{h2h.get('revx2_pct',0)})

POİSSON xG MODELİ:
  MS-xG: {h}={hxg} | {a}={axg} | Toplam={round(hxg+axg,2)}
  İY-xG: {h}={h_htxg} | {a}={a_htxg}
  MS: 1=%{stats['p1']} X=%{stats['px']} 2=%{stats['p2']}
  İY: 1=%{stats['iy1']} X=%{stats['iyx']} 2=%{stats['iy2']}
  En olası MS: {' | '.join(f"{hg}-{ag}(%{round(v,1)})" for(hg,ag),v in top_ms[:6])}
  En olası İY: {' | '.join(f"{hg}-{ag}(%{round(v,1)})" for(hg,ag),v in top_ht[:5])}
  İY/MS kombo: {' | '.join(f"{k}(%{round(v,1)})" for k,v in stats['combos'][:6])}
  KG VAR=%{stats['kg']} | 2.5Üst=%{stats['u25']} | 3.5Üst=%{stats['u35']}
  Model 2/1=%{stats['rev21']} | Model 1/2=%{stats['rev12']}

═══════════════════════════════════════════
GÖREV: Aşağıdaki 9 başlıkta analiz yaz.
Her başlık bu maçın KENDİNE ÖZGÜ verisini kullanmalı.
"Genel olarak...", "Her iki takım da..." gibi jenerik cümleler YASAK.
Takımların gerçek isimlerini ve gerçek rakamları kullan.
═══════════════════════════════════════════

## 1) EN OLASI İY + MS SKORU
[Önce İY tahmini, sonra MS tahmini. Her biri için %olasılık + bu maçın verisine özgü gerekçe.
"Neden bu skor?" sorusunu: xG, son İY skorları, H2H İY sonuçları, gol zamanlama verisiyle cevapla.]

## 2) SKOR DAĞILIMI
[MS için 8 skor. İY için 4 skor. Her biri için kısa ama bu maça özgü gerekçe.]

## 3) İY / MS TAHMİN DETAYI
[İY 1/X/2 yüzde + bu maçtaki İY dinamiği neden böyle?
MS 1/X/2 yüzde + bu maçtaki ana belirleyici nedir?
En önemli 3 İY/MS kombosu için: "Bu kombo gerçekleşirse şunun için: ..." şeklinde senaryo.
Tüm 9 komboyu tablo olarak ver.]

## 4) GOL SAYISI
[KG VAR/YOK %+ bu iki takımın son maçlardaki KG trendi.
1.5/2.5/3.5/4.5 Üst-Alt yüzde + bu maçın xG ve H2H göz önünde bulundurulduğunda anlam.
İY gol beklentisi (h_htxg + a_htxg) vs 2Y beklentisi ayrıca yorumla.]

## 5) 2/1 – 1/2 DÖNÜŞ (EN KRİTİK — EN DETAYLI YAZ)
[2/1 için:
- Model: %{stats['rev21']} | H2H geçmiş: %{h2h.get('rev21_pct',0)} ({h2h.get('rev21',0)}/{h2h.get('n',0)} maç)
- {h}'ın gol zamanlama verisi: %{fv(hf,'st_pct',55)} 2Y — bu 2Y'de dönüş için ne anlama geliyor?
- {a}'nın İY agresifliği: %{fv(af,'ht_pct',45)} gol İY'de — İY önde bitme ihtimali?
- Senaryo: "İY nasıl biter? Hangi dakikada ne değişir? MS nasıl kapanır?"
- NET SONUÇ: Gerçekçi mi? Bahis değeri var mı?

1/2 için aynı şekilde detaylı yaz.
KESİN KARAR: Hangi dönüş daha olası ve neden?]

## 6) GÜÇLÜ – ZAYIF YÖNLER
[{h} güçlü yönleri ve zayıf yönleri — sadece bu sezonki verilere dayalı.
{a} güçlü yönleri ve zayıf yönleri — sadece bu sezonki verilere dayalı.
Golcü faktörü: Bu maçta fark yaratabilecek isim kim ve neden?]

## 7) VALUE TAHMİNİ
[Model %'si yüksek ama piyasada muhtemelen düşük oranlı olan bahis nedir?
Model ile piyasa arasında en büyük fark nerede? Neden değerli?]

## 8) RİSK SEVİYESİ
[DÜŞÜK / ORTA / YÜKSEK — Bu maçın özelinden gerekçe. Kaç faktör belirsiz?]

## 9) PROFESYONEL TAVSİYELER
🔒 BANKO: [Tahmin] — %[güven] — [Bu maçtaki spesifik gerekçe]
⚡ ORTA: [Tahmin] — %[güven] — [Gerekçe]
💎 SÜRPRİZ: [Tahmin + tahmini oran] — [Pattern gerekçesi]
🎯 SKOR: İY [X-Y] + MS [X-Y] — [Bu spesifik skoru destekleyen veriler]
"""
    return prompt

def groq_analyze(prompt, key, model):
    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.15,
                "max_tokens": 4000,
            },
            timeout=120,
        )
        r.raise_for_status()
        usage = r.json().get("usage", {})
        if debug: st.caption(f"🐛 Token: {usage.get('total_tokens','?')}")
        return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"❌ Groq Hatası: {e}"

# ═══════════════════════════════════════════════════════════
# UI YARDIMCI — İnteraktif İstatistik Bileşenleri
# ═══════════════════════════════════════════════════════════

def render_score_grid(top_scores, label="MS Skor Dağılımı"):
    st.markdown(f"**{label}**")
    html = '<div class="score-grid">'
    for i, ((hg, ag), prob) in enumerate(top_scores[:12]):
        cls = "top1" if i==0 else "top2" if i==1 else "score-box"
        if "top" not in cls: cls = "score-box"
        html += (f'<div class="{cls}">'
                 f'<div class="score">{hg}–{ag}</div>'
                 f'<div class="prob">%{round(prob,1)}</div></div>')
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)

def render_combo_grid(combos):
    st.markdown("**İY/MS Kombinasyonları**")
    html = '<div class="combo-grid">'
    for i, (k, v) in enumerate(combos):
        cls = "combo-cell hot" if i==0 else "combo-cell warm" if i<=2 else "combo-cell"
        html += (f'<div class="{cls}">'
                 f'<div class="key">{k}</div>'
                 f'<div class="val">%{round(v,1)}</div></div>')
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)

def render_pbar(label, val, max_val=100, color="#3b82f6"):
    w = min(100, round(val/max_val*100))
    st.markdown(f"""
    <div class="pbar-wrap">
      <div class="pbar-label"><span>{label}</span><span>%{val}</span></div>
      <div class="pbar"><div class="pbar-fill" style="width:{w}%;background:{color}"></div></div>
    </div>""", unsafe_allow_html=True)

def render_match_card(match, hf, af, h2h, hxg, axg, stats):
    h  = match["homeTeam"]["name"]
    a  = match["awayTeam"]["name"]
    utc= match.get("utcDate","")[:16].replace("T"," ")

    top_ms = sorted(
        {k: v for k, v in zip(
            [(0,0)],  # placeholder
            [0]
        )}.items()
    ) if False else []  # computed below

    # Quick chips
    chips = []
    if hf:
        chips.append(f'<span class="chip {"green" if hf.get("pts5",0)>=9 else "red" if hf.get("pts5",0)<=4 else ""}">'
                     f'🏠 {hf.get("form_str","?")} ({hf.get("pts5",0)}/15)</span>')
    if af:
        chips.append(f'<span class="chip {"green" if af.get("pts5",0)>=9 else "red" if af.get("pts5",0)<=4 else ""}">'
                     f'✈️ {af.get("form_str","?")} ({af.get("pts5",0)}/15)</span>')
    if h2h and h2h.get("n",0)>0:
        chips.append(f'<span class="chip blue">H2H {h2h.get("hw",0)}G-{h2h.get("dr",0)}B-{h2h.get("aw",0)}M</span>')
        if h2h.get("rev21_pct",0) >= 20:
            chips.append(f'<span class="chip yellow">2/1: %{h2h.get("rev21_pct",0)}</span>')
        if h2h.get("rev12_pct",0) >= 20:
            chips.append(f'<span class="chip purple">1/2: %{h2h.get("rev12_pct",0)}</span>')

    xg_str = f'<span class="chip blue">xG: {hxg} – {axg}</span>'
    chips.insert(0, xg_str)

    return "".join(chips), h, a, utc

# ═══════════════════════════════════════════════════════════
# SESSION STATE
# ═══════════════════════════════════════════════════════════
for k in ["matches","mdata","analyses"]:
    if k not in st.session_state:
        st.session_state[k] = [] if k=="matches" else {}

# ═══════════════════════════════════════════════════════════
# ANA LAYOUT
# ═══════════════════════════════════════════════════════════
c1, c2, c3 = st.columns([3,2,2])
with c1: st.markdown(f"**{sel_label}** · {sel_date.strftime('%d.%m.%Y')} · Maks {max_match} maç")
with c2: fetch_btn = st.button("🔍 Maçları Çek", type="primary", use_container_width=True)
with c3: all_btn   = st.button("🤖 Tümünü Analiz Et", use_container_width=True)
st.divider()

# ═══════════════════════════════════════════════════════════
# MAÇLARI ÇEK
# ═══════════════════════════════════════════════════════════
if fetch_btn:
    if not fd_key:
        st.error("⛔ football-data.org API Key giriniz (sol sidebar)."); st.stop()

    with st.spinner("📡 Maçlar çekiliyor..."):
        matches = api_matches(fd_key, sel_code, sel_date.strftime("%Y-%m-%d"), max_match)

    if not matches:
        st.error(f"**{sel_date:%d.%m.%Y} · {sel_label}** için planlanmış maç bulunamadı.")
        st.stop()

    st.session_state.matches = matches
    st.session_state.mdata   = {}
    st.session_state.analyses= {}
    st.success(f"✅ {len(matches)} maç bulundu!")

    with st.spinner("📊 Lig verileri..."):
        standings = api_standings(fd_key, sel_code)
        scorers   = api_scorers(fd_key, sel_code)
        time.sleep(0.5)

    bar = st.progress(0)
    for i, m in enumerate(matches):
        mid = m["id"]
        hid = m["homeTeam"]["id"]
        aid = m["awayTeam"]["id"]
        hn  = m["homeTeam"]["name"]
        an  = m["awayTeam"]["name"]
        bar.progress(i/len(matches), text=f"({i+1}/{len(matches)}) {hn} – {an}")

        hf_r = api_team_matches(fd_key, hid, n_form)
        af_r = api_team_matches(fd_key, aid, n_form)
        hf   = parse_form(hf_r, hid)
        af   = parse_form(af_r, aid)
        time.sleep(0.4)

        h2h_r = api_h2h(fd_key, mid, n_h2h)
        h2h   = parse_h2h(h2h_r, hid)
        time.sleep(0.4)

        h_s  = find_standing(standings, hid)
        a_s  = find_standing(standings, aid)
        h_sc = find_scorer(scorers, hid)
        a_sc = find_scorer(scorers, aid)

        hxg    = calc_xg(hf, af, True)  if hf else 1.2
        axg    = calc_xg(af, hf, False) if af else 1.1
        h_htxg = calc_ht_xg(hf, hxg)
        a_htxg = calc_ht_xg(af, axg)

        ms_mat = score_mat(hxg, axg)
        ht_mat = score_mat(h_htxg, a_htxg, mx=4)
        stats  = compute_stats(ms_mat, ht_mat)
        top_ms = sorted(ms_mat.items(), key=lambda x:-x[1])[:12]
        top_ht = sorted(ht_mat.items(), key=lambda x:-x[1])[:6]

        prompt = build_groq_prompt(
            hn, an, hf, af, h2h, hxg, axg, h_htxg, a_htxg,
            stats, h_s, a_s, h_sc, a_sc, top_ms, top_ht
        )

        st.session_state.mdata[mid] = {
            "match": m, "prompt": prompt,
            "hf": hf, "af": af, "h2h": h2h,
            "hxg": hxg, "axg": axg, "h_htxg": h_htxg, "a_htxg": a_htxg,
            "stats": stats, "top_ms": top_ms, "top_ht": top_ht,
            "h_stand": h_s, "a_stand": a_s,
        }

    bar.progress(1.0); time.sleep(0.4); bar.empty()
    st.success("✅ Veriler hazır!")

# ═══════════════════════════════════════════════════════════
# TOPLU ANALİZ
# ═══════════════════════════════════════════════════════════
if all_btn:
    if not st.session_state.mdata: st.warning("Önce Maçları Çek!")
    elif not groq_key: st.error("⛔ Groq API Key giriniz.")
    else:
        items = list(st.session_state.mdata.items())
        bar2  = st.progress(0)
        for i,(mid,d) in enumerate(items):
            hn = d["match"]["homeTeam"]["name"]
            an = d["match"]["awayTeam"]["name"]
            bar2.progress(i/len(items), text=f"({i+1}/{len(items)}) {hn} – {an}")
            st.session_state.analyses[mid] = groq_analyze(d["prompt"], groq_key, groq_model)
            time.sleep(0.5)
        bar2.progress(1.0); time.sleep(0.3); bar2.empty()
        st.success("✅ Tümü tamamlandı!")

# ═══════════════════════════════════════════════════════════
# MAÇ LİSTESİ — YENİ UI
# ═══════════════════════════════════════════════════════════
if st.session_state.matches:
    st.markdown(f"### 📋 {len(st.session_state.matches)} Maç")

    for m in st.session_state.matches:
        mid  = m["id"]
        hn   = m["homeTeam"]["name"]
        an   = m["awayTeam"]["name"]
        comp = m.get("competition",{}).get("name","")
        utc  = m.get("utcDate","")[:16].replace("T"," ")
        done = mid in st.session_state.analyses
        d    = st.session_state.mdata.get(mid,{})

        with st.expander(f"{'✅' if done else '⚽'}  {hn}  vs  {an}  ·  {utc}  ·  {comp}"):

            if d:
                hf = d.get("hf",{}); af = d.get("af",{})
                h2 = d.get("h2h",{}); stats = d.get("stats",{})
                hxg = d.get("hxg",0); axg = d.get("axg",0)
                top_ms = d.get("top_ms",[]); top_ht = d.get("top_ht",[])

                # ── Üst bilgi satırı ──
                chips_html = ""
                if hf: chips_html += (f'<span class="chip {"green" if hf.get("pts5",0)>=9 else "red" if hf.get("pts5",0)<=4 else ""}">'
                                      f'🏠 {hf.get("form_str","?")} · {hf.get("pts5",0)}/15</span> ')
                if af: chips_html += (f'<span class="chip {"green" if af.get("pts5",0)>=9 else "red" if af.get("pts5",0)<=4 else ""}">'
                                      f'✈️ {af.get("form_str","?")} · {af.get("pts5",0)}/15</span> ')
                chips_html += f'<span class="chip blue">xG: {hxg} – {axg}</span> '
                if h2.get("n",0)>0:
                    chips_html += f'<span class="chip">H2H {h2.get("hw",0)}G-{h2.get("dr",0)}B-{h2.get("aw",0)}M</span> '
                    if h2.get("rev21_pct",0)>=15:
                        chips_html += f'<span class="chip yellow">2/1: %{h2.get("rev21_pct",0)}</span> '
                    if h2.get("rev12_pct",0)>=15:
                        chips_html += f'<span class="chip purple">1/2: %{h2.get("rev12_pct",0)}</span> '
                st.markdown(chips_html, unsafe_allow_html=True)

                # ── 3 Sütun: İstatistikler ──
                tab1, tab2, tab3 = st.tabs(["📊 Model & Skor", "⚽ Form & H2H", "🔄 Dönüş Analizi"])

                with tab1:
                    col_l, col_r = st.columns(2)
                    with col_l:
                        if top_ms:
                            render_score_grid(top_ms, "MS Skor Dağılımı")
                    with col_r:
                        if top_ht:
                            render_score_grid(top_ht[:6], "İY Skor Dağılımı")

                    st.markdown("---")
                    c_a, c_b, c_c = st.columns(3)
                    with c_a:
                        st.markdown("**MS Olasılıkları**")
                        render_pbar(f"1 ({hn})", stats.get('p1',0))
                        render_pbar("X (Beraberlik)", stats.get('px',0), color="#f59e0b")
                        render_pbar(f"2 ({an})", stats.get('p2',0), color="#ef4444")
                    with c_b:
                        st.markdown("**İY Olasılıkları**")
                        render_pbar(f"1 ({hn})", stats.get('iy1',0))
                        render_pbar("X", stats.get('iyx',0), color="#f59e0b")
                        render_pbar(f"2 ({an})", stats.get('iy2',0), color="#ef4444")
                    with c_c:
                        st.markdown("**Gol Tahminleri**")
                        render_pbar("KG VAR", stats.get('kg',0), color="#10b981")
                        render_pbar("2.5 Üst", stats.get('u25',0), color="#8b5cf6")
                        render_pbar("3.5 Üst", stats.get('u35',0), color="#ec4899")

                    st.markdown("---")
                    if stats.get("combos"):
                        render_combo_grid(stats["combos"])

                with tab2:
                    cc1, cc2 = st.columns(2)
                    with cc1:
                        st.markdown(f"**{hn} Form**")
                        if hf:
                            st.markdown(f"""
<span class="chip">MS: {hf.get('form_str','?')}</span>
<span class="chip">İY: {hf.get('ht_form','?')}</span><br>
<span class="chip">Gol Zamanı: %{hf.get('ht_pct',45)}İY / %{hf.get('st_pct',55)}2Y</span><br>
<span class="chip">Att/Yd: {hf.get('avg_gf',0)}/{hf.get('avg_gc',0)}</span>
<span class="chip">KG VAR: {hf.get('btts',0)}/{hf.get('n',0)}</span>
<span class="chip">2.5Üst: {hf.get('o25',0)}/{hf.get('n',0)}</span>
""", unsafe_allow_html=True)
                            st.caption(f"Son MS: {' '.join(hf.get('ms_scores',[])[:5])}")
                            st.caption(f"Son İY: {' '.join(hf.get('ht_scores',[])[:5])}")
                    with cc2:
                        st.markdown(f"**{an} Form**")
                        if af:
                            st.markdown(f"""
<span class="chip">MS: {af.get('form_str','?')}</span>
<span class="chip">İY: {af.get('ht_form','?')}</span><br>
<span class="chip">Gol Zamanı: %{af.get('ht_pct',45)}İY / %{af.get('st_pct',55)}2Y</span><br>
<span class="chip">Att/Yd: {af.get('avg_gf',0)}/{af.get('avg_gc',0)}</span>
<span class="chip">KG VAR: {af.get('btts',0)}/{af.get('n',0)}</span>
<span class="chip">2.5Üst: {af.get('o25',0)}/{af.get('n',0)}</span>
""", unsafe_allow_html=True)
                            st.caption(f"Son MS: {' '.join(af.get('ms_scores',[])[:5])}")
                            st.caption(f"Son İY: {' '.join(af.get('ht_scores',[])[:5])}")

                    if h2.get("n",0) > 0:
                        st.markdown("**H2H Geçmiş**")
                        st.markdown(f"""
<span class="chip">MS: {hn} {h2.get('hw',0)}G-{h2.get('dr',0)}B-{h2.get('aw',0)}M</span>
<span class="chip">İY: {hn} {h2.get('ht_hw',0)}G-{h2.get('ht_dr',0)}B-{h2.get('ht_aw',0)}M</span><br>
<span class="chip">Gol/Maç: {h2.get('avg_goals',0)}</span>
<span class="chip">2.5Üst: %{h2.get('o25_pct',0)}</span>
<span class="chip">KG VAR: %{h2.get('btts_pct',0)}</span>
""", unsafe_allow_html=True)
                        st.caption(f"Son MS: {' | '.join(h2.get('ms_scores',[])[:5])}")
                        st.caption(f"Son İY: {' | '.join(h2.get('ht_scores',[])[:5])}")

                with tab3:
                    c_d, c_e = st.columns(2)
                    with c_d:
                        st.markdown(f"**2/1 Dönüş** *(İY: {an} önde → MS: {hn} kazanır)*")
                        render_pbar("Model İhtimali", stats.get('rev21',0), max_val=30, color="#f59e0b")
                        render_pbar("H2H Tarihsel", h2.get('rev21_pct',0), max_val=50, color="#f59e0b")
                        render_pbar(f"{hn} 2Y Gol Yükü", hf.get('st_pct',55) if hf else 55, color="#10b981")
                        st.caption(f"H2H'de {h2.get('rev21',0)}/{h2.get('n',0)} maçta gerçekleşti")
                    with c_e:
                        st.markdown(f"**1/2 Dönüş** *(İY: {hn} önde → MS: {an} kazanır)*")
                        render_pbar("Model İhtimali", stats.get('rev12',0), max_val=30, color="#8b5cf6")
                        render_pbar("H2H Tarihsel", h2.get('rev12_pct',0), max_val=50, color="#8b5cf6")
                        render_pbar(f"{an} 2Y Gol Yükü", af.get('st_pct',55) if af else 55, color="#ef4444")
                        st.caption(f"H2H'de {h2.get('rev12',0)}/{h2.get('n',0)} maçta gerçekleşti")

            # ── Analiz Butonu & Sonucu ──
            btn_c, _ = st.columns([1,3])
            with btn_c:
                if st.button("🤖 Groq ile Analiz Et", key=f"btn_{mid}", type="primary"):
                    if not groq_key:
                        st.error("⛔ Groq API Key!")
                    elif not d.get("prompt"):
                        st.warning("Önce Maçları Çek!")
                    else:
                        with st.spinner(f"🦙 Llama 70B: {hn} – {an} analiz ediliyor..."):
                            st.session_state.analyses[mid] = groq_analyze(
                                d["prompt"], groq_key, groq_model)

            if mid in st.session_state.analyses:
                st.markdown(
                    f'<div class="report-wrap">'
                    f'<div class="report-header">'
                    f'<span>📊 {hn.upper()} vs {an.upper()} — GROQ LLAMA 3.3 70B ANALİZİ</span>'
                    f'</div>'
                    f'<div class="report-body">{st.session_state.analyses[mid]}</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )
                st.download_button(
                    "⬇️ Analizi İndir (.txt)",
                    data=st.session_state.analyses[mid],
                    file_name=f"{hn}_vs_{an}_{sel_date}.txt",
                    mime="text/plain", key=f"dl_{mid}"
                )

# ═══════════════════════════════════════════════════════════
# BAŞLANGIÇ EKRANI
# ═══════════════════════════════════════════════════════════
else:
    st.markdown("""
    <div class="guide" style="font-size:.88rem;line-height:2.1">
    <b style="color:#60a5fa;font-size:1rem">⚽ BetAnalyst Pro — Tamamen Ücretsiz</b><br><br>
    <b>1) Groq API Key</b> →
    <a href="https://console.groq.com" target="_blank">console.groq.com</a>
    → Google giriş → API Keys → Create → <b>gsk_</b> ile başlar · 500K token/gün<br>
    <b>2) football-data.org Key</b> →
    <a href="https://www.football-data.org/client/register" target="_blank">
    football-data.org/client/register</a>
    → E-posta kayıt → Key mail'e gelir<br><br>
    <b>Her maç için özel analiz içeriği:</b><br>
    ✅ Maç karakteri çıkarımı — "Bu maç neden diğerlerinden farklı?"<br>
    ✅ İY skor + MS skor ayrı ayrı (İY xG + İY form + H2H İY verileriyle)<br>
    ✅ Gol zamanlama (%İY vs %2Y) — 2/1 & 1/2 dönüş analizinin temeli<br>
    ✅ 2/1 & 1/2: Model + H2H + gol zamanlama + senaryo birlikte<br>
    ✅ X/1 & X/2 dönüş takibi (H2H)<br>
    ✅ Her maç için unique veri → jenerik cümle yok<br>
    ✅ Interaktif UI: Skor grid, progress bar, tab layout, renk kodlaması
    </div>
    """, unsafe_allow_html=True)
