import streamlit as st
import requests
import math
import time
def _safe_minute(val, default=45):
    \"\"\"Parse a match minute safely — handles ?, empty, None, 45+2, etc.\"\"\"
    try:
        s = str(val).replace(\"'\",\"\").strip()
        # \"45+2\" → 47, \"90+4\" → 94
        if \"+\" in s:
            parts = s.split(\"+\")
            return int(parts[0]) + int(parts[1])
        s = s.split()[0]
        return int(s) if s and s[0].isdigit() else default
    except:
        return default

def calc_live_minute(m):
    \"\"\"
    football-data.org maç nesnesinden gerçek oyun dakikasını hesapla.
    utcDate UTC'dir. Devre arası ~15dk. Stopaj hesaba katılmaz.
    \"\"\"
    import datetime as _dt

    status = m.get(\"status\", \"\")
    if status == \"PAUSED\":
        return 45

    utc_str = m.get(\"utcDate\", \"\")
    if not utc_str:
        return 45

    try:
        clean = utc_str.rstrip(\"Z\").replace(\"T\", \" \")[:19]
        start = _dt.datetime.strptime(clean, \"%Y-%m-%d %H:%M:%S\")
    except Exception:
        return 45

    now     = _dt.datetime.utcnow()
    elapsed = max(0, int((now - start).total_seconds() / 60))

    if elapsed <= 45:
        return max(1, elapsed)          # 1Y: 1–45
    elif elapsed <= 60:
        return 45                       # Devre arası (45+15dk)
    else:
        minute = elapsed - 15           # 2Y: devre arası 15dk
        return max(46, min(90, minute))


from datetime import date

st.set_page_config(page_title=\"⚽ BetAnalyst Pro\", page_icon=\"⚽\",
                   layout=\"wide\", initial_sidebar_state=\"expanded\")

FD_KEY          = \"5cc88bf0dbac4fb699482886eb4c2270\"
AF_KEY_DEFAULT  = \"b30caea6f2a4c305ff317308de0b917d\"
GROQ_KEY = \"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\"
ODDS_API_KEY_DEFAULT = \"4d4d08c88873623761e05df66d0aeb07\"

# ══════════════════════════════════════════════════════════════════
# CSS
# ══════════════════════════════════════════════════════════════════
st.markdown(\"\"\"
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Inter:wght@300;400;500;600;700;800&display=swap');
*{box-sizing:border-box}
html,body,[class*=\"css\"]{font-family:'Inter',sans-serif}

/* ── RENK SİSTEMİ ──────────────────────────────────────
  Arka plan L1:  #09101e   (en koyu — card içi)
  Arka plan L2:  #0d1829   (panel zemin)
  Arka plan L3:  #111f35   (hover, alt element)
  Bölücü:        #1c2e44
  Etiket soluk:  #2a3a4a → #4a6880
  Etiket orta:   #7a9ab8
  Ana metin:     #a8c4d8 → #d0dce8
  Ev (mavi):     #4c9eff
  Dep (kırmızı): #ff7070
  Beraberlik:    #f5a623
  İyi/Pozitif:   #3ecf7a
  Kötü/Negatif:  #f87171
  Vurgu:         #00e5a0
  Dönüş:         #fbbf24
──────────────────────────────────────────────────── */

/* ── HERO ── */
.hero{
  background:linear-gradient(160deg,#06090f 0%,#0d1829 100%);
  border:1px solid #1c2e44;border-radius:14px;padding:1.6rem 2rem;
  margin-bottom:1.2rem;text-align:center;position:relative;overflow:hidden
}
.hero h1{color:#d0dce8;margin:0;font-size:1.7rem;font-weight:800;letter-spacing:-.8px}
.hero h1 span{color:#00e5a0}
.hero p{color:#4a6880;margin:.4rem 0 0;font-size:.78rem}

/* ── VS WRAPPER ── */
.vs-wrapper{background:#0d1829;border:1px solid #1c2e44;border-radius:14px;overflow:hidden;margin-bottom:1rem}
.vs-header{
  display:grid;grid-template-columns:1fr auto 1fr;align-items:center;
  padding:1.1rem 1.5rem;background:#09101e;border-bottom:1px solid #1c2e44;gap:1rem
}
.vs-team{text-align:center}
.vs-team .t-name{font-size:1.05rem;font-weight:800;color:#d0dce8;letter-spacing:-.2px}
.vs-team .t-league{font-size:.62rem;color:#2a3a4a;margin-top:3px;text-transform:uppercase;letter-spacing:.08em}
.vs-team.home .t-name{color:#4c9eff}
.vs-team.away .t-name{color:#ff7070}
.vs-middle{text-align:center}
.vs-badge{background:#0d1829;border:1px solid #1c2e44;border-radius:9px;padding:7px 13px;display:inline-block}
.vs-badge .vb-vs{font-size:.62rem;color:#2a3a4a;font-weight:700;letter-spacing:.15em}
.vs-badge .vb-time{font-size:.9rem;font-weight:700;color:#00e5a0;font-family:'JetBrains Mono',monospace;display:block;margin-top:2px}
.vs-badge .vb-date{font-size:.6rem;color:#2a3a4a;margin-top:1px}

/* ── XG BAR ── */
.xg-bar-section{padding:.9rem 1.5rem;border-bottom:1px solid #1c2e44}
.xg-bar-wrap{display:flex;align-items:center;height:26px;border-radius:5px;overflow:hidden;margin:5px 0}
.xg-bar-home{height:100%;display:flex;align-items:center;justify-content:flex-end;
  padding-right:9px;background:linear-gradient(90deg,#1a4ed8,#3b7afc);
  font-size:.75rem;font-weight:700;color:#c8dbff;font-family:'JetBrains Mono',monospace;transition:width .5s}
.xg-bar-mid{background:#060c17;padding:0 5px;display:flex;align-items:center;
  font-size:.52rem;color:#1c2e44;font-weight:700;white-space:nowrap;height:100%}
.xg-bar-away{height:100%;display:flex;align-items:center;
  padding-left:9px;background:linear-gradient(90deg,#c92b2b,#f05050);
  font-size:.75rem;font-weight:700;color:#ffd0d0;font-family:'JetBrains Mono',monospace;transition:width .5s}
.xg-label{display:flex;justify-content:space-between;font-size:.63rem;color:#4a6880;margin-top:3px}

/* ── VERİ PANELİ (2 sütun) ── */
.data-panel{display:grid;grid-template-columns:1fr 1fr;border-bottom:1px solid #1c2e44}
.dp-col{padding:.9rem 1.5rem}
.dp-col.home-col{border-right:1px solid #1c2e44}
.dp-section-title{font-size:.56rem;font-weight:700;letter-spacing:.13em;text-transform:uppercase;
  color:#4a6880;margin-bottom:6px;padding-bottom:3px;border-bottom:1px solid #1c2e44}
.dp-row{display:flex;justify-content:space-between;align-items:center;padding:3px 0;border-bottom:1px solid #0d1423}
.dp-row:last-child{border-bottom:none}
.dp-row .dr-label{font-size:.68rem;color:#4a6880}
.dp-row .dr-val{font-size:.74rem;font-weight:600;color:#a8c4d8;font-family:'JetBrains Mono',monospace}
.dp-row .dr-val.good{color:#3ecf7a}
.dp-row .dr-val.bad{color:#f87171}
.dp-row .dr-val.warn{color:#f5a623}

/* Form rozetleri */
.form-badges{display:flex;gap:4px;flex-wrap:wrap;margin:3px 0}
.fb{width:23px;height:23px;border-radius:4px;display:flex;align-items:center;justify-content:center;font-size:.68rem;font-weight:700}
.fb.g{background:#04200e;color:#3ecf7a;border:1px solid #1a5c32}
.fb.b{background:#1a1600;color:#f5a623;border:1px solid #6b4400}
.fb.m{background:#200606;color:#f87171;border:1px solid #6b1c1c}

/* Skor rozetleri */
.score-list{display:flex;gap:4px;flex-wrap:wrap;margin:3px 0}
.sc-badge{background:#111f35;border:1px solid #1c2e44;border-radius:4px;
  padding:2px 6px;font-size:.68rem;font-weight:600;color:#a8c4d8;font-family:'JetBrains Mono',monospace}
.sc-badge.iy{border-color:#1c2e44;color:#4a6880}

/* ── KARŞILAŞTIRMA SATIRI ── */
.vs-compare{padding:.9rem 1.5rem;border-bottom:1px solid #1c2e44}
.vc-row{display:grid;grid-template-columns:1fr 90px 1fr;gap:6px;align-items:center;padding:4px 0;border-bottom:1px solid #0d1423}
.vc-row:last-child{border:none}
.vc-home{text-align:right}
.vc-away{text-align:left}
.vc-label{text-align:center;font-size:.6rem;color:#2a3a4a;font-weight:600;letter-spacing:.06em;text-transform:uppercase}
.vc-val{font-size:.8rem;font-weight:700;font-family:'JetBrains Mono',monospace}
.vc-val.better{color:#3ecf7a}
.vc-val.worse{color:#4a6880}
.vc-val.equal{color:#f5a623}

/* ── OLASILİK PANEL ── */
.prob-panel{padding:.9rem 1.5rem;border-bottom:1px solid #1c2e44}
.ms-trio{display:grid;grid-template-columns:1fr 1fr 1fr;gap:7px;margin:7px 0}
.ms-box{background:#111f35;border:1px solid #1c2e44;border-radius:8px;padding:9px 6px;text-align:center}
.ms-box.fav-home{border-color:#1e4ed8;background:#081530}
.ms-box.fav-away{border-color:#b91c1c;background:#160808}
.ms-box.fav-draw{border-color:#b45309;background:#120e00}
.ms-box .mb-label{font-size:.56rem;color:#4a6880;text-transform:uppercase;letter-spacing:.1em;margin-bottom:3px}
.ms-box .mb-name{font-size:.6rem;color:#2a3a4a;margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.ms-box .mb-pct{font-size:1.35rem;font-weight:800;font-family:'JetBrains Mono',monospace}
.fav-home .mb-pct{color:#4c9eff}
.fav-away .mb-pct{color:#ff7070}
.fav-draw .mb-pct{color:#f5a623}
.default .mb-pct{color:#4a6880}

/* ── SKOR DAĞILIMI ── */
.skor-panel{padding:.9rem 1.5rem;border-bottom:1px solid #1c2e44}
.skor-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:5px;margin:6px 0}
.skor-box{background:#111f35;border:1px solid #1c2e44;border-radius:6px;padding:7px 4px;text-align:center}
.skor-box .sb-score{font-size:.95rem;font-weight:700;color:#a8c4d8;font-family:'JetBrains Mono',monospace}
.skor-box .sb-pct{font-size:.58rem;color:#4a6880;margin-top:2px}
.skor-box.rank1{border-color:#b45309;background:#0e0a00}
.skor-box.rank1 .sb-score{color:#f5a623}
.skor-box.rank1 .sb-pct{color:#6b4400}
.skor-box.rank2{border-color:#1d4ed8;background:#06101e}
.skor-box.rank2 .sb-score{color:#4c9eff}
.skor-box.rank2 .sb-pct{color:#1e3a7a}
.skor-box.rank3{border-color:#166534;background:#041209}
.skor-box.rank3 .sb-score{color:#3ecf7a}

/* ── İY/MS KOMBOLAR ── */
.combo-panel{padding:.9rem 1.5rem;border-bottom:1px solid #1c2e44}
.combo-title{font-size:.56rem;color:#4a6880;font-weight:700;letter-spacing:.12em;text-transform:uppercase;margin-bottom:8px}
.combo-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:5px}
.combo-cell{background:#111f35;border:1px solid #1c2e44;border-radius:6px;padding:7px 5px;text-align:center}
.combo-cell .cc-key{font-size:.88rem;font-weight:800;font-family:'JetBrains Mono',monospace;color:#4a6880}
.combo-cell .cc-pct{font-size:.64rem;color:#4a6880;margin-top:2px}
.combo-cell .cc-desc{font-size:.53rem;color:#2a3a4a;margin-top:1px}
.combo-cell.top1{border-color:#b45309;background:#0e0a00}
.combo-cell.top1 .cc-key{color:#f5a623}
.combo-cell.top1 .cc-pct{color:#7a5010}
.combo-cell.top2{border-color:#1d4ed8;background:#06101e}
.combo-cell.top2 .cc-key{color:#4c9eff}
.combo-cell.top2 .cc-pct{color:#1e3a7a}
.combo-cell.top3{border-color:#166534;background:#041209}
.combo-cell.top3 .cc-key{color:#3ecf7a}

/* ── DÖNÜŞ PANEL ── */
.donus-panel{padding:.9rem 1.5rem;border-bottom:1px solid #1c2e44}
.donus-grid{display:grid;grid-template-columns:1fr 1fr;gap:9px}
.donus-card{background:#111f35;border:1px solid #1c2e44;border-radius:9px;padding:10px 12px}
.donus-card.hot21{border-color:#b45309;background:#0c0800}
.donus-card.hot12{border-color:#6d28d9;background:#070410}
.donus-card .dc-title{font-size:.6rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase;margin-bottom:5px;color:#4a6880}
.donus-card.hot21 .dc-title{color:#f5a623}
.donus-card.hot12 .dc-title{color:#a78bfa}
.donus-card .dc-explain{font-size:.66rem;color:#4a6880;margin-bottom:6px;line-height:1.5}
.donus-row{display:flex;justify-content:space-between;align-items:center;padding:3px 0;border-bottom:1px solid #0d1423}
.donus-row:last-child{border:none}
.donus-row .dr-lbl{font-size:.62rem;color:#4a6880}
.donus-row .dr-v{font-size:.78rem;font-weight:700;font-family:'JetBrains Mono',monospace}

/* ── TAHMİN PANEL ── */
.tahmin-panel{padding:.9rem 1.5rem;border-bottom:1px solid #1c2e44}
.pred-card{border-radius:8px;padding:10px 12px;margin:5px 0;display:flex;align-items:flex-start;gap:9px}
.pred-card.banko{background:#04180a;border:1px solid #166534}
.pred-card.orta{background:#060f20;border:1px solid #1d4ed8}
.pred-card.risky{background:#0e0800;border:1px solid #92400e}
.pred-card.skor{background:#070410;border:1px solid #5b21b6}
.pred-icon{font-size:.95rem;margin-top:2px}
.pred-body .pt{font-size:.56rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase}
.pred-card.banko .pt{color:#3ecf7a}
.pred-card.orta  .pt{color:#4c9eff}
.pred-card.risky .pt{color:#f5a623}
.pred-card.skor  .pt{color:#a78bfa}
.pred-body .pp{font-size:.82rem;font-weight:700;color:#d0dce8;margin:3px 0;font-family:'JetBrains Mono',monospace}
.pred-body .pw{font-size:.66rem;color:#4a6880;line-height:1.5}

/* ── ANALİZ METNİ ── */
.analiz-panel{padding:.9rem 1.5rem}
.analiz-title{font-size:.56rem;color:#4a6880;font-weight:700;letter-spacing:.12em;text-transform:uppercase;margin-bottom:6px}
.analiz-text{font-size:.76rem;color:#7a9ab8;line-height:1.85;white-space:pre-wrap;max-height:200px;overflow-y:auto}

/* ── GOL METRİKLER ── */
.gol-panel{padding:.9rem 1.5rem;border-bottom:1px solid #1c2e44}
.gol-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:6px}
.gol-box{background:#111f35;border:1px solid #1c2e44;border-radius:7px;padding:8px 5px;text-align:center}
.gol-box .gb-label{font-size:.56rem;color:#4a6880;text-transform:uppercase;letter-spacing:.08em;margin-bottom:3px}
.gol-box .gb-val{font-size:1.1rem;font-weight:800;font-family:'JetBrains Mono',monospace}
.gol-box .gb-sub{font-size:.58rem;color:#4a6880;margin-top:2px}
.gol-box.high .gb-val{color:#3ecf7a}
.gol-box.mid  .gb-val{color:#f5a623}
.gol-box.low  .gb-val{color:#f87171}

/* ── H2H PANEL ── */
.h2h-panel{padding:.9rem 1.5rem;border-bottom:1px solid #1c2e44}
.h2h-score-list{display:flex;flex-wrap:wrap;gap:4px;margin:5px 0}
.h2h-sc{background:#111f35;border:1px solid #1c2e44;border-radius:4px;
  padding:2px 7px;font-size:.7rem;font-weight:600;color:#a8c4d8;font-family:'JetBrains Mono',monospace}
.h2h-sc.iy{border-color:#1c2e44;color:#4a6880}

/* ── DISCLAIMER ── */
.disclaimer{font-size:.6rem;color:#2a3a4a;text-align:center;padding:7px;border-top:1px solid #1c2e44}

/* ── PATTERN PANEL — YENİ TASARIM ── */
.pattern-wrap{background:#09101e;border:1px solid #1c2e44;border-radius:12px;margin:4px 0;overflow:hidden}
.pattern-header{background:#09101e;padding:.75rem 1.2rem;border-bottom:1px solid #1c2e44;
  display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.pattern-badge{background:#00e5a010;border:1px solid #00e5a028;
  color:#00e5a0;font-size:.56rem;font-weight:700;letter-spacing:.1em;
  text-transform:uppercase;padding:2px 8px;border-radius:20px}
.pattern-badge.b365{background:#0a1e4010;border-color:#1e4ed828;color:#4c9eff}
.pattern-title{font-size:.76rem;font-weight:700;color:#a8c4d8}
.pattern-n{font-size:.64rem;color:#4a6880;margin-left:auto;font-family:'JetBrains Mono',monospace}
.pattern-odds-row{background:#0d1829;padding:.5rem 1.2rem;border-bottom:1px solid #1c2e44;
  display:flex;align-items:center;gap:16px;flex-wrap:wrap}
.pat-odd-box{text-align:center}
.pat-odd-lbl{font-size:.54rem;color:#4a6880;text-transform:uppercase;letter-spacing:.08em;display:block}
.pat-odd-val{font-size:.95rem;font-weight:700;font-family:'JetBrains Mono',monospace;display:block}
.pat-odd-box.home .pat-odd-val{color:#4c9eff}
.pat-odd-box.draw .pat-odd-val{color:#f5a623}
.pat-odd-box.away .pat-odd-val{color:#ff7070}
.pat-odd-sep{color:#1c2e44;font-size:1.2rem}
.pat-src{font-size:.58rem;color:#4a6880;margin-left:auto;
  background:#111f35;border:1px solid #1c2e44;border-radius:4px;padding:2px 8px}
.pat-src.bet365{color:#4c9eff;border-color:#1e4ed8;background:#06101e}
.pattern-body{padding:.9rem 1.2rem}
.pat-sec{margin-bottom:12px}
.pat-sec-lbl{font-size:.56rem;font-weight:700;letter-spacing:.13em;text-transform:uppercase;
  color:#4a6880;border-bottom:1px solid #1c2e44;padding-bottom:3px;margin-bottom:8px}
/* Sonuç üçlüsü */
.pat-res-trio{display:grid;grid-template-columns:1fr 1fr 1fr;gap:6px;margin-bottom:10px}
.pat-res-box{border-radius:6px;padding:7px 5px;text-align:center}
.pat-res-box .prb-lbl{font-size:.56rem;text-transform:uppercase;letter-spacing:.08em;margin-bottom:2px}
.pat-res-box .prb-big{font-size:1.25rem;font-weight:800;font-family:'JetBrains Mono',monospace}
.pat-res-box .prb-cnt{font-size:.58rem;margin-top:1px}
.pat-home{background:#081530;border:1px solid #1e4ed8}
.pat-home .prb-lbl,.pat-home .prb-cnt{color:#1e4ed8}
.pat-home .prb-big{color:#4c9eff}
.pat-draw{background:#120e00;border:1px solid #b45309}
.pat-draw .prb-lbl,.pat-draw .prb-cnt{color:#b45309}
.pat-draw .prb-big{color:#f5a623}
.pat-away{background:#160808;border:1px solid #b91c1c}
.pat-away .prb-lbl,.pat-away .prb-cnt{color:#b91c1c}
.pat-away .prb-big{color:#ff7070}
/* Skor listesi (bar formatı) */
.skor-bar-list{display:flex;flex-direction:column;gap:4px}
.skor-bar-row{display:flex;align-items:center;gap:7px}
.skor-bar-key{font-size:.8rem;font-weight:700;font-family:'JetBrains Mono',monospace;min-width:32px;color:#a8c4d8}
.skor-bar-track{flex:1;height:4px;background:#1c2e44;border-radius:3px;overflow:hidden}
.skor-bar-fill{height:100%;border-radius:3px}
.skor-bar-pct{font-size:.68rem;font-family:'JetBrains Mono',monospace;min-width:38px;text-align:right;color:#7a9ab8}
.skor-bar-cnt{font-size:.58rem;color:#4a6880;min-width:24px}
/* Dönüş kombolar */
.pat-combo-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:5px;margin-bottom:10px}
.pat-combo-cell{border-radius:6px;padding:6px 4px;text-align:center;background:#111f35;border:1px solid #1c2e44}
.pat-combo-cell.donus{background:#0e0900;border-color:#b45309}
.pat-combo-cell .pcc-key{font-size:.85rem;font-weight:800;font-family:'JetBrains Mono',monospace;color:#4a6880}
.pat-combo-cell.donus .pcc-key{color:#f5a623}
.pat-combo-cell .pcc-pct{font-size:.68rem;font-family:'JetBrains Mono',monospace;margin-top:2px;color:#4a6880}
.pat-combo-cell.donus .pcc-pct{color:#f5a623}
.pat-combo-cell .pcc-cnt{font-size:.54rem;color:#2a3a4a;margin-top:1px}
/* Notable dönüş satırları */
.notable-row{display:flex;align-items:center;gap:8px;padding:5px 8px;margin:3px 0;
  background:#0e0900;border-left:3px solid #b45309;border-radius:0 6px 6px 0}
.notable-combo{font-size:.82rem;font-weight:800;color:#f5a623;font-family:'JetBrains Mono',monospace;min-width:36px}
.notable-text{font-size:.68rem;color:#a8c4d8;flex:1}
.notable-pct{font-size:.8rem;font-weight:700;color:#f5a623;font-family:'JetBrains Mono',monospace}
.notable-cnt{font-size:.6rem;color:#4a6880;margin-left:4px}

/* ── CANLI MAÇ MODÜLÜ ───────────────────────────────── */
.live-header{
  background:linear-gradient(90deg,#0d1829,#120808);
  border:1px solid #b91c1c;border-radius:12px;
  padding:.9rem 1.4rem;margin-bottom:.8rem;
  display:flex;align-items:center;gap:12px
}
.live-dot{width:9px;height:9px;border-radius:50%;background:#f87171;
  box-shadow:0 0 8px #f87171;animation:pulse 1.2s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.3}}
.live-badge{font-size:.58rem;font-weight:800;letter-spacing:.12em;color:#f87171;
  text-transform:uppercase;background:#1a0808;border:1px solid #b91c1c;
  border-radius:4px;padding:2px 8px}
.live-title{font-size:.82rem;font-weight:700;color:#d0dce8;flex:1}
.live-minute{font-size:1.1rem;font-weight:800;color:#f5a623;
  font-family:'JetBrains Mono',monospace}

/* Canlı skor kutusu */
.live-score-wrap{
  background:#09101e;border:1px solid #1c2e44;border-radius:12px;
  overflow:hidden;margin-bottom:.7rem
}
.live-score-row{
  display:grid;grid-template-columns:1fr auto 1fr;
  align-items:center;padding:1rem 1.4rem;gap:8px
}
.ls-team{text-align:center}
.ls-team .lst-name{font-size:.9rem;font-weight:700}
.ls-team .lst-name.home{color:#4c9eff}
.ls-team .lst-name.away{color:#ff7070}
.ls-team .lst-events{font-size:.62rem;color:#4a6880;margin-top:3px;min-height:14px}
.ls-score{text-align:center;background:#111f35;border-radius:8px;padding:6px 16px}
.ls-score .lss-main{font-size:1.8rem;font-weight:800;color:#d0dce8;
  font-family:'JetBrains Mono',monospace;letter-spacing:4px}
.ls-score .lss-ht{font-size:.62rem;color:#4a6880;margin-top:2px}

/* İstatistik bar */
.stat-bar-row{display:grid;grid-template-columns:48px 1fr 1fr 1fr 48px;
  gap:4px;align-items:center;padding:3px 1.4rem;border-bottom:1px solid #0d1423}
.stat-bar-row:last-child{border:none}
.sbr-val{font-size:.72rem;font-weight:700;font-family:'JetBrains Mono',monospace}
.sbr-val.home{color:#4c9eff;text-align:right}
.sbr-val.away{color:#ff7070;text-align:left}
.sbr-label{font-size:.58rem;color:#4a6880;text-align:center;letter-spacing:.04em}
.sbr-bars{display:flex;gap:2px;align-items:center;height:6px}
.sbr-bar-h{height:100%;border-radius:2px 0 0 2px;background:#4c9eff;opacity:.7}
.sbr-bar-a{height:100%;border-radius:0 2px 2px 0;background:#ff7070;opacity:.7}

/* Gol tavsiye kutuları */
.goal-rec-grid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:7px;margin:.7rem 0}
.goal-rec-box{border-radius:8px;padding:10px 8px;text-align:center;cursor:default}
.grb-label{font-size:.56rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;margin-bottom:3px}
.grb-bet{font-size:.88rem;font-weight:800;font-family:'JetBrains Mono',monospace;margin:2px 0}
.grb-odd{font-size:.7rem;font-family:'JetBrains Mono',monospace;margin-bottom:2px}
.grb-why{font-size:.58rem;line-height:1.4}
.grb-conf{font-size:.58rem;font-weight:700;margin-top:4px;letter-spacing:.06em}
.goal-rec-box.strong{background:#04180a;border:1px solid #166534}
.goal-rec-box.strong .grb-label,.goal-rec-box.strong .grb-conf{color:#3ecf7a}
.goal-rec-box.strong .grb-bet{color:#d0dce8}
.goal-rec-box.strong .grb-why{color:#4a6880}
.goal-rec-box.medium{background:#0e0a00;border:1px solid #b45309}
.goal-rec-box.medium .grb-label,.goal-rec-box.medium .grb-conf{color:#f5a623}
.goal-rec-box.medium .grb-bet{color:#d0dce8}
.goal-rec-box.medium .grb-why{color:#4a6880}
.goal-rec-box.risky{background:#060f20;border:1px solid #1d4ed8}
.goal-rec-box.risky .grb-label,.goal-rec-box.risky .grb-conf{color:#4c9eff}
.goal-rec-box.risky .grb-bet{color:#d0dce8}
.goal-rec-box.risky .grb-why{color:#4a6880}
.goal-rec-box.wait{background:#111f35;border:1px solid #1c2e44}
.goal-rec-box.wait .grb-label{color:#4a6880}
.goal-rec-box.wait .grb-bet{color:#4a6880}
.goal-rec-box.wait .grb-why{color:#2a3a4a}

/* Momentum bar */
.momentum-wrap{padding:.7rem 1.4rem;border-top:1px solid #1c2e44}
.mom-bar-track{height:8px;border-radius:4px;background:#1c2e44;overflow:hidden;margin:4px 0;position:relative}
.mom-bar-fill{height:100%;border-radius:4px;transition:width .5s}
.mom-labels{display:flex;justify-content:space-between;font-size:.6rem;color:#4a6880;margin-top:2px}

/* Canlı maç refresh */
.live-refresh-row{display:flex;align-items:center;gap:8px;
  font-size:.62rem;color:#4a6880;padding:.5rem 1.4rem;
  border-top:1px solid #1c2e44}
.live-updated{color:#3ecf7a;font-weight:600}

/* Streamlit overrides */
div[data-testid=\"stExpander\"]{border:1px solid #1c2e44!important;border-radius:12px!important;background:#0d1829!important;overflow:hidden}
div[data-testid=\"stExpander\"] summary{background:#0d1829!important}
.stTabs [data-baseweb=\"tab-list\"]{background:#09101e;padding:3px;gap:3px;border-radius:7px}
.stTabs [data-baseweb=\"tab\"]{border-radius:5px;color:#4a6880;font-size:.74rem;padding:4px 11px}
.stTabs [aria-selected=\"true\"]{background:#111f35!important;color:#00e5a0!important}
button[kind=\"primary\"]{background:linear-gradient(90deg,#0ea5e9,#00e5a0)!important;
color:#06090f!important;font-weight:700!important;border:none!important;border-radius:7px!important}
</style>
\"\"\", unsafe_allow_html=True)

st.markdown(\"\"\"
<div class=\"hero\">
  <h1>⚽ Bet<span>Analyst</span> Pro</h1>
  <p>football-data.org · Groq Llama 3.3 70B · Profesyonel VS Analiz</p>
</div>
\"\"\", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown(\"## ⚙️ Filtreler\")
    st.success(\"✅ API key'ler hazır\")

    # ── MOD SEÇİMİ ──
    app_mode = st.radio(
        \"Mod\",
        [\"📅 Maç Analizi\", \"🔴 Canlı Maçlar\"],
        horizontal=True,
        help=\"Canlı modda oynanan maçları gerçek zamanlı analiz et\"
    )

    # ── Ücretsiz planda çalışan ligler (football-data.org) ──
    LEAGUE_GROUPS = {
        \"🌍 Avrupa Kulüp\": {
            \"UEFA Champions League ⭐\": \"CL\",
            \"UEFA Europa League\":       \"EL\",
            \"UEFA Conference League\":   \"ECL\",
        },
        \"🏴󠁧󠁢󠁥󠁮󠁧󠁿 İngiltere\": {
            \"Premier League\":           \"PL\",
            \"Championship (2. Lig) ✅\": \"ELC\",
            \"FA Cup\":                   \"FAC\",
        },
        \"🇪🇸 İspanya\": {
            \"La Liga\":                  \"PD\",
        },
        \"🇩🇪 Almanya\": {
            \"Bundesliga\":               \"BL1\",
        },
        \"🇮🇹 İtalya\": {
            \"Serie A\":                  \"SA\",
        },
        \"🇫🇷 Fransa\": {
            \"Ligue 1\":                  \"FL1\",
        },
        \"🇳🇱 Hollanda\": {
            \"Eredivisie\":               \"DED\",
        },
        \"🇵🇹 Portekiz\": {
            \"Primeira Liga\":            \"PPL\",
        },
        \"🇧🇷 Brezilya\": {
            \"Série A\":                  \"BSA\",
        },
        \"🌐 Milli Takım\": {
            \"FIFA World Cup\":           \"WC\",
            \"UEFA Avrupa Şampiyonası\":  \"EC\",
        },
    }

    sel_group = st.selectbox(\"Kategori\", list(LEAGUE_GROUPS.keys()))
    sel_label = st.selectbox(\"Lig\", list(LEAGUE_GROUPS[sel_group].keys()))
    sel_code  = LEAGUE_GROUPS[sel_group][sel_label].split(\"#\")[0].strip()

    st.info(
        \"ℹ️ **2. ligler neden yok?**\\n\\n\"
        \"football-data.org ücretsiz planda yalnızca belirli 1. ligler ve \"
        \"İngiltere Championship dahil. 2. Bundesliga, Serie B, Ligue 2, \"
        \"Segunda División vb. 49€/ay ücretli plan gerektiriyor. \"
        \"Ücretsiz planda mevcut olan ligler yukarıda listelenmiştir.\"
    )
    sel_date  = st.date_input(\"Tarih\", value=date.today())
    max_match = st.slider(\"Maks Maç\", 1, 15, 8)
    n_form    = st.slider(\"Form Maç Sayısı\", 5, 12, 8)
    n_h2h     = st.slider(\"H2H Maç Sayısı\", 4, 10, 6)
    groq_model = st.selectbox(
        \"Groq Modeli\",
        [
            \"llama-3.1-8b-instant\",
            \"llama-3.3-70b-versatile\",
            \"llama3-70b-8192\",
        ],
        help=\"llama-3.1-8b-instant çok daha hızlı ve rate limit yok gibi. 70B daha derin analiz yapar ama yavaş.\"
    )
    debug     = st.checkbox(\"🐛 Debug\", value=False)

    st.divider()
    st.markdown(\"### 💰 Oran Kaynakları\")

    st.markdown(\"\"\"<div style=\"background:#0d1829;border:1px solid #1c2e44;border-left:3px solid #00e5a0;
border-radius:6px;padding:8px 10px;font-size:.73rem;color:#7a9ab8;line-height:1.4;margin-bottom:6px\">
<b style=\"color:#00e5a0\">✅ The Odds API — AKTİF</b><br>
<span style=\"color:#3ecf7a\">Bet365 · Pinnacle · Unibet gerçek oranları</span>
</div>\"\"\", unsafe_allow_html=True)
    odds_api_key = ODDS_API_KEY_DEFAULT

    with st.expander(\"⚙️ API-Football Key (yedek)\", expanded=False):
        st.caption(\"The Odds API bulamazsa fallback. Ücretsiz 100 istek/gün.\")
        apifootball_key = st.text_input(
            \"API-Football Key\",
            value=AF_KEY_DEFAULT,
            type=\"password\",
            placeholder=\"dashboard.api-football.com → API Key\",
        )
    if 'apifootball_key' not in dir():
        apifootball_key = AF_KEY_DEFAULT

    auto_odds = st.checkbox(\"✅ Oranları otomatik çek\", value=True,
        help=\"The Odds API → API-Football → fdco.uk CSV → model tahmini sırasıyla dener\")
    tolerance = st.slider(\"Oran Toleransı (±)\", 0.10, 0.60, 0.30, 0.05,
                           help=\"Geçmiş pattern aramasında kabul edilen oran farkı\")
    n_seasons = st.slider(\"Kaç Sezon Analiz Edilsin\", 1, 5, 3)
    use_manual_odds = False
    manual_o1 = manual_ox = manual_o2 = None
    with st.expander(\"✏️ Manuel Oran Giriş\", expanded=False):
        st.caption(\"Hiçbir kaynak çalışmazsa buraya gir\")
        manual_o1 = st.number_input(\"1 (Ev Kazanır)\", min_value=1.01, max_value=30.0, value=2.0, step=0.01, format=\"%.2f\")
        manual_ox = st.number_input(\"X (Beraberlik)\", min_value=1.01, max_value=30.0, value=3.20, step=0.01, format=\"%.2f\")
        manual_o2 = st.number_input(\"2 (Dep Kazanır)\", min_value=1.01, max_value=30.0, value=3.80, step=0.01, format=\"%.2f\")
        use_manual_odds = st.checkbox(\"Bu oranları kullan\", value=False)

# ══════════════════════════════════════════════════════════════════
# API
# ══════════════════════════════════════════════════════════════════
BASE = \"https://api.football-data.org/v4\"

def fd_get(path, params=None, _retries=3):
    headers = {\"X-Auth-Token\": FD_KEY}
    url     = f\"{BASE}{path}\"
    for attempt in range(_retries):
        try:
            r = requests.get(url, headers=headers,
                             params=params or {},
                             timeout=(8, 30))
            if r.status_code == 429:
                wait = 66 if attempt == 0 else 10
                ph = st.empty()
                for i in range(wait, 0, -1):
                    ph.warning(f\"⏳ Rate limit — {i}sn bekleniyor...\")
                    time.sleep(1)
                ph.empty()
                continue
            if r.status_code == 200:
                if debug: st.caption(f\"🐛 {path} → 200\")
                return r.json()
            if debug: st.caption(f\"🐛 {path} → {r.status_code}\")
            return {}
        except requests.exceptions.ReadTimeout:
            if attempt < _retries - 1:
                time.sleep(3 * (attempt + 1))
                continue
            st.warning(f\"⚠️ Sunucu yanıt vermedi ({path}) — tekrar dene.\")
            return {}
        except requests.exceptions.ConnectionError:
            if attempt < _retries - 1:
                time.sleep(4)
                continue
            st.warning(f\"⚠️ Bağlantı hatası ({path})\")
            return {}
        except Exception as e:
            if debug: st.caption(f\"🐛 fd_get {path}: {e}\")
            return {}
    return {}

def api_matches(code, dt, lim):
    d = fd_get(f\"/competitions/{code}/matches\",
               {\"dateFrom\": dt, \"dateTo\": dt, \"status\": \"SCHEDULED,TIMED,POSTPONED\"})
    return d.get(\"matches\", [])[:lim]

def api_team_matches(tid, n):
    data = fd_get(
        f\"/teams/{tid}/matches\",
        {\"status\": \"FINISHED\", \"limit\": n}
    )
    matches = data.get(\"matches\", [])
    matches.sort(key=lambda m: m.get(\"utcDate\", \"\"), reverse=True)
    return matches[:n]

def api_h2h(mid, n):
    data = fd_get(f\"/matches/{mid}/head2head\", {\"limit\": n})
    matches = data.get(\"matches\", [])
    finished = [m for m in matches if m.get(\"status\") == \"FINISHED\"]
    finished.sort(key=lambda m: m.get(\"utcDate\", \"\"), reverse=True)
    return finished[:n]

def api_standings(code):
    try: return fd_get(f\"/competitions/{code}/standings\")[\"standings\"][0][\"table\"]
    except: return []

def api_scorers(code):
    return fd_get(f\"/competitions/{code}/scorers\", {\"limit\": 20}).get(\"scorers\", [])

def find_standing(table, tid):
    for row in table:
        if row[\"team\"][\"id\"] == tid: return row
    return {}
    
def find_scorer(scorers, tid):
    for s in scorers:
        if s[\"team\"][\"id\"] == tid: return s[\"player\"]
    return {}

# ── CANLI MAÇ API FONKSİYONLARI ──────────────────────────────────

def api_live_matches(code=None):
    import datetime as _dt

    LIVE_STATUSES = {\"IN_PLAY\", \"PAUSED\"}

    params = {\"status\": \"IN_PLAY,PAUSED\"}
    if code:
        raw = fd_get(f\"/competitions/{code}/matches\", params).get(\"matches\", [])
    else:
        raw = fd_get(\"/matches\", params).get(\"matches\", [])

    now_utc = _dt.datetime.utcnow()
    live = []
    for m in raw:
        status = m.get(\"status\", \"\")
        if status not in LIVE_STATUSES:
            continue

        utc_str = m.get(\"utcDate\", \"\")
        if utc_str:
            try:
                match_dt = _dt.datetime.strptime(utc_str[:16], \"%Y-%m-%dT%H:%M\")
                if match_dt > now_utc:
                    continue
                if (now_utc - match_dt).total_seconds() > 3 * 3600:
                    continue
            except:
                pass

        live.append(m)

    return live

def api_live_match_detail(match_id):
    return fd_get(f\"/matches/{match_id}\")

@st.cache_data(ttl=60, show_spinner=False)
def fetch_sofascore_live_stats(match_id_ss):
    try:
        headers = {
            \"User-Agent\": \"Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) \"
                          \"AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1\",
            \"Accept\": \"application/json\",
            \"Referer\": \"https://www.sofascore.com/\",
        }
        r = requests.get(
            f\"https://api.sofascore.com/api/v1/event/{match_id_ss}/statistics\",
            headers=headers, timeout=20
        )
        if r.status_code == 200:
            return r.json()
        return None
    except:
        return None

@st.cache_data(ttl=60, show_spinner=False)
def fetch_sofascore_live_event(h_name, a_name):
    try:
        headers = {
            \"User-Agent\": \"Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) \"
                          \"AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1\",
            \"Accept\": \"application/json\",
            \"Referer\": \"https://www.sofascore.com/\",
        }
        from datetime import date as _date
        today = _date.today().strftime(\"%Y-%m-%d\")
        r = requests.get(
            f\"https://api.sofascore.com/api/v1/sport/football/scheduled-events/{today}\",
            headers=headers, timeout=20
        )
        if r.status_code != 200:
            return None, None

        events = r.json().get(\"events\", [])
        for ev in events:
            status = ev.get(\"status\", {}).get(\"type\", \"\")
            if status not in (\"inprogress\", \"halftime\"):
                continue
            gh = ev.get(\"homeTeam\", {}).get(\"name\", \"\")
            ga = ev.get(\"awayTeam\", {}).get(\"name\", \"\")
            if fuzzy_match_team(gh, h_name) and fuzzy_match_team(ga, a_name):
                ev_id = ev.get(\"id\")
                r2 = requests.get(
                    f\"https://api.sofascore.com/api/v1/event/{ev_id}/statistics\",
                    headers=headers, timeout=20
                )
                stats_raw = r2.json() if r2.status_code == 200 else {}
                return ev, stats_raw

        return None, None
    except:
        return None, None

def parse_live_stats(stats_raw):
    result = {
        \"possession_h\": 50, \"possession_a\": 50,
        \"shots_h\": 0, \"shots_a\": 0,
        \"shots_on_h\": 0, \"shots_on_a\": 0,
        \"dangerous_h\": 0, \"dangerous_a\": 0,
        \"corners_h\": 0, \"corners_a\": 0,
        \"fouls_h\": 0, \"fouls_a\": 0,
        \"yellow_h\": 0, \"yellow_a\": 0,
        \"red_h\": 0, \"red_a\": 0,
        \"xg_h\": 0.0, \"xg_a\": 0.0,
        \"attacks_h\": 0, \"attacks_a\": 0,
    }
    if not stats_raw:
        return result

    stat_map = {
        \"Ball possession\": (\"possession_h\", \"possession_a\"),
        \"Total shots\": (\"shots_h\", \"shots_a\"),
        \"Shots on target\": (\"shots_on_h\", \"shots_on_a\"),
        \"Dangerous attacks\": (\"dangerous_h\", \"dangerous_a\"),
        \"Corner kicks\": (\"corners_h\", \"corners_a\"),
        \"Fouls\": (\"fouls_h\", \"fouls_a\"),
        \"Yellow cards\": (\"yellow_h\", \"yellow_a\"),
        \"Red cards\": (\"red_h\", \"red_a\"),
        \"Expected goals\": (\"xg_h\", \"xg_a\"),
        \"Attacks\": (\"attacks_h\", \"attacks_a\"),
        \"Total Shots\": (\"shots_h\", \"shots_a\"),
        \"Shots On Target\": (\"shots_on_h\", \"shots_on_a\"),
    }

    periods = stats_raw.get(\"statistics\", [])
    stat_list = []
    for p in periods:
        if p.get(\"period\") in (\"ALL\", \"2ND\", \"1ST\"):
            stat_list = p.get(\"groups\", [])
            if p.get(\"period\") == \"ALL\":
                break

    for group in stat_list:
        for item in group.get(\"statisticsItems\", []):
            name = item.get(\"name\", \"\")
            if name in stat_map:
                hk, ak = stat_map[name]
                try:
                    hv = item.get(\"home\", \"0\")
                    av = item.get(\"away\", \"0\")
                    hv = float(str(hv).replace(\"%\",\"\").strip() or 0)
                    av = float(str(av).replace(\"%\",\"\").strip() or 0)
                    result[hk] = hv
                    result[ak] = av
                except:
                    pass
    return result

def calc_live_goal_probability(live_stats, minute, h_score, a_score, hf, af, league_code=None):
    import math as _math

    fv = lambda d, k, dv=0: d.get(k, dv) if d else dv

    LEAGUE_AVG = {
        \"SA\":  2.55, \"FL1\": 2.60, \"PD\":  2.65,
        \"PPL\": 2.65, \"PL\":  2.80, \"ELC\": 2.75,
        \"BL1\": 3.10, \"DED\": 3.10, \"CL\":  2.80,
        \"EL\":  2.75, \"BSA\": 2.50,
    }
    league_avg = LEAGUE_AVG.get(league_code, 2.70)

    elapsed       = max(1, minute)
    is_first_half = elapsed <= 45
    ht_remaining  = max(0, 47 - elapsed) if is_first_half else 0
    ms_remaining  = max(0, 92 - elapsed)
    rem_frac      = ms_remaining / 90.0
    ht_rem_frac   = ht_remaining / 45.0
    total_goals   = h_score + a_score

    form_avg_gf_h = fv(hf, \"avg_gf\", league_avg * 0.5)
    form_avg_gf_a = fv(af, \"avg_gf\", league_avg * 0.5)
    form_rate_raw = form_avg_gf_h + form_avg_gf_a
    form_rate = max(league_avg * 0.6, min(league_avg * 1.4, form_rate_raw))

    ht_form_h = fv(hf, \"ht_avg_gf\", form_avg_gf_h * 0.42)
    ht_form_a = fv(af, \"ht_avg_gf\", form_avg_gf_a * 0.42)
    ht_form_rate = ht_form_h + ht_form_a

    live_xg_h     = live_stats.get(\"xg_h\", 0) or 0
    live_xg_a     = live_stats.get(\"xg_a\", 0) or 0
    live_xg_total = live_xg_h + live_xg_a

    if live_xg_total > 0.05 and elapsed > 8:
        live_xg_rate = (live_xg_total / elapsed * 90)
        live_xg_rate = min(live_xg_rate, league_avg * 1.8)
        xg_rate = live_xg_rate * 0.50 + form_rate * 0.30 + league_avg * 0.20
    elif total_goals > 0 and elapsed > 10:
        goal_rate_live = total_goals / elapsed * 90
        xg_rate = goal_rate_live * 0.35 + form_rate * 0.40 + league_avg * 0.25
    else:
        xg_rate = form_rate * 0.55 + league_avg * 0.45

    dan_h      = live_stats.get(\"dangerous_h\", 0) or 0
    dan_a      = live_stats.get(\"dangerous_a\", 0) or 0
    shots_h    = live_stats.get(\"shots_h\", 0) or 0
    shots_on_h = live_stats.get(\"shots_on_h\", 0) or 0
    shots_a    = live_stats.get(\"shots_a\", 0) or 0
    shots_on_a = live_stats.get(\"shots_on_a\", 0) or 0

    dan_total = dan_h + dan_a
    if dan_total > 0 and elapsed > 5:
        dan_rate = dan_total / elapsed
        dan_threshold = 0.35 if league_avg < 2.65 else 0.28
        dan_multiplier = min(1.35, 1.0 + max(0, (dan_rate - dan_threshold)) * 0.4)
    else:
        dan_multiplier = 1.0

    if shots_h + shots_a >= 4:
        shot_acc = (shots_on_h + shots_on_a) / (shots_h + shots_a)
        expected_acc = 0.30 if league_avg < 2.65 else 0.35
        shot_mult = min(1.15, 0.92 + (shot_acc - expected_acc) * 0.8)
    else:
        shot_mult = 1.0

    combined_mult = min(1.45, dan_multiplier * shot_mult)

    expected_ms = max(0.05, xg_rate * rem_frac * combined_mult)
    expected_ht = max(0.02, ht_form_rate * ht_rem_frac * combined_mult) if is_first_half and ht_remaining > 0 else 0.0

    if live_xg_h > 0.03 and elapsed > 8:
        exp_h_rate = (live_xg_h / elapsed * 90) * 0.5 + form_avg_gf_h * 0.3 + league_avg * 0.2 * 0.5
        exp_a_rate = (live_xg_a / elapsed * 90) * 0.5 + form_avg_gf_a * 0.3 + league_avg * 0.2 * 0.5
    else:
        exp_h_rate = form_avg_gf_h * 0.6 + league_avg * 0.4 * 0.5
        exp_a_rate = form_avg_gf_a * 0.6 + league_avg * 0.4 * 0.5

    exp_h_rem = max(0.02, exp_h_rate * rem_frac * combined_mult)
    exp_a_rem = max(0.02, exp_a_rate * rem_frac * combined_mult)
    exp_h_ht  = max(0.01, fv(hf, \"ht_avg_gf\", exp_h_rate * 0.42) * ht_rem_frac * combined_mult)
    exp_a_ht  = max(0.01, fv(af, \"ht_avg_gf\", exp_a_rate * 0.42) * ht_rem_frac * combined_mult)

    def poi(lam, k):
        lam = max(0.001, lam)
        return _math.exp(-lam) * (lam ** k) / _math.factorial(k)

    def p_at_least(lam, n):
        return max(0.0, 1 - sum(poi(lam, k) for k in range(int(n))))

    cur = total_goals
    market_probs = {}
    for thr in [1.5, 2.5, 3.5, 4.5]:
        needed = thr - cur
        if needed <= 0:
            market_probs[f\"o{int(thr*10)}\"] = 99.0
            market_probs[f\"u{int(thr*10)}\"] = 1.0
        else:
            p_over = round(p_at_least(expected_ms, needed) * 100, 1)
            market_probs[f\"o{int(thr*10)}\"] = p_over
            market_probs[f\"u{int(thr*10)}\"] = round(100 - p_over, 1)

    ht_market = {}
    if is_first_half and ht_remaining > 0:
        for thr in [0.5, 1.5, 2.5]:
            needed = thr - total_goals
            if needed <= 0:
                ht_market[f\"ht_o{int(thr*10)}\"] = 99.0
                ht_market[f\"ht_u{int(thr*10)}\"] = 1.0
            else:
                p_over = round(p_at_least(expected_ht, needed) * 100, 1)
                ht_market[f\"ht_o{int(thr*10)}\"] = p_over
                ht_market[f\"ht_u{int(thr*10)}\"] = round(100 - p_over, 1)

        if h_score > 0 and a_score > 0:
            ht_market[\"ht_kg_var\"] = 99.0
        elif h_score > 0:
            ht_market[\"ht_kg_var\"] = round(p_at_least(exp_a_ht, 1) * 100, 1)
        elif a_score > 0:
            ht_market[\"ht_kg_var\"] = round(p_at_least(exp_h_ht, 1) * 100, 1)
        else:
            ht_market[\"ht_kg_var\"] = round(p_at_least(exp_h_ht, 1) * p_at_least(exp_a_ht, 1) * 100, 1)

        ht_market[\"ht_next_h\"] = round(p_at_least(exp_h_ht, 1) * 100, 1)
        ht_market[\"ht_next_a\"] = round(p_at_least(exp_a_ht, 1) * 100, 1)

    if h_score > 0 and a_score > 0:
        p_kg_var = 99.0
    elif h_score > 0:
        p_kg_var = round(p_at_least(exp_a_rem, 1) * 100, 1)
    elif a_score > 0:
        p_kg_var = round(p_at_least(exp_h_rem, 1) * 100, 1)
    else:
        p_kg_var = round(p_at_least(exp_h_rem, 1) * p_at_least(exp_a_rem, 1) * 100, 1)

    total_attacks = dan_h + dan_a + shots_h + shots_a
    momentum_h = max(0, min(100, round((dan_h + shots_on_h * 1.5) / max(1, dan_h + dan_a + shots_on_h + shots_on_a) * 100))) if total_attacks > 0 else 50

    return {
        \"elapsed\":            elapsed,
        \"remaining_min\":      ms_remaining,
        \"ht_remaining_min\":   ht_remaining,
        \"is_first_half\":      is_first_half,
        \"expected_remaining\": round(expected_ms, 2),
        \"expected_ht\":        round(expected_ht, 2),
        \"xg_rate_per90\":      round(xg_rate, 2),
        \"league_avg\":         league_avg,
        \"p_next_goal\":        round(p_at_least(expected_ms, 1) * 100, 1),
        \"p_next_h\":           round(p_at_least(exp_h_rem, 1) * 100, 1),
        \"p_next_a\":           round(p_at_least(exp_a_rem, 1) * 100, 1),
        \"p_kg_var\":           p_kg_var,
        \"momentum_h\":         momentum_h,
        \"dan_multiplier\":     round(combined_mult, 2),
        **market_probs,
        **ht_market,
    }

def build_live_prompt(h, a, minute, h_score, a_score, ht_h, ht_a,
                      live_stats, lp, hf, af, h2h):
    fv = lambda d, k, dv=0: d.get(k, dv) if d else dv

    is_ht = lp.get(\"is_first_half\", minute <= 45)
    ht_rem = lp.get(\"ht_remaining_min\", 0)
    ms_rem = lp.get(\"remaining_min\", 0)

    league_desc = {\"SA\":\"Serie A (düşük gol ligi, ort 2.55/maç)\",\"FL1\":\"Ligue 1 (düşük gol ligi, ort 2.60/maç)\",\"PD\":\"La Liga (ort 2.65/maç)\",\"BL1\":\"Bundesliga (yüksek gol ligi, ort 3.10/maç)\",\"DED\":\"Eredivisie (yüksek gol ligi, ort 3.10/maç)\",\"PL\":\"Premier League (ort 2.80/maç)\"}.get(live_league if \"live_league\" in dir() else \"\", f\"Lig ort: {lp.get('league_avg',2.70):.2f} gol/maç\")
    stat_block = f\"\"\"CANLI İSTATİSTİKLER — Dakika {minute}:
  LİG KARAKTERİ: {league_desc}
  Skor: {h} {h_score} – {a_score} {a}{\"  (1. Yarı)\" if is_ht else \"  (2. Yarı / İY: \" + str(ht_h) + \"-\" + str(ht_a) + \")\"}
  Top Kontrolü: %{live_stats.get('possession_h',50)} EV — %{live_stats.get('possession_a',50)} DEP
  Şut (İsabetli): {int(live_stats.get('shots_h',0))} ({int(live_stats.get('shots_on_h',0))}) EV — {int(live_stats.get('shots_on_a',0))} ({int(live_stats.get('shots_a',0))}) DEP
  Tehlikeli Atak: {int(live_stats.get('dangerous_h',0))} EV — {int(live_stats.get('dangerous_a',0))} DEP
  xG: {live_stats.get('xg_h',0):.2f} EV — {live_stats.get('xg_a',0):.2f} DEP
  Korner: {int(live_stats.get('corners_h',0))} EV — {int(live_stats.get('corners_a',0))} DEP
  Sarı Kart: {int(live_stats.get('yellow_h',0))} EV — {int(live_stats.get('yellow_a',0))} DEP
  Momentum Skoru (0=dep baskısı, 100=ev baskısı): {lp.get('momentum_h',50)}/100
  Atak Çarpanı: x{lp.get('dan_multiplier',1.0)}\"\"\"

    ht_block = \"\"
    if is_ht and ht_rem > 0:
        ht_block = f\"\"\"
İLK YARI KALAN SÜRE ({ht_rem} dk kaldı):
  İY Mevcut Gol: {h_score + a_score} | Beklenen Ek İY Gol: {lp.get('expected_ht', 0)}
  İY 0.5 ÜST: %{lp.get('ht_o5', 0)} | İY 0.5 ALT: %{lp.get('ht_u5', 0)}
  İY 1.5 ÜST: %{lp.get('ht_o15', 0)} | İY 1.5 ALT: %{lp.get('ht_u15', 0)}
  İY 2.5 ÜST: %{lp.get('ht_o25', 0)}
  İY KG VAR: %{lp.get('ht_kg_var', 0)}
  Sonraki İY Gol EV: %{lp.get('ht_next_h', 0)} | Sonraki İY Gol DEP: %{lp.get('ht_next_a', 0)}
  Tarihsel: {h} İY ort gol {fv(hf,'ht_avg_gf',0)} | {a} İY ort gol {fv(af,'ht_avg_gf',0)}
  H2H İY: {h2h.get('ht_hw',0)}G-{h2h.get('ht_dr',0)}B-{h2h.get('ht_aw',0)}M\"\"\"

    ms_block = f\"\"\"
MAÇ SONU ({ms_rem} dk kaldı):
  Beklenen Ek Gol: {lp.get('expected_remaining', 0)} | Sonraki Gol: %{lp.get('p_next_goal', 0)}
  Sonraki Gol EV: %{lp.get('p_next_h', 0)} | Sonraki Gol DEP: %{lp.get('p_next_a', 0)}
  1.5 ÜST: %{lp.get('o15', 0)} | 2.5 ÜST: %{lp.get('o25', 0)} | 3.5 ÜST: %{lp.get('o35', 0)}
  2.5 ALT: %{lp.get('u25', 0)} | 3.5 ALT: %{lp.get('u35', 0)}
  KG VAR: %{lp.get('p_kg_var', 0)}\"\"\"

    form_block = f\"\"\"
TARİHSEL FORM:
  {h}: {fv(hf,'form_str','?')} | Ort gol: {fv(hf,'avg_gf',0)} att/{fv(hf,'avg_gc',0)} yedi
     İY ort: {fv(hf,'ht_avg_gf',0)} att/{fv(hf,'ht_avg_gc',0)} yedi | 2Y ort: {fv(hf,'st_avg_gf',0)}/{fv(hf,'st_avg_gc',0)}
     2.5 Üst: {fv(hf,'o25',0)}/{fv(hf,'n',1)} maç | KG VAR: {fv(hf,'btts',0)}/{fv(hf,'n',1)}
  {a}: {fv(af,'form_str','?')} | Ort gol: {fv(af,'avg_gf',0)} att/{fv(af,'avg_gc',0)} yedi
     İY ort: {fv(af,'ht_avg_gf',0)} att/{fv(af,'ht_avg_gc',0)} yedi | 2Y ort: {fv(af,'st_avg_gf',0)}/{fv(af,'st_avg_gc',0)}
     2.5 Üst: {fv(af,'o25',0)}/{fv(af,'n',1)} maç | KG VAR: {fv(af,'btts',0)}/{fv(af,'n',1)}
  H2H: Ort {h2h.get('avg_goals',0)} gol/maç | 2.5 Üst %{h2h.get('o25_pct',0)} | KG VAR %{h2h.get('btts_pct',0)}
     Son İY Skorları: {' '.join(h2h.get('ht_scores',[])[:4])}\"\"\"

    iy_section = f\"\"\"
### 2. İLK YARI GOL ANALİZİ
{f\"İY {ht_rem} dakika kaldı — mevcut: {h_score}-{a_score}\" if is_ht and ht_rem > 0 else \"İLK YARI TAMAMLANDI — İY skoru: \" + str(ht_h) + \"-\" + str(ht_a)}
{\"[Yukarıdaki İY olasılık sayılarını kullan. Kalan süre EXACTLY \" + str(ht_rem) + \" dakika. Skor \" + str(h_score) + \"-\" + str(a_score) + \". Bu sayıları değiştirme. İY 0.5 Üst/Alt için net karar ver.]\" if is_ht and ht_rem > 0 else \"[İY skoru \" + str(ht_h) + \"-\" + str(ht_a) + \". 2. yarıda gol beklentisini değerlendir.]\"}

İY BAHİS TAVSİYESİ:
{(\"IY_BAHSI_1: [pazar adı — ör: İY 0.5 Alt veya İY 1.5 Alt veya İY KG YOK — ZATEN OLAN PAZARLARI ÖNERME] — [gerekçe] — GÜVENİLİRLİK: [YÜKSEK/ORTA/DÜŞÜK]\" if is_ht and ht_rem > 0 else \"IY_BAHSI_1: İY tamamlandı\")}
{\"IY_BAHSI_2: [pazar adı] — [gerekçe] — GÜVENİLİRLİK: [YÜKSEK/ORTA/DÜŞÜK]\" if is_ht and ht_rem > 0 else \"\"}\"\"\" if is_ht else f\"\"\"
### 2. İLK YARI SONUCU
İY skoru: {ht_h}-{ht_a} (EV {ht_h}, DEP {ht_a})
[İY sonucunun 2Y gol beklentisine etkisi — hangi takım 2Y'da daha fazla gol arar, neden?]\
    return f"""Sen bir profesyonel canlı bahis analistisin. Türkçe yaz. Her cümle bu maça özgü olmalı — jenerik yorum yasak.

KRİTİK KURALLAR:
1. Sadece KALAN SÜREYE uygun pazar öner — maç biterken "2.5 Üst" önermek anlamsız.
2. Zaten gerçekleşmiş pazarları ÖNERME — skor 1-1 iken "MS 1.5 Üst" işe yaramaz.
3. TUTARLI OL — aynı maça hem "2.5 Üst" hem "2.5 Alt" önerme, hangisi daha güçlüyse onu seç.
4. Kalan süre {ms_rem}dk, skor {h_score}-{a_score} — buna göre hangi pazarın değeri var düşün.
5. Oran 1.05 olan pazar önerme — %95+ olasılıklı pazarların oran değeri yok.

MAÇ: {h} (EV) vs {a} (DEP) — Dakika: {minute}'
{stat_block}
{ht_block}
{ms_block}
{form_block}

AYNEN bu formatta yaz (başlıkları değiştirme):

### 1. CANLI DURUM ANALİZİ
[Hangi takım baskıda, momentum nerede, istatistik rakamlarını kullanarak 2 cümle]

{iy_section}

### 3. MAÇ SONU GOL BEKLENTİSİ
[xG hızı + form + kalan süreyi harmanlayarak 2.5 Üst/Alt ve KG VAR/YOK için NET karar — "Üst alınır çünkü..." veya "Alt alınır çünkü..." formatında]

### 4. GOL BAHİS TAVSİYELERİ
GOL_BAHSI_1: [pazar] — [gerekçe, max 12 kelime] — GÜVENİLİRLİK: [YÜKSEK/ORTA/DÜŞÜK]
GOL_BAHSI_2: [pazar] — [gerekçe, max 12 kelime] — GÜVENİLİRLİK: [YÜKSEK/ORTA/DÜŞÜK]
GOL_BAHSI_3: [pazar] — [gerekçe, max 12 kelime] — GÜVENİLİRLİK: [YÜKSEK/ORTA/DÜŞÜK]

Pazar seçenekleri: "İY 0.5 ÜST", "İY 0.5 ALT", "İY 1.5 ÜST", "İY KG VAR", "İY KG YOK",
"2.5 ÜST", "2.5 ALT", "3.5 ÜST", "KG VAR", "KG YOK",
"Sonraki gol EV ({h})", "Sonraki gol DEP ({a})", "Gol YOK (0.5 Alt)"

### 5. EN İYİ BAHIS
ŞIMDI_AL: [tek en iyi pazar] — [neden şu an ideal — max 15 kelime]
GEÇME: [kaçınılacak pazar] — [neden riskli — max 12 kelime]"""

# ══════════════════════════════════════════════════════════════════
# VERİ İŞLEME
# ══════════════════════════════════════════════════════════════════

def _calc_score_freq(score_pairs):
    from collections import Counter
    c = Counter(score_pairs)
    total = sum(c.values())
    return {f"{h}-{a}": {"count": cnt, "pct": round(cnt/total*100, 1)}
            for (h, a), cnt in sorted(c.items(), key=lambda x: -x[1])}

def parse_form(matches, tid):
    if not matches:
        return {}
    ms_r, ht_r = [], []
    gf, gc, htgf, htgc = [], [], [], []
    h_gf = h_gc = h_n = a_gf = a_gc = a_n = 0
 
    for m in matches:
        if m.get("status") != "FINISHED":
            continue
 
        hid = m["homeTeam"]["id"]
 
        ft   = m.get("score", {}).get("fullTime") or {}
        fh   = ft.get("home") or 0
        fa   = ft.get("away") or 0
 
        ht_score = m.get("score", {}).get("halfTime") or {}
        hh = ht_score.get("home") or 0
        ha = ht_score.get("away") or 0
 
        fh = int(fh); fa = int(fa)
        hh = int(hh); ha = int(ha)
 
        if hid == tid:
            my_f, op_f, my_h, op_h = fh, fa, hh, ha
            h_gf += fh; h_gc += fa; h_n += 1
        else:
            my_f, op_f, my_h, op_h = fa, fh, ha, hh
            a_gf += fa; a_gc += fh; a_n += 1
 
        ms_r.append("G" if my_f > op_f else "B" if my_f == op_f else "M")
        ht_r.append("G" if my_h > op_h else "B" if my_h == op_h else "M")
        gf.append(my_f);   gc.append(op_f)
        htgf.append(my_h); htgc.append(op_h)
 
    n = len(ms_r)
    if n == 0:
        return {}
 
    pts5  = sum({"G": 3, "B": 1, "M": 0}[r] for r in ms_r[:5])
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
        "pts5": pts5, "pts_pct": round(pts5 / 15 * 100, 1),
        "avg_gf":  round(sum(gf) / n, 2),    "avg_gc":  round(sum(gc) / n, 2),
        "ht_avg_gf": round(sum(htgf) / n, 2), "ht_avg_gc": round(sum(htgc) / n, 2),
        "st_avg_gf": round(sum(st_gf) / n, 2),"st_avg_gc": round(sum(st_gc) / n, 2),
        "ht_pct": ht_pct, "st_pct": round(100 - ht_pct, 1),
        "h_avg_gf": round(h_gf / h_n, 2) if h_n else 0,
        "h_avg_gc": round(h_gc / h_n, 2) if h_n else 0, "h_n": h_n,
        "a_avg_gf": round(a_gf / a_n, 2) if a_n else 0,
        "a_avg_gc": round(a_gc / a_n, 2) if a_n else 0, "a_n": a_n,
        "btts":  sum(1 for f, c in zip(gf, gc) if f > 0 and c > 0),
        "o25":   sum(1 for f, c in zip(gf, gc) if f + c > 2),
        "o35":   sum(1 for f, c in zip(gf, gc) if f + c > 3),
        "cs":    sum(1 for c in gc if c == 0),
        "fts":   sum(1 for f in gf if f == 0),
        "streak": f"{sn} {'galibiyet' if sr == 'G' else 'beraberlik' if sr == 'B' else 'mağlubiyet'} serisi",
        "ms_scores": [f"{f}-{c}" for f, c in zip(gf[:6], gc[:6])],
        "ht_scores": [f"{h}-{a}" for h, a in zip(htgf[:6], htgc[:6])],
        "ht_score_freq": _calc_score_freq(list(zip(htgf, htgc))),
        "ms_score_freq": _calc_score_freq(list(zip(gf, gc))),
    }

def parse_h2h(matches, home_id):
    if not matches:
        return {}
 
    hw = aw = dr = ht_hw = ht_aw = ht_dr = 0
    rev21 = rev12 = revx1 = revx2 = btts = o25 = 0
    gl, ms_sc, ht_sc = [], [], []
 
    for m in matches:
        if m.get("status") != "FINISHED":
            continue
 
        hid = m["homeTeam"]["id"]
 
        ft = m.get("score", {}).get("fullTime") or {}
        fh = int(ft.get("home") or 0)
        fa = int(ft.get("away") or 0)
 
        ht_score = m.get("score", {}).get("halfTime") or {}
        hh = int(ht_score.get("home") or 0)
        ha = int(ht_score.get("away") or 0)
 
        if hid == home_id:
            my_f, op_f, my_h, op_h = fh, fa, hh, ha
        else:
            my_f, op_f, my_h, op_h = fa, fh, ha, hh
 
        if my_f > op_f:   hw += 1
        elif my_f < op_f: aw += 1
        else:             dr += 1
 
        if my_h > op_h:   ht_hw += 1
        elif my_h < op_h: ht_aw += 1
        else:             ht_dr += 1
 
        if my_h < op_h and my_f > op_f: rev21 += 1
        if my_h > op_h and my_f < op_f: rev12 += 1
        if my_h == op_h and my_f > op_f: revx1 += 1
        if my_h == op_h and my_f < op_f: revx2 += 1
 
        if my_f > 0 and op_f > 0: btts += 1
        if my_f + op_f > 2:       o25  += 1
 
        gl.append(my_f + op_f)
        ms_sc.append(f"{my_f}-{op_f}")
        ht_sc.append(f"{my_h}-{op_h}")
 
    n = len(gl)
    if n == 0:
        return {}
 
    p = lambda x: round(x / n * 100, 1)
    return {
        "n": n, "hw": hw, "dr": dr, "aw": aw,
        "hw_pct": p(hw), "dr_pct": p(dr), "aw_pct": p(aw),
        "ht_hw": ht_hw, "ht_dr": ht_dr, "ht_aw": ht_aw,
        "ht_hw_pct": p(ht_hw), "ht_dr_pct": p(ht_dr), "ht_aw_pct": p(ht_aw),
        "rev21": rev21, "rev21_pct": p(rev21),
        "rev12": rev12, "rev12_pct": p(rev12),
        "revx1": revx1, "revx1_pct": p(revx1),
        "revx2": revx2, "revx2_pct": p(revx2),
        "avg_goals": round(sum(gl) / n, 2) if n else 0,
        "o25": o25, "o25_pct": p(o25),
        "btts": btts, "btts_pct": p(btts),
        "ms_scores": ms_sc, "ht_scores": ht_sc,
    }

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
# ODDS MODÜLÜ
# ══════════════════════════════════════════════════════════════════

FDCOUK_FIXTURE_URL = "https://www.football-data.co.uk/fixtures.csv"

FD_ORG_TO_COUK = {
    "PL":"E0","ELC":"E1","PD":"SP1","BL1":"D1",
    "SA":"I1","FL1":"F1","DED":"N1","PPL":"P1",
}

FD_ORG_TO_ODDSAPI = {
    "PL":  "soccer_epl",
    "ELC": "soccer_efl_champ",
    "PD":  "soccer_spain_la_liga",
    "BL1": "soccer_germany_bundesliga",
    "SA":  "soccer_italy_serie_a",
    "FL1": "soccer_france_ligue_one",
    "DED": "soccer_netherlands_eredivisie",
    "PPL": "soccer_portugal_primeira_liga",
    "CL":  "soccer_uefa_champs_league",
    "EL":  "soccer_uefa_europa_league",
    "ECL": "soccer_uefa_europa_conference_league",
    "BSA": "soccer_brazil_campeonato",
}

ODDS_API_KEY = ODDS_API_KEY_DEFAULT

SEASON_CODES = ["2526","2425","2324","2223","2122","2021"]

@st.cache_data(ttl=1800, show_spinner=False)
def fetch_fixtures_with_odds(couk_code):
    import io, csv as _csv

    def fetch_text(url):
        try:
            r = requests.get(url, timeout=15)
            if r.status_code != 200:
                return []
            try:    txt = r.content.decode("utf-8")
            except: txt = r.content.decode("latin-1")
            rows = list(_csv.DictReader(io.StringIO(txt)))
            return [row for row in rows if any(v.strip() for v in row.values())]
        except:
            return []

    def extract_odds(rows, require_div=None):
        out = {}
        for row in rows:
            if require_div and row.get("Div","").strip() != require_div:
                continue
            home = row.get("HomeTeam","").strip()
            away = row.get("AwayTeam","").strip()
            if not home or not away:
                continue
            fthg = row.get("FTHG","").strip()
            if fthg not in ("","?","-"):
                continue
            def pick(*keys):
                for k in keys:
                    v = _safe_float(row.get(k,""))
                    if v and v > 1.0: return v
                return None
            o1  = pick("B365H","AvgH","PSH","IWH","VCH","WHH")
            ox  = pick("B365D","AvgD","PSD","IWD","VCD","WHD")
            o2  = pick("B365A","AvgA","PSA","IWA","VCA","WHA")
            if not (o1 and ox and o2):
                continue
            o25 = pick("B365>2.5","Avg>2.5","P>2.5")
            u25 = pick("B365<2.5","Avg<2.5","P<2.5")
            src = "Bet365" if row.get("B365H","").strip() else "football-data.co.uk"
            out[f"{home}|||{away}"] = {
                "home":home,"away":away,
                "o1":o1,"ox":ox,"o2":o2,
                "o25_ov":o25,"o25_un":u25,
                "source": f"football-data.co.uk ({src})"
            }
        return out

    rows = fetch_text(FDCOUK_FIXTURE_URL)
    result = extract_odds(rows, require_div=couk_code)
    if result:
        return result

    for season in ["2526","2425"]:
        url = f"https://www.football-data.co.uk/mmz4281/{season}/{couk_code}.csv"
        rows = fetch_text(url)
        if rows:
            r2 = extract_odds(rows, require_div=None)
            if r2:
                return r2

    return {}

AF_BASE   = "https://v3.football.api-sports.io"

FD_TO_AF_LEAGUE = {
    "PL": 39, "ELC": 40, "FAC": 45,
    "PD": 140, "BL1": 78, "SA": 135,
    "FL1": 61, "DED": 88, "PPL": 94,
    "CL": 2, "EL": 3, "ECL": 848,
    "BSA": 71,
}

@st.cache_data(ttl=3600, show_spinner=False)
def af_get(endpoint, params, key):
    try:
        r = requests.get(
            f"{AF_BASE}/{endpoint}",
            headers={"x-apisports-key": key},
            params=params, timeout=15
        )
        if r.status_code == 200:
            data = r.json()
            if debug:
                rem = r.headers.get("X-RateLimit-Remaining","?")
                st.caption(f"🐛 AF /{endpoint} → {r.status_code} | Kalan istek: {rem}")
            return data.get("response", [])
        if r.status_code == 401:
            st.warning("⚠️ API-Football key geçersiz — dashboard.api-football.com'dan kontrol edin")
        elif r.status_code == 499:
            st.warning("⚠️ API-Football günlük limit doldu (100 istek/gün)")
        if debug:
            st.caption(f"🐛 AF /{endpoint} → HTTP {r.status_code}")
        return []
    except Exception as e:
        if debug: st.caption(f"🐛 AF error: {e}")
        return []

def get_af_fixture_id(af_key, league_id, match_date, home_name, away_name):
    year = int(match_date[:4])
    month = int(match_date[5:7])
    season_year = year if month >= 7 else year - 1

    fixtures = af_get("fixtures", {
        "league": league_id,
        "date":   match_date,
        "season": season_year,
    }, af_key)

    if debug:
        st.caption(f"🐛 AF fixtures league={league_id} date={match_date} season={season_year} → {len(fixtures)} maç")
        for fx in fixtures[:3]:
            h_n = fx.get("teams",{}).get("home",{}).get("name","?")
            a_n = fx.get("teams",{}).get("away",{}).get("name","?")
            st.caption(f"🐛   {h_n} vs {a_n}")

    for f in fixtures:
        h = f.get("teams",{}).get("home",{}).get("name","")
        a = f.get("teams",{}).get("away",{}).get("name","")
        if fuzzy_match_team(h, home_name) and fuzzy_match_team(a, away_name):
            return f.get("fixture",{}).get("id")
    return None

def get_af_odds(af_key, fixture_id):
    odds_data = af_get("odds", {"fixture": fixture_id}, af_key)

    if debug:
        st.caption(f"🐛 AF /odds fixture={fixture_id} → {len(odds_data)} item")

    def parse_bookmaker(bm):
        o1 = ox = o2 = o25_ov = o25_un = None
        for bet in bm.get("bets", []):
            bet_name = bet.get("name", "").lower()
            bet_id   = bet.get("id", 0)
            if (bet_id == 1 or "match winner" in bet_name) and o1 is None:
                for v in bet.get("values", []):
                    val = v.get("value", "")
                    odd = _safe_float(v.get("odd"))
                    if val in ("Home", "1"):    o1 = odd
                    elif val in ("Draw", "X"):  ox = odd
                    elif val in ("Away", "2"):  o2 = odd
            if (bet_id == 5 or "goals over/under" in bet_name) and o25_ov is None:
                for v in bet.get("values", []):
                    val = v.get("value", "")
                    odd = _safe_float(v.get("odd"))
                    if "over" in val.lower() and "2.5" in val:  o25_ov = odd
                    elif "under" in val.lower() and "2.5" in val: o25_un = odd
        return o1, ox, o2, o25_ov, o25_un

    best_o1 = best_ox = best_o2 = best_o25_ov = best_o25_un = None
    best_source = "api-football.com"

    for item in odds_data:
        bookmakers = item.get("bookmakers", [])

        bet365_bm = next((bm for bm in bookmakers
                          if "bet365" in bm.get("name","").lower()), None)
        if bet365_bm:
            o1, ox, o2, o25_ov, o25_un = parse_bookmaker(bet365_bm)
            if o1 and ox and o2:
                best_o1, best_ox, best_o2 = o1, ox, o2
                best_o25_ov, best_o25_un = o25_ov, o25_un
                best_source = "Bet365"
                if debug: st.caption(f"🐛 Bet365 oranı bulundu: 1={o1} X={ox} 2={o2}")
                break

        if not best_o1:
            for bm in bookmakers:
                o1, ox, o2, o25_ov, o25_un = parse_bookmaker(bm)
                if o1 and ox and o2:
                    best_o1, best_ox, best_o2 = o1, ox, o2
                    best_o25_ov, best_o25_un = o25_ov, o25_un
                    best_source = bm.get("name", "api-football.com")
                    if debug: st.caption(f"🐛 [{best_source}] oranı bulundu: 1={o1} X={ox} 2={o2}")
                    break

        if best_o1:
            break

    if not (best_o1 and best_ox and best_o2):
        if debug: st.caption(f"🐛 AF odds bulunamadı fixture_id={fixture_id}")
        return None

    return {
        "o1": round(best_o1,2), "ox": round(best_ox,2), "o2": round(best_o2,2),
        "o25_ov": round(best_o25_ov,2) if best_o25_ov else None,
        "o25_un": round(best_o25_un,2) if best_o25_un else None,
        "source": best_source
    }

def get_match_odds(sel_code, odds_api_key, hn, an, auto_odds,
                   match_date=None, af_key=None):
    if not auto_odds:
        return None

    if odds_api_key and odds_api_key.strip():
        result = get_odds_api_odds(odds_api_key, sel_code, hn, an, match_date)
        if result:
            return result

    if af_key and af_key.strip():
        af_league = FD_TO_AF_LEAGUE.get(sel_code)
        if af_league and match_date:
            cache_fid = f"af_fid_{sel_code}_{match_date}_{hn[:6]}"
            if cache_fid not in st.session_state:
                fid = get_af_fixture_id(af_key, af_league, match_date, hn, an)
                st.session_state[cache_fid] = fid
            else:
                fid = st.session_state[cache_fid]
            if debug: st.caption(f"🐛 AF fixture_id={fid} | {hn} vs {an}")
            if fid:
                cache_odds = f"af_odds_{fid}"
                if cache_odds not in st.session_state:
                    result = get_af_odds(af_key, fid)
                    st.session_state[cache_odds] = result
                else:
                    result = st.session_state[cache_odds]
                if result:
                    return result

    couk_code = FD_ORG_TO_COUK.get(sel_code)
    if couk_code:
        fo_key = f"fdcouk_{couk_code}"
        if fo_key not in st.session_state:
            fo = fetch_fixtures_with_odds(couk_code)
            st.session_state[fo_key] = fo
        else:
            fo = st.session_state[fo_key]
        if debug:
            st.caption(f"🐛 fdcouk [{couk_code}] {len(fo)} maç bulundu")
        result = match_odds_to_fixture(fo, hn, an)
        if result:
            return result

    if match_date:
        result = get_sofascore_odds(hn, an, match_date)
        if result:
            return result

    return None

ODDS_API_BASE = "https://api.the-odds-api.com/v4"

FD_TO_ODDSAPI_SPORT = {
    "PL":  "soccer_epl",
    "ELC": "soccer_efl_champ",
    "PD":  "soccer_spain_la_liga",
    "BL1": "soccer_germany_bundesliga",
    "SA":  "soccer_italy_serie_a",
    "FL1": "soccer_france_ligue_one",
    "DED": "soccer_netherlands_eredivisie",
    "PPL": "soccer_portugal_primeira_liga",
    "CL":  "soccer_uefa_champs_league",
    "EL":  "soccer_uefa_europa_league",
    "ECL": "soccer_uefa_europa_conference_league",
    "BSA": "soccer_brazil_campeonato",
}

@st.cache_data(ttl=60, show_spinner=False)
def fetch_live_odds_api(api_key, sport_key):
    try:
        r = requests.get(
            f"{ODDS_API_BASE}/sports/{sport_key}/odds/",
            params={"apiKey":api_key,"regions":"eu","markets":"h2h,totals",
                    "oddsFormat":"decimal","bookmakers":"bet365,pinnacle,unibet,williamhill"},
            timeout=15)
        return r.json() if r.status_code == 200 else []
    except:
        return []

def get_live_match_odds(api_key, sport_key, hn, an):
    if not api_key or not sport_key:
        return None
    ck = f"liveodds_{sport_key}_{hn[:5]}"
    if ck not in st.session_state:
        st.session_state[ck] = fetch_live_odds_api(api_key, sport_key)
    data = st.session_state.get(ck, [])
    for game in data:
        if not (fuzzy_match_team(game.get("home_team",""), hn) and
                fuzzy_match_team(game.get("away_team",""), an)):
            continue
        bms = game.get("bookmakers", [])
        bm = next((b for b in bms if "bet365" in b.get("key","")), None) or \
             next((b for b in bms if "pinnacle" in b.get("key","")), None) or \
             (bms[0] if bms else None)
        if not bm:
            continue
        res = {"h2h":{}, "totals":{}, "source": bm.get("title","?")}
        for mkt in bm.get("markets",[]):
            if mkt.get("key") == "h2h":
                for oc in mkt.get("outcomes",[]):
                    p = _safe_float(oc.get("price"))
                    n = oc.get("name","")
                    if n == game["home_team"]: res["h2h"]["1"] = round(p,2)
                    elif n == game["away_team"]: res["h2h"]["2"] = round(p,2)
                    else: res["h2h"]["X"] = round(p,2)
            elif mkt.get("key") == "totals":
                for oc in mkt.get("outcomes",[]):
                    pt = _safe_float(oc.get("point"))
                    pr = _safe_float(oc.get("price"))
                    if not pt or not pr: continue
                    dr = "over" if "over" in oc.get("name","").lower() else "under"
                    res["totals"][f"{pt}_{dr}"] = round(pr,2)
        if res["h2h"] or res["totals"]:
            return res
    return None

@st.cache_data(ttl=1800, show_spinner=False)
def fetch_odds_api(api_key, sport_key):
    try:
        r = requests.get(
            f"{ODDS_API_BASE}/sports/{sport_key}/odds/",
            params={
                "apiKey":    api_key,
                "regions":   "eu",
                "markets":   "h2h",
                "oddsFormat":"decimal",
                "bookmakers":"bet365,pinnacle,unibet,williamhill,betfair",
            },
            timeout=15
        )
        if r.status_code == 200:
            remaining = r.headers.get("x-requests-remaining","?")
            if debug: st.caption(f"🐛 OddsAPI {sport_key} → {len(r.json())} maç | Kalan: {remaining}")
            return r.json()
        elif r.status_code == 401:
            st.warning("⚠️ The Odds API key geçersiz — the-odds-api.com'dan kontrol edin")
        elif r.status_code == 422:
            st.warning(f"⚠️ The Odds API: bu lig desteklenmiyor ({sport_key})")
        if debug: st.caption(f"🐛 OddsAPI HTTP {r.status_code}: {r.text[:100]}")
        return []
    except Exception as e:
        if debug: st.caption(f"🐛 OddsAPI error: {e}")
        return []

def get_odds_api_odds(api_key, sel_code, hn, an, match_date):
    sport_key = FD_TO_ODDSAPI_SPORT.get(sel_code)
    if not sport_key:
        return None

    cache_key = f"oddsapi_{sport_key}_{match_date or 'any'}"
    if cache_key not in st.session_state:
        data = fetch_odds_api(api_key, sport_key)
        st.session_state[cache_key] = data
    else:
        data = st.session_state[cache_key]

    if not data:
        return None

    import datetime as _dt
    target_date = None
    if match_date:
        try:
            target_date = _dt.datetime.strptime(match_date, "%Y-%m-%d").date()
        except:
            pass

    for game in data:
        gdate = game.get("commence_time","")[:10]
        if target_date:
            try:
                gd = _dt.datetime.strptime(gdate, "%Y-%m-%d").date()
                if abs((gd - target_date).days) > 1:
                    continue
            except:
                pass

        g_home = game.get("home_team","")
        g_away = game.get("away_team","")
        if not (fuzzy_match_team(g_home, hn) and fuzzy_match_team(g_away, an)):
            continue

        bookmakers = game.get("bookmakers",[])
        def find_bm(name_frag):
            return next((b for b in bookmakers if name_frag.lower() in b.get("key","").lower()), None)

        bm = find_bm("bet365") or find_bm("pinnacle") or find_bm("unibet") or (bookmakers[0] if bookmakers else None)
        if not bm:
            continue

        bm_name = bm.get("title", bm.get("key","?"))
        o1 = ox = o2 = None
        for market in bm.get("markets",[]):
            if market.get("key") != "h2h":
                continue
            for outcome in market.get("outcomes",[]):
                name = outcome.get("name","")
                price = _safe_float(outcome.get("price"))
                if name == g_home:   o1 = price
                elif name == g_away: o2 = price
                else:                ox = price

        if o1 and ox and o2 and o1 > 1.0 and ox > 1.0 and o2 > 1.0:
            if debug: st.caption(f"🐛 OddsAPI [{bm_name}] {g_home} vs {g_away}: 1={o1} X={ox} 2={o2}")
            return {
                "o1": round(o1,2), "ox": round(ox,2), "o2": round(o2,2),
                "o25_ov": None, "o25_un": None,
                "source": f"The Odds API ({bm_name})"
            }

    if debug: st.caption(f"🐛 OddsAPI: {hn} vs {an} bulunamadı ({sport_key})")
    return None

@st.cache_data(ttl=1800, show_spinner=False)
def get_sofascore_odds(hn, an, match_date):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) "
                          "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
            "Accept": "application/json",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.sofascore.com/",
        }
        r = requests.get(
            f"https://api.sofascore.com/api/v1/sport/football/scheduled-events/{match_date}",
            headers=headers, timeout=20
        )
        if r.status_code != 200:
            if debug: st.caption(f"🐛 SofaScore HTTP {r.status_code}")
            return None

        events = r.json().get("events", [])
        if debug: st.caption(f"🐛 SofaScore {match_date}: {len(events)} maç")

        target_id = None
        for ev in events:
            h_name = ev.get("homeTeam",{}).get("name","")
            a_name = ev.get("awayTeam",{}).get("name","")
            if fuzzy_match_team(h_name, hn) and fuzzy_match_team(a_name, an):
                target_id = ev.get("id")
                if debug: st.caption(f"🐛 SofaScore maç bulundu: {h_name} vs {a_name} id={target_id}")
                break

        if not target_id:
            if debug: st.caption(f"🐛 SofaScore: {hn} vs {an} bulunamadı")
            return None

        r2 = requests.get(
            f"https://api.sofascore.com/api/v1/event/{target_id}/odds/1/all",
            headers=headers, timeout=20
        )
        if r2.status_code != 200:
            if debug: st.caption(f"🐛 SofaScore odds HTTP {r2.status_code}")
            return None

        odds_data = r2.json()
        o1 = ox = o2 = None
        markets = odds_data.get("markets", []) or odds_data.get("oddgroups", [])

        for market in markets:
            mname = (market.get("marketName") or market.get("name") or "").lower()
            if "1x2" not in mname and "full time" not in mname and "match winner" not in mname:
                continue
            choices = market.get("choices") or market.get("odds") or []
            for ch in choices:
                name = (ch.get("name") or ch.get("choice") or "").strip()
                val = _safe_float(ch.get("decimalValue") or ch.get("decimal") or ch.get("odd"))
                if not val or val <= 1.0:
                    continue
                if name in ("1", "Home"):    o1 = val
                elif name in ("X", "Draw"): ox = val
                elif name in ("2", "Away"): o2 = val
            if o1 and ox and o2:
                break

        if o1 and ox and o2:
            src = odds_data.get("provider",{}).get("name","SofaScore")
            if debug: st.caption(f"🐛 SofaScore [{src}]: 1={o1} X={ox} 2={o2}")
            return {
                "o1": round(o1,2), "ox": round(ox,2), "o2": round(o2,2),
                "o25_ov": None, "o25_un": None,
                "source": f"SofaScore ({src})"
            }
        if debug: st.caption(f"🐛 SofaScore: oranlar parse edilemedi")
        return None

    except Exception as e:
        if debug: st.caption(f"🐛 SofaScore error: {e}")
        return None

@st.cache_data(ttl=86400, show_spinner=False)
def fetch_season_csv(couk_code, season_code):
    url = f"https://www.football-data.co.uk/mmz4281/{season_code}/{couk_code}.csv"
    try:
        import io, csv
        r = requests.get(url, timeout=15)
        if r.status_code != 200:
            return []
        try:    text = r.content.decode("utf-8")
        except: text = r.content.decode("latin-1")
        rows = list(csv.DictReader(io.StringIO(text)))
        return [row for row in rows
                if row.get("FTHG","").strip() and row.get("HTHG","").strip()]
    except:
        return []

@st.cache_data(ttl=86400, show_spinner=False)
def fetch_all_seasons(couk_code, n_seasons=3):
    all_rows = []
    for sc in SEASON_CODES[:n_seasons]:
        rows = fetch_season_csv(couk_code, sc)
        all_rows.extend(rows)
    return all_rows

def fuzzy_match_team(name1, name2):
    def norm(s):
        s = s.lower().strip()
        replacements = [
            (" fc",""),("fc ",""),(" afc",""),("afc ",""),(" utd",""),
            (" united",""),(" city",""),(" town",""),(" cf",""),(" sc",""),
            (" & hove albion",""),(" albion",""),(" athletic",""),
            (" wanderers",""),(" rovers",""),(" hotspur",""),
            ("manchester ","man "),("tottenham","spurs"),
            ("wolverhampton","wolves"),("leicester","leicester"),
            ("nottingham","nott'm"),("nott'm","notm"),
            ("paris saint-germain","psg"),("paris sg","psg"),
            ("inter milan","inter"),("ac milan","milan"),
            ("atletico","atl"),("real madrid","real"),
            ("bayer leverkusen","leverkusen"),
        ]
        for old, new in replacements:
            s = s.replace(old, new)
        return s.strip()

    n1, n2 = norm(name1), norm(name2)
    if n1 == n2: return True
    if len(n1) >= 4 and n1 in n2: return True
    if len(n2) >= 4 and n2 in n1: return True
    if len(n1) >= 4 and len(n2) >= 4 and n1[:4] == n2[:4]: return True
    w1 = set(n1.split())
    w2 = set(n2.split())
    common = w1 & w2
    if common and max(len(w) for w in common) >= 4: return True
    return False

def match_odds_to_fixture(fixtures_odds, h_name, a_name):
    for key, info in fixtures_odds.items():
        fh, fa = info["home"], info["away"]
        if fuzzy_match_team(fh, h_name) and fuzzy_match_team(fa, a_name):
            return info
    return None

def auto_pattern_search(couk_code, o1, ox, o2, n_seasons=3, tol=0.25):
    all_rows = fetch_all_seasons(couk_code, n_seasons)
    if not all_rows:
        return None, 0
    matched = find_similar_odds_matches(all_rows, o1, ox, o2, tol=tol)
    if not matched:
        return None, len(all_rows)
    pattern = analyze_score_patterns(matched, o1, ox, o2)
    return pattern, len(all_rows)

def _safe_float(val, default=None):
    try:
        return float(str(val).strip())
    except:
        return default

def find_similar_odds_matches(rows, o1_target, ox_target, o2_target, tol=0.25):
    matched = []
    for row in rows:
        h_odds = _safe_float(row.get("B365H") or row.get("AvgH") or row.get("PSH") or row.get("IWH") or row.get("VCH"))
        d_odds = _safe_float(row.get("B365D") or row.get("AvgD") or row.get("PSD") or row.get("IWD") or row.get("VCD"))
        a_odds = _safe_float(row.get("B365A") or row.get("AvgA") or row.get("PSA") or row.get("IWA") or row.get("VCA"))

        if not h_odds or not d_odds or not a_odds:
            continue
        if h_odds <= 1.0 or d_odds <= 1.0 or a_odds <= 1.0:
            continue

        if (abs(h_odds - float(o1_target)) <= tol and
            abs(d_odds - float(ox_target)) <= tol and
            abs(a_odds - float(o2_target)) <= tol):
            row["_b365h"] = h_odds
            row["_b365d"] = d_odds
            row["_b365a"] = a_odds
            matched.append(row)

    return matched

def analyze_score_patterns(matched_rows, o1, ox, o2):
    if not matched_rows:
        return None

    from collections import Counter, defaultdict

    n = len(matched_rows)
    ms_scores  = Counter()
    ht_scores  = Counter()
    results    = Counter()
    ht_results = Counter()
    turnovers  = defaultdict(int)

    for row in matched_rows:
        try:
            fthg = int(float(row.get("FTHG","0")))
            ftag = int(float(row.get("FTAG","0")))
            hthg = int(float(row.get("HTHG","0")))
            htag = int(float(row.get("HTAG","0")))
        except:
            continue

        ms_scores[f"{fthg}-{ftag}"] += 1
        ht_scores[f"{hthg}-{htag}"] += 1

        if fthg > ftag:   results["1"] += 1
        elif fthg < ftag: results["2"] += 1
        else:             results["X"] += 1

        if hthg > htag:   ht_results["1"] += 1
        elif hthg < htag: ht_results["2"] += 1
        else:             ht_results["X"] += 1

        iy_r = "1" if hthg>htag else ("2" if hthg<htag else "X")
        ms_r = "1" if fthg>ftag else ("2" if fthg<ftag else "X")
        combo = f"{iy_r}/{ms_r}"
        turnovers[combo] += 1

    def pcts(counter, total):
        return {k: round(v/total*100, 1) for k,v in counter.most_common(10)}

    ms_top  = pcts(ms_scores,  n)
    ht_top  = pcts(ht_scores,  n)
    res_pct = {k: round(v/n*100,1) for k,v in results.items()}
    htr_pct = {k: round(v/n*100,1) for k,v in ht_results.items()}
    trn_pct = {k: round(v/n*100,1) for k,v in sorted(turnovers.items(), key=lambda x:-x[1])[:9]}

    notable = []
    for combo, pct in trn_pct.items():
        iy_p, ms_p = combo.split("/")
        if iy_p != ms_p and pct >= 8:
            notable.append((combo, pct))

    try:
        imp_h = round(1/float(o1)/(1/float(o1)+1/float(ox)+1/float(o2))*100, 1)
    except:
        imp_h = 0

    upsets = round((results.get("2",0) + results.get("X",0)*0.5) / n * 100, 1) if n > 0 else 0

    return {
        "n": n,
        "ms_top":   ms_top,
        "ht_top":   ht_top,
        "res_pct":  res_pct,
        "htr_pct":  htr_pct,
        "trn_pct":  trn_pct,
        "notable_turnovers": notable,
        "upset_rate": upsets,
        "imp_h": imp_h,
    }

def render_pattern_panel(pattern, o1, ox, o2, h, a, odds_source="football-data.co.uk"):
    if not pattern:
        st.info("Bu oran aralığı için yeterli geçmiş maç bulunamadı.")
        return

    n   = pattern["n"]
    res = pattern["res_pct"]
    htr = pattern["htr_pct"]
    mono = "JetBrains Mono,monospace"

    is_b365 = "bet365" in odds_source.lower() or "Bet365" in odds_source
    src_cls  = "bet365" if is_b365 else ""
    src_icon = "🔵 Bet365" if is_b365 else f"📊 {odds_source[:20]}"

    header_html = (
        f'<div class="pattern-wrap">'
        f'<div class="pattern-header">'
        f'<span class="pattern-badge b365">ORAN PATTERN</span>'
        f'<span class="pattern-title">Benzer Bet365 Oranlarında Geçmiş Maçlar</span>'
        f'<span class="pattern-n">{n} maç analiz edildi</span>'
        f'</div>'
        f'<div class="pattern-odds-row">'
        f'<div class="pat-odd-box home"><span class="pat-odd-lbl">{h[:12]}</span>'
        f'<span class="pat-odd-val">{o1}</span></div>'
        f'<span class="pat-odd-sep">·</span>'
        f'<div class="pat-odd-box draw"><span class="pat-odd-lbl">Beraberlik</span>'
        f'<span class="pat-odd-val">{ox}</span></div>'
        f'<span class="pat-odd-sep">·</span>'
        f'<div class="pat-odd-box away"><span class="pat-odd-lbl">{a[:12]}</span>'
        f'<span class="pat-odd-val">{o2}</span></div>'
        f'<span class="pat-src {src_cls}">{src_icon} · ±0.25 tolerans</span>'
        f'</div>'
    )

    def res_trio(res_dict, home_lbl, away_lbl, prefix=""):
        total_n = n
        return (
            f'<div class="pat-res-trio">'
            f'<div class="pat-res-box pat-home">'
            f'<div class="prb-lbl">{prefix}{home_lbl[:10]}</div>'
            f'<div class="prb-big">%{res_dict.get("1",0)}</div>'
            f'<div class="prb-cnt">{round(res_dict.get("1",0)*total_n/100)} maç</div>'
            f'</div>'
            f'<div class="pat-res-box pat-draw">'
            f'<div class="prb-lbl">{prefix}Beraberlik</div>'
            f'<div class="prb-big">%{res_dict.get("X",0)}</div>'
            f'<div class="prb-cnt">{round(res_dict.get("X",0)*total_n/100)} maç</div>'
            f'</div>'
            f'<div class="pat-res-box pat-away">'
            f'<div class="prb-lbl">{prefix}{away_lbl[:10]}</div>'
            f'<div class="prb-big">%{res_dict.get("2",0)}</div>'
            f'<div class="prb-cnt">{round(res_dict.get("2",0)*total_n/100)} maç</div>'
            f'</div>'
            f'</div>'
        )

    def skor_bar_list(scores_dict, fill_color):
        if not scores_dict:
            return '<div style="font-size:.68rem;color:#4a6880">Veri yetersiz</div>'
        html = '<div class="skor-bar-list">'
        max_pct = max(scores_dict.values()) if scores_dict else 1
        for sc, pct in list(scores_dict.items())[:8]:
            bar_w = max(3, int(pct / max_pct * 100))
            cnt = max(1, round(pct * n / 100))
            html += (
                f'<div class="skor-bar-row">'
                f'<div class="skor-bar-key">{sc}</div>'
                f'<div class="skor-bar-track">'
                f'<div class="skor-bar-fill" style="width:{bar_w}%;background:{fill_color}"></div>'
                f'</div>'
                f'<div class="skor-bar-pct">%{pct}</div>'
                f'<div class="skor-bar-cnt">({cnt})</div>'
                f'</div>'
            )
        html += '</div>'
        return html

    def combo_grid_html(combos_dict):
        combo_desc = {
            "1/1": "Ev önde kalır","X/1": "Ber→Ev kazanır","2/1": "DEP→EV DÖNÜŞ",
            "1/X": "Ev→Beraberlik","X/X": "Her yarı ber.","2/X": "Dep→Beraberlik",
            "1/2": "EV→DEP DÖNÜŞ","X/2": "Ber→Dep kazanır","2/2": "Dep önde kalır",
        }
        html = '<div class="pat-combo-grid">'
        for k, pct in sorted(combos_dict.items(), key=lambda x: -x[1]):
            iy_r, ms_r = k.split("/")
            is_t = (iy_r != ms_r)
            cls  = "pat-combo-cell donus" if is_t and pct >= 8 else "pat-combo-cell"
            cnt  = round(pct * n / 100)
            html += (
                f'<div class="{cls}">'
                f'<div class="pcc-key">{k}</div>'
                f'<div class="pcc-pct">%{pct}</div>'
                f'<div class="pcc-cnt">{combo_desc.get(k,"")} ({cnt})</div>'
                f'</div>'
            )
        html += '</div>'
        return html

    notable_html = ""
    if pattern.get("notable_turnovers"):
        notable_html = '<div class="pat-sec"><div class="pat-sec-lbl">⚡ Öne Çıkan Dönüşler</div>'
        for combo, pct in pattern["notable_turnovers"]:
            cnt = round(pct * n / 100)
            label = "İY Dep → MS Ev Kazandı" if combo == "2/1" else \
                    "İY Ev → MS Dep Kazandı" if combo == "1/2" else \
                    f"Dönüş {combo}"
            notable_html += (
                f'<div class="notable-row">'
                f'<div class="notable-combo">{combo}</div>'
                f'<div class="notable-text">{label} — bu oran aralığında</div>'
                f'<div class="notable-pct">%{pct}</div>'
                f'<div class="notable-cnt">({cnt}/{n})</div>'
                f'</div>'
            )
        notable_html += '</div>'

    body_html = (
        f'{header_html}'
        f'<div class="pattern-body">'

        f'<div class="pat-sec">'
        f'<div class="pat-sec-lbl">Maç Sonu Sonuçları — Bu oran aralığında {n} maçta</div>'
        + res_trio(res, h, a, prefix="MS ") +
        f'</div>'

        f'<div class="pat-sec">'
        f'<div class="pat-sec-lbl">İlk Yarı Sonuçları — Aynı {n} maçta</div>'
        + res_trio(htr, h, a, prefix="İY ") +
        f'</div>'

        f'<div class="pat-sec">'
        f'<div class="pat-sec-lbl">İY / MS Kombinasyonları — Dönüş Analizi (turuncu = dönüş)</div>'
        + combo_grid_html(pattern["trn_pct"]) +
        f'</div>'

        + notable_html +

        f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:14px">'
        f'<div class="pat-sec">'
        f'<div class="pat-sec-lbl">Maç Sonu Skor Dağılımı</div>'
        + skor_bar_list(pattern["ms_top"], "#3ecf7a") +
        f'</div>'
        f'<div class="pat-sec">'
        f'<div class="pat-sec-lbl">İlk Yarı Skor Dağılımı</div>'
        + skor_bar_list(pattern["ht_top"], "#a78bfa") +
        f'</div></div>'

        f'<div style="font-size:.58rem;color:#2a3a4a;margin-top:8px;text-align:right;padding-top:6px;border-top:1px solid #1c2e44">'
        f'Sürpriz oranı (favori kaybet/berabere): %{pattern["upset_rate"]}'
        f'</div>'

        f'</div></div>'
    )

    st.markdown(body_html, unsafe_allow_html=True)

def odds_implied_probs(o1, ox, o2):
    try:
        f1, fx, f2 = 1/float(o1), 1/float(ox), 1/float(o2)
        margin = f1 + fx + f2
        return {
            "p1":  round(f1/margin*100, 1),
            "px":  round(fx/margin*100, 1),
            "p2":  round(f2/margin*100, 1),
            "vig": round((margin - 1)*100, 2),
        }
    except:
        return None

def odds_value_score(model_pct, implied_pct):
    if not implied_pct or implied_pct == 0: return None
    edge = model_pct - implied_pct
    kelly = edge / (100 - implied_pct) if edge > 0 else 0
    return {"edge": round(edge, 1), "kelly": round(kelly*100, 1)}

def odds_risk_level(o1, ox, o2):
    try:
        vals = [float(o1), float(ox), float(o2)]
        lo = min(vals)
        if lo < 1.40: return "DÜŞÜK", "Belirgin favori (oran < 1.40)"
        if lo < 1.80: return "ORTA-DÜŞÜK", "Hafif favori"
        if lo < 2.20: return "ORTA", "Dengeli maç"
        return "YÜKSEK", "Açık maç — her sonuç mümkün"
    except:
        return "BİLİNMİYOR", "Oran verisi yok"

def odds_deviation(sources):
    valid = [v for v in sources if v is not None]
    if len(valid) < 2: return None
    return round(max(valid) - min(valid), 3)

def estimate_odds_with_groq(h, a, stats, hf, af, h2h, h_stand, a_stand):
    fv = lambda d,k,dv=0: d.get(k,dv) if d else dv
    hs = h_stand or {}; as_ = a_stand or {}

    hxg_real = fv(hf,'avg_gf',1.2)
    axg_real = fv(af,'avg_gf',1.0)

    mini_prompt = f"""Sen bir profesyonel futbol bahis analistisin.
Bu maç için Bet365 tarzı gerçekçi piyasa oranı tahmin et.
SADECE 3 satır yaz, başka HİÇBİR ŞEY yazma.

MAÇ: {h} (Ev) vs {a} (Deplasman)
Poisson model: 1=%{stats['p1']} X=%{stats['px']} 2=%{stats['p2']}
xG tahmini: {h}={hxg_real} gol/maç | {a}={axg_real} gol/maç
{h} form: {fv(hf,'form_str','?')} son5={fv(hf,'pts5',0)}/15 puan
{a} form: {fv(af,'form_str','?')} son5={fv(af,'pts5',0)}/15 puan
Lig sırası: {h}={hs.get('position','?')} | {a}={as_.get('position','?')}

Cevap SADECE şu 3 satır:
1: [oran]
X: [oran]
2: [oran]"""

    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"},
            json={"model": "llama-3.1-8b-instant",
                  "messages": [{"role": "user", "content": mini_prompt}],
                  "temperature": 0.05, "max_tokens": 40},
            timeout=30
        )
        r.raise_for_status()
        text = r.json()["choices"][0]["message"]["content"].strip()
        import re
        o1 = ox = o2 = None
        for line in text.splitlines():
            line = line.strip()
            m1 = re.match(r'^1\s*:\s*([0-9]+\.?[0-9]*)$', line)
            mx = re.match(r'^X\s*:\s*([0-9]+\.?[0-9]*)$', line)
            m2 = re.match(r'^2\s*:\s*([0-9]+\.?[0-9]*)$', line)
            if m1: o1 = round(float(m1.group(1)), 2)
            if mx: ox = round(float(mx.group(1)), 2)
            if m2: o2 = round(float(m2.group(1)), 2)
        if o1 and ox and o2:
            if 1.05 <= o1 <= 25 and 1.05 <= ox <= 25 and 1.05 <= o2 <= 25:
                implied_sum = 1/o1 + 1/ox + 1/o2
                if 1.02 <= implied_sum <= 1.20:
                    return {"o1": o1, "ox": ox, "o2": o2,
                            "o25_ov": None, "o25_un": None,
                            "source": "groq-tahmin"}
    except:
        pass

    try:
        p1 = max(5, stats["p1"]) / 100
        px = max(5, stats["px"]) / 100
        p2 = max(5, stats["p2"]) / 100
        total = p1 + px + p2
        p1 /= total; px /= total; p2 /= total
        margin = 1.08
        o1_calc = round(1 / p1 / margin, 2)
        ox_calc = round(1 / px / margin, 2)
        o2_calc = round(1 / p2 / margin, 2)
        if 1.05 <= o1_calc <= 20 and 1.05 <= ox_calc <= 20 and 1.05 <= o2_calc <= 20:
            return {
                "o1": o1_calc, "ox": ox_calc, "o2": o2_calc,
                "o25_ov": None, "o25_un": None,
                "source": "model-tahmin"
            }
    except:
        pass
    return None

def analyze_odds(o1, ox, o2, model_stats, h_name, a_name):
    if not o1 or not ox or not o2:
        return None

    imp = odds_implied_probs(o1, ox, o2)
    if not imp:
        return None

    risk_lv, risk_why = odds_risk_level(o1, ox, o2)

    v1 = odds_value_score(model_stats["p1"], imp["p1"])
    vx = odds_value_score(model_stats["px"], imp["px"])
    v2 = odds_value_score(model_stats["p2"], imp["p2"])

    values = [
        ("1", h_name, v1, float(o1)),
        ("X", "Beraberlik", vx, float(ox)),
        ("2", a_name, v2, float(o2)),
    ]
    best_value = max(
        [(k, n, v, o) for k, n, v, o in values if v and v["edge"] > 0],
        key=lambda x: x[2]["edge"],
        default=None
    )

    try:
        o1f, oxf, o2f = float(o1), float(ox), float(o2)
        if o1f < o2f and o1f < oxf:
            fav, fav_odd = "home", o1f
        elif o2f < o1f and o2f < oxf:
            fav, fav_odd = "away", o2f
        else:
            fav, fav_odd = "draw", oxf
    except:
        fav, fav_odd = "unknown", 0

    try:
        underdog_odd = max(float(o1), float(o2))
        upset_risk = "YÜKSEK" if underdog_odd < 3.5 else "ORTA" if underdog_odd < 5.0 else "DÜŞÜK"
    except:
        upset_risk = "BİLİNMİYOR"

    movement_signals = []
    try:
        if o1f < 1.60 and model_stats["p1"] < imp["p1"] - 5:
            movement_signals.append(f"⚠️ Piyasa {h_name}'i %{imp['p1']} gösteriyor ama model %{model_stats['p1']} — aşırı fiyatlanmış")
        if o2f < 1.80 and model_stats["p2"] < imp["p2"] - 5:
            movement_signals.append(f"⚠️ Piyasa {a_name}'i %{imp['p2']} gösteriyor ama model %{model_stats['p2']} — aşırı fiyatlanmış")
        if abs(model_stats["p1"] - imp["p1"]) < 3 and abs(model_stats["p2"] - imp["p2"]) < 3:
            movement_signals.append("✅ Model ve piyasa uyumlu — güvenilir fiyatlama")
    except:
        pass

    signals = []
    try:
        if o1f < 1.50 and model_stats["p1"] < 55:
            signals.append(f"🔴 {h_name} aşırı düşük oran ({o1f}) ama model sadece %{model_stats['p1']} — düşük value")
        if o1f < 1.50 and model_stats["p1"] >= 60:
            signals.append(f"🟢 {h_name} favorilik modelle örtüşüyor (%{model_stats['p1']}) — güvenilir")
        if 2.40 <= o2f <= 3.80 and model_stats["p2"] >= imp["p2"] + 6:
            signals.append(f"💎 {a_name} {o2f} oranda VALUE — model %{model_stats['p2']} ama piyasa %{imp['p2']}")
        if 2.40 <= o1f <= 3.80 and model_stats["p1"] >= imp["p1"] + 6:
            signals.append(f"💎 {h_name} {o1f} oranda VALUE — model %{model_stats['p1']} ama piyasa %{imp['p1']}")
        if oxf < 3.20 and model_stats["px"] >= imp["px"] + 8:
            signals.append(f"💎 Beraberlik {oxf} oranda VALUE — model %{model_stats['px']}")
        if o1f > 4.0 and o2f > 4.0:
            signals.append("⚡ Her iki takım da yüksek oranlı — tamamen açık maç")
    except:
        pass

    return {
        "o1": o1, "ox": ox, "o2": o2,
        "imp": imp,
        "risk_level": risk_lv,
        "risk_why": risk_why,
        "v1": v1, "vx": vx, "v2": v2,
        "best_value": best_value,
        "fav": fav, "fav_odd": fav_odd,
        "upset_risk": upset_risk,
        "signals": signals,
        "movement": movement_signals,
    }

def odds_to_prompt_segment(oa, h, a):
    if not oa: return ""
    imp = oa["imp"]
    bv = oa["best_value"]
    bv_str = f"VALUE: {bv[0]}({bv[1]}) oran={bv[3]} edge=+%{bv[2]['edge']}" if bv else "Belirgin value yok"
    sigs = " | ".join(oa["signals"][:3]) if oa["signals"] else "Normal oran yapısı"
    return (f"ORANLAR: 1={oa['o1']} X={oa['ox']} 2={oa['o2']} | "
            f"ZIMNİ: 1=%{imp['p1']} X=%{imp['px']} 2=%{imp['p2']} Vig=%{imp['vig']} | "
            f"RİSK:{oa['risk_level']} | {bv_str} | SİNYAL:{sigs}")

def render_odds_panel(oa, h, a, model_stats):
    if not oa:
        return

    imp   = oa["imp"]
    mono  = "JetBrains Mono,monospace"
    _src  = oa.get("_source", "")
    _is_est = "groq" in _src.lower() or "model" in _src.lower()

    if _is_est:
        st.warning(f"⚠️ **Gerçek oran bulunamadı** — `{_src}` kullanıldı. "
                   f"Gerçek oran için: **The Odds API** key girin (the-odds-api.com, ücretsiz 500/ay) "
                   f"veya **Manuel Oran Giriş**'i kullanın.")
    elif "Bet365" in _src or "The Odds API" in _src:
        st.success(f"✅ Gerçek oran: **{_src}**")
    elif "SofaScore" in _src:
        st.info(f"📊 Oran kaynağı: **{_src}**")
    elif "football-data" in _src:
        st.info(f"📊 Oran kaynağı: **{_src}**")
    elif _src == "manuel":
        st.info("✏️ Oranlar: **Manuel girildi**")

    risk_color = {"DÜŞÜK":"#3ecf7a","ORTA-DÜŞÜK":"#86efac","ORTA":"#f5a623",
                  "YÜKSEK":"#f87171","BİLİNMİYOR":"#4a6880"}.get(oa["risk_level"],"#4a6880")

    def oran_box(label, odd, model_pct, imp_pct, val_obj, bg, border, color):
        edge_html = ""
        if val_obj and val_obj["edge"] > 0:
            edge_html = (f'<div style="font-size:.6rem;color:#34d399;margin-top:2px;font-weight:700">'
                         f'+%{val_obj["edge"]} VALUE</div>')
        elif val_obj and val_obj["edge"] < -3:
            edge_html = (f'<div style="font-size:.6rem;color:#f87171;margin-top:2px">'
                         f'%{val_obj["edge"]} düşük</div>')
        return (
            f'<div style="background:{bg};border:1px solid {border};border-radius:10px;'
            f'padding:10px 8px;text-align:center">'
            f'<div style="font-size:.6rem;color:#3a5570;text-transform:uppercase;'
            f'letter-spacing:.08em;margin-bottom:4px">{label}</div>'
            f'<div style="font-size:1.6rem;font-weight:800;color:{color};font-family:{mono}">{odd}</div>'
            f'<div style="font-size:.65rem;color:#2a4060;margin-top:4px">Piyasa %{imp_pct}</div>'
            f'<div style="font-size:.65rem;color:#3a5570">Model %{model_pct}</div>'
            f'{edge_html}'
            f'</div>'
        )

    h_bg = "#061d0f" if oa["fav"]=="home" else "#0a1628"
    a_bg = "#1a0505" if oa["fav"]=="away" else "#0a1628"
    x_bg = "#140e00" if oa["fav"]=="draw" else "#0a1628"

    box1 = oran_box(h[:14], oa["o1"], model_stats["p1"], imp["p1"], oa["v1"],
                    h_bg, "#1d4ed8", "#60a5fa")
    boxx = oran_box("Beraberlik", oa["ox"], model_stats["px"], imp["px"], oa["vx"],
                    x_bg, "#854d0e", "#fbbf24")
    box2 = oran_box(a[:14], oa["o2"], model_stats["p2"], imp["p2"], oa["v2"],
                    a_bg, "#991b1b", "#f87171")

    signals_html = ""
    for sig in oa["signals"]:
        signals_html += (f'<div style="font-size:.73rem;color:#c0cfe0;padding:6px 10px;'
                         f'margin:4px 0;background:#0a1628;border-left:3px solid #1e3a5f;'
                         f'border-radius:0 6px 6px 0">{sig}</div>')

    movement_html = ""
    for mv in oa["movement"]:
        movement_html += (f'<div style="font-size:.72rem;color:#94a3b8;padding:4px 10px;'
                          f'margin:3px 0;background:#060d1c;border-left:2px solid #2a4060;'
                          f'border-radius:0 4px 4px 0">{mv}</div>')

    vig_color = "#34d399" if imp["vig"] < 5 else "#fbbf24" if imp["vig"] < 8 else "#f87171"

    st.markdown(
        f'<div style="padding:1.2rem 1.8rem;border-bottom:1px solid #0a1e30">'
        f'<div class="dp-section-title">💰 ORAN ANALİZİ — Model vs Piyasa Karşılaştırması</div>'
        f'<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin:10px 0">'
        f'{box1}{boxx}{box2}'
        f'</div>'
        f'<div style="display:flex;gap:12px;margin:8px 0;flex-wrap:wrap">'
        f'<span style="font-size:.72rem;background:#0a1628;border:1px solid #0f2a45;'
        f'border-radius:6px;padding:3px 10px;color:{risk_color}">⚡ Risk: {oa["risk_level"]}</span>'
        f'<span style="font-size:.72rem;background:#0a1628;border:1px solid #0f2a45;'
        f'border-radius:6px;padding:3px 10px;color:{vig_color}">Vig: %{imp["vig"]}</span>'
        f'<span style="font-size:.72rem;background:#0a1628;border:1px solid #0f2a45;'
        f'border-radius:6px;padding:3px 10px;color:#6b7280">Upset Riski: {oa["upset_risk"]}</span>'
        f'</div>'
        + (f'<div style="margin-top:8px">{signals_html}</div>' if signals_html else '')
        + (f'<div style="margin-top:6px">{movement_html}</div>' if movement_html else '')
        + f'</div>',
        unsafe_allow_html=True
    )

# ══════════════════════════════════════════════════════════════════
# GROQ — MAÇA ÖZEL PROMPT
# ══════════════════════════════════════════════════════════════════

def build_prompt(h, a, hf, af, h2h, hxg, axg, h_htxg, a_htxg,
                 stats, h_stand, a_stand, h_sc, a_sc, top_ms, top_ht,
                 odds_analysis=None):
    fv = lambda d,k,dv=0: d.get(k,dv) if d else dv
    hs = h_stand or {}; as_ = a_stand or {}

    chars = []
    diff = round(hxg - axg, 2)
    if diff > 0.6:    chars.append(f"EV_FAVORİ xG+{diff}")
    elif diff < -0.6: chars.append(f"DEP_FAVORİ xG+{abs(diff)}")
    else:             chars.append(f"DENGE xG={hxg}vs{axg}")
    hp=fv(hf,"pts5"); ap=fv(af,"pts5")
    if hp>=12: chars.append(f"{h}_SÜPER_FORM {hp}/15")
    elif hp<=4: chars.append(f"{h}_KÖTÜ_FORM {hp}/15")
    if ap>=12: chars.append(f"{a}_SÜPER_FORM {ap}/15")
    elif ap<=4: chars.append(f"{a}_KÖTÜ_FORM {ap}/15")
    if fv(hf,"st_pct",55)>=62: chars.append(f"{h}_2Y_AĞIR(%{fv(hf,'st_pct',55)})")
    if fv(af,"st_pct",55)>=62: chars.append(f"{a}_2Y_AĞIR(%{fv(af,'st_pct',55)})")
    if h2h.get("rev21_pct",0)>=25: chars.append(f"H2H_2/1_YÜKSEK=%{h2h['rev21_pct']}")
    if h2h.get("rev12_pct",0)>=25: chars.append(f"H2H_1/2_YÜKSEK=%{h2h['rev12_pct']}")
    if fv(hf,"cs",0)>=3: chars.append(f"{h}_SAĞLAM_DEF {fv(hf,'cs')}/{fv(hf,'n')}CS")
    if fv(af,"avg_gc",0)>=2.0: chars.append(f"{a}_ZAYIF_DEF {fv(af,'avg_gc')}yenen")
    if hs.get("position",10)>=16: chars.append(f"{h}_DÜŞME_ZONU sıra:{hs.get('position')}")
    if as_.get("position",10)>=16: chars.append(f"{a}_DÜŞME_ZONU sıra:{as_.get('position')}")

    h_sc_str = f"{h_sc.get('name','?')}({h_sc.get('goals',0)}g)" if h_sc else "Veri yok"
    a_sc_str = f"{a_sc.get('name','?')}({a_sc.get('goals',0)}g)" if a_sc else "Veri yok"

    oran_seg = odds_to_prompt_segment(odds_analysis, h, a) if odds_analysis else "Oran verisi girilmedi"

    iy_11 = next((round(v,1) for (hg,ag),v in top_ht if hg==1 and ag==1), 0)
    iy_10 = next((round(v,1) for (hg,ag),v in top_ht if hg==1 and ag==0), 0)
    iy_01 = next((round(v,1) for (hg,ag),v in top_ht if hg==0 and ag==1), 0)
    iy_00 = next((round(v,1) for (hg,ag),v in top_ht if hg==0 and ag==0), 0)
    iy_21 = next((round(v,1) for (hg,ag),v in top_ht if hg==2 and ag==1), 0)
    iy_12 = next((round(v,1) for (hg,ag),v in top_ht if hg==1 and ag==2), 0)
    iy_22 = next((round(v,1) for (hg,ag),v in top_ht if hg==2 and ag==2), 0)
    iy_20 = next((round(v,1) for (hg,ag),v in top_ht if hg==2 and ag==0), 0)
    iy_02 = next((round(v,1) for (hg,ag),v in top_ht if hg==0 and ag==2), 0)

    ms_10 = next((round(v,1) for (hg,ag),v in top_ms if hg==1 and ag==0), 0)
    ms_20 = next((round(v,1) for (hg,ag),v in top_ms if hg==2 and ag==0), 0)
    ms_21 = next((round(v,1) for (hg,ag),v in top_ms if hg==2 and ag==1), 0)
    ms_11 = next((round(v,1) for (hg,ag),v in top_ms if hg==1 and ag==1), 0)
    ms_01 = next((round(v,1) for (hg,ag),v in top_ms if hg==0 and ag==1), 0)
    ms_02 = next((round(v,1) for (hg,ag),v in top_ms if hg==0 and ag==2), 0)
    ms_12 = next((round(v,1) for (hg,ag),v in top_ms if hg==1 and ag==2), 0)
    ms_22 = next((round(v,1) for (hg,ag),v in top_ms if hg==2 and ag==2), 0)
    ms_30 = next((round(v,1) for (hg,ag),v in top_ms if hg==3 and ag==0), 0)
    ms_31 = next((round(v,1) for (hg,ag),v in top_ms if hg==3 and ag==1), 0)

    prompt = f"""Sen bir Profesyonel Betting Analyst + Pattern Engine olarak çalışıyorsun.
Türkçe yaz. Takım isimlerini her zaman kullan. Jenerik/genel cümleler yasak — her cümle bu maça özgü olmalı.
Veri yoksa "veri yetersiz" yaz. İstatistik ile öneri çelişmeyecek.

═══════════════════════════════════════
MAÇ VERİSİ (Ham Input)
═══════════════════════════════════════
KARAKTER: {" | ".join(chars)}
MAÇ: {h} (Ev) vs {a} (Deplasman)

{h} PUAN DURUMU: Sıra:{hs.get('position','?')} | {hs.get('won','?')}G-{hs.get('draw','?')}B-{hs.get('lost','?')}M | GolFarkı:{hs.get('goalDifference',0):+d} | Puan:{hs.get('points','?')}
{a} PUAN DURUMU: Sıra:{as_.get('position','?')} | {as_.get('won','?')}G-{as_.get('draw','?')}B-{as_.get('lost','?')}M | GolFarkı:{as_.get('goalDifference',0):+d} | Puan:{as_.get('points','?')}
GOLCÜLER: {h}→{h_sc_str} | {a}→{a_sc_str}

{h} FORM ({fv(hf,'n',0)} maç): {fv(hf,'form_str','?')} | Son5:{fv(hf,'pts5')}/15
  Gol Ort: {fv(hf,'avg_gf')} attı/{fv(hf,'avg_gc')} yedi | İç Saha: {fv(hf,'h_avg_gf')}/{fv(hf,'h_avg_gc')} ({fv(hf,'h_n')} maç)
  İY Gol: {fv(hf,'ht_avg_gf')} attı/{fv(hf,'ht_avg_gc')} yedi | 2Y Gol: {fv(hf,'st_avg_gf')} attı/{fv(hf,'st_avg_gc')} yedi
  Gol Zamanı: %{fv(hf,'ht_pct',45)} İlk Yarı / %{fv(hf,'st_pct',55)} İkinci Yarı
  KG VAR: {fv(hf,'btts')}/{fv(hf,'n')} | 2.5 Üst: {fv(hf,'o25')}/{fv(hf,'n')} | 3.5 Üst: {fv(hf,'o35')}/{fv(hf,'n')} | CS: {fv(hf,'cs')}/{fv(hf,'n')}
  Son MS Skorları: {" ".join((hf.get('ms_scores',[]) if hf else [])[:5])}
  Son İY Skorları: {" ".join((hf.get('ht_scores',[]) if hf else [])[:5])}
  Seri: {fv(hf,'streak','?')}

{a} FORM ({fv(af,'n',0)} maç): {fv(af,'form_str','?')} | Son5:{fv(af,'pts5')}/15
  Gol Ort: {fv(af,'avg_gf')} attı/{fv(af,'avg_gc')} yedi | Deplasman: {fv(af,'a_avg_gf')}/{fv(af,'a_avg_gc')} ({fv(af,'a_n')} maç)
  İY Gol: {fv(af,'ht_avg_gf')} attı/{fv(af,'ht_avg_gc')} yedi | 2Y Gol: {fv(af,'st_avg_gf')} attı/{fv(af,'st_avg_gc')} yedi
  Gol Zamanı: %{fv(af,'ht_pct',45)} İlk Yarı / %{fv(af,'st_pct',55)} İkinci Yarı
  KG VAR: {fv(af,'btts')}/{fv(af,'n')} | 2.5 Üst: {fv(af,'o25')}/{fv(af,'n')} | 3.5 Üst: {fv(af,'o35')}/{fv(af,'n')} | CS: {fv(af,'cs')}/{fv(af,'n')}
  Son MS Skorları: {" ".join((af.get('ms_scores',[]) if af else [])[:5])}
  Son İY Skorları: {" ".join((af.get('ht_scores',[]) if af else [])[:5])}
  Seri: {fv(af,'streak','?')}

H2H ({h2h.get('n',0)} maç): {h} {h2h.get('hw',0)}G-{h2h.get('dr',0)}B-{h2h.get('aw',0)}M
  İY Sonuçları: {h} {h2h.get('ht_hw',0)}G-{h2h.get('ht_dr',0)}B-{h2h.get('ht_aw',0)}M
  H2H MS Skorları: {" ".join(h2h.get('ms_scores',[])[:5])}
  H2H İY Skorları: {" ".join(h2h.get('ht_scores',[])[:5])}
  Gol/Maç: {h2h.get('avg_goals',0)} | 2.5 Üst: %{h2h.get('o25_pct',0)} | KG VAR: %{h2h.get('btts_pct',0)}
  DÖNÜŞ → 2/1: {h2h.get('rev21',0)}/{h2h.get('n',0)} maç (%{h2h.get('rev21_pct',0)}) | 1/2: {h2h.get('rev12',0)}/{h2h.get('n',0)} maç (%{h2h.get('rev12_pct',0)})
  X→1: {h2h.get('revx1',0)}/{h2h.get('n',0)} (%{h2h.get('revx1_pct',0)}) | X→2: {h2h.get('revx2',0)}/{h2h.get('n',0)} (%{h2h.get('revx2_pct',0)})

{oran_seg}

POISSON MODEL:
  xG: {h}={hxg}(İY:{h_htxg}) | {a}={axg}(İY:{a_htxg})
  MS Olasılık: 1=%{stats['p1']} X=%{stats['px']} 2=%{stats['p2']}
  İY Olasılık: 1=%{stats['iy1']} X=%{stats['iyx']} 2=%{stats['iy2']}
  Model Dönüş: 2/1=%{stats['rev21']}% | 1/2=%{stats['rev12']}%
  KG=%{stats['kg']}% | 2.5Üst=%{stats['u25']}% | 2.5Alt=%{stats['alt25']}% | 3.5Üst=%{stats['u35']}%
  Top İY/MS Kombolar: {" ".join(f"{k}={round(v,1)}%" for k,v in stats['combos'][:6])}

İY SKOR OLASILIKLARI (Poisson):
  0-0=%{iy_00}% | 1-0=%{iy_10}% | 0-1=%{iy_01}% | 1-1=%{iy_11}%
  2-0=%{iy_20}% | 0-2=%{iy_02}% | 2-1=%{iy_21}% | 1-2=%{iy_12}% | 2-2=%{iy_22}%

MS SKOR OLASILIKLARI (Poisson):
  1-0=%{ms_10}% | 2-0=%{ms_20}% | 2-1=%{ms_21}% | 1-1=%{ms_11}%
  0-1=%{ms_01}% | 0-2=%{ms_02}% | 1-2=%{ms_12}% | 2-2=%{ms_22}%
  3-0=%{ms_30}% | 3-1=%{ms_31}%
  Top5 MS: {" ".join(f"{hg}-{ag}(%{round(v,1)})" for(hg,ag),v in top_ms[:5])}
  Top4 İY: {" ".join(f"{hg}-{ag}(%{round(v,1)})" for(hg,ag),v in top_ht[:4])}

═══════════════════════════════════════
ANALİZ FORMATI — AYNEN BU YAPIDA YAZ
═══════════════════════════════════════

### 🔍 1. Genel Maç Analizi
[{h} ve {a} form durumu karşılaştırması, xG farkı, savunma/hücum zayıf noktaları. 3-4 cümle, tamamen bu maça özgü.]

### ⏱️ 2. İlk Yarı (İY) Analizi
İY Gol Ort: {h}={fv(hf,'ht_avg_gf',0)} | {a}={fv(af,'ht_avg_gf',0)}
İY xG: {h}={h_htxg} | {a}={a_htxg}
İY 0.5 Üst ihtimali: %[hesapla = 100 - iy_00 yuvarla]
İY 1.5 Üst ihtimali: %[hesapla]
İY 1-1 ihtimali: %{iy_11}
KRİTİK SKOR ANALİZİ:
  → İY 2-1 (%{iy_21}): [bu skor çıkarsa ne anlama gelir, dönüş sinyali mi?]
  → İY 1-2 (%{iy_12}): [bu skor çıkarsa ne anlama gelir, dönüş sinyali mi?]
  → İY 2-2 (%{iy_22}): [yüksek varyans durumu — analiz et]
Erken Gol Riski: [{h} ve {a}'nın 0-15 dk gol üretimi forma göre yorumla]
[İY genel yorumu — 2-3 cümle]

### 🔁 3. 2/1 – 1/2 Dönüş Analizi
**2/1 Dönüş** ({a} öne geçip {h} döner):
  H2H Geçmiş: %{h2h.get('rev21_pct',0)} ({h2h.get('rev21',0)}/{h2h.get('n',0)} maç)
  Model Olasılık: %{stats['rev21']}
  {h} 2Y Gol Yükü: %{fv(hf,'st_pct',55)} | {a} 2Y Savunma: {fv(af,'st_avg_gc',0)} yenilen/maç
  Oran Pattern Etkisi: [oran yapısı bu dönüşü destekliyor mu?]
  NET Değerlendirme: [gerçekçi mi, hangi koşulda olur?]

**1/2 Dönüş** ({h} öne geçip {a} döner):
  H2H Geçmiş: %{h2h.get('rev12_pct',0)} ({h2h.get('rev12',0)}/{h2h.get('n',0)} maç)
  Model Olasılık: %{stats['rev12']}
  {a} 2Y Gol Yükü: %{fv(af,'st_pct',55)} | {h} 2Y Savunma: {fv(hf,'st_avg_gc',0)} yenilen/maç
  Oran Pattern Etkisi: [oran yapısı bu dönüşü destekliyor mu?]
  NET Değerlendirme: [gerçekçi mi, hangi koşulda olur?]

### 🎯 4. Skor Olasılık Dağılımı
**İY En Olası 3 Skor:**
1. [skor] %[pct] — [bu maça özgü kısa gerekçe]
2. [skor] %[pct] — [gerekçe]
3. [skor] %[pct] — [gerekçe]

**MS En Olası 5 Skor:**
1. [skor] %[pct] — [xG + form bazlı gerekçe]
2. [skor] %[pct] — [gerekçe]
3. [skor] %[pct] — [gerekçe]
4. [skor] %[pct] — [gerekçe]
5. [skor] %[pct] — [gerekçe]

Beklenen Gol: {h} xG={hxg} | {a} xG={axg} | Toplam={round(hxg+axg,2)}

### 📊 5. Oran Analizi ve İstatistiksel Destek
Açılış Oranı: 1={odds_analysis.get('o1','?') if odds_analysis else '?'} X={odds_analysis.get('ox','?') if odds_analysis else '?'} 2={odds_analysis.get('o2','?') if odds_analysis else '?'}
Implied Probability: 1=%{odds_analysis['imp']['p1'] if odds_analysis else '?'} X=%{odds_analysis['imp']['px'] if odds_analysis else '?'} 2=%{odds_analysis['imp']['p2'] if odds_analysis else '?'}
Vig (bookmaker marjı): %{odds_analysis['imp']['vig'] if odds_analysis else '?'}
Model vs Piyasa Farkı: 1=+%{round(stats['p1']-(odds_analysis['imp']['p1'] if odds_analysis else stats['p1']),1)} X=+%{round(stats['px']-(odds_analysis['imp']['px'] if odds_analysis else stats['px']),1)} 2=+%{round(stats['p2']-(odds_analysis['imp']['p2'] if odds_analysis else stats['p2']),1)}
Risk Seviyesi: {odds_analysis.get('risk_level','?') if odds_analysis else 'Veri yok'}
Market Bias: [piyasa hangi sonucu fazla/az fiyatlamış? Model-piyasa farkına göre yorum yap]
Value Fırsatı: [en yüksek edge hangi tarafta? Açıkça belirt]
Bu Oran Aralığında Tarihsel Örüntü: [benzer oran yapılı maçlarda ne tür sonuçlar çıkmış? H2H + form verisine dayandır]

### 🧩 6. Tahmin Sonuçları
BANKO: [tahmin] — %[veri uyumu, min 75%] — [istatistiksel gerekçe, en az 2 veri noktası]
ORTA: [tahmin] — %[55-75 arası] — [gerekçe]
SÜRPRİZ: [yüksek varyans veya <55% tahmin] — [neden riskli?]
SKOR ÖNERİSİ: İY [X-Y] + MS [X-Y] — [tutarlı gerekçe, skor dağılımıyla çelişmemeli]

### 📌 7. Profesyonel Son Yorum
[Analizin 3-4 cümlelik kısa özeti. Maç tipi (defensif mi, açık mı, dönüş riski var mı?), en önemli 2 faktör, genel betting notu. Takım isimlerini kullan.]"""

    return prompt

def groq_call(prompt, retries=4):
    import json as _json
    for attempt in range(retries):
        try:
            r = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization":f"Bearer {GROQ_KEY}","Content-Type":"application/json"},
                json={"model":groq_model,
                      "messages":[{"role":"user","content":prompt}],
                      "temperature":0.2,
                      "max_tokens":3500},
                timeout=120)

            if r.status_code == 429:
                retry_after = r.headers.get("retry-after") or r.headers.get("Retry-After")
                try:
                    wait = int(float(retry_after)) + 2 if retry_after else 20 + attempt * 15
                except:
                    wait = 20 + attempt * 15
                wait = min(wait, 60)
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

    parts = re.split(r'###\s*(?:[^\d]*)?\d+[.)]\s*', text)
    hdrs  = re.findall(r'###\s*(?:[^\d]*)?\d+[.)]\s*(.+)', text)
    secs  = {}
    for hdr, content in zip(hdrs, parts[1:]):
        key = hdr.strip().upper()
        key_clean = re.sub(r'[^\w\s]', ' ', key).strip()
        secs[key_clean] = content.strip()

    scenarios = []
    for k, v in secs.items():
        if any(x in k for x in ["SENARYO", "DÖNÜ", "DONUS", "2 1", "1 2"]):
            for line in v.split("\n"):
                line = line.strip()
                if not line: continue
                m = re.search(r'İY\s*(\d-\d).*?2Y\s*(\d-\d).*?MS\s*(\d-\d).*?%\s*(\d+\.?\d*)', line, re.I)
                if m:
                    scenarios.append({
                        "iy": m.group(1), "2y": m.group(2),
                        "ms": m.group(3), "pct": m.group(4),
                        "desc": line
                    })

    preds = {}
    for k, v in secs.items():
        if any(x in k for x in ["TAHMİN", "TAHMIN", "TAVSİYE", "TAVSIYE", "SONUÇ", "SONUC"]):
            for line in v.split("\n"):
                line_up = line.strip().upper()
                for tag in ["BANKO", "ORTA", "SÜRPRİZ", "SURPRIZ", "RİSKLİ", "RISKLI", "SKOR"]:
                    tag_norm = tag.replace("İ","I").replace("Ş","S").replace("Ü","U").replace("Ö","O")
                    line_norm = line_up.replace("İ","I").replace("Ş","S").replace("Ü","U").replace("Ö","O")
                    if line_norm.startswith(tag_norm):
                        key_out = "SKOR" if "SKOR" in tag else tag_norm[:5]
                        preds[key_out] = line.split(":", 1)[-1].strip()

    def parse_score_list(section_text):
        items = []
        for line in section_text.split("\n"):
            line = line.strip()
            if not line: continue
            m = re.search(r"(\d-\d)\s*%?(\d+\.?\d*)[%\s]*[—–\-]?\s*(.*)", line)
            if m:
                items.append({"score": m.group(1), "pct": m.group(2), "why": m.group(3).strip()})
        return items

    iy_special = []
    ms_special = []
    for k, v in secs.items():
        k_norm = k.replace("İ","I").replace("Ş","S").replace("Ü","U").replace("Ö","O")
        if any(x in k_norm for x in ["SKOR OLASILIK", "SKOR DAGILIM", "ILK YARI OZEL", "IY OZEL"]):
            iy_block = re.search(r'IY.*?(?=MS|$)', v, re.S | re.I)
            ms_block = re.search(r'MS.*', v, re.S | re.I)
            if iy_block: iy_special = parse_score_list(iy_block.group())
            if ms_block: ms_special = parse_score_list(ms_block.group())

    return secs, scenarios, preds, iy_special, ms_special

def render_live_match(m, live_stats, lp, analysis_text, hf, af, h2h):
    h      = m["homeTeam"]["name"]
    a      = m["awayTeam"]["name"]
    h_sc   = m.get("score",{}).get("fullTime",{}).get("home") or 0
    a_sc   = m.get("score",{}).get("fullTime",{}).get("away") or 0
    ht_h   = m.get("score",{}).get("halfTime",{}).get("home") or 0
    ht_a   = m.get("score",{}).get("halfTime",{}).get("away") or 0
    minute = calc_live_minute(m)
    is_ht  = lp.get("is_first_half", _safe_minute(minute) <= 45)
    ht_rem = lp.get("ht_remaining_min", 0)
    ms_rem = lp.get("remaining_min", 0)
    fv     = lambda d,k,dv=0: d.get(k,dv) if d else dv

    phase = f"1. Yarı — {ht_rem}dk kaldı" if is_ht and ht_rem > 0 else ("Devre Arası" if is_ht else f"2. Yarı — {ms_rem}dk kaldı")
    st.markdown(
        f'<div class="live-header">'
        f'<div class="live-dot"></div>'
        f'<span class="live-badge">CANLI</span>'
        f'<span class="live-title">{h} <b style="color:#d0dce8"> vs </b>{a}'
        f' &nbsp;·&nbsp; <span style="color:#4a6880;font-size:.78rem">{phase}</span></span>'
        f'<span class="live-minute">{minute}\'</span>'
        f'</div>', unsafe_allow_html=True
    )

    events_h = events_a = ""
    home_id = m.get("homeTeam",{}).get("id")
    for ev in m.get("goals", []):
        team_id = ev.get("team",{}).get("id")
        scorer  = ev.get("scorer",{}).get("name") or ev.get("scorer",{}).get("shortName","?")
        scorer_short = scorer.split()[-1] if scorer else "?"
        mi      = ev.get("minute","?")
        inj     = ev.get("injuryTime")
        mi_str  = f"{mi}+{inj}" if inj else str(mi)
        line    = f"⚽ {scorer_short} {mi_str}' "
        if team_id == home_id:
            events_h += line
        else:
            events_a += line
    
    goal_h_count = sum(1 for ev in m.get("goals",[]) if ev.get("team",{}).get("id") == home_id)
    goal_a_count = len(m.get("goals",[])) - goal_h_count
    if goal_h_count != h_sc or goal_a_count != a_sc:
        if h_sc > 0 and not events_h:
            events_h = "⚽ " * h_sc
        if a_sc > 0 and not events_a:
            events_a = "⚽ " * a_sc

    st.markdown(f"""
<div class="live-score-wrap">
  <div class="live-score-row">
    <div class="ls-team">
      <div class="lst-name home">{h}</div>
      <div class="lst-events">{events_h or '–'}</div>
    </div>
    <div class="ls-score">
      <div class="lss-main">{h_sc} – {a_sc}</div>
      <div class="lss-ht">{"İY devam" if is_ht else f"İY: {ht_h}–{ht_a}"}</div>
    </div>
    <div class="ls-team">
      <div class="lst-name away">{a}</div>
      <div class="lst-events">{events_a or '–'}</div>
    </div>
  </div>
""", unsafe_allow_html=True)

    stats_display = [
        ("Top Kontrolü",  f"%{int(live_stats['possession_h'])}",  f"%{int(live_stats['possession_a'])}",   live_stats['possession_h'],  live_stats['possession_a']),
        ("Şut/İsabetli",  f"{int(live_stats['shots_h'])}/{int(live_stats['shots_on_h'])}",
                          f"{int(live_stats['shots_on_a'])}/{int(live_stats['shots_a'])}",
                          live_stats['shots_h'],  live_stats['shots_a']),
        ("Teh. Atak",     str(int(live_stats['dangerous_h'])),     str(int(live_stats['dangerous_a'])),     live_stats['dangerous_h'],   live_stats['dangerous_a']),
        ("Korner",        str(int(live_stats['corners_h'])),        str(int(live_stats['corners_a'])),        live_stats['corners_h'],     live_stats['corners_a']),
        ("xG",            f"{live_stats['xg_h']:.2f}",             f"{live_stats['xg_a']:.2f}",             live_stats['xg_h']*10,       live_stats['xg_a']*10),
        ("Sarı Kart",     str(int(live_stats['yellow_h'])),         str(int(live_stats['yellow_a'])),         live_stats['yellow_h'],      live_stats['yellow_a']),
    ]
    stat_html = '<div style="padding:.5rem 0">'
    for lbl, hv, av, hw, aw in stats_display:
        total = max(hw + aw, 0.01)
        h_w   = round(hw / total * 100)
        stat_html += (
            f'<div class="stat-bar-row">'
            f'<div class="sbr-val home">{hv}</div>'
            f'<div class="sbr-bars" style="justify-content:flex-end">'
            f'<div class="sbr-bar-h" style="width:{h_w}%;max-width:100%"></div></div>'
            f'<div class="sbr-label">{lbl}</div>'
            f'<div class="sbr-bars">'
            f'<div class="sbr-bar-a" style="width:{100-h_w}%;max-width:100%"></div></div>'
            f'<div class="sbr-val away">{av}</div>'
            f'</div>'
        )

    mom = lp.get("momentum_h", 50)
    stat_html += f"""
<div class="momentum-wrap">
  <div style="font-size:.54rem;color:#4a6880;text-transform:uppercase;letter-spacing:.1em;margin-bottom:4px">
    Momentum &nbsp;<span style="color:#4c9eff">{h[:12]}</span> ← → <span style="color:#ff7070">{a[:12]}</span>
  </div>
  <div class="mom-bar-track">
    <div class="mom-bar-fill" style="width:{mom}%;background:linear-gradient(90deg,#1d4ed8,#4c9eff)"></div>
  </div>
  <div class="mom-labels"><span>{mom}%</span><span>{100-mom}%</span></div>
</div>"""
    stat_html += '</div>'
    st.markdown(stat_html + '</div>', unsafe_allow_html=True)

    if is_ht and ht_rem > 0:
        st.markdown(f"""
<div style="background:#09101e;border:2px solid #1d4ed8;border-radius:10px;
padding:.9rem 1.4rem;margin-bottom:.7rem">
  <div style="font-size:.56rem;font-weight:700;letter-spacing:.13em;text-transform:uppercase;
  color:#4c9eff;margin-bottom:8px;padding-bottom:4px;border-bottom:1px solid #1c2e44">
  ⏱ İLK YARI — {ht_rem} dakika kaldı &nbsp;·&nbsp; Mevcut: {h_sc}–{a_sc}</div>
  <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:6px;margin-bottom:6px">
    {_prob_box("İY 0.5 ÜST", lp.get('ht_o5', 0))}
    {_prob_box("İY 0.5 ALT", lp.get('ht_u5', 0))}
    {_prob_box("İY 1.5 ÜST", lp.get('ht_o15', 0))}
    {_prob_box("İY KG VAR",  lp.get('ht_kg_var', 0))}
  </div>
  <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:6px">
    {_prob_box("Snrk İY Gol EV",  lp.get('ht_next_h', 0))}
    {_prob_box("Snrk İY Gol DEP", lp.get('ht_next_a', 0))}
    {_prob_box("Bkl.İY Gol", lp.get('expected_ht', 0), is_xg=True)}
  </div>
  <div style="margin-top:8px;font-size:.62rem;color:#4a6880">
    Tarihsel → {h}: İY ort <b style="color:#4c9eff">{fv(hf,'ht_avg_gf',0)}</b> gol &nbsp;|&nbsp;
    {a}: İY ort <b style="color:#ff7070">{fv(af,'ht_avg_gf',0)}</b> gol &nbsp;|&nbsp;
    H2H İY: {h2h.get('ht_hw',0)}G–{h2h.get('ht_dr',0)}B–{h2h.get('ht_aw',0)}M
  </div>
</div>
""", unsafe_allow_html=True)
    else:
        ht_winner = f"{h} önde" if ht_h > ht_a else (f"{a} önde" if ht_a > ht_h else "Berabere")
        st.markdown(f"""
<div style="background:#09101e;border:1px solid #1c2e44;border-radius:8px;
padding:.7rem 1.2rem;margin-bottom:.7rem;display:flex;align-items:center;gap:12px">
  <div style="font-size:.56rem;font-weight:700;color:#4a6880;text-transform:uppercase;letter-spacing:.1em">İY Sonucu</div>
  <div style="font-size:1.1rem;font-weight:800;color:#d0dce8;font-family:JetBrains Mono,monospace">{ht_h}–{ht_a}</div>
  <div style="font-size:.68rem;color:#4a6880">{ht_winner}</div>
  <div style="margin-left:auto;font-size:.62rem;color:#4a6880">
    2. Yarı için → {h}: 2Y ort <b style="color:#4c9eff">{fv(hf,'st_avg_gf',0)}</b> &nbsp;|&nbsp;
    {a}: 2Y ort <b style="color:#ff7070">{fv(af,'st_avg_gf',0)}</b>
  </div>
</div>
""", unsafe_allow_html=True)

    st.markdown(f"""
<div style="background:#09101e;border:1px solid #1c2e44;border-radius:10px;
padding:.9rem 1.4rem;margin-bottom:.7rem">
  <div style="font-size:.56rem;font-weight:700;letter-spacing:.13em;text-transform:uppercase;
  color:#4a6880;margin-bottom:8px;padding-bottom:4px;border-bottom:1px solid #1c2e44">
  🏁 MAÇ SONU — {ms_rem} dakika kaldı &nbsp;·&nbsp; Bklenen ek gol: {lp.get('expected_remaining',0)}</div>
  <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:6px;margin-bottom:6px">
    {_prob_box("Snrk Gol EV",  lp.get('p_next_h',0))}
    {_prob_box("Snrk Gol DEP", lp.get('p_next_a',0))}
    {_prob_box("KG VAR",       lp.get('p_kg_var',0))}
    {_prob_box("2.5 ÜST",      lp.get('o25',0))}
  </div>
  <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:6px">
    {_prob_box("2.5 ALT", lp.get('u25',0))}
    {_prob_box("1.5 ÜST", lp.get('o15',0))}
    {_prob_box("3.5 ÜST", lp.get('o35',0))}
    {_prob_box("3.5 ALT", lp.get('u35',0))}
  </div>
</div>
""", unsafe_allow_html=True)

    if analysis_text:
        import re as _re

        durum = _extract_section(analysis_text, "CANLI DURUM")
        iy_analiz = _extract_section(analysis_text, "İLK YARI")
        ms_analiz = _extract_section(analysis_text, "MAÇ SONU")
        all_recs = _parse_goal_bets(analysis_text)
        iy_recs = _parse_iy_bets(analysis_text)
        bekle_txt = _extract_bekle_gec(analysis_text)

        if durum:
            st.markdown(f"""
<div style="background:#0d1829;border:1px solid #1c2e44;border-radius:8px;
padding:.75rem 1.1rem;margin-bottom:.6rem">
  <div style="font-size:.54rem;font-weight:700;letter-spacing:.12em;text-transform:uppercase;
  color:#4a6880;margin-bottom:5px">📊 Canlı Durum</div>
  <div style="font-size:.76rem;color:#7a9ab8;line-height:1.75">{durum}</div>
</div>""", unsafe_allow_html=True)

        if iy_analiz:
            st.markdown(f"""
<div style="background:#060f20;border:1px solid #1d4ed8;border-radius:8px;
padding:.75rem 1.1rem;margin-bottom:.6rem">
  <div style="font-size:.54rem;font-weight:700;letter-spacing:.12em;text-transform:uppercase;
  color:#4c9eff;margin-bottom:5px">⏱ İlk Yarı Analizi</div>
  <div style="font-size:.76rem;color:#7a9ab8;line-height:1.75">{iy_analiz}</div>
</div>""", unsafe_allow_html=True)

        if iy_recs:
            st.markdown('<div style="font-size:.54rem;font-weight:700;letter-spacing:.12em;'
                       'text-transform:uppercase;color:#4c9eff;margin-bottom:5px">⏱ İY Bahis Tavsiyeleri</div>',
                       unsafe_allow_html=True)
            cols = st.columns(len(iy_recs))
            for rec, col in zip(iy_recs, cols):
                conf = rec.get("confidence","ORTA").upper()
                cls  = "strong" if "YÜKSEK" in conf else ("medium" if "ORTA" in conf else "risky")
                with col:
                    st.markdown(f"""
<div class="goal-rec-box {cls}" style="border-color:#1d4ed8">
  <div class="grb-label" style="color:#4c9eff">{'🔒 İY BANKO' if 'YÜKSEK' in conf else '⚡ İY ORTA'}</div>
  <div class="grb-bet">{rec.get('market','?')}</div>
  <div class="grb-why">{rec.get('why','')[:80]}</div>
  <div class="grb-conf" style="color:#4c9eff">{conf}</div>
</div>""", unsafe_allow_html=True)

        if all_recs:
            st.markdown('<div style="font-size:.54rem;font-weight:700;letter-spacing:.12em;'
                       'text-transform:uppercase;color:#4a6880;margin:.6rem 0 5px">🏁 MS Bahis Tavsiyeleri</div>',
                       unsafe_allow_html=True)
            cols = st.columns(len(all_recs))
            for rec, col in zip(all_recs, cols):
                conf = rec.get("confidence","ORTA").upper()
                cls  = "strong" if "YÜKSEK" in conf else ("medium" if "ORTA" in conf else "risky")
                with col:
                    st.markdown(f"""
<div class="goal-rec-box {cls}">
  <div class="grb-label">{'🔒 BANKO' if 'YÜKSEK' in conf else ('⚡ ORTA' if 'ORTA' in conf else '💎 RİSKLİ')}</div>
  <div class="grb-bet">{rec.get('market','?')}</div>
  <div class="grb-why">{rec.get('why','')[:80]}</div>
  <div class="grb-conf">{conf}</div>
</div>""", unsafe_allow_html=True)

        if bekle_txt:
            simdi_al_txt, gecme_txt = bekle_txt
            parts_html = ""
            if simdi_al_txt:
                parts_html += f'<div style="background:#04180a;border:1px solid #166534;border-radius:7px;padding:.5rem .9rem;font-size:.72rem;color:#3ecf7a">✅ <b>Şimdi Al:</b> {simdi_al_txt}</div>'
            if gecme_txt:
                parts_html += f'<div style="background:#120e00;border:1px solid #b45309;border-radius:7px;padding:.5rem .9rem;font-size:.72rem;color:#f5a623">🚫 <b>Geçme:</b> {gecme_txt}</div>'
            if parts_html:
                st.markdown(f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:7px;margin-top:.5rem">{parts_html}</div>', unsafe_allow_html=True)

def _prob_box(label, val, is_xg=False):
    if is_xg:
        color   = "#4c9eff"
        display = f"{float(val):.2f}"
        sub     = "beklenen"
    else:
        v       = float(val)
        color   = "#3ecf7a" if v >= 65 else ("#f5a623" if v >= 40 else "#ff7070")
        display = f"%{v:.0f}"
        sub     = ""
    return (f'<div style="background:#111f35;border:1px solid #1c2e44;border-radius:6px;'
            f'padding:7px 4px;text-align:center">'
            f'<div style="font-size:.52rem;color:#4a6880;text-transform:uppercase;'
            f'letter-spacing:.07em;margin-bottom:2px">{label}</div>'
            f'<div style="font-size:1.05rem;font-weight:800;color:{color};'
            f'font-family:JetBrains Mono,monospace">{display}</div>'
            + (f'<div style="font-size:.52rem;color:#4a6880">{sub}</div>' if sub else '')
            + '</div>')

def _parse_goal_bets(text):
    import re as _re
    recs = []
    for line in text.splitlines():
        m = _re.match(r'GOL_BAHSI_\d+\s*:\s*(.+?)\s*—\s*(.+?)\s*—\s*GÜVENİLİRLİK\s*:\s*(\w+)', line.strip(), _re.I)
        if m:
            recs.append({"market": m.group(1).strip(), "why": m.group(2).strip(), "confidence": m.group(3).strip()})
    return recs[:3]

def _parse_iy_bets(text):
    import re as _re
    recs = []
    for line in text.splitlines():
        m = _re.match(r'IY_BAHSI_\d+\s*:\s*(.+?)\s*—\s*(.+?)\s*—\s*GÜVENİLİRLİK\s*:\s*(\w+)', line.strip(), _re.I)
        if m and "tamamlandı" not in m.group(1).lower():
            recs.append({"market": m.group(1).strip(), "why": m.group(2).strip(), "confidence": m.group(3).strip()})
    return recs[:2]

def _extract_section(text, keyword):
    import re as _re
    m = _re.search(rf'###\s*\d*\.?\s*{keyword}.*?\n(.*?)(?=###|\Z)', text, _re.S | _re.I)
    if m:
        content = m.group(1).strip()
        content = _re.sub(r'(GOL_BAHSI|IY_BAHSI)_\d+.*', '', content).strip()
        return content[:350]
    return ""

def _extract_bekle_gec(text):
    import re as _re
    simdi_al = gecme = ""
    sec_m = _re.search(r'###\s*5\..*?\n(.*?)(?=###|\Z)', text, _re.S | _re.I)
    block = sec_m.group(1) if sec_m else text
    for line in block.splitlines():
        ls = line.strip()
        if _re.match(r'(ŞIMDI_AL|SIMDI_AL|ŞİMDİ_AL)', ls, _re.I):
            simdi_al = ls.split(":",1)[-1].strip()[:200]
        elif _re.match(r'GEÇME|GECME', ls, _re.I):
            gecme    = ls.split(":",1)[-1].strip()[:150]
    return (simdi_al, gecme) if (simdi_al or gecme) else None

def _extract_simdi_al(text):
    import re as _re
    m = _re.search(r'(ŞIMDI_AL|SIMDI_AL|ŞİMDİ_AL)\s*:\s*(.+?)(?:\n|$)', text, _re.I)
    if m:
        full = m.group(2).strip()
        parts = full.split("—")
        return {"market": parts[0].strip(), "why": parts[1].strip() if len(parts) > 1 else ""}
    return None

def auto_best_bet(lp, h_name, a_name, h_score, a_score, hf=None, af=None, league_code=None):
    fv = lambda d, k, dv=0: d.get(k, dv) if d else dv
    is_ht      = lp.get("is_first_half", False)
    ht_rem     = lp.get("ht_remaining_min", 0)
    ms_rem     = lp.get("remaining_min", 90)
    league_avg = lp.get("league_avg", 2.70)
    low        = league_avg < 2.65

    cands = []
    def add(mkt, prob, why, pri):
        cands.append({"market": mkt, "prob": float(prob), "why": why, "priority": pri})

    up = 5 if low else 0
    dn = 5 if low else 0

    pnh = lp.get("p_next_h", 0)
    if pnh >= 70:
        add(f"{h_name} Gol Atar (0.5 Üst)", pnh, f"ev baskısı %{pnh}", 1)

    pna = lp.get("p_next_a", 0)
    if pna >= 70:
        add(f"{a_name} Gol Atar (0.5 Üst)", pna, f"dep atağı %{pna}", 2)

    if is_ht and ht_rem >= 5:
        v = lp.get("ht_o5", 0)
        if v >= 62 - dn:
            add("İY 0.5 Üst", v, f"İY gol gelir {ht_rem}dk kaldı %{v}", 3)

    v = lp.get("o15", 0)
    if v >= 65 - dn:
        add("MS 1.5 Üst", v, f"2+ gol bekleniyor %{v}", 4)

    if h_score + a_score == 0:
        v = lp.get("p_next_goal", 0)
        if v >= 80:
            add("MS 0.5 Üst (İlk Gol)", v, f"henüz gol yok beklenti %{v}", 5)

    v = lp.get("o25", 0)
    if v >= 65 - dn:
        add("MS 2.5 Üst", v, f"3+ gol bekleniyor %{v}", 6)

    if is_ht and ht_rem >= 8:
        v = lp.get("ht_o15", 0)
        if v >= 60 - dn:
            add("İY 1.5 Üst", v, f"İY 2+ gol %{v}", 7)

    v = lp.get("u25", 0)
    if v >= 65 + up and ms_rem <= 55:
        add("MS 2.5 Alt", v, f"düşük gol beklentisi %{v}", 8)

    if is_ht and ht_rem <= 10 and h_score + a_score == 0 and low:
        v = lp.get("ht_u5", 0)
        if v >= 58:
            add("İY 0.5 Alt", v, f"az kaldı golsüz %{v}", 9)

    v = lp.get("p_kg_var", 0)
    if v >= 70:
        add("KG VAR", v, f"her iki takım gol atar %{v}", 10)

    if is_ht and ht_rem >= 6:
        v = lp.get("ht_kg_var", 0)
        if v >= 62:
            add("İY KG VAR", v, f"İY her iki takım %{v}", 11)

    if not cands:
        return None

    meaningful = [c for c in cands if 52 <= c["prob"] <= 94]
    if not meaningful:
        meaningful = [c for c in cands if c["prob"] < 99]
    if not meaningful:
        return None

    meaningful.sort(key=lambda x: (-x["prob"], x["priority"]))
    return meaningful[0]

def _get_all_bets(lp, h_name, a_name, h_score, a_score, hf=None, af=None, league_code=None, live_odds=None):
    is_ht   = lp.get("is_first_half", False)
    ht_rem  = lp.get("ht_remaining_min", 0)
    ms_rem  = lp.get("remaining_min", 90)
    total_g = int(h_score or 0) + int(a_score or 0)
    if ms_rem <= 3: return []
    if is_ht and ht_rem <= 2: return []

    totals   = (live_odds or {}).get("totals", {})
    h2h_o    = (live_odds or {}).get("h2h", {})
    has_odds = bool(totals or h2h_o)

    cands = []
    def add(mkt, prob, why, pri, done_at=None, odd=None):
        if done_at is not None and total_g > done_at: return
        p = float(prob or 0)
        if has_odds:
            if odd is None or float(odd) <= 1.10: return
            imp  = 100 / float(odd)
            edge = round(p - imp, 1)
            label = f"oran {odd}" + (f" ⚡VALUE +{edge:.0f}%" if edge >= 3 else "")
            cands.append({"market":mkt,"prob":p,"odd":odd,"why":f"{why} | {label}","priority":pri,"value":edge})
        else:
            if 55 <= p <= 90:
                cands.append({"market":mkt,"prob":p,"odd":None,"why":why,"priority":pri,"value":0})

    add(f"{h_name} Kazanır", lp.get("p_next_h",50)*0.7, "1 kazanır", 20, odd=h2h_o.get("1"))
    add("Beraberlik",        30,                          "beraberlik",21, odd=h2h_o.get("X"))
    add(f"{a_name} Kazanır", lp.get("p_next_a",50)*0.7, "2 kazanır", 22, odd=h2h_o.get("2"))
    add(f"{h_name} Gol Atar", lp.get("p_next_h",0), "ev baskısı", 1)
    add(f"{a_name} Gol Atar", lp.get("p_next_a",0), "dep atağı",  2)
    for thr_str, over_odd in totals.items():
        if "_over" not in thr_str: continue
        try: thr = float(thr_str.replace("_over",""))
        except: continue
        under_odd  = totals.get(f"{thr}_under")
        done_thr   = int(thr - 0.5)
        add(f"{thr} Üst", lp.get(f"o{int(thr*10)}",0), f"{int(thr+0.5)}+ gol", int(thr*10)+1, done_at=done_thr, odd=over_odd)
        add(f"{thr} Alt", lp.get(f"u{int(thr*10)}",0), f"max {int(thr-0.5)} gol", int(thr*10)+2, odd=under_odd)
    if not has_odds:
        add("MS 1.5 Üst",lp.get("o15",0),"2+ gol",   4,done_at=0)
        add("MS 1.5 Alt",lp.get("u15",0),"max 1 gol",14)
        add("MS 2.5 Üst",lp.get("o25",0),"3+ gol",   6,done_at=1)
        add("MS 2.5 Alt",lp.get("u25",0),"max 2 gol",8)
        add("MS 3.5 Alt",lp.get("u35",0),"max 3 gol",10)
        add("KG VAR",    lp.get("p_kg_var",0),"her iki takım atar",11)
        if total_g == 0:
            add("İlk Gol",lp.get("p_next_goal",0),"maçta gol olur",5)
    if is_ht and ht_rem >= 4:
        add("İY 0.5 Üst",lp.get("ht_o5",0),   f"İY gol gelir {ht_rem}dk",3,done_at=0)
        add("İY 0.5 Alt",lp.get("ht_u5",0),   "İY gol gelmez",           12)
        add("İY KG VAR", lp.get("ht_kg_var",0),"İY her iki takım atar",  13)
    if is_ht and ht_rem >= 7:
        add("İY 1.5 Üst",lp.get("ht_o15",0),f"İY 2+ gol {ht_rem}dk",7,done_at=0)
        add("İY 1.5 Alt",lp.get("ht_u15",0),"İY max 1 gol",          15)

    cands.sort(key=lambda x:(-x.get("value",0),-x["prob"],x["priority"]))
    seen,result=[],[]
    for c in cands:
        if c["market"] not in seen:
            seen.append(c["market"])
            result.append(c)
    return result[:6]

def render_vs_ui(match, hf, af, h2h, hxg, axg, h_htxg, a_htxg,
                 stats, top_ms, top_ht, h_stand, a_stand, h_sc, a_sc,
                 analysis_text, odds_analysis=None):
    h   = match["homeTeam"]["name"]
    a   = match["awayTeam"]["name"]
    utc = match.get("utcDate","")[:16].replace("T"," ")
    secs, scenarios, preds, iy_special, ms_special = parse_analysis(analysis_text)
    fv  = lambda d,k,dv=0: d.get(k,dv) if d else dv
    hs  = h_stand or {}; as_ = a_stand or {}

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
    vc_html += f"""
<div class="vc-row">
  <div class="vc-home"><span style="font-size:.72rem;color:#2563eb">{h_sc_str}</span></div>
  <div class="vc-label">Golcü</div>
  <div class="vc-away"><span style="font-size:.72rem;color:#dc2626">{a_sc_str}</span></div>
</div>"""
    vc_html += "</div>"
    st.markdown(vc_html, unsafe_allow_html=True)

    dp_html = '<div class="data-panel">'

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

    rev21_m = stats['rev21']; rev21_h = h2h.get('rev21_pct',0)
    rev12_m = stats['rev12']; rev12_h = h2h.get('rev12_pct',0)
    hot21 = rev21_m > 10 or rev21_h > 20
    hot12 = rev12_m > 10 or rev12_h > 20
    def _find_sec(secs_dict, *keywords):
        for k, v in secs_dict.items():
            k_norm = k.upper().replace("İ","I").replace("Ö","O").replace("Ü","U").replace("Ş","S").replace("Ç","C").replace("/","").replace("-","")
            if all(kw.upper() in k_norm for kw in keywords):
                return v
        return ""
    import re as _re21
    _donus_full = _find_sec(secs, "DON")
    _m21 = _re21.search(r'2/1.*?(?=\*\*1/2|\Z)', _donus_full, _re21.S|_re21.I) if _donus_full else None
    _m12 = _re21.search(r'1/2.*',               _donus_full, _re21.S|_re21.I) if _donus_full else None
    d21_txt = " ".join((_m21.group(0) if _m21 else _find_sec(secs,"2","1","DON")).split()[:80])
    d12_txt = " ".join((_m12.group(0) if _m12 else _find_sec(secs,"1","2","DON")).split()[:80])

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

    def _build_iy_scores(hform, aform, ht_top):
        from collections import defaultdict

        h_htxg = hform.get("ht_avg_gf", 0.5) if hform else 0.5
        a_htxg = aform.get("ht_avg_gf", 0.5) if aform else 0.5
        h_n    = hform.get("n", 1) if hform else 1
        a_n    = aform.get("n", 1) if aform else 1

        h_ht_freq = hform.get("ht_score_freq", {}) if hform else {}
        a_ht_freq = aform.get("ht_score_freq", {}) if aform else {}

        def form_weight(n_matches):
            return min(0.40, max(0.20, n_matches / 30))

        h_fw = form_weight(h_n)
        a_fw = form_weight(a_n)
        poi_w = 1.0 - (h_fw + a_fw) / 2

        scores = {}
        for (hg, ag), prob in ht_top[:12]:
            scores[f"{hg}-{ag}"] = {"pct": round(prob, 1), "why": ""}

        for sc, info in h_ht_freq.items():
            if info.get("count", 0) < 2:
                continue
            if sc in scores:
                combined = round(scores[sc]["pct"] * (1 - h_fw) + info["pct"] * h_fw, 1)
                scores[sc] = {"pct": combined, "why": f"Ev {info['count']}x"}
            else:
                scores[sc] = {"pct": round(info["pct"] * h_fw, 1),
                              "why": f"Ev {info['count']}x"}

        for sc, info in a_ht_freq.items():
            if info.get("count", 0) < 2:
                continue
            parts = sc.split("-")
            if len(parts) == 2:
                rev_sc = f"{parts[1]}-{parts[0]}"
                if rev_sc in scores:
                    combined = round(scores[rev_sc]["pct"] * (1 - a_fw) + info["pct"] * a_fw, 1)
                    old_why  = scores[rev_sc].get("why", "")
                    scores[rev_sc] = {"pct": combined,
                                      "why": f"{old_why} | Dep {info['count']}x".strip(" |")}
                else:
                    scores[rev_sc] = {"pct": round(info["pct"] * a_fw, 1),
                                      "why": f"Dep {info['count']}x"}

        filtered = {}
        for sc, info in scores.items():
            parts = sc.split("-")
            if len(parts) != 2:
                continue
            try:
                hg, ag = int(parts[0]), int(parts[1])
            except:
                continue
            if hg + ag >= 3 and h_htxg + a_htxg < 1.5:
                continue
            if hg > 0 and ag > 0 and h_htxg < 0.3 and a_htxg < 0.3:
                continue
            filtered[sc] = info

        sorted_scores = sorted(filtered.items(), key=lambda x: -x[1]["pct"])
        return [{"score": sc, "pct": str(info["pct"]), "why": info.get("why", "")}
                for sc, info in sorted_scores[:6] if info["pct"] >= 0.5]

    def _build_ms_scores(hform, aform, ms_top):
        h_avg_gf = hform.get("avg_gf", 1.2) if hform else 1.2
        a_avg_gf = aform.get("avg_gf", 1.0) if aform else 1.0
        h_n      = hform.get("n", 1) if hform else 1
        a_n      = aform.get("n", 1) if aform else 1

        h_ms_freq = hform.get("ms_score_freq", {}) if hform else {}
        a_ms_freq = aform.get("ms_score_freq", {}) if aform else {}

        def form_weight(n_matches):
            return min(0.40, max(0.20, n_matches / 30))

        h_fw = form_weight(h_n)
        a_fw = form_weight(a_n)

        scores = {}
        for (hg, ag), prob in ms_top[:12]:
            scores[f"{hg}-{ag}"] = {"pct": round(prob, 1), "why": ""}

        for sc, info in h_ms_freq.items():
            if info.get("count", 0) < 2:
                continue
            if sc in scores:
                combined = round(scores[sc]["pct"] * (1 - h_fw) + info["pct"] * h_fw, 1)
                scores[sc] = {"pct": combined, "why": f"Ev {info['count']}x"}
            elif info["pct"] >= 5:
                scores[sc] = {"pct": round(info["pct"] * h_fw, 1),
                              "why": f"Ev {info['count']}x"}

        for sc, info in a_ms_freq.items():
            if info.get("count", 0) < 2:
                continue
            parts = sc.split("-")
            if len(parts) == 2:
                rev_sc = f"{parts[1]}-{parts[0]}"
                if rev_sc in scores:
                    old = scores[rev_sc]
                    combined = round(old["pct"] * (1 - a_fw) + info["pct"] * a_fw, 1)
                    scores[rev_sc] = {"pct": combined,
                                      "why": f"{old.get('why','')} Dep {info['count']}x".strip()}
                elif info["pct"] >= 5:
                    scores[rev_sc] = {"pct": round(info["pct"] * a_fw, 1),
                                      "why": f"Dep {info['count']}x"}

        sorted_s = sorted(scores.items(), key=lambda x: -x[1]["pct"])
        return [{"score": sc, "pct": str(round(info["pct"], 1)), "why": info.get("why", "")}
                for sc, info in sorted_s[:8] if info["pct"] >= 1.0]

    iy_scores_combined = _build_iy_scores(hf, af, top_ht)
    ms_scores_combined = _build_ms_scores(hf, af, top_ms_shape if "top_ms_shape" in dir() else top_ms)

    if iy_scores_combined:
        st.markdown("""
<div class="skor-panel">
  <div class="dp-section-title">📊 GERÇEK SKOR DAĞILIMI — Form + Poisson Kombine</div>
""", unsafe_allow_html=True)
        cols_i = st.columns(len(iy_scores_combined[:6]))
        for col, sc in zip(cols_i, iy_scores_combined[:6]):
            with col:
                st.markdown(f"""
<div style="background:#111f35;border:1px solid #1c2e44;border-radius:6px;padding:6px 3px;text-align:center">
  <div style="font-size:1rem;font-weight:800;color:#a8c4d8;font-family:JetBrains Mono,monospace">{sc['score']}</div>
  <div style="font-size:.58rem;color:#4a6880">%{sc['pct']}</div>
  <div style="font-size:.5rem;color:#2a3a4a">{sc['why'][:25]}</div>
</div>""", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    if ms_scores_combined:
        st.markdown("""
<div class="skor-panel">
  <div class="dp-section-title">📊 MS GERÇEK SKOR DAĞILIMI — Form + Poisson Kombine</div>
""", unsafe_allow_html=True)
        cols_m = st.columns(len(ms_scores_combined[:8]))
        for col, sc in zip(cols_m, ms_scores_combined[:8]):
            with col:
                st.markdown(f"""
<div style="background:#111f35;border:1px solid #1c2e44;border-radius:6px;padding:6px 3px;text-align:center">
  <div style="font-size:1rem;font-weight:800;color:#a8c4d8;font-family:JetBrains Mono,monospace">{sc['score']}</div>
  <div style="font-size:.58rem;color:#4a6880">%{sc['pct']}</div>
  <div style="font-size:.5rem;color:#2a3a4a">{sc['why'][:25]}</div>
</div>""", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    banko  = preds.get("BANKO","")
    orta   = preds.get("ORTA","")
    risky  = preds.get("RISKI", preds.get("RISKL", preds.get("SURPR", preds.get("RİSKLİ",""))))
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
    if secs.get("SKOR","") or preds.get("SKOR",""):
        skor_val = preds.get("SKOR","") or ""
        import re
        iy_match = re.search(r"İY\s*(\d-\d)", skor_val, re.I)
        ms_match = re.search(r"MS\s*(\d-\d)", skor_val, re.I)
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

    analiz_text = ""
    for k, v in secs.items():
        k_norm = k.replace("İ","I").replace("Ş","S").replace("Ü","U").replace("Ö","O").replace("Ç","C")
        if any(x in k_norm for x in ["GENEL MAC", "GENEL MAÇ", "GENEL ANALIZ", "SON YORUM", "PROFESYONEL SON", "PROFESYONEL MAC"]):
            analiz_text = v; break
    if not analiz_text:
        for k, v in secs.items():
            if "ANALIZ" in k.replace("İ","I").replace("Ş","S").replace("Ü","U").replace("Ö","O").replace("Ç","C"):
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

    st.markdown("</div>", unsafe_allow_html=True)
    st.download_button("⬇️ Tam Analizi İndir (.txt)", data=analysis_text,
                       file_name=f"{h}_vs_{a}_{sel_date}.txt",
                       mime="text/plain", key=f"dl_{h[:4]}_{a[:4]}")

# ══════════════════════════════════════════════════════════════════
# SESSION STATE
# ══════════════════════════════════════════════════════════════════
for k in ["matches","mdata","analyses","patterns"]:
    if k not in st.session_state:
        st.session_state[k] = [] if k=="matches" else {}

for k in ["live_matches","live_analyses","live_stats_cache"]:
    if k not in st.session_state:
        st.session_state[k] = {}

# ══════════════════════════════════════════════════════════════════
# CANLI MAÇ MODU
# ══════════════════════════════════════════════════════════════════
if app_mode == "🔴 Canlı Maçlar":

    st.markdown("""
<div class="live-header" style="margin-bottom:.8rem">
  <div class="live-dot"></div>
  <span class="live-badge">CANLI ANALİZ</span>
  <span class="live-title">Gerçek Zamanlı Gol Bahis Rehberi</span>
</div>""", unsafe_allow_html=True)

    lc1, lc2, lc3, lc4 = st.columns([2,2,2,2])
    with lc1:
        live_league = st.selectbox("Lig", ["Tüm Ligler","PL","PD","BL1","SA","FL1","CL","EL"], key="live_league_sel")
    with lc2:
        live_refresh_btn = st.button("🔄 Maçları Çek/Yenile", type="primary", use_container_width=True, key="live_refresh")
    with lc3:
        live_analyze_all_btn = st.button("🤖 Tümünü Analiz Et", use_container_width=True, key="live_all")
    with lc4:
        live_auto = st.checkbox("⚡ 60sn otomatik yenile", value=False, key="live_auto_refresh")

    st.divider()

    if live_refresh_btn or live_auto:
        code_filter = None if live_league == "Tüm Ligler" else live_league
        with st.spinner("📡 Canlı maçlar çekiliyor..."):
            live_ms = api_live_matches(code_filter)

        current_live_ids = {lm["id"] for lm in live_ms}
        for sid in [k for k in st.session_state["live_matches"] if k not in current_live_ids]:
            st.session_state["live_matches"].pop(sid, None)
            st.session_state["live_analyses"].pop(sid, None)

        if not live_ms:
            st.info("🔴 Şu anda oynanan maç bulunamadı.")
        else:
            st.success(f"✅ {len(live_ms)} canlı maç")
            for lm in live_ms:
                if lm.get("status","") not in ("IN_PLAY","PAUSED"):
                    continue
                lid  = lm["id"]
                lhid = lm["homeTeam"]["id"]
                laid = lm["awayTeam"]["id"]
                fk   = f"live_form_{lhid}_{laid}"
                if fk not in st.session_state:
                    hff  = parse_form(api_team_matches(lhid, 8), lhid)
                    aff  = parse_form(api_team_matches(laid, 8), laid)
                    h2hf = parse_h2h(api_h2h(lid, 6), lhid)
                    st.session_state[fk] = (hff, aff, h2hf)
                else:
                    hff, aff, h2hf = st.session_state[fk]
                st.session_state["live_matches"][lid] = {"match": lm, "hf": hff, "af": aff, "h2h": h2hf}

    if live_analyze_all_btn and st.session_state["live_matches"]:
        total = len(st.session_state["live_matches"])
        bar   = st.progress(0)
        for idx, (lid, ld) in enumerate(st.session_state["live_matches"].items()):
            lm   = ld["match"]
            lhn  = lm["homeTeam"]["name"]
            lan  = lm["awayTeam"]["name"]
            lhsc = lm.get("score",{}).get("fullTime",{}).get("home") or 0
            lasc = lm.get("score",{}).get("fullTime",{}).get("away") or 0
            ht_h = lm.get("score",{}).get("halfTime",{}).get("home") or 0
            ht_a = lm.get("score",{}).get("halfTime",{}).get("away") or 0
            try:
                minute_int = calc_live_minute(lm)
            except:
                minute_int = 45
            bar.progress((idx) / total, text=f"({idx+1}/{total}) {lhn} – {lan}")
            ss_ev, ss_raw = fetch_sofascore_live_event(lhn, lan)
            lstats = parse_live_stats(ss_raw)
            lp_    = calc_live_goal_probability(lstats, minute_int, lhsc, lasc, ld["hf"], ld["af"], league_code=live_league if live_league != "Tüm Ligler" else None)
            prompt = build_live_prompt(lhn, lan, minute_int, lhsc, lasc, ht_h, ht_a, lstats, lp_, ld["hf"], ld["af"], ld["h2h"])
            st.session_state["live_analyses"][lid] = groq_call(prompt)
            if idx < total - 1:
                time.sleep(5)
        bar.progress(1.0); time.sleep(.3); bar.empty()
        st.success("✅ Tüm analizler hazır!")
        st.rerun()

    if not st.session_state["live_matches"]:
        st.markdown("""
<div style="background:#0d1829;border:1px solid #1c2e44;border-radius:10px;
padding:2rem;text-align:center;color:#4a6880;font-size:.82rem">
  🔴 <b style="color:#d0dce8">Canlı Maçları Çek</b> butonuna bas, ardından <b style="color:#d0dce8">Tümünü Analiz Et</b>
</div>""", unsafe_allow_html=True)
    else:
        def _confidence_score(analysis_text):
            if not analysis_text: return 0
            import re as _re
            vals = _re.findall(r'GÜVENİLİRLİK\s*:\s*(\w+)', analysis_text, _re.I)
            score = 0
            for v in vals:
                v = v.upper()
                if "YÜKSEK" in v: score += 3
                elif "ORTA"  in v: score += 2
                elif "DÜŞÜK" in v: score += 1
            return score

        sorted_matches = sorted(
            st.session_state["live_matches"].items(),
            key=lambda x: _confidence_score(st.session_state["live_analyses"].get(x[0], "")),
            reverse=True
        )

        all_picks = []
        for lid, ld in sorted_matches:
            lm_   = ld["match"]
            lhsc_ = lm_.get("score",{}).get("fullTime",{}).get("home") or 0
            lasc_ = lm_.get("score",{}).get("fullTime",{}).get("away") or 0
            min_  = calc_live_minute(lm_)
            ss_ev_, ss_raw_ = fetch_sofascore_live_event(lm_["homeTeam"]["name"], lm_["awayTeam"]["name"])
            lstat_ = parse_live_stats(ss_raw_)
            lc_    = live_league if live_league != "Tüm Ligler" else None
            lp_    = calc_live_goal_probability(lstat_, min_, lhsc_, lasc_, ld["hf"], ld["af"], league_code=lc_)
            _sk=FD_TO_ODDSAPI_SPORT.get(lc_ or "","")
            _lo=get_live_match_odds(ODDS_API_KEY_DEFAULT,_sk,lm_["homeTeam"]["name"],lm_["awayTeam"]["name"]) if _sk else None
            match_bets = _get_all_bets(lp_, lm_["homeTeam"]["name"], lm_["awayTeam"]["name"],
                                        lhsc_, lasc_, ld["hf"], ld["af"], league_code=lc_, live_odds=_lo)
            for bp in match_bets[:2]:
                all_picks.append({
                    "lid": lid, "lm": lm_, "lp": lp_,
                    "match": f"{lm_['homeTeam']['name']} vs {lm_['awayTeam']['name']}",
                    "score": f"{lhsc_}–{lasc_}",
                    "minute": min_,
                    **bp
                })

        all_picks.sort(key=lambda x: (-x["prob"], x["priority"]))
        top_pick = all_picks[0] if all_picks else None

        if top_pick:
            banner_items = all_picks[:4]
            items_html = ""
            for i, bp in enumerate(banner_items):
                prob_color = "#3ecf7a" if bp["prob"] >= 75 else "#f5a623"
                border_color = "#3ecf7a" if i == 0 else "#1c2e44"
                bg_color = "#04180a" if i == 0 else "#0d1829"
                items_html += f"""
<div style="background:{bg_color};border:1px solid {border_color};border-radius:9px;
padding:.7rem 1rem;display:flex;align-items:center;gap:10px">
  <div style="flex:1">
    <div style="font-size:.9rem;font-weight:800;color:#d0dce8;
    font-family:JetBrains Mono,monospace">{bp['market']}</div>
    <div style="font-size:.62rem;color:#4a6880;margin-top:2px">
      {bp['match']} · {bp['score']} · {bp['minute']}'
    </div>
    <div style="font-size:.62rem;color:#7a9ab8;margin-top:1px">{bp.get('why','')}</div>
  </div>
  <div style="background:{prob_color};color:#04180a;font-size:.72rem;font-weight:800;
  padding:4px 10px;border-radius:5px;white-space:nowrap">%{bp['prob']:.0f}</div>
</div>"""

            st.markdown(f"""
<div style="background:#09101e;border:2px solid #3ecf7a;border-radius:12px;
padding:1rem 1.2rem;margin-bottom:1rem">
  <div style="font-size:.56rem;font-weight:800;letter-spacing:.15em;color:#3ecf7a;
  text-transform:uppercase;margin-bottom:8px;display:flex;align-items:center;gap:6px">
    🏆 ŞİMDİ AL — Aktif Canlı Tavsiyeler (Olasılığa Göre Sıralı)
  </div>
  <div style="display:flex;flex-direction:column;gap:6px">
    {items_html}
  </div>
</div>""", unsafe_allow_html=True)

        for lid, ld in sorted_matches:
            lm   = ld["match"]
            lhn  = lm["homeTeam"]["name"]
            lan  = lm["awayTeam"]["name"]
            lhsc = lm.get("score",{}).get("fullTime",{}).get("home") or 0
            lasc = lm.get("score",{}).get("fullTime",{}).get("away") or 0
            lmin = calc_live_minute(lm)
            done = lid in st.session_state["live_analyses"]
            cscore = _confidence_score(st.session_state["live_analyses"].get(lid,""))

            conf_badge = "🟢 YÜKSEK" if cscore >= 6 else ("🟡 ORTA" if cscore >= 3 else ("🔴 DÜŞÜK" if done else ""))

            with st.expander(
                f"🔴 {lhn} {lhsc}–{lasc} {lan}  ·  {lmin}'  {conf_badge}",
                expanded=True
            ):
                ss_ev, ss_raw = fetch_sofascore_live_event(lhn, lan)
                live_stats    = parse_live_stats(ss_raw)

                try:
                    minute_int = _safe_minute(lmin)
                except:
                    minute_int = 45

                ht_h = lm.get("score",{}).get("halfTime",{}).get("home") or 0
                ht_a = lm.get("score",{}).get("halfTime",{}).get("away") or 0

                lp = calc_live_goal_probability(live_stats, minute_int, lhsc, lasc, ld["hf"], ld["af"], league_code=live_league if live_league != "Tüm Ligler" else None)

                if done:
                    atxt = st.session_state["live_analyses"][lid]

                    lc_tmp = live_league if live_league != "Tüm Ligler" else None
                    auto_pick = auto_best_bet(lp, lhn, lan, lhsc, lasc, ld["hf"], ld["af"], league_code=lc_tmp)
                    groq_pick = _extract_simdi_al(atxt)
                    if groq_pick and groq_pick.get("market"):
                        if auto_pick and auto_pick["market"] != groq_pick["market"]:
                            st.markdown(f"""
<div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-bottom:.6rem">
  <div style="background:#04180a;border:1px solid #3ecf7a;border-radius:8px;padding:.55rem .9rem">
    <div style="font-size:.5rem;color:#3ecf7a;font-weight:700;text-transform:uppercase;margin-bottom:2px">📊 Model</div>
    <div style="font-size:.85rem;font-weight:800;color:#d0dce8;font-family:JetBrains Mono,monospace">{auto_pick['market']}</div>
    <div style="font-size:.6rem;color:#4a6880">%{auto_pick['prob']:.0f} · {auto_pick.get('why','')[:50]}</div>
  </div>
  <div style="background:#060f20;border:1px solid #1d4ed8;border-radius:8px;padding:.55rem .9rem">
    <div style="font-size:.5rem;color:#4c9eff;font-weight:700;text-transform:uppercase;margin-bottom:2px">🤖 AI</div>
    <div style="font-size:.85rem;font-weight:800;color:#d0dce8;font-family:JetBrains Mono,monospace">{groq_pick['market']}</div>
    <div style="font-size:.6rem;color:#4a6880">{groq_pick.get('why','')[:60]}</div>
  </div>
</div>""", unsafe_allow_html=True)
                    lc_tmp2 = live_league if live_league != "Tüm Ligler" else None
                    _sk2=FD_TO_ODDSAPI_SPORT.get(lc_tmp2 or "","")
                    _lo2=get_live_match_odds(ODDS_API_KEY_DEFAULT,_sk2,lhn,lan) if _sk2 else None
                    all_auto = _get_all_bets(lp, lhn, lan, lhsc, lasc, ld["hf"], ld["af"], league_code=lc_tmp2, live_odds=_lo2)
                    if all_auto:
                        rows_html = ""
                        for bp in all_auto[:5]:
                            pc = bp["prob"]
                            pcolor = "#3ecf7a" if pc >= 72 else ("#f5a623" if pc >= 58 else "#a8c4d8")
                            rows_html += (
                                f'<div style="display:flex;align-items:center;gap:8px;'
                                f'padding:5px 0;border-bottom:1px solid #1c2e44">'
                                f'<div style="font-size:.82rem;font-weight:700;color:#d0dce8;'
                                f'font-family:JetBrains Mono,monospace;flex:1">{bp["market"]}</div>'
                                f'<div style="font-size:.66rem;color:#4a6880;flex:2">{bp.get("why","")}</div>'
                                f'<div style="background:{pcolor};color:#04180a;font-size:.72rem;'
                                f'font-weight:800;padding:3px 10px;border-radius:4px;white-space:nowrap">'
                                f'%{pc:.0f}</div></div>'
                            )
                        st.markdown(
                            f'<div style="background:#09101e;border:1px solid #1c2e44;'
                            f'border-radius:8px;padding:.7rem 1rem;margin-bottom:.6rem">'
                            f'<div style="font-size:.54rem;font-weight:700;letter-spacing:.12em;'
                            f'text-transform:uppercase;color:#4a6880;margin-bottom:6px">'
                            f'🎯 Tavsiyeler — Olasılığa Göre</div>'
                            + rows_html + '</div>',
                            unsafe_allow_html=True
                        )
                    elif auto_pick:
                        st.markdown(f"""
<div style="background:#04180a;border:1px solid #3ecf7a;border-radius:8px;
padding:.6rem 1rem;margin-bottom:.6rem;display:flex;align-items:center;gap:10px">
  <span style="font-size:.56rem;font-weight:800;letter-spacing:.12em;color:#3ecf7a;text-transform:uppercase">ŞİMDİ AL</span>
  <span style="font-size:.9rem;font-weight:800;color:#d0dce8;font-family:JetBrains Mono,monospace">{auto_pick['market']}</span>
  <span style="font-size:.68rem;color:#4a6880;flex:1">{auto_pick.get('why','')}</span>
  <span style="background:#3ecf7a;color:#04180a;font-size:.68rem;font-weight:800;padding:3px 9px;border-radius:4px">%{auto_pick['prob']:.0f}</span>
</div>""", unsafe_allow_html=True)

                    render_live_match(lm, live_stats, lp, atxt, ld["hf"], ld["af"], ld["h2h"])

                    if st.button("🔄 Güncelle", key=f"live_upd_{lid}", use_container_width=False):
                        with st.spinner("🦙 Güncelleniyor..."):
                            prompt = build_live_prompt(lhn, lan, minute_int, lhsc, lasc, ht_h, ht_a,
                                                       live_stats, lp, ld["hf"], ld["af"], ld["h2h"])
                            st.session_state["live_analyses"][lid] = groq_call(prompt)
                        st.rerun()
                else:
                    ca, cb = st.columns([4,1])
                    with ca:
                        st.caption(
                            f"xG: {lhn} {live_stats.get('xg_h',0):.2f}–{live_stats.get('xg_a',0):.2f} {lan}  |  "
                            f"Teh.Atak: {int(live_stats.get('dangerous_h',0))}–{int(live_stats.get('dangerous_a',0))}  |  "
                            f"Bkl.Ek Gol: {lp['expected_remaining']}  |  "
                            f"2.5 Üst: %{lp.get('o25',0)}"
                        )
                    with cb:
                        if st.button("🤖 Analiz", key=f"live_btn_{lid}", type="primary", use_container_width=True):
                            with st.spinner("🦙 Analiz ediliyor..."):
                                prompt = build_live_prompt(lhn, lan, minute_int, lhsc, lasc, ht_h, ht_a,
                                                           live_stats, lp, ld["hf"], ld["af"], ld["h2h"])
                                st.session_state["live_analyses"][lid] = groq_call(prompt)
                            st.rerun()

    if live_auto:
        time.sleep(58)
        st.rerun()

    st.stop()

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
        st.error(f"**{sel_date:%d.%m.%Y} · {sel_label}** için planlanmış maç bulunamadı.")
        st.stop()
    st.session_state.matches=matches
    st.session_state.mdata={}
    st.session_state.analyses={}
    st.success(f"✅ {len(matches)} maç!")
    with st.spinner("📊 Lig verileri..."):
        standings=api_standings(sel_code)
        scorers=api_scorers(sel_code)
        time.sleep(0.5)
    bar=st.progress(0)
    for i,m in enumerate(matches):
        mid=m["id"]
        hid=m["homeTeam"]["id"]
        aid=m["awayTeam"]["id"]
        hn=m["homeTeam"]["name"]
        an=m["awayTeam"]["name"]
        bar.progress(i/len(matches),text=f"({i+1}/{len(matches)}) {hn} – {an}")
        hf=parse_form(api_team_matches(hid,n_form),hid)
        af=parse_form(api_team_matches(aid,n_form),aid)
        time.sleep(0.4)
        h2h=parse_h2h(api_h2h(mid,n_h2h),hid)
        time.sleep(0.4)
        h_s=find_standing(standings,hid)
        a_s=find_standing(standings,aid)
        h_sc=find_scorer(scorers,hid)
        a_sc=find_scorer(scorers,aid)
        hxg=calc_xg(hf,af,True)
        axg=calc_xg(af,hf,False)
        h_htxg=calc_ht_xg(hf,hxg)
        a_htxg=calc_ht_xg(af,axg)
        ms_mat=score_mat(hxg,axg)
        ht_mat=score_mat(h_htxg,a_htxg,mx=4)
        stats=compute_stats(ms_mat,ht_mat)
        top_ms=sorted(ms_mat.items(),key=lambda x:-x[1])[:12]
        top_ht=sorted(ht_mat.items(),key=lambda x:-x[1])[:6]
        oa = None
        matched_odds = None
        if auto_odds:
            _match_date = m.get("utcDate","")[:10]
            matched_odds = get_match_odds(
                sel_code, odds_api_key, hn, an, auto_odds,
                match_date=_match_date,
                af_key=apifootball_key
            )

        if matched_odds:
            oa = analyze_odds(
                matched_odds["o1"], matched_odds["ox"], matched_odds["o2"],
                stats, hn, an
            )
            if matched_odds.get("o25_ov"):
                oa["o25_ov"] = matched_odds["o25_ov"]
                oa["o25_un"] = matched_odds.get("o25_un")
            oa["_source"] = matched_odds.get("source","?")
        elif use_manual_odds and manual_o1:
            oa = analyze_odds(manual_o1, manual_ox, manual_o2, stats, hn, an)
            oa["_source"] = "manuel"
        else:
            est = estimate_odds_with_groq(hn, an, stats, hf, af, h2h, h_s, a_s)
            if est:
                oa = analyze_odds(est["o1"], est["ox"], est["o2"], stats, hn, an)
                oa["_source"] = est["source"]

        pattern_data = None
        _couk = FD_ORG_TO_COUK.get(sel_code)
        if _couk and oa:
            o1_v = oa["o1"]
            ox_v = oa["ox"]
            o2_v = oa["o2"]
            pattern_data, total_rows = auto_pattern_search(
                _couk, o1_v, ox_v, o2_v,
                n_seasons=n_seasons, tol=tolerance
            )

        prompt = build_prompt(hn,an,hf,af,h2h,hxg,axg,h_htxg,a_htxg,
                              stats,h_s,a_s,h_sc,a_sc,top_ms,top_ht,
                              odds_analysis=oa)

        st.session_state.mdata[mid]={
            "match":m,"prompt":prompt,"hf":hf,"af":af,"h2h":h2h,
            "hxg":hxg,"axg":axg,"h_htxg":h_htxg,"a_htxg":a_htxg,
            "stats":stats,"top_ms":top_ms,"top_ht":top_ht,
            "h_stand":h_s,"a_stand":a_s,"h_sc":h_sc,"a_sc":a_sc,
            "odds_analysis":oa,
            "pattern_data":pattern_data,
        }
    bar.progress(1.0)
    time.sleep(0.3)
    bar.empty()
    st.success("✅ Veriler hazır! Analiz için maç seç.")

# ══════════════════════════════════════════════════════════════════
# TOPLU ANALİZ
# ══════════════════════════════════════════════════════════════════
if all_btn:
    if not st.session_state.mdata:
        st.warning("Önce Maçları Çek!")
    else:
        items=list(st.session_state.mdata.items())
        bar2=st.progress(0)
        for i,(mid,d) in enumerate(items):
            hn=d["match"]["homeTeam"]["name"]
            an=d["match"]["awayTeam"]["name"]
            bar2.progress(i/len(items),text=f"({i+1}/{len(items)}) {hn}–{an}")
            result = groq_call(d["prompt"])
            st.session_state.analyses[mid] = result
            if i < len(items) - 1:
                time.sleep(8)
        bar2.progress(1.0)
        time.sleep(0.3)
        bar2.empty()
        st.success("✅ Tümü tamamlandı!")

# ══════════════════════════════════════════════════════════════════
# MAÇ LİSTESİ
# ══════════════════════════════════════════════════════════════════
if st.session_state.matches:
    st.markdown(f"### ⚽ {len(st.session_state.matches)} Maç · {sel_date.strftime('%d.%m.%Y')}")
    for m in st.session_state.matches:
        mid=m["id"]
        hn=m["homeTeam"]["name"]
        an=m["awayTeam"]["name"]
        utc=m.get("utcDate","")[:16].replace("T"," ")
        done=mid in st.session_state.analyses
        d=st.session_state.mdata.get(mid,{})
        _odds_chip = \"\"
        _d_oa = st.session_state.mdata.get(mid,{}).get(\"odds_analysis\")
        if _d_oa:
            _src = _d_oa.get(\"_source\",\"\")
            _is_real  = \"Bet365\" in _src or \"football-data\" in _src or _src == \"manuel\"
            _is_est   = \"groq\" in _src.lower() or \"model\" in _src.lower()
            _src_icon = (\"🟢\" if \"Bet365\" in _src
                        else \"📊\" if \"football-data\" in _src
                        else \"✏️\" if _src == \"manuel\"
                        else \"⚠️\")
            _src_label = (_src if _is_real
                          else \"TAHMİN — gerçek oran yok\")
            _chip_color = \"#3ecf7a\" if \"Bet365\" in _src else \"#f5a623\" if _is_est else \"#4c9eff\"
            _odds_chip = f' · {_src_icon} <span style=\"color:{_chip_color}\">1:{_d_oa[\"o1\"]} X:{_d_oa[\"ox\"]} 2:{_d_oa[\"o2\"]}</span> <span style=\"color:#4a6880;font-size:.7em\">({_src_label})</span>'
        with st.expander(f\"{'✅' if done else '🔴'}  {hn}  vs  {an}  ·  {utc[11:16]}\"):
            if d:
                hxg = d.get(\"hxg\",0)
                axg = d.get(\"axg\",0)
                hf  = d.get(\"hf\",{})
                af  = d.get(\"af\",{})
                h2  = d.get(\"h2h\",{})
                oa  = d.get(\"odds_analysis\")
                pd_ = d.get(\"pattern_data\")

                if oa:
                    _src      = oa.get(\"_source\",\"\")
                    _is_est   = \"groq\" in _src.lower() or \"model\" in _src.lower()
                    _src_icon = \"🟢 Bet365\" if \"Bet365\" in _src else (\"📊 fdco.uk\" if \"football-data\" in _src else (\"✏️ Manuel\" if _src==\"manuel\" else \"⚠️ TAHMİN\"))
                    _warn_txt = ' <span style=\"color:#f5a623;font-weight:700\">⚠️ Gerçek oran yok — bu oranlar model tahminidir</span>' if _is_est else ''
                    odds_txt = (f' &nbsp;·&nbsp; <b style=\"color:#f5a623\">1:{oa[\"o1\"]} X:{oa[\"ox\"]} 2:{oa[\"o2\"]}</b>'
                                f' <span style=\"color:#4a6880;font-size:.85em\">({_src_icon})</span>{_warn_txt}')
                else:
                    odds_txt = ' &nbsp;·&nbsp; <span style=\"color:#4a6880\">Oran çekilemedi</span>'
                st.markdown(
                    f'<div style=\"font-size:.75rem;color:#4a6880;padding:6px 0;border-bottom:1px solid #1c2e44;margin-bottom:8px\">'
                    f'xG: <b style=\"color:#4c9eff\">{hxg}</b>–<b style=\"color:#ff7070\">{axg}</b>'
                    f' &nbsp;·&nbsp; {hn}: <b style=\"color:#a8c4d8\">{hf.get(\"form_str\",\"?\") if hf else \"?\"}</b>'
                    f' &nbsp;·&nbsp; {an}: <b style=\"color:#a8c4d8\">{af.get(\"form_str\",\"?\") if af else \"?\"}</b>'
                    f' &nbsp;·&nbsp; H2H: {h2.get(\"hw\",0)}G-{h2.get(\"dr\",0)}B-{h2.get(\"aw\",0)}M'
                    f'{odds_txt}</div>', unsafe_allow_html=True)

                if oa:
                    render_odds_panel(oa, hn, an, d.get(\"stats\",{}))

                if pd_ and oa:
                    render_pattern_panel(pd_, oa.get(\"o1\",0), oa.get(\"ox\",0), oa.get(\"o2\",0), hn, an,
                                         odds_source=oa.get(\"_source\",\"football-data.co.uk\"))
                elif not oa:
                    st.info(\"💡 Oran verisi bulunamadı. Lig fixtures.csv'de bu maç yoksa sonraki hafta güncellenir.\")

                if not done:
                    if st.button(\"🤖 Analiz Et\", key=f\"btn_{mid}\", type=\"primary\"):
                        with st.spinner(f\"🦙 Groq: {hn}–{an}...\"):
                            st.session_state.analyses[mid] = groq_call(d[\"prompt\"])
                        st.rerun()
                else:
                    try:
                        render_vs_ui(
                            d[\"match\"],d[\"hf\"],d[\"af\"],d[\"h2h\"],
                            d[\"hxg\"],d[\"axg\"],d[\"h_htxg\"],d[\"a_htxg\"],
                            d[\"stats\"],d[\"top_ms\"],d[\"top_ht\"],
                            d[\"h_stand\"],d[\"a_stand\"],d[\"h_sc\"],d[\"a_sc\"],
                            st.session_state.analyses[mid],
                            odds_analysis=oa,
                        )
                    except Exception as _e:
                        st.error(f\"UI render hatası: {_e}\")
                        st.markdown(
                            f'<div style=\"background:#060d1c;border:1px solid #1a2e4a;border-radius:10px;'
                            f'padding:1.2rem;font-size:.83rem;color:#c0cfe0;white-space:pre-wrap;'
                            f'max-height:600px;overflow-y:auto;font-family:monospace\">'
                            f'{st.session_state.analyses[mid]}</div>',
                            unsafe_allow_html=True
                        )
else:
    st.markdown(\"\"\"
<div style=\"background:#0a1628;border:1px solid #0f2a45;border-radius:14px;padding:1.5rem 1.8rem\">
  <div style=\"font-size:.7rem;color:#1a3050;font-weight:700;letter-spacing:.12em;
  text-transform:uppercase;margin-bottom:10px\">🚀 BAŞLAMAK İÇİN</div>
  <div style=\"font-size:.85rem;color:#3a5570;line-height:2.2\">
    1. Sol sidebar'dan <b style=\"color:#c0cfe0\">Kategori</b> → <b style=\"color:#c0cfe0\">Lig</b> seç<br>
    2. <b style=\"color:#c0cfe0\">Tarih</b> seç (maçların olduğu bir gün)<br>
    3. <b style=\"color:#00e5a0\">🔍 Maçları Çek</b> butonuna bas<br>
    4. Maçı aç → <b style=\"color:#00e5a0\">🤖 Analiz Et</b><br>
    5. Profesyonel VS karşılaştırma arayüzü açılır
  </div>
  <div style=\"font-size:.68rem;color:#1a3050;margin-top:14px\">
    ✅ API key'ler hazır · football-data.org + Groq Llama 3.3 70B
  </div>
</div>
\"\"\", unsafe_allow_html=True)
