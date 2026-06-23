# -*- coding: utf-8 -*-
"""Monkeypatch matplotlib so every saved PNG also gets a Turkish-labelled twin '<name>_tr.png'.
Translation is ordered substring replacement (longest English phrase first), so dynamic titles that
embed numbers keep their numbers while the words around them are translated. One sim run -> EN + TR."""
import os
import matplotlib.text as mtext
from matplotlib.figure import Figure

PAIRS = [
    # --- full titles / long phrases (matched first) ---
    ("Field as actuator: open-loop over-steers, closed-loop control balances", "Alan-aktüatör: açık-döngü aşırı yönlendirir, kapalı-döngü dengeler"),
    ("Naive over-steers (→1); closed-loop balances (→.5)", "Naif aşırı yönlendirir (→1); kapalı-döngü dengeler (→.5)"),
    ("Steering: far-exit usage", "Yönlendirme: uzak kapı kullanımı"),
    ("Safe capacity vs door design & prevention", "Güvenli kapasite — kapı tasarımı ve önleme"),
    ("(where each curve crosses the limit = max safe occupancy)", "(her eğrinin limiti kestiği yer = max güvenli doluluk)"),
    ("Case study — Itaewon-type alley: counter-flow gridlock at a choke, and the fix that works", "Vaka — İtaewon-tipi sokak: darboğazda karşıt-akış kilidi ve işe yarayan çözüm"),
    ("Communication-free affective coordination (NearFar)", "İletişimsiz duygusal koordinasyon (NearFar)"),
    ("Crush-density: the lethal limit (peak crowding vs occupancy & door design)", "Ezilme-yoğunluğu: ölümcül sınır (pik yoğunluk — doluluk ve kapı tasarımına göre)"),
    ("Force-based crush: pressure is the lethal observable, not static density", "Kuvvet-tabanlı ezilme: ölümcül gösterge basınçtır, statik yoğunluk değil"),
    ("Crowd PRESSURE keeps rising (crush risk)", "Kalabalık BASINCI yükselmeye devam eder (ezilme riski)"),
    ("Static density saturates (under-predicts danger)", "Statik yoğunluk doygunlaşır (tehlikeyi az gösterir)"),
    ("peak crowd pressure (density × vel-variance)", "pik kalabalık basıncı (yoğunluk × hız-varyansı)"),
    ("Dual-process arbitration at the decision level (NearFar)", "Karar seviyesinde çift-süreç harmanlama (NearFar)"),
    ("Deliberation routes the crowd to the far exit", "Düşünme, kalabalığı uzak kapıya yönlendirir"),
    ("Decision gate has a LARGE footprint", "Karar kapısının etkisi BÜYÜK"),
    ("0=reactive nearest, 1=deliberative field-aware", "0=refleks en-yakın, 1=düşünerek alan-farkında"),
    ("Critical slowing down: ensemble susceptibility rises into the panic tip", "Kritik yavaşlama: topluluk duyarlılığı panik devrilmesine doğru yükselir"),
    ("ensemble susceptibility (norm.)", "topluluk duyarlılığı (norm.)"),
    ("lag-1 autocorrelation", "lag-1 otokorelasyon"),
    ("early-warning indicators", "erken-uyarı göstergeleri"),
    ("order parameter $M$ (mean load)", "düzen parametresi $M$ (ortalama yük)"),
    ("Fundamental diagram (2D python)", "Temel diyagram"),
    ("Mean-field theory reproduces the panic transition curve", "Ortalama-alan teorisi panik geçiş eğrisini üretir"),
    ("mean affective load $M$ (order parameter)", "ortalama duygusal yük $M$ (düzen parametresi)"),
    ("field→affect gain (control parameter)", "alan→duygu kazancı (kontrol parametresi)"),
    ("A genuine fold: the panic transition shows hysteresis (path dependence)", "Gerçek bir kıvrım: panik geçişi histerezis gösterir (yol bağımlılığı)"),
    ("gain ↑ : crowd tips to panic late", "kazanç ↑ : kalabalık geç paniğe geçer"),
    ("gain ↓ : crowd recovers late", "kazanç ↓ : kalabalık geç toparlanır"),
    ("hysteresis loop (area ≈", "histerezis çevrimi (alan ≈"),
    ("Early-warning-triggered intervention averts the panic transition", "Erken-uyarı tetikli müdahale panik geçişini önler"),
    ("early-warning intervention → averted", "erken-uyarı müdahalesi → önlendi"),
    ("no intervention → panic", "müdahale yok → panik"),
    ("panic level $M$ (mean affective load)", "panik düzeyi $M$ (ortalama duygusal yük)"),
    ("Collective panic phase transition (2D python)", "Kolektif panik faz geçişi"),
    ("feedback gain: calm->panic", "geri-besleme kazancı: sakin→panik"),
    ("density: calm->panic", "yoğunluk: sakin→panik"),
    ("Real-architecture test — Itaewon 2022 alley: model reproduces the counter-flow crush in the middle", "Gerçek-mimari testi — İtaewon 2022 sokağı: model karşıt-akış ezilmesini ortada üretir"),
    ("Precision gate: defer from stalled physics -> fewer stuck-states", "Kesinlik kapısı: takılan fizikten devret → daha az sıkışma"),
    ("Stuck-states over time", "Zamanla sıkışma"),
    ("mean stuck fraction", "ortalama sıkışma oranı"),
    ("Mean stuck-states (", "Ortalama sıkışma ("),
    ("stuck fraction", "sıkışma oranı"),
    ("precision gate", "kesinlik kapısı"),
    ("no gate", "kapı yok"),
    ("affect-gated (reflex+deliberation)", "duygu-kapılı (refleks+düşünme)"),
    ("physics only (reflex)", "yalnız fizik (refleks)"),
    ("crowd size N (counter-flow)", "kalabalık N (karşıt-akış)"),
    ("extra people evacuated (gate − physics)", "ek tahliye (kapı − fizik)"),
    ("Gate − physics by crowd size (helps in most deadlock cases)", "Kapı − fizik (çoğu kilitlenmede yardımcı)"),
    ("Evacuated vs crowd size", "Tahliye — kalabalık boyutuna göre"),
    ("uncertainty-gated arbitration is a robustness mechanism — it pays off when reflex deadlocks", "belirsizlik-kapılı harmanlama bir sağlamlık mekanizmasıdır — refleks kilitlendiğinde kazandırır"),
    ("crowd size N", "kalabalık N"),
    ("Held-out validation: model vs REAL raw Jülich bottleneck trajectories", "Ayrık doğrulama: model vs GERÇEK ham Jülich darboğaz verisi"),
    ("our model (held-out, RMSE", "modelimiz (ayrık, RMSE"),
    ("real data (binned median)", "gerçek veri (binlenmiş ortanca)"),
    ("Weidmann (calibration target)", "Weidmann (kalibrasyon hedefi)"),
    ("raw frames (Jülich)", "ham kareler (Jülich)"),
    ("Speed–density: model vs Weidmann (full range)", "Hız–yoğunluk: model vs Weidmann (tam aralık)"),
    ("Flow–density: capacity hump + jam", "Akış–yoğunluk: kapasite tepesi + kilitlenme"),
    ("Validation vs REAL measured data:", "Gerçek ölçülen veriye karşı doğrulama:"),
    ("FD matches Weidmann across free-flow", "FD Weidmann’a uyar (serbest-akış"),
    ("bottleneck 1.9 (Seyfried)", "darboğaz 1.9 (Seyfried)"),
    ("model specific flow", "model özgül akış"),
    ("model bottleneck", "model darboğaz"),
    ("Weidmann flow", "Weidmann akışı"),
    ("Weidmann (empirical)", "Weidmann (ampirik)"),
    ("Validation: door throughput vs the empirical band (RiMEA / Hermes)", "Doğrulama: kapı akışı vs ampirik band (RiMEA / Hermes)"),
    ("bottleneck specific flow (ped/m/s)", "darboğaz özgül akış (kişi/m/s)"),
    ("Heterogeneous crowds:", "Heterojen kalabalık:"),
    ("slow agents plug the bottleneck, costing egress disproportionately", "yavaş ajan darboğazı tıkar, boşalmayı orantısız yavaşlatır"),
    ("Sensitivity analysis: which parameters drive the predictions (tornado)", "Duyarlılık analizi: tahminleri hangi parametreler sürüyor (tornado)"),
    ("|Δ Moran's I| over ±40%", "|Δ Moran's I| (±%40 değişimde)"),
    ("|Δ egress| over ±40%", "|Δ tahliye| (±%40 değişimde)"),
    ("Sensitivity: field structure", "Duyarlılık: alan yapısı"),
    ("Sensitivity: egress", "Duyarlılık: tahliye"),
    ("Inverse design: best arrangement of a fixed", "Ters tasarım: sabit"),
    ("door budget (green = optimiser pick)", "kapı bütçesinin en iyi düzeni (yeşil = optimizatör seçimi)"),
    ("median clearance t50 (s)  — lower is safer", "ortanca boşalma t50 (s)  — düşük = daha güvenli"),
    ("median clearance t50 (s)", "ortanca boşalma t50 (s)"),
    ("median (50%) clearance time (s)", "ortanca (%50) boşalma süresi (s)"),
    ("occupancy (number of people)", "doluluk (kişi sayısı)"),
    ("peak local density (ped/m²)", "pik yerel yoğunluk (kişi/m²)"),
    ("peak density (ped/m²)", "pik yoğunluk (kişi/m²)"),
    ("Agent-drain: field persists, decays at", "Alan-özerkliği: alan kalır, sönüm hızı"),
    ("affect-field mean", "duygu-alanı ortalaması"),
    ("all agents removed", "tüm ajanlar silindi"),
    ("max-exit share (1=imbalanced, .5=balanced)", "en-dolu kapı payı (1=dengesiz, .5=dengeli)"),
    ("max-exit share (lower=balanced)", "en-dolu kapı payı (düşük=dengeli)"),
    ("max-exit share (1=imbalanced)", "en-dolu kapı payı (1=dengesiz)"),
    ("far (wasted) exit usage", "uzak (atıl) kapı kullanımı"),
    ("far-exit usage", "uzak kapı kullanımı"),
    ("mean-field theory", "ortalama-alan teorisi"),
    ("agent simulation", "ajan simülasyonu"),
    ("transition (gain≈", "geçiş (kazanç≈"),
    ("feedback gain", "geri-besleme kazancı"),
    ("panic level", "panik düzeyi"),
    ("Egress time", "Boşalma süresi"),
    ("Throughput", "Akış kapasitesi"),
    ("door width", "kapı genişliği"),
    ("wall (obstacle)", "duvar (engel)"),
    ("speed--density", "hız–yoğunluk"),
    ("flow--density", "akış–yoğunluk"),
    ("Fundamental diagram", "Temel diyagram"),
    ("evacuated in", "tahliye —"),
    ("decision gate", "karar kapısı"),
    ("clamped", "sabitlenmiş"),
    ("affect-gated", "duygu-kapılı"),
    ("field mean", "alan ortalaması"),
    ("tipping", "devrilme"),
    ("empirical", "ampirik"),
    # --- common axis labels / units (matched last) ---
    ("density (ped/m$^2$)", "yoğunluk (kişi/m$^2$)"),
    ("density (ped/m²)", "yoğunluk (kişi/m²)"),
    ("specific flow (ped/m/s)", "özgül akış (kişi/m/s)"),
    ("flow (ped/m/s)", "akış (kişi/m/s)"),
    ("speed (m/s)", "hız (m/s)"),
    ("time (s)", "zaman (s)"),
    ("occupancy", "doluluk"),
    ("(of ", "(/ "),
]
PAIRS.sort(key=lambda p: -len(p[0]))


def _tr(s):
    for en, tr in PAIRS:
        if en in s:
            s = s.replace(en, tr)
    return s


_orig = Figure.savefig


def _patched(self, fname, *a, **k):
    _orig(self, fname, *a, **k)
    try:
        name = os.fspath(fname)
    except TypeError:
        return
    if not isinstance(name, str) or not name.lower().endswith(".png"):
        return
    saved = []
    for t in self.findobj(mtext.Text):
        s = t.get_text()
        ns = _tr(s)
        if ns != s:
            saved.append((t, s)); t.set_text(ns)
    if saved:
        _orig(self, name[:-4] + "_tr.png", *a, **k)
        for t, s in saved:
            t.set_text(s)


def install():
    Figure.savefig = _patched
    print("[figlang] bilingual savefig installed (EN + _tr.png)")
