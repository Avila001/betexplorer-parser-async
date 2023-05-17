from bs4 import BeautifulSoup
import requests
import leagues.leagues_url
import csv
import sqlite3
import mappings.mappings
import match.match
import re
import time
import asyncio
import aiohttp
import database_footy.db
from aiohttp_retry import RetryClient
import socket


LEAGUE = 'England2_19-20' + '.csv'
season = 23976

RECORD = 'a' #'w' - запись заново с нуля, 'a' - дозапись к текущему
HEADERS = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                         'Chrome/93.0.4577.82 Safari/537.36 OPR/79.0.4143.72',
           'accept': '*/*', 'Referer': 'https://www.betexplorer.com'}
all_data = []
database = r'D:/Downloads/sqlitestudio-3.3.3/SQLiteStudio/footystats'


def get_html(url, params=None):
    r = requests.get(url, headers=HEADERS, params=params)
    return r


def get_href(html):
    """Мы здесь из файла забираем все ссылки. Но можно сделать через последний элемент."""
    mas_current_href = []


    mas_href = []
    soup = BeautifulSoup(html, 'lxml')
    # items = soup.find_all('a', class_ = 'in-match')
    items = soup.find_all('td', class_='h-text-center')
    for item in reversed(items):
        exception = str(item)
        post = item.text
        if (post != 'POSTP.') and (post != 'CAN.') and ('ABN.' not in post) and \
            (exception != '<td class="h-text-center"><a href="/soccer/england/championship-2020-2021/watford-wycombe/xjFSvDP8/">2:0</a></td>') and \
            (exception != '<td class="h-text-center"><a href="/soccer/england/championship-2020-2021/sheffield-wed-rotherham/baGOugA2/">1:2</a></td>'):
            mas_href.append('https://www.betexplorer.com' + item.find('a').get('href'))
        # print('https://www.betexplorer.com'+item.find('a').get('href'))
    result = [item for item in mas_href if item not in mas_current_href]
    # print(result)
    return result


#здесь я ишу хэш матча через match_init (легкий способ через ссылку)
def extract_1x2(URL):
     result = re.match(r"https:\/\/www\.betexplorer\.com\/soccer\/(.*)\/(.*)\/(.*)\/(.*)\/",URL)
     #print(result.group(4))
     '''result = re.match(r"match_init\('(.*)', 0, '1x2'\);", SCRIPT)
     print(result.group(1))'''
     return "https://www.betexplorer.com/match-odds/"+result.group(4)+"/0/1x2/"


async def get_match_data(session, url, retry=5) -> list:
    if url == "https://www.betexplorer.com/soccer/england/championship-2020-2021/middlesbrough-brentford/veu1x2sk/":
        all_data.append([-1, -1, -1, -1, url])
        return []
    """У нас есть url матча
        1. Получаем сначала дату и названия команд.
        2. Получаем кэфы 1х2.
        3. Получаем фору.
        4. Получаем тотал.
        5. Добавляем ссылку.
        """
    match_data_list = []
    # try:
    #     async with session.get(url=url, headers=HEADERS, ssl=False) as response:
    #         response_text = await response.text()
    #     #page_results_of_leagues = get_html(url)
    # except Exception as ex:
    #     if retry:
    #         print(f"[INFO] retry get_team_name  = {retry} => {url}")
    #         return get_match_data(session, url, retry=(retry - 1))
    #     else:
    #         raise f"Ошибка get_team_name в {url}"
    # else:
    #     list_of_date_names = match.match.Match.get_team_name(response_text)
    async with session.get(url=url, headers=HEADERS, ssl=False) as response:
        response_text = await response.text()
    list_of_date_names = match.match.Match.get_team_name(response_text)
    match_data_list.append(list_of_date_names[0])
    match_data_list.append(list_of_date_names[1])
    match_data_list.append(list_of_date_names[2])

    url_1x2 = extract_1x2(url)

    async with session.get(url=url_1x2, headers=HEADERS, ssl=False) as response:
        page_odds = await response.text()



    list_odds = match.match.Match.get_odds(page_odds, list_of_date_names[1], list_of_date_names[2])
    match_data_list.append(list_odds[0])
    match_data_list.append(list_odds[1])
    match_data_list.append(list_odds[2])

    url_ah = url_1x2.replace("1x2", "ah")

    async with session.get(url=url_ah, headers=HEADERS, ssl=False) as response:
        page_ah = await response.text()
    #page_ah = get_html(url_ah)
    ah = match.match.Match.get_ah(page_ah, url)

    url_total = url_1x2.replace("1x2", "ou")

    async with session.get(url=url_total, headers=HEADERS, ssl=False) as response:
        page_total = await response.text()
    # #page_total = get_html(url_total)
    total = match.match.Match.get_total(page_total, url)

    goals1 = (total - ah) / 2
    goals2 = total - goals1
    goals1 = round(goals1, 2)
    goals2 = round(goals2, 2)

    match_data_list.append(goals1)
    match_data_list.append(goals2)
    match_data_list.append(goals1 + goals2)
    match_data_list.append(goals2 - goals1)
    match_data_list.append(url)
    all_data.append(match_data_list)
    return match_data_list


async def load_league_data():
    full_list_match_data = []

    url_league = leagues.leagues_url.leagues_url_dict[LEAGUE]
    page_league = get_html(url_league)
    list_of_league = get_href(page_league.text)

    conn = aiohttp.TCPConnector(
        family=socket.AF_INET,
        verify_ssl=False,
        limit=20,
    )

    connector = aiohttp.TCPConnector(limit=20, force_close=True)
    async with aiohttp.ClientSession(connector=conn, trust_env=True) as session:
    #async with aiohttp.ClientSession() as session:
        tasks = []
        for i in range(len(list_of_league)):
        #for i in range(10):
            #match_info = get_match_data(session, list_of_league[i])
            task = asyncio.create_task(get_match_data(session, list_of_league[i]))
            tasks.append(task)
            #full_list_match_data.append(match_info)
        await asyncio.gather(*tasks)

if __name__ == '__main__':
    start_time = time.time()
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    #asyncio.get_event_loop().run_until_complete(load_league_data())
    asyncio.run(load_league_data())
    print(all_data)
    print("--- %s seconds ---" % (time.time() - start_time))
    conn = database_footy.db.create_connection(database)
    for match in all_data:
        team_a_exp_xg = match[6]
        team_b_exp_xg = match[7]
        exp_diff = team_b_exp_xg - team_a_exp_xg
        team_a = mappings.mappings.EPL_sofascore[match[1]]
        team_b = mappings.mappings.EPL_sofascore[match[2]]
        with conn:
            database_footy.db.update_table(conn, (team_a_exp_xg, team_b_exp_xg, exp_diff, team_a, team_b, season))

    #load_league_data()
    print("--- %s seconds ---" % (time.time() - start_time))

    #Season
    #LEAGUE
    #Mappings Teams
