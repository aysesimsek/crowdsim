#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build chapter.html as a polished bilingual ACADEMIC CHAPTER. Each figure carries a simple caption +
a professional 3-line box: Amaç (Aim) / Yöntem (Method, full parameters) / Bulgu (Result). Assumptions
are cited. Every text helper emits BOTH languages (balanced by construction). Run, then inline_figs.py."""
import os, sys
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
HERE = os.path.dirname(os.path.abspath(__file__))

def L(tr, en): return f'<span class="lang tr">{tr}</span><span class="lang en">{en}</span>'
def P(tr, en): return f'  <p>{L(tr, en)}</p>\n'
def LEAD(tr, en): return f'  <p class="lede">{L(tr, en)}</p>\n'
def H3(tr, en): return f'  <h3>{L(tr, en)}</h3>\n'
def NOTE(kind, htr, hen, tr, en): return f'  <div class="note {kind}"><h4>{L(htr,hen)}</h4><p>{L(tr,en)}</p></div>\n'
def CITE(*ns): return '<sup class="cite">' + ''.join(f'<a href="#R{n}">{n}</a>' for n in ns) + '</sup>'

SECTIONS = []
def SEC(sid, ey_tr, ey_en, t_tr, t_en, body):
    SECTIONS.append((sid, t_tr, t_en))
    return (f'<section id="{sid}"><div class="wrap">\n  <p class="eyebrow">{L(ey_tr,ey_en)}</p>\n'
            f'  <h2>{L(t_tr,t_en)}</h2>\n{body}</div></section>\n')

def FIG(src, alt, cap, aim, method, result):
    rows = [("Amaç", "Aim", aim), ("Yöntem", "Method", method), ("Bulgu", "Result", result)]
    body = ''.join(f'    <div class="row"><b>{L(a,b)}</b> {L(v[0],v[1])}</div>\n' for a,b,v in rows)
    tr = src[:-4] + "_tr.png"
    imgs = (f'<img class="figimg en" src="figures/{src}" alt="{alt}">'
            f'<img class="figimg tr" src="figures/{tr}" alt="{alt}">')
    return (f'  <figure class="figwrap">{imgs}\n'
            f'    <figcaption>{L(cap[0],cap[1])}</figcaption></figure>\n'
            f'  <div class="figexp">\n{body}  </div>\n')

REFS = [
 ("R1","Weidmann, U. (1993). <i>Transporttechnik der Fußgänger</i>. IVT, ETH Zürich.","Weidmann, U. (1993). <i>Transporttechnik der Fußgänger</i>. IVT, ETH Zürich."),
 ("R2","Helbing, D., Farkas, I., Vicsek, T. (2000). Simulating dynamical features of escape panic. <i>Nature</i> 407, 487–490.","Helbing, D., Farkas, I., Vicsek, T. (2000). Simulating dynamical features of escape panic. <i>Nature</i> 407, 487–490."),
 ("R3","Seyfried, A. et al. (2009). New insights into pedestrian flow through bottlenecks. <i>Transportation Science</i> 43(3). (arXiv physics/0702004)","Seyfried, A. et al. (2009). New insights into pedestrian flow through bottlenecks. <i>Transportation Science</i> 43(3). (arXiv physics/0702004)"),
 ("R4","Helbing, D., Johansson, A., Al-Abideen, H.Z. (2007). Dynamics of crowd disasters: an empirical study. <i>Phys. Rev. E</i> 75, 046109.","Helbing, D., Johansson, A., Al-Abideen, H.Z. (2007). Dynamics of crowd disasters: an empirical study. <i>Phys. Rev. E</i> 75, 046109."),
 ("R5","Helbing, D., Mukerji, P. (2012). Crowd disasters as systemic failures: the Love Parade disaster. <i>EPJ Data Science</i> 1:7.","Helbing, D., Mukerji, P. (2012). Crowd disasters as systemic failures: the Love Parade disaster. <i>EPJ Data Science</i> 1:7."),
 ("R6","Moran, P.A.P. (1950). Notes on continuous stochastic phenomena. <i>Biometrika</i> 37(1), 17–23.","Moran, P.A.P. (1950). Notes on continuous stochastic phenomena. <i>Biometrika</i> 37(1), 17–23."),
 ("R7","RiMEA e.V. (2016). <i>Guideline for Microscopic Evacuation Analysis</i> (RiMEA) 3.0.","RiMEA e.V. (2016). <i>Guideline for Microscopic Evacuation Analysis</i> (RiMEA) 3.0."),
 ("R8","Grassé, P.-P. (1959). La reconstruction du nid… la théorie de la stigmergie. <i>Insectes Sociaux</i> 6, 41–80.","Grassé, P.-P. (1959). La reconstruction du nid… la théorie de la stigmergie. <i>Insectes Sociaux</i> 6, 41–80."),
 ("R9","Friston, K. (2010). The free-energy principle: a unified brain theory? <i>Nat. Rev. Neurosci.</i> 11, 127–138.","Friston, K. (2010). The free-energy principle: a unified brain theory? <i>Nat. Rev. Neurosci.</i> 11, 127–138."),
 ("R10","Kahneman, D. (2011). <i>Thinking, Fast and Slow</i>. Farrar, Straus & Giroux.","Kahneman, D. (2011). <i>Thinking, Fast and Slow</i>. Farrar, Straus & Giroux."),
 ("R11","Scheffer, M. et al. (2009). Early-warning signals for critical transitions. <i>Nature</i> 461, 53–59.","Scheffer, M. et al. (2009). Early-warning signals for critical transitions. <i>Nature</i> 461, 53–59."),
 ("R12","Schadschneider, A., Seyfried, A. (2009). Empirical results for pedestrian dynamics… (arXiv 1007.4058)","Schadschneider, A., Seyfried, A. (2009). Empirical results for pedestrian dynamics… (arXiv 1007.4058)"),
 ("R13","Pedestrian Dynamics Data Archive, FZ Jülich / Univ. Wuppertal (2018). Bottleneck experiment. doi:10.34735/ped.2018.1.","Pedestrian Dynamics Data Archive, FZ Jülich / Univ. Wuppertal (2018). Bottleneck experiment. doi:10.34735/ped.2018.1."),
 ("R14","Seoul Halloween (Itaewon) crowd-crush reconstruction (2024). <i>PMC11244771</i>.","Seoul Halloween (Itaewon) crowd-crush reconstruction (2024). <i>PMC11244771</i>."),
 ("R15","Moussaïd, M., Helbing, D., Theraulaz, G. (2011). How simple rules determine pedestrian behavior and crowd disasters. <i>PNAS</i> 108(17).","Moussaïd, M., Helbing, D., Theraulaz, G. (2011). How simple rules determine pedestrian behavior and crowd disasters. <i>PNAS</i> 108(17)."),
 ("R16","Fruin, J.J. (1971/1993). <i>Pedestrian Planning and Design</i> & “The causes and prevention of crowd disasters.” — yoğunluk hizmet-seviyesi ve tehlike eşikleri.","Fruin, J.J. (1971/1993). <i>Pedestrian Planning and Design</i> & “The causes and prevention of crowd disasters.” — density level-of-service and danger thresholds."),
]

MECH_SVG = ('<div class="aid"><span class="aidbadge">' + L("Mekanizma şeması","Mechanism schematic") + '</span>'
 '<svg viewBox="0 0 760 188" xmlns="http://www.w3.org/2000/svg">'
 '<defs><marker id="m" markerWidth="9" markerHeight="9" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#0A5A62"/></marker></defs>'
 '<style>.bx{fill:#fff;stroke:#0E7C86;stroke-width:1.6}.tt{font:600 13px Inter,sans-serif;fill:#16242B}.ss{font:11.5px IBM Plex Mono,monospace;fill:#6B7C85}.ar{stroke:#0A5A62;stroke-width:1.8;fill:none;marker-end:url(#m)}</style>'
 '<rect class="bx" x="12" y="66" width="120" height="54" rx="10"/><text class="tt" x="72" y="89" text-anchor="middle">Birey</text><text class="ss" x="72" y="107" text-anchor="middle">stres yaşar</text>'
 '<path class="ar" d="M134 93 L184 93"/>'
 '<rect class="bx" x="186" y="66" width="124" height="54" rx="10"/><text class="tt" x="248" y="89" text-anchor="middle">İz bırak</text><text class="ss" x="248" y="107" text-anchor="middle">deposit (S)</text>'
 '<path class="ar" d="M312 93 L362 93"/>'
 '<rect class="bx" x="364" y="52" width="156" height="82" rx="10"/><text class="tt" x="442" y="80" text-anchor="middle">Duygu Alanı Φ</text><text class="ss" x="442" y="100" text-anchor="middle">yayıl + sön</text><text class="ss" x="442" y="118" text-anchor="middle">∂Φ/∂t=D∇²Φ−kΦ+S</text>'
 '<path class="ar" d="M522 93 L572 93"/>'
 '<rect class="bx" x="574" y="66" width="168" height="54" rx="10"/><text class="tt" x="658" y="89" text-anchor="middle">Oku → Karar ver</text><text class="ss" x="658" y="107" text-anchor="middle">yoğun kapıdan kaç</text>'
 '<path class="ar" d="M658 66 C658 18, 72 18, 72 62"/>'
 '<text class="ss" x="365" y="22" text-anchor="middle">konuşmadan, yalnız alanı sezerek — geri besleme döngüsü</text>'
 '</svg><div class="aidcap">' +
 L("Döngü: birey stres yaşar → ortama iz bırakır → iz yayılıp söner (reaksiyon-difüzyon) → diğerleri izi okuyup kararını değiştirir. Hiç doğrudan iletişim yok.",
   "Loop: a person feels stress → deposits a trace → it diffuses and decays (reaction–diffusion) → others read it and change their decision. No direct communication.") + '</div></div>\n')


ARCH_SVG = ('<div class="aid"><span class="aidbadge">' + L("Mimari — bileşenler nasıl birleşir","Architecture — how the components combine") + '</span>'
 '<svg viewBox="0 0 760 210" xmlns="http://www.w3.org/2000/svg">'
 '<defs><marker id="ma" markerWidth="9" markerHeight="9" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#0A5A62"/></marker></defs>'
 '<style>.b2{fill:#fff;stroke:#0E7C86;stroke-width:1.5}.g2{fill:#E6F0F1;stroke:#0A5A62;stroke-width:1.8}.p2{fill:#FBF1E1;stroke:#A8691F;stroke-width:1.5}.t2{font:600 12.5px Inter,sans-serif;fill:#16242B}.s2{font:11px IBM Plex Mono,monospace;fill:#6B7C85}.a2{stroke:#0A5A62;stroke-width:1.7;fill:none;marker-end:url(#ma)}</style>'
 '<rect class="b2" x="10" y="12" width="184" height="44" rx="9"/><text class="t2" x="102" y="31" text-anchor="middle">Sosyal-Kuvvet</text><text class="s2" x="102" y="47" text-anchor="middle">fizik · kuvvet ODE’leri</text>'
 '<rect class="b2" x="10" y="83" width="184" height="44" rx="9"/><text class="t2" x="102" y="102" text-anchor="middle">Duygu Alanı Φ</text><text class="s2" x="102" y="118" text-anchor="middle">reaksiyon-difüzyon PDE</text>'
 '<rect class="b2" x="10" y="154" width="184" height="44" rx="9"/><text class="t2" x="102" y="173" text-anchor="middle">Navigasyon</text><text class="s2" x="102" y="189" text-anchor="middle">Dijkstra rota</text>'
 '<rect class="g2" x="302" y="72" width="178" height="66" rx="10"/><text class="t2" x="391" y="96" text-anchor="middle">λ-kapı (harman)</text><text class="s2" x="391" y="114" text-anchor="middle">ivme = λ·fizik</text><text class="s2" x="391" y="129" text-anchor="middle">+ (1−λ)·PPO</text>'
 '<rect class="p2" x="302" y="162" width="178" height="40" rx="9"/><text class="t2" x="391" y="180" text-anchor="middle">PPO politikası</text><text class="s2" x="391" y="195" text-anchor="middle">paylaşımlı MLP · koşullu</text>'
 '<rect class="b2" x="566" y="82" width="184" height="46" rx="9"/><text class="t2" x="658" y="101" text-anchor="middle">İvme → hareket</text><text class="s2" x="658" y="117" text-anchor="middle">+ alana iz bırakır</text>'
 '<path class="a2" d="M194 34 C252 34, 250 92, 300 98"/>'
 '<path class="a2" d="M194 105 L300 105"/>'
 '<path class="a2" d="M194 176 C252 176, 250 124, 300 118"/>'
 '<path class="a2" d="M391 162 L391 140"/>'
 '<path class="a2" d="M480 105 L564 105"/>'
 '</svg><div class="aidcap">' +
 L("Üç fizik/algoritma bileşeni (solda) λ-kapısında harmanlanır; öğrenilmiş PPO düzeltmesi (altta, koşullu) aynı kapıya girer; çıktı ivmedir — ajan hareket eder ve alana yeni iz bırakır (geri besleme). λ = σ(stres): stres arttıkça refleks/öğrenme dengesi kayar.",
   "Three physics/algorithm components (left) are blended at a λ-gate; the learned PPO correction (bottom, conditional) enters the same gate; the output is acceleration — the agent moves and deposits new trace into the field (feedback). λ = σ(stress): stress shifts the reflex/learning balance.") + '</div></div>\n')


def main():
    H = ['<!doctype html><html data-lang="tr"><head><meta charset="utf-8">',
         '<meta name="viewport" content="width=device-width, initial-scale=1">',
         '<title>Stigmerjik Duygu Alanı ile Kalabalık Güvenliği</title>',
         '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>',
         '<link href="https://fonts.googleapis.com/css2?family=Spectral:ital,wght@0,400;0,600;0,700;1,400&family=Inter:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">',
         f'<style>{CSS}</style></head><body>',
         '<div id="progress"></div>',
         '<div id="langtoggle"><button data-set="tr" class="on">TR</button><button data-set="en">EN</button></div>',
         '<div class="shell"><nav aria-label="TOC"><div class="brand">Kalabalık Güvenliği<small>Stigmergic Affect Field</small></div>'
         f'<div class="sub">{L("Duygu-alanı temelli kalabalık modeli — gerçek veriyle doğrulanmış bir bölüm.","An affect-field crowd model — a chapter validated on real data.")}</div>'
         '<ol id="toc"></ol></nav><main>']

    H.append('<header class="hero"><div class="wrap">')
    H.append(f'<p class="eyebrow">{L("Doktora bölümü · kalabalık dinamiği","PhD chapter · crowd dynamics")}</p>')
    H.append(f'<h1>{L("Kalabalık güvenliği için bir “duygu alanı” modeli","An “affect field” model for crowd safety")}</h1>')
    H.append(f'<p class="tagline">{L("Mevcut modeller paniği ya yok sayar ya da kişiden-kişiye bulaşma sanır. Biz onu ortamda kalan, yayılıp sönen bir alan olarak modelliyor; gerçek insan deneyleriyle doğruluyor ve çalışan bir tasarım aracına çeviriyoruz.","Existing models either ignore panic or treat it as person-to-person contagion. We model it as a persistent field that diffuses and decays; validate it against real human experiments; and turn it into a working design tool.")}</p>')
    H.append('<div class="pillars">' + ''.join(f'<div class="pill"><b>{L(bt,be)}</b><span>{L(st,se)}</span></div>' for bt,be,st,se in [
        ("Yeni fikir","The idea",
         "Duygu, ortamda kalan, yayılıp sönen bir alandır — kişiden-kişiye bulaşma değil.",
         "Affect is a persistent field that diffuses and decays — not person-to-person contagion."),
        ("Kanıt","The evidence",
         "Gerçek insan deneyleriyle ve gerçek bir felaketle (İtaewon) doğrulandı.",
         "Validated against real human experiments and a real disaster (Itaewon)."),
        ("Ürün","The product",
         "İzdiham riskini önceden gösteren, çözüm öneren çalışan bir araç (3D dahil).",
         "A working tool that maps crush risk in advance and proposes fixes (incl. 3D)."),
        ]) + '</div>')
    H.append('</div></header>')

    # 1. Intro
    body = (LEAD("Kalabalık felaketlerinin çoğu yangın ya da saldırı değildir: çok fazla insan, çok dar bir alan, yanlış akış. Ölümcül olan görünmez bir büyüklüktür — yerel yoğunluk.",
        "Most crowd disasters are not fire or attack: too many people, too narrow a space, the wrong flow. The killer is an invisible quantity — local density.")
     + P(f"İtaewon 2022’de ~3.2 m genişliğindeki bir sokakta 159 kişi öldü{CITE(14)}; Love Parade 2010’da tek bir rampada 21 kişi{CITE(5)}. Panik bir “kötülük” değil; yüksek yoğunlukta bedenlerin sıkışmasıyla oluşan <em class=\"term\">kalabalık türbülansı</em>dır{CITE(4)}.",
        f"At Itaewon 2022, 159 people died in an alley ~3.2 m wide{CITE(14)}; at Love Parade 2010, 21 on a single ramp{CITE(5)}. Panic is not “evil” but <em class=\"term\">crowd turbulence</em> — the fluid-like surging of a dense crowd{CITE(4)}.")
     + P("Hayat kurtaran iki soru: (1) Bir mekânı <strong>inşa etmeden önce</strong> “burada izdiham olur mu?” diyebilir miyiz? (2) Bir olay sırasında <strong>panik patlamadan önce</strong> uyarabilir miyiz?",
        "Two life-saving questions: (1) <strong>before a venue is built</strong>, can we say “will this crush?” (2) during an event, can we warn <strong>before panic erupts?</strong>")
     + H3("Araştırma soruları","Research questions")
     + '  <ul class="clean">\n'
       f'    <li>{L("<strong>AS1:</strong> Kalabalık duygusu, ortamda kalan bir alan olarak modellenebilir ve bu alan <em>iletişimsiz</em> koordinasyon sağlar mı?","<strong>RQ1:</strong> Can crowd affect be modelled as a persistent field that enables coordination <em>without communication</em>?")}</li>\n'
       f'    <li>{L("<strong>AS2:</strong> Refleks (fizik) ile düşünerek-kararın stres düzeyine göre harmanlanması işe yarar mı?","<strong>RQ2:</strong> Does blending reflex (physics) with deliberation, gated by stress, actually help?")}</li>\n'
       f'    <li>{L("<strong>AS3:</strong> Model gerçek mi — gerçek insan verisine uyuyor ve gerçek bir felaketi yeniden üretiyor mu?","<strong>RQ3:</strong> Is the model real — does it match real human data and reproduce a real disaster?")}</li>\n'
       f'    <li>{L("<strong>AS4:</strong> Bütün bunlar izdiham riskini önceden gösteren bir araca dönüşebilir mi?","<strong>RQ4:</strong> Can all of this become a tool that maps crush risk in advance?")}</li>\n  </ul>\n'
     + NOTE("tip","Anahtar büyüklük: yoğunluk","The key quantity: density",
        f"Yoğunluk = bir metrekareye kaç kişi düştüğü (kişi/m²). Bu eşikler bizim icadımız değil; <strong>gözlemlenmiş izdiham olaylarından ve kalabalık-mühendisliği standartlarından</strong> gelir (Fruin’in “hizmet seviyesi” ölçeği; Helbing’in izdiham analizleri){CITE(4,16)}: ~1–2 kişi/m² rahat yürüme; <strong>~4–5 kişi/m²</strong> insanlar birbirine değer, kendi iradesiyle hareket edemez (tehlikeli); <strong>&gt;6 kişi/m²</strong> bedenler sıkışır, göğüs basıncı nefesi keser — ölümcül. Amaç bu eşiğe hiç yaklaşmamaktır.",
        f"Density = how many people share one square metre (ped/m²). These thresholds are not ours; they come from <strong>observed crowd disasters and crowd-engineering standards</strong> (Fruin’s “level of service” scale; Helbing’s crush analyses){CITE(4,16)}: ~1–2 ped/m² is comfortable walking; <strong>~4–5 ped/m²</strong> people touch and can no longer move at will (dangerous); <strong>&gt;6 ped/m²</strong> bodies compress and chest pressure stops breathing — lethal. The aim is never to approach it."))
    H.append(SEC("giris","01 · Giriş","01 · Introduction","Problem ve motivasyon","Problem & motivation", body))

    # 2. Approach
    body = (LEAD("Önce modelin ne olduğunu sade anlatalım; sonra teknik kuralları ve varsayımları kaynaklarıyla verelim.",
        "Let us first say plainly what the model is; then give the technical rules and assumptions with citations.")
     + H3("Modelin yapısı","Model structure")
     + P("Model <strong>mikroskobik, ajan-tabanlı bir simülasyondur</strong>: her yaya, basit kurallarla hareket eden tek bir ajandır ve topluluk davranışı (sıkışma, kuyruk, panik) bu ajanlardan kendiliğinden doğar. Tek bir uçtan-uca sinir ağı değildir; dört bileşenin birleşimidir:",
        "The model is a <strong>microscopic, agent-based simulation</strong>: each pedestrian is a single agent moving by simple rules, and collective behaviour (congestion, queues, panic) emerges from them. It is not a single end-to-end neural network; it combines four components:")
     + '  <ul class="clean">\n    <li>'
     + L(f"<strong>Lokomosyon (hareket):</strong> Helbing’in <em class=\"term\">Sosyal-Kuvvet Modeli</em> — her ajan, hedefe çekim ile komşulardan ve duvarlardan itme kuvvetlerinin toplamıyla, sürekli uzayda Newton-tipi ivmeyle hareket eder (kuvvet-tabanlı diferansiyel denklemler){CITE(2)}.",
         f"<strong>Locomotion:</strong> Helbing’s <em class=\"term\">Social-Force Model</em> — each agent moves by Newton-like acceleration from goal attraction plus repulsion from neighbours and walls, in continuous space (force-based ODEs){CITE(2)}.")
     + '</li>\n    <li>'
     + L("<strong>Duygu alanı:</strong> ızgara üzerinde bir <em class=\"term\">reaksiyon-difüzyon PDE’si</em> (bırak → yayıl → sön), açık sonlu farklarla çözülür. Özgün katkı budur.",
         "<strong>Affect field:</strong> a <em class=\"term\">reaction–diffusion PDE</em> on a grid (deposit → diffuse → decay), solved by explicit finite differences. This is the novel part.")
     + '</li>\n    <li>'
     + L("<strong>Navigasyon:</strong> duvarları dolaşıp çıkışa giden en kısa yolu veren bir <em class=\"term\">Dijkstra mesafe alanı</em>.",
         "<strong>Navigation:</strong> a <em class=\"term\">Dijkstra distance field</em> giving the shortest route around walls to the exit.")
     + '</li>\n    <li>'
     + L(f"<strong>Karar harmanı (2. sütun):</strong> ivme = λ·(fizik) + (1−λ)·(öğrenilmiş düzeltme); λ, strese göre sigmoid bir <em>kapı</em> ile ayarlanır. Öğrenilmiş kısım küçük bir <em class=\"term\">PPO aktör-kritik</em> ağı (tüm ajanlarca paylaşılan bir MLP){CITE(10,9)}. <strong>Ama fizik baskındır</strong> — PPO koşullu bir eklentidir (Bölüm 5).",
         f"<strong>Decision blend (pillar 2):</strong> acceleration = λ·(physics) + (1−λ)·(learned correction); λ is set by a sigmoid <em>gate</em> on stress. The learned part is a small <em class=\"term\">PPO actor–critic</em> network (an MLP shared across all agents){CITE(10,9)}. <strong>But physics dominates</strong> — PPO is a conditional add-on (Section 5).")
     + '</li>\n  </ul>\n'
     + ARCH_SVG
     + P("Mimari ağırlıkla <strong>fizik-tabanlıdır</strong> (kuvvet denklemleri + alan PDE’si + grafik araması); makine öğrenmesi yalnızca küçük ve koşullu PPO katmanında yer alır. Görüntü-tabanlı bir ağ (örn. evrişimli ağ) kullanılmaz; politikanın girdisi ajan-başına bir özellik vektörüdür (konum, hız, yük, alan değeri, hedef-yön).",
        "The architecture is predominantly <strong>physics-based</strong> (force equations + a field PDE + graph search); machine learning appears only in the small, conditional PPO layer. No image-based (e.g. convolutional) network is used; the policy’s input is a per-agent feature vector (position, velocity, load, field value, goal direction).")
     + H3("Varsayım 1 — Duygu stigmerjik bir alandır","Assumption 1 — Affect is a stigmergic field")
     + P(f"Karıncalar yere feromon bırakıp birbirini dolaylı yönlendirir; bu ortam-aracılı koordinasyona <em class=\"term\">stigmerji</em> denir{CITE(8)}. Stresi aynı şekilde modelliyoruz: birey iz bırakır, iz komşu hücrelere <strong>yayılır</strong> ve zamanla <strong>söner</strong> — klasik bir <em class=\"term\">reaksiyon-difüzyon</em> denklemi: ∂Φ/∂t = D∇²Φ − kΦ + S.",
        f"Ants leave pheromone and steer each other indirectly; this environment-mediated coordination is <em class=\"term\">stigmergy</em>{CITE(8)}. We model stress the same way: a person deposits a trace, it <strong>diffuses</strong> and <strong>decays</strong> — a classic <em class=\"term\">reaction–diffusion</em> equation: ∂Φ/∂t = D∇²Φ − kΦ + S.")
     + NOTE("tip","Denklemin anlamı","What the equation means",
        "Φ = bir noktadaki stres düzeyi. Sol taraf (∂Φ/∂t) “stres zamanla nasıl değişir?”i sorar. Sağ taraf üç şeyi toplar: <strong>D∇²Φ</strong> = stres komşu hücrelere yayılır (D = yayılma hızı); <strong>−kΦ</strong> = zamanla söner/unutulur (k = unutma hızı); <strong>+S</strong> = stresli insanlar yeni iz ekler (S = kaynak). Tek cümleyle: <em>stres yayılır, söner ve insanlarca beslenir.</em>",
        "Φ = the stress level at a point. The left side (∂Φ/∂t) asks “how does stress change over time?”. The right side adds three things: <strong>D∇²Φ</strong> = stress spreads to neighbouring cells (D = spread rate); <strong>−kΦ</strong> = it fades/forgets over time (k = forgetting rate); <strong>+S</strong> = stressed people add new trace (S = source). In one line: <em>stress spreads, fades, and is fed by people.</em>")
     + MECH_SVG
     + NOTE("tip","Alan ile bulaşmanın farkı","Field vs. contagion",
        "Bulaşmada kişi gidince etkisi anında sıfırlanır. Alanda iz <strong>kalır</strong> (ölçümümüzde 2 s sonra %48). Alan, kalabalığın mekâna ait hafızasıdır — özgün katkımızın çekirdeği.",
        "In contagion a person’s effect vanishes instantly. In a field the trace <strong>lingers</strong> (48% after 2 s in our measurement). The field is the crowd’s memory of the place — the core of our novelty.")
     + H3("Varsayım 2 — Yürüme refleks + düşünme harmanıdır","Assumption 2 — Walking is a reflex + deliberation blend")
     + P(f"Lokomosyon için <em class=\"term\">sosyal-kuvvet modeli</em>ni kullanıyoruz{CITE(2)} ve serbest hızı gerçek değere (1.34 m/s) ayarlıyoruz{CITE(1)}. Üstüne <em class=\"term\">çift-süreç</em> karar koyuyoruz{CITE(10)}: sakinken hızlı refleks (Sistem-1), sıkışınca belirsizlik artıp düşünerek-karara (Sistem-2) geçiş — beynin belirsizlik altında politika değiştirmesini tanımlayan <em class=\"term\">aktif çıkarım/kesinlik</em> ilkesiyle{CITE(9)}.",
        f"For locomotion we use the <em class=\"term\">social-force model</em>{CITE(2)} and set free speed to the real value (1.34 m/s){CITE(1)}. On top we add a <em class=\"term\">dual-process</em> decision{CITE(10)}: fast reflex when calm (System-1); when stuck, uncertainty rises and the agent switches to deliberation (System-2) — modelled with the <em class=\"term\">active-inference/precision</em> principle{CITE(9)}.")
     + NOTE("warn","Dürüstlük","Honesty",
        "Bunlar varsayım; her birini gerçek veriyle test ediyoruz (Bölüm 3) ve geçmeyen noktaları işaretliyoruz.",
        "These are assumptions; we test each against real data (Section 3) and flag what does not pass."))
    H.append(SEC("yaklasim","02 · Yöntem","02 · Method","Yaklaşım ve varsayımlar","Approach & assumptions", body))

    # 3. Validation
    body = (LEAD("Elimizde bir simülasyon var (Bölüm 2’deki model). Peki bu simülasyon gerçek insanlar gibi mi davranıyor, yoksa sadece makul mu görünüyor?",
        "We have a simulation (the model from Section 2). But does it behave like real people, or does it merely look plausible?")
     + P("“Doğrulama” tam da budur: simülasyonun ürettiği <strong>ölçülebilir</strong> sayıları — yürüme hızı, kapıdan akış, yoğunluk — <strong>gerçek insan deneylerinde ölçülmüş</strong> değerlerle yan yana koymak. Uyuyorsa model “gerçek” (veriye dayalı); uymuyorsa “sadece bir hikâye”. Üç gittikçe zorlaşan test yaptık: (1) laboratuvar yürüme ölçümleri, (2) modelin <em>hiç görmediği</em> ham veri, (3) gerçek bir felaketin yeniden üretimi. Geçmeyen tek noktayı da gizlemeden yazdık.",
        "“Validation” is exactly this: placing the simulation’s <strong>measurable</strong> outputs — walking speed, door flow, density — beside values <strong>measured in real human experiments</strong>. If they match, the model is “real” (data-grounded); if not, it is “just a story”. We ran three increasingly hard tests: (1) lab walking measurements, (2) raw data the model <em>never saw</em>, (3) reproducing a real disaster. We also state, without hiding, the one point that does not pass.")
     + H3("3.1 — Temel diyagram (gerçek kurala kalibrasyon)","3.1 — Fundamental diagram (calibration to the real rule)")
     + P(f"<em class=\"term\">Temel diyagram</em>, yoğunluk ile yürüme hızı arasındaki ölçülmüş ilişkidir — trafikteki “doluysa yavaş” kuralının yaya hâli{CITE(1,12)}.",
        f"The <em class=\"term\">fundamental diagram</em> is the measured relation between density and walking speed — the pedestrian version of traffic’s “dense = slow” rule{CITE(1,12)}.")
     + FIG("fd.png","Fundamental diagram",
        ("Serbest yürüme hızı + temel diyagram (model çekirdeği).","Free-walking speed + fundamental diagram (model core)."),
        ("Modelin serbest yürüme hızı gerçek değere (1.34 m/s) oturuyor mu?","Does the model's free-walking speed match the real value (1.34 m/s)?"),
        ("<strong>Kenarsız bir alan</strong> (<em class=\"term\">torus</em> — bir kenardan çıkan öbüründen girer, böylece duvar etkisi olmadan yoğunluk her yerde eşit kalır), 16×16 m; ajan sayısı 4→250 ile yoğunluk tarandı; herkes aynı yöne akar; duygu alanı kapalı (taban = stresli hız = 1.34 m/s); 6 s ısınma + 8 s ölçüm (adım = 0.05 s), 2 tekrar; ortalama ileri hız.","An <strong>edgeless space</strong> (<em class=\"term\">torus</em> — exit one side and re-enter the opposite, so density stays uniform with no wall effects), 16×16 m; density swept via agent count 4→250; all flow the same way; affect field off (base = stressed speed = 1.34 m/s); 6 s warm-up + 8 s measurement (step = 0.05 s), 2 runs; mean forward speed."),
        ("Boş alanda 1.34 m/s; yoğunlukla monoton düşer (ρ≈1’de ~0.92 m/s). Lokomosyon katmanı gerçekçi.","1.34 m/s in open space; falls monotonically with density (~0.92 m/s at ρ≈1). The locomotion layer is realistic."))
     + FIG("val_fd.png","Validation full range",
        ("Tam-aralık FD doğrulaması: model vs Weidmann.","Full-range FD validation: model vs Weidmann."),
        ("Model sadece serbest hızda değil, <em>tüm</em> yoğunluk aralığında (tıkanma→kilitlenme) gerçek FD’ye uyuyor mu?","Does the model match the real FD across the <em>whole</em> range (congestion→jam), not just free speed?"),
        (f"Torus FD’si ρ≈0.3→5 arası ölçüldü (side = 10 m, 2 tohum); Weidmann formülü{CITE(1)} + ampirik serbest-hız/kapasite/jam aralıkları + Seyfried{CITE(3)} darboğaz değeri üzerinden 6 nicel kontrol.",
         f"Torus FD measured from ρ≈0.3→5 (side = 10 m, 2 seeds); 6 quantitative checks against the Weidmann formula{CITE(1)} + empirical free-speed/capacity/jam ranges + Seyfried's{CITE(3)} bottleneck value."),
        ("RMSE 0.055; 6 kontrolden 5’i geçer. Akış-yoğunluk gerçek tepe+jam şeklini verir. Tek kalıntı: kapı akışı (◆, ~%10 hızlı).","RMSE 0.055; 5 of 6 checks pass. The flow–density curve has the real peak+jam shape. Lone residual: door flow (◆, ~10% fast)."))
     + FIG("valflow.png","Bottleneck specific flow",
        ("Darboğaz özgül akışı, kapı genişliğine göre.","Bottleneck specific flow, by door width."),
        (f"Bir kapıdan akış, ölçülen ~1.9 kişi/m/s ampirik değerine{CITE(3,7)} uyuyor mu?",
         f"Does a door's flow match the measured ~1.9 ped/m/s empirical value{CITE(3,7)}?"),
        ("Tek kapıdan sürekli kuyruk (N = 160) akıtıldı; 8–28 s kararlı-hal penceresinde tahliye-eğiminin eğimi ölçülüp kapı genişliğine bölündü; genişlikler 1.6/2.4/3.2 m, 3 tohum.","A sustained queue (N = 160) was pushed through one door; the slope of the evacuation count was measured over an 8–28 s steady-state window and divided by door width; widths 1.6/2.4/3.2 m, 3 seeds."),
        ("2.4 m kapı 1.59 (bandda); 1.6 m kapı 2.56 (üstünde). Model dar kapıda biraz hızlı — modelin tek zayıf doğrulama noktası, gizlenmedi.","2.4 m door 1.59 (in band); 1.6 m door 2.56 (above). The model runs a touch fast at the narrow door — its one weak validation point, not hidden."))
     + H3("3.2 — Ayrık doğrulama (modelin görmediği ham veri)","3.2 — Held-out test (raw data the model never saw)")
     + FIG("val_juelich.png","Held-out Juelich",
        ("Ayrık doğrulama: gerçek ham Jülich verisi (siyah) vs model (kırmızı).","Held-out validation: real raw Jülich data (black) vs model (red)."),
        ("Model, kalibrasyonda kullanılmayan bağımsız gerçek veriyi öngörür mü?","Does the model predict independent real data not used in calibration?"),
        (f"Jülich/Wuppertal darboğaz deneyinin{CITE(13)} ham trajectory dosyası (75 kişi, 25 kare/s); pozisyonlardan ±6 kare (≈0.48 s) pencereli hız; en yoğun noktada 1.5×1.5 m ölçüm alanı; 0.6 kişi/m² genişlikte yoğunluk binleri (≥8 kare); modelin (yalnız Weidmann’a kalibre) FD’si overlay edildi.",
         f"Raw trajectory file of the Jülich/Wuppertal bottleneck experiment{CITE(13)} (75 people, 25 fps); windowed speed over ±6 frames (≈0.48 s); a 1.5×1.5 m measurement area at the busiest spot; density bins of width 0.6 ped/m² (≥8 frames each); the model's FD (calibrated only to Weidmann) overlaid."),
        ("Korelasyon 0.99, RMSE 0.21 m/s — Weidmann’dan (0.26) bile iyi. Model görmediği veriyi bildi: ezberlemedi, genelliyor.","Correlation 0.99, RMSE 0.21 m/s — even better than Weidmann (0.26). The model predicted unseen data: it generalises, did not memorise."))
     + H3("3.3 — Gerçek mekân: İtaewon 2022","3.3 — Real venue: Itaewon 2022")
     + FIG("itaewon.png","Itaewon real venue",
        ("Gerçek İtaewon sokağı; yoğunluk ısı haritası (üst: karşıt-akış, alt: tek-yön).","Real Itaewon alley; density heat-map (top: counter-flow, bottom: one-way)."),
        ("Gerçek ölçülerle kurulunca model felaketi kendi başına üretir mi?","Built with the real dimensions, does the model produce the disaster on its own?"),
        (f"Gerçek geometri 45 m × 3.2 m{CITE(14)}; iki karşıt akış (her biri 150 kişi, sürekli besleme); gövde-deformasyon açık (w_compress = 2.0, yoğunluk-eşikli sıkışma); 45 s, yerel yoğunluk r = 1 m yarıçapla, 2 tohum; A/B karşılaştırması: tek-yön kuralı.",
         f"Real geometry 45 m × 3.2 m{CITE(14)}; two opposing streams (150 each, continuous feed); body deformation on (w_compress = 2.0, density-gated compression); 45 s, local density at r = 1 m radius, 2 seeds; A/B against a one-way rule."),
        (f"Pik ~10 kişi/m², tam ortada — belgelenen 9.95 ile örtüşür{CITE(14)}; sebep karşıt-akış kilidi; tek-yön çarpışmayı siler. Model doğru yer + sebep + yoğunluğu kendi buldu.",
         f"Peak ~10 ped/m², in the exact middle — matching the documented 9.95{CITE(14)}; cause is the counter-flow lock; one-way erases the collision. The model found the right place + cause + density on its own."))
     + NOTE("flag","Dürüst sınır","Honest limit",
        f"Gerçek İtaewon CCTV verisi açık değildir (gizlilik); eşleştiğimiz 9.95 başka bir hidrodinamik modelin tahminidir{CITE(14)}. Yani gerçek geometri + yayımlanmış yeniden-üretimle kıyasladık, ham sensör verisiyle değil.",
        f"Real Itaewon CCTV data is not public (privacy); the 9.95 we matched is another hydrodynamic model's estimate{CITE(14)}. We compared real geometry + a published reconstruction, not raw sensor data."))
    H.append(SEC("dogrulama","03 · Doğrulama","03 · Validation","Gerçek veriyle doğrulama","Validation against real data", body))

    # 4. Findings 1
    body = (LEAD("Birinci sütun (AS1) en güçlü ve en özgün katkıdır: kalabalık alanı okuyarak iletişimsiz koordine olur, ve panik bir faz geçişi gibi davranır.",
        "The first pillar (RQ1) is the strongest, most novel contribution: the crowd coordinates without communication by reading the field, and panic behaves like a phase transition.")
     + FIG("scenarios.png","Scenario library",
        ("28 test yerleşiminden oluşan senaryo kütüphanesi.","A scenario library of 28 test layouts."),
        ("Bulgular tek bir geometriye mi özel, yoksa genellenebilir mi?","Are the findings specific to one geometry, or do they generalise?"),
        (f"RiMEA-tarzı{CITE(7)} + gerçek-hayat benzeri 28 senaryo geometrisi (koridor, darboğaz, kavşak, atriyum, sahne çıkışı, karşıt-akış…) tanımlandı; tüm A/B deneyleri aynı kütüphanede koşuldu.",
         f"28 scenario geometries (RiMEA-style{CITE(7)} + real-life-like: corridor, bottleneck, junction, atrium, stage egress, counter-flow…) were defined; all A/B experiments ran on this same library."),
        ("Aynı model 28 farklı geometride çalışıyor — bulgular geometriye özel değil, genellenebilir.","The same model runs across 28 geometries — the findings are not geometry-specific, they generalise."))
     + H3("İletişimsiz koordinasyon","Communication-free coordination")
     + FIG("coordination.png","Communication-free coordination",
        ("İletişimsiz çıkış dengeleme (NearFar odası).","Communication-free exit balancing (NearFar room)."),
        ("Alan, merkezi yönetici ya da konuşma olmadan kalabalığı dengeler mi (AS1)?","Does the field balance the crowd with no controller or communication (RQ1)?"),
        (f"NearFar odası (yakın + uzak kapı), N = 45, kalabalık yakına biaslı; 10 tohum, 60 s. İki koşul: Temel = en-yakın kapı; AlanRota = her 2 s’de kapı önündeki (1.5 m üstü) alan yoğunluğuna ceza (k = 20) verip rota seç. Mann-Whitney testi + Cliff δ{CITE(6)}.",
         f"NearFar room (near + far door), N = 45, crowd biased to the near door; 10 seeds, 60 s. Two conditions: Baseline = nearest door; FieldRoute = every 2 s choose route penalising the field 1.5 m before each door (k = 20). Mann-Whitney test + Cliff's δ{CITE(6)}."),
        ("En-dolu kapı payı 1.00→0.68; Cliff δ = −1.0, p &lt; 0.0001; uzak kapı kullanıldı. Konuşma/yönetici olmadan kalabalık kendini dengeledi — gerçek öz-örgütlenme.","Busiest-door share 1.00→0.68; Cliff δ = −1.0, p &lt; 0.0001; the far door was used. With no controller or communication the crowd balanced itself — genuine self-organisation."))
     + FIG("drain.png","Field autonomy",
        ("Alan-özerkliği: kalabalık gittikten sonra alanın sönümü.","Field autonomy: the field decaying after the crowd leaves."),
        ("Alan, kalabalık gidince <em>kalır</em> mı — yani bir “hafıza” mıdır?","Does the field <em>persist</em> after the crowd leaves — is it a “memory”?"),
        ("16×16 m torus; 45 ajan 25 s milling (3 s’de bir yeni hedef) ile alanı kurar; sonra TÜM ajanlar anında silinir; alan 12 s özerk evrilir (yalnız sönüm, decay k = 0.35); Φ ortalamasından üstel sönüm hızı fit edilir.","16×16 m torus; 45 agents mill for 25 s (new target every 3 s) building the field; then ALL agents are removed at once; the field evolves autonomously for 12 s (decay only, k = 0.35); the exponential decay rate is fit from the mean Φ."),
        ("k ≈ 0.35/s, yarı-ömür ~2 s; 2 s sonra izin %48’i kalır (bulaşma modelinde 0). Alan bir hafızadır — özgünlüğün somut kanıtı.","k ≈ 0.35/s, half-life ~2 s; 48% of the trace remains after 2 s (0 in a contagion model). The field is a memory — concrete evidence for the novelty."))
     + H3("Faz geçişi ve erken uyarı","Phase transition and early warning")
     + FIG("phase.png","Phase transition",
        ("Panik faz geçişi: düzen parametresi + duyarlılık.","Panic phase transition: order parameter + susceptibility."),
        ("Panik bireysel mi, yoksa kalabalığın kolektif bir hâl değişimi (faz geçişi) mi?","Is panic individual, or a collective state change of the crowd (a phase transition)?"),
        ("18×18 m torus, max_value = 5, decay = 0.35, taban-sakinleştirme FAM = 0.6; yoğunluk (N 10→180) ve geri-besleme kazancı ayrı ayrı tarandı; 18 s ısınma + 12 s ölçüm, 3 tohum; düzen parametresi M = ort. yük, duyarlılık χ = N·var(M).","18×18 m torus, max_value = 5, decay = 0.35, baseline calming FAM = 0.6; density (N 10→180) and feedback gain were swept separately; 18 s warm-up + 12 s measurement, 3 seeds; order parameter M = mean load, susceptibility χ = N·var(M)."),
        ("Sakinden paniğe keskin geçiş + kritik yoğunlukta χ zirvesi — bir faz geçişinin imzası. Panik fizik diliyle açıklanabilir.","A sharp calm→panic transition + a susceptibility peak at the critical density — the signature of a phase transition. Panic is explainable in the language of physics."))
     + FIG("early_warning.png","Critical slowing down",
        ("Kritik yavaşlama: tipping öncesi erken-uyarı sinyali.","Critical slowing down: an early-warning signal before tipping."),
        (f"Panik patlamadan <em>önce</em> ölçülebilir bir uyarı sinyali var mı{CITE(11)}?",
         f"Is there a measurable warning signal <em>before</em> panic erupts{CITE(11)}?"),
        ("18 m torus, N = 70, FAM = 0.6; geri-besleme kazancı 44 s’de 0.3→3.4 yavaşça rampalandı; 8-koşuluk topluluk; düzen parametresi her 4 adımda örneklendi; 28-örnek (~5.6 s) kayan pencerede artık-varyans + lag-1 otokorelasyon (AR(1)).","18 m torus, N = 70, FAM = 0.6; the feedback gain was slowly ramped 0.3→3.4 over 44 s; an 8-run ensemble; the order parameter sampled every 4 steps; rolling residual-variance + lag-1 autocorrelation (AR(1)) over a 28-sample (~5.6 s) window."),
        ("Tipping’e doğru duyarlılık ×14 büyür, AR(1) yükselir — sinyal tipping noktasını önceler. Bir operatöre erken uyarı verilebilir.","Toward tipping susceptibility grows ~14×, AR(1) rises — the signal leads the tipping point. An operator can be warned early."))
     + FIG("panic_prevention.png","Panic prevention",
        ("Erken-uyarı tetikli panik önleme.","Early-warning-triggered panic prevention."),
        ("Erken uyarı yalnız tahmin değil, gerçek bir <strong>önleme</strong> sağlar mı?","Does early warning enable not just prediction but real <strong>prevention</strong>?"),
        ("Aynı kazanç rampası (0.3→3.4 / 44 s, N = 70, 8-koşul); canlı erken-uyarı = kesit yük-varyansı; sinyal erken-tabanın 2.2 katını aşınca müdahale tetiklenir: familiarity (sakinleştirme) +0.04/adım rampalanır. Müdahalesiz kontrol vs müdahale.","Same gain ramp (0.3→3.4 / 44 s, N = 70, 8 runs); live early warning = cross-sectional load variance; when it exceeds 2.2× its early baseline an intervention fires: familiarity (calming) ramps +0.04/step. No-intervention control vs intervention."),
        ("Kontrol tipiyor (M = 0.94); müdahale düz tutuyor (M = 0.00), tetik t ≈ 9 s. Uyar-ve-müdahale döngüsü çalışıyor — felaketi durdurmak mümkün.","Control tips (M = 0.94); intervention holds it flat (M = 0.00), trigger t ≈ 9 s. The warn-then-act loop works — the disaster can be stopped."))
     + FIG("hysteresis.png","Hysteresis",
        ("Histerezis çevrimi: yukarı yol ≠ aşağı yol.","Hysteresis loop: the up path ≠ the down path."),
        ("Panik geçişi geri-dönüşlü mü, yoksa başladıktan sonra söndürmek zor mu?","Is the panic transition reversible, or hard to quench once it starts?"),
        ("18 m torus, N = 80, FAM = 0.62; tek koşuda kazanç 0.3→3.2 yukarı sonra aşağı (her bacak 34 s), 6-koşul; ayrıca ortalama-alan Hill geri-beslemesinde (üs = 4) fold noktaları analitik bulundu.","18 m torus, N = 80, FAM = 0.62; in one run the gain ramps 0.3→3.2 up then down (each leg 34 s), 6 runs; the fold points were also found analytically in a mean-field Hill feedback (exponent = 4)."),
        ("Yukarı/aşağı yolları ayrışıyor (çevrim alanı ≈ 0.92) + iki fold (saddle-node). Panik geri-dönüşü zor bir geçiş → erken müdahale kritik.","The up/down paths separate (loop area ≈ 0.92) + two folds (saddle-node). Panic is a hard-to-reverse transition → early intervention is critical."))
     + FIG("meanfield.png","Mean-field theory",
        ("Ortalama-alan teorisi: geçiş eğrisinin analitik üretimi.","Mean-field theory: the transition curve reproduced analytically."),
        ("Ajan-bazlı geçiş, basit bir matematiksel teoriyle de açıklanabilir mi?","Can the agent-based transition also be explained by a simple mathematical theory?"),
        ("İyi-karışmış limitte dM/dt = −d·M + c·g·F(M), F = Hill (M²/(M²+h²)); D = 0.5, C = 0.62, H = 0.42, A = 0.09 (etkin); tek bir etkin eşleşme κ ile bare-gain’e eşlenip ajan-sim eğrisine fit edildi.","In the well-mixed limit dM/dt = −d·M + c·g·F(M), F = Hill (M²/(M²+h²)); D = 0.5, C = 0.62, H = 0.42, A = 0.09 (effective); a single effective coupling κ maps to the bare gain and is fit to the agent-sim curve."),
        ("κ ≈ 0.55 ajan geçişini sürekli biçimde üretir; g_c ≈ 0.44. Bulgu teoriyle de destekleniyor.","κ ≈ 0.55 reproduces the agent transition as a continuous crossover; g_c ≈ 0.44. The finding is also backed by theory."))
     + NOTE("warn","Dürüst negatif","Honest negative",
        f"Alanın yön bilgisini standart uzaysal istatistik <em class=\"term\">Moran’s I</em> (komşu hücrelerin ne kadar benzeştiğini özetler{CITE(6)}) ile görünür kılamadık; doğru gözlemci yönlü-otokorelasyondur. Açıkça yazıyoruz.",
        f"We could not surface the field's directionality with the standard spatial statistic <em class=\"term\">Moran's I</em> (which summarises how similar neighbouring cells are{CITE(6)}); the right observable is directional autocorrelation. We state it openly."))
    H.append(SEC("alan","04 · Bulgu 1","04 · Finding 1","Duygu alanı: koordinasyon, özerklik ve faz geçişi","The affect field: coordination, autonomy and phase transition", body))

    # 5. Findings 2
    body = (LEAD("İkinci sütun (AS2): refleks ile düşünmenin harmanı bir hız değil, bir sağlamlık mekanizmasıdır — refleksin kilitlendiği tehlikeli rejimde devreye girer.",
        "The second pillar (RQ2): the reflex–deliberation blend is not a speed but a robustness mechanism — it engages where reflex deadlocks, in the dangerous regime.")
     + P(f"Alt-seviye yürümede fizik baskındır — bu gerçekçidir, çünkü gerçek yürüme büyük ölçüde reflekstir{CITE(15)}. Harmanlamanın değeri <strong>karar seviyesinde</strong> ve <strong>kilitlenme rejiminde</strong>dir.",
        f"At the locomotion level physics dominates — realistic, since real walking is largely reflexive{CITE(15)}. The blend's value is at the <strong>decision level</strong> and in the <strong>deadlock regime</strong>.")
     + FIG("rq2.png","Dual-process robustness",
        ("Çift-süreç sağlamlığı: karşıt-akış darboğazında tahliye.","Dual-process robustness: evacuation in a counter-flow choke."),
        ("Refleks+düşünme harmanı <em>ne zaman</em> saf reflekse üstün gelir?","<em>When</em> does the reflex+deliberation blend beat pure reflex?"),
        ("44×12 m koridor + orta choke (≈1.4 m), iki karşıt akış; kalabalık N = 40→190 tarandı, 8 tohum, 50 s; yalnız-fizik vs harman (ajan sıkışınca — hedeften uzak + hız &lt; 0.25 m/s — refleksi bırakıp ‘sağdan git’ yanal şerit kuralına geçer, nudge = 3).","44×12 m corridor + a mid-choke (≈1.4 m), two opposing streams; crowd size swept N = 40→190, 8 seeds, 50 s; physics-only vs the blend (when stuck — far from exit + speed &lt; 0.25 m/s — the agent drops reflex for a ‘keep-right’ lateral lane rule, nudge = 3)."),
        ("Kolayda benzer; refleksin kilitlendiği yoğun karşıt-akışta (N = 70, 190) harman tahliyeyi ~2× yaptı (N≥70 ort. +%43); N = 110’da fizik serbest aktı, harman azıcık zarar verdi — dürüst istisna. Sistem-1/Sistem-2’nin somut karşılığı.","Similar when easy; in dense counter-flow where reflex deadlocks (N = 70, 190) the blend ~doubled evacuation (avg +43% for N≥70); at N = 110 physics flowed freely and the blend cost a little — an honest exception. The concrete System-1/System-2 split."))
     + FIG("precision.png","Precision gate",
        ("Kesinlik kapısı: sıkışma azaltımı (Bottleneck).","Precision gate: stuck-state reduction (Bottleneck)."),
        (f"Belirsizlik (sıkışma) yüksekken politika değiştirmek{CITE(9)} sıkışmayı azaltır mı?",
         f"Does switching policy under high uncertainty (stuck){CITE(9)} reduce stuck-states?"),
        ("Bottleneck senaryosu, N = 60, 5 tohum, 45 s; ‘sıkışmış’ = hedeften uzak (&gt;1 m) + hız &lt; 0.25 m/s; kapı açıkken bu ajanlara yanal kaçış nudge’ı (= 3) verilip λ düşürülür; sıkışma oranı + tahliye, kapı açık vs kapalı.","Bottleneck scenario, N = 60, 5 seeds, 45 s; ‘stuck’ = far from exit (&gt;1 m) + speed &lt; 0.25 m/s; when the gate is on these agents get a lateral escape nudge (= 3) and lowered λ; stuck-fraction + evacuation, gate on vs off."),
        ("Sıkışma %56 düşer (0.65→0.28), karşılığında ~%14 hız bedeli — aktif-çıkarımın somut bir uygulaması.","Stuck-states drop 56% (0.65→0.28) at a ~14% speed cost — a concrete instance of active inference."))
     + FIG("actuator.png","Field as actuator",
        ("Alan-aktüatör: dışarıdan yazarak kalabalığı yönlendirme.","Field as actuator: steering the crowd by writing to it."),
        ("Alan yalnız okunmaz; ona yazarak kalabalık <em>yönlendirilebilir</em> mi — ve bu güvenli mi?","The field is not only read; can writing to it <em>steer</em> the crowd — and is that safe?"),
        ("NearFar odası, N = 45, 5 tohum, 60 s; dört koşul — Temel (en-yakın kapı), Öz-örgütlenme (ajanların kendi affect’i), Naif aktüatör (yakın kapıya dış 80/s döküm), Kapalı-döngü aktüatör (anlık dengesizlikle orantılı, kazanç 6); en-dolu kapı payı + uzak kapı kullanımı.","NearFar room, N = 45, 5 seeds, 60 s; four conditions — Baseline (nearest door), Self-organisation (agents' own affect), Naive actuator (external 80/s deposit at the near door), Closed-loop actuator (proportional to live imbalance, gain 6); busiest-door share + far-exit usage."),
        ("Alana yazmak yönlendiriyor (uzak kapı 0→9.4); naif kontrol aşırıya kaçıp dengeyi bozuyor (pay 1.00); kapalı-döngü 0.76’ya çekiyor. Kör kontrol tehlikeli — geri-besleme şart.","Writing steers (far exit 0→9.4); naive control overshoots and unbalances (share 1.00); closed-loop pulls it to 0.76. Blind control is dangerous — feedback is essential."))
     + NOTE("warn","Dürüst kapsam","Honest scope",
        "Harman garantili bir kazanç değil; tehlikeli (kilitlenme) rejimde güçlü, kolayda nötr. Koşullu ama büyük bir sağlamlık kazancı.",
        "The blend is not a guaranteed win; strong in the dangerous (deadlock) regime, neutral when easy. A conditional but large robustness gain."))
    H.append(SEC("karar","05 · Bulgu 2","05 · Finding 2","Çift-süreç karar mimarisi","Dual-process decision architecture", body))

    # 6. Tool
    body = (LEAD("Bütün bunları somut bir ürüne çevirdik: plan çiz/yükle → ezilme-risk haritası, güvenli kapasite, A/B test edilmiş düzeltmeler. Gerçek senaryolar hazır, simülasyon 3D’de canlı.",
        "We turned it all into a product: draw/upload a plan → crush-risk map, safe capacity, A/B-tested fixes. Real scenarios built-in, simulation live in 3D.")
     + FIG("crush.png","Crush density (tool core)",
        ("Crush-yoğunluk eğrisi (aracın çekirdeği).","Crush-density curve (the tool's core)."),
        ("Bir tasarım, ölümcül yoğunluğa (≈5 kişi/m²) ne kadar yaklaşır (AS4)?","How close does a design come to lethal density (≈5 ped/m²) (RQ4)?"),
        ("Oda + kapı geometrisi; doluluk N = 60→400 tarandı, 2 tohum, 45 s; 4 kapı tasarımı (tek 1.6/2.4/3.2 m + 2×1.6 m); her N’de pik yerel yoğunluk ölçüldü.","Room + door geometry; occupancy swept N = 60→400, 2 seeds, 45 s; 4 door designs (single 1.6/2.4/3.2 m + 2×1.6 m); peak local density measured at each N."),
        ("Yoğunluk doluluğla monoton artar; tek dar kapı en yüksek, iki kapı en düşük. Aracın çekirdeği: tehlike eşiğine yaklaşımı <strong>önceden</strong> gösterir.","Density rises monotonically; one narrow door highest, two doors lowest. The tool's core: it shows the approach to danger <strong>in advance</strong>."))
     + FIG("capacity.png","Safe capacity",
        ("Güvenli kapasite, kapı tasarımına göre.","Safe capacity, by door design."),
        ("Bir mekânın güvenli doluluğu kapı tasarımına nasıl bağlı?","How does a venue's safe occupancy depend on door design?"),
        ("Oda geometrisi; doluluk N = 60→400 tarandı, 2 tohum, 45 s; ortanca boşalma süresi t50; kapı genişliği (1.6/2.4/3.2 m) ve iki-kapı değişimi.","Room geometry; occupancy swept N = 60→400, 2 seeds, 45 s; median clearance time t50; door width (1.6/2.4/3.2 m) and a two-door variation."),
        ("Kapı genişledikçe t50 belirgin düşer (45→27→21 s @N=400); ikinci kapı benzer kazanç. Monoton, nicel bir tasarım kuralı.","As the door widens t50 drops markedly (45→27→21 s @N=400); a second door gives a similar gain. A monotone, quantitative design rule."))
     + FIG("optimize.png","Inverse design",
        ("Ters tasarım: kapı bütçesinin en güvenli dağılımı.","Inverse design: the safest distribution of a door budget."),
        ("Sabit 4.8 m kapı bütçesini nereye koymalı?","Given a fixed 4.8 m door budget, where should it go?"),
        ("30×20 m oda, toplam bütçe 4.8 m; N = 180, 3 tohum, 60 s; adaylar 1×4.8 / 2×2.4 / 3×1.6 m (farklı konumlarda); her aday için t50 + tahliye.","30×20 m room, total budget 4.8 m; N = 180, 3 seeds, 60 s; candidates 1×4.8 / 2×2.4 / 3×1.6 m (at different positions); t50 + evacuation per candidate."),
        ("Tek geniş kapı en hızlı (7.5 s); üçe bölmek +%80 (13.5 s) ve ~20 kişiyi mahsur bırakır. Kural: kapı bütçeni parçalama.","One wide door is fastest (7.5 s); splitting into three costs +80% (13.5 s) and strands ~20 people. Rule: don't fragment your door budget."))
     + FIG("case.png","Itaewon design-clinic A/B",
        ("İtaewon-tipi koridor: tasarım-kliniği A/B.","Itaewon-type corridor: design-clinic A/B."),
        ("Araç gerçek bir kilit örüntüsünü işaretler + doğru çözümü bulur mu?","Would the tool flag a real lock pattern + find the right fix?"),
        ("44×14 m koridor + orta choke, karşıt-akış; N = 70, 3 tohum, 60 s; üç koşul (temel / genişlet / tek-yön); affect-alanı risk haritası + hotspot’lar + tahliye sayısı.","44×14 m corridor + a mid-choke, counter-flow; N = 70, 3 seeds, 60 s; three conditions (baseline / widen / one-way); affect-field risk map + hotspots + evacuation count."),
        ("Karşıt-akış kilitleniyor (26/70); yalnız genişletmek az yardımcı (50/70); tek-yön çözüyor (62/70). Risk haritası kilidi tam doğru yerde işaretliyor.","Counter-flow gridlocks (26/70); widening alone helps little (50/70); one-way resolves it (62/70). The risk map flags the lock exactly where it forms."))
     + FIG("pressure.png","Crowd pressure",
        ("Kalabalık basıncı, yoğunluk doygunluğuna karşı.","Crowd pressure vs density saturation."),
        (f"Yoğunluk doyduğunda tehlike biter mi{CITE(4)}?",
         f"When density saturates, is the danger over{CITE(4)}?"),
        ("Oda + kapı, N = 60→240, 2 tohum, 50 s; Helbing kalabalık-basıncı = yerel yoğunluk × yerel hız-varyansı; kapı tasarımlarına göre pik basınç ve pik yoğunluk.","Room + door, N = 60→240, 2 seeds, 50 s; Helbing crowd pressure = local density × local velocity variance; peak pressure and peak density by door design."),
        ("Yoğunluk doysa bile basınç yükselmeye devam eder; iki kapı en düşük basınç. Yalnız yoğunluk değil, basınç da izlenmeli — gerçek itme kuvveti budur.","Even as density saturates, pressure keeps rising; two doors give the lowest pressure. Track pressure, not just density — this is the real shoving force."))
     + FIG("hetero.png","Heterogeneous crowds",
        ("Heterojen kalabalık: kırılgan bireylerin etkisi.","Heterogeneous crowds: the effect of vulnerable individuals."),
        ("Kırılgan (yavaş) bireyler güvenli kapasiteyi nasıl etkiler?","How do vulnerable (slow) individuals affect safe capacity?"),
        ("N = 80, 5 tohum, 90 s; üç koşul — homojen, kırılgan (%20’si 0.4× hız), aileler (grup-bağlılığı); ortanca boşalma süresi t50 + tahliye.","N = 80, 5 seeds, 90 s; three conditions — homogeneous, vulnerable (20% at 0.4× speed), families (group cohesion); median clearance t50 + evacuation."),
        ("Kırılgan altküme t50’yi +%24 artırır (10.5→13.1 s) ve daha az kişi çıkar. Kapasite ortalama insana değil, en kırılgana göre planlanmalı.","The vulnerable subgroup raises t50 +24% (10.5→13.1 s) and fewer evacuate. Plan capacity for the most vulnerable, not the average."))
     + NOTE("tip","3D simülatör","3D simulator",
        "Araç tarayıcıda 3D oynatma sunar: ajanlar yoğunluğa göre mavi→sarı→kırmızı (kırmızı = ezilme). İtaewon/Love Parade gerçek senaryoları yüklenip canlı izlenir.",
        "The tool offers 3D playback: agents coloured blue→yellow→red by density (red = crush). Itaewon/Love Parade real scenarios load and play live."))
    H.append(SEC("arac","06 · Uygulama","06 · Application","Araç — tasarım kliniği ve 3D","The tool — design clinic & 3D", body))

    # 7. Robustness
    body = (P("Çekirdek modeli gerçek veriye yeniden kalibre etmek eski tüm sonuçları şüpheli kılar; bu yüzden 21 deneyin hepsini yeni modelde yeniden koşturduk.",
        "Recalibrating the core model to real data makes all earlier results suspect; so we re-ran all 21 experiments on the new model.")
     + NOTE("tip","Sonuç","Result",
        "13 bulgu aynen korundu, 8’i sayıca kaydı (çoğu daha gerçekçiye), 0’ı bozuldu. Kalibrasyon hiçbir niteliksel bulguyu çökertmedi.",
        "13 findings held unchanged, 8 shifted numerically (mostly toward more realistic values), 0 broke. The calibration broke no qualitative finding.")
     + FIG("sensitivity.png","Sensitivity analysis",
        ("Duyarlılık (tornado): hangi parametreler sonucu sürüyor?","Sensitivity (tornado): which parameters drive the result?"),
        ("Bulgular özenle ayarlanmış bir parametre setine mi asılı, yoksa gürbüz mü?","Do the findings hinge on a tuned parameter set, or are they robust?"),
        ("Bottleneck senaryosu, N = 45, 3 tohum, 50 s; 6 çekirdek parametre (field_gain, decay, diffusion, deposit_gain, contagion_gain, calm_gain) tek tek ±%40 oynatıldı; Moran’s I (uzaysal yapı) + tahliye değişimi; %95 güven aralığı.","Bottleneck scenario, N = 45, 3 seeds, 50 s; each of 6 core parameters (field_gain, decay, diffusion, deposit_gain, contagion_gain, calm_gain) varied ±40%; change in Moran's I (spatial structure) + evacuation; 95% confidence intervals."),
        ("En etkili knob (difüzyon) bile çıktıyı sağlamlık eşiğinin (0.15) çok altında oynatır; Moran’s I ~0.93 sabit kalır. Bulgular tek parametreye asılı değil, gürbüz.","Even the most influential knob (diffusion) moves the output far below the robustness threshold (0.15); Moran's I stays ~0.93. The findings don't hinge on one parameter — robust.")))
    H.append(SEC("saglamlik","07 · Sağlamlık","07 · Robustness","Sağlamlık ve yeniden-doğrulama","Robustness and re-verification", body))

    # 8. Contribution
    body = (P("Bu bölümün özgün katkısı üç katmanlıdır:","The novel contribution of this chapter has three layers:")
     + '  <ul class="clean">\n    <li>'
     + L(f"<strong>Kavramsal:</strong> kalabalık duygusunu bulaşma değil, ortamda kalan stigmerjik bir alan olarak modellemek{CITE(8)} — kalabalığın mekâna ait hafızası.",
         f"<strong>Conceptual:</strong> modelling crowd emotion not as contagion but a persistent stigmergic field{CITE(8)} — the crowd’s memory of the place.")
     + '</li>\n    <li>'
     + L(f"<strong>Bilimsel:</strong> bu alanı gerçek deneylerle (temel diyagram{CITE(1)} + ayrık Jülich verisi{CITE(13)}) doğrulamak ve gerçek bir felaketi{CITE(14)} yeniden üretmek.",
         f"<strong>Scientific:</strong> validating this field against real experiments (fundamental diagram{CITE(1)} + held-out Jülich data{CITE(13)}) and reproducing a real disaster{CITE(14)}.")
     + '</li>\n    <li>'
     + L("<strong>Pratik:</strong> her şeyi izdiham riskini önceden gösteren ve çözüm öneren çalışan bir araca (tasarım kliniği + 3D) çevirmek.",
         "<strong>Practical:</strong> turning it all into a working tool (design clinic + 3D) that maps crush risk in advance and proposes fixes.")
     + '</li>\n  </ul>\n'
     + H3("Bulgu özeti","Findings at a glance")
     + '  <table><thead><tr>'
       f'<th>{L("Bulgu","Finding")}</th><th>{L("Durum","Status")}</th><th>{L("Kanıt","Evidence")}</th></tr></thead><tbody>\n'
     + ''.join('  <tr><td>'+L(a,b)+'</td><td><span class="tag '+c+'">'+L(d,e)+'</span></td><td class="num">'+L(f,g)+'</td></tr>\n'
        for a,b,c,d,e,f,g in [
         ("Alan + iletişimsiz koordinasyon","Field + comm-free coordination","t","güçlü","strong","1.00→0.68, p&lt;0.0001","1.00→0.68, p&lt;0.0001"),
         ("Gerçek-veri doğrulaması","Real-data validation","t","5/6 + ayrık","5/6 + held-out","RMSE 0.055; korr 0.99","RMSE 0.055; corr 0.99"),
         ("Panik = faz geçişi + erken uyarı","Panic = phase transition + warning","t","güçlü","strong","duyarlılık ×14; 0.94→0.00","susceptibility ×14; 0.94→0.00"),
         ("Çift-süreç harmanlama","Dual-process blend","a","koşullu","conditional","kilitlenmede +%43 (×2)","deadlock +43% (×2)"),
         ("Sağlamlık (yeniden-doğrulama)","Robustness (regression)","t","13/8/0","13/8/0","±%40 gürbüz","robust to ±40%"),
         ("Kapı akışı (gerçek veriye karşı)","Door flow (vs real)","c","kalıntı","residual","2.1 vs 1.9 (~%10)","2.1 vs 1.9 (~10%)"),
        ])
     + '  </tbody></table>\n'
     + H3("Dürüst sınırlar","Honest limitations")
     + '  <ul class="clean">\n'
       f'    <li class="x">{L("Gerçek CCTV/sensör yoğunluk verisi yok (gizlilik); İtaewon kıyası gerçek geometri + yayımlanmış yeniden-üretimle.","No real CCTV/sensor density data (privacy); the Itaewon comparison uses real geometry + a published reconstruction.")}</li>\n'
       f'    <li class="w">{L("Kapı akışı ~%10 hızlı — koridor FD’sini Weidmann’a oturtan kalibrasyonun takası.","Door flow ~10% fast — a trade-off of fitting the corridor FD to Weidmann.")}</li>\n'
       f'    <li class="w">{L("Çift-süreç harman koşullu (tehlikeli rejimde güçlü, kolayda nötr).","The dual-process blend is conditional (strong in the dangerous regime, neutral when easy).")}</li>\n'
       f'    <li class="x">{L("Model 2B; merdiven/eğim ve tam beden-mekaniği yok (ezilme yaklaşık).","Model is 2D; no stairs/incline or full body mechanics (compression approximate).")}</li>\n  </ul>\n')
    H.append(SEC("katki","08 · Katkı","08 · Contribution","Katkı, özgünlük ve sınırlar","Contribution, novelty & limits", body))

    refbody = '  <ol class="refs">\n' + ''.join(f'    <li id="{rid}">{L(rtr, ren)}</li>\n' for (rid, rtr, ren) in REFS) + '  </ol>\n'
    H.append(SEC("kaynakca","09 · Kaynakça","09 · References","Kaynaklar","References", refbody))

    H.append('</main></div>')
    H.append('<div class="lightbox" id="lb"><img id="lbi" src=""></div>')
    H.append(f'<script>{JS}</script></body></html>')

    out = os.path.join(HERE, "chapter.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(H))
    print(f"built chapter.html ({os.path.getsize(out)//1024} KB pre-inline; {len(SECTIONS)} sections, {len(REFS)} refs)")


CSS = """
:root{--bg:#F5F7F8;--surface:#FFF;--ink:#16242B;--ink-soft:#3D4F58;--muted:#6B7C85;--nav-bg:#102029;--nav-ink:#C7D6DC;--nav-dim:#7E94A0;--teal:#0E7C86;--teal-deep:#0A5A62;--mist:#E6F0F1;--amber:#A8691F;--amber-tint:#FBF1E1;--coral:#B5503F;--coral-tint:#FAEAE6;--line:#DCE5E7;--shadow:0 1px 2px rgba(16,32,41,.04),0 8px 24px rgba(16,32,41,.06)}
*{box-sizing:border-box} html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--ink);font-family:Inter,system-ui,sans-serif;font-size:16px;line-height:1.62}
h1,h2,h3,h4{font-family:Spectral,Georgia,serif;line-height:1.22;color:var(--ink);font-weight:700}
.lang{display:none}
:root[data-lang="tr"] .lang.tr{display:inline} :root[data-lang="en"] .lang.en{display:inline}
a{color:var(--teal-deep)}
#progress{position:fixed;top:0;left:0;height:3px;background:var(--teal);width:0;z-index:60}
#langtoggle{position:fixed;top:11px;right:16px;z-index:80;display:flex;background:var(--surface);border:1px solid var(--line);border-radius:20px;overflow:hidden;box-shadow:var(--shadow)}
#langtoggle button{border:none;background:none;padding:7px 15px;font:600 12px 'IBM Plex Mono',monospace;color:var(--muted);cursor:pointer}
#langtoggle button.on{background:var(--teal);color:#fff}
.shell{display:grid;grid-template-columns:288px 1fr;min-height:100vh}
nav{position:sticky;top:0;align-self:start;height:100vh;background:var(--nav-bg);color:var(--nav-ink);padding:26px 20px;overflow-y:auto}
nav .brand{font-family:Spectral,serif;font-weight:700;font-size:19px;color:#fff;line-height:1.25}
nav .brand small{display:block;font-family:'IBM Plex Mono',monospace;font-size:11px;letter-spacing:.18em;color:var(--teal);text-transform:uppercase;margin-bottom:10px;font-weight:500}
nav .sub{font-size:12.5px;color:var(--nav-dim);margin:4px 0 22px;line-height:1.5}
nav ol{list-style:none;margin:0;padding:0;counter-reset:s}
nav ol li{counter-increment:s;margin:1px 0}
nav ol li a{display:flex;gap:10px;align-items:baseline;text-decoration:none;color:var(--nav-ink);font-size:13.5px;padding:7px 10px;border-radius:7px}
nav ol li a::before{content:counter(s,decimal-leading-zero);font-family:'IBM Plex Mono',monospace;font-size:10.5px;color:var(--nav-dim);min-width:20px}
nav ol li a:hover{background:rgba(255,255,255,.06);color:#fff}
nav ol li a.active{background:var(--teal);color:#fff}
main{padding:0 0 100px;min-width:0}
.wrap{max-width:880px;margin:0 auto;padding:0 40px}
section{padding:50px 0 6px;scroll-margin-top:16px;border-bottom:1px solid var(--line)}
.eyebrow{font-family:'IBM Plex Mono',monospace;font-size:11.5px;letter-spacing:.2em;text-transform:uppercase;color:var(--teal-deep);font-weight:500;margin:0 0 8px}
section>.wrap>h2{font-size:31px;margin:0 0 8px}
.lede{font-size:18px;color:var(--ink-soft);margin:6px 0 20px;font-family:Spectral,serif}
p{margin:0 0 15px} h3{font-size:21px;margin:30px 0 10px} h4{font-size:15px;margin:0 0 4px;font-family:Inter,sans-serif;font-weight:700}
strong{font-weight:600;color:var(--ink)}
em.term{font-style:normal;font-weight:600;color:var(--teal-deep);border-bottom:1.5px dotted var(--teal)}
sup.cite a{font-family:'IBM Plex Mono',monospace;font-size:10px;color:var(--teal-deep);text-decoration:none;padding:0 1px}
.hero{background:var(--nav-bg);color:#fff;padding:60px 0 46px}
.hero .eyebrow{color:var(--teal)}
.hero h1{color:#fff;font-size:40px;line-height:1.08;margin:0 0 14px}
.hero p.tagline{color:#B9C7CD;font-size:18px;max-width:720px;font-family:Spectral,serif}
.stats{display:flex;flex-wrap:wrap;gap:10px;margin-top:24px}
.stat{background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.1);border-radius:10px;padding:11px 16px;min-width:120px}
.stat b{display:block;font-family:'IBM Plex Mono',monospace;font-size:20px;color:#fff;font-weight:600}
.stat span{font-size:11.5px;color:var(--nav-dim)}
.pillars{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-top:26px}
.pill{background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.12);border-radius:11px;padding:15px 17px}
.pill b{display:block;font-family:Spectral,serif;font-size:17px;color:#fff;margin-bottom:6px}
.pill span{font-size:13.5px;color:#B9C7CD;line-height:1.5}
.howto{margin-top:22px;background:rgba(14,124,134,.16);border:1px solid rgba(14,124,134,.4);border-radius:10px;padding:13px 17px;font-size:14px;color:#D6E6E8}
.howto b{color:#fff}
.note{border-radius:10px;padding:13px 17px;margin:18px 0;font-size:14.5px}
.note h4{margin:0 0 4px;font-size:14.5px} .note p{margin:0}
.note.tip{background:var(--mist);border:1px solid #BFDEE1} .note.tip h4{color:var(--teal-deep)}
.note.warn{background:var(--amber-tint);border:1px solid #EAD2A6} .note.warn h4{color:var(--amber)}
.note.flag{background:var(--coral-tint);border:1px solid #E9C4BB} .note.flag h4{color:var(--coral)}
ul.clean{margin:0 0 16px;padding-left:0;list-style:none}
ul.clean li{position:relative;padding-left:24px;margin:9px 0}
ul.clean li::before{content:"";position:absolute;left:4px;top:9px;width:7px;height:7px;border-radius:2px;background:var(--teal)}
ul.clean li.x::before{background:var(--coral)} ul.clean li.w::before{background:var(--amber)}
table{width:100%;border-collapse:collapse;margin:16px 0;font-size:14.5px}
th,td{padding:10px 12px;text-align:left;border-bottom:1px solid var(--line);vertical-align:top}
thead th{background:var(--nav-bg);color:#fff;font-family:Inter;font-weight:600;font-size:13px}
tbody tr:nth-child(even){background:#FAFCFC}
td.num{font-family:'IBM Plex Mono',monospace;color:var(--teal-deep);font-weight:500}
.tag{display:inline-block;font-family:'IBM Plex Mono',monospace;font-size:11px;padding:2px 8px;border-radius:20px}
.tag.t{background:var(--mist);color:var(--teal-deep)} .tag.a{background:var(--amber-tint);color:var(--amber)} .tag.c{background:var(--coral-tint);color:var(--coral)}
figure.figwrap{margin:22px 0 0}
.figimg{width:100%;border:1px solid var(--line);border-radius:10px;background:#fff;cursor:zoom-in;box-shadow:var(--shadow);display:block}
:root[data-lang="tr"] img.figimg.en{display:none} :root[data-lang="en"] img.figimg.tr{display:none}
figure.figwrap figcaption{font:400 12.5px 'IBM Plex Mono',monospace;color:var(--muted);margin-top:8px}
.figexp{background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:4px 16px;margin:10px 0 8px;font-size:14px}
.figexp .row{padding:10px 0;border-bottom:1px dashed var(--line)} .figexp .row:last-child{border-bottom:0}
.figexp b{display:block;color:var(--teal-deep);font-family:'IBM Plex Mono',monospace;font-size:11px;letter-spacing:.07em;text-transform:uppercase;margin-bottom:3px}
.aid{border:1.5px dashed #C9B68C;background:#FCFAF4;border-radius:12px;padding:16px 18px 14px;margin:22px 0}
.aid .aidbadge{display:inline-block;font:600 10px 'IBM Plex Mono',monospace;letter-spacing:.16em;text-transform:uppercase;color:#8A6D2F;background:#F4E9CF;border:1px solid #E3D2A6;border-radius:6px;padding:3px 9px;margin-bottom:12px}
.aid svg{width:100%;height:auto;display:block} .aid .aidcap{font:400 12.5px 'IBM Plex Mono',monospace;color:var(--muted);margin-top:12px;line-height:1.45}
ol.refs{font-size:13.5px;color:var(--ink-soft);line-height:1.5;padding-left:22px} ol.refs li{margin:7px 0}
.lightbox{position:fixed;inset:0;background:rgba(10,20,25,.93);display:none;align-items:center;justify-content:center;z-index:100;padding:24px;cursor:zoom-out}
.lightbox.open{display:flex} .lightbox img{max-width:97%;max-height:97%;border-radius:8px}
@media(max-width:880px){.shell{grid-template-columns:1fr} nav{position:static;height:auto;padding:14px} nav .sub{display:none} nav ol{display:flex;flex-wrap:wrap;gap:4px} nav ol li a::before{display:none} .wrap{padding:0 22px} .hero h1{font-size:30px} .pillars{grid-template-columns:1fr}}
"""

JS = """
const root=document.documentElement;
function setLang(l){root.dataset.lang=l;document.querySelectorAll('#langtoggle button').forEach(b=>b.classList.toggle('on',b.dataset.set===l));}
setLang('tr');
document.querySelectorAll('#langtoggle button').forEach(b=>b.onclick=()=>setLang(b.dataset.set));
const toc=document.getElementById('toc');
const secs=[...document.querySelectorAll('main section')];
secs.forEach(s=>{const h=s.querySelector('h2');const a=document.createElement('a');a.href='#'+s.id;a.innerHTML=h.innerHTML;const li=document.createElement('li');li.appendChild(a);toc.appendChild(li);});
const links=[...toc.querySelectorAll('a')];
function onScroll(){const y=scrollY+120;let cur=secs[0];secs.forEach(s=>{if(s.offsetTop<=y)cur=s;});
  links.forEach(a=>a.classList.toggle('active',a.getAttribute('href')==='#'+cur.id));
  const d=document.documentElement;document.getElementById('progress').style.width=(100*scrollY/(d.scrollHeight-d.clientHeight))+'%';}
addEventListener('scroll',onScroll,{passive:true});onScroll();
const lb=document.getElementById('lb'),lbi=document.getElementById('lbi');
document.querySelectorAll('.figimg').forEach(im=>im.onclick=()=>{lbi.src=im.src;lb.classList.add('open');});
lb.onclick=()=>lb.classList.remove('open');
"""

if __name__ == "__main__":
    main()
