#!/usr/bin/env python3
"""
Classify and distribute Roger推薦 (1805 tracks) into target playlists.
Uses /items API endpoints directly.
"""
import json, time, urllib.request, urllib.error, re
from collections import defaultdict

with open('C:/Github/spotify-mcp-server/spotify-config.json') as f:
    config = json.load(f)

TOKEN = config['accessToken']
SOURCE = '1cgwZLMj6Vf6DUqr9OWbDz'  # Roger推薦

PLAYLISTS = {
    'vocal':     '2tZEYcn1PSe0FBvNQu0w6T',
    'sounds':    '2pdVzlisPDj33mk5t3FdHe',
    'guofeng':   '1SVQN5CUvKXyuT4l2pSTed',
    'jazz':      '756kh5zJLE1CLenI0VI05j',
    'movie':     '469KbI3xpL9Xi7quO35g25',
    'anime':     '4NHlnsgVcTc9wKxSF2SluK',
    'mandarin':  '7xrf7NkaHNvXKWYaQknIT9',
    'classical': '0lXyhKtZumv0tbsxLsyvq2',
    'game':      '6w12L3CmTbnNnLqwxGzo6S',
    'piano':     '1rrHLpD1gBmMWAc2t4LwLq',
    'pop':       '1aLGO0PgxkL1PpLjwgri5b',
}

def api_get(url):
    req = urllib.request.Request(url, headers={'Authorization': f'Bearer {TOKEN}'})
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

