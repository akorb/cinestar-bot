import requests
from pyquery import PyQuery


TELEGRAM_CHANNEL_ID = '<THE CHANNEL ID>'
TELEGRAM_BOT_TOKEN = '<THE BOT TOKEN>'
CINEMA_ID = 29  # Cinema Jena, randomly chosen


class Movie:
    def __init__(self, movie_id, title, poster_url):
        self.movie_id = movie_id
        self.title = title
        self.poster_url = poster_url


def send_to_telegram(text, image_url=None):
    params = {
        'chat_id': TELEGRAM_CHANNEL_ID,
    }

    method: str
    if image_url:
        method = 'sendPhoto'
        params['caption'] = text
        params['photo'] = image_url
    else:
        method = 'sendMessage'
        params['text'] = text

    requests.get(f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/{method}', params=params)


def send_update_to_telegram(date, movies):
    send_to_telegram(date)
    for movie in movies:
        send_to_telegram(movie.title, movie.poster_url)


def query_movie_information(movie_id):
    response = requests.get(f"https://www.cinestar.de/api/show/{movie_id}?appVersion=1.5.3")
    json = response.json()
    title = json['title']
    # The URL from the API contains a quite small picture
    # We want a big one
    poster_url = json['poster'].replace('/poster_tile/', '/web_l/')
    return Movie(movie_id, title, poster_url)


def get_fdw(webpage):
    ids_text: str = webpage('[data-show-ids]')[0].attrib['data-show-ids']
    ids = map(int, ids_text.split(','))
    movies = map(query_movie_information, ids)
    return list(movies)


def write_new_date(date):
    with open('cinestar-date', 'w') as f:
        return f.write(date)


def get_last_date():
    try:
        with open('cinestar-date', 'r') as f:
            return f.read()
    except FileNotFoundError:
        return ''


def get_webpage(fdw_page_url):
    pq = PyQuery(url=fdw_page_url)
    return pq


def get_date_text(webpage: PyQuery):
    date_text = webpage('div.subHeadline')[0].text.strip()
    return date_text


def get_fdw_identifier():
    response = requests.get("https://www.cinestar.de/api/attribute/?appVersion=1.5.3")
    json = response.json()
    identifier = next(obj['name'] for obj in json if obj['id'] == 'ET_FILM_DER_WOCHE')
    return identifier


def get_cinema_suburl():
    response = requests.get(f"https://www.cinestar.de/api/cinema/?appVersion=1.5.3")
    json = response.json()
    url = next(obj['slug'] for obj in json if obj['id'] == CINEMA_ID)
    return url


def get_fdw_page_url(fdw_identifier, suburl):
    response = requests.get(f"https://www.cinestar.de/aets/flaps/{CINEMA_ID}?appVersion=1.5.3")
    json = response.json()
    url = next(obj['link'] for obj in json if obj['title'] == fdw_identifier)
    # Location doesn't matter. Film der Woche is same everywhere
    return url.replace('/redirect/', f'/{suburl}/')


def main():
    fdw_identifier = get_fdw_identifier()
    suburl = get_cinema_suburl()
    fdw_page_url = get_fdw_page_url(fdw_identifier, suburl)
    
    webpage = get_webpage(fdw_page_url)
    date = get_date_text(webpage)
    last_date = get_last_date()
    if date != last_date:
        write_new_date(date)
        movies = get_fdw(webpage)
        send_update_to_telegram(date, movies)


if __name__ == '__main__':
    main()
