import json, requests, concurrent.futures, time, os
from bs4 import BeautifulSoup

try:
    CLIENT_ID = os.environ["CLIENT_ID"]
except KeyError:
    CLIENT_ID = "Token not available!"

anime_manual = {
    "a3": 39184,
    "ai-mai-mi": 16169,
    "astraea-testament-the-good-witch-of-the-west": 942,
    "blood-of-zeus": None,
    "castlevania": None,
    "codebreaker": 11703,
    "dgray-man": 1482,
    "date-a-bullet": 40416,
    "dota-dragons-blood": None,
    "dragonball-z-kai": 6033,
    "fatekaleid-liner-prisma-illya": 14829,
    "fatestay-night-heavens-feel-i-presage-flower": 25537,
    "fatestay-night-heavens-feel-ii-lost-butterfly": 33049,
    "fatestay-night-heavens-feel-iii-spring-song": 33050,
    "fox-spirit-matchmaker": 31499,
    "garden-of-sinners": 2593,
    "tengen-toppa-gurren-lagann": 2001,
    "idolmster-cinderella-girls-u149": 51536,
    "junjo-romantica": 3092,
    "k-on": 5680,
    "land-of-the-lustrous": 35557,
    "love-chunibyo-other-delusions": 14741,
    "loveless-sd-theatre": 149,
    "maesetsu": 40085,
    "mila-superstar": 1550,
    "naruto-spin-off-rock-lee-his-ninja-pals": 12979,
    "norn9": 31452,
    "ntr-netsuzou-trap": 34383,
    "onyx-equinox": None,
    "pacific-rim-the-black": None,
    "persona-3-the-movie": 14407,
    "quan-zhi-fa-shi": 34300,
    "queens-blade": 4719,
    "rezero-starting-life-in-another-world-directors-cut": 31240,
    "rosario-vampire": 2993,
    "rwby": None,
    "sankarea-undying-love": 11499,
    "star-blazers-2199-space-battleship-yamato": 12029,
    "super-dragonball-heroes": 37885,
    "tada-kun-wa-koi-o-shinai": 36470,
    "takt-opdestiny": 48556,
    "tenchi-muyo": 539,
    "the-red-turtle": None,
    "thunderbolt-fantas": None,
    "todays-menu-for-the-emiya-family": 37033,
    "towanoquon": 10294,
    "x": 156
}

def get_mal_id(id, info):
    # Get from manual ids
    mal_id = anime_manual.get(id)
    if mal_id:
        return mal_id

    # Get from IMDB id
    if info["imdb-id"]:
        for anime in anime_list_full:
            if anime.get("imdb_id") == info["imdb-id"]:
                if anime.get("mal_id"):
                    return anime.get("mal_id")

    # Get from title / synonyms
    info_titles = [info["title"]]
    alternative_titles = info["alternative-titles"].split(', ')
    info_titles.extend(alternative_titles)
    for anime in anime_offline_database["data"]:
        current_list_titles = [anime.get("title")]
        current_list_titles.extend(anime.get("synonyms"))
        for title in current_list_titles:
            if title in info_titles and anime.get("animeSeason").get("year") == int(info["start-date"]) and ((anime.get("type") == "TV" or anime.get("type") == "ONA") if len(info["seasons"]["1"]) > 1 else (anime.get("type") == "MOVIE")):
                for source in anime.get("sources"):
                    if source.startswith('https://myanimelist.net/anime/'):
                        return int(source.replace('https://myanimelist.net/anime/', ''))
    
    # Get from Anime Planet id
    for anime in anime_list_full:
        if anime.get("anime-planet_id") == id:
            if anime.get("mal_id"):
                return anime.get("mal_id")
    
    # Get from title / synonyms with no type restriction
    for anime in anime_offline_database["data"]:
        current_list_titles = [anime.get("title")]
        current_list_titles.extend(anime.get("synonyms"))
        for title in current_list_titles:
            if title in info_titles and anime.get("animeSeason").get("year") == int(info["start-date"]):
                for source in anime.get("sources"):
                    if source.startswith('https://myanimelist.net/anime/'):
                        return int(source.replace('https://myanimelist.net/anime/', ''))
    
    return None

