#!/usr/bin/env python3
"""Build data/fishing.json for the Palms Fishing Report page.
Stdlib only. Free, keyless public sources:
  - NOAA CO-OPS tide predictions, station 8723814 (Upper Matecumbe Key, Hawk Channel - oceanside)
    and 8723808 (Islamorada, Upper Matecumbe Key, Florida Bay - bayside)
  - NOAA CO-OPS water temperature, station 8723970 (Vaca Key) - nearest active water-temp sensor
  - NWS marine zone forecasts GMZ042 (Hawk Channel Ocean Reef to Craig Key) and GMZ052 (Straits, out 20 NM)
Sun, moon and solunar times are computed here (low-precision astronomy, estimates).
"""
import json, math, os, sys, urllib.request, datetime as dt
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")
LAT, LON = 24.9300, -80.6110   # The Palms, MM 79.9 oceanside
UA = {"User-Agent": "palms-islamorada-preview fishing report (github.com/andy843m-creator)"}
OUT = os.path.join(os.path.dirname(__file__), "..", "data", "fishing.json")
TIDE_OCEAN, TIDE_BAY, WTEMP = "8723814", "8723808", "8723970"
ZONES = [("GMZ042", "Hawk Channel, Ocean Reef to Craig Key (out to the reef)"),
         ("GMZ052", "Straits of Florida, Ocean Reef to Craig Key (out 20 NM)")]

def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.loads(r.read().decode())

# ---------- astronomy (low precision) ----------
def jd(t):  # t aware datetime
    return t.astimezone(dt.timezone.utc).timestamp() / 86400.0 + 2440587.5
def rev(x): return x % 360.0
R = math.radians; D = math.degrees

def sun_radec(j):
    n = j - 2451545.0
    L = rev(280.460 + 0.9856474 * n); g = R(rev(357.528 + 0.9856003 * n))
    lam = R(L + 1.915 * math.sin(g) + 0.020 * math.sin(2 * g))
    eps = R(23.439 - 0.0000004 * n)
    ra = math.atan2(math.cos(eps) * math.sin(lam), math.cos(lam))
    dec = math.asin(math.sin(eps) * math.sin(lam))
    return ra, dec, D(lam)

def moon_radec(j):
    T = (j - 2451545.0) / 36525.0
    Lp = R(rev(218.32 + 481267.881 * T)); M = R(rev(134.9 + 477198.85 * T))
    Ms = R(rev(357.5 + 35999.05 * T)); Dd = R(rev(297.85 + 445267.11 * T)); F = R(rev(93.27 + 483202.02 * T))
    lam = D(Lp) + 6.29 * math.sin(M) - 1.27 * math.sin(M - 2 * Dd) + 0.66 * math.sin(2 * Dd) \
        + 0.21 * math.sin(2 * M) - 0.19 * math.sin(Ms) - 0.11 * math.sin(2 * F)
    bet = 5.13 * math.sin(F) + 0.28 * math.sin(M + F) - 0.28 * math.sin(F - M) - 0.17 * math.sin(F - 2 * Dd)
    pi = 0.9508 + 0.0518 * math.cos(M) + 0.0095 * math.cos(M - 2 * Dd) + 0.0078 * math.cos(2 * Dd) + 0.0028 * math.cos(2 * M)
    l, b, eps = R(lam), R(bet), R(23.439 - 0.013 * T)
    x = math.cos(b) * math.cos(l); y = math.cos(eps) * math.cos(b) * math.sin(l) - math.sin(eps) * math.sin(b)
    z = math.sin(eps) * math.cos(b) * math.sin(l) + math.cos(eps) * math.sin(b)
    return math.atan2(y, x), math.asin(z), rev(lam), pi

def alt(j, ra, dec):
    gmst = rev(280.46061837 + 360.98564736629 * (j - 2451545.0))
    H = R(gmst + LON) - ra
    la = R(LAT)
    return D(math.asin(math.sin(la) * math.sin(dec) + math.cos(la) * math.cos(dec) * math.cos(H))), H

