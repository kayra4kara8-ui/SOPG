import streamlit as st
import requests
from datetime import date, timedelta
import time
import math
import json

st.set_page_config(
    page_title="⚽ Pro Betting Analyst",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.hero {
    background: linear-gradient(135deg, #0a0e1a 0%, #0f1e35 100%);
    border: 1px solid #1e3a5f; border-radius: 14px;
    padding: 1.8rem 2.5rem; margin-bottom: 1.5rem; text-align: center;
}
.hero h1 { color: #60a5fa; margin:0; font-size:1.9rem; font-weight:700; }
.hero p  { color:#6b7280; margin:0.4rem 0 0; font-size:0.88rem; }
.guide {
    background:#0f1923; border:1px solid #1e3a5f;
    border-left:3px solid #3b82f6; border-radius:8px;
    padding:0.9rem 1rem; font-size:0.82rem; color:#9ca3af;
    line-height:2; margin-bottom:1rem;
}
.guide a { color:#60a5fa; }
.guide b { color:#e5e7eb; }
.opill {
    display:inline-block; background:#1f2937;
    border:1px solid #374151; color:#d1d5db;
    padding:3px 10px; border-radius:20px;
    font-size:0.78rem; margin:2px 3px 2px 0;
}
.abox {
    background:#060b14; border:1px solid #1e3a5f;
    border-radius:10px; padding:1.4rem 1.6rem;
    font-size:0.84rem; color:#e5e7eb;
    line-height:2; white-space:pre-wrap;
    max-height:780px; overflow-y:auto;
    font-family:'Courier New',monospace;
}
.dbox {
    background:#111827; border:1px solid #374151;
    border-radius:6px; padding:0.8rem 1rem;
    font-size:0.78rem; color:#9ca3af;
    font-family:'Courier New',monospace;
    max-height:300px; overflow-y:auto;
    white-space:pre-wrap;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
  <h1>⚽ PRO BETTING ANALYST ENGINE</h1>
  <p>football-data.org · Gerçek Veri · Poisson xG Modeli · Claude AI Derin Analiz</p>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🔑 API Anahtarları")
    st.markdown("""
    <div class="guide">
    <b style="color:#60a5fa">football-data.org (ÜCRETSİZ)</b><br>
    1. <a href="https://www.football-data.org/client/register" target="_blank">
       football-data.org/client/register</a><br>
    2. E-posta gir → Kayıt ol → <b>Mail'e API key gelir</b><br>
    3. Buraya yapıştır → Çalışır<br>
    <br>
    <b style="color:#60a5fa">Claude API</b><br>
    <a href="https://console.anthropic.com" target="_blank">console.anthropic.com</a>
    → API Keys → Create Key
    </div>
    """, unsafe_allow_html=True)

    fd_key     = st.text_input("football-data.org Key", type="password",
                                placeholder="Mail'den gelen key...")
    st.markdown("**Claude API Key (opsiyonel)**")
    st.caption("Boş bırak → Yerleşik analiz motoru kullanılır (ücretsiz)")
    claude_key = st.text_input("Claude API Key", type="password",
                                placeholder="sk-ant-... (boş bırakabilirsin)",
                                label_visibility="collapsed")
    if claude_key and claude_key.strip().startswith("sk-ant"):
        st.success("✅ Claude modu — Gelişmiş AI analiz")
    else:
        st.info("⚙️ Yerleşik motor aktif — Ücretsiz tam analiz")

    st.divider()
    st.markdown("## ⚙️ Filtreler")

    LEAGUES = {
        "Premier League 🏴󠁧󠁢󠁥󠁮󠁧󠁿": ("PL",   39),
        "La Liga 🇪🇸":            ("PD",  140),
        "Bundesliga 🇩🇪":         ("BL1",  78),
        "Serie A 🇮🇹":            ("SA",  135),
        "Ligue 1 🇫🇷":            ("FL1",  61),
        "Eredivisie 🇳🇱":         ("DED",  88),
        "Primeira Liga 🇵🇹":      ("PPL",  94),
        "Champions League ⭐":    ("CL",    2),
    }

    sel_label = st.selectbox("Lig Seç", list(LEAGUES.keys()))
    sel_code, sel_league_id = LEAGUES[sel_label]
    sel_date  = st.date_input("Maç Tarihi", value=date.today())
    max_match = st.slider("Maks. Maç Sayısı", 1, 15, 8)

    st.divider()
    st.markdown("### 📊 Analiz Derinliği")
    use_h2h      = st.checkbox("H2H Geçmişi", value=True)
    use_form     = st.checkbox("Son Maç Formu", value=True)
    n_h2h        = st.slider("H2H Maç Sayısı", 3, 10, 6)
    n_form       = st.slider("Form Maç Sayısı", 3, 10, 8)

    st.divider()
    debug = st.checkbox("🐛 Debug (API yanıtı)", value=False)
    st.caption("Rate limit: 10 istek/dak — otomatik yönetilir")

# ─────────────────────────────────────────
# football-data.org API
# ─────────────────────────────────────────
BASE = "https://api.football-data.org/v4"

def fd_get(path, key, params=None):
    headers = {"X-Auth-Token": key}
    try:
        r = requests.get(f"{BASE}{path}", headers=headers,
                         params=params or {}, timeout=15)
        if r.status_code == 429:
            st.warning("⏳ Rate limit — 65sn bekleniyor...")
            time.sleep(66)
            r = requests.get(f"{BASE}{path}", headers=headers,
                             params=params or {}, timeout=15)
        if debug:
            st.caption(f"🐛 GET {path} {params} → {r.status_code}")
        if r.status_code == 200:
            return r.json()
        else:
            st.error(f"API {r.status_code} [{path}]: {r.text[:200]}")
            return {}
    except Exception as e:
        st.error(f"Bağlantı hatası: {e}")
        return {}

def get_matches_on_date(key, code, target_date, limit):
    """Belirli tarihteki planlanmış maçları çek."""
    data = fd_get(f"/competitions/{code}/matches", key, {
        "dateFrom": target_date,
        "dateTo":   target_date,
        "status":   "SCHEDULED,TIMED,POSTPONED",
    })
    matches = data.get("matches", [])
    if debug:
        st.write(f"🐛 {code} / {target_date} → {len(matches)} maç bulundu")
        if matches:
            st.write("İlk maç:", matches[0].get("homeTeam",{}).get("name"),
                     "vs", matches[0].get("awayTeam",{}).get("name"))
    return matches[:limit]

def get_team_matches(key, team_id, n, status="FINISHED"):
    """Takımın son N maçını çek."""
    data = fd_get(f"/teams/{team_id}/matches", key, {
        "status": status, "limit": n,
    })
    return data.get("matches", [])

def get_h2h_matches(key, match_id, n):
    """İki takım arasındaki H2H maçları."""
    data = fd_get(f"/matches/{match_id}/head2head", key, {"limit": n})
    return data.get("matches", [])

def get_standings(key, code):
    """Puan durumu."""
    data = fd_get(f"/competitions/{code}/standings", key)
    try:
        return data["standings"][0]["table"]
    except:
        return []

def get_competition_scorers(key, code):
    """Golcüler listesi."""
    data = fd_get(f"/competitions/{code}/scorers", key, {"limit": 20})
    return data.get("scorers", [])

# ─────────────────────────────────────────
# VERİ İŞLEME
# ─────────────────────────────────────────

def parse_form(matches, team_id):
    """Maçlardan kapsamlı form verisi çıkar."""
    if not matches:
        return {}

    results = []
    gf_list, gc_list = [], []
    ht_gf_list, ht_gc_list = [], []
    home_matches, away_matches = 0, 0
    home_gf, home_gc, away_gf, away_gc = 0, 0, 0, 0

    for m in matches:
        hid = m["homeTeam"]["id"]
        hg  = m["score"]["fullTime"]["home"] or 0
        ag  = m["score"]["fullTime"]["away"] or 0
        hht = (m["score"].get("halfTime") or {}).get("home") or 0
        aht = (m["score"].get("halfTime") or {}).get("away") or 0

        if hid == team_id:
            gf, gc, htgf, htgc = hg, ag, hht, aht
            home_matches += 1
            home_gf += hg; home_gc += ag
        else:
            gf, gc, htgf, htgc = ag, hg, aht, hht
            away_matches += 1
            away_gf += ag; away_gc += hg

        results.append("G" if gf > gc else "B" if gf == gc else "M")
        gf_list.append(gf); gc_list.append(gc)
        ht_gf_list.append(htgf); ht_gc_list.append(htgc)

    n = len(results)
    pts5 = sum({"G":3,"B":1,"M":0}[r] for r in results[:5])

    # İY form
    ht_results = []
    for hg, ag in zip(ht_gf_list, ht_gc_list):
        ht_results.append("G" if hg > ag else "B" if hg == ag else "M")

    # Gol dağılımı analizi (ne kadar ilk yarıda, ne kadar ikinci yarıda)
    total_gf = sum(gf_list)
    total_ht_gf = sum(ht_gf_list)
    ht_ratio = round(total_ht_gf / total_gf * 100, 1) if total_gf > 0 else 50.0
    st_ratio  = round(100 - ht_ratio, 1)

    return {
        "n": n,
        "results": results,
        "form_str": "-".join(results[:6]),
        "pts5": pts5,
        "pts_pct": round(pts5 / 15 * 100, 1),
        "avg_gf": round(sum(gf_list)/n, 2),
        "avg_gc": round(sum(gc_list)/n, 2),
        "ht_form": "-".join(ht_results[:5]),
        "ht_avg_gf": round(sum(ht_gf_list)/n, 2),
        "ht_avg_gc": round(sum(ht_gc_list)/n, 2),
        "ht_gol_orani": ht_ratio,   # gollerinin yüzde kaçı ilk yarıda
        "st_gol_orani": st_ratio,   # ikinci yarı
        "btts": sum(1 for g,c in zip(gf_list,gc_list) if g>0 and c>0),
        "over25": sum(1 for g,c in zip(gf_list,gc_list) if g+c>2),
        "over35": sum(1 for g,c in zip(gf_list,gc_list) if g+c>3),
        "clean_sheets": sum(1 for c in gc_list if c==0),
        "failed_score": sum(1 for g in gf_list if g==0),
        "home_matches": home_matches,
        "away_matches": away_matches,
        "home_avg_gf": round(home_gf/home_matches,2) if home_matches else 0,
        "home_avg_gc": round(home_gc/home_matches,2) if home_matches else 0,
        "away_avg_gf": round(away_gf/away_matches,2) if away_matches else 0,
        "away_avg_gc": round(away_gc/away_matches,2) if away_matches else 0,
        "streak": _streak(results),
    }

def _streak(results):
    if not results:
        return "Veri yok"
    cur = results[0]
    count = 1
    for r in results[1:]:
        if r == cur: count += 1
        else: break
    label = {"G":"galibiyet","B":"beraberlik","M":"mağlubiyet"}.get(cur, cur)
    return f"{count} maç {label} serisi"

def parse_h2h(matches, home_id):
    """H2H maçlarından derin istatistik çıkar."""
    if not matches:
        return {}

    hw=aw=dr=0
    goals_list = []
    ht_hw=ht_aw=ht_dr=0
    rev_21=rev_12=0
    scores, ht_scores = [], []
    btts_count = over25_count = 0

    for m in matches:
        hid = m["homeTeam"]["id"]
        hg  = m["score"]["fullTime"]["home"] or 0
        ag  = m["score"]["fullTime"]["away"] or 0
        hht = (m["score"].get("halfTime") or {}).get("home") or 0
        aht = (m["score"].get("halfTime") or {}).get("away") or 0
        total = hg + ag

        # Ev gözüyle normalize et
        if hid == home_id:
            my_g, op_g = hg, ag
            my_ht, op_ht = hht, aht
        else:
            my_g, op_g = ag, hg
            my_ht, op_ht = aht, hht

        if my_g > op_g: hw += 1
        elif my_g < op_g: aw += 1
        else: dr += 1

        if my_ht > op_ht: ht_hw += 1
        elif my_ht < op_ht: ht_aw += 1
        else: ht_dr += 1

        # 2/1 dönüş: İY deplasman önde, MS ev önde
        if my_ht < op_ht and my_g > op_g: rev_21 += 1
        # 1/2 dönüş: İY ev önde, MS deplasman önde
        if my_ht > op_ht and my_g < op_g: rev_12 += 1

        goals_list.append(total)
        scores.append(f"{my_g}-{op_g}")
        ht_scores.append(f"{my_ht}-{op_ht}")
        if my_g > 0 and op_g > 0: btts_count += 1
        if total > 2: over25_count += 1

    n = len(matches)
    return {
        "n": n,
        "hw": hw, "dr": dr, "aw": aw,
        "ht_hw": ht_hw, "ht_dr": ht_dr, "ht_aw": ht_aw,
        "avg_goals": round(sum(goals_list)/n, 2),
        "over25": over25_count,
        "over25_pct": round(over25_count/n*100, 1),
        "btts": btts_count,
        "btts_pct": round(btts_count/n*100, 1),
        "rev_21": rev_21,
        "rev_21_pct": round(rev_21/n*100, 1),
        "rev_12": rev_12,
        "rev_12_pct": round(rev_12/n*100, 1),
        "scores": scores,
        "ht_scores": ht_scores,
        "hw_pct": round(hw/n*100, 1),
        "dr_pct": round(dr/n*100, 1),
        "aw_pct": round(aw/n*100, 1),
    }

def find_standing(table, team_id):
    for row in table:
        if row.get("team", {}).get("id") == team_id:
            return row
    return {}

def find_top_scorer(scorers, team_id):
    for s in scorers:
        if s.get("team", {}).get("id") == team_id:
            p = s.get("player", {})
            return f"{p.get('name','?')} ({s.get('goals',0)} gol, {s.get('assists',0)} asist)"
    return "Veri yok"

# ─────────────────────────────────────────
# POISSON xG MODELİ
# ─────────────────────────────────────────

def poisson(lam, k):
    if lam <= 0: lam = 0.01
    return math.exp(-lam) * (lam**k) / math.factorial(k)

def calc_xg(team_form, opp_form, is_home=True):
    """
    xG = sezonluk gol ort ağırlıklı + ev/deplasman faktörü + rakip savunma
    """
    if not team_form or not opp_form:
        return 1.2

    base = team_form.get("avg_gf", 1.2)
    opp_def = opp_form.get("avg_gc", 1.2)

    # Ev/deplasman spesifik ortalama
    if is_home:
        specific = team_form.get("home_avg_gf", base)
    else:
        specific = team_form.get("away_avg_gf", base)

    if specific == 0: specific = base

    # Ağırlıklı xG
    xg = (specific * 0.45) + (base * 0.25) + (opp_def * 0.30)
    return max(0.3, round(xg, 3))

def score_matrix(home_xg, away_xg, max_g=6):
    """Skor olasılık matrisi (%)"""
    m = {}
    for h in range(max_g + 1):
        for a in range(max_g + 1):
            m[(h,a)] = round(poisson(home_xg,h) * poisson(away_xg,a) * 100, 3)
    return m

def ht_xg(form, is_home):
    """İlk yarı xG: toplam xG * ilk yarı gol oranı"""
    ratio = form.get("ht_gol_orani", 45) / 100 if form else 0.45
    base  = form.get("ht_avg_gf", 0.55) if form else 0.55
    return max(0.2, round(base, 3))

# ─────────────────────────────────────────
# BÜYÜK PROMPT OLUŞTUR
# ─────────────────────────────────────────

def build_prompt(match, hform, aform, h2h,
                 h_stand, a_stand, scorers):

    h    = match["homeTeam"]
    a    = match["awayTeam"]
    comp = match.get("competition", {}).get("name", "?")
    dt   = (match.get("utcDate") or "")[:10]
    utc  = (match.get("utcDate") or "")[:16].replace("T"," ")

    # xG hesapla
    home_xg = calc_xg(hform, aform, is_home=True)
    away_xg = calc_xg(aform, hform, is_home=False)

    # İY xG
    home_ht_xg = ht_xg(hform, True)
    away_ht_xg = ht_xg(aform, False)

    # Skor matrisleri
    ms_mat  = score_matrix(home_xg, away_xg)
    ht_mat  = score_matrix(home_ht_xg, away_ht_xg, max_g=4)

    # Sıralı skorlar
    top_ms = sorted(ms_mat.items(), key=lambda x:-x[1])[:10]
    top_ht = sorted(ht_mat.items(), key=lambda x:-x[1])[:6]

    # 1/X/2 olasılıkları
    p1  = round(sum(v for (hg,ag),v in ms_mat.items() if hg>ag),  1)
    px  = round(sum(v for (hg,ag),v in ms_mat.items() if hg==ag), 1)
    p2  = round(sum(v for (hg,ag),v in ms_mat.items() if hg<ag),  1)
    iy1 = round(sum(v for (hg,ag),v in ht_mat.items() if hg>ag),  1)
    iyx = round(sum(v for (hg,ag),v in ht_mat.items() if hg==ag), 1)
    iy2 = round(sum(v for (hg,ag),v in ht_mat.items() if hg<ag),  1)

    # İY/MS kombinasyonları
    combos = {}
    for iy_res,iy_p in [("1",iy1),("X",iyx),("2",iy2)]:
        for ms_res,ms_p in [("1",p1),("X",px),("2",p2)]:
            combos[f"{iy_res}/{ms_res}"] = round(iy_p * ms_p / 100, 2)
    combos_sorted = sorted(combos.items(), key=lambda x:-x[1])

    # 2/1 ve 1/2 ihtimali
    rev_21_model = round(iy2 * p1 / 100, 2)  # İY: 2 kazanır, MS: 1 kazanır
    rev_12_model = round(iy1 * p2 / 100, 2)  # İY: 1 kazanır, MS: 2 kazanır

    # Gol hesapları
    p_h0    = poisson(home_xg, 0)
    p_a0    = poisson(away_xg, 0)
    kg_var  = round((1-p_h0)*(1-p_a0)*100, 1)
    kg_yok  = round(100-kg_var, 1)
    ust15   = round(sum(v for (h,a),v in ms_mat.items() if h+a>1), 1)
    ust25   = round(sum(v for (h,a),v in ms_mat.items() if h+a>2), 1)
    alt25   = round(100-ust25, 1)
    ust35   = round(sum(v for (h,a),v in ms_mat.items() if h+a>3), 1)
    alt35   = round(100-ust35, 1)
    ust45   = round(sum(v for (h,a),v in ms_mat.items() if h+a>4), 1)

    # Puan durumu
    def stand_str(s):
        if not s: return "Veri yok"
        ag = s.get("goalsFor",0); gc = s.get("goalsAgainst",0)
        av = s.get("goalDifference",0)
        return (f"Sıra:{s.get('position','?')} | "
                f"O:{s.get('playedGames','?')} G:{s.get('won','?')} "
                f"B:{s.get('draw','?')} M:{s.get('lost','?')} | "
                f"Gol:{ag}-{gc} AV:{av:+d} | Puan:{s.get('points','?')}")

    # Form string
    def form_block(f, name, is_home):
        if not f: return f"{name}: Veri yok"
        loc = "İç Saha" if is_home else "Deplasman"
        return f"""{name}:
  Son Form (MS)  : {f.get('form_str','?')} ({f.get('pts5','?')}/15 puan — %{f.get('pts_pct','?')} verim)
  Son Form (İY)  : {f.get('ht_form','?')}
  Gol Ort (tüm)  : {f.get('avg_gf','?')} attı / {f.get('avg_gc','?')} yedi
  Gol Ort ({loc}): {f.get('home_avg_gf' if is_home else 'away_avg_gf','?')} attı / {f.get('home_avg_gc' if is_home else 'away_avg_gc','?')} yedi
  İY Gol Ort     : {f.get('ht_avg_gf','?')} attı / {f.get('ht_avg_gc','?')} yedi
  Gol Zamanlaması: %{f.get('ht_gol_orani','?')} İY · %{f.get('st_gol_orani','?')} 2Y
  KG VAR         : {f.get('btts','?')}/{f.get('n','?')} maç
  2.5 Üst        : {f.get('over25','?')}/{f.get('n','?')} maç
  3.5 Üst        : {f.get('over35','?')}/{f.get('n','?')} maç
  Kuru kaldı     : {f.get('clean_sheets','?')}/{f.get('n','?')} maç
  Gol atamadı    : {f.get('failed_score','?')}/{f.get('n','?')} maç
  Mevcut Seri    : {f.get('streak','?')}"""

    # H2H block
    def h2h_block(h2):
        if not h2 or not h2.get("n"): return "H2H: Veri yok"
        n = h2["n"]
        return f"""Son {n} maç:
  Sonuçlar    : {h['name']} {h2['hw']}G – {h2['dr']}B – {h2['aw']}M
              ( %{h2['hw_pct']} / %{h2['dr_pct']} / %{h2['aw_pct']} )
  İY Sonuçlar : {h['name']} {h2['ht_hw']}G – {h2['ht_dr']}B – {h2['ht_aw']}M
  Son Skorlar : {' | '.join(h2.get('scores',[])[:6])}
  Son İY Skor : {' | '.join(h2.get('ht_scores',[])[:6])}
  Ort Gol/Maç : {h2['avg_goals']}
  2.5 Üst     : {h2['over25']}/{n} (%{h2['over25_pct']})
  KG VAR      : {h2['btts']}/{n} (%{h2['btts_pct']})
  2/1 Dönüş   : {h2['rev_21']}/{n} maç (%{h2['rev_21_pct']}) — İY 2 önde → MS 1 kazandı
  1/2 Dönüş   : {h2['rev_12']}/{n} maç (%{h2['rev_12_pct']}) — İY 1 önde → MS 2 kazandı"""

    # Golcüler
    h_scorer = find_top_scorer(scorers, h["id"])
    a_scorer = find_top_scorer(scorers, a["id"])

    prompt = f"""
╔══════════════════════════════════════════════════════════════╗
  MAÇ  : {h['name']} vs {a['name']}
  LİG  : {comp}
  ZAMAN: {utc} UTC
╚══════════════════════════════════════════════════════════════╝

━━━ A) PUAN DURUMU ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{h['name']}: {stand_str(h_stand)}
{a['name']}: {stand_str(a_stand)}

━━━ B) GOL LIDERLERI (sezon) ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{h['name']}: {h_scorer}
{a['name']}: {a_scorer}

━━━ C) FORM ANALİZİ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{form_block(hform, h['name'], is_home=True)}

{form_block(aform, a['name'], is_home=False)}

━━━ D) H2H GEÇMİŞİ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{h2h_block(h2h)}

━━━ E) xG MODELİ (Poisson) ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Beklenen Gol:
  {h['name']} xG = {home_xg}  |  {a['name']} xG = {away_xg}
  {h['name']} İY-xG = {home_ht_xg}  |  {a['name']} İY-xG = {away_ht_xg}

MS Olasılıkları:  1 = %{p1}  |  X = %{px}  |  2 = %{p2}
İY Olasılıkları:  1 = %{iy1}  |  X = %{iyx}  |  2 = %{iy2}

En Olası MS Skorları:
{chr(10).join(f"  {hg}-{ag}  →  %{round(prob,2)}" for (hg,ag),prob in top_ms)}

En Olası İY Skorları:
{chr(10).join(f"  {hg}-{ag}  →  %{round(prob,2)}" for (hg,ag),prob in top_ht)}

İY/MS Kombinasyonları (9 senaryo):
{chr(10).join(f"  {k}  →  %{round(v,2)}" for k,v in combos_sorted)}

Gol Sayısı Olasılıkları:
  1.5 Üst: %{ust15}  |  2.5 Üst: %{ust25}  |  2.5 Alt: %{alt25}
  3.5 Üst: %{ust35}  |  3.5 Alt: %{alt35}  |  4.5 Üst: %{ust45}
  KG VAR : %{kg_var}  |  KG YOK: %{kg_yok}

Model 2/1 Dönüş İhtimali: %{rev_21_model}
Model 1/2 Dönüş İhtimali: %{rev_12_model}
H2H Tarihsel 2/1: %{h2h.get('rev_21_pct',0) if h2h else 0}
H2H Tarihsel 1/2: %{h2h.get('rev_12_pct',0) if h2h else 0}
══════════════════════════════════════════════════════════════
""".strip()
    return prompt, home_xg, away_xg

# ─────────────────────────────────────────
# CLAUDE ANALİZ
# ─────────────────────────────────────────

SYSTEM = """Sen dünyanın en kapsamlı futbol bahis veri analistlerinden birisin.
Sana verilen detaylı maç verisini kullanarak 9 maddelik DEDERİNLİKLİ profesyonel rapor yaz.
Her madde için NEDEN sorusunu cevapla. Veriyi yorumla, sadece tekrarlama.

## 1) EN OLASI SKOR + İY SKOR TAHMİNİ
- MS tahmini: Skor, olasılık, NEDEN (form + xG + H2H + puan durumu gerekçeli)
- İY tahmini: Skor, olasılık, NEDEN (gol zamanlama verisi + İY form gerekçeli)
- Hangi takım daha çok baskı kurar? Neden?

## 2) ALTERNATİF SKOR DAĞILIMI (en az 8 skor)
- Her skor: olasılık + kısa gerekçe (neden bu skor mümkün / mümkün değil)
- Özellikle yüksek oranlı sürpriz skorları açıkla

## 3) İY / MS TAHMİNİ — DETAYLI
- İY 1/X/2: Yüzde + gerekçe (ilk yarıda kim üstün olur, neden?)
- MS 1/X/2: Yüzde + gerekçe
- 9 İY/MS kombinasyonu listele, en önemlileri yorumla
- Model olasılığı ile beklenen bahis oranı arasındaki potansiyel value'yu belirt

## 4) KG VAR–YOK & GOL SAYISI — DETAYLI
- KG VAR/YOK: Yüzde + gerekçe (her iki takımın son maçlardaki gol atma/yeme trendi)
- 1.5, 2.5, 3.5, 4.5 Üst/Alt yüzdeleri
- Form bazlı trend: Son maçlarda gol sayısı artıyor mu azalıyor mu?
- İY gol beklentisi vs 2Y gol beklentisi farkı

## 5) 2/1 – 1/2 DÖNÜŞ ANALİZİ — KRİTİK
- Model bazlı 2/1 ihtimali ve H2H tarihsel 2/1 oranı — uyuşuyor mu?
- Model bazlı 1/2 ihtimali ve H2H tarihsel 1/2 oranı — uyuşuyor mu?
- Gol zamanlama verisi: Hangi takım daha çok 2Y'de gol atıyor? Bu dönüşü destekliyor mu?
- Seri durumu: Seri halinde gelen galibiyet/mağlubiyet takımlar dönüşe daha açık mı?
- Taktik değerlendirme: Geride kalan takım nasıl tepki verir?
- Kesin yorum: "2/1 gerçekçi çünkü... / 1/2 zayıf çünkü..." şeklinde

## 6) FORM & TAKTİK ANALİZİ
- Her iki takımın mevcut serisini yorumla
- İç saha / deplasman performans farkı kritik mi?
- Golcü verisine göre: Kim daha tehlikeli?
- Puan durumu motivasyonu: Hangi takımın kazanmaya daha çok ihtiyacı var?

## 7) ORAN–MODEL UYUMU & VALUE TESPİTİ
- Modelimizin 1/X/2 vs piyasa oranlarının zımni olasılıkları — fark var mı?
- Hangi bahis tipinde model ile piyasa arasında en büyük fark var? (VALUE)
- Bu oran aralığında tarihsel pattern ne söylüyor?

## 8) MAÇ RİSK SEVİYESİ
- Düşük / Orta / Yüksek
- Neden? (Veri güvenilirliği, güç farkı, H2H tutarlılığı)

## 9) BANKO – ORTA – SÜRPRİZ – SKOR TAHMİNİ
- 🔒 BANKO (en güvenli, %70+ güven): Tahmin + gerekçe
- ⚡ ORTA RİSK (iyi değer, %50-70): Tahmin + gerekçe
- 💎 SÜRPRİZ (yüksek oran, pattern destekli): Tahmin + gerekçe
- 🎯 SKOR TAHMİNİ (kesin skor, en yüksek value): MS + İY kombine + gerekçe

UYARI: Tüm değerlendirmeler verilen data'ya dayalı. Kişisel yorum yok.
Profesyonel bahis analizi dili. Her tahmin için olasılık yüzdesi ver."""

def claude_analyze(prompt, key):
    try:
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 4000,
                "system": SYSTEM,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=120,
        )
        r.raise_for_status()
        return r.json()["content"][0]["text"]
    except Exception as e:
        return f"❌ Claude Hatası: {e}"


# ─────────────────────────────────────────
# YERLEŞİK DERİN ANALİZ MOTORU
# ─────────────────────────────────────────

def bar_chart(pct, width=20):
    filled = int(pct / 100 * width)
    return "█" * filled + "░" * (width - filled)

def risk_calc(hf, af, h2h):
    hp = hf.get("pts5", 7) if hf else 7
    ap = af.get("pts5", 7) if af else 7
    h2n = h2h.get("n", 0) if h2h else 0
    diff = abs(hp - ap)
    if diff >= 9 and h2n >= 4:
        return "DÜŞÜK ✅", "Belirgin güç farkı var, yeterli H2H geçmişi mevcut."
    elif diff >= 5 or h2n >= 3:
        return "ORTA ⚡", "Güç farkı var ancak sürpriz ihtimali göz ardı edilemez."
    else:
        return "YÜKSEK ⚠️", "Takımlar birbirine yakın ya da veri yetersiz — dikkatli ol."

def local_analyze(d):
    """Claude API olmadan tam 9 maddelik profesyonel analiz üret."""
    m     = d["match"]
    hform = d.get("hform", {}) or {}
    aform = d.get("aform", {}) or {}
    h2h   = d.get("h2h", {})   or {}
    hxg   = d.get("hxg", 1.2)
    axg   = d.get("axg", 1.0)
    h     = m["homeTeam"]["name"]
    a     = m["awayTeam"]["name"]

    # Matrisler (önceden build_prompt tarafından hesaplanmış xG'yi kullan)
    ms_mat = score_matrix(hxg, axg)
    # İY xG yaklaşık
    h_ht_xg = round(hform.get("ht_avg_gf", hxg * 0.42), 3)
    a_ht_xg = round(aform.get("ht_avg_gf", axg * 0.42), 3)
    ht_mat  = score_matrix(max(0.2, h_ht_xg), max(0.2, a_ht_xg), max_g=4)

    top_ms = sorted(ms_mat.items(), key=lambda x: -x[1])
    top_ht = sorted(ht_mat.items(), key=lambda x: -x[1])

    p1  = round(sum(v for (hg,ag),v in ms_mat.items() if hg>ag),  1)
    px  = round(sum(v for (hg,ag),v in ms_mat.items() if hg==ag), 1)
    p2  = round(100-p1-px, 1)
    iy1 = round(sum(v for (hg,ag),v in ht_mat.items() if hg>ag),  1)
    iyx = round(sum(v for (hg,ag),v in ht_mat.items() if hg==ag), 1)
    iy2 = round(100-iy1-iyx, 1)

    combos = {}
    for ir,ip in [("1",iy1),("X",iyx),("2",iy2)]:
        for mr,mp in [("1",p1),("X",px),("2",p2)]:
            combos[f"{ir}/{mr}"] = round(ip*mp/100, 2)
    combos_s = sorted(combos.items(), key=lambda x:-x[1])

    p_h0   = poisson(hxg, 0); p_a0 = poisson(axg, 0)
    kg_var = round((1-p_h0)*(1-p_a0)*100, 1)
    kg_yok = round(100-kg_var, 1)
    ust15  = round(sum(v for (hg,ag),v in ms_mat.items() if hg+ag>1), 1)
    ust25  = round(sum(v for (hg,ag),v in ms_mat.items() if hg+ag>2), 1)
    alt25  = round(100-ust25, 1)
    ust35  = round(sum(v for (hg,ag),v in ms_mat.items() if hg+ag>3), 1)
    alt35  = round(100-ust35, 1)
    ust45  = round(sum(v for (hg,ag),v in ms_mat.items() if hg+ag>4), 1)

    rev_21_model = round(iy2*p1/100, 2)
    rev_12_model = round(iy1*p2/100, 2)
    rev_21_h2h   = h2h.get("rev_21_pct", 0)
    rev_12_h2h   = h2h.get("rev_12_pct", 0)

    best_ms  = top_ms[0][0]
    best_ht  = top_ht[0][0]
    best_ms_p = round(top_ms[0][1], 1)
    best_ht_p = round(top_ht[0][1], 1)

    risk_lv, risk_why = risk_calc(hform, aform, h2h)

    # --- Form yorumları ---
    def form_yorum(f, name, is_home):
        if not f: return f"  {name}: Form verisi yok."
        pts  = f.get("pts5", 0)
        avgf = f.get("home_avg_gf" if is_home else "away_avg_gf", f.get("avg_gf", 1.2))
        avgg = f.get("home_avg_gc" if is_home else "away_avg_gc", f.get("avg_gc", 1.2))
        seri = f.get("streak", "?")
        ht_r = f.get("ht_gol_orani", 45)
        st_r = f.get("st_gol_orani", 55)
        tip  = "İç saha" if is_home else "Deplasman"
        lines = [
            f"  {name} ({tip}) — Form: {f.get('form_str','?')} | {pts}/15 puan",
            f"  Gol ort: {avgf} attı / {avgg} yedi | Seri: {seri}",
            f"  İY Gol Ort: {f.get('ht_avg_gf','?')} attı / {f.get('ht_avg_gc','?')} yedi",
            f"  Gol zamanı: %{ht_r} İY · %{st_r} 2Y",
            f"  KG VAR: {f.get('btts',0)}/{f.get('n',0)} | 2.5Üst: {f.get('over25',0)}/{f.get('n',0)} | Kuru: {f.get('clean_sheets',0)}/{f.get('n',0)}",
        ]
        # Tempo yorumu
        if ht_r < 38:
            lines.append(f"  ⚡ Bu takım gollerini ağırlıklı 2. yarıda atıyor (%{st_r}) → yavaş başlangıç eğilimi")
        elif ht_r > 55:
            lines.append(f"  ⚡ Bu takım gollerini ağırlıklı ilk yarıda atıyor (%{ht_r}) → erken baskı eğilimi")
        if avgg < 0.7:
            lines.append(f"  🛡️ Savunma çok sağlam — maç başına {avgg} gol yiyor")
        elif avgg > 1.8:
            lines.append(f"  ⚠️ Savunma zayıf — maç başına {avgg} gol yiyor")
        return "\n".join(lines)

    # --- Skor gerekçesi ---
    fav = h if p1 > p2 else (a if p2 > p1 else "Belirsiz")
    fav_xg = hxg if p1 > p2 else axg
    und_xg  = axg if p1 > p2 else hxg

    def score_reason(hg, ag):
        total = hg + ag
        reasons = []
        if hg > ag:
            reasons.append(f"{h} xG {hxg} > {a} xG {axg} — ev üstünlüğü destekliyor")
        elif ag > hg:
            reasons.append(f"{a} xG {axg} form verisiyle yeterli — deplasman gücü var")
        else:
            reasons.append("xG dengeli, beraberlik Poisson modelinde güçlü")
        if total > 3:
            reasons.append("Her iki tarafın savunma açığı yüksek gol sayısını destekliyor")
        elif total < 2:
            reasons.append("Savunma sağlamlığı düşük skorlu sonucu destekliyor")
        return "; ".join(reasons)

    # --- 2/1 & 1/2 derin yorum ---
    def donus_yorum_21():
        lines = []
        model_str = f"%{rev_21_model}"
        h2h_str   = f"%{rev_21_h2h} ({h2h.get('rev_21',0)}/{h2h.get('n',1)} maç)"
        lines.append(f"  Model: {model_str} | H2H geçmiş: {h2h_str}")
        # Tempo analizi
        h_2y = aform.get("st_gol_orani", 55) if aform else 55
        a_2y = aform.get("st_gol_orani", 55) if aform else 55
        if axg > hxg * 0.8 and h_2y > 55:
            lines.append(f"  {a} 2Y'de daha aktif (%{h_2y} gol 2Y'de) → İY üstünlüğü mümkün")
        if hform.get("st_gol_orani", 50) > 58:
            lines.append(f"  {h} 2Y'de gol atma eğilimi yüksek (%{hform.get('st_gol_orani',50)}) → Dönüş için zemin var")
        if rev_21_model < 8 and rev_21_h2h < 15:
            lines.append(f"  ⚠️ Hem model hem H2H düşük → 2/1 pek gerçekçi değil")
        elif rev_21_model > 12 or rev_21_h2h > 25:
            lines.append(f"  ✅ Model veya H2H geçmiş yüksek → 2/1 senaryosu izlenebilir")
        return "\n".join(lines)

    def donus_yorum_12():
        lines = []
        model_str = f"%{rev_12_model}"
        h2h_str   = f"%{rev_12_h2h} ({h2h.get('rev_12',0)}/{h2h.get('n',1)} maç)"
        lines.append(f"  Model: {model_str} | H2H geçmiş: {h2h_str}")
        a_2y = aform.get("st_gol_orani", 50) if aform else 50
        if hxg > axg * 0.8 and a_2y > 55:
            lines.append(f"  {h} erken baskı, {a} 2Y'de gol baskısı → 1/2 için zemin")
        if rev_12_model < 8 and rev_12_h2h < 15:
            lines.append(f"  ⚠️ Hem model hem H2H düşük → 1/2 pek gerçekçi değil")
        elif rev_12_model > 12 or rev_12_h2h > 25:
            lines.append(f"  ✅ Model veya H2H geçmiş yüksek → 1/2 senaryosu izlenebilir")
        return "\n".join(lines)

    # --- Banko / Orta / Sürpriz ---
    if p1 >= 58:
        banko = f"MS 1 ({h} galibiyeti) — %{p1}"
        banko_why = f"{h} xG {hxg} ile belirgin üstün; form {hform.get('form_str','?')}"
    elif p2 >= 52:
        banko = f"MS 2 ({a} galibiyeti) — %{p2}"
        banko_why = f"{a} xG {axg}, deplasman formu güçlü"
    elif ust25 >= 65:
        banko = f"2.5 ÜST — %{ust25}"
        banko_why = f"Her iki takım da yüksek xG; KG VAR %{kg_var}"
    elif alt25 >= 62:
        banko = f"2.5 ALT — %{alt25}"
        banko_why = f"İki savunma da sağlam; toplam xG {round(hxg+axg,2)} düşük"
    elif kg_var >= 65:
        banko = f"KG VAR — %{kg_var}"
        banko_why = f"Her iki takım da gol atma kapasitesi yüksek"
    else:
        top_combo = combos_s[0]
        banko = f"İY/MS {top_combo[0]} — %{top_combo[1]}"
        banko_why = "En yüksek olasılıklı İY/MS kombinasyonu"

    # Orta risk
    if px >= 28:
        orta = f"Beraberlik (X) — %{px}"
        orta_why = "İki takım güç dengeli; x oranı değerli olabilir"
    elif kg_var >= 58 and ust25 >= 55:
        orta = f"KG VAR + 2.5 ÜST — %{round(kg_var*ust25/100,1)}"
        orta_why = "Her iki takımın da hücum/savunma dengesi destekliyor"
    else:
        sc = combos_s[1]
        orta = f"İY/MS {sc[0]} — %{sc[1]}"
        orta_why = "İkinci en yüksek olasılıklı İY/MS kombinasyonu"

    # Sürpriz
    surpriz_score = top_ms[3] if len(top_ms) > 3 else top_ms[-1]
    surpriz = f"Skor {surpriz_score[0][0]}-{surpriz_score[0][1]} — %{round(surpriz_score[1],1)}"
    surpriz_why = "4. en olası skor — piyasada yüksek oran taşır, Poisson model destekli"

    # Skor sürprizi
    yuksek_gol = [(s,p) for (s,p) in top_ms if s[0]+s[1] >= 4]
    skor_surpriz = yuksek_gol[0] if yuksek_gol else top_ms[2]
    skor_surp_str = f"{skor_surpriz[0][0]}-{skor_surpriz[0][1]} — %{round(skor_surpriz[1],1)}"

    # ───────── RAPOR ─────────
    report = f"""
╔══════════════════════════════════════════════════════════════════╗
  ⚽ {h.upper()} vs {a.upper()}
╚══════════════════════════════════════════════════════════════════╝

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1️⃣  EN OLASI SKOR TAHMİNİ
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  🎯 MS TAHMİN : {best_ms[0]}-{best_ms[1]}  →  %{best_ms_p}
  🎯 İY TAHMİN : {best_ht[0]}-{best_ht[1]}  →  %{best_ht_p}

  Gerekçe: {score_reason(best_ms[0], best_ms[1])}
  {h} xG = {hxg}  |  {a} xG = {axg}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
2️⃣  ALTERNATİF SKOR DAĞILIMI
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{chr(10).join(
    f"  {hg}-{ag}  {bar_chart(prob,18)}  %{round(prob,1):5.1f}  {'← EN OLASILIK' if i==0 else ''}"
    for i,((hg,ag),prob) in enumerate(top_ms[:9])
)}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
3️⃣  İY / MS TAHMİNİ
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  İLK YARI  :  1=%{iy1}  |  X=%{iyx}  |  2=%{iy2}
  MAÇ SONU  :  1=%{p1}   |  X=%{px}   |  2=%{p2}

  İY/MS Kombinasyonları:
  ┌─────────┬────────┐
  │ Senaryo │ Oran   │
  ├─────────┼────────┤
{chr(10).join(f"  │  {k:<7}  │  %{v:<5.1f} │" for k,v in combos_s)}
  └─────────┴────────┘

  Yorum:
  • {h} form puanı {hform.get('pts5',0)}/15 · {a} form puanı {aform.get('pts5',0)}/15
  • {'İlk yarıda ' + h + ' üstün görünüyor (xG ' + str(h_ht_xg) + ')' if h_ht_xg > a_ht_xg else 'İlk yarıda ' + a + ' üstün görünüyor (xG ' + str(a_ht_xg) + ')'}
  • Güçlü fav: {"Yok — maç açık" if abs(p1-p2)<10 else (h if p1>p2 else a)}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
4️⃣  KG VAR–YOK & ÜST/ALT TAHMİNLERİ
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  KG VAR  {bar_chart(kg_var)}  %{kg_var}
  KG YOK  {bar_chart(kg_yok)}  %{kg_yok}
  ─────────────────────────────────────────
  1.5 ÜST {bar_chart(ust15)}  %{ust15}
  2.5 ÜST {bar_chart(ust25)}  %{ust25}  │  2.5 ALT  %{alt25}
  3.5 ÜST {bar_chart(ust35)}  %{ust35}  │  3.5 ALT  %{alt35}
  4.5 ÜST {bar_chart(ust45)}  %{ust45}
  ─────────────────────────────────────────
  Yorum:
  • Toplam xG: {round(hxg+axg,2)} → {"Gol ziyafeti bekleniyor" if hxg+axg>3 else "Dengeli, az gollü maç olabilir" if hxg+axg<2.2 else "Normal gol beklentisi"}
  • {h} son {hform.get('n',0)} maçta {hform.get('btts',0)} kez KG VAR ({round(hform.get('btts',0)/max(hform.get('n',1),1)*100,1)}%)
  • {a} son {aform.get('n',0)} maçta {aform.get('btts',0)} kez KG VAR ({round(aform.get('btts',0)/max(aform.get('n',1),1)*100,1)}%)
  • {h} 2.5 Üst: {hform.get('over25',0)}/{hform.get('n',1)} | {a} 2.5 Üst: {aform.get('over25',0)}/{aform.get('n',1)}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
5️⃣  2/1 – 1/2 DÖNÜŞ TESPİTİ
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  2/1 Dönüş ({a} İY önde → {h} MS kazanır):
{donus_yorum_21()}

  1/2 Dönüş ({h} İY önde → {a} MS kazanır):
{donus_yorum_12()}

  Gol Zamanlama:
  • {h}: %{hform.get('ht_gol_orani',45)} İY · %{hform.get('st_gol_orani',55)} 2Y
  • {a}: %{aform.get('ht_gol_orani',45)} İY · %{aform.get('st_gol_orani',55)} 2Y
  • {"⚡ Her iki takım da 2Y'de daha tehlikeli → dönüş senaryoları izlenebilir" if hform.get('st_gol_orani',50)>54 and aform.get('st_gol_orani',50)>54 else "ℹ️ Gol dağılımı dengeli"}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
6️⃣  FORM & TAKTİK ANALİZİ
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{form_yorum(hform, h, True)}

{form_yorum(aform, a, False)}

  H2H Özet: {h} {h2h.get('hw',0)}G – {h2h.get('dr',0)}B – {h2h.get('aw',0)}M
  Son Skorlar: {" | ".join(h2h.get("scores",[])[:5]) or "Veri yok"}
  H2H Ort Gol: {h2h.get('avg_goals','?')} | 2.5 Üst: {h2h.get('over25_pct','?')}% | KG VAR: {h2h.get('btts_pct','?')}%

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
7️⃣  ORAN–MODEL UYUMU
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Model MS Olasılıkları: 1=%{p1} | X=%{px} | 2=%{p2}
  (İddaa oranı yoksa piyasa karşılaştırması yapılamıyor)

  Bu oran aralığında tipik pattern:
  • xG {hxg:.2f}-{axg:.2f} dengesiyle en sık biten skor: {best_ms[0]}-{best_ms[1]}
  • KG VAR eğilimi: {"Güçlü" if kg_var>=60 else "Orta" if kg_var>=45 else "Zayıf"} (%{kg_var})
  • 2.5 Üst eğilimi: {"Güçlü" if ust25>=62 else "Orta" if ust25>=48 else "Zayıf"} (%{ust25})

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
8️⃣  MAÇ RİSK SEVİYESİ
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Seviye : {risk_lv}
  Gerekçe: {risk_why}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
9️⃣  BANKO – ORTA RİSK – SÜRPRİZ
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  🔒 BANKO    : {banko}
               {banko_why}

  ⚡ ORTA RİSK: {orta}
               {orta_why}

  💎 SÜRPRİZ  : {surpriz}
               {surpriz_why}

  🎯 SKOR SÜRPRİZİ: {skor_surp_str}
               Toplam xG {round(hxg+axg,2)} destekli, yüksek oran value taşır

══════════════════════════════════════════════════════════════════
  ⚠️ Bu analiz istatistiksel model çıktısıdır.
     Yatırım tavsiyesi değildir. Sorumluluğunuzda kullanın.
══════════════════════════════════════════════════════════════════
""".strip()
    return report


def run_analysis(d, claude_key):
    """Claude varsa Claude, yoksa yerleşik motor."""
    if claude_key and claude_key.strip().startswith("sk-ant"):
        return claude_analyze(d["prompt"], claude_key)
    else:
        return local_analyze(d)


# ─────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────
for k in ["matches","match_data","analyses"]:
    if k not in st.session_state:
        st.session_state[k] = [] if k=="matches" else {}

# ─────────────────────────────────────────
# ANA BUTONLAR
# ─────────────────────────────────────────
c1, c2, c3 = st.columns([3, 2, 2])
with c1:
    st.markdown(f"**{sel_label}** · {sel_date.strftime('%d.%m.%Y')} · Maks {max_match} maç")
with c2:
    fetch_btn = st.button("🔍 Maçları Çek", type="primary", use_container_width=True)
with c3:
    all_btn = st.button("🤖 Tümünü Analiz Et (Ücretsiz)", use_container_width=True)

st.divider()

# ─────────────────────────────────────────
# MAÇLARI ÇEK
# ─────────────────────────────────────────
if fetch_btn:
    if not fd_key:
        st.error("⛔ football-data.org API Key giriniz.")
        st.stop()

    with st.spinner("📡 Maçlar çekiliyor..."):
        matches = get_matches_on_date(fd_key, sel_code,
                                       sel_date.strftime("%Y-%m-%d"), max_match)

    if not matches:
        st.error(f"""
**⚠️ {sel_date.strftime('%d.%m.%Y')} tarihinde {sel_label} için maç bulunamadı.**

Olası nedenler:
- O gün bu ligde maç yok (boş hafta / uluslararası ara)
- API key hatalı — [football-data.org](https://www.football-data.org/client/login) giriş yap ve key'i kontrol et
- Lig bu plan kapsamında değil

**Çözüm:** Farklı bir tarih veya lig dene. Yarın / bu hafta sonu seç.
        """)
        st.stop()

    st.session_state.matches   = matches
    st.session_state.match_data = {}
    st.session_state.analyses   = {}
    st.success(f"✅ {len(matches)} maç bulundu! Detaylı veriler hazırlanıyor...")

    # Ek veriler
    with st.spinner("📊 Puan durumu ve golcüler çekiliyor..."):
        standings = get_standings(fd_key, sel_code)
        scorers   = get_competition_scorers(fd_key, sel_code)
        time.sleep(0.5)

    bar = st.progress(0)
    for i, m in enumerate(matches):
        mid = m["id"]
        hid = m["homeTeam"]["id"]
        aid = m["awayTeam"]["id"]
        hn  = m["homeTeam"]["name"]
        an  = m["awayTeam"]["name"]

        bar.progress(i/len(matches), text=f"({i+1}/{len(matches)}) {hn} – {an}")

        # Form
        hf_raw = get_team_matches(fd_key, hid, n_form) if use_form else []
        af_raw = get_team_matches(fd_key, aid, n_form) if use_form else []
        hform  = parse_form(hf_raw, hid)
        aform  = parse_form(af_raw, aid)
        time.sleep(0.4)

        # H2H
        h2h_raw = get_h2h_matches(fd_key, mid, n_h2h) if use_h2h else []
        h2h     = parse_h2h(h2h_raw, hid)
        time.sleep(0.4)

        # Puan durumu
        h_stand = find_standing(standings, hid)
        a_stand = find_standing(standings, aid)

        # Prompt
        prompt, hxg, axg = build_prompt(
            m, hform, aform, h2h,
            h_stand, a_stand, scorers
        )

        st.session_state.match_data[mid] = {
            "match": m, "prompt": prompt,
            "hxg": hxg, "axg": axg,
            "hform": hform, "aform": aform,
            "h2h": h2h,
        }

    bar.progress(1.0, text="Veriler hazır!")
    time.sleep(0.5)
    bar.empty()
    st.success("✅ Tüm veriler hazır! Maç seç → Analiz Et")

# ─────────────────────────────────────────
# TOPLU ANALİZ
# ─────────────────────────────────────────
if all_btn:
    if not st.session_state.match_data:
        st.warning("Önce Maçları Çek!")
    else:
        bar2 = st.progress(0)
        items = list(st.session_state.match_data.items())
        for i, (mid, d) in enumerate(items):
            hn = d["match"]["homeTeam"]["name"]
            an = d["match"]["awayTeam"]["name"]
            bar2.progress(i/len(items), text=f"({i+1}/{len(items)}) {hn} – {an}")
            st.session_state.analyses[mid] = run_analysis(d, claude_key)
            time.sleep(0.5)
        bar2.progress(1.0)
        time.sleep(0.3); bar2.empty()
        st.success("✅ Tüm analizler tamamlandı!")

# ─────────────────────────────────────────
# MAÇ LİSTESİ
# ─────────────────────────────────────────
if st.session_state.matches:
    st.markdown(f"## 📋 Maçlar ({len(st.session_state.matches)})")

    for m in st.session_state.matches:
        mid  = m["id"]
        hn   = m["homeTeam"]["name"]
        an   = m["awayTeam"]["name"]
        comp = m.get("competition",{}).get("name","")
        utc  = (m.get("utcDate",""))[:16].replace("T"," ")
        done = mid in st.session_state.analyses
        d    = st.session_state.match_data.get(mid,{})

        with st.expander(f"{'✅' if done else '⚽'}  {hn}  –  {an}  |  {comp}  |  {utc}"):
            # xG özet
            if d.get("hxg"):
                st.markdown(
                    f"<span class='opill'>🏠 {hn} xG: {d['hxg']}</span>"
                    f"<span class='opill'>✈️ {an} xG: {d['axg']}</span>",
                    unsafe_allow_html=True
                )

            # Form özet
            if d.get("hform") and d.get("aform"):
                hf = d["hform"]; af = d["aform"]
                st.markdown(
                    f"<span class='opill'>{hn}: {hf.get('form_str','?')}</span>"
                    f"<span class='opill'>{an}: {af.get('form_str','?')}</span>"
                    f"<span class='opill'>H2H: {d.get('h2h',{}).get('hw',0)}G-{d.get('h2h',{}).get('dr',0)}B-{d.get('h2h',{}).get('aw',0)}M</span>",
                    unsafe_allow_html=True
                )

            # Ham veri
            if d.get("prompt"):
                with st.expander("📊 Ham Veri & Model Çıktısı"):
                    st.markdown(f"<div class='dbox'>{d['prompt']}</div>",
                                unsafe_allow_html=True)

            # Analiz butonu
            ca, cb = st.columns([3,1])
            with cb:
                if st.button("🤖 Analiz Et", key=f"a_{mid}"):
                    if not d.get("prompt"):
                        st.warning("Önce Maçları Çek!")
                    else:
                        with st.spinner(f"Derin analiz: {hn} – {an}..."):
                            st.session_state.analyses[mid] = run_analysis(d, claude_key)

            # Analiz sonucu
            if mid in st.session_state.analyses:
                st.markdown("---")
                st.markdown(
                    f"<div class='abox'>{st.session_state.analyses[mid]}</div>",
                    unsafe_allow_html=True)
                st.download_button("⬇️ Analizi İndir",
                    data=st.session_state.analyses[mid],
                    file_name=f"{hn}_vs_{an}_{sel_date}.txt",
                    mime="text/plain", key=f"dl_{mid}")

# ─────────────────────────────────────────
# BAŞLANGIÇ EKRANI
# ─────────────────────────────────────────
else:
    st.markdown("""
    <div class="guide" style="font-size:0.88rem; line-height:2.1">
    <b style="color:#60a5fa; font-size:1rem">⚽ Her Maç İçin Çekilen Veriler</b><br><br>
    📊 <b>Puan Durumu</b> — Sıra, gol averajı, maç başına puan<br>
    ⚽ <b>Golcü Listesi</b> — Sezonun en iyi gol atan oyuncuları<br>
    📈 <b>Son N Maç Formu</b> — MS + İY ayrı ayrı, ev/deplasman bazlı<br>
    ⏱️ <b>Gol Zamanlama</b> — Gollerini 1Y'de mi 2Y'de mi atıyor?<br>
    🔄 <b>H2H Geçmişi</b> — Skorlar, İY sonuçları, 2/1 & 1/2 dönüş sayısı<br>
    🎯 <b>Poisson xG Modeli</b> — Sezon + form + rakip savunma ağırlıklı<br>
    📐 <b>10+ Skor Senaryosu</b> — Her biri olasılıklı<br>
    🔁 <b>9 İY/MS Kombinasyonu</b> — Yüzdeli<br>
    🔃 <b>2/1 – 1/2 Dönüş</b> — Model + H2H tarihsel karşılaştırması<br><br>
    <b>Başlamak için:</b><br>
    1. <a href="https://www.football-data.org/client/register" target="_blank">
       football-data.org/client/register</a> → E-posta ile ücretsiz kayıt → Key mail'e gelir<br>
    2. <a href="https://console.anthropic.com" target="_blank">console.anthropic.com</a>
       → Claude API Key al<br>
    3. Soldaki sidebar'a key'leri gir → Lig + tarih → Maçları Çek → Analiz Et
    </div>
    """, unsafe_allow_html=True)
