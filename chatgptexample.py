import io

import requests
import matplotlib.pyplot as plt
import logging
import sys
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
import chess.pgn

from chesscom_cache import GameCache


def main():
    some_generic_method()
    # create_chart()
    # now = datetime.now().replace(month=2)
    # # print(get_end_of_month(now))
    # for i in range(45):
    #     print("now plus {} days is {}".format(i, now + timedelta(i)))
    #     print(get_end_of_month(now + timedelta(i)))

def some_generic_method():
    db = GameCache("chesscom_cache.db")

    # case sensistive
    username = 'printerpaper'
    url = f'https://api.chess.com/pub/player/{username}/games/archives'

    days = 7

    logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))
    logging.getLogger().setLevel(logging.INFO)
    logger = logging.getLogger()

    # Make a GET request to the API to get a list of archives for the user
    response = requests.get(url, headers={"User-Agent": "5tk18"})

    # Get the URL of the archive for 3 months ago
    lookback_date = datetime.now() - timedelta(days=days)
    end_of_month = get_end_of_month(lookback_date)
    archive_urls = response.json()['archives']
    archive_urls = [url for url in archive_urls if
                    get_end_of_month(get_date_from_archive_url(url)) >= lookback_date.date()]

    for archive_url in archive_urls:
        start_of_month = get_date_from_archive_url(archive_url)
        response_json = db.get(username, start_of_month)
        if response_json is not None and not is_current_month(start_of_month):
            logger.info("Found game archive in db for {}".format(archive_url))
        else:
            logger.info("Requesting games archive at {}".format(archive_url))
            response_json = requests.get(archive_url, headers={"User-Agent": "5tk18"}).json()
            db.set(username, start_of_month, response_json)
        total_seconds = 0
        total_games = 0
        for game in response_json['games']:
            # and game['time_class'] == 'blitz'
            if game['rules'] == 'chess' and datetime.fromtimestamp(game['end_time']).date() >= lookback_date.date():
                try:
                    game_duration = get_game_duration(game['pgn'])
                    total_seconds += game_duration
                    total_games += 1
                    print(f"Spent {game_duration} seconds playing this game")
                except Exception as e:
                    logger.error(e)
                    print(e)
                    print("tommy error: " + game['url'])
        print(f"Spent a total of {total_seconds} seconds playing {total_games} games")



def get_game_duration(pgn_str: str):
    pgn = chess.pgn.read_game(io.StringIO(pgn_str))
    t1 = datetime.strptime(pgn.headers.get('UTCDate') + pgn.headers.get('StartTime'), "%Y.%m.%d%H:%M:%S")
    t2 = datetime.strptime(pgn.headers.get('EndDate') + pgn.headers.get('EndTime'), "%Y.%m.%d%H:%M:%S")
    t_delta = t2 - t1
    return t_delta.seconds


def get_end_of_month(date: datetime):
    return (date + relativedelta(months=1)).replace(day=1) - timedelta(1)


def get_date_from_archive_url(url: str):
    return datetime.strptime(''.join(url.split('/')[-2:]), '%Y%m').date()


def is_current_month(date_1: date):
    return (datetime.now().replace(day=1) - timedelta(1)).date() < date_1


def create_chart():
    db = GameCache("chesscom_cache.db")

    # case sensistive
    username = '5tk18'
    url = f'https://api.chess.com/pub/player/{username}/games/archives'

    days = 100

    logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))
    logging.getLogger().setLevel(logging.INFO)
    logger = logging.getLogger()

    # Make a GET request to the API to get a list of archives for the user
    response = requests.get(url, headers={"User-Agent": "5tk18"})

    # Get the URL of the archive for 3 months ago
    lookback_date = datetime.now() - timedelta(days=days)
    end_of_month = get_end_of_month(lookback_date)
    archive_urls = response.json()['archives']
    archive_urls = [url for url in archive_urls if
                    get_end_of_month(get_date_from_archive_url(url)) >= lookback_date.date()]

    # Make a GET request to the API to get the games from the last 3 months
    elo_history = []
    game_ids = []
    for archive_url in archive_urls:
        start_of_month = get_date_from_archive_url(archive_url)
        response_json = db.get(username, start_of_month)
        if response_json is not None and not is_current_month(start_of_month):
            logger.info("Found game archive in db for {}".format(archive_url))
        else:
            logger.info("Requesting games archive at {}".format(archive_url))
            response_json = requests.get(archive_url, headers={"User-Agent": "5tk18"}).json()
            db.set(username, start_of_month, response_json)
        for game in response_json['games']:
            if game['rules'] == 'chess' and game['time_class'] == 'blitz' and datetime.fromtimestamp(
                    game['end_time']).date() >= lookback_date.date():
                white_elo = game['white']['rating']
                black_elo = game['black']['rating']
                if username == game['white']['username']:
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


if __name__ == '__main__':
    main()
