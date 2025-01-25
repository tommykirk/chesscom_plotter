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
    username = '5tk18'
    download_games(30, username)
    print_games_played(7, username)
    # create_chart()
    # now = datetime.now().replace(month=2)
    # # print(get_end_of_month(now))
    # for i in range(45):
    #     print("now plus {} days is {}".format(i, now + timedelta(i)))
    #     print(get_end_of_month(now + timedelta(i)))


def download_games(duration: int, username: str):
    db = GameCache("chesscom_cache.db")

    # case sensistive
    url = f'https://api.chess.com/pub/player/{username}/games/archives'

    # Make a GET request to the API to get a list of archives for the user
    response = requests.get(url, headers={"User-Agent": "5tk18"})

    # Get the URL of the archive for 3 months ago
    lookback_date = datetime.now() - timedelta(days=duration)
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


def print_games_played(days: int, username: str):
    db = GameCache("chesscom_cache.db")
    url = f'https://api.chess.com/pub/player/{username}/games/archives'

    # Make a GET request to the API to get a list of archives for the user
    response = requests.get(url, headers={"User-Agent": "5tk18"})

    # Get the URL of the archive for 3 months ago
    lookback_date = datetime.now() - timedelta(days=days)
    archive_urls = response.json()['archives']
    archive_urls = [url for url in archive_urls if
                    get_end_of_month(get_date_from_archive_url(url)) >= lookback_date.date()]

    for archive_url in archive_urls:
        start_of_month = get_date_from_archive_url(archive_url)
        response_json = db.get(username, start_of_month)
        total_seconds = 0
        total_games = 0
        last_game_end_time = None
        for game in response_json['games']:
            # and game['time_class'] == 'blitz'
            # print(datetime.fromtimestamp(game['end_time']).date(), lookback_date.date())
            if game['rules'] == 'chess' and datetime.fromtimestamp(game['end_time']).date() >= lookback_date.date():
                try:
                    pgn = chess.pgn.read_game(io.StringIO(game['pgn']))
                    game_duration = get_game_duration(pgn)
                    total_seconds += game_duration
                    total_games += 1
                    time_between_games = None
                    if last_game_end_time is not None:
                        time_between_games = get_game_start_time(pgn) - last_game_end_time
                        if time_between_games < timedelta(0):
                            time_between_games = timedelta(0)
                    print(f"Spent {game_duration} seconds playing this game at {get_game_start_time(pgn)}. {time_between_games} between last game.")
                    last_game_end_time = get_game_end_time(pgn)
                except Exception as e:
                    logger.error(e)
                    print(e)
                    print("tommy error: " + game['url'])
        print(f"Spent a total of {format_seconds(total_seconds)} seconds playing {total_games} games in the last {days} days")


def format_seconds(seconds: int) -> str:
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0 or hours > 0:  # Include minutes if hours are present
        parts.append(f"{minutes}m")
    parts.append(f"{seconds}s")
    return " ".join(parts)

def get_game_start_time(pgn: chess.pgn.GameT):
    t1 = datetime.strptime(pgn.headers.get('UTCDate') + pgn.headers.get('StartTime'), "%Y.%m.%d%H:%M:%S")
    return t1


def get_game_end_time(pgn: chess.pgn.GameT):
    t2 = datetime.strptime(pgn.headers.get('EndDate') + pgn.headers.get('EndTime'), "%Y.%m.%d%H:%M:%S")
    return t2


def get_game_duration(pgn: chess.pgn.GameT):
    t_delta = get_game_end_time(pgn) - get_game_start_time(pgn)
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
    logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))
    logging.getLogger().setLevel(logging.INFO)
    logger = logging.getLogger()
    main()
