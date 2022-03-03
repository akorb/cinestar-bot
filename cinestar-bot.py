import requests
from pyquery import PyQuery

# Location doesn't matter. Movies of the week are same everywhere
URL = 'https://www.cinestar.de/kino-bremen-kristall-palast/film-der-woche'

TELEGRAM_CHANNEL_ID = '<THE CHANNEL ID>'
TELEGRAM_BOT_TOKEN = '<THE BOT TOKEN>'


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


def get_movies_of_the_week(webpage):
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


def get_webpage():
    pq = PyQuery(URL)
    return pq


def get_date_text(webpage: PyQuery):
    date_text = webpage('div.subHeadline')[0].text.strip()
    return date_text


def main():
    webpage = get_webpage()
    date = get_date_text(webpage)
    last_date = get_last_date()
    if date != last_date:
        write_new_date(date)
        movies = get_movies_of_the_week(webpage)
        send_update_to_telegram(date, movies)


if __name__ == '__main__':
    main()
