import concurrent.futures
import time
from typing import List, Any, Dict

import requests
import matplotlib.pyplot as plt
import logging
import sys
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta

from chesscom_cache import GameCache

logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))
logging.getLogger().setLevel(logging.INFO)
logger = logging.getLogger()


def main():
    start = time.time()
    url = f'https://api.chess.com/pub/player/{username}/games/archives'

    # Make a GET request to the API to get a list of archives for the user
    response = requests.get(url, headers={"User-Agent": "5tk18"})

    # Get the most recent archive urls
    lookback_date = datetime.now() - timedelta(days=days)
    archive_urls = response.json()['archives']
    archive_urls = [url for url in archive_urls if
                    get_end_of_month(get_date_from_archive_url(url)) >= lookback_date.date()]

    if MULTI_THREADED:
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            month_json_futures = [executor.submit(get_games_json, archive_url) for archive_url in archive_urls]
            create_chart(
                [future.result() for future in (concurrent.futures.as_completed(month_json_futures))], start)
    else:
        create_chart([get_games_json(archive_url) for archive_url in archive_urls], start)


def get_end_of_month(date: datetime):
    return (date + relativedelta(months=1)).replace(day=1) - timedelta(1)


def get_date_from_archive_url(archive_url: str):
    return datetime.strptime(''.join(archive_url.split('/')[-2:]), '%Y%m').date()


def is_current_month(date_1: date):
    return (datetime.now().replace(day=1) - timedelta(1)).date() < date_1


def get_games_json(archive_url: str):
    db = GameCache("chesscom_cache.db")
    start_of_month = get_date_from_archive_url(archive_url)
    if USE_DB and not is_current_month(start_of_month):
        response_json = db.get(username, start_of_month)
        if response_json:
            logger.info("Found game archive in db for {}".format(archive_url))
            return response_json
    logger.info("Requesting games archive at {}".format(archive_url))
    response_json = requests.get(archive_url, headers={"User-Agent": "5tk18"}).json()
    db.set(username, start_of_month, response_json)
    return response_json


def create_chart(games_jsons: List[Dict[str, Any]], start: time):
    logger.info(f'Took {time.time() - start} seconds to fetch data')

    # Make a GET request to the API to get the games from the last 3 months
    elo_history = []
    game_ids = []
    lookback_date = datetime.now() - timedelta(days=days)
    for games_json in games_jsons:
        for game in games_json['games']:
            if game['rules'] == 'chess' and game['time_class'] == 'blitz' and datetime.fromtimestamp(
                    game['end_time']).date() >= lookback_date.date():
                white_elo = game['white']['rating']
                black_elo = game['black']['rating']
                if username.lower() == game['white']['username'].lower():
                    elo_history.append(white_elo)
                else:
                    elo_history.append(black_elo)
                game_ids.append(game['url'].split('/')[-1])

    # Plot the ELO over time
    fig, ax = plt.subplots()
    ax.plot(elo_history)
    # for i, txt in enumerate(game_ids):
    #     ax.annotate(txt, (i, elo_history[i]))

    # Plot the ELO over time
    # plt.plot(elo_history)
    plt.xlabel('Game number')
    plt.ylabel('ELO')
    plt.title(f'Blitz ELO history for {username} (last {days} days)')
    plt.show()


# case sensistive
username = '5tk18'
days = 100
USE_DB = True
MULTI_THREADED = False

if __name__ == '__main__':
    main()