def api_post(url, data):
    body = json.dumps(data).encode()
    req = urllib.request.Request(url, data=body, method='POST',
        headers={'Authorization': f'Bearer {TOKEN}', 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return {'error': e.read().decode()}

def has_chinese(text):
    return any('一' <= c <= '鿿' for c in text)

def has_japanese_kana(text):
    return any('぀' <= c <= 'ヿ' for c in text)

CLASSICAL_COMPOSERS = {
    'bach','mozart','beethoven','chopin','debussy','vivaldi','schubert','brahms',
    'liszt','handel','haydn','schumann','mendelssohn','tchaikovsky','rachmaninoff',
    'dvorak','sibelius','ravel','satie','pachelbel','corelli','telemann','purcell',
    'albinoni','monteverdi','boccherini','paganini','verdi','puccini','rossini',
}
CLASSICAL_KEYWORDS = {
    'royal philharmonic','london symphony','berlin philharmonic','philharmonic orchestra',
    'string quartet','chamber music','jean-efflam bavouzet','nino rota','nigel hess',
    'lucas jussen','arthur jussen','2cellos','angèle dubeau','la pietà',
    'yo-yo ma','itzhak perlman','joshua bell','lang lang','angela hewitt',
}
JAZZ_ARTISTS = {
    'nat king cole','frank sinatra','ella fitzgerald','louis armstrong','miles davis',
    'john coltrane','billie holiday','diana krall','norah jones','laura fygi',
    'emilie-claire barlow','stacey kent','curtis stigers','michael bublé','michael buble',
    'tony bennett','harry connick','bossa nova','stan getz',
}
PIANO_ARTISTS = {
    'yiruma','richard clayderman','ludovico einaudi','george winston','naoki sato',
    'brice davoli','kevin kern','david lanz','jim brickman','maksim',
}
SOUNDS_KEYWORDS = {
    '432hz','healing','meditation','chakra','sacred','solfeggio','binaural',
    'tibetan','gregorian','chant','mantra','reiki','ambient','atmospheric',
    'theta','rune','seiðr','norse','mystwood','altáriel','quenya','seiðrleið',
    'auraliel','zero error','yorishiro','神の宿る場','cristina serrato',
    'castle in the sky',
}
ANIME_KEYWORDS = {
    'naruto','one piece','dragon ball','attack on titan','shingeki','evangelion',
    'gundam','bleach','fullmetal','ghibli','spirited','totoro','princess mononoke',
    'sword art','demon slayer','kimetsu','my hero academia','boku no hero',
    'death note','cowboy bebop','neon genesis','ranma','sailor moon','doraemon',
    'studio ghibli','miyazaki','joe hisaishi','yoko kanno',
}
GAME_KEYWORDS = {
    'final fantasy','kingdom hearts','zelda','pokemon','mario','sonic','halo',
    'skyrim','undertale','video game','nobuo uematsu','koji kondo','yasunori mitsuda',
    'ff7','ff8','ff9','ff10','chrono trigger','nier','persona','fire emblem',
}
MOVIE_KEYWORDS = {
    'out of africa','ladies in lavender','theme from','film score','movie theme',
    'james bond','harry potter','lord of the rings','pirates of the caribbean',
    'schindler','jurassic','titanic','interstellar','inception','la la land',
    'ennio morricone','john williams','hans zimmer','alan silvestri','howard shore',
}
MANDARIN_ARTISTS = {
    'della','陳嘉樺','fish leong','梁靜茹','nan quan mama','南拳媽媽',
    'teresa teng','鄧麗君','wanting','曲婉婷','jay chou','周杰倫',
    'mayday','五月天','sodagreen','蘇打綠','jj lin','林俊傑',
    'rainie yang','楊丞琳','a-mei','張惠妹','angela chang','張韶涵',
    'elva hsiao','蕭亞軒','hebe','田馥甄','tia lee','李佳薇',
    'lala hsu','徐佳瑩','julia peng','彭佳慧','eason chan','陳奕迅',
    'nicholas teo','張棟樑','energy','energy男團','s.h.e','fahrenheit','飛輪海',
    'show luo','羅志祥','aaron yan','炎亞綸','vanness wu','吳建豪',
    'tank','弦子','yoga lin','林宥嘉','wu bai','伍佰','lo ta-yu','羅大佑',
    'cheer chen','陳綺貞','david tao','陶喆','pin kuan','品冠','power station',
    'michael wong','光良','lee hom','王力宏','ren xian qi','任賢齊',
}
GUOFENG_KEYWORDS = {
    '古風','國風','guqin','erhu','pipa','二胡','琵琶','古琴','笛子','簫',
    'chinese traditional','chinese folk','民樂','絲竹','宮調',
}
VOCAL_ARTISTS = {
    'hayley westenra','loren allred','cimorelli','charlotte church',
    'sarah brightman','andrea bocelli','katharine jenkins','il divo',
    'ten tenors','celtic woman','jackie evancho','connie talbot',
}

def classify(name, artists, album):
    n = name.lower()
    a = ' '.join(artists).lower()
    al = (album or '').lower()
    txt = f"{n} {a} {al}"

    # Classical composers
    for c in CLASSICAL_COMPOSERS:
        if c in a or c in al:
            if any(p in a for p in PIANO_ARTISTS) or 'piano' in n or 'arabesque' in n or 'nocturne' in n or 'étude' in n or 'prelude' in n:
                return 'piano'
            return 'classical'
    for c in CLASSICAL_KEYWORDS:
        if c in txt:
            return 'classical'

    # Jazz
    for j in JAZZ_ARTISTS:
        if j in txt:
            return 'jazz'
    if 'jazz' in txt:
        return 'jazz'

    # Piano solos
    for p in PIANO_ARTISTS:
        if p in a:
            return 'piano'

    # Sounds / Ambient / Spiritual
    for s in SOUNDS_KEYWORDS:
        if s.lower() in txt:
            return 'sounds'
    # Japanese kana = spiritual/ambient by default (unless clearly anime)
    if has_japanese_kana(name) or has_japanese_kana(''.join(artists)):
        for ak in ANIME_KEYWORDS:
            if ak in txt:
                return 'anime'
        return 'sounds'

    # Game OST
    for g in GAME_KEYWORDS:
        if g in txt:
            return 'game'

    # Movie OST
    for m in MOVIE_KEYWORDS:
        if m in txt:
            return 'movie'

    # Anime
    for ak in ANIME_KEYWORDS:
        if ak in txt:
            return 'anime'

    # 國風
    for gf in GUOFENG_KEYWORDS:
        if gf.lower() in txt:
            return 'guofeng'

    # Mandarin artists (explicit list)
    for ma in MANDARIN_ARTISTS:
        if ma.lower() in txt:
            return 'mandarin'
    # Chinese characters in name or artist (non-Japanese) → Mandarin
    if has_chinese(name) or any(has_chinese(ar) for ar in artists):
        return 'mandarin'

    # Vocal artists
    for va in VOCAL_ARTISTS:
        if va in txt:
            return 'vocal'

    # Default: Western pop
    return 'pop'

# --- Fetch all tracks from source ---
print(f"Fetching all tracks from Roger推薦...")
all_tracks = []
offset = 0
limit = 50
while True:
    url = f"https://api.spotify.com/v1/playlists/{SOURCE}/items?limit={limit}&offset={offset}"
    data = api_get(url)
    items = data.get('items', [])
    for item in items:
        tr = item.get('track') or item.get('item')
        if tr and tr.get('id') and tr.get('type') == 'track':
            all_tracks.append({
                'id': tr['id'],
                'name': tr.get('name', ''),
                'artists': [a['name'] for a in tr.get('artists', [])],
                'album': tr.get('album', {}).get('name', ''),
            })
    total = data.get('total', 0)
    offset += len(items)
    print(f"  Fetched {offset}/{total}...")
    if offset >= total or not items:
        break
    time.sleep(0.1)

print(f"Total tracks fetched: {len(all_tracks)}")

# --- Fetch existing tracks in each target playlist (for dedup) ---
print("Loading existing tracks in target playlists...")
existing = {cat: set() for cat in PLAYLISTS}
for cat, pid in PLAYLISTS.items():
    off = 0
    while True:
        url = f"https://api.spotify.com/v1/playlists/{pid}/items?limit=50&offset={off}"
        try:
            data = api_get(url)
        except Exception:
            break
        items = data.get('items', [])
        for item in items:
            tr = item.get('track') or item.get('item')
            if tr and tr.get('id'):
                existing[cat].add(tr['id'])
        off += len(items)
        total = data.get('total', 0)
        if off >= total or not items:
            break
    print(f"  {cat}: {len(existing[cat])} existing tracks")
    time.sleep(0.1)

# --- Classify ---
print("\nClassifying tracks...")
buckets = defaultdict(list)
for t in all_tracks:
    cat = classify(t['name'], t['artists'], t['album'])
    if t['id'] not in existing[cat]:
        buckets[cat].append(t['id'])

print("\nClassification results:")
for cat, ids in sorted(buckets.items(), key=lambda x: -len(x[1])):
    print(f"  {cat:12s}: {len(ids)} new tracks")

# --- Add to playlists in batches of 50 ---
print("\nAdding tracks to playlists...")
total_added = 0
for cat, ids in buckets.items():
    pid = PLAYLISTS[cat]
    added = 0
    for i in range(0, len(ids), 50):
        batch = ids[i:i+50]
        result = api_post(
            f"https://api.spotify.com/v1/playlists/{pid}/items",
            {'uris': [f'spotify:track:{tid}' for tid in batch]}
        )
        if 'error' in result:
            print(f"  ERROR {cat} batch {i//50+1}: {result['error']}")
        else:
            added += len(batch)
        time.sleep(0.2)
    print(f"  {cat:12s}: added {added}/{len(ids)}")
    total_added += added

print(f"\nDone! Total added: {total_added} tracks across {len(buckets)} playlists.")
