import requests
import matplotlib.pyplot as plt
import logging
import sys
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from collections import defaultdict
import matplotlib.dates as mdates

def main():
    create_chart()

def get_end_of_month(date: datetime):
    return (date + relativedelta(months=1)).replace(day=1) - timedelta(1)

def create_chart():
    username = '5tk18'
    url = f'https://api.chess.com/pub/player/{username}/games/archives'
    days = 5000

    logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))
    logging.getLogger().setLevel(logging.INFO)
    logger = logging.getLogger()

    # Make a GET request to the API to get a list of archives for the user
    response = requests.get(url, headers={"User-Agent": "5tk18"})

    lookback_date = datetime.now() - timedelta(days=days)
    archive_urls = response.json()['archives']
    archive_urls = [url for url in archive_urls if
                    get_end_of_month(
                        datetime.strptime(''.join(url.split('/')[-2:]), '%Y%m').date()) >= lookback_date.date()]

    games_by_date_and_time_control = defaultdict(lambda: defaultdict(int))
    # today = datetime.now().date()
    # print(today)
    # print(games_by_date_and_time_control[today])
    # print(games_by_date_and_time_control[today]['rando'])
    # print(games_by_date_and_time_control[today]['1+2'])

    for archive_url in archive_urls:
        logger.info("Requesting games archive at {}".format(archive_url))
        response = requests.get(archive_url, headers={"User-Agent": "5tk18"})
        for game in response.json()['games']:
            game_end_date = datetime.fromtimestamp(game['end_time']).date()
            if game_end_date >= lookback_date.date():
                if game['time_class'] == 'blitz':
                    initial_time = game['time_control'].split('+')[0]
                    increment = game['time_control'].split('+')[1] if '+' in game['time_control'] else '0'
                    time_control = f"{initial_time}+{increment}"
                    games_by_date_and_time_control[game_end_date][time_control] += 1

    # Prepare data for plotting
    dates = sorted(games_by_date_and_time_control.keys())
    time_controls = set(tc for date in dates for tc in games_by_date_and_time_control[date])
    print(games_by_date_and_time_control)
    time_control_counts = {tc: [games_by_date_and_time_control[date][tc] for date in dates] for tc in time_controls}

    fig, ax = plt.subplots()

    for time_control, counts in time_control_counts.items():
        ax.plot(dates, counts, label=time_control)

    # Format the x-axis to show dates properly
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    fig.autofmt_xdate()

    plt.xlabel('Date')
    plt.ylabel('Number of Games')
    plt.title(f'Blitz Game Count by Time Control for {username} (last {days} days)')
    plt.legend(title='Time Control')
    plt.tight_layout()
    plt.show()

if __name__ == '__main__':
    main()
