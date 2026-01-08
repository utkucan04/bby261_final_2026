import re
import requests
from bs4 import BeautifulSoup
from bs4.element import NavigableString
from rommenu import MenuSistemi

ETKINLIK_URL = "https://etkinlikler.hacettepe.edu.tr/"
HABER_URL = "https://gazete.hacettepe.edu.tr/"
HEADERS = {"User-Agent": "Mozilla/5.0"}

DATE_META_RE = re.compile(r"\d{2}\.\d{2}\.\d{4}\s+\d{2}:\d{2}\s*\|\s*.+")  

def clean(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())

def get_soup(url: str) -> BeautifulSoup:
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    return BeautifulSoup(r.text, "html.parser")

def parse_cards_by_devami(soup: BeautifulSoup, devami_text_regex: str, limit: int = 10, want_meta: bool = False):
    
    items = []
    devami_links = soup.find_all("a", string=re.compile(devami_text_regex, re.IGNORECASE))

    for a in devami_links:
        prev_texts = []
        for el in a.previous_elements:
            if isinstance(el, NavigableString):
                t = clean(str(el))
                if not t:
                    continue
                if re.fullmatch(devami_text_regex, t, flags=re.IGNORECASE):
                    continue
                # tekrarları alma
                if t in prev_texts:
                    continue
                prev_texts.append(t)
                if len(prev_texts) >= 2:
                    break

        if len(prev_texts) < 2:
            continue

        summary = prev_texts[0]
        title = prev_texts[1]

        meta = ""
        if want_meta:
            # Devamı'nın ALTINDAN: ilk tarih|kategori satırını yakala
            for el in a.next_elements:
                if isinstance(el, NavigableString):
                    t = clean(str(el))
                    if not t:
                        continue
                    if DATE_META_RE.search(t):
                        meta = t
                        break

        items.append({"title": title, "summary": summary, "meta": meta})
        if len(items) >= limit:
            break

    return items

def etkinlikleri_goster():
    soup = get_soup(ETKINLIK_URL)
    items = parse_cards_by_devami(soup, r"Devamı", limit=10, want_meta=True)

    print("\nETKİNLİKLER")
    print("-" * 60)

    if not items:
        print("Etkinlik bulunamadı (sayfa yapısı değişmiş olabilir).")
        return

    for i, it in enumerate(items, 1):
        print(f"{i}) {it['title']}")
        if it["meta"]:
            print(f"   {it['meta']}")
        print(f"   {it['summary']}\n")

def haberleri_goster():
    soup = get_soup(HABER_URL)
    items = parse_cards_by_devami(soup, r"Devamı\.{0,3}", limit=10, want_meta=False)  # Devamı... dahil

    print("\nHABERLER")
    print("-" * 60)

    if not items:
        print("Haber bulunamadı (sayfa yapısı değişmiş olabilir).")
        return

    for i, it in enumerate(items, 1):
        print(f"{i}) {it['title']}")
        print(f"   {it['summary']}\n")

def main():
    MenuSistemi.karsilama("HÜ Etkinlik & Haber")

    menu_map = {
        "Etkinlikleri listele": etkinlikleri_goster,
        "Haberleri listele": haberleri_goster,
    }

    MenuSistemi.menuyuCalistir(menu_map)

if __name__ == "__main__":
    main()
