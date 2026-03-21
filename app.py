import streamlit as st
import requests
import math
import time
from datetime import date

st.set_page_config(
    page_title="⚽ Pro Betting Analyst v4",
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
.hero h1 { color: #60a5fa; margin: 0; font-size: 1.9rem; font-weight: 700; }
.hero p  { color: #6b7280; margin: 0.4rem 0 0; font-size: 0.88rem; }

.guide {
    background: #0f1923; border: 1px solid #1e3a5f;
    border-left: 3px solid #3b82f6; border-radius: 8px;
    padding: 0.9rem 1rem; font-size: 0.82rem; color: #9ca3af;
    line-height: 2; margin-bottom: 1rem;
}
.guide a { color: #60a5fa; }
.guide b { color: #e5e7eb; }

.opill {
    display: inline-block; background: #1f2937;
    border: 1px solid #374151; color: #d1d5db;
    padding: 3px 10px; border-radius: 20px;
    font-size: 0.78rem; margin: 2px 3px 2px 0;
}

.abox {
    background: #060b14; border: 1px solid #1e3a5f;
    border-radius: 10px; padding: 1.4rem 1.6rem;
    font-size: 0.84rem; color: #e5e7eb; line-height: 2;
    white-space: pre-wrap; max-height: 820px; overflow-y: auto;
    font-family: 'Courier New', monospace;
}

.dbox {
    background: #111827; border: 1px solid #374151;
    border-radius: 6px; padding: 0.8rem 1rem;
    font-size: 0.75rem; color: #6b7280;
    font-family: 'Courier New', monospace;
    max-height: 300px; overflow-y: auto; white-space: pre-wrap;
}

.statrow {
    display: flex; justify-content: space-between;
    padding: 4px 0; border-bottom: 1px solid #1f2937;
    font-size: 0.8rem;
}
.statrow .label { color: #6b7280; }
.statrow .val   { color: #e5e7eb; font-weight: 500; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
  <h1>⚽ PRO BETTING ANALYST ENGINE v4</h1>
  <p>football-data.org (Ücretsiz Veri) + Groq Llama 3.3 70B (Ücretsiz AI)
  · İY & MS Skor · 2/1–1/2 Dönüş · Gol Zamanlama · 9 Kombo · Tamamen Ücretsiz</p>
</div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 🔑 API Anahtarları")
    st.markdown("""
    <div class="guide">
    <b style="color:#60a5fa">1) Groq API — ÜCRETSİZ</b><br>
    → <a href="https://console.groq.com" target="_blank">console.groq.com</a> git<br>
    → Google hesabınla giriş yap<br>
    → Sol menü: API Keys → Create API Key<br>
    → Key <b>gsk_</b> ile başlar · 500K token/gün · Kart YOK<br><br>
    <b style="color:#60a5fa">2) football-data.org — ÜCRETSİZ</b><br>
    → <a href="https://www.football-data.org/client/register" target="_blank">
       football-data.org/client/register</a><br>
    → E-posta ile kayıt ol → Key direkt mail'e gelir<br>
    → Premier League, La Liga, Bundesliga, Serie A, CL dahil
    </div>
    """, unsafe_allow_html=True)

    groq_key = st.text_input(
        "Groq API Key",
        type="password",
        placeholder="gsk_...",
        help="console.groq.com → API Keys → Create Key"
    )
    fd_key = st.text_input(
        "football-data.org Key",
        type="password",
        placeholder="Mail'den gelen key...",
        help="football-data.org/client/register → ücretsiz kayıt"
    )

    if groq_key and groq_key.startswith("gsk_"):
        st.success("✅ Groq bağlı — Llama 3.3 70B aktif")
    elif groq_key:
        st.warning("⚠️ Groq key 'gsk_' ile başlamalı")

    st.divider()
    st.markdown("## ⚙️ Filtreler")

    LEAGUES = {
        "Premier League 🏴󠁧󠁢󠁥󠁮󠁧󠁿": "PL",
        "La Liga 🇪🇸":            "PD",
        "Bundesliga 🇩🇪":         "BL1",
        "Serie A 🇮🇹":            "SA",
        "Ligue 1 🇫🇷":            "FL1",
        "Eredivisie 🇳🇱":         "DED",
        "Primeira Liga 🇵🇹":      "PPL",
        "Champions League ⭐":    "CL",
        "Europa League 🌍":       "EL",
    }
    sel_label = st.selectbox("Lig Seç", list(LEAGUES.keys()))
    sel_code  = LEAGUES[sel_label]
    sel_date  = st.date_input("Maç Tarihi", value=date.today())
    max_match = st.slider("Maks. Maç Sayısı", 1, 15, 8)

    st.divider()
    st.markdown("### 📊 Veri Derinliği")
    use_h2h  = st.checkbox("H2H Geçmişi", value=True)
    use_form = st.checkbox("Son Maç Formu", value=True)
    n_h2h    = st.slider("H2H Maç Sayısı", 3, 10, 6)
    n_form   = st.slider("Form Maç Sayısı", 3, 10, 8)

    st.divider()
    groq_model = st.selectbox(
        "Groq Model",
        ["llama-3.3-70b-versatile", "llama3-70b-8192", "mixtral-8x7b-32768"],
        help="llama-3.3-70b-versatile en iyi sonucu verir"
    )
    debug = st.checkbox("🐛 Debug Modu", value=False)
    st.caption("500K token/gün ücretsiz · ~8-15 maç analizi")

# ═══════════════════════════════════════════════════
# football-data.org API KATMANI
# ═══════════════════════════════════════════════════
BASE = "https://api.football-data.org/v4"

def fd_get(path, key, params=None):
    """football-data.org'a istek at, rate limit yönet."""
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
            st.caption(f"🐛 {path} params={params} → HTTP {r.status_code}")
        if r.status_code == 200:
            return r.json()
        else:
            st.error(f"API {r.status_code} [{path}]: {r.text[:200]}")
            return {}
    except Exception as e:
        st.error(f"Bağlantı hatası [{path}]: {e}")
        return {}

def get_matches_on_date(key, code, target_date, limit):
    """Belirtilen günde planlanmış maçları çek."""
    data = fd_get(
        f"/competitions/{code}/matches", key,
        {"dateFrom": target_date, "dateTo": target_date,
         "status": "SCHEDULED,TIMED,POSTPONED"}
    )
    matches = data.get("matches", [])
    if debug:
        st.write(f"🐛 {code} {target_date}: {len(matches)} maç bulundu")
    return matches[:limit]

def get_team_last_matches(key, team_id, n):
    """Takımın son N tamamlanmış maçını çek."""
    data = fd_get(
        f"/teams/{team_id}/matches", key,
        {"status": "FINISHED", "limit": n}
    )
    return data.get("matches", [])

def get_h2h_matches(key, match_id, n):
    """İki takım arasındaki kafa kafaya maçları çek."""
    data = fd_get(f"/matches/{match_id}/head2head", key, {"limit": n})
    return data.get("matches", [])

def get_league_standings(key, code):
    """Lig puan durumunu çek."""
    data = fd_get(f"/competitions/{code}/standings", key)
    try:
        return data["standings"][0]["table"]
    except (KeyError, IndexError):
        return []

def get_top_scorers(key, code, limit=20):
    """Sezonun gol kraliyet listesini çek."""
    data = fd_get(f"/competitions/{code}/scorers", key, {"limit": limit})
    return data.get("scorers", [])

# ═══════════════════════════════════════════════════
# VERİ İŞLEME — FORM ANALİZİ
# ═══════════════════════════════════════════════════

def parse_team_form(matches, team_id):
    """
    Maçlardan kapsamlı form verisi çıkar:
    - MS sonuçları (G/B/M)
    - İY sonuçları
    - Gol ortalamaları (genel + iç saha + deplasman)
    - Gol zamanlama (İY vs 2Y yüzdesi) ← KRİTİK
    - Son maç skorları ve İY skorları
    """
    if not matches:
        return {}

    ms_res   = []  # Maç sonu: G/B/M
    ht_res   = []  # İlk yarı: G/B/M
    gf_list  = []  # Maç sonu attıkları
    gc_list  = []  # Maç sonu yedikleri
    htgf_list = [] # İlk yarı attıkları
    htgc_list = [] # İlk yarı yedikleri

    # İç saha ve deplasman ayrımı
    home_gf = home_gc = home_n = 0
    away_gf = away_gc = away_n = 0

    for m in matches:
        hid  = m["homeTeam"]["id"]
        ft_h = m["score"]["fullTime"]["home"] or 0
        ft_a = m["score"]["fullTime"]["away"] or 0
        ht_h = (m["score"].get("halfTime") or {}).get("home") or 0
        ht_a = (m["score"].get("halfTime") or {}).get("away") or 0

        # Takımın bakış açısından normalize et
        if hid == team_id:
            my_ft, op_ft = ft_h, ft_a
            my_ht, op_ht = ht_h, ht_a
            home_gf += ft_h; home_gc += ft_a; home_n += 1
        else:
            my_ft, op_ft = ft_a, ft_h
            my_ht, op_ht = ht_a, ht_h
            away_gf += ft_a; away_gc += ft_h; away_n += 1

        ms_res.append("G" if my_ft > op_ft else "B" if my_ft == op_ft else "M")
        ht_res.append("G" if my_ht > op_ht else "B" if my_ht == op_ht else "M")
        gf_list.append(my_ft);   gc_list.append(op_ft)
        htgf_list.append(my_ht); htgc_list.append(op_ht)

    n = len(ms_res)
    if n == 0:
        return {}

    # Puan hesapla (son 5)
    pts5 = sum({"G": 3, "B": 1, "M": 0}[r] for r in ms_res[:5])

    # Gol zamanlama analizi
    total_gf   = sum(gf_list)
    total_htgf = sum(htgf_list)
    if total_gf > 0:
        ht_gol_pct = round(total_htgf / total_gf * 100, 1)
    else:
        ht_gol_pct = 45.0
    st_gol_pct = round(100 - ht_gol_pct, 1)

    # 2Y gol ortalaması (total - ht)
    st_gf_list = [ft - ht for ft, ht in zip(gf_list, htgf_list)]
    st_gc_list = [ft - ht for ft, ht in zip(gc_list, htgc_list)]

    # Seri hesapla
    streak_char = ms_res[0] if ms_res else "?"
    streak_len  = 0
    for r in ms_res:
        if r == streak_char:
            streak_len += 1
        else:
            break
    streak_label = {"G": "galibiyet", "B": "beraberlik", "M": "mağlubiyet"}
    streak_str = f"{streak_len} maç {streak_label.get(streak_char, '?')} serisi"

    return {
        "n":              n,
        "form_str":       "-".join(ms_res[:6]),
        "ht_form":        "-".join(ht_res[:5]),
        "pts5":           pts5,
        "pts_pct":        round(pts5 / 15 * 100, 1),
        # Genel gol ortalamaları
        "avg_gf":         round(sum(gf_list) / n, 2),
        "avg_gc":         round(sum(gc_list) / n, 2),
        "ht_avg_gf":      round(sum(htgf_list) / n, 2),
        "ht_avg_gc":      round(sum(htgc_list) / n, 2),
        "st_avg_gf":      round(sum(st_gf_list) / n, 2),
        "st_avg_gc":      round(sum(st_gc_list) / n, 2),
        # Gol zamanlama ← 2/1 1/2 analizi için KRİTİK
        "ht_gol_pct":     ht_gol_pct,
        "st_gol_pct":     st_gol_pct,
        # İç saha / Deplasman ayrımı
        "home_avg_gf":    round(home_gf / home_n, 2) if home_n > 0 else 0.0,
        "home_avg_gc":    round(home_gc / home_n, 2) if home_n > 0 else 0.0,
        "home_n":         home_n,
        "away_avg_gf":    round(away_gf / away_n, 2) if away_n > 0 else 0.0,
        "away_avg_gc":    round(away_gc / away_n, 2) if away_n > 0 else 0.0,
        "away_n":         away_n,
        # Gol/piyasa istatistikleri
        "btts_count":     sum(1 for f, c in zip(gf_list, gc_list) if f > 0 and c > 0),
        "over25_count":   sum(1 for f, c in zip(gf_list, gc_list) if f + c > 2),
        "over35_count":   sum(1 for f, c in zip(gf_list, gc_list) if f + c > 3),
        "over15_count":   sum(1 for f, c in zip(gf_list, gc_list) if f + c > 1),
        "clean_sheets":   sum(1 for c in gc_list if c == 0),
        "failed_to_score":sum(1 for f in gf_list if f == 0),
        # Son maç skorları
        "last_ms_scores": [f"{f}-{c}" for f, c in zip(gf_list[:6], gc_list[:6])],
        "last_ht_scores": [f"{h}-{a}" for h, a in zip(htgf_list[:6], htgc_list[:6])],
        # Seri bilgisi
        "streak":         streak_str,
        "last_5_results": "-".join(ms_res[:5]),
    }

# ═══════════════════════════════════════════════════
# VERİ İŞLEME — H2H ANALİZİ
# ═══════════════════════════════════════════════════

def parse_h2h_deep(matches, home_team_id):
    """
    H2H maçlarından derin istatistik çıkar.
    Özellikle 2/1 ve 1/2 dönüş tarihsel verisi.
    """
    if not matches:
        return {}

    hw = aw = dr = 0           # Maç sonu
    ht_hw = ht_aw = ht_dr = 0  # İlk yarı
    rev_21 = 0                 # İY 2 önde → MS 1 kazandı
    rev_12 = 0                 # İY 1 önde → MS 2 kazandı
    rev_x1 = 0                 # İY berabere → MS 1 kazandı
    rev_x2 = 0                 # İY berabere → MS 2 kazandı
    btts   = 0
    over25 = 0
    over35 = 0
    goals_list = []
    ms_scores  = []
    ht_scores  = []

    for m in matches:
        hid  = m["homeTeam"]["id"]
        ft_h = m["score"]["fullTime"]["home"] or 0
        ft_a = m["score"]["fullTime"]["away"] or 0
        ht_h = (m["score"].get("halfTime") or {}).get("home") or 0
        ht_a = (m["score"].get("halfTime") or {}).get("away") or 0

        # Ev sahibi bakış açısından normalize
        if hid == home_team_id:
            my_ft, op_ft = ft_h, ft_a
            my_ht, op_ht = ht_h, ht_a
        else:
            my_ft, op_ft = ft_a, ft_h
            my_ht, op_ht = ht_a, ht_h

        # MS sonucu
        if my_ft > op_ft:   hw += 1
        elif my_ft < op_ft: aw += 1
        else:                dr += 1

        # İY sonucu
        if my_ht > op_ht:   ht_hw += 1
        elif my_ht < op_ht: ht_aw += 1
        else:                ht_dr += 1

        # Dönüş tespiti
        if my_ht < op_ht and my_ft > op_ft:  rev_21 += 1  # 2/1
        if my_ht > op_ht and my_ft < op_ft:  rev_12 += 1  # 1/2
        if my_ht == op_ht and my_ft > op_ft: rev_x1 += 1  # X/1
        if my_ht == op_ht and my_ft < op_ft: rev_x2 += 1  # X/2

        total = my_ft + op_ft
        if my_ft > 0 and op_ft > 0: btts   += 1
        if total > 2:                over25 += 1
        if total > 3:                over35 += 1
        goals_list.append(total)
        ms_scores.append(f"{my_ft}-{op_ft}")
        ht_scores.append(f"{my_ht}-{op_ht}")

    n = len(matches)
    return {
        "n":            n,
        # MS sonuçlar
        "hw":           hw, "dr": dr, "aw": aw,
        "hw_pct":       round(hw / n * 100, 1),
        "dr_pct":       round(dr / n * 100, 1),
        "aw_pct":       round(aw / n * 100, 1),
        # İY sonuçlar
        "ht_hw":        ht_hw, "ht_dr": ht_dr, "ht_aw": ht_aw,
        "ht_hw_pct":    round(ht_hw / n * 100, 1),
        "ht_dr_pct":    round(ht_dr / n * 100, 1),
        "ht_aw_pct":    round(ht_aw / n * 100, 1),
        # Dönüşler
        "rev_21":       rev_21,
        "rev_21_pct":   round(rev_21 / n * 100, 1),
        "rev_12":       rev_12,
        "rev_12_pct":   round(rev_12 / n * 100, 1),
        "rev_x1":       rev_x1,
        "rev_x1_pct":   round(rev_x1 / n * 100, 1),
        "rev_x2":       rev_x2,
        "rev_x2_pct":   round(rev_x2 / n * 100, 1),
        # Gol istatistikleri
        "avg_goals":    round(sum(goals_list) / n, 2),
        "over25":       over25, "over25_pct": round(over25 / n * 100, 1),
        "over35":       over35, "over35_pct": round(over35 / n * 100, 1),
        "btts":         btts,   "btts_pct":   round(btts   / n * 100, 1),
        # Skor listeleri
        "ms_scores":    ms_scores,
        "ht_scores":    ht_scores,
    }

# ═══════════════════════════════════════════════════
# VERİ İŞLEME — YARDIMCI FONKSİYONLAR
# ═══════════════════════════════════════════════════

def find_team_standing(standings_table, team_id):
    """Puan tablosunda takımı bul."""
    for row in standings_table:
        if row.get("team", {}).get("id") == team_id:
            return row
    return {}

def find_team_top_scorer(scorers_list, team_id):
    """Takımın en golcü oyuncusunu bul."""
    for s in scorers_list:
        if s.get("team", {}).get("id") == team_id:
            p = s.get("player", {})
            return {
                "name":    p.get("name", "?"),
                "goals":   s.get("goals", 0),
                "assists": s.get("assists", 0),
                "played":  s.get("playedMatches", 0),
            }
    return {}

def format_standing(s):
    if not s:
        return "Puan durumu verisi yok"
    d = s.get("goalDifference", 0)
    return (
        f"Sıra: {s.get('position', '?')} | "
        f"Oynadığı: {s.get('playedGames', '?')} | "
        f"G: {s.get('won', '?')} B: {s.get('draw', '?')} M: {s.get('lost', '?')} | "
        f"Gol: {s.get('goalsFor', '?')}-{s.get('goalsAgainst', '?')} "
        f"AV: {d:+d} | Puan: {s.get('points', '?')}"
    )

def pct(count, total):
    """Güvenli yüzde hesabı."""
    if total == 0:
        return 0.0
    return round(count / total * 100, 1)

# ═══════════════════════════════════════════════════
# POISSON xG MODELİ
# ═══════════════════════════════════════════════════

def poisson_prob(lam, k):
    lam = max(lam, 0.01)
    return math.exp(-lam) * (lam ** k) / math.factorial(k)

def calc_team_xg(team_form, opp_form, is_home):
    """
    xG Hesaplama:
    - Takımın iç saha/deplasman gol ortalaması: %40
    - Genel gol ortalaması: %30
    - Rakibin yendiği gol ortalaması: %30
    """
    if not team_form:
        return 1.2 if is_home else 1.0

    general_avg = team_form.get("avg_gf", 1.2)
    loc_avg = team_form.get("home_avg_gf" if is_home else "away_avg_gf", general_avg)
    opp_def = opp_form.get("avg_gc", 1.2) if opp_form else 1.2

    if loc_avg == 0:
        loc_avg = general_avg

    xg = (loc_avg * 0.40) + (general_avg * 0.30) + (opp_def * 0.30)
    return max(0.30, round(xg, 3))

def calc_ht_xg(form, full_xg):
    """İlk yarı xG: İY gol ortalaması veya toplam xG'nin %43'ü."""
    if not form:
        return max(0.2, round(full_xg * 0.43, 3))
    ht_avg = form.get("ht_avg_gf", full_xg * 0.43)
    return max(0.2, round(ht_avg, 3))

def build_score_matrix(home_xg, away_xg, max_goals=6):
    """Poisson skor olasılık matrisi (%)."""
    matrix = {}
    for h in range(max_goals + 1):
        for a in range(max_goals + 1):
            matrix[(h, a)] = round(
                poisson_prob(home_xg, h) * poisson_prob(away_xg, a) * 100, 3
            )
    return matrix

def calc_all_stats(ms_matrix, ht_matrix):
    """Matrislerden tüm bahis istatistiklerini hesapla."""
    # MS 1/X/2
    p1 = round(sum(v for (h, a), v in ms_matrix.items() if h > a), 1)
    px = round(sum(v for (h, a), v in ms_matrix.items() if h == a), 1)
    p2 = round(100 - p1 - px, 1)

    # İY 1/X/2
    iy1 = round(sum(v for (h, a), v in ht_matrix.items() if h > a), 1)
    iyx = round(sum(v for (h, a), v in ht_matrix.items() if h == a), 1)
    iy2 = round(100 - iy1 - iyx, 1)

    # İY/MS 9 kombinasyon
    combos = {}
    for iy_r, iy_p in [("1", iy1), ("X", iyx), ("2", iy2)]:
        for ms_r, ms_p in [("1", p1), ("X", px), ("2", p2)]:
            combos[f"{iy_r}/{ms_r}"] = round(iy_p * ms_p / 100, 2)
    combos_sorted = sorted(combos.items(), key=lambda x: -x[1])

    # 2/1 ve 1/2 dönüş (model)
    rev_21_model = round(iy2 * p1 / 100, 2)
    rev_12_model = round(iy1 * p2 / 100, 2)
    rev_x1_model = round(iyx * p1 / 100, 2)
    rev_x2_model = round(iyx * p2 / 100, 2)

    # Gol sayısı
    p_h0   = poisson_prob(sum(v for (h, a), v in [(k, v) for k, v in ms_matrix.items() if k[0] == 0]), 0) if False else poisson_prob(1, 0)
    # Düzgün hesaplama:
    u15  = round(sum(v for (h, a), v in ms_matrix.items() if h + a > 1), 1)
    u25  = round(sum(v for (h, a), v in ms_matrix.items() if h + a > 2), 1)
    u35  = round(sum(v for (h, a), v in ms_matrix.items() if h + a > 3), 1)
    u45  = round(sum(v for (h, a), v in ms_matrix.items() if h + a > 4), 1)

    # KG VAR: Her iki takım da gol atar
    kg_var = round(
        sum(v for (h, a), v in ms_matrix.items() if h > 0 and a > 0), 1
    )
    kg_yok = round(100 - kg_var, 1)

    return {
        "p1": p1, "px": px, "p2": p2,
        "iy1": iy1, "iyx": iyx, "iy2": iy2,
        "combos": combos_sorted,
        "rev_21_model": rev_21_model,
        "rev_12_model": rev_12_model,
        "rev_x1_model": rev_x1_model,
        "rev_x2_model": rev_x2_model,
        "u15": u15, "u25": u25, "u35": u35, "u45": u45,
        "kg_var": kg_var, "kg_yok": kg_yok,
    }

# ═══════════════════════════════════════════════════
# VERİ PAKETİ OLUŞTUR (Groq'a gönderilecek)
# ═══════════════════════════════════════════════════

def build_analysis_package(match, hform, aform, h2h,
                            h_stand, a_stand, h_scorer, a_scorer):
    """
    Tüm verileri Groq'un anlayacağı formata dönüştür.
    Her alan açıklamalı ve yapılandırılmış olmalı.
    """
    h    = match["homeTeam"]["name"]
    a    = match["awayTeam"]["name"]
    hid  = match["homeTeam"]["id"]
    aid  = match["awayTeam"]["id"]
    comp = match.get("competition", {}).get("name", "?")
    utc  = match.get("utcDate", "")[:16].replace("T", " ")

    # xG hesapla
    hxg    = calc_team_xg(hform, aform, is_home=True)
    axg    = calc_team_xg(aform, hform, is_home=False)
    h_htxg = calc_ht_xg(hform, hxg)
    a_htxg = calc_ht_xg(aform, axg)

    # Skor matrisleri
    ms_mat = build_score_matrix(hxg, axg)
    ht_mat = build_score_matrix(h_htxg, a_htxg, max_goals=4)

    # İstatistikler
    stats  = calc_all_stats(ms_mat, ht_mat)
    top_ms = sorted(ms_mat.items(), key=lambda x: -x[1])[:10]
    top_ht = sorted(ht_mat.items(), key=lambda x: -x[1])[:6]

    # Yardımcı fonksiyonlar
    def fv(d, key, default=0):
        """Form verisinden güvenli değer al."""
        return (d.get(key, default) if d else default)

    def fl(d, key):
        """Form verisinden liste al ve formatla."""
        lst = (d.get(key, []) if d else [])
        return " | ".join(lst[:6]) if lst else "Veri yok"

    # Golcü formatla
    def scorer_str(sc):
        if not sc:
            return "Veri yok"
        return f"{sc.get('name','?')} — {sc.get('goals',0)} gol / {sc.get('assists',0)} asist ({sc.get('played',0)} maç)"

    # Paketi oluştur
    NL = "\n"
    pkg = f"""{'='*60}
MAÇ    : {h} vs {a}
LİG    : {comp}
TARİH  : {utc} UTC
{'='*60}

━━━━ PUAN DURUMU ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{h}:
  {format_standing(h_stand)}
{a}:
  {format_standing(a_stand)}

━━━━ SEZONUN GOL KRALI ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{h}: {scorer_str(h_scorer)}
{a}: {scorer_str(a_scorer)}

━━━━ {h.upper()} — FORM ANALİZİ (son {fv(hform,'n',0)} maç) ━━━━━━━━━━━━━━

MS Form Serisi   : {fv(hform,'form_str','?')}
  Form Puanı     : {fv(hform,'pts5',0)}/15  (%{fv(hform,'pts_pct',0)} verim)
  Mevcut Seri    : {fv(hform,'streak','?')}

İY Form Serisi   : {fv(hform,'ht_form','?')}

Son MS Skorları  : {fl(hform,'last_ms_scores')}
Son İY Skorları  : {fl(hform,'last_ht_scores')}

Genel Gol Ort    : {fv(hform,'avg_gf',0)} attı / {fv(hform,'avg_gc',0)} yedi (maç başı)
İç Saha Gol Ort  : {fv(hform,'home_avg_gf',0)} attı / {fv(hform,'home_avg_gc',0)} yedi ({fv(hform,'home_n',0)} maç)
Deplasman Gol Ort: {fv(hform,'away_avg_gf',0)} attı / {fv(hform,'away_avg_gc',0)} yedi ({fv(hform,'away_n',0)} maç)
İY Gol Ort       : {fv(hform,'ht_avg_gf',0)} attı / {fv(hform,'ht_avg_gc',0)} yedi
2Y Gol Ort       : {fv(hform,'st_avg_gf',0)} attı / {fv(hform,'st_avg_gc',0)} yedi

GOL ZAMANLAMASI (← 2/1 & 1/2 ANALİZİ İÇİN KRİTİK):
  İLK YARI  : %{fv(hform,'ht_gol_pct',45)} → Ortalama {fv(hform,'ht_avg_gf',0)} gol/maç
  İKİNCİ YARİ: %{fv(hform,'st_gol_pct',55)} → Ortalama {fv(hform,'st_avg_gf',0)} gol/maç
  Yorum: {"2Y ağırlıklı gol atan takım (dönüş senaryoları için önemli)" if fv(hform,'st_gol_pct',55) > 58 else "İY ağırlıklı gol atan takım" if fv(hform,'ht_gol_pct',45) > 55 else "Dengeli gol dağılımı"}

Gol/Maç İstatistikleri:
  KG VAR     : {fv(hform,'btts_count',0)}/{fv(hform,'n',0)} maç (%{pct(fv(hform,'btts_count',0), fv(hform,'n',1))})
  1.5 Üst    : {fv(hform,'over15_count',0)}/{fv(hform,'n',0)} maç (%{pct(fv(hform,'over15_count',0), fv(hform,'n',1))})
  2.5 Üst    : {fv(hform,'over25_count',0)}/{fv(hform,'n',0)} maç (%{pct(fv(hform,'over25_count',0), fv(hform,'n',1))})
  3.5 Üst    : {fv(hform,'over35_count',0)}/{fv(hform,'n',0)} maç (%{pct(fv(hform,'over35_count',0), fv(hform,'n',1))})
  Kuru Kaldı : {fv(hform,'clean_sheets',0)}/{fv(hform,'n',0)} maç (%{pct(fv(hform,'clean_sheets',0), fv(hform,'n',1))})
  Gol Atamadı: {fv(hform,'failed_to_score',0)}/{fv(hform,'n',0)} maç (%{pct(fv(hform,'failed_to_score',0), fv(hform,'n',1))})

━━━━ {a.upper()} — FORM ANALİZİ (son {fv(aform,'n',0)} maç) ━━━━━━━━━━━━━━

MS Form Serisi   : {fv(aform,'form_str','?')}
  Form Puanı     : {fv(aform,'pts5',0)}/15  (%{fv(aform,'pts_pct',0)} verim)
  Mevcut Seri    : {fv(aform,'streak','?')}

İY Form Serisi   : {fv(aform,'ht_form','?')}

Son MS Skorları  : {fl(aform,'last_ms_scores')}
Son İY Skorları  : {fl(aform,'last_ht_scores')}

Genel Gol Ort    : {fv(aform,'avg_gf',0)} attı / {fv(aform,'avg_gc',0)} yedi (maç başı)
İç Saha Gol Ort  : {fv(aform,'home_avg_gf',0)} attı / {fv(aform,'home_avg_gc',0)} yedi ({fv(aform,'home_n',0)} maç)
Deplasman Gol Ort: {fv(aform,'away_avg_gf',0)} attı / {fv(aform,'away_avg_gc',0)} yedi ({fv(aform,'away_n',0)} maç)
İY Gol Ort       : {fv(aform,'ht_avg_gf',0)} attı / {fv(aform,'ht_avg_gc',0)} yedi
2Y Gol Ort       : {fv(aform,'st_avg_gf',0)} attı / {fv(aform,'st_avg_gc',0)} yedi

GOL ZAMANLAMASI (← 2/1 & 1/2 ANALİZİ İÇİN KRİTİK):
  İLK YARI  : %{fv(aform,'ht_gol_pct',45)} → Ortalama {fv(aform,'ht_avg_gf',0)} gol/maç
  İKİNCİ YARİ: %{fv(aform,'st_gol_pct',55)} → Ortalama {fv(aform,'st_avg_gf',0)} gol/maç
  Yorum: {"2Y ağırlıklı gol atan takım (dönüş senaryoları için önemli)" if fv(aform,'st_gol_pct',55) > 58 else "İY ağırlıklı gol atan takım" if fv(aform,'ht_gol_pct',45) > 55 else "Dengeli gol dağılımı"}

Gol/Maç İstatistikleri:
  KG VAR     : {fv(aform,'btts_count',0)}/{fv(aform,'n',0)} maç (%{pct(fv(aform,'btts_count',0), fv(aform,'n',1))})
  1.5 Üst    : {fv(aform,'over15_count',0)}/{fv(aform,'n',0)} maç (%{pct(fv(aform,'over15_count',0), fv(aform,'n',1))})
  2.5 Üst    : {fv(aform,'over25_count',0)}/{fv(aform,'n',0)} maç (%{pct(fv(aform,'over25_count',0), fv(aform,'n',1))})
  3.5 Üst    : {fv(aform,'over35_count',0)}/{fv(aform,'n',0)} maç (%{pct(fv(aform,'over35_count',0), fv(aform,'n',1))})
  Kuru Kaldı : {fv(aform,'clean_sheets',0)}/{fv(aform,'n',0)} maç (%{pct(fv(aform,'clean_sheets',0), fv(aform,'n',1))})
  Gol Atamadı: {fv(aform,'failed_to_score',0)}/{fv(aform,'n',0)} maç (%{pct(fv(aform,'failed_to_score',0), fv(aform,'n',1))})

━━━━ H2H GEÇMİŞİ — Son {h2h.get('n', 0)} Maç ━━━━━━━━━━━━━━━━━━━━━

MAÇSONU SONUÇLARI:
  {h}: {h2h.get('hw',0)} Galibiyet | Beraberlik: {h2h.get('dr',0)} | {a}: {h2h.get('aw',0)} Galibiyet
  Yüzdeler: {h} %{h2h.get('hw_pct',0)} | Beraberlik %{h2h.get('dr_pct',0)} | {a} %{h2h.get('aw_pct',0)}

İLK YARI SONUÇLARI:
  {h}: {h2h.get('ht_hw',0)} Galibiyet | Beraberlik: {h2h.get('ht_dr',0)} | {a}: {h2h.get('ht_aw',0)} Galibiyet
  Yüzdeler: {h} %{h2h.get('ht_hw_pct',0)} | Beraberlik %{h2h.get('ht_dr_pct',0)} | {a} %{h2h.get('ht_aw_pct',0)}

SON MS SKORLARI : {' | '.join(h2h.get('ms_scores', [])[:6])}
SON İY SKORLARI : {' | '.join(h2h.get('ht_scores', [])[:6])}

GOL İSTATİSTİKLERİ:
  Maç Başı Ort Gol: {h2h.get('avg_goals','?')}
  2.5 Üst: {h2h.get('over25',0)}/{h2h.get('n',0)} maç (%{h2h.get('over25_pct',0)})
  3.5 Üst: {h2h.get('over35',0)}/{h2h.get('n',0)} maç (%{h2h.get('over35_pct',0)})
  KG VAR : {h2h.get('btts',0)}/{h2h.get('n',0)} maç (%{h2h.get('btts_pct',0)})

DÖNÜŞ GEÇMİŞİ (← ÇOK ÖNEMLİ):
  2/1 Dönüş (İY {a} önde → MS {h} kazandı): {h2h.get('rev_21',0)}/{h2h.get('n',0)} maç → %{h2h.get('rev_21_pct',0)}
  1/2 Dönüş (İY {h} önde → MS {a} kazandı): {h2h.get('rev_12',0)}/{h2h.get('n',0)} maç → %{h2h.get('rev_12_pct',0)}
  X/1 Dönüş (İY berabere → MS {h} kazandı): {h2h.get('rev_x1',0)}/{h2h.get('n',0)} maç → %{h2h.get('rev_x1_pct',0)}
  X/2 Dönüş (İY berabere → MS {a} kazandı): {h2h.get('rev_x2',0)}/{h2h.get('n',0)} maç → %{h2h.get('rev_x2_pct',0)}

━━━━ POİSSON xG MODELİ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Beklenen Gol (xG):
  {h} MS-xG  = {hxg}   |  {a} MS-xG  = {axg}
  {h} İY-xG  = {h_htxg}  |  {a} İY-xG  = {a_htxg}
  Toplam xG  = {round(hxg + axg, 2)}

MAÇSONU OLASILIKları (Poisson):
  1 (Ev Gal.) = %{stats['p1']}
  X (Beraberlik) = %{stats['px']}
  2 (Dep. Gal.) = %{stats['p2']}

İLK YARI OLASILIKları (Poisson):
  1 = %{stats['iy1']}  |  X = %{stats['iyx']}  |  2 = %{stats['iy2']}

EN OLASILIKLI 10 MS SKORU:
{NL.join(f"  {hg}-{ag}  →  %{round(prob, 2)}" for (hg, ag), prob in top_ms)}

EN OLASILIKLI 6 İY SKORU:
{NL.join(f"  {hg}-{ag}  →  %{round(prob, 2)}" for (hg, ag), prob in top_ht)}

İY/MS 9 KOMBİNASYON (en yüksekten düşüğe):
{NL.join(f"  {k}  →  %{round(v, 2)}" for k, v in stats['combos'])}

GOL SAYISI TAHMİNLERİ:
  1.5 Üst = %{stats['u15']}  |  1.5 Alt = %{round(100 - stats['u15'], 1)}
  2.5 Üst = %{stats['u25']}  |  2.5 Alt = %{round(100 - stats['u25'], 1)}
  3.5 Üst = %{stats['u35']}  |  3.5 Alt = %{round(100 - stats['u35'], 1)}
  4.5 Üst = %{stats['u45']}  |  4.5 Alt = %{round(100 - stats['u45'], 1)}
  KG VAR  = %{stats['kg_var']}  |  KG YOK = %{stats['kg_yok']}

DÖNÜŞ OLASILIKları (MODEL):
  2/1 (İY {a} önde → MS {h} kazanır): %{stats['rev_21_model']}
    H2H karşılığı: %{h2h.get('rev_21_pct', 0)} (gerçek geçmiş)
  1/2 (İY {h} önde → MS {a} kazanır): %{stats['rev_12_model']}
    H2H karşılığı: %{h2h.get('rev_12_pct', 0)} (gerçek geçmiş)
  X/1 (İY berabere → MS {h} kazanır): %{stats['rev_x1_model']}
  X/2 (İY berabere → MS {a} kazanır): %{stats['rev_x2_model']}
{'='*60}"""

    return pkg, hxg, axg, h_htxg, a_htxg, stats

# ═══════════════════════════════════════════════════
# GROQ API — ANALİZ
# ═══════════════════════════════════════════════════

GROQ_SYSTEM_PROMPT = """Sen dünyanın en iyi profesyonel futbol bahis analistlerinden birisin.
Sana verilen ayrıntılı maç veri paketini analiz ederek 9 maddelik kapsamlı rapor üret.

TEMEL KURALLAR:
1. Sadece verilen veriye dayan — uydurma, tahmin etme
2. Her tahmin için yüzde olasılık ver
3. İY skoru ve MS skorunu MUTLAKA AYRI AYRI tahmin et
4. "Gol Zamanlama" (%İY vs %2Y) verisini 2/1 ve 1/2 analizinde mutlaka kullan
5. H2H dönüş geçmişini (kaç maçta oldu) model ihtimaliyle karşılaştır
6. Türkçe yaz, profesyonel bahis dili kullan

---

## 1) EN OLASI MS SKORU + İY SKORU

**MS Tahmini:** X-Y (%...)
Gerekçe: [xG değerleri + form trendi + H2H sonuçlar + puan durumu motivasyonu]

**İY Tahmini:** X-Y (%...)
Gerekçe: [İY xG + İY form serisi + H2H İY sonuçları + gol zamanlama verisi]

İlk 45 dakikada taktik üstünlük: [Kim? Neden? Gol zamanlama destekliyor mu?]

---

## 2) ALTERNATİF SKOR DAĞILIMI

**MS için en az 8 skor:**
X-Y (%...) — [neden bu skor mümkün / az mümkün]
...

**İY için en az 4 skor:**
X-Y (%...) — [kısa gerekçe]
...

---

## 3) İY / MS TAHMİNİ — DETAYLI

**İlk Yarı:**
1=%...  X=%...  2=%...
Gerekçe: [İY form, İY H2H, İY xG, tempo analizi]

**Maç Sonu:**
1=%...  X=%...  2=%...
Gerekçe: [MS form, H2H, xG, puan durumu]

**İY/MS Kombinasyon Yorumu (en önemli 3 tanesi):**
- [Örn: 1/1 %...] → Senaryo: "İlk yarıda X olur çünkü... İkinci yarıda Y olur çünkü..."
- [Örn: X/1 %...] → Senaryo: "..."
- [Örn: 1/X %...] → Senaryo: "..."

**Tüm 9 kombinasyon (listele):**

---

## 4) GOL SAYISI TAHMİNLERİ — DETAYLI

**KG VAR:** %... — Gerekçe: [her iki takımın son maçlardaki KG istatistikleri]
**KG YOK:** %...

**Gol Sayısı:**
1.5 Üst: %...  2.5 Üst: %...  2.5 Alt: %...
3.5 Üst: %...  4.5 Üst: %...

**Gol Dağılımı Analizi:**
- İY beklentisi: [takım A xG + takım B xG = toplam İY gol]
- 2Y beklentisi: [tahmin]
- Form trendi: [Son maçlarda gol sayısı artıyor mu azalıyor mu?]

---

## 5) 2/1 – 1/2 DÖNÜŞ ANALİZİ — EN KRİTİK BÖLÜM

### 2/1 Dönüş Analizi (İY: deplasman önde → MS: ev sahibi kazanır)
- **Model İhtimali:** %{rev_21_model}
- **H2H Geçmiş:** %{h2h_rev_21} (X/Y maçta gerçekleşti)
- **Model ↔ H2H Uyumu:** [Uyuşuyor mu? Sapma var mı?]
- **Gol Zamanlama Destekliyor mu?**
  → Ev sahibi 2Y gol yüzdesi: ... → [Dönüş için güçlü/zayıf zemin]
  → Deplasman İY gol yüzdesi: ... → [İY önde bitme ihtimali]
- **Senaryo:** "İY X-Y biter çünkü... Sonra 2Y'de şunlar olur... Ev sahibi döner çünkü..."
- **SONUÇ:** Gerçekçi mi? Neden? (1-2 cümle net yorum)

### 1/2 Dönüş Analizi (İY: ev sahibi önde → MS: deplasman kazanır)
- **Model İhtimali:** %{rev_12_model}
- **H2H Geçmiş:** %{h2h_rev_12} (X/Y maçta gerçekleşti)
- **Model ↔ H2H Uyumu:** [Uyuşuyor mu?]
- **Gol Zamanlama Destekliyor mu?**
  → Deplasman 2Y gol yüzdesi: ... → [Dönüş için güçlü/zayıf zemin]
- **Senaryo:** "İY X-Y biter çünkü... Sonra..."
- **SONUÇ:** Gerçekçi mi? Neden?

### Genel Dönüş Kararı:
**Hangi dönüş daha mümkün?** [Net, kesin yorum. Neden?]

---

## 6) FORM & GÜÇ ANALİZİ

- Mevcut seri yorumu: [Kim formda, kim çöküştе?]
- İç saha / Deplasman performans farkı önemli mi?
- Golcü gücü: [Hangi takımın golcüsü daha etkili? Son maçlardaki gol katkısı?]
- Puan durumu motivasyonu: [Kim kazanmaya daha muhtaç? Bu maça nasıl yansır?]

---

## 7) DEĞER (VALUE) TESPİTİ

- Model 1/X/2 olasılıkları ne söylüyor?
- Beklenen piyasa oranları ile karşılaştır
- En değerli bahis tipi hangisi ve neden?
- KG ve Üst-Alt'ta en değerli seçenek

---

## 8) MAÇ RİSK SEVİYESİ

**Seviye:** Düşük / Orta / Yüksek
**Gerekçe:** [Veri güvenilirliği, güç farkı, H2H tutarlılığı, belirsizlik faktörleri]

---

## 9) TAVSİYELER

🔒 **BANKO (%70+ güven):** [Tahmin] — [Gerekçe]
⚡ **ORTA RİSK (%50-70):** [Tahmin] — [Gerekçe]
💎 **SÜRPRİZ (yüksek oran, pattern destekli):** [Tahmin + beklenen oran] — [Gerekçe]
🎯 **SKOR TAHMİNİ:** İY [X-Y] + MS [X-Y] — [Gerekçe]
"""

def groq_analyze(data_package, key, model_name):
    """Groq API üzerinden Llama ile analiz yap."""
    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type":  "application/json",
            },
            json={
                "model":    model_name,
                "messages": [
                    {"role": "system", "content": GROQ_SYSTEM_PROMPT},
                    {"role": "user",   "content": data_package},
                ],
                "temperature": 0.25,
                "max_tokens":  4000,
            },
            timeout=120,
        )
        r.raise_for_status()
        usage = r.json().get("usage", {})
        if debug:
            st.caption(f"🐛 Groq token: {usage.get('total_tokens', '?')}")
        return r.json()["choices"][0]["message"]["content"]
    except requests.exceptions.HTTPError as e:
        body = e.response.text if hasattr(e, 'response') else str(e)
        return f"❌ Groq HTTP Hatası: {e}\n{body[:300]}"
    except Exception as e:
        return f"❌ Groq Hatası: {e}"

# ═══════════════════════════════════════════════════
# SESSION STATE
# ═══════════════════════════════════════════════════
for k in ["matches", "match_data", "analyses"]:
    if k not in st.session_state:
        st.session_state[k] = [] if k == "matches" else {}

# ═══════════════════════════════════════════════════
# ANA BUTONLAR
# ═══════════════════════════════════════════════════
col1, col2, col3 = st.columns([3, 2, 2])
with col1:
    st.markdown(f"**{sel_label}** · {sel_date.strftime('%d.%m.%Y')} · Maks {max_match} maç")
with col2:
    fetch_btn = st.button("🔍 Maçları Çek", type="primary", use_container_width=True)
with col3:
    all_btn = st.button("🤖 Tümünü Analiz Et", use_container_width=True)

st.divider()

# ═══════════════════════════════════════════════════
# MAÇLARI ÇEK VE VERİ HAZIRLA
# ═══════════════════════════════════════════════════
if fetch_btn:
    if not fd_key:
        st.error("⛔ football-data.org API Key giriniz (sol sidebar).")
        st.stop()

    with st.spinner("📡 Maçlar çekiliyor..."):
        matches = get_matches_on_date(
            fd_key, sel_code,
            sel_date.strftime("%Y-%m-%d"),
            max_match
        )

    if not matches:
        st.error(
            f"**{sel_date.strftime('%d.%m.%Y')} · {sel_label}** için "
            f"planlanmış maç bulunamadı.\n\n"
            f"Farklı bir tarih veya lig dene. "
            f"Debug modunu aç ve API yanıtını kontrol et."
        )
        st.stop()

    st.session_state.matches    = matches
    st.session_state.match_data = {}
    st.session_state.analyses   = {}
    st.success(f"✅ {len(matches)} maç bulundu!")

    # Puan durumu ve golcüler
    with st.spinner("📊 Puan durumu ve golcüler çekiliyor..."):
        standings = get_league_standings(fd_key, sel_code)
        scorers   = get_top_scorers(fd_key, sel_code)
        time.sleep(0.5)

    bar = st.progress(0)
    for i, m in enumerate(matches):
        mid = m["id"]
        hid = m["homeTeam"]["id"]
        aid = m["awayTeam"]["id"]
        hn  = m["homeTeam"]["name"]
        an  = m["awayTeam"]["name"]

        bar.progress(
            i / len(matches),
            text=f"({i+1}/{len(matches)}) {hn} – {an} verileri hazırlanıyor..."
        )

        # Form verileri
        hf_raw = get_team_last_matches(fd_key, hid, n_form) if use_form else []
        af_raw = get_team_last_matches(fd_key, aid, n_form) if use_form else []
        hform  = parse_team_form(hf_raw, hid)
        aform  = parse_team_form(af_raw, aid)
        time.sleep(0.4)

        # H2H
        h2h_raw = get_h2h_matches(fd_key, mid, n_h2h) if use_h2h else []
        h2h     = parse_h2h_deep(h2h_raw, hid)
        time.sleep(0.4)

        # Puan durumu
        h_stand = find_team_standing(standings, hid)
        a_stand = find_team_standing(standings, aid)

        # Golcüler
        h_scorer = find_team_top_scorer(scorers, hid)
        a_scorer = find_team_top_scorer(scorers, aid)

        # Veri paketi oluştur
        pkg, hxg, axg, h_htxg, a_htxg, stats = build_analysis_package(
            m, hform, aform, h2h,
            h_stand, a_stand, h_scorer, a_scorer
        )

        st.session_state.match_data[mid] = {
            "match":   m,
            "pkg":     pkg,
            "hform":   hform,
            "aform":   aform,
            "h2h":     h2h,
            "hxg":     hxg,
            "axg":     axg,
            "h_htxg":  h_htxg,
            "a_htxg":  a_htxg,
            "stats":   stats,
        }

    bar.progress(1.0, text="Tüm veriler hazır!")
    time.sleep(0.5)
    bar.empty()
    st.success("✅ Veriler hazır! Maçları aç → Analiz Et")

# ═══════════════════════════════════════════════════
# TOPLU ANALİZ
# ═══════════════════════════════════════════════════
if all_btn:
    if not st.session_state.match_data:
        st.warning("Önce Maçları Çek!")
    elif not groq_key:
        st.error("⛔ Groq API Key giriniz (sol sidebar).")
    else:
        bar2  = st.progress(0)
        items = list(st.session_state.match_data.items())
        for i, (mid, d) in enumerate(items):
            hn = d["match"]["homeTeam"]["name"]
            an = d["match"]["awayTeam"]["name"]
            bar2.progress(
                i / len(items),
                text=f"({i+1}/{len(items)}) Groq analiz: {hn} – {an}"
            )
            result = groq_analyze(d["pkg"], groq_key, groq_model)
            st.session_state.analyses[mid] = result
            time.sleep(0.5)

        bar2.progress(1.0, text="Tamamlandı!")
        time.sleep(0.3)
        bar2.empty()
        st.success("✅ Tüm analizler tamamlandı!")

# ═══════════════════════════════════════════════════
# MAÇ LİSTESİ
# ═══════════════════════════════════════════════════
if st.session_state.matches:
    st.markdown(f"## 📋 Maçlar ({len(st.session_state.matches)})")

    for m in st.session_state.matches:
        mid  = m["id"]
        hn   = m["homeTeam"]["name"]
        an   = m["awayTeam"]["name"]
        comp = m.get("competition", {}).get("name", "")
        utc  = m.get("utcDate", "")[:16].replace("T", " ")
        done = mid in st.session_state.analyses
        d    = st.session_state.match_data.get(mid, {})

        label = f"{'✅' if done else '⚽'}  {hn}  –  {an}  |  {comp}  |  {utc}"

        with st.expander(label):
            # Özet bilgiler
            if d.get("hxg"):
                h2 = d.get("h2h", {})
                st.markdown(
                    f"<span class='opill'>🏠 {hn} MS-xG:{d['hxg']} İY-xG:{d.get('h_htxg','?')}</span>"
                    f"<span class='opill'>✈️ {an} MS-xG:{d['axg']} İY-xG:{d.get('a_htxg','?')}</span>",
                    unsafe_allow_html=True
                )
            if d.get("hform") and d.get("aform"):
                hf = d["hform"]; af = d["aform"]
                h2 = d.get("h2h", {})
                st.markdown(
                    f"<span class='opill'>{hn}: {hf.get('form_str','?')} ({hf.get('pts5',0)}/15p)</span>"
                    f"<span class='opill'>{an}: {af.get('form_str','?')} ({af.get('pts5',0)}/15p)</span>"
                    f"<span class='opill'>H2H: {h2.get('hw',0)}G-{h2.get('dr',0)}B-{h2.get('aw',0)}M</span>"
                    f"<span class='opill'>2/1: %{h2.get('rev_21_pct',0)} | 1/2: %{h2.get('rev_12_pct',0)}</span>",
                    unsafe_allow_html=True
                )
                # Gol zamanlama özeti
                st.markdown(
                    f"<span class='opill'>⏱️ {hn} gol: %{hf.get('ht_gol_pct',45)}İY/%{hf.get('st_gol_pct',55)}2Y</span>"
                    f"<span class='opill'>⏱️ {an} gol: %{af.get('ht_gol_pct',45)}İY/%{af.get('st_gol_pct',55)}2Y</span>",
                    unsafe_allow_html=True
                )

            # Ham veri paketi
            if d.get("pkg"):
                with st.expander("📊 Ham Veri Paketi (Groq'a gönderilen)"):
                    st.markdown(
                        f"<div class='dbox'>{d['pkg']}</div>",
                        unsafe_allow_html=True
                    )

            # Analiz butonu
            col_a, col_b = st.columns([3, 1])
            with col_b:
                if st.button("🤖 Analiz Et", key=f"btn_{mid}"):
                    if not groq_key:
                        st.error("⛔ Groq API Key giriniz.")
                    elif not d.get("pkg"):
                        st.warning("Önce Maçları Çek!")
                    else:
                        with st.spinner(f"🦙 Groq Llama: {hn} – {an} analiz ediliyor..."):
                            result = groq_analyze(d["pkg"], groq_key, groq_model)
                            st.session_state.analyses[mid] = result

            # Analiz sonucu göster
            if mid in st.session_state.analyses:
                st.markdown("---")
                st.markdown(
                    f"<div class='abox'>{st.session_state.analyses[mid]}</div>",
                    unsafe_allow_html=True
                )
                col_dl, col_clear = st.columns([3, 1])
                with col_dl:
                    st.download_button(
                        "⬇️ Analizi İndir (.txt)",
                        data=st.session_state.analyses[mid],
                        file_name=f"{hn}_vs_{an}_{sel_date}.txt",
                        mime="text/plain",
                        key=f"dl_{mid}"
                    )

# ═══════════════════════════════════════════════════
# BAŞLANGIÇ EKRANI
# ═══════════════════════════════════════════════════
else:
    st.markdown("""
    <div class="guide" style="font-size: 0.88rem; line-height: 2.1">
    <b style="color:#60a5fa; font-size: 1rem">
        ⚽ Tamamen Ücretsiz — Sadece 2 Key Yeterli
    </b><br><br>

    <b>1) Groq API Key</b> (Llama 3.3 70B — ÜCRETSİZ)<br>
    → <a href="https://console.groq.com" target="_blank">console.groq.com</a>
    → Google hesabınla giriş → API Keys → Create Key<br>
    → Key <b>gsk_</b> ile başlar · 500.000 token/gün · Kredi kartı yok<br><br>

    <b>2) football-data.org Key</b> (ÜCRETSİZ)<br>
    → <a href="https://www.football-data.org/client/register" target="_blank">
       football-data.org/client/register</a>
    → E-posta ile kayıt → Key mail'e gelir<br><br>

    <b>Analiz Kapsamı:</b><br>
    ✅ İY skoru tahmini + MS skoru tahmini AYRI AYRI<br>
    ✅ Gol zamanlama (%İY vs %2Y) — 2/1 & 1/2 analizinin temeli<br>
    ✅ H2H: Kaç maçta 2/1, kaç maçta 1/2 dönüş yaşandı?<br>
    ✅ 9 İY/MS kombinasyonu — her biri için senaryo<br>
    ✅ İç saha / Deplasman ayrı gol ortalaması<br>
    ✅ 2Y gol ortalaması (İY'den ayrı hesap)<br>
    ✅ Poisson xG modeli (İY-xG + MS-xG ayrı)<br>
    ✅ Sezonun golcüsü + puan durumu<br>
    ✅ Groq Llama 3.3 70B ile ChatGPT seviyesi yorum
    </div>
    """, unsafe_allow_html=True)
