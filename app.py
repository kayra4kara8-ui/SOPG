import streamlit as st
import requests
from datetime import date
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
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.hero {
    background: linear-gradient(135deg, #0a0e1a 0%, #111827 60%, #0f2040 100%);
    border: 1px solid #1e3a5f; border-radius: 14px;
    padding: 2rem 2.5rem; margin-bottom: 2rem; text-align: center;
}
.hero h1 { color: #60a5fa; margin: 0; font-size: 2rem; font-weight: 700; letter-spacing: -0.5px; }
.hero p  { color: #6b7280; margin: 0.5rem 0 0; font-size: 0.9rem; }

.key-guide {
    background: #0f1923; border: 1px solid #1e3a5f;
    border-left: 3px solid #3b82f6; border-radius: 8px;
    padding: 0.9rem 1rem; font-size: 0.82rem; color: #9ca3af;
    line-height: 1.9; margin-bottom: 1rem;
}
.key-guide a { color: #60a5fa; }
.key-guide b { color: #e5e7eb; }

.odd-pill {
    display: inline-block; background: #1f2937;
    border: 1px solid #374151; color: #d1d5db;
    padding: 3px 10px; border-radius: 20px;
    font-size: 0.78rem; margin: 2px 3px 2px 0;
}
.section-title {
    color: #60a5fa; font-size: 0.75rem; font-weight: 600;
    letter-spacing: 0.1em; text-transform: uppercase;
    border-bottom: 1px solid #1f2937; padding-bottom: 5px;
    margin: 1.2rem 0 0.6rem;
}
.analysis-box {
    background: #0a0e1a; border: 1px solid #1e3a5f;
    border-radius: 10px; padding: 1.4rem 1.6rem;
    font-size: 0.84rem; color: #e5e7eb;
    line-height: 1.95; white-space: pre-wrap;
    max-height: 750px; overflow-y: auto;
    font-family: 'Courier New', monospace;
}
.data-pill {
    display: inline-block; background: #111827;
    border: 1px solid #1f2937; color: #9ca3af;
    padding: 2px 8px; border-radius: 4px;
    font-size: 0.75rem; margin: 1px 2px;
}
.warn-box {
    background: #1a1200; border: 1px solid #92400e;
    border-left: 3px solid #f59e0b; border-radius: 6px;
    padding: 0.7rem 1rem; font-size: 0.82rem; color: #fcd34d;
    margin: 0.5rem 0;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
  <h1>⚽ PRO BETTING ANALYST ENGINE</h1>
  <p>API-Football (Kadro · xG · Dizilim · Bireysel İstatistik) + Claude AI Derin Analiz</p>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🔑 API Anahtarları")

    st.markdown("""
    <div class="key-guide">
    <b style="color:#60a5fa">1) API-Football (apisports.io)</b><br>
    → <a href="https://dashboard.api-football.com/register" target="_blank">dashboard.api-football.com/register</a><br>
    → E-posta + şifre → Kayıt ol → Dashboard'da API Key var<br>
    → Ücretsiz · 100 istek/gün · Kart YOK<br><br>
    <b style="color:#60a5fa">2) Claude API Key</b><br>
    → <a href="https://console.anthropic.com" target="_blank">console.anthropic.com</a><br>
    → API Keys → Create Key<br>
    → ~$0.003/analiz (çok ucuz)
    </div>
    """, unsafe_allow_html=True)

    api_football_key = st.text_input(
        "API-Football Key",
        type="password",
        placeholder="apisports.io dashboard'dan al",
    )
    claude_key = st.text_input(
        "Claude API Key",
        type="password",
        placeholder="sk-ant-...",
    )

    st.divider()
    st.markdown("## ⚙️ Filtreler")

    LEAGUES = {
        "Premier League 🏴󠁧󠁢󠁥󠁮󠁧󠁿": 39,
        "La Liga 🇪🇸": 140,
        "Bundesliga 🇩🇪": 78,
        "Serie A 🇮🇹": 135,
        "Ligue 1 🇫🇷": 61,
        "Süper Lig 🇹🇷": 203,
        "Champions League ⭐": 2,
        "Europa League 🌍": 3,
        "Eredivisie 🇳🇱": 88,
        "Primeira Liga 🇵🇹": 94,
    }

    sel_label  = st.selectbox("Lig Seç", list(LEAGUES.keys()))
    sel_league = LEAGUES[sel_label]
    sel_date   = st.date_input("Maç Tarihi", value=date.today())
    # Sezon otomatik hesapla
    auto_season = sel_date.year if sel_date.month >= 7 else sel_date.year - 1
    sel_season = auto_season
    st.caption(f"Sezon: {auto_season} (otomatik)")
    max_match  = st.slider("Maks. Maç Sayısı", 1, 15, 8)

    st.divider()
    st.markdown("### 📊 Analiz Derinliği")
    use_lineups  = st.checkbox("Kadro & Dizilim", value=True)
    use_players  = st.checkbox("Oyuncu İstatistikleri", value=True)
    use_h2h      = st.checkbox("H2H Geçmişi", value=True)
    use_injuries = st.checkbox("Sakat/Cezalı", value=True)
    n_h2h        = st.slider("H2H Maç Sayısı", 3, 10, 6)

    st.divider()
    debug_mode = st.checkbox("🐛 Debug Modu (API yanıtını göster)", value=False)
    st.caption("API-Football free: 100 istek/gün")

# ─────────────────────────────────────────────
# API-FOOTBALL (api-sports.io doğrudan)
# ─────────────────────────────────────────────
AF_BASE = "https://v3.football.api-sports.io"

def af_get(endpoint, key, params=None, debug=False):
    """api-sports.io doğrudan istek — RapidAPI değil."""
    headers = {"x-apisports-key": key}
    try:
        r = requests.get(f"{AF_BASE}/{endpoint}", headers=headers,
                         params=params or {}, timeout=15)
        if r.status_code == 429:
            st.warning("⏳ Rate limit — 60s bekleniyor...")
            time.sleep(62)
            r = requests.get(f"{AF_BASE}/{endpoint}", headers=headers,
                             params=params or {}, timeout=15)
        remaining = r.headers.get("x-ratelimit-requests-remaining", "?")
        if r.status_code == 200:
            data = r.json()
            if debug:
                st.write(f"**DEBUG [{endpoint}]** params={params} | status=200 | kalan={remaining}")
                st.write(f"response count: {len(data.get('response',[]))}")
                errors = data.get('errors', {})
                if errors:
                    st.error(f"API errors: {errors}")
            return data, remaining
        else:
            st.error(f"API Hatası {r.status_code} [{endpoint}]: {r.text[:300]}")
            return {}, remaining
    except Exception as e:
        st.error(f"Bağlantı hatası [{endpoint}]: {e}")
        return {}, "?"

def get_fixtures_today(key, league_id, season, target_date, limit, debug=False):
    """Maçları çek — status filtresi yok, tüm durumlar gelsin."""
    params = {"league": league_id, "season": season, "date": target_date}
    data, rem = af_get("fixtures", key, params, debug=debug)
    fixtures = data.get("response", [])

    # Sonuç yoksa bir önceki sezonu dene
    if not fixtures:
        alt_season = season - 1
        if debug:
            st.info(f"Sezon {season} boş — {alt_season} deneniyor...")
        params2 = {"league": league_id, "season": alt_season, "date": target_date}
        data2, rem = af_get("fixtures", key, params2, debug=debug)
        fixtures = data2.get("response", [])

    # Oynanmış maçları (FT, AET, PEN) hariç tut, planlanmış ve oynanıyor olanları al
    # Eğer tarih bugün veya gelecekse NS/TBD/1H/2H/HT hepsini al
    # Eğer hiç planlanmış yoksa tümünü döndür (kullanıcı geçmiş tarihe bakmış olabilir)
    scheduled = [f for f in fixtures if f.get("fixture", {}).get("status", {}).get("short") in
                 ("NS", "TBD", "1H", "2H", "HT", "ET", "BT", "P", "SUSP", "INT", "PST", "CANC", "ABD", "WO", "AWD")]
    if scheduled:
        return scheduled[:limit], rem
    return fixtures[:limit], rem

def get_fixture_stats(key, fixture_id):
    """Maç bazlı takım istatistikleri (şut, isabetli şut, top hakimiyeti vb.)"""
    data, _ = af_get("fixtures/statistics", key, {"fixture": fixture_id})
    return data.get("response", [])

def get_lineups(key, fixture_id):
    """Kadro ve dizilim."""
    data, _ = af_get("fixtures/lineups", key, {"fixture": fixture_id})
    return data.get("response", [])

def get_player_stats_fixture(key, fixture_id):
    """Oyuncu bazlı istatistikler (şut, pas, dribbling, rating vb.)"""
    data, _ = af_get("fixtures/players", key, {"fixture": fixture_id})
    return data.get("response", [])

def get_h2h(key, team1, team2, n):
    data, _ = af_get("fixtures/headtohead", key, {
        "h2h": f"{team1}-{team2}", "last": n, "status": "FT"
    })
    return data.get("response", [])

def get_team_last_matches(key, team_id, league_id, season, n=8):
    data, _ = af_get("fixtures", key, {
        "team": team_id, "league": league_id, "season": season,
        "last": n, "status": "FT"
    })
    return data.get("response", [])

def get_team_season_stats(key, team_id, league_id, season):
    data, _ = af_get("teams/statistics", key, {
        "team": team_id, "league": league_id, "season": season
    })
    return data.get("response", {})

def get_injuries(key, team_id, fixture_id):
    data, _ = af_get("injuries", key, {
        "team": team_id, "fixture": fixture_id
    })
    return data.get("response", [])

def get_player_season_stats(key, player_id, season, league_id):
    data, _ = af_get("players", key, {
        "id": player_id, "season": season, "league": league_id
    })
    resp = data.get("response", [])
    if resp:
        return resp[0].get("statistics", [{}])[0]
    return {}

def get_standings(key, league_id, season):
    data, _ = af_get("standings", key, {"league": league_id, "season": season})
    try:
        return data["response"][0]["league"]["standings"][0]
    except:
        return []

def get_odds(key, fixture_id):
    data, _ = af_get("odds", key, {"fixture": fixture_id, "bookmaker": 6})
    try:
        bets = data["response"][0]["bookmakers"][0]["bets"]
        result = {}
        for bet in bets:
            name = bet["name"]
            vals = {v["value"]: v["odd"] for v in bet["values"]}
            if name == "Match Winner":
                result["ms"] = vals
            elif name == "Both Teams Score":
                result["btts"] = vals
            elif name == "Goals Over/Under":
                result["goals"] = vals
            elif name == "First Half Winner":
                result["iy"] = vals
            elif name == "Double Chance":
                result["dc"] = vals
        return result
    except:
        return {}

# ─────────────────────────────────────────────
# VERİ İŞLEME YARDIMCILARI
# ─────────────────────────────────────────────

def parse_form(matches, team_id):
    results, goals_for, goals_ag = [], [], []
    ht_results, ht_gf, ht_ga = [], [], []
    for m in matches:
        hid = m["teams"]["home"]["id"]
        hg  = (m["goals"]["home"] or 0)
        ag  = (m["goals"]["away"] or 0)
        hht = (m["score"]["halftime"]["home"] or 0)
        aht = (m["score"]["halftime"]["away"] or 0)
        if hid == team_id:
            gf, gc = hg, ag; ht_gf_v, ht_ga_v = hht, aht
        else:
            gf, gc = ag, hg; ht_gf_v, ht_ga_v = aht, hht
        results.append("G" if gf > gc else "B" if gf == gc else "M")
        goals_for.append(gf); goals_ag.append(gc)
        ht_results.append("G" if ht_gf_v > ht_ga_v else "B" if ht_gf_v == ht_ga_v else "M")
        ht_gf.append(ht_gf_v); ht_ga.append(ht_ga_v)
    return {
        "results": results,
        "form_str": "-".join(results[:5]),
        "pts5": sum({"G":3,"B":1,"M":0}[r] for r in results[:5]),
        "avg_gf": round(sum(goals_for)/len(goals_for), 2) if goals_for else 1.2,
        "avg_gc": round(sum(goals_ag)/len(goals_ag), 2) if goals_ag else 1.2,
        "ht_form": "-".join(ht_results[:5]),
        "ht_avg_gf": round(sum(ht_gf)/len(ht_gf), 2) if ht_gf else 0.6,
        "ht_avg_gc": round(sum(ht_ga)/len(ht_ga), 2) if ht_ga else 0.6,
        "btts_count": sum(1 for g, c in zip(goals_for, goals_ag) if g > 0 and c > 0),
        "over25_count": sum(1 for g, c in zip(goals_for, goals_ag) if g + c > 2),
        "total_matches": len(results),
        "clean_sheets": sum(1 for c in goals_ag if c == 0),
        "failed_to_score": sum(1 for g in goals_for if g == 0),
    }

def parse_team_stats(stats):
    if not stats:
        return {}
    gs = stats.get("goals", {})
    fx = stats.get("fixtures", {})
    return {
        "played": fx.get("played", {}).get("total", 0),
        "wins": fx.get("wins", {}).get("total", 0),
        "draws": fx.get("draws", {}).get("total", 0),
        "losses": fx.get("loses", {}).get("total", 0),
        "goals_for_avg": gs.get("for", {}).get("average", {}).get("total", "?"),
        "goals_ag_avg": gs.get("against", {}).get("average", {}).get("total", "?"),
        "goals_for_ht_avg": gs.get("for", {}).get("average", {}).get("first_half", "?"),
        "goals_ag_ht_avg": gs.get("against", {}).get("average", {}).get("first_half", "?"),
        "biggest_win": stats.get("biggest", {}).get("wins", {}).get("home", "?"),
        "formation": stats.get("lineups", [{}])[0].get("formation", "?") if stats.get("lineups") else "?",
        "clean_sheets": stats.get("clean_sheet", {}).get("total", 0),
        "failed_to_score": stats.get("failed_to_score", {}).get("total", 0),
    }

def parse_lineup(lineup_data):
    if not lineup_data:
        return None, [], []
    formation = lineup_data.get("formation", "?")
    coach = lineup_data.get("coach", {}).get("name", "?")
    starters = []
    for p in lineup_data.get("startXI", []):
        pl = p.get("player", {})
        starters.append({
            "name": pl.get("name", "?"),
            "number": pl.get("number", "?"),
            "pos": pl.get("pos", "?"),
            "grid": pl.get("grid", "?"),
        })
    subs = [p.get("player", {}).get("name", "?") for p in lineup_data.get("substitutes", [])]
    return {"formation": formation, "coach": coach}, starters, subs

def parse_player_stats(players_data, team_id):
    """Oyuncu istatistiklerini çözümle."""
    for team_block in players_data:
        if team_block.get("team", {}).get("id") == team_id:
            result = []
            for p in team_block.get("players", []):
                pinfo = p.get("player", {})
                stats = p.get("statistics", [{}])[0]
                result.append({
                    "name": pinfo.get("name", "?"),
                    "pos": stats.get("games", {}).get("position", "?"),
                    "rating": stats.get("games", {}).get("rating", None),
                    "minutes": stats.get("games", {}).get("minutes", 0),
                    "goals": stats.get("goals", {}).get("total", 0) or 0,
                    "assists": stats.get("goals", {}).get("assists", 0) or 0,
                    "shots_total": stats.get("shots", {}).get("total", 0) or 0,
                    "shots_on": stats.get("shots", {}).get("on", 0) or 0,
                    "key_passes": stats.get("passes", {}).get("key", 0) or 0,
                    "dribbles": stats.get("dribbles", {}).get("success", 0) or 0,
                })
            return result
    return []

def h2h_deep(matches, home_id):
    hw = aw = dr = 0
    total_g = []
    ht_winner = {"home": 0, "away": 0, "draw": 0}
    reversal_21 = reversal_12 = 0
    scores = []
    for m in matches:
        hid = m["teams"]["home"]["id"]
        hg  = m["goals"]["home"] or 0
        ag  = m["goals"]["away"] or 0
        hht = m["score"]["halftime"]["home"] or 0
        aht = m["score"]["halftime"]["away"] or 0
        # MS sonucu ev gözüyle
        if hid == home_id:
            if hg > ag: hw += 1
            elif hg < ag: aw += 1
            else: dr += 1
            # IY/MS dönüş
            if hht < aht and hg > ag: reversal_21 += 1
            if hht > aht and hg < ag: reversal_12 += 1
            if hht > aht: ht_winner["home"] += 1
            elif hht < aht: ht_winner["away"] += 1
            else: ht_winner["draw"] += 1
            scores.append(f"{hg}-{ag}")
        else:
            if ag > hg: hw += 1
            elif ag < hg: aw += 1
            else: dr += 1
            if aht < hht and ag > hg: reversal_21 += 1
            if aht > hht and ag < hg: reversal_12 += 1
            if aht > hht: ht_winner["home"] += 1
            elif aht < hht: ht_winner["away"] += 1
            else: ht_winner["draw"] += 1
            scores.append(f"{ag}-{hg}")
        total_g.append(hg + ag)

    n = len(matches)
    return {
        "total": n,
        "hw": hw, "dr": dr, "aw": aw,
        "avg_goals": round(sum(total_g)/n, 2) if n else 2.5,
        "over25": sum(1 for g in total_g if g > 2),
        "btts": sum(1 for m in matches if
                    (m["goals"]["home"] or 0) > 0 and (m["goals"]["away"] or 0) > 0),
        "ht_winner": ht_winner,
        "reversal_21": reversal_21,
        "reversal_12": reversal_12,
        "scores": scores,
    }

def find_standing(standings, team_id):
    for s in standings:
        if s.get("team", {}).get("id") == team_id:
            return s
    return {}

# ─────────────────────────────────────────────
# POISSON MODELI
# ─────────────────────────────────────────────

def poisson(lam, k):
    return math.exp(-lam) * (lam ** k) / math.factorial(k)

def compute_score_probs(home_xg, away_xg, max_g=6):
    probs = {}
    for h in range(max_g + 1):
        for a in range(max_g + 1):
            probs[(h, a)] = round(poisson(home_xg, h) * poisson(away_xg, a) * 100, 2)
    return probs

def compute_ht_probs(home_ht_xg, away_ht_xg, max_g=4):
    return compute_score_probs(home_ht_xg, away_ht_xg, max_g)

def odds_to_prob(odd_str):
    try:
        return round(1 / float(odd_str) * 100, 1)
    except:
        return None

# ─────────────────────────────────────────────
# KAPSAMLI PROMPT OLUŞTUR
# ─────────────────────────────────────────────

def build_deep_prompt(fixture, home_form, away_form,
                       home_stats, away_stats,
                       home_lineup, home_starters, home_subs,
                       away_lineup, away_starters, away_subs,
                       player_stats, h2h_data,
                       home_injuries, away_injuries,
                       odds, standings, home_standing, away_standing):

    h = fixture["teams"]["home"]
    a = fixture["teams"]["away"]
    comp = fixture["league"]["name"]
    dt = fixture["fixture"]["date"][:10]
    utc = fixture["fixture"]["date"][11:16]

    # xG hesapla
    hf = home_form
    af = away_form
    hs = home_stats
    as_ = away_stats

    # Sezon ortalaması
    try: h_gf_avg = float(hs.get("goals_for_avg", 1.3))
    except: h_gf_avg = 1.3
    try: h_gc_avg = float(hs.get("goals_ag_avg", 1.1))
    except: h_gc_avg = 1.1
    try: a_gf_avg = float(as_.get("goals_for_avg", 1.2))
    except: a_gf_avg = 1.2
    try: a_gc_avg = float(as_.get("goals_ag_avg", 1.2))
    except: a_gc_avg = 1.2

    # xG = (takımın sezon ortalaması * 0.4) + (son maç form ortalaması * 0.35) + (rakibin yenilen ortalaması * 0.25)
    home_xg = round(h_gf_avg * 0.40 + hf.get("avg_gf", 1.3) * 0.35 + a_gc_avg * 0.25, 2)
    away_xg = round(a_gf_avg * 0.40 + af.get("avg_gf", 1.1) * 0.35 + h_gc_avg * 0.25, 2)
    home_xg = max(0.4, home_xg)
    away_xg = max(0.4, away_xg)

    # İY xG
    try: h_ht_avg = float(hs.get("goals_for_ht_avg", home_xg * 0.42))
    except: h_ht_avg = home_xg * 0.42
    try: a_ht_avg = float(as_.get("goals_for_ht_avg", away_xg * 0.42))
    except: a_ht_avg = away_xg * 0.42
    home_ht_xg = round(h_ht_avg * 0.5 + hf.get("ht_avg_gf", home_xg*0.42) * 0.5, 2)
    away_ht_xg = round(a_ht_avg * 0.5 + af.get("ht_avg_gf", away_xg*0.42) * 0.5, 2)

    # Skor olasılıkları
    ms_probs  = compute_score_probs(home_xg, away_xg)
    ht_probs  = compute_ht_probs(home_ht_xg, away_ht_xg)

    sorted_ms = sorted(ms_probs.items(), key=lambda x: -x[1])
    sorted_ht = sorted(ht_probs.items(), key=lambda x: -x[1])

    # MS 1/X/2
    p1  = round(sum(v for (h_g,a_g),v in ms_probs.items() if h_g > a_g), 1)
    px  = round(sum(v for (h_g,a_g),v in ms_probs.items() if h_g == a_g), 1)
    p2  = round(sum(v for (h_g,a_g),v in ms_probs.items() if h_g < a_g), 1)

    # İY 1/X/2
    iy1 = round(sum(v for (h_g,a_g),v in ht_probs.items() if h_g > a_g), 1)
    iyx = round(sum(v for (h_g,a_g),v in ht_probs.items() if h_g == a_g), 1)
    iy2 = round(sum(v for (h_g,a_g),v in ht_probs.items() if h_g < a_g), 1)

    # KG / Üst-Alt
    p_h0 = poisson(home_xg, 0)
    p_a0 = poisson(away_xg, 0)
    kg_var  = round((1 - p_h0) * (1 - p_a0) * 100, 1)
    kg_yok  = round(100 - kg_var, 1)
    ust25   = round(sum(v for (h_g,a_g),v in ms_probs.items() if h_g+a_g > 2), 1)
    alt25   = round(100 - ust25, 1)
    ust35   = round(sum(v for (h_g,a_g),v in ms_probs.items() if h_g+a_g > 3), 1)
    alt35   = round(100 - ust35, 1)
    ust15   = round(sum(v for (h_g,a_g),v in ms_probs.items() if h_g+a_g > 1), 1)

    # İY/MS kombinasyonları (9 kombinasyon)
    iy_ms_combos = {}
    for (iyh, iya), iyp in ht_probs.items():
        for (msh, msa), msp in ms_probs.items():
            if msh >= iyh and msa >= iya:
                iy_res = "1" if iyh > iya else ("X" if iyh == iya else "2")
                ms_res = "1" if msh > msa else ("X" if msh == msa else "2")
                key = f"{iy_res}/{ms_res}"
                iy_ms_combos[key] = iy_ms_combos.get(key, 0) + iyp * msp / 100
    iy_ms_sorted = sorted(iy_ms_combos.items(), key=lambda x: -x[1])

    # 2/1 ve 1/2 dönüş
    rev_21 = round(sum(v for (h_g,a_g),v in ms_probs.items() if h_g > a_g)
                   * sum(v for (h_g,a_g),v in ht_probs.items() if h_g < a_g) / 100, 1)
    rev_12 = round(sum(v for (h_g,a_g),v in ms_probs.items() if h_g < a_g)
                   * sum(v for (h_g,a_g),v in ht_probs.items() if h_g > a_g) / 100, 1)
    # H2H dönüş geçmişi
    h2h_21 = h2h_data.get("reversal_21", 0)
    h2h_12 = h2h_data.get("reversal_12", 0)
    h2h_n  = h2h_data.get("total", 1) or 1
    h2h_rev_21_pct = round(h2h_21 / h2h_n * 100, 1)
    h2h_rev_12_pct = round(h2h_12 / h2h_n * 100, 1)

    # Oranlardan zımni olasılık
    ms_odds = odds.get("ms", {})
    iy_odds = odds.get("iy", {})
    btts_odds = odds.get("btts", {})
    goals_odds = odds.get("goals", {})

    imp1 = odds_to_prob(ms_odds.get("Home"))
    impx = odds_to_prob(ms_odds.get("Draw"))
    imp2 = odds_to_prob(ms_odds.get("Away"))
    imp_iy1 = odds_to_prob(iy_odds.get("Home"))
    imp_iyx = odds_to_prob(iy_odds.get("Draw"))
    imp_iy2 = odds_to_prob(iy_odds.get("Away"))
    imp_btts_yes = odds_to_prob(btts_odds.get("Yes"))
    imp_ust25 = odds_to_prob(goals_odds.get("Over 2.5"))
    imp_alt25 = odds_to_prob(goals_odds.get("Under 2.5"))

    # Kadro bilgileri
    def format_lineup(starters, formation):
        if not starters:
            return "Kadro verisi yok"
        pos_map = {"G": [], "D": [], "M": [], "F": []}
        for p in starters:
            pos_map.get(p.get("pos","M"), pos_map["M"]).append(p["name"])
        lines = [f"Dizilim: {formation}"]
        for pos, names in pos_map.items():
            if names:
                label = {"G":"KALECİ","D":"DEFANS","M":"ORTA SAHA","F":"FORVET"}.get(pos, pos)
                lines.append(f"  {label}: {', '.join(names)}")
        return "\n".join(lines)

    h_formation = home_lineup.get("formation","?") if home_lineup else "?"
    a_formation = away_lineup.get("formation","?") if away_lineup else "?"

    # Oyuncu xG tahmini (sezon istatistiklerine göre)
    home_player_stats = parse_player_stats(player_stats, h["id"])
    away_player_stats = parse_player_stats(player_stats, a["id"])

    def top_players_str(players, n=5):
        if not players:
            return "Veri yok"
        rated = [p for p in players if p.get("rating")]
        top = sorted(rated, key=lambda x: float(x["rating"] or 0), reverse=True)[:n]
        lines = []
        for p in top:
            g = p.get("goals", 0) or 0
            a_v = p.get("assists", 0) or 0
            sh = p.get("shots_on", 0) or 0
            kp = p.get("key_passes", 0) or 0
            r = p.get("rating", "?")
            lines.append(
                f"    {p['name']} ({p['pos']}) | Rating:{r} | Gol:{g} Asist:{a_v} "
                f"İsabetli Şut:{sh} Kilit Pas:{kp}"
            )
        return "\n".join(lines) if lines else "Veri yok"

    # Sakatlar
    def injuries_str(injuries):
        if not injuries:
            return "Bilgi yok"
        lines = []
        for inj in injuries[:6]:
            p = inj.get("player", {})
            reason = inj.get("injury", {}).get("reason", "?") or "?"
            lines.append(f"    {p.get('name','?')} — {reason}")
        return "\n".join(lines) if lines else "Yok"

    # Puan durumu
    def standing_str(s):
        if not s:
            return "Veri yok"
        return (f"Sıra: {s.get('rank','?')} | "
                f"O:{s.get('playedGames','?')} "
                f"G:{s.get('won','?')} B:{s.get('draw','?')} M:{s.get('lost','?')} | "
                f"AG:{s.get('goalsFor','?')}-{s.get('goalsAgainst','?')} | "
                f"Puan:{s.get('points','?')}")

    # ──────────────────────────────────────────
    # BÜYÜK PROMPT
    # ──────────────────────────────────────────
    prompt = f"""
==========================================================
MAÇ: {h['name']} vs {a['name']}
LİG: {comp} | TARİH: {dt} {utc} UTC
==========================================================

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
A) PUAN DURUMU
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{h['name']}: {standing_str(home_standing)}
{a['name']}: {standing_str(away_standing)}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
B) SEZON İSTATİSTİKLERİ
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{h['name']}:
  Oynadığı: {hs.get('played','?')} | G:{hs.get('wins','?')} B:{hs.get('draws','?')} M:{hs.get('losses','?')}
  Gol Ort: {hs.get('goals_for_avg','?')} attı / {hs.get('goals_ag_avg','?')} yedi (maç başı)
  İY Gol Ort: {hs.get('goals_for_ht_avg','?')} attı / {hs.get('goals_ag_ht_avg','?')} yedi
  En Çok Kullanılan Dizilim: {hs.get('formation','?')}
  Kuru Kalan: {hs.get('clean_sheets','?')} | Gol Atamayan: {hs.get('failed_to_score','?')}

{a['name']}:
  Oynadığı: {as_.get('played','?')} | G:{as_.get('wins','?')} B:{as_.get('draws','?')} M:{as_.get('losses','?')}
  Gol Ort: {as_.get('goals_for_avg','?')} attı / {as_.get('goals_ag_avg','?')} yedi (maç başı)
  İY Gol Ort: {as_.get('goals_for_ht_avg','?')} attı / {as_.get('goals_ag_ht_avg','?')} yedi
  En Çok Kullanılan Dizilim: {as_.get('formation','?')}
  Kuru Kalan: {as_.get('clean_sheets','?')} | Gol Atamayan: {as_.get('failed_to_score','?')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
C) SON 8 MAÇ FORMU
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{h['name']}:
  MS Form: {hf.get('form_str','?')} | Puan(son5): {hf.get('pts5','?')}/15
  İY Form: {hf.get('ht_form','?')}
  Gol Ort(son maçlar): {hf.get('avg_gf','?')} attı / {hf.get('avg_gc','?')} yedi
  İY Gol Ort: {hf.get('ht_avg_gf','?')} attı / {hf.get('ht_avg_gc','?')} yedi
  KG VAR: {hf.get('btts_count','?')}/{hf.get('total_matches','?')} maç
  2.5 ÜST: {hf.get('over25_count','?')}/{hf.get('total_matches','?')} maç
  Kuru kalan: {hf.get('clean_sheets','?')} | Gol atamayan: {hf.get('failed_to_score','?')}

{a['name']}:
  MS Form: {af.get('form_str','?')} | Puan(son5): {af.get('pts5','?')}/15
  İY Form: {af.get('ht_form','?')}
  Gol Ort(son maçlar): {af.get('avg_gf','?')} attı / {af.get('avg_gc','?')} yedi
  İY Gol Ort: {af.get('ht_avg_gf','?')} attı / {af.get('ht_avg_gc','?')} yedi
  KG VAR: {af.get('btts_count','?')}/{af.get('total_matches','?')} maç
  2.5 ÜST: {af.get('over25_count','?')}/{af.get('total_matches','?')} maç
  Kuru kalan: {af.get('clean_sheets','?')} | Gol atamayan: {af.get('failed_to_score','?')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
D) KADRO & DİZİLİM
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{h['name']} ({h_formation}):
{format_lineup(home_starters, h_formation)}
  Yedekler: {', '.join(home_subs[:5]) if home_subs else 'Veri yok'}
  Antrenör: {home_lineup.get('coach','?') if home_lineup else '?'}

{a['name']} ({a_formation}):
{format_lineup(away_starters, a_formation)}
  Yedekler: {', '.join(away_subs[:5]) if away_subs else 'Veri yok'}
  Antrenör: {away_lineup.get('coach','?') if away_lineup else '?'}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
E) OYUNCU İSTATİSTİKLERİ (son maç bazlı)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{h['name']} En İyi Oyuncular:
{top_players_str(home_player_stats)}

{a['name']} En İyi Oyuncular:
{top_players_str(away_player_stats)}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
F) SAKAT / CEZALI OYUNCULAR
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{h['name']}: {injuries_str(home_injuries)}
{a['name']}: {injuries_str(away_injuries)}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
G) H2H GEÇMİŞİ ({h2h_data.get('total',0)} MAÇLIK)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{h['name']} {h2h_data.get('hw',0)}G – {h2h_data.get('dr',0)}B – {h2h_data.get('aw',0)}M
Son Skorlar: {' | '.join(h2h_data.get('scores', [])[:6])}
Ortalama Gol: {h2h_data.get('avg_goals','?')} | 2.5 ÜST: {h2h_data.get('over25',0)}/{h2h_data.get('total',0)}
KG VAR: {h2h_data.get('btts',0)}/{h2h_data.get('total',0)}
İY Kazanan → {h['name']}: {h2h_data.get('ht_winner',{}).get('home',0)} | B: {h2h_data.get('ht_winner',{}).get('draw',0)} | {a['name']}: {h2h_data.get('ht_winner',{}).get('away',0)}
2/1 Dönüş H2H: {h2h_21}/{h2h_n} maç (%{h2h_rev_21_pct})
1/2 Dönüş H2H: {h2h_12}/{h2h_n} maç (%{h2h_rev_12_pct})

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
H) İDDAA ORANLARI
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MS  : 1={ms_odds.get('Home','?')} (Zımni %{imp1}) | X={ms_odds.get('Draw','?')} (Zımni %{impx}) | 2={ms_odds.get('Away','?')} (Zımni %{imp2})
İY  : 1={iy_odds.get('Home','?')} (Zımni %{imp_iy1}) | X={iy_odds.get('Draw','?')} (Zımni %{imp_iyx}) | 2={iy_odds.get('Away','?')} (Zımni %{imp_iy2})
KG  : VAR={btts_odds.get('Yes','?')} (Zımni %{imp_btts_yes}) | YOK={btts_odds.get('No','?')}
GOL : 2.5 ÜST={goals_odds.get('Over 2.5','?')} (Zımni %{imp_ust25}) | 2.5 ALT={goals_odds.get('Under 2.5','?')} (Zımni %{imp_alt25})

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
I) MODEL HESAPLAMALARI (Poisson xG)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Beklenen Gol (xG proxy):
  {h['name']} xG: {home_xg}  |  {a['name']} xG: {away_xg}
  {h['name']} İY xG: {home_ht_xg}  |  {a['name']} İY xG: {away_ht_xg}

MS Olasılıkları (Poisson):  1=%{p1} | X=%{px} | 2=%{p2}
İY Olasılıkları (Poisson):  1=%{iy1} | X=%{iyx} | 2=%{iy2}

En Olası MS Skorları:
{chr(10).join(f"  {hg}-{ag}: %{prob}" for (hg,ag),prob in sorted_ms[:8])}

En Olası İY Skorları:
{chr(10).join(f"  {hg}-{ag}: %{prob}" for (hg,ag),prob in sorted_ht[:5])}

KG VAR: %{kg_var} | KG YOK: %{kg_yok}
1.5 ÜST: %{ust15} | 2.5 ÜST: %{ust25} | 2.5 ALT: %{alt25} | 3.5 ÜST: %{ust35} | 3.5 ALT: %{alt35}

İY/MS Kombinasyonları (model):
{chr(10).join(f"  {k}: %{round(v,1)}" for k,v in iy_ms_sorted[:9])}

Poisson 2/1 Dönüş: %{rev_21}  |  1/2 Dönüş: %{rev_12}
H2H Tarihsel 2/1: %{h2h_rev_21_pct}  |  1/2: %{h2h_rev_12_pct}
==========================================================
""".strip()
    return prompt

# ─────────────────────────────────────────────
# CLAUDE ANALIZ
# ─────────────────────────────────────────────
SYSTEM_PROMPT = """Sen dünyanın en iyi futbol bahis veri analistlerinden birisin. Sana verilen kapsamlı maç verisini (kadro, dizilim, oyuncu istatistikleri, xG modeli, H2H, oranlar, sezon istatistikleri) kullanarak aşağıdaki 8 maddelik DEDERİNLİKLİ profesyonel analiz üret.

HER MADDE için detaylı gerekçe yaz. "Neden bu skor?", "Hangi oyuncu neden belirleyici?", "Dizilim nasıl etkiliyor?", "H2H pattern'i ne söylüyor?", "Oranla model farkı ne anlama geliyor?" sorularını cevapla.

## 1) EN OLASI SKOR TAHMİNİ
- Tek skor, yüzdesi, ve NEDEN bu skor (xG, dizilim, H2H, form gerekçeli)
- İY skoru tahmini de ver ve gerekçele

## 2) ALTERNATİF SKOR DAĞILIMI (en az 8 skor)
- Her skor için yüzde ve kısa gerekçe (neden o skor mümkün?)
- Özellikle yüksek skorlu alternatifleri açıkla

## 3) İY / MS TAHMİNİ (DETAYLI)
- İY 1/X/2 yüzdeleri + gerekçe (hangi takım ilk yarıda üstün, neden?)
- MS 1/X/2 yüzdeleri + gerekçe
- Tüm İY/MS kombinasyonları yüzde ile (9 kombinasyon)
- Model vs oran farkı varsa yorumla

## 4) KG VAR–YOK & ÜST/ALT (DETAYLI)
- KG VAR/YOK yüzde + gerekçe (her iki takımın savunma/hücum verisine dayalı)
- 1.5 Üst/Alt, 2.5 Üst/Alt, 3.5 Üst/Alt yüzdeleri
- Form bazlı KG ve Üst-Alt trendi açıkla

## 5) 2/1 – 1/2 DÖNÜŞ TESPİTİ (KRİTİK BÖLÜM)
- Poisson modeli 2/1 ihtimali: %... | 1/2 ihtimali: %...
- H2H tarihsel dönüş pattern'i
- İlk yarı düşük tempo / ikinci yarı yüksek tempo analizi (xG ve gol dağılımı)
- Sakat/eksik oyuncu etkisi dönüşü etkiler mi?
- Dizilim ve taktik açıdan dönüş senaryosu mümkün mü?
- Oran anomalisi var mı? (Zımni olasılık ile model arasındaki fark)

## 6) KADRO – DİZİLİM – OYUNCU ANALİZİ
- Her iki takımın dizilim avantajı/dezavantajı
- Kilit oyuncular: Bu maçta fark yaratabilecek isimler (rating, şut, kilit pas verisiyle)
- Sakat/cezalı oyuncuların taktiksel etkisi
- Hücum–savunma dengesi (xG oranı üzerinden)

## 7) ORAN–SKOR PATTERN ANALİZİ
- Mevcut oranlar hangi sonucu fiyatlıyor?
- Model ile oran arasında VALUE fırsatı var mı?
- Bu oran aralığında tarihsel pattern ne söylüyor?
- En baskın skor tipi ve KG/Üst eğilimi

## 8) MAÇ RİSK SEVİYESİ
- Düşük / Orta / Yüksek + detaylı gerekçe

## 9) BANKO – ORTA RİSK – SÜRPRİZ ÖNERİLERİ
- 🔒 BANKO: En güvenli, gerekçeli
- ⚡ ORTA RİSK: Değerli oran-veri uyumu
- 💎 SÜRPRİZ: Yüksek oranlı, pattern destekli
- 🎯 SKOR SÜRPRİZİ: Kesin skor için en yüksek value kombinasyonu

UYARI: Kişisel yorum yok. Tüm değerlendirmeler verilen data'ya dayalı olacak. Profesyonel bahis analiz dili kullan. Her tahmin için olasılık yüzdesi ver."""

def claude_analyze(prompt_text, key):
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
                "system": SYSTEM_PROMPT,
                "messages": [{"role": "user", "content": prompt_text}],
            },
            timeout=120,
        )
        r.raise_for_status()
        return r.json()["content"][0]["text"]
    except Exception as e:
        return f"❌ Claude Hatası: {e}"

# ─────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────
for k in ["fixtures", "match_data", "analyses", "remaining"]:
    if k not in st.session_state:
        default = [] if k == "fixtures" else ({} if k != "remaining" else "?")
        st.session_state[k] = default

# ─────────────────────────────────────────────
# BUTONLAR
# ─────────────────────────────────────────────
c1, c2, c3 = st.columns([3, 2, 2])
with c1:
    st.markdown(f"**{sel_label}** · {sel_date.strftime('%d.%m.%Y')} · Sezon {sel_season} · Maks {max_match} maç")
    if st.session_state.remaining != "?":
        st.caption(f"API kalan istek: {st.session_state.remaining}/100")
with c2:
    fetch_btn = st.button("🔍 Maçları Çek", type="primary", use_container_width=True)
with c3:
    all_btn = st.button("🤖 Tümünü Analiz Et", use_container_width=True)

st.divider()

# ─────────────────────────────────────────────
# MAÇLARI ÇEK
# ─────────────────────────────────────────────
if fetch_btn:
    if not api_football_key:
        st.error("⛔ API-Football key giriniz (sol sidebar).")
        st.stop()

    with st.spinner("📡 Maçlar çekiliyor..."):
        fixtures, rem = get_fixtures_today(
            api_football_key, sel_league, sel_season,
            sel_date.strftime("%Y-%m-%d"), max_match,
            debug=debug_mode
        )
        st.session_state.remaining = rem

    if not fixtures:
        st.error(f"""
⚠️ **Maç bulunamadı.** Olası nedenler:
- Seçilen tarihte bu ligde maç yok (sezon dışı veya boş hafta olabilir)
- Sezon yanlış: Denenen sezon **{sel_season}** (ve {sel_season-1})
- Lig ID: **{sel_league}** — doğru mu?
- API key geçerli mi? → Debug Modu aç ve API yanıtını kontrol et

**Çözüm dene:** Farklı bir tarih veya lig seç. Debug modunu aç.
        """)
    else:
        st.session_state.fixtures = fixtures
        st.session_state.match_data = {}
        st.session_state.analyses = {}
        st.success(f"✅ {len(fixtures)} maç bulundu! Detaylı veriler çekiliyor...")

        standings = get_standings(api_football_key, sel_league, sel_season)

        bar = st.progress(0)
        for i, fix in enumerate(fixtures):
            fid  = fix["fixture"]["id"]
            hid  = fix["teams"]["home"]["id"]
            aid  = fix["teams"]["away"]["id"]
            bar.progress(i / len(fixtures),
                         text=f"({i+1}/{len(fixtures)}) {fix['teams']['home']['name']} – {fix['teams']['away']['name']}")

            # Sezon istatistikleri
            hs_raw = get_team_season_stats(api_football_key, hid, sel_league, sel_season) if use_players else {}
            as_raw = get_team_season_stats(api_football_key, aid, sel_league, sel_season) if use_players else {}
            hs = parse_team_stats(hs_raw)
            as_ = parse_team_stats(as_raw)
            time.sleep(0.3)

            # Son maçlar
            hf_raw = get_team_last_matches(api_football_key, hid, sel_league, sel_season)
            af_raw = get_team_last_matches(api_football_key, aid, sel_league, sel_season)
            hf = parse_form(hf_raw, hid)
            af = parse_form(af_raw, aid)
            time.sleep(0.3)

            # Kadro
            lineups = get_lineups(api_football_key, fid) if use_lineups else []
            hl_raw = next((l for l in lineups if l.get("team", {}).get("id") == hid), {})
            al_raw = next((l for l in lineups if l.get("team", {}).get("id") == aid), {})
            hl, hst, hsb = parse_lineup(hl_raw)
            al, ast_, asb = parse_lineup(al_raw)
            time.sleep(0.3)

            # Oyuncu istatistikleri
            pstats = get_player_stats_fixture(api_football_key, fid) if use_players else []
            time.sleep(0.2)

            # H2H
            h2h_raw = get_h2h(api_football_key, hid, aid, n_h2h) if use_h2h else []
            h2h = h2h_deep(h2h_raw, hid)
            time.sleep(0.3)

            # Sakatlar
            h_inj = get_injuries(api_football_key, hid, fid) if use_injuries else []
            a_inj = get_injuries(api_football_key, aid, fid) if use_injuries else []
            time.sleep(0.2)

            # Oranlar
            odds = get_odds(api_football_key, fid)
            time.sleep(0.2)

            # Puan durumu
            h_standing = find_standing(standings, hid)
            a_standing = find_standing(standings, aid)

            # Prompt oluştur
            prompt = build_deep_prompt(
                fix, hf, af, hs, as_,
                hl, hst, hsb, al, ast_, asb,
                pstats, h2h, h_inj, a_inj,
                odds, standings, h_standing, a_standing
            )

            st.session_state.match_data[fid] = {
                "fixture": fix, "prompt": prompt,
                "home_xg": round(
                    (float(hs.get("goals_for_avg", 1.3) or 1.3) * 0.4 +
                     hf.get("avg_gf", 1.3) * 0.35 +
                     float(as_.get("goals_ag_avg", 1.1) or 1.1) * 0.25), 2),
                "away_xg": round(
                    (float(as_.get("goals_for_avg", 1.2) or 1.2) * 0.4 +
                     af.get("avg_gf", 1.1) * 0.35 +
                     float(hs.get("goals_ag_avg", 1.2) or 1.2) * 0.25), 2),
            }

        bar.progress(1.0, text="Tüm veriler hazır!")
        time.sleep(0.5)
        bar.empty()
        st.success("✅ Veriler hazır! Analiz için maçı aç veya Tümünü Analiz Et'e bas.")

# ─────────────────────────────────────────────
# TOPLU ANALİZ
# ─────────────────────────────────────────────
if all_btn:
    if not st.session_state.match_data:
        st.warning("Önce Maçları Çek!")
    elif not claude_key:
        st.error("⛔ Derin analiz için Claude API Key gerekli.")
    else:
        bar2 = st.progress(0)
        items = list(st.session_state.match_data.items())
        for i, (fid, md) in enumerate(items):
            h = md["fixture"]["teams"]["home"]["name"]
            a = md["fixture"]["teams"]["away"]["name"]
            bar2.progress(i / len(items), text=f"({i+1}/{len(items)}) {h} – {a}")
            result = claude_analyze(md["prompt"], claude_key)
            st.session_state.analyses[fid] = result
            time.sleep(1)
        bar2.progress(1.0)
        time.sleep(0.3)
        bar2.empty()
        st.success("✅ Tüm analizler tamamlandı!")

# ─────────────────────────────────────────────
# MAÇ LİSTESİ
# ─────────────────────────────────────────────
if st.session_state.fixtures:
    st.markdown(f"## 📋 Maçlar ({len(st.session_state.fixtures)})")

    for fix in st.session_state.fixtures:
        fid   = fix["fixture"]["id"]
        hname = fix["teams"]["home"]["name"]
        aname = fix["teams"]["away"]["name"]
        comp  = fix["league"]["name"]
        utc   = fix["fixture"]["date"][11:16]
        done  = fid in st.session_state.analyses
        md    = st.session_state.match_data.get(fid, {})

        label = f"{'✅' if done else '⚽'}  {hname}  –  {aname}  |  {comp}  |  {utc} UTC"

        with st.expander(label):
            # xG göster
            if md:
                hxg = md.get("home_xg", "?")
                axg = md.get("away_xg", "?")
                st.markdown(
                    f"<span class='odd-pill'>xG: {hname} {hxg} – {aname} {axg}</span>",
                    unsafe_allow_html=True
                )

            # Ham veri
            if md.get("prompt"):
                with st.expander("📊 Ham Veri & Model Çıktısı", expanded=False):
                    st.code(md["prompt"], language="markdown")

            # Analiz et butonu
            col_a, col_b = st.columns([3, 1])
            with col_b:
                if st.button("🤖 Analiz Et", key=f"btn_{fid}"):
                    if not claude_key:
                        st.error("Claude API Key gerekli!")
                    elif not md.get("prompt"):
                        st.warning("Önce Maçları Çek!")
                    else:
                        with st.spinner(f"{hname} – {aname} derin analiz yapılıyor..."):
                            result = claude_analyze(md["prompt"], claude_key)
                            st.session_state.analyses[fid] = result

            # Analiz sonucu
            if fid in st.session_state.analyses:
                st.markdown("---")
                st.markdown(
                    f"<div class='analysis-box'>{st.session_state.analyses[fid]}</div>",
                    unsafe_allow_html=True
                )
                st.download_button(
                    "⬇️ Analizi İndir",
                    data=st.session_state.analyses[fid],
                    file_name=f"{hname}_vs_{aname}_{sel_date}.txt",
                    mime="text/plain",
                    key=f"dl_{fid}",
                )

# ─────────────────────────────────────────────
# BAŞLANGIÇ
# ─────────────────────────────────────────────
else:
    st.markdown("""
    <div class="key-guide" style="font-size:0.88rem; line-height:2">
    <b style="color:#60a5fa; font-size:1rem">⚽ Pro Betting Analyst Engine — Veri Kapsamı</b><br><br>
    Bu sistem her maç için şunları çeker ve analiz eder:<br>
    <b>Kadro & Dizilim</b> — 11'ler, formasyon, antrenör<br>
    <b>Oyuncu İstatistikleri</b> — Rating, şut, kilit pas, dribbling<br>
    <b>Sezon İstatistikleri</b> — Gol ort, kuru kalma, gol atamama<br>
    <b>Son 8 Maç Formu</b> — İY + MS ayrı ayrı, gol trendi<br>
    <b>H2H Geçmişi</b> — Skorlar, İY kazananı, 2/1–1/2 dönüş geçmişi<br>
    <b>Sakatlar / Cezalılar</b> — Kadro eksikleri<br>
    <b>İddaa Oranları</b> — MS, İY, KG, 2.5 Üst/Alt<br>
    <b>Poisson xG Modeli</b> — 8'den fazla senaryo skor olasılığı<br>
    <b>İY/MS Kombinasyonları</b> — 9 kombinasyon, yüzdeli<br>
    <b>2/1–1/2 Dönüş Analizi</b> — Model + H2H tarihi + tempo analizi<br><br>
    <b>Adımlar:</b><br>
    1. <a href="https://dashboard.api-football.com/register" target="_blank">dashboard.api-football.com/register</a> → ücretsiz kayıt → key al<br>
    2. <a href="https://console.anthropic.com" target="_blank">console.anthropic.com</a> → Claude key al<br>
    3. Sidebar'a gir → Lig + tarih seç → Maçları Çek → Analiz Et
    </div>
    """, unsafe_allow_html=True)