def get_season_info(id, season):
    html_page = aniworld_session.get(
        f"https://aniworld.to/anime/stream/{id}/staffel-{season}"
    )
    soup = BeautifulSoup(html_page.content, "html.parser")

    container = soup.select_one(f"#season{season}")
    episodes = container.select("tr")
    season_data = []
    for episode in episodes:
        german_title = episode.select("strong")[0].text
        english_title = episode.select("span")[0].text
        hosts = [i["title"] for i in episode.select("i")]
        languages = [
            img["src"].replace(".svg", "").replace("/public/img/", "")
            for img in episode.select("img")
        ]
        episode_data = {
            "german-title": german_title,
            "english-title": english_title,
            "hosts": hosts,
            "languages": languages,
        }
        season_data.append(episode_data)

    return season_data

def get_info(id):
    data = {
        "title": "",
        "alternative-titles": "",
        "start-date": "",
        "end-date": "",
        "fsk": 0,
        "description": "",
        "imdb-id": "",
        "mal-id": None,
        "mal-data": {},
        "seasons": {},
    }
    # Get general data
    html_page = aniworld_session.get(f"https://aniworld.to/anime/stream/{id}")
    soup = BeautifulSoup(html_page.content, "html.parser")
    season_ul = soup.select_one("#stream > ul:nth-child(1)")
    seasons = [season.text.replace("Filme", "0") for season in season_ul.find_all("a")]
    data["title"] = soup.select_one(
        ".series-title > h1:nth-child(1) > span:nth-child(1)"
    ).text
    data["alternative-titles"] = soup.select_one(".series-title > h1:nth-child(1)")[
        "data-alternativetitles"
    ]
    data["start-date"] = soup.select_one(
        ".series-title > small:nth-child(2) > span:nth-child(1) > a:nth-child(1)"
    ).text
    data["end-date"] = soup.select_one(
        ".series-title > small:nth-child(2) > span:nth-child(2) > a:nth-child(1)"
    ).text
    data["fsk"] = int(soup.select_one(".fsk")["data-fsk"])
    data["description"] = soup.select_one(".seri_des")["data-full-description"]
    try:
        data["imdb-id"] = soup.select_one(".imdb-link")["data-imdb"]
    except:
        data["imdb-id"] = ""
    
    # Get season specific data
    for season in seasons:
        data["seasons"][season] = get_season_info(id, season)
    
    mal_id = get_mal_id(id, data)
    if mal_id:
        data["mal-id"] = mal_id

    return id, data

def get_mal(mal_id, client_id):
    url = f"https://api.myanimelist.net/v2/anime/{mal_id}?fields=id,title,main_picture,alternative_titles,start_date,end_date,synopsis,mean,rank,popularity,num_scoring_users,media_type,status,genres,num_episodes,start_season,source,average_episode_duration,rating,studios,statistics"
    headers = {
        'X-MAL-CLIENT-ID': client_id,
    }
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        return {}

if __name__ == '__main__':
    anime_offline_database = requests.get("https://raw.githubusercontent.com/manami-project/anime-offline-database/master/anime-offline-database-minified.json").json()
    print("Fetched anime-offline-database")
    anime_list_full = requests.get("https://raw.githubusercontent.com/Fribb/anime-lists/master/anime-list-mini.json").json()
    print("Fetched anime-list-full")

    aniworld_session = requests.Session()
    html_page = aniworld_session.get("https://aniworld.to/animes-alphabet")
    print(html_page.content)
    soup = BeautifulSoup(html_page.content, 'html.parser')
    series_container = soup.select_one('.genre > ul:nth-child(2)')

    anime_ids = []
    for a_tag in series_container.find_all('a'):
        anime_ids.append(a_tag['href'].replace('/anime/stream/', ''))
    anime_ids = sorted(anime_ids)

    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = executor.map(get_info, anime_ids)

    aniworld_session.close()

    anime_dict = {}
    for id, data in results:
        anime_dict[id] = data

    # Get MyAnimelist data
    for key, value in anime_dict.items():
        if value["mal-id"]:
            anime_dict[key]["mal-data"] = get_mal(value["mal-id"], CLIENT_ID)
            del value["mal-id"]
            time.sleep(0.5)

    with open('anime-list-mini.json', 'w') as file:
        json.dump(anime_dict, file)

    with open('anime-list.json', 'w') as file:
        json.dump(anime_dict, file, indent=4)