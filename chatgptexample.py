import requests
import matplotlib.pyplot as plt
import logging
import sys
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

def main():
    create_chart()
    # now = datetime.now().replace(month=2)
    # # print(get_end_of_month(now))
    # for i in range(45):
    #     print("now plus {} days is {}".format(i, now + timedelta(i)))
    #     print(get_end_of_month(now + timedelta(i)))

def get_end_of_month(date: datetime):
    return (date + relativedelta(months=1)).replace(day=1) - timedelta(1)

def create_chart():
    username = '5tk18'
    url = f'https://api.chess.com/pub/player/{username}/games/archives'

    days = 180

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
                    get_end_of_month(datetime.strptime(''.join(url.split('/')[-2:]), '%Y%m').date()) >= lookback_date.date()]

    # Make a GET request to the API to get the games from the last 3 months
    elo_history = []
    game_ids = []
    for archive_url in archive_urls:
        logger.info("Requesting games archive at {}".format(archive_url))
        response = requests.get(archive_url, headers={"User-Agent": "5tk18"})
        for game in response.json()['games']:
            if game['rules'] == 'chess' and game['time_class'] == 'blitz' and datetime.fromtimestamp(game['end_time']).date() >= lookback_date.date():
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
