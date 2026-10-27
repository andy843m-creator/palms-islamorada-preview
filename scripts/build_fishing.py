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
    data = {"generated": now.isoformat(timespec="minutes"),
            "generated_label": now.strftime("%A, %B %-d, %Y at %-I:%M %p ET"),
            "location": "The Palms of Islamorada, MM 79.9 oceanside",
            "stations": {"tide_ocean": TIDE_OCEAN, "tide_bay": TIDE_BAY, "water_temp": WTEMP,
                         "marine_zones": [z for z, _ in ZONES]},
            "days": out_days, "marine": marine, "water_temp": water, "errors": errors}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f: json.dump(data, f, indent=1)
    print("wrote", OUT, "errors:", errors)
    if len(errors) >= 4: sys.exit(1)

if __name__ == "__main__":
    main()
