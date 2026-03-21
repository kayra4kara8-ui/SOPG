import streamlit as st
import requests
import math
import time
from datetime import date

st.set_page_config(page_title="⚽ BetAnalyst Pro", page_icon="⚽",
                   layout="wide", initial_sidebar_state="expanded")

FD_KEY   = "5cc88bf0dbac4fb699482886eb4c2270"
GROQ_KEY = "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"

# ══════════════════════════════════════════════════════════════════
# CSS
# ══════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Inter:wght@300;400;500;600;700;800&display=swap');
*{box-sizing:border-box}
html,body,[class*="css"]{font-family:'Inter',sans-serif}

/* ── HERO ── */
.hero{
  background:linear-gradient(160deg,#05080f 0%,#0a1628 60%,#071420 100%);
  border:1px solid #0f2a45;border-radius:20px;padding:2rem 2.5rem;
  margin-bottom:1.5rem;text-align:center;position:relative;overflow:hidden
}
.hero::before{content:'';position:absolute;top:-60px;left:50%;transform:translateX(-50%);
width:300px;height:300px;background:radial-gradient(circle,#00e5a015 0%,transparent 70%)}
.hero h1{color:#fff;margin:0;font-size:2rem;font-weight:800;letter-spacing:-1.5px}
.hero h1 span{color:#00e5a0}
.hero p{color:#3a5570;margin:.5rem 0 0;font-size:.82rem}

/* ── VS KART (Ana karşılaştırma bloğu) ── */
.vs-wrapper{
  background:linear-gradient(160deg,#060d1c 0%,#0a1628 100%);
  border:1px solid #0f2a45;border-radius:20px;overflow:hidden;margin-bottom:1.2rem
}
.vs-header{
  display:grid;grid-template-columns:1fr auto 1fr;
  align-items:center;padding:1.4rem 1.8rem;
  background:linear-gradient(90deg,#071628 0%,#040b14 50%,#071628 100%);
  border-bottom:1px solid #0f2a45;gap:1rem
}
.vs-team{text-align:center}
.vs-team .t-name{font-size:1.15rem;font-weight:800;color:#e2e8f0;letter-spacing:-.3px}
.vs-team .t-league{font-size:.68rem;color:#2a4060;margin-top:3px}
.vs-team.home .t-name{color:#60a5fa}
.vs-team.away .t-name{color:#f87171}
.vs-middle{text-align:center}
.vs-badge{
  background:#0a1628;border:1px solid #1a3050;border-radius:12px;
  padding:8px 16px;display:inline-block
}
.vs-badge .vb-vs{font-size:.7rem;color:#1a3050;font-weight:700;letter-spacing:.15em}
.vs-badge .vb-time{font-size:1rem;font-weight:700;color:#00e5a0;
font-family:'JetBrains Mono',monospace;display:block;margin-top:2px}
.vs-badge .vb-date{font-size:.65rem;color:#2a4060;margin-top:1px}

/* ── XG GÖSTERGE ── */
.xg-bar-section{padding:1.2rem 1.8rem;border-bottom:1px solid #0a1e30}
.xg-bar-wrap{display:flex;align-items:center;gap:0;height:32px;border-radius:8px;overflow:hidden;margin:8px 0}
.xg-bar-home{height:100%;display:flex;align-items:center;justify-content:flex-end;
padding-right:10px;background:linear-gradient(90deg,#1d4ed8,#2563eb);
font-size:.82rem;font-weight:700;color:#bfdbfe;font-family:'JetBrains Mono',monospace;
transition:width .5s}
.xg-bar-mid{background:#040b14;padding:0 8px;display:flex;align-items:center;
font-size:.6rem;color:#1a3050;font-weight:700;white-space:nowrap;height:100%}
.xg-bar-away{height:100%;display:flex;align-items:center;
padding-left:10px;background:linear-gradient(90deg,#dc2626,#ef4444);
font-size:.82rem;font-weight:700;color:#fecaca;font-family:'JetBrains Mono',monospace;
transition:width .5s}
.xg-label{display:flex;justify-content:space-between;font-size:.68rem;color:#2a4060;margin-top:3px}

/* ── İKİ SÜTUN VERİ PANEL ── */
.data-panel{display:grid;grid-template-columns:1fr 1fr;border-bottom:1px solid #0a1e30}
.dp-col{padding:1.2rem 1.8rem}
.dp-col.home-col{border-right:1px solid #0a1e30}
.dp-section-title{font-size:.62rem;font-weight:700;letter-spacing:.12em;
text-transform:uppercase;color:#1a3050;margin-bottom:8px;padding-bottom:4px;
border-bottom:1px solid #0a1e30}
.dp-row{display:flex;justify-content:space-between;align-items:center;
padding:4px 0;border-bottom:1px solid #050d18}
.dp-row .dr-label{font-size:.72rem;color:#3a5570}
.dp-row .dr-val{font-size:.78rem;font-weight:600;color:#c0cfe0;
font-family:'JetBrains Mono',monospace}
.dp-row .dr-val.good{color:#34d399}
.dp-row .dr-val.bad{color:#f87171}
.dp-row .dr-val.warn{color:#fbbf24}

/* Form sekmesi — harf kutucukları */
.form-badges{display:flex;gap:4px;flex-wrap:wrap;margin:4px 0}
.fb{width:26px;height:26px;border-radius:5px;display:flex;align-items:center;
justify-content:center;font-size:.72rem;font-weight:700}
.fb.g{background:#052e16;color:#34d399;border:1px solid #166534}
.fb.b{background:#1c1a00;color:#fbbf24;border:1px solid #854d0e}
.fb.m{background:#450a0a;color:#f87171;border:1px solid #991b1b}

/* Son skorlar */
.score-list{display:flex;gap:5px;flex-wrap:wrap;margin:4px 0}
.sc-badge{background:#0a1628;border:1px solid #0f2a45;border-radius:5px;
padding:3px 7px;font-size:.72rem;font-weight:600;color:#c0cfe0;
font-family:'JetBrains Mono',monospace}
.sc-badge.iy{border-color:#1a3050;color:#6b7280}

/* ── ORTA VS PANEL ── */
.vs-compare{padding:1.2rem 1.8rem;border-bottom:1px solid #0a1e30}
.vc-row{display:grid;grid-template-columns:1fr 80px 1fr;gap:8px;
align-items:center;padding:5px 0;border-bottom:1px solid #050d18}
.vc-row:last-child{border:none}
.vc-home{text-align:right}
.vc-away{text-align:left}
.vc-label{text-align:center;font-size:.65rem;color:#2a4060;font-weight:600;
letter-spacing:.05em;text-transform:uppercase}
.vc-val{font-size:.85rem;font-weight:700;font-family:'JetBrains Mono',monospace}
.vc-val.better{color:#34d399}
.vc-val.worse{color:#6b7280}
.vc-val.equal{color:#fbbf24}

/* ── OLASILİK PANEL ── */
.prob-panel{padding:1.2rem 1.8rem;border-bottom:1px solid #0a1e30}
.ms-trio{display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin:10px 0}
.ms-box{background:#0a1628;border:1px solid #0f2a45;border-radius:10px;
padding:10px 8px;text-align:center}
.ms-box.fav-home{border-color:#2563eb;background:#070d1f}
.ms-box.fav-away{border-color:#dc2626;background:#1a0505}
.ms-box.fav-draw{border-color:#d97706;background:#140e00}
.ms-box .mb-label{font-size:.6rem;color:#2a4060;text-transform:uppercase;
letter-spacing:.1em;margin-bottom:4px}
.ms-box .mb-name{font-size:.65rem;color:#3a5570;margin-top:2px;
white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.ms-box .mb-pct{font-size:1.5rem;font-weight:800;font-family:'JetBrains Mono',monospace}
.fav-home .mb-pct{color:#60a5fa}
.fav-away .mb-pct{color:#f87171}
.fav-draw .mb-pct{color:#fbbf24}
.default .mb-pct{color:#4a6080}

/* ── SKOR DAĞILIMI ── */
.skor-panel{padding:1.2rem 1.8rem;border-bottom:1px solid #0a1e30}
.skor-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:6px;margin:8px 0}
.skor-box{background:#0a1628;border:1px solid #0f2a45;border-radius:8px;
padding:8px 6px;text-align:center;cursor:default}
.skor-box .sb-score{font-size:1.05rem;font-weight:700;color:#c0cfe0;
font-family:'JetBrains Mono',monospace}
.skor-box .sb-pct{font-size:.62rem;color:#2a4060;margin-top:2px}
.skor-box.rank1{border-color:#f59e0b;background:#0f0900}
.skor-box.rank1 .sb-score{color:#fbbf24}
.skor-box.rank1 .sb-pct{color:#92700a}
.skor-box.rank2{border-color:#2563eb;background:#040d1f}
.skor-box.rank2 .sb-score{color:#60a5fa}
.skor-box.rank2 .sb-pct{color:#1e3a7a}
.skor-box.rank3{border-color:#16a34a;background:#040f09}
.skor-box.rank3 .sb-score{color:#4ade80}

/* ── İY/MS KOMBOLAR ── */
.combo-panel{padding:1.2rem 1.8rem;border-bottom:1px solid #0a1e30}
.combo-title{font-size:.62rem;color:#2a4060;font-weight:700;
letter-spacing:.12em;text-transform:uppercase;margin-bottom:10px}
.combo-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:6px}
.combo-cell{background:#0a1628;border:1px solid #0f2a45;border-radius:8px;
padding:8px 6px;text-align:center}
.combo-cell .cc-key{font-size:.95rem;font-weight:800;font-family:'JetBrains Mono',monospace;
color:#6b7280}
.combo-cell .cc-pct{font-size:.68rem;color:#1a3050;margin-top:2px}
.combo-cell .cc-desc{font-size:.55rem;color:#162030;margin-top:1px}
.combo-cell.top1{border-color:#f59e0b;background:#0f0900}
.combo-cell.top1 .cc-key{color:#fbbf24}
.combo-cell.top1 .cc-pct{color:#92700a}
.combo-cell.top2{border-color:#2563eb;background:#040d1f}
.combo-cell.top2 .cc-key{color:#60a5fa}
.combo-cell.top2 .cc-pct{color:#1e3a7a}
.combo-cell.top3{border-color:#16a34a;background:#040f09}
.combo-cell.top3 .cc-key{color:#4ade80}

/* ── DÖNÜŞ PANEL ── */
.donus-panel{padding:1.2rem 1.8rem;border-bottom:1px solid #0a1e30}
.donus-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.donus-card{background:#0a1628;border:1px solid #0f2a45;border-radius:12px;padding:12px 14px}
.donus-card.hot21{border-color:#f59e0b;background:#0c0900}
.donus-card.hot12{border-color:#8b5cf6;background:#08050f}
.donus-card .dc-title{font-size:.65rem;font-weight:700;letter-spacing:.08em;
text-transform:uppercase;margin-bottom:6px}
.donus-card.hot21 .dc-title{color:#f59e0b}
.donus-card.hot12 .dc-title{color:#8b5cf6}
.donus-card .dc-title{color:#1a3050}
.donus-card .dc-explain{font-size:.7rem;color:#2a4060;margin-bottom:8px;line-height:1.5}
.donus-row{display:flex;justify-content:space-between;align-items:center;
padding:3px 0;border-bottom:1px solid #050d18}
.donus-row:last-child{border:none}
.donus-row .dr-lbl{font-size:.65rem;color:#2a4060}
.donus-row .dr-v{font-size:.82rem;font-weight:700;font-family:'JetBrains Mono',monospace}

/* ── TAHMIN PANEL ── */
.tahmin-panel{padding:1.2rem 1.8rem;border-bottom:1px solid #0a1e30}
.pred-card{border-radius:10px;padding:12px 14px;margin:6px 0;
display:flex;align-items:flex-start;gap:10px}
.pred-card.banko{background:#040f09;border:1px solid #166534}
.pred-card.orta{background:#040d1f;border:1px solid #1d4ed8}
.pred-card.risky{background:#0f0900;border:1px solid #9a3412}
.pred-card.skor{background:#08050f;border:1px solid #6d28d9}
.pred-icon{font-size:1.1rem;margin-top:1px}
.pred-body .pt{font-size:.6rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase}
.pred-card.banko .pt{color:#34d399}
.pred-card.orta  .pt{color:#60a5fa}
.pred-card.risky .pt{color:#fb923c}
.pred-card.skor  .pt{color:#c4b5fd}
.pred-body .pp{font-size:.88rem;font-weight:700;color:#e2e8f0;margin:2px 0;
font-family:'JetBrains Mono',monospace}
.pred-body .pw{font-size:.7rem;color:#3a5570;line-height:1.5}

/* ── ANALİZ METNİ ── */
.analiz-panel{padding:1.2rem 1.8rem}
.analiz-title{font-size:.62rem;color:#2a4060;font-weight:700;
letter-spacing:.12em;text-transform:uppercase;margin-bottom:8px}
.analiz-text{font-size:.8rem;color:#3a5570;line-height:1.9;
white-space:pre-wrap;max-height:250px;overflow-y:auto}

/* ── GOL METRİKLER ── */
.gol-panel{padding:1.2rem 1.8rem;border-bottom:1px solid #0a1e30}
.gol-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}
.gol-box{background:#0a1628;border:1px solid #0f2a45;border-radius:10px;
padding:10px 8px;text-align:center}
.gol-box .gb-label{font-size:.6rem;color:#2a4060;text-transform:uppercase;
letter-spacing:.08em;margin-bottom:4px}
.gol-box .gb-val{font-size:1.2rem;font-weight:800;font-family:'JetBrains Mono',monospace}
.gol-box .gb-sub{font-size:.62rem;color:#2a4060;margin-top:2px}
.gol-box.high .gb-val{color:#34d399}
.gol-box.mid .gb-val{color:#fbbf24}
.gol-box.low .gb-val{color:#f87171}

/* ── H2H PANEL ── */
.h2h-panel{padding:1.2rem 1.8rem;border-bottom:1px solid #0a1e30}
.h2h-score-list{display:flex;flex-wrap:wrap;gap:5px;margin:6px 0}
.h2h-sc{background:#0a1628;border:1px solid #0f2a45;border-radius:5px;
padding:3px 8px;font-size:.75rem;font-weight:600;color:#c0cfe0;
font-family:'JetBrains Mono',monospace}
.h2h-sc.iy{border-color:#0a1e30;color:#3a5570}

/* ── DISCLAIMER ── */
.disclaimer{font-size:.65rem;color:#1a3050;text-align:center;
padding:8px;border-top:1px solid #0a1e30}

/* Streamlit overrides */
div[data-testid="stExpander"]{
  border:1px solid #0f2a45!important;border-radius:16px!important;
  background:#060d1c!important;overflow:hidden}
div[data-testid="stExpander"] summary{background:#060d1c!important}
.stTabs [data-baseweb="tab-list"]{background:#060d1c;padding:4px;gap:4px;border-radius:8px}
.stTabs [data-baseweb="tab"]{border-radius:6px;color:#2a4060;font-size:.78rem;padding:5px 12px}
.stTabs [aria-selected="true"]{background:#0a1628!important;color:#00e5a0!important}
button[kind="primary"]{background:linear-gradient(90deg,#0ea5e9,#00e5a0)!important;
color:#060d1c!important;font-weight:700!important;border:none!important;border-radius:8px!important}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
  <h1>⚽ Bet<span>Analyst</span> Pro</h1>
  <p>football-data.org · Groq Llama 3.3 70B · Profesyonel VS Analiz</p>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## ⚙️ Filtreler")
    st.success("✅ API key'ler hazır")

    # ── Ücretsiz planda çalışan ligler (football-data.org) ──
    # 2. ligler ücretli plan gerektirir (49€/ay) — sadece 1. ligler ücretsiz
    LEAGUE_GROUPS = {
        "🌍 Avrupa Kulüp": {
            "UEFA Champions League ⭐": "CL",
            "UEFA Europa League":       "EL",
            "UEFA Conference League":   "ECL",
        },
        "🏴󠁧󠁢󠁥󠁮󠁧󠁿 İngiltere": {
            "Premier League":           "PL",
            "Championship (2. Lig) ✅": "ELC",  # İngiltere 2. ligi ücretsiz!
            "FA Cup":                   "FAC",
        },
        "🇪🇸 İspanya": {
            "La Liga":                  "PD",
        },
        "🇩🇪 Almanya": {
            "Bundesliga":               "BL1",
        },
        "🇮🇹 İtalya": {
            "Serie A":                  "SA",
        },
        "🇫🇷 Fransa": {
            "Ligue 1":                  "FL1",
        },
        "🇳🇱 Hollanda": {
            "Eredivisie":               "DED",
        },
        "🇵🇹 Portekiz": {
            "Primeira Liga":            "PPL",
        },
        "🇧🇷 Brezilya": {
            "Série A":                  "BSA",
        },
        "🌐 Milli Takım": {
            "FIFA World Cup":           "WC",
            "UEFA Avrupa Şampiyonası":  "EC",
        },
    }

    sel_group = st.selectbox("Kategori", list(LEAGUE_GROUPS.keys()))
    sel_label = st.selectbox("Lig", list(LEAGUE_GROUPS[sel_group].keys()))
    sel_code  = LEAGUE_GROUPS[sel_group][sel_label].split("#")[0].strip()

    st.info(
        "ℹ️ **2. ligler neden yok?**\n\n"
        "football-data.org ücretsiz planda yalnızca belirli 1. ligler ve "
        "İngiltere Championship dahil. 2. Bundesliga, Serie B, Ligue 2, "
        "Segunda División vb. 49€/ay ücretli plan gerektiriyor. "
        "Ücretsiz planda mevcut olan ligler yukarıda listelenmiştir."
    )
    sel_date  = st.date_input("Tarih", value=date.today())
    max_match = st.slider("Maks Maç", 1, 15, 8)
    n_form    = st.slider("Form Maç Sayısı", 5, 12, 8)
    n_h2h     = st.slider("H2H Maç Sayısı", 4, 10, 6)
    groq_model = st.selectbox(
        "Groq Modeli",
        [
            "llama-3.1-8b-instant",       # ⚡ En hızlı (önerilen)
            "llama-3.3-70b-versatile",    # 🧠 En kaliteli (yavaş)
            "llama3-70b-8192",            # 🧠 Kaliteli (yavaş)
        ],
        help="llama-3.1-8b-instant çok daha hızlı ve rate limit yok gibi. 70B daha derin analiz yapar ama yavaş."
    )
    debug     = st.checkbox("🐛 Debug", value=False)

# ══════════════════════════════════════════════════════════════════
# API
# ══════════════════════════════════════════════════════════════════
BASE = "https://api.football-data.org/v4"

def fd_get(path, params=None):
    try:
        r = requests.get(f"{BASE}{path}", headers={"X-Auth-Token": FD_KEY},
                         params=params or {}, timeout=15)
        if r.status_code == 429:
            st.warning("⏳ Rate limit — 65sn..."); time.sleep(66)
            r = requests.get(f"{BASE}{path}", headers={"X-Auth-Token": FD_KEY},
                             params=params or {}, timeout=15)
        if debug: st.caption(f"🐛 {path} → {r.status_code}")
        return r.json() if r.status_code == 200 else {}
    except Exception as e:
        st.error(f"API: {e}"); return {}

def api_matches(code, dt, lim):
    d = fd_get(f"/competitions/{code}/matches",
               {"dateFrom": dt, "dateTo": dt, "status": "SCHEDULED,TIMED,POSTPONED"})
    return d.get("matches", [])[:lim]

def api_team_matches(tid, n):
    return fd_get(f"/teams/{tid}/matches",
                  {"status": "FINISHED", "limit": n}).get("matches", [])

def api_h2h(mid, n):
    return fd_get(f"/matches/{mid}/head2head", {"limit": n}).get("matches", [])

def api_standings(code):
    try: return fd_get(f"/competitions/{code}/standings")["standings"][0]["table"]
    except: return []

def api_scorers(code):
    return fd_get(f"/competitions/{code}/scorers", {"limit": 20}).get("scorers", [])

# ══════════════════════════════════════════════════════════════════
# VERİ İŞLEME
# ══════════════════════════════════════════════════════════════════

def _calc_score_freq(score_pairs):
    """Skor listesinden frekans sözlüğü çıkar — {(h,a): count}"""
    from collections import Counter
    c = Counter(score_pairs)
    total = sum(c.values())
    return {f"{h}-{a}": {"count": cnt, "pct": round(cnt/total*100, 1)}
            for (h, a), cnt in sorted(c.items(), key=lambda x: -x[1])}

def parse_form(matches, tid):
    if not matches: return {}
    ms_r, ht_r = [], []
    gf, gc, htgf, htgc = [], [], [], []
    h_gf=h_gc=h_n=a_gf=a_gc=a_n = 0
    for m in matches:
        hid = m["homeTeam"]["id"]
        fh  = m["score"]["fullTime"]["home"]  or 0
        fa  = m["score"]["fullTime"]["away"]  or 0
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
    pts5   = sum({"G":3,"B":1,"M":0}[r] for r in ms_r[:5])
    tot_gf = sum(gf); tot_ht = sum(htgf)
    ht_pct = round(tot_ht / tot_gf * 100, 1) if tot_gf > 0 else 45.0
    st_gf  = [f - h for f, h in zip(gf, htgf)]
    st_gc  = [c - h for c, h in zip(gc, htgc)]
    sr = ms_r[0]; sn = 0
    for r in ms_r:
        if r == sr: sn += 1
        else: break
    return {
        "n": n,
        "form_list": ms_r[:8],
        "form_str":  "-".join(ms_r[:6]),
        "ht_form":   "-".join(ht_r[:5]),
        "pts5": pts5, "pts_pct": round(pts5/15*100, 1),
        "avg_gf":  round(sum(gf)/n, 2),   "avg_gc":  round(sum(gc)/n, 2),
        "ht_avg_gf": round(sum(htgf)/n,2),"ht_avg_gc": round(sum(htgc)/n,2),
        "st_avg_gf": round(sum(st_gf)/n,2),"st_avg_gc": round(sum(st_gc)/n,2),
        "ht_pct": ht_pct, "st_pct": round(100-ht_pct,1),
        "h_avg_gf": round(h_gf/h_n,2) if h_n else 0,
        "h_avg_gc": round(h_gc/h_n,2) if h_n else 0, "h_n": h_n,
        "a_avg_gf": round(a_gf/a_n,2) if a_n else 0,
        "a_avg_gc": round(a_gc/a_n,2) if a_n else 0, "a_n": a_n,
        "btts":  sum(1 for f,c in zip(gf,gc) if f>0 and c>0),
        "o25":   sum(1 for f,c in zip(gf,gc) if f+c>2),
        "o35":   sum(1 for f,c in zip(gf,gc) if f+c>3),
        "cs":    sum(1 for c in gc if c==0),
        "fts":   sum(1 for f in gf if f==0),
        "streak": f"{sn} {'galibiyet' if sr=='G' else 'beraberlik' if sr=='B' else 'mağlubiyet'} serisi",
        "ms_scores": [f"{f}-{c}" for f,c in zip(gf[:6],gc[:6])],
        "ht_scores": [f"{h}-{a}" for h,a in zip(htgf[:6],htgc[:6])],
        # Gerçek İY skor frekansları (hangi skor kaç kez çıktı)
        "ht_score_freq": _calc_score_freq(list(zip(htgf, htgc))),
        # Gerçek MS skor frekansları
        "ms_score_freq": _calc_score_freq(list(zip(gf, gc))),
    }

def parse_h2h(matches, home_id):
    if not matches: return {}
    hw=aw=dr=ht_hw=ht_aw=ht_dr=rev21=rev12=revx1=revx2=btts=o25 = 0
    gl, ms_sc, ht_sc = [], [], []
    for m in matches:
        hid = m["homeTeam"]["id"]
        fh  = m["score"]["fullTime"]["home"] or 0
        fa  = m["score"]["fullTime"]["away"] or 0
        hh  = (m["score"].get("halfTime") or {}).get("home") or 0
        ha  = (m["score"].get("halfTime") or {}).get("away") or 0
        if hid == home_id: my_f,op_f,my_h,op_h = fh,fa,hh,ha
        else:              my_f,op_f,my_h,op_h = fa,fh,ha,hh
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
        if my_f>0 and op_f>0: btts+=1
        if my_f+op_f>2: o25+=1
        gl.append(my_f+op_f)
        ms_sc.append(f"{my_f}-{op_f}")
        ht_sc.append(f"{my_h}-{op_h}")
    n = len(matches)
    p = lambda x: round(x/n*100, 1)
    return {
        "n":n, "hw":hw,"dr":dr,"aw":aw,
        "hw_pct":p(hw),"dr_pct":p(dr),"aw_pct":p(aw),
        "ht_hw":ht_hw,"ht_dr":ht_dr,"ht_aw":ht_aw,
        "ht_hw_pct":p(ht_hw),"ht_dr_pct":p(ht_dr),"ht_aw_pct":p(ht_aw),
        "rev21":rev21,"rev21_pct":p(rev21),
        "rev12":rev12,"rev12_pct":p(rev12),
        "revx1":revx1,"revx1_pct":p(revx1),
        "revx2":revx2,"revx2_pct":p(revx2),
        "avg_goals":round(sum(gl)/n,2) if n else 0,
        "o25":o25,"o25_pct":p(o25),
        "btts":btts,"btts_pct":p(btts),
        "ms_scores":ms_sc,"ht_scores":ht_sc,
    }

def find_standing(table, tid):
    for r in table:
        if r.get("team",{}).get("id") == tid: return r
    return {}

def find_scorer(scorers, tid):
    for s in scorers:
        if s.get("team",{}).get("id") == tid:
            p = s.get("player",{})
            return {"name":p.get("name","?"),"goals":s.get("goals",0),"assists":s.get("assists",0)}
    return {}

# ══════════════════════════════════════════════════════════════════
# POISSON
# ══════════════════════════════════════════════════════════════════

def poi(lam, k):
    lam = max(lam, 0.01)
    return math.exp(-lam) * (lam**k) / math.factorial(k)

def calc_xg(tf, of, is_home):
    base = tf.get("avg_gf", 1.2) if tf else 1.2
    loc  = (tf.get("h_avg_gf" if is_home else "a_avg_gf", base) if tf else base) or base
    opp  = of.get("avg_gc", 1.2) if of else 1.2
    return max(0.3, round(base*0.30 + loc*0.40 + opp*0.30, 3))

def calc_ht_xg(f, xg):
    raw = f.get("ht_avg_gf", xg*0.43) if f else xg*0.43
    return max(0.18, round(raw, 3))

def score_mat(hx, ax, mx=6):
    return {(h,a): round(poi(hx,h)*poi(ax,a)*100, 3)
            for h in range(mx+1) for a in range(mx+1)}

def compute_stats(ms_mat, ht_mat):
    p1 = round(sum(v for(h,a),v in ms_mat.items() if h>a), 1)
    px = round(sum(v for(h,a),v in ms_mat.items() if h==a), 1)
    p2 = round(100-p1-px, 1)
    iy1= round(sum(v for(h,a),v in ht_mat.items() if h>a), 1)
    iyx= round(sum(v for(h,a),v in ht_mat.items() if h==a), 1)
    iy2= round(100-iy1-iyx, 1)
    combos = {}
    for ir,ip in [("1",iy1),("X",iyx),("2",iy2)]:
        for mr,mp in [("1",p1),("X",px),("2",p2)]:
            combos[f"{ir}/{mr}"] = round(ip*mp/100, 2)
    cs = sorted(combos.items(), key=lambda x: -x[1])
    u25 = round(sum(v for(h,a),v in ms_mat.items() if h+a>2), 1)
    u35 = round(sum(v for(h,a),v in ms_mat.items() if h+a>3), 1)
    u45 = round(sum(v for(h,a),v in ms_mat.items() if h+a>4), 1)
    kg  = round(sum(v for(h,a),v in ms_mat.items() if h>0 and a>0), 1)
    return {
        "p1":p1,"px":px,"p2":p2,
        "iy1":iy1,"iyx":iyx,"iy2":iy2,
        "combos":cs,
        "u25":u25,"alt25":round(100-u25,1),
        "u35":u35,"alt35":round(100-u35,1),
        "u45":u45,
        "kg":kg,"kgy":round(100-kg,1),
        "rev21":round(iy2*p1/100, 2),
        "rev12":round(iy1*p2/100, 2),
    }

# ══════════════════════════════════════════════════════════════════
# GROQ — MAÇA ÖZEL PROMPT
# ══════════════════════════════════════════════════════════════════

def build_prompt(h, a, hf, af, h2h, hxg, axg, h_htxg, a_htxg,
                 stats, h_stand, a_stand, h_sc, a_sc, top_ms, top_ht):
    """Kısa ama yeterli prompt — token limitini aşmamak için kompakt."""
    fv = lambda d,k,dv=0: d.get(k,dv) if d else dv
    hs = h_stand or {}; as_ = a_stand or {}

    # Maç karakteri (sadece önemli olanlar)
    chars = []
    diff = round(hxg - axg, 2)
    if diff > 0.6:    chars.append(f"EV FAVORİ xG+{diff}")
    elif diff < -0.6: chars.append(f"DEP FAVORİ xG+{abs(diff)}")
    else:             chars.append(f"DENGE xG={hxg}vs{axg}")
    hp=fv(hf,"pts5"); ap=fv(af,"pts5")
    if hp>=12: chars.append(f"{h} SÜPER FORM {hp}/15")
    elif hp<=4: chars.append(f"{h} KÖTÜ {hp}/15")
    if ap>=12: chars.append(f"{a} SÜPER FORM {ap}/15")
    elif ap<=4: chars.append(f"{a} KÖTÜ {ap}/15")
    if fv(hf,"st_pct",55)>=62: chars.append(f"{h} 2Y_TAKIM(%{fv(hf,'st_pct',55)})")
    if fv(af,"st_pct",55)>=62: chars.append(f"{a} 2Y_TAKIM(%{fv(af,'st_pct',55)})")
    if h2h.get("rev21_pct",0)>=25: chars.append(f"H2H_2/1=%{h2h['rev21_pct']}")
    if h2h.get("rev12_pct",0)>=25: chars.append(f"H2H_1/2=%{h2h['rev12_pct']}")
    if fv(hf,"cs",0)>=3: chars.append(f"{h} SAĞLAM_SAVUNMA {fv(hf,'cs')}/{fv(hf,'n')}CS")
    if fv(af,"avg_gc",0)>=2.0: chars.append(f"{a} SIFIR_SAVUNMA {fv(af,'avg_gc')}yenen")
    if hs.get("position",10)>=16: chars.append(f"{h} DÜŞME_ZONu sıra:{hs.get('position')}")
    if as_.get("position",10)>=16: chars.append(f"{a} DÜŞME_ZONu sıra:{as_.get('position')}")

    h_sc_str = f"{h_sc.get('name','?')}({h_sc.get('goals',0)}g)" if h_sc else "?"
    a_sc_str = f"{a_sc.get('name','?')}({a_sc.get('goals',0)}g)" if a_sc else "?"

    prompt = f"""Profesyonel futbol bahis analisti. Türkçe. Takım isimlerini kullan. Jenerik cümle yasak.

KARAKTER: {" | ".join(chars)}
MAÇ: {h}(Ev) vs {a}(Dep)
PUAN: {h} S:{hs.get('position','?')} {hs.get('won','?')}G-{hs.get('draw','?')}B-{hs.get('lost','?')}M GolAV:{hs.get('goalDifference',0):+d} P:{hs.get('points','?')}
PUAN: {a} S:{as_.get('position','?')} {as_.get('won','?')}G-{as_.get('draw','?')}B-{as_.get('lost','?')}M GolAV:{as_.get('goalDifference',0):+d} P:{as_.get('points','?')}
GOLCÜ: {h_sc_str} | {a_sc_str}
{h} FORM: {fv(hf,'form_str','?')} {fv(hf,'pts5')}/15 | Gol:{fv(hf,'avg_gf')}/{fv(hf,'avg_gc')} | İY:{fv(hf,'ht_avg_gf')}/{fv(hf,'ht_avg_gc')} | 2Y:{fv(hf,'st_avg_gf')}/{fv(hf,'st_avg_gc')} | %{fv(hf,'ht_pct',45)}İY-%{fv(hf,'st_pct',55)}2Y | KG:{fv(hf,'btts')}/{fv(hf,'n')} Üst25:{fv(hf,'o25')}/{fv(hf,'n')} CS:{fv(hf,'cs')}/{fv(hf,'n')} | SonMS:{" ".join((hf.get('ms_scores',[]) if hf else [])[:4])} İY:{" ".join((hf.get('ht_scores',[]) if hf else [])[:4])}
{a} FORM: {fv(af,'form_str','?')} {fv(af,'pts5')}/15 | Gol:{fv(af,'avg_gf')}/{fv(af,'avg_gc')} Dep:{fv(af,'a_avg_gf')}/{fv(af,'a_avg_gc')} | İY:{fv(af,'ht_avg_gf')}/{fv(af,'ht_avg_gc')} | 2Y:{fv(af,'st_avg_gf')}/{fv(af,'st_avg_gc')} | %{fv(af,'ht_pct',45)}İY-%{fv(af,'st_pct',55)}2Y | KG:{fv(af,'btts')}/{fv(af,'n')} Üst25:{fv(af,'o25')}/{fv(af,'n')} CS:{fv(af,'cs')}/{fv(af,'n')} | SonMS:{" ".join((af.get('ms_scores',[]) if af else [])[:4])} İY:{" ".join((af.get('ht_scores',[]) if af else [])[:4])}
H2H({h2h.get('n',0)}maç): {h} {h2h.get('hw',0)}G-{h2h.get('dr',0)}B-{h2h.get('aw',0)}M | İY:{h2h.get('ht_hw',0)}G-{h2h.get('ht_dr',0)}B-{h2h.get('ht_aw',0)}M | MS:{" ".join(h2h.get('ms_scores',[])[:4])} İY:{" ".join(h2h.get('ht_scores',[])[:4])} | Gol:{h2h.get('avg_goals',0)} Üst25:{h2h.get('o25_pct',0)}% KG:{h2h.get('btts_pct',0)}% | 2/1:{h2h.get('rev21',0)}/{h2h.get('n',0)}(%{h2h.get('rev21_pct',0)}) 1/2:{h2h.get('rev12',0)}/{h2h.get('n',0)}(%{h2h.get('rev12_pct',0)})
MODEL: {h}xG={hxg}(İY:{h_htxg}) {a}xG={axg}(İY:{a_htxg}) | MS:1=%{stats['p1']} X=%{stats['px']} 2=%{stats['p2']} | İY:1=%{stats['iy1']} X=%{stats['iyx']} 2=%{stats['iy2']} | TopMS:{" ".join(f"{hg}-{ag}(%{round(v,1)})" for(hg,ag),v in top_ms[:5])} | TopİY:{" ".join(f"{hg}-{ag}(%{round(v,1)})" for(hg,ag),v in top_ht[:4])} | KG={stats['kg']}% Üst25={stats['u25']}% Üst35={stats['u35']}% | Kombo:{" ".join(f"{k}=%{round(v,1)}%" for k,v in stats['combos'][:5])} | Model2/1={stats['rev21']}% Model1/2={stats['rev12']}%

AYNEN bu formatta yaz (başlıkları değiştirme):

### 1) EN OLASI İY SKORU
[skor] (%xx) — [bu maça özgü gerekçe, İY xG ve İY H2H bazlı]

### 2) EN OLASI MS SKORU
[skor] (%xx) — [xG, form, H2H bazlı gerekçe]

### 3) SENARYOLAR
İY [X-Y] → 2Y [X-Y] → MS [X-Y] | %xx | [açıklama]
İY [X-Y] → 2Y [X-Y] → MS [X-Y] | %xx | [açıklama]
İY [X-Y] → 2Y [X-Y] → MS [X-Y] | %xx | [açıklama]
İY [X-Y] → 2Y [X-Y] → MS [X-Y] | %xx | [açıklama]

### 4) MS 1/X/2
1 (%{stats['p1']}): [gerekçe]
X (%{stats['px']}): [gerekçe]
2 (%{stats['p2']}): [gerekçe]

### 5) GOL TAHMİNLERİ
KG VAR (%{stats['kg']}): [gerekçe]
2.5 ÜST (%{stats['u25']}): [gerekçe]
2.5 ALT (%{stats['alt25']}): [gerekçe]
3.5 ÜST (%{stats['u35']}): [gerekçe]

### 6) 2/1 DÖNÜŞ
Model: %{stats['rev21']} | H2H: %{h2h.get('rev21_pct',0)} ({h2h.get('rev21',0)}/{h2h.get('n',0)} maç) | {h} 2Y yükü: %{fv(hf,'st_pct',55)}
Senaryo: [kısa]
NET: [gerçekçi mi, neden?]

### 7) 1/2 DÖNÜŞ
Model: %{stats['rev12']} | H2H: %{h2h.get('rev12_pct',0)} ({h2h.get('rev12',0)}/{h2h.get('n',0)} maç) | {a} 2Y yükü: %{fv(af,'st_pct',55)}
Senaryo: [kısa]
NET: [gerçekçi mi, neden?]

### 8) MAÇ ANALİZİ
[3 cümle — bu maçın spesifik hikayesi]

### 9) TAVSİYELER
BANKO: [tahmin] — %xx — [gerekçe]
ORTA: [tahmin] — %xx — [gerekçe]
RİSKLİ: [tahmin] — [gerekçe]
SKOR: İY [X-Y] + MS [X-Y] — [gerekçe]"""
    return prompt


def groq_call(prompt, retries=4):
    """Groq API — rate limit için akıllı retry ve Retry-After header desteği."""
    import json as _json
    for attempt in range(retries):
        try:
            r = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization":f"Bearer {GROQ_KEY}","Content-Type":"application/json"},
                json={"model":groq_model,
                      "messages":[{"role":"user","content":prompt}],
                      "temperature":0.2,
                      "max_tokens":2000},   # 3500'den 2000'e düşürdük
                timeout=120)

            if r.status_code == 429:
                # Groq Retry-After header'ını oku
                retry_after = r.headers.get("retry-after") or r.headers.get("Retry-After")
                try:
                    wait = int(float(retry_after)) + 2 if retry_after else 20 + attempt * 15
                except:
                    wait = 20 + attempt * 15
                wait = min(wait, 60)  # max 60sn bekle
                ph = st.empty()
                for remaining in range(wait, 0, -1):
                    ph.warning(f"⏳ Rate limit — {remaining}sn bekleniyor... (deneme {attempt+1}/{retries})")
                    time.sleep(1)
                ph.empty()
                continue

            if r.status_code == 413:
                prompt = prompt[:int(len(prompt)*0.75)]
                continue

            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]

        except requests.exceptions.HTTPError as e:
            if attempt < retries - 1:
                time.sleep(15)
                continue
            return f"❌ Groq Hatası: {e}"
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(8)
                continue
            return f"❌ Groq Hatası: {e}"
    return "❌ Groq rate limit aşıldı. 2-3 dakika bekleyip tekrar dene."

# ══════════════════════════════════════════════════════════════════
# ANALİZ PARSE
# ══════════════════════════════════════════════════════════════════

def parse_analysis(text):
    import re
    parts = re.split(r'###\s*\d+\)\s*', text)
    hdrs  = re.findall(r'###\s*\d+\)\s*(.+)', text)
    secs  = {}
    for hdr, content in zip(hdrs, parts[1:]):
        secs[hdr.strip().upper()] = content.strip()

    # Senaryoları parse et
    scenarios = []
    for k,v in secs.items():
        if "SENARYO" in k:
            for line in v.split("\n"):
                line = line.strip()
                if not line: continue
                m = re.search(r'İY\s*(\d-\d).*?2Y\s*(\d-\d).*?MS\s*(\d-\d).*?%\s*(\d+\.?\d*)', line, re.I)
                if m:
                    scenarios.append({
                        "iy":m.group(1),"2y":m.group(2),
                        "ms":m.group(3),"pct":m.group(4),
                        "desc": line
                    })
            break

    # Tavsiyeler
    preds = {}
    for k,v in secs.items():
        if "TAVSİYE" in k or "TAVSIYE" in k:
            for line in v.split("\n"):
                for tag in ["BANKO","ORTA","RİSKLİ","RISKI","SKOR"]:
                    if line.strip().upper().startswith(tag):
                        preds[tag.rstrip("İ").rstrip("Ş")] = line.split(":",1)[-1].strip()

    # Özel skor listeleri — İY ve MS yüksek skorlar
    def parse_score_list(text):
        items = []
        for line in text.split("\n"):
            line = line.strip()
            if not line: continue
            m = re.search(r"(\d-\d)\s*\(%?\s*(\d+\.?\d*)\s*\)\s*[—–-]?\s*(.*)", line)
            if m:
                items.append({"score": m.group(1), "pct": m.group(2), "why": m.group(3).strip()})
        return items

    iy_special = []
    ms_special = []
    for k,v in secs.items():
        if "İLK YARI ÖZEL" in k or "IY ÖZEL" in k or "ILK YARI" in k.replace("İ","I"):
            iy_special = parse_score_list(v)
        if "MAÇ SONU ÖZEL" in k or "MAC SONU" in k.replace("Ç","C"):
            ms_special = parse_score_list(v)

    return secs, scenarios, preds, iy_special, ms_special

# ══════════════════════════════════════════════════════════════════
# VS UI — Ana render fonksiyonu
# ══════════════════════════════════════════════════════════════════

def render_vs_ui(match, hf, af, h2h, hxg, axg, h_htxg, a_htxg,
                 stats, top_ms, top_ht, h_stand, a_stand, h_sc, a_sc,
                 analysis_text):
    h   = match["homeTeam"]["name"]
    a   = match["awayTeam"]["name"]
    utc = match.get("utcDate","")[:16].replace("T"," ")
    secs, scenarios, preds, iy_special, ms_special = parse_analysis(analysis_text)
    fv  = lambda d,k,dv=0: d.get(k,dv) if d else dv
    hs  = h_stand or {}; as_ = a_stand or {}

    # ── 1. VS BAŞLIK ─────────────────────────────────────────
    st.markdown(f"""
<div class="vs-wrapper">
  <div class="vs-header">
    <div class="vs-team home">
      <div class="t-name">{h}</div>
      <div class="t-league">{sel_label}</div>
    </div>
    <div class="vs-middle">
      <div class="vs-badge">
        <div class="vb-vs">VS</div>
        <div class="vb-time">{utc[11:16]}</div>
        <div class="vb-date">{utc[:10]}</div>
      </div>
    </div>
    <div class="vs-team away">
      <div class="t-name">{a}</div>
      <div class="t-league">{sel_label}</div>
    </div>
  </div>
""", unsafe_allow_html=True)

    # ── 2. XG BARI ───────────────────────────────────────────
    total_xg = hxg + axg
    h_pct = round(hxg / total_xg * 100) if total_xg > 0 else 50
    a_pct = 100 - h_pct
    st.markdown(f"""
  <div class="xg-bar-section">
    <div class="xg-label">
      <span style="color:#2563eb">xG {hxg}</span>
      <span style="color:#3a5570;font-size:.65rem">BEKLENEN GOL (xG)</span>
      <span style="color:#dc2626">xG {axg}</span>
    </div>
    <div class="xg-bar-wrap">
      <div class="xg-bar-home" style="width:{h_pct}%">{hxg}</div>
      <div class="xg-bar-mid">·</div>
      <div class="xg-bar-away" style="width:{a_pct}%">{axg}</div>
    </div>
    <div class="xg-label">
      <span>İY xG: {h_htxg}</span>
      <span style="color:#1a3050">Toplam: {round(total_xg,2)}</span>
      <span>İY xG: {a_htxg}</span>
    </div>
  </div>
""", unsafe_allow_html=True)

    # ── 3. PUAN DURUMU VS ────────────────────────────────────
    def better(hv, av, higher_is_better=True):
        if hv == av: hc, ac = "equal","equal"
        elif (hv > av) == higher_is_better: hc, ac = "better","worse"
        else: hc, ac = "worse","better"
        return hc, ac

    rows = []
    def add_row(lbl, hv, av, hib=True, fmt=str):
        hc, ac = better(hv, av, hib)
        rows.append((lbl, fmt(hv), fmt(av), hc, ac))

    if hs and as_:
        add_row("Sıra", hs.get('position',0), as_.get('position',0), hib=False)
        add_row("Puan", hs.get('points',0), as_.get('points',0))
        add_row("Galibiyet", hs.get('won',0), as_.get('won',0))
        add_row("Gol AV", hs.get('goalDifference',0), as_.get('goalDifference',0))

    h_sc_str = f"{h_sc.get('name','?')} ({h_sc.get('goals',0)}⚽)" if h_sc else "?"
    a_sc_str = f"{a_sc.get('name','?')} ({a_sc.get('goals',0)}⚽)" if a_sc else "?"

    vc_html = '<div class="vs-compare">'
    vc_html += '<div class="dp-section-title" style="margin-bottom:8px">PUAN DURUMU KARŞILAŞTIRMA</div>'
    for lbl, hv, av, hc, ac in rows:
        vc_html += f"""
<div class="vc-row">
  <div class="vc-home"><span class="vc-val {hc}">{hv}</span></div>
  <div class="vc-label">{lbl}</div>
  <div class="vc-away"><span class="vc-val {ac}">{av}</span></div>
</div>"""
    # Golcü satırı
    vc_html += f"""
<div class="vc-row">
  <div class="vc-home"><span style="font-size:.72rem;color:#2563eb">{h_sc_str}</span></div>
  <div class="vc-label">Golcü</div>
  <div class="vc-away"><span style="font-size:.72rem;color:#dc2626">{a_sc_str}</span></div>
</div>"""
    vc_html += "</div>"
    st.markdown(vc_html, unsafe_allow_html=True)

    # ── 4. FORM & İSTATİSTİK VS ──────────────────────────────
    dp_html = '<div class="data-panel">'

    # Ev sahibi sütunu
    def form_badges_html(form_list):
        html = '<div class="form-badges">'
        for r in form_list[:8]:
            cls = "fb g" if r=="G" else "fb b" if r=="B" else "fb m"
            html += f'<div class="{cls}">{r}</div>'
        html += "</div>"
        return html

    def score_list_html(scores, label=""):
        html = f'<div class="dp-section-title" style="margin-top:10px">{label}</div>'
        html += '<div class="score-list">'
        for s in scores[:5]:
            html += f'<span class="sc-badge">{s}</span>'
        html += "</div>"
        return html

    def stat_rows_html(rows_data):
        html = ""
        for lbl, val, cls in rows_data:
            html += f'<div class="dp-row"><span class="dr-label">{lbl}</span><span class="dr-val {cls}">{val}</span></div>'
        return html

    def color_class(val, good_thresh, bad_thresh, higher_is_good=True):
        if higher_is_good:
            return "good" if val >= good_thresh else "bad" if val <= bad_thresh else ""
        else:
            return "good" if val <= good_thresh else "bad" if val >= bad_thresh else ""

    # Ev sahibi form verileri
    h_stat_rows = [
        ("Maç Sayısı", fv(hf,"n"), ""),
        ("Form Puanı", f"{fv(hf,'pts5')}/15 (%{fv(hf,'pts_pct')})",
         color_class(fv(hf,"pts5"),9,4)),
        ("Gol Ort (tüm)", f"{fv(hf,'avg_gf')} attı / {fv(hf,'avg_gc')} yedi", ""),
        ("İç Saha Gol", f"{fv(hf,'h_avg_gf')} / {fv(hf,'h_avg_gc')} ({fv(hf,'h_n')} maç)", ""),
        ("İY Gol", f"{fv(hf,'ht_avg_gf')} attı / {fv(hf,'ht_avg_gc')} yedi", ""),
        ("2Y Gol", f"{fv(hf,'st_avg_gf')} attı / {fv(hf,'st_avg_gc')} yedi", ""),
        ("Gol Zamanı", f"%{fv(hf,'ht_pct',45)} İY / %{fv(hf,'st_pct',55)} 2Y",
         "warn" if fv(hf,"st_pct",55)>=60 else ""),
        ("KG VAR", f"{fv(hf,'btts')}/{fv(hf,'n')} maç",
         color_class(fv(hf,"btts"), fv(hf,"n",1)*0.6, fv(hf,"n",1)*0.3)),
        ("2.5 Üst", f"{fv(hf,'o25')}/{fv(hf,'n')} maç", ""),
        ("3.5 Üst", f"{fv(hf,'o35')}/{fv(hf,'n')} maç", ""),
        ("Kuru Kaldı", f"{fv(hf,'cs')}/{fv(hf,'n')} maç",
         color_class(fv(hf,"cs"), fv(hf,"n",1)*0.4, 0)),
        ("Gol Atamadı", f"{fv(hf,'fts')}/{fv(hf,'n')} maç",
         color_class(fv(hf,"fts"), 0, fv(hf,"n",1)*0.3, higher_is_good=False)),
        ("Seri", fv(hf,"streak","?"), "warn"),
    ]

    # Deplasman form verileri
    a_stat_rows = [
        ("Maç Sayısı", fv(af,"n"), ""),
        ("Form Puanı", f"{fv(af,'pts5')}/15 (%{fv(af,'pts_pct')})",
         color_class(fv(af,"pts5"),9,4)),
        ("Gol Ort (tüm)", f"{fv(af,'avg_gf')} attı / {fv(af,'avg_gc')} yedi", ""),
        ("Deplasman Gol", f"{fv(af,'a_avg_gf')} / {fv(af,'a_avg_gc')} ({fv(af,'a_n')} maç)", ""),
        ("İY Gol", f"{fv(af,'ht_avg_gf')} attı / {fv(af,'ht_avg_gc')} yedi", ""),
        ("2Y Gol", f"{fv(af,'st_avg_gf')} attı / {fv(af,'st_avg_gc')} yedi", ""),
        ("Gol Zamanı", f"%{fv(af,'ht_pct',45)} İY / %{fv(af,'st_pct',55)} 2Y",
         "warn" if fv(af,"st_pct",55)>=60 else ""),
        ("KG VAR", f"{fv(af,'btts')}/{fv(af,'n')} maç",
         color_class(fv(af,"btts"), fv(af,"n",1)*0.6, fv(af,"n",1)*0.3)),
        ("2.5 Üst", f"{fv(af,'o25')}/{fv(af,'n')} maç", ""),
        ("3.5 Üst", f"{fv(af,'o35')}/{fv(af,'n')} maç", ""),
        ("Kuru Kaldı", f"{fv(af,'cs')}/{fv(af,'n')} maç",
         color_class(fv(af,"cs"), fv(af,"n",1)*0.4, 0)),
        ("Gol Atamadı", f"{fv(af,'fts')}/{fv(af,'n')} maç",
         color_class(fv(af,"fts"), 0, fv(af,"n",1)*0.3, higher_is_good=False)),
        ("Seri", fv(af,"streak","?"), "warn"),
    ]

    dp_html += f"""
<div class="dp-col home-col">
  <div class="dp-section-title" style="color:#1d4ed8">{h} — FORM</div>
  {form_badges_html(hf.get('form_list',[]) if hf else [])}
  {stat_rows_html(h_stat_rows)}
  {score_list_html(hf.get('ms_scores',[]) if hf else [], "Son MS Skorlar")}
  {score_list_html(hf.get('ht_scores',[]) if hf else [], "Son İY Skorlar")}
</div>
<div class="dp-col">
  <div class="dp-section-title" style="color:#dc2626">{a} — FORM</div>
  {form_badges_html(af.get('form_list',[]) if af else [])}
  {stat_rows_html(a_stat_rows)}
  {score_list_html(af.get('ms_scores',[]) if af else [], "Son MS Skorlar")}
  {score_list_html(af.get('ht_scores',[]) if af else [], "Son İY Skorlar")}
</div>
"""
    dp_html += "</div>"
    st.markdown(dp_html, unsafe_allow_html=True)

    # ── 5. H2H PANEL ─────────────────────────────────────────
    if h2h.get("n",0) > 0:
        h2h_html = f"""
<div class="h2h-panel">
  <div class="dp-section-title">H2H GEÇMİŞİ — Son {h2h['n']} Maç</div>
  <div style="display:grid;grid-template-columns:1fr 80px 1fr;gap:8px;align-items:center;margin:8px 0">
    <div style="text-align:right">
      <span style="font-size:1.4rem;font-weight:800;color:#60a5fa;font-family:'JetBrains Mono',monospace">{h2h['hw']}</span>
      <span style="font-size:.7rem;color:#2a4060;margin-left:4px">GALİBİYET</span>
    </div>
    <div style="text-align:center">
      <span style="font-size:1.4rem;font-weight:800;color:#fbbf24;font-family:'JetBrains Mono',monospace">{h2h['dr']}</span>
      <div style="font-size:.6rem;color:#2a4060">BERAB.</div>
    </div>
    <div>
      <span style="font-size:.7rem;color:#2a4060;margin-right:4px">GALİBİYET</span>
      <span style="font-size:1.4rem;font-weight:800;color:#f87171;font-family:'JetBrains Mono',monospace">{h2h['aw']}</span>
    </div>
  </div>
  <div style="display:grid;grid-template-columns:1fr 80px 1fr;gap:8px;margin-bottom:10px">
    <div style="text-align:right;font-size:.7rem;color:#2a4060">%{h2h['hw_pct']}</div>
    <div style="text-align:center;font-size:.7rem;color:#2a4060">%{h2h['dr_pct']}</div>
    <div style="text-align:left;font-size:.7rem;color:#2a4060">%{h2h['aw_pct']}</div>
  </div>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:8px">
    <div>
      <div class="dp-section-title" style="margin-bottom:5px">İY Sonuçları</div>
      <div style="font-size:.78rem;color:#3a5570">{h}: {h2h['ht_hw']}G / X:{h2h['ht_dr']} / {a}: {h2h['ht_aw']}M</div>
      <div style="font-size:.68rem;color:#1a3050">%{h2h['ht_hw_pct']} / %{h2h['ht_dr_pct']} / %{h2h['ht_aw_pct']}</div>
    </div>
    <div>
      <div class="dp-section-title" style="margin-bottom:5px">Gol İstatistikleri</div>
      <div style="font-size:.78rem;color:#3a5570">Ort: {h2h['avg_goals']} gol/maç</div>
      <div style="font-size:.68rem;color:#1a3050">2.5Üst: %{h2h['o25_pct']} · KG VAR: %{h2h['btts_pct']}</div>
    </div>
  </div>
  <div class="dp-section-title" style="margin-bottom:5px">Son MS Skorları</div>
  <div class="h2h-score-list">{"".join(f'<span class="h2h-sc">{s}</span>' for s in h2h.get('ms_scores',[])[:6])}</div>
  <div class="dp-section-title" style="margin-top:8px;margin-bottom:5px">Son İY Skorları</div>
  <div class="h2h-score-list">{"".join(f'<span class="h2h-sc iy">{s}</span>' for s in h2h.get('ht_scores',[])[:6])}</div>
</div>
"""
        st.markdown(h2h_html, unsafe_allow_html=True)

    # ── 6. OLASILİK — MS 1/X/2 ───────────────────────────────
    fav_ms = max(stats['p1'], stats['px'], stats['p2'])
    h_cls  = "fav-home" if stats['p1']==fav_ms else "default"
    x_cls  = "fav-draw" if stats['px']==fav_ms else "default"
    a_cls  = "fav-away" if stats['p2']==fav_ms else "default"

    st.markdown(f"""
<div class="prob-panel">
  <div class="dp-section-title">POİSSON MODELİ — MAÇSONU OLASILIKları</div>
  <div class="ms-trio">
    <div class="ms-box {h_cls}">
      <div class="mb-label">Ev Gal. (1)</div>
      <div class="mb-pct">%{stats['p1']}</div>
      <div class="mb-name">{h[:18]}</div>
    </div>
    <div class="ms-box {x_cls}">
      <div class="mb-label">Beraberlik (X)</div>
      <div class="mb-pct">%{stats['px']}</div>
      <div class="mb-name">Draw</div>
    </div>
    <div class="ms-box {a_cls}">
      <div class="mb-label">Dep Gal. (2)</div>
      <div class="mb-pct">%{stats['p2']}</div>
      <div class="mb-name">{a[:18]}</div>
    </div>
  </div>
  <div class="dp-section-title" style="margin-top:12px">İLK YARI OLASILIKları</div>
  <div class="ms-trio">
    <div class="ms-box {'fav-home' if stats['iy1']==max(stats['iy1'],stats['iyx'],stats['iy2']) else 'default'}">
      <div class="mb-label">İY Ev (1)</div>
      <div class="mb-pct">%{stats['iy1']}</div>
      <div class="mb-name">{h[:18]}</div>
    </div>
    <div class="ms-box {'fav-draw' if stats['iyx']==max(stats['iy1'],stats['iyx'],stats['iy2']) else 'default'}">
      <div class="mb-label">İY Berab. (X)</div>
      <div class="mb-pct">%{stats['iyx']}</div>
      <div class="mb-name">Draw</div>
    </div>
    <div class="ms-box {'fav-away' if stats['iy2']==max(stats['iy1'],stats['iyx'],stats['iy2']) else 'default'}">
      <div class="mb-label">İY Dep (2)</div>
      <div class="mb-pct">%{stats['iy2']}</div>
      <div class="mb-name">{a[:18]}</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

    # ── 7. GOL METRİKLERİ ────────────────────────────────────
    def gol_cls(v):
        if v >= 65: return "high"
        if v >= 45: return "mid"
        return "low"

    st.markdown(f"""
<div class="gol-panel">
  <div class="dp-section-title">GOL OLASILIKları</div>
  <div class="gol-grid">
    <div class="gol-box {gol_cls(stats['kg'])}">
      <div class="gb-label">KG VAR</div>
      <div class="gb-val">%{stats['kg']}</div>
      <div class="gb-sub">İki taraf da gol atar</div>
    </div>
    <div class="gol-box {gol_cls(stats['kgy'])}">
      <div class="gb-label">KG YOK</div>
      <div class="gb-val">%{stats['kgy']}</div>
      <div class="gb-sub">En az biri gol atamaz</div>
    </div>
    <div class="gol-box {gol_cls(stats['u25'])}">
      <div class="gb-label">2.5 ÜST</div>
      <div class="gb-val">%{stats['u25']}</div>
      <div class="gb-sub">3+ gol atılır</div>
    </div>
    <div class="gol-box {gol_cls(stats['alt25'])}">
      <div class="gb-label">2.5 ALT</div>
      <div class="gb-val">%{stats['alt25']}</div>
      <div class="gb-sub">0/1/2 gol</div>
    </div>
    <div class="gol-box {gol_cls(stats['u35'])}">
      <div class="gb-label">3.5 ÜST</div>
      <div class="gb-val">%{stats['u35']}</div>
      <div class="gb-sub">4+ gol atılır</div>
    </div>
    <div class="gol-box {gol_cls(stats['u45'])}">
      <div class="gb-label">4.5 ÜST</div>
      <div class="gb-val">%{stats['u45']}</div>
      <div class="gb-sub">5+ gol atılır</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

    # ── 8. SKOR DAĞILIMI ─────────────────────────────────────
    st.markdown('<div class="skor-panel"><div class="dp-section-title">EN OLASILIKLI MS SKORLARI</div>',
                unsafe_allow_html=True)
    skor_html = '<div class="skor-grid">'
    for i, ((hg,ag), prob) in enumerate(top_ms[:8]):
        cls = "skor-box rank1" if i==0 else "skor-box rank2" if i==1 else "skor-box rank3" if i==2 else "skor-box"
        skor_html += f'<div class="{cls}"><div class="sb-score">{hg}–{ag}</div><div class="sb-pct">%{round(prob,1)}</div></div>'
    skor_html += "</div>"
    st.markdown(skor_html + '<div class="dp-section-title" style="margin-top:12px">EN OLASILIKLI İY SKORLARI</div>',
                unsafe_allow_html=True)
    iy_html = '<div class="skor-grid">'
    for i, ((hg,ag), prob) in enumerate(top_ht[:6]):
        cls = "skor-box rank1" if i==0 else "skor-box rank2" if i==1 else "skor-box"
        iy_html += f'<div class="{cls}"><div class="sb-score">{hg}–{ag}</div><div class="sb-pct">%{round(prob,1)}</div></div>'
    iy_html += "</div></div>"
    st.markdown(iy_html, unsafe_allow_html=True)

    # ── 9. İY/MS KOMBOLAR ────────────────────────────────────
    st.markdown('<div class="combo-panel"><div class="combo-title">İY/MS KOMBİNASYONLARI — 9 Senaryo</div>',
                unsafe_allow_html=True)
    combo_html = '<div class="combo-grid">'
    combo_descs = {
        "1/1":f"İY {h} önde kalır","X/1":f"İY ber → MS {h}","2/1":f"2/1 Dönüş",
        "1/X":f"İY {h} → ber MS","X/X":"Her iki yarı ber.",f"2/X":f"İY {a} → ber MS",
        "1/2":"1/2 Dönüş",f"X/2":f"İY ber → MS {a}",f"2/2":f"İY {a} önde kalır",
    }
    for i, (k, v) in enumerate(stats['combos']):
        cls = "combo-cell top1" if i==0 else "combo-cell top2" if i==1 else "combo-cell top3" if i==2 else "combo-cell"
        desc = combo_descs.get(k, "")
        combo_html += f'<div class="{cls}"><div class="cc-key">{k}</div><div class="cc-pct">%{round(v,1)}</div><div class="cc-desc">{desc}</div></div>'
    combo_html += "</div></div>"
    st.markdown(combo_html, unsafe_allow_html=True)

    # ── 10. DÖNÜŞ ANALİZİ ────────────────────────────────────
    rev21_m = stats['rev21']; rev21_h = h2h.get('rev21_pct',0)
    rev12_m = stats['rev12']; rev12_h = h2h.get('rev12_pct',0)
    hot21 = rev21_m > 10 or rev21_h > 20
    hot12 = rev12_m > 10 or rev12_h > 20
    d21 = " ".join(secs.get("2/1 DÖNÜŞ","").split()[:50]) if secs.get("2/1 DÖNÜŞ") else ""
    d12 = " ".join(secs.get("1/2 DÖNÜŞ","").split()[:50]) if secs.get("1/2 DÖNÜŞ") else ""

    # ── 10. DÖNÜŞ ANALİZİ — Python ile oluştur (tag güvenliği) ──
    rev21_m = stats['rev21']; rev21_h = h2h.get('rev21_pct',0)
    rev12_m = stats['rev12']; rev12_h = h2h.get('rev12_pct',0)
    hot21 = rev21_m > 10 or rev21_h > 20
    hot12 = rev12_m > 10 or rev12_h > 20
    d21_txt = " ".join(secs.get("2/1 DÖNÜŞ","").split()[:60]) if secs.get("2/1 DÖNÜŞ") else ""
    d12_txt = " ".join(secs.get("1/2 DÖNÜŞ","").split()[:60]) if secs.get("1/2 DÖNÜŞ") else ""

    def _donus_card(title, explain, model_pct, h2h_pct, h2h_n, h2h_total,
                    team1_lbl, team1_pct, team1_color,
                    team2_lbl, team2_pct,
                    extra_text, is_hot, hot_color):
        card_cls = "donus-card hot21" if is_hot and "2/1" in title else "donus-card hot12" if is_hot else "donus-card"
        title_color = hot_color if is_hot else "#1a3050"
        model_color = hot_color if is_hot else "#3a5570"
        h2h_color   = hot_color if h2h_pct > 15 else "#3a5570"
        t1_color    = "#34d399" if team1_pct >= 60 else "#3a5570"
        extra_div   = f'<div style="font-size:.68rem;color:#3a5570;margin-top:6px;line-height:1.5;padding-top:6px;border-top:1px solid #0a1e30">{extra_text}</div>' if extra_text else ""
        return f"""<div class="{card_cls}">
  <div class="dc-title" style="color:{title_color}">{title}</div>
  <div class="dc-explain">{explain}</div>
  <div class="donus-row">
    <div class="dr-lbl">Model İhtimali</div>
    <div class="dr-v" style="color:{model_color}">%{model_pct}</div>
  </div>
  <div class="donus-row">
    <div class="dr-lbl">H2H Tarihsel</div>
    <div class="dr-v" style="color:{h2h_color}">%{h2h_pct} ({h2h_n}/{h2h_total} maç)</div>
  </div>
  <div class="donus-row">
    <div class="dr-lbl">{team1_lbl}</div>
    <div class="dr-v" style="color:{t1_color}">%{team1_pct}</div>
  </div>
  <div class="donus-row">
    <div class="dr-lbl">{team2_lbl}</div>
    <div class="dr-v" style="color:#6b7280">%{team2_pct}</div>
  </div>
  {extra_div}
</div>"""

    card21 = _donus_card(
        title   = "2/1 DÖNÜŞ" + (" 🔥" if hot21 else ""),
        explain = f'İY: <b style="color:#f87171">{a}</b> önde → MS: <b style="color:#60a5fa">{h}</b> kazanır',
        model_pct=rev21_m, h2h_pct=rev21_h,
        h2h_n=h2h.get("rev21",0), h2h_total=h2h.get("n",0),
        team1_lbl=f"{h} 2Y Gol Yükü", team1_pct=fv(hf,"st_pct",55), team1_color="#fbbf24",
        team2_lbl=f"{a} İY Gol Yükü", team2_pct=fv(af,"ht_pct",45),
        extra_text=d21_txt, is_hot=hot21, hot_color="#fbbf24"
    )
    card12 = _donus_card(
        title   = "1/2 DÖNÜŞ" + (" 🔥" if hot12 else ""),
        explain = f'İY: <b style="color:#60a5fa">{h}</b> önde → MS: <b style="color:#f87171">{a}</b> kazanır',
        model_pct=rev12_m, h2h_pct=rev12_h,
        h2h_n=h2h.get("rev12",0), h2h_total=h2h.get("n",0),
        team1_lbl=f"{a} 2Y Gol Yükü", team1_pct=fv(af,"st_pct",55), team1_color="#c4b5fd",
        team2_lbl=f"{h} İY Gol Yükü", team2_pct=fv(hf,"ht_pct",45),
        extra_text=d12_txt, is_hot=hot12, hot_color="#c4b5fd"
    )
    st.markdown(
        f'<div class="donus-panel"><div class="dp-section-title">DÖNÜŞ ANALİZİ</div>'
        f'<div class="donus-grid">{card21}{card12}</div></div>',
        unsafe_allow_html=True
    )


    # ── 11b. GERÇEK VERİYE DAYALI SKOR TABLOSU ──────────────
    # İY skorları: Poisson + gerçek frekans birleşimi
    def _build_iy_scores(hform, aform, ht_top):
        """
        İY skor listesi oluştur:
        1. Her iki takımın gerçek İY skor frekansları → Poisson ağırlıklı birleştir
        2. Sadece xG ile uyumlu makul skorlar (takımların İY gol ort'una yakın)
        """
        from collections import defaultdict
        h_htxg = hform.get("ht_avg_gf", 0.5) if hform else 0.5
        a_htxg = aform.get("ht_avg_gf", 0.5) if aform else 0.5

        # Gerçek frekans verileri
        h_ht_freq = hform.get("ht_score_freq", {}) if hform else {}
        a_ht_freq = aform.get("ht_score_freq", {}) if aform else {}

        # Poisson top İY skorları (zaten hesaplanmış)
        scores = {}
        for (hg, ag), prob in ht_top[:12]:
            scores[f"{hg}-{ag}"] = {"pct": round(prob, 1), "sources": ["model"]}

        # Gerçek frekans: ev sahibi için (kendi attığı = hg, yediği = ag)
        for sc, info in h_ht_freq.items():
            if sc in scores:
                # Model ile gerçek frekansı ağırlıkla
                combined = round(scores[sc]["pct"] * 0.55 + info["pct"] * 0.45, 1)
                scores[sc] = {"pct": combined, "sources": ["model", "ev_form"],
                              "why": f"Ev {info['count']}x gerçekte çıktı"}
            else:
                scores[sc] = {"pct": round(info["pct"] * 0.45, 1),
                              "sources": ["ev_form"],
                              "why": f"Ev {info['count']}x gerçekte çıktı"}

        # Gerçek frekans: deplasman için (attığı = ag, yediği = hg — ters çevir)
        for sc, info in a_ht_freq.items():
            parts = sc.split("-")
            if len(parts) == 2:
                rev_sc = f"{parts[1]}-{parts[0]}"  # deplasman perspektifinden ev-dep'e çevir
                if rev_sc in scores:
                    combined = round(scores[rev_sc]["pct"] * 0.55 + info["pct"] * 0.45, 1)
                    old_why = scores[rev_sc].get("why","")
                    scores[rev_sc] = {"pct": combined, "sources": scores[rev_sc]["sources"] + ["dep_form"],
                                      "why": f"{old_why} | Dep {info['count']}x".strip(" |")}
                else:
                    scores[rev_sc] = {"pct": round(info["pct"] * 0.40, 1),
                                      "sources": ["dep_form"],
                                      "why": f"Dep {info['count']}x gerçekte çıktı"}

        # Makulsüz skorları filtrele (xG'den çok uzak olanları düşür)
        filtered = {}
        for sc, info in scores.items():
            parts = sc.split("-")
            if len(parts) != 2: continue
            try:
                hg, ag = int(parts[0]), int(parts[1])
            except: continue
            # İY'de 3+ gol çok nadir — sadece yüksek xG varsa göster
            if hg + ag >= 3 and h_htxg + a_htxg < 1.5:
                continue
            # Her iki takım da 0'dan fazla atacaksa xG desteği gerek
            if hg > 0 and ag > 0 and h_htxg < 0.3 and a_htxg < 0.3:
                continue
            filtered[sc] = info

        # Sırala ve en iyi 6 döndür
        sorted_scores = sorted(filtered.items(), key=lambda x: -x[1]["pct"])
        return [{"score": sc, "pct": str(info["pct"]), "why": info.get("why","")}
                for sc, info in sorted_scores[:6] if info["pct"] >= 0.5]

    def _build_ms_scores(hform, aform, ms_top):
        """MS skor listesi: Poisson + gerçek frekans birleşimi"""
        h_avg_gf = hform.get("avg_gf", 1.2) if hform else 1.2
        a_avg_gf = aform.get("avg_gf", 1.0) if aform else 1.0
        h_ms_freq = hform.get("ms_score_freq", {}) if hform else {}
        a_ms_freq = aform.get("ms_score_freq", {}) if aform else {}

        scores = {}
        for (hg, ag), prob in ms_top[:12]:
            scores[f"{hg}-{ag}"] = {"pct": round(prob, 1), "why": ""}

        for sc, info in h_ms_freq.items():
            if sc in scores:
                combined = round(scores[sc]["pct"] * 0.5 + info["pct"] * 0.5, 1)
                scores[sc] = {"pct": combined, "why": f"Ev {info['count']}x"}
            elif info["pct"] >= 5:
                scores[sc] = {"pct": round(info["pct"] * 0.45, 1), "why": f"Ev {info['count']}x"}

        for sc, info in a_ms_freq.items():
            parts = sc.split("-")
            if len(parts) == 2:
                rev_sc = f"{parts[1]}-{parts[0]}"
                if rev_sc in scores:
                    old = scores[rev_sc]
                    combined = round(old["pct"] * 0.5 + info["pct"] * 0.5, 1)
                    scores[rev_sc] = {"pct": combined,
                                      "why": f"{old.get('why','')} Dep {info['count']}x".strip()}
                elif info["pct"] >= 5:
                    scores[rev_sc] = {"pct": round(info["pct"] * 0.40, 1),
                                      "why": f"Dep {info['count']}x"}

        sorted_s = sorted(scores.items(), key=lambda x: -x[1]["pct"])
        return [{"score": sc, "pct": str(round(info["pct"],1)), "why": info.get("why","")}
                for sc, info in sorted_s[:8] if info["pct"] >= 1.0]

    iy_src = _build_iy_scores(hf, af, top_ht)
    ms_src = _build_ms_scores(hf, af, top_ms)

    if iy_src or ms_src:
        def _score_item(score, pct, why, bg, border, score_color, pct_color):
            why_div = (f'<div style="font-size:.6rem;color:#3a2a6e;margin-top:1px">{why[:40]}</div>'
                       if why else "")
            mono = "JetBrains Mono,monospace"
            return (
                f'<div style="display:flex;justify-content:space-between;align-items:center;'
                f'padding:6px 10px;margin:4px 0;background:{bg};border:1px solid {border};border-radius:8px">'
                f'<div style="font-size:1.05rem;font-weight:800;color:{score_color};font-family:{mono}">'
                f'{score}</div>'
                f'<div style="text-align:right">'
                f'<div style="font-size:.85rem;font-weight:700;color:{pct_color};font-family:{mono}">%{pct}</div>'
                f'{why_div}</div></div>'
            )

        iy_items_html = "".join(_score_item(it["score"],it["pct"],it.get("why",""),"#0d0a1a","#2d1d5e","#c4b5fd","#a78bfa") for it in iy_src[:6])
        ms_items_html = "".join(_score_item(it["score"],it["pct"],it.get("why",""),"#040f09","#0d3320","#34d399","#6ee7b7") for it in ms_src[:8])

        spec_html = (
            '<div style="padding:1.2rem 1.8rem;border-bottom:1px solid #0a1e30">'
            '<div class="dp-section-title">📐 SKOR ANALİZİ — Gerçek Form + Poisson Modeli</div>'
            '<div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:8px">'
            '<div>'
            '<div style="font-size:.65rem;color:#6d28d9;font-weight:700;letter-spacing:.1em;'
            'text-transform:uppercase;margin-bottom:8px;padding-bottom:4px;border-bottom:1px solid #1a0a3c">'
            '🕐 İLK YARI SKOR TAHMİNLERİ (Form + Model)</div>'
            + iy_items_html +
            '</div>'
            '<div>'
            '<div style="font-size:.65rem;color:#059669;font-weight:700;letter-spacing:.1em;'
            'text-transform:uppercase;margin-bottom:8px;padding-bottom:4px;border-bottom:1px solid #052e16">'
            '🏁 MAÇ SONU SKOR TAHMİNLERİ (Form + Model)</div>'
            + ms_items_html +
            '</div>'
            '</div>'
            '</div>'
        )
        st.markdown(spec_html, unsafe_allow_html=True)

    # ── 12. TAVSİYELER ────────────────────────────────────────
    banko  = preds.get("BANKO","")
    orta   = preds.get("ORTA","")
    risky  = preds.get("RISKI", preds.get("RİSKLİ",""))
    skor   = preds.get("SKOR","")

    tav_html = '<div class="tahmin-panel"><div class="dp-section-title">PROFESYONEL TAVSİYELER</div>'
    if banko:
        tav_html += f"""
<div class="pred-card banko">
  <div class="pred-icon">🔒</div>
  <div class="pred-body">
    <div class="pt">BANKO</div>
    <div class="pp">{banko[:120]}</div>
  </div>
</div>"""
    if orta:
        tav_html += f"""
<div class="pred-card orta">
  <div class="pred-icon">⚡</div>
  <div class="pred-body">
    <div class="pt">ORTA RİSK</div>
    <div class="pp">{orta[:120]}</div>
  </div>
</div>"""
    if risky:
        tav_html += f"""
<div class="pred-card risky">
  <div class="pred-icon">💎</div>
  <div class="pred-body">
    <div class="pt">RİSKLİ</div>
    <div class="pp">{risky[:120]}</div>
  </div>
</div>"""
    if skor:
        tav_html += f"""
<div class="pred-card skor">
  <div class="pred-icon">🎯</div>
  <div class="pred-body">
    <div class="pt">SKOR TAHMİNİ</div>
    <div class="pp">{skor[:120]}</div>
  </div>
</div>"""
    # İY/MS skor kombinasyon kutuları
    if secs.get("SKOR","") or preds.get("SKOR",""):
        skor_val = preds.get("SKOR","") or ""
        iy_match = __import__("re").search(r"İY\s*(\d-\d)", skor_val, __import__("re").I)
        ms_match = __import__("re").search(r"MS\s*(\d-\d)", skor_val, __import__("re").I)
        def _score_str(val):
            if isinstance(val, tuple): return f"{val[0]}-{val[1]}"
            return str(val) if val else "?"
        iy_s = iy_match.group(1) if iy_match else _score_str(top_ht[0][0] if top_ht else "?")
        ms_s = ms_match.group(1) if ms_match else _score_str(top_ms[0][0] if top_ms else "?")
        tav_html += f"""
<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:8px">
  <div style="background:#08050f;border:1px solid #4c1d95;border-radius:10px;
  padding:12px;text-align:center">
    <div style="font-size:.6rem;color:#6d28d9;font-weight:700;
    letter-spacing:.1em;text-transform:uppercase;margin-bottom:6px">🕐 TAHMİN İY SKORU</div>
    <div style="font-size:2rem;font-weight:800;color:#c4b5fd;
    font-family:'JetBrains Mono',monospace">{iy_s}</div>
  </div>
  <div style="background:#040f09;border:1px solid #065f46;border-radius:10px;
  padding:12px;text-align:center">
    <div style="font-size:.6rem;color:#059669;font-weight:700;
    letter-spacing:.1em;text-transform:uppercase;margin-bottom:6px">🏁 TAHMİN MS SKORU</div>
    <div style="font-size:2rem;font-weight:800;color:#34d399;
    font-family:'JetBrains Mono',monospace">{ms_s}</div>
  </div>
</div>"""
    tav_html += "</div>"
    st.markdown(tav_html, unsafe_allow_html=True)

    # ── 13. MAÇ ANALİZİ METNİ ────────────────────────────────
    analiz_text = ""
    for k,v in secs.items():
        if "ANALİZ" in k or "ANALIZ" in k:
            analiz_text = v; break
    if analiz_text:
        st.markdown(f"""
<div class="analiz-panel">
  <div class="analiz-title">📋 MAÇ ANALİZİ</div>
  <div class="analiz-text">{analiz_text[:600]}</div>
</div>
""", unsafe_allow_html=True)

    st.markdown('<div class="disclaimer">⚠️ DISCLAIMER — İstatistikler bilgilendirme amaçlıdır. Kesinlik içermez.</div>',
                unsafe_allow_html=True)

    # Tam analizi indirme
    st.markdown("</div>", unsafe_allow_html=True)  # vs-wrapper kapat
    st.download_button("⬇️ Tam Analizi İndir (.txt)", data=analysis_text,
                       file_name=f"{h}_vs_{a}_{sel_date}.txt",
                       mime="text/plain", key=f"dl_{h[:4]}_{a[:4]}")

# ══════════════════════════════════════════════════════════════════
# SESSION STATE
# ══════════════════════════════════════════════════════════════════
for k in ["matches","mdata","analyses"]:
    if k not in st.session_state:
        st.session_state[k] = [] if k=="matches" else {}

# ══════════════════════════════════════════════════════════════════
# KONTROLLER
# ══════════════════════════════════════════════════════════════════
c1,c2,c3 = st.columns([3,2,2])
with c1: st.markdown(f"**{sel_label}** · {sel_date.strftime('%d.%m.%Y')}")
with c2: fetch_btn = st.button("🔍 Maçları Çek", type="primary", use_container_width=True)
with c3: all_btn   = st.button("🤖 Tümünü Analiz Et", use_container_width=True)
st.divider()

# ══════════════════════════════════════════════════════════════════
# MAÇLARI ÇEK
# ══════════════════════════════════════════════════════════════════
if fetch_btn:
    with st.spinner("📡 Maçlar çekiliyor..."):
        matches = api_matches(sel_code, sel_date.strftime("%Y-%m-%d"), max_match)
    if not matches:
        st.error(f"**{sel_date:%d.%m.%Y} · {sel_label}** için planlanmış maç bulunamadı."); st.stop()
    st.session_state.matches=matches; st.session_state.mdata={}; st.session_state.analyses={}
    st.success(f"✅ {len(matches)} maç!")
    with st.spinner("📊 Lig verileri..."):
        standings=api_standings(sel_code); scorers=api_scorers(sel_code); time.sleep(0.5)
    bar=st.progress(0)
    for i,m in enumerate(matches):
        mid=m["id"]; hid=m["homeTeam"]["id"]; aid=m["awayTeam"]["id"]
        hn=m["homeTeam"]["name"]; an=m["awayTeam"]["name"]
        bar.progress(i/len(matches),text=f"({i+1}/{len(matches)}) {hn} – {an}")
        hf=parse_form(api_team_matches(hid,n_form),hid)
        af=parse_form(api_team_matches(aid,n_form),aid); time.sleep(0.4)
        h2h=parse_h2h(api_h2h(mid,n_h2h),hid); time.sleep(0.4)
        h_s=find_standing(standings,hid); a_s=find_standing(standings,aid)
        h_sc=find_scorer(scorers,hid);   a_sc=find_scorer(scorers,aid)
        hxg=calc_xg(hf,af,True); axg=calc_xg(af,hf,False)
        h_htxg=calc_ht_xg(hf,hxg); a_htxg=calc_ht_xg(af,axg)
        ms_mat=score_mat(hxg,axg); ht_mat=score_mat(h_htxg,a_htxg,mx=4)
        stats=compute_stats(ms_mat,ht_mat)
        top_ms=sorted(ms_mat.items(),key=lambda x:-x[1])[:12]
        top_ht=sorted(ht_mat.items(),key=lambda x:-x[1])[:6]
        prompt=build_prompt(hn,an,hf,af,h2h,hxg,axg,h_htxg,a_htxg,stats,h_s,a_s,h_sc,a_sc,top_ms,top_ht)
        st.session_state.mdata[mid]={
            "match":m,"prompt":prompt,"hf":hf,"af":af,"h2h":h2h,
            "hxg":hxg,"axg":axg,"h_htxg":h_htxg,"a_htxg":a_htxg,
            "stats":stats,"top_ms":top_ms,"top_ht":top_ht,
            "h_stand":h_s,"a_stand":a_s,"h_sc":h_sc,"a_sc":a_sc,
        }
    bar.progress(1.0); time.sleep(0.3); bar.empty()
    st.success("✅ Veriler hazır! Analiz için maç seç.")

# ══════════════════════════════════════════════════════════════════
# TOPLU ANALİZ
# ══════════════════════════════════════════════════════════════════
if all_btn:
    if not st.session_state.mdata: st.warning("Önce Maçları Çek!")
    else:
        items=list(st.session_state.mdata.items()); bar2=st.progress(0)
        for i,(mid,d) in enumerate(items):
            hn=d["match"]["homeTeam"]["name"]; an=d["match"]["awayTeam"]["name"]
            bar2.progress(i/len(items),text=f"({i+1}/{len(items)}) {hn}–{an}")
            result = groq_call(d["prompt"])
            st.session_state.analyses[mid] = result
            if i < len(items) - 1:
                time.sleep(8)   # Groq rate limit: maçlar arası 8sn bekle
        bar2.progress(1.0); time.sleep(0.3); bar2.empty()
        st.success("✅ Tümü tamamlandı!")

# ══════════════════════════════════════════════════════════════════
# MAÇ LİSTESİ
# ══════════════════════════════════════════════════════════════════
if st.session_state.matches:
    st.markdown(f"### ⚽ {len(st.session_state.matches)} Maç · {sel_date.strftime('%d.%m.%Y')}")
    for m in st.session_state.matches:
        mid=m["id"]; hn=m["homeTeam"]["name"]; an=m["awayTeam"]["name"]
        utc=m.get("utcDate","")[:16].replace("T"," "); done=mid in st.session_state.analyses
        d=st.session_state.mdata.get(mid,{})
        with st.expander(f"{'✅' if done else '🔴'}  {hn}  vs  {an}  ·  {utc[11:16]}"):
            if d and not done:
                hxg=d.get("hxg",0); axg=d.get("axg",0)
                hf=d.get("hf",{}); af=d.get("af",{})
                h2=d.get("h2h",{})
                st.markdown(
                    f'<span style="font-size:.75rem;color:#2a4060">'
                    f'xG: <b style="color:#60a5fa">{hxg}</b> – <b style="color:#f87171">{axg}</b> &nbsp;·&nbsp; '
                    f'{hn}: <b style="color:#c0cfe0">{hf.get("form_str","?") if hf else "?"}</b> &nbsp;·&nbsp; '
                    f'{an}: <b style="color:#c0cfe0">{af.get("form_str","?") if af else "?"}</b> &nbsp;·&nbsp; '
                    f'H2H: {h2.get("hw",0)}G-{h2.get("dr",0)}B-{h2.get("aw",0)}M'
                    f'</span>', unsafe_allow_html=True)
                if st.button("🤖 Analiz Et", key=f"btn_{mid}", type="primary"):
                    with st.spinner(f"🦙 Groq: {hn}–{an}..."):
                        st.session_state.analyses[mid]=groq_call(d["prompt"])
                    st.rerun()
            elif done and d:
                try:
                    render_vs_ui(
                        d["match"],d["hf"],d["af"],d["h2h"],
                        d["hxg"],d["axg"],d["h_htxg"],d["a_htxg"],
                        d["stats"],d["top_ms"],d["top_ht"],
                        d["h_stand"],d["a_stand"],d["h_sc"],d["a_sc"],
                        st.session_state.analyses[mid]
                    )
                except Exception as _e:
                    st.error(f"UI render hatası: {_e}")
                    # Fallback: ham analiz metnini göster
                    st.markdown(
                        f'<div style="background:#060d1c;border:1px solid #1a2e4a;border-radius:10px;'
                        f'padding:1.2rem;font-size:.83rem;color:#c0cfe0;white-space:pre-wrap;'
                        f'max-height:600px;overflow-y:auto;font-family:monospace">'
                        f'{st.session_state.analyses[mid]}</div>',
                        unsafe_allow_html=True
                    )
else:
    st.markdown("""
<div style="background:#0a1628;border:1px solid #0f2a45;border-radius:14px;padding:1.5rem 1.8rem">
  <div style="font-size:.7rem;color:#1a3050;font-weight:700;letter-spacing:.12em;
  text-transform:uppercase;margin-bottom:10px">🚀 BAŞLAMAK İÇİN</div>
  <div style="font-size:.85rem;color:#3a5570;line-height:2.2">
    1. Sol sidebar'dan <b style="color:#c0cfe0">Kategori</b> → <b style="color:#c0cfe0">Lig</b> seç<br>
    2. <b style="color:#c0cfe0">Tarih</b> seç (maçların olduğu bir gün)<br>
    3. <b style="color:#00e5a0">🔍 Maçları Çek</b> butonuna bas<br>
    4. Maçı aç → <b style="color:#00e5a0">🤖 Analiz Et</b><br>
    5. Profesyonel VS karşılaştırma arayüzü açılır
  </div>
  <div style="font-size:.68rem;color:#1a3050;margin-top:14px">
    ✅ API key'ler hazır · football-data.org + Groq Llama 3.3 70B
  </div>
</div>
""", unsafe_allow_html=True)