def events(day, body):
    """rise/set (and transit/antitransit for moon) on local date `day` by 2-minute scan."""
    start = dt.datetime(day.year, day.month, day.day, tzinfo=ET)
    out = {"rise": None, "set": None, "transit": None, "under": None}
    prev = None
    for k in range(0, 24 * 30 + 1):
        t = start + dt.timedelta(minutes=2 * k)
        if t.date() != day and k: break
        j = jd(t)
        if body == "sun":
            ra, dec, _ = sun_radec(j); h0 = -0.833
        else:
            ra, dec, _, pi = moon_radec(j); h0 = 0.7275 * pi - 0.5667
        a, H = alt(j, ra, dec)
        ha = (D(H) + 180) % 360 - 180  # hour angle -180..180
        if prev:
            pa, pha, pt = prev
            if pa < h0 <= a and not out["rise"]: out["rise"] = t
            if pa >= h0 > a and not out["set"]: out["set"] = t
            if pha < 0 <= ha and not out["transit"]: out["transit"] = t
            if pha > 150 and ha < -150 and not out["under"]: out["under"] = t
        prev = (a, ha, t)
    return out

def moon_phase(t):
    j = jd(t)
    _, _, slon = sun_radec(j); _, _, mlon, _ = moon_radec(j)
    el = rev(mlon - slon)
    illum = (1 - math.cos(R(el))) / 2
    names = ["New Moon", "Waxing Crescent", "First Quarter", "Waxing Gibbous", "Full Moon",
             "Waning Gibbous", "Last Quarter", "Waning Crescent"]
    return names[int(((el + 22.5) % 360) // 45)], round(illum * 100), round(el, 1)

def hm(t): return t.strftime("%-I:%M %p") if t else None
def window(t, mins):
    if not t: return None
    return f"{hm(t - dt.timedelta(minutes=mins))} - {hm(t + dt.timedelta(minutes=mins))}"

def rating(name, illum, el):
    # traditional solunar lore: best near new/full moon
    d = min(abs(el - 0), abs(el - 180), abs(el - 360))
    return "Excellent" if d < 25 else "Good" if d < 55 else "Fair"


# ---------- weekly report cards (rule-based, automated) ----------
NEAR = (24.92, -80.60)   # Islamorada ocean side (Hawk Channel)
OFF = (24.80, -80.40)    # offshore, toward the reef line / Gulf Stream edge
# seasonal base score per month Jan..Dec: 3 excellent, 2 good, 1 fair (typical Upper Keys patterns)
SEASON = {
 "backcountry": [("Tarpon",      [1,1,2,3,3,3,2,2,2,2,1,1]),
                 ("Snook",       [1,1,2,2,2,2,2,2,3,3,2,1]),
                 ("Redfish",     [3,3,2,2,2,2,2,2,2,3,3,3]),
                 ("Jacks",       [3,3,2,2,2,2,2,2,2,2,3,3]),
                 ("Sea trout",   [3,3,2,2,1,1,1,1,2,2,3,3])],
 "flats":       [("Bonefish",    [1,1,2,3,3,2,2,2,3,3,2,1]),
                 ("Permit",      [1,1,2,3,3,2,2,2,2,2,2,1]),
                 ("Tarpon",      [1,1,2,3,3,3,2,2,2,2,1,1]),
                 ("Barracuda",   [3,3,2,2,2,2,2,2,2,2,3,3]),
                 ("Sea trout",   [3,3,2,2,1,1,1,1,2,2,3,3])],
 "reef":        [("Yellowtail snapper", [2,2,2,3,3,3,3,3,3,3,3,2]),
                 ("Mutton snapper",     [2,2,2,3,3,3,2,2,2,2,2,2]),
                 ("Grouper",            [1,1,1,1,2,2,2,2,2,3,3,3]),
                 ("Mangrove snapper",   [1,1,2,2,2,3,3,3,2,2,2,1]),
                 ("Hogfish",            [2,2,2,2,2,2,2,2,2,2,2,2])],
 "offshore":    [("Sailfish",    [3,3,2,1,1,1,1,1,1,2,3,3]),
                 ("Mahi",        [1,1,2,3,3,3,3,2,2,1,1,1]),
                 ("Blackfin tuna",[2,2,3,3,2,2,2,2,2,2,2,2]),
                 ("Wahoo",       [2,2,1,1,1,1,1,1,2,3,3,2]),
                 ("Kingfish",    [3,3,2,1,1,1,1,1,1,2,3,3])],
}
ICON = {"backcountry": "mangrove", "flats": "flats", "reef": "reef", "offshore": "offshore"}
TITLE = {"backcountry": "Backcountry", "flats": "Flats", "reef": "Reef", "offshore": "Offshore / Deep Sea"}

def reg_note(sp, month):
    # verified against myfwc.com, Oct 2026. Monroe County is in FWC's Southwest snook region.
    if sp == "Snook":
        return "harvest open" if month in (3, 4, 10, 11) else "catch and release only this month"
    if sp == "Grouper":
        if month <= 4: return "closed Jan 1 - Apr 30"
        return "gag closed after Aug 1; others open, rules apply" if month >= 8 else "season rules apply"
    if sp in ("Tarpon", "Bonefish"): return "catch and release"
    if sp == "Permit": return "special Keys permit rules"
    return None

def build_report(now, water_f):
    m = now.month
    errs = []
    def om(url):
        try: return get(url)
        except Exception as e: errs.append(f"open-meteo: {e}"); return None
    wind = om(f"https://api.open-meteo.com/v1/forecast?latitude={NEAR[0]}&longitude={NEAR[1]}"
              "&daily=wind_speed_10m_max,wind_gusts_10m_max,wind_direction_10m_dominant"
              "&wind_speed_unit=kn&timezone=America%2FNew_York&forecast_days=7")
    near = om(f"https://marine-api.open-meteo.com/v1/marine?latitude={NEAR[0]}&longitude={NEAR[1]}"
              "&daily=wave_height_max&hourly=sea_surface_temperature&timezone=America%2FNew_York&forecast_days=7")
    off = om(f"https://marine-api.open-meteo.com/v1/marine?latitude={OFF[0]}&longitude={OFF[1]}"
             "&daily=wave_height_max&hourly=sea_surface_temperature&timezone=America%2FNew_York&forecast_days=7")
    ft = lambda x: x * 3.28084
    cond = {}
    days7 = []
    if wind:
        d = wind["daily"]
        for i, t in enumerate(d["time"]):
            dirs = ["N","NE","E","SE","S","SW","W","NW"]
            days7.append({"date": t, "day": dt.date.fromisoformat(t).strftime("%a"),
                          "wind_kt": round(d["wind_speed_10m_max"][i]), "gust_kt": round(d["wind_gusts_10m_max"][i]),
                          "dir": dirs[int(((d["wind_direction_10m_dominant"][i] or 0) + 22.5) % 360 // 45)]})
        w = [x["wind_kt"] for x in days7]
        first, last = sum(w[:2]) / 2, sum(w[-3:]) / 3
        trend = "dropping" if last < first - 4 else "building" if last > first + 4 else "steady"
        cond["wind_trend"] = trend
        cond["wind_now"] = f'{days7[0]["dir"]} {w[0]} kt, gusts {days7[0]["gust_kt"]} kt'
        # find the first day winds fall to 12 kt or less
        calm = next((x for x in days7 if x["wind_kt"] <= 12), None)
        if trend == "dropping":
            out = f'Winds are forecast to drop from about {w[0]} knots today to around {round(last)} knots by {days7[-1]["day"]}.'
        elif trend == "building":
            out = f'Winds are forecast to build from about {w[0]} knots today to around {round(last)} knots by {days7[-1]["day"]}.'
        else:
            out = f'Winds are forecast to stay fairly steady, around {round(sum(w)/len(w))} knots most days.'
        if calm: out += f' The first lighter day (12 knots or less) looks like {calm["day"]}.' if calm is not days7[0] else ' Today already looks light.'
        cond["outlook"] = out
        cond["rough_now"] = w[0] >= 18
        cond["calm_ahead"] = calm is not None
    def seas(x):
        if not x: return None
        v = [ft(a) for a in x["daily"]["wave_height_max"] if a is not None]
        return (round(min(v)), round(max(v)), round(v[0]))
    sn, so = seas(near), seas(off)
    if sn: cond["seas_near"] = f"{sn[0]}-{sn[1]} ft over the week (today up to {sn[2]} ft)"
    if so: cond["seas_off"] = f"{so[0]}-{so[1]} ft over the week (today up to {so[2]} ft)"
    temps = []
    for x in (near, off):
        if x: temps += [a for a in x["hourly"]["sea_surface_temperature"] if a is not None]
    if water_f: temps.append((water_f - 32) / 1.8)
    if temps:
        lo, hi = round(min(temps) * 1.8 + 32), round(max(temps) * 1.8 + 32)
        cond["water"] = f"{lo}-{hi}\u00b0F" if lo != hi else f"{lo}\u00b0F"
        cond["water_hi"] = hi; cond["water_lo"] = lo
    ph, il, el = moon_phase(now)
    springish = min(abs(el), abs(el - 180), abs(el - 360)) < 40
    cond["moon"] = f"{ph}, {il}% lit"
    cond["tides"] = ("Stronger tidal movement this week around the " + ("full" if abs(el-180) < 40 else "new") +
                     " moon. Moving water, especially the incoming tide, is traditionally the better bite.") if springish else \
                    "Moderate tides this week (between quarter moons). Plan around moving water rather than slack tide."
    cards = []
    rough, calm_ahead = cond.get("rough_now"), cond.get("calm_ahead")
    lo = cond.get("water_lo", 80)
    for key, lst in SEASON.items():
        sp_out = []
        for name, arr in lst:
            sc = arr[m - 1]
            if key in ("flats",) and rough and not calm_ahead: sc -= 1
            if key == "offshore" and so and so[1] >= 7 and not calm_ahead: sc -= 1
            if name in ("Tarpon", "Bonefish", "Permit") and lo < 70: sc -= 1
            sc = max(1, min(3, sc))
            sp_out.append({"name": name, "rating": ["", "Fair", "Good", "Excellent"][sc], "note": reg_note(name, m)})
        sp_out.sort(key=lambda x: -["Fair", "Good", "Excellent"].index(x["rating"]))
        best = [x["name"] for x in sp_out if x["rating"] == "Excellent"] or [sp_out[0]["name"]]
        nm = [b.lower() for b in best[:3]]
        lead = nm[0] if len(nm) == 1 else ", ".join(nm[:-1]) + " and " + nm[-1]
        txt = f"Typical for {now.strftime('%B')}: {lead} {'is usually' if len(nm) == 1 else 'are usually'} the top target{'s' if len(nm) > 1 else ''}. "
        if key == "backcountry":
            txt += "Bay and mangrove shorelines are the most protected water when the wind blows." if rough else "Light wind makes the mangrove shorelines and channels easy to fish."
        elif key == "flats":
            txt += ("Sight fishing needs calm, clear water, so wait for the lighter days." if rough else "Light wind and clear water favor sight fishing.")
        elif key == "reef":
            txt += ("Seas on the reef line are rough early in the week; " + ("conditions look better later in the week." if calm_ahead else "watch the forecast.")) if rough else "Seas look manageable for the reef line."
        else:
            txt += (f"Offshore seas reach about {so[1]} ft at times this week, so pick your day." if so and so[1] >= 5 else "Offshore seas look fishable for most of the week.")
        if springish and key in ("reef", "backcountry"): txt += " Stronger moon tides should keep water moving."
        cards.append({"key": key, "title": TITLE[key], "text": txt, "species": sp_out})
    return {"cards": cards, "conditions": cond, "wind_days": days7}, errs

# ---------- build ----------
def main():
    now = dt.datetime.now(ET)
    today = now.date()
    days = [today + dt.timedelta(days=i) for i in range(7)]
    errors = []
    b = today.strftime("%Y%m%d")
    tides = {}
    for key, st in (("ocean", TIDE_OCEAN), ("bay", TIDE_BAY)):
        try:
            d = get("https://api.tidesandcurrents.noaa.gov/api/prod/datagetter?product=predictions"
                    f"&station={st}&begin_date={b}&range=168&datum=MLLW&interval=hilo&units=english"
                    "&time_zone=lst_ldt&format=json&application=palms_islamorada")
            for p in d["predictions"]:
                t = dt.datetime.strptime(p["t"], "%Y-%m-%d %H:%M")
                tides.setdefault((key, t.date()), []).append(
                    {"type": "High" if p["type"] == "H" else "Low", "time": t.strftime("%-I:%M %p"),
                     "ft": round(float(p["v"]), 1) + 0.0})
        except Exception as e:
            errors.append(f"tides {st}: {e}")
    out_days = []
    for d in days:
        s = events(d, "sun"); m = events(d, "moon")
        noon = dt.datetime(d.year, d.month, d.day, 12, tzinfo=ET)
        ph, il, el = moon_phase(noon)
        majors = [w for w in (window(m["transit"], 60), window(m["under"], 60)) if w]
        minors = [w for w in (window(m["rise"], 30), window(m["set"], 30)) if w]
        out_days.append({
            "date": d.isoformat(), "label": d.strftime("%a, %b %-d"),
            "sunrise": hm(s["rise"]), "sunset": hm(s["set"]),
            "moon": {"phase": ph, "illumination": il, "rise": hm(m["rise"]), "set": hm(m["set"])},
            "solunar": {"major": majors, "minor": minors, "rating": rating(ph, il, el)},
            "tides_ocean": tides.get(("ocean", d), []), "tides_bay": tides.get(("bay", d), []),
        })
    marine = []
    for z, nm in ZONES:
        try:
            p = get(f"https://api.weather.gov/zones/forecast/{z}/forecast")["properties"]
            marine.append({"zone": z, "name": nm, "updated": p.get("updated"),
                           "periods": [{"name": x["name"], "text": x["detailedForecast"]} for x in p["periods"][:6]]})
        except Exception as e:
            errors.append(f"marine {z}: {e}")
    water = None
    try:
        w = get("https://api.tidesandcurrents.noaa.gov/api/prod/datagetter?product=water_temperature"
                f"&station={WTEMP}&date=latest&units=english&time_zone=lst_ldt&format=json&application=palms_islamorada")
        x = w["data"][0]
        water = {"f": float(x["v"]), "time": dt.datetime.strptime(x["t"], "%Y-%m-%d %H:%M").strftime("%b %-d, %-I:%M %p"),
                 "station": f"{w['metadata']['name']} ({WTEMP})"}
    except Exception as e:
        errors.append(f"water temp: {e}")
    rep, e2 = build_report(now, water["f"] if water else None)
    errors += e2
    data = {"report": rep, "generated": now.isoformat(timespec="minutes"),
            "generated_label": now.strftime("%A, %B %-d, %Y at %-I:%M %p ET"),
            "location": "The Palms of Islamorada, MM 79.9 oceanside",
            "stations": {"tide_ocean": TIDE_OCEAN, "tide_bay": TIDE_BAY, "water_temp": WTEMP,
                         "marine_zones": [z for z, _ in ZONES], "open_meteo_near": NEAR, "open_meteo_offshore": OFF},
            "days": out_days, "marine": marine, "water_temp": water, "errors": errors}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f: json.dump(data, f, indent=1)
    print("wrote", OUT, "errors:", errors)
    if len(errors) >= 5: sys.exit(1)

if __name__ == "__main__":
    main()
