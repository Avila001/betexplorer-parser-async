from bs4 import BeautifulSoup
import re


class Match:
    def __init__(self, html):
        self.html = html

    @staticmethod
    def get_team_name(page):
        """"Метод возвращает массив из даты, имени команд"""
        mas_name = []
        soup = BeautifulSoup(page, 'lxml')
        dates = soup.find_all('p', class_='list-details__item__date')
        for date in dates:
            date_str = date['data-dt']
            date_str = date_str.replace(',', '.')
            date_str = date_str[:len(date_str) - 6]
            # print(date_str)
            mas_name.append(date_str)
        items = soup.find_all('h2', class_='list-details__item__title')
        for item in items:
            print(item.text)
            mas_name.append(item.text)
        '''mas_name[date, HomeTeamName, AwayTeamName'''
        if len(mas_name) < 3:
            print("Ошибка", items)
            print(page)
        return mas_name

    @staticmethod
    def get_odds(page, team_a, team_b):
        print(f'{team_a} - {team_b}')
        # print(page)
        result = None
        '''alert_block = soup.find(class_="uk-alert-danger")
        if alert_block is not None:
            continue'''
        mas_1x2 = []
        # soup = BeautifulSoup(html, 'html.parser')
        text = page
        start = 'Pinnacle'
        if start not in text:
            start = 'bet365'
        end = 'Unibet'

        '''if start in text:
            result = text[text.index(start):text.index(end)+len(end)]
        else:
            start = '1xBet'
            end = '888sport'
            result = text[text.index(start):text.index(end)+len(end)]'''

        if end in text:
            result = text[text.index(start):text.index(end) + len(end)]
        elif end in text:
            end = 'Betfair Exchange'
            result = text[text.index(start):text.index(end) + len(end)]
        elif end in text:
            end = 'William Hill'
            result = text[text.index(start):text.index(end) + len(end)]
        else:
            print(f"{team_a} - {team_b}")

        if result is None:
            print(page)

        #test = re.findall(r' data-odd="(.*?)"', result)
        test = re.findall(r' data-odd=\\"(.*?)\\"', result)
        # print(test)
        # print(test[0],type(test[0]))
        k1 = float(test[0])
        x = float(test[1])
        k2 = float(test[2])
        mas_1x2.append(k1)
        mas_1x2.append(x)
        mas_1x2.append(k2)
        return mas_1x2

    @staticmethod
    def get_ah(page, url):
        print(f"Вошли в ah {url}")
        fora = 0
        mas = []
        result = []
        length_of_result = len(result)
        # print(html)
        list_of_bookmakers = ['Pinnacle', 'Betfair Exchange', '1xBet', 'bet365', '188BET']
        i = 0
        while list_of_bookmakers:
            result = re.findall(fr'{list_of_bookmakers[i]}.*?doubleparameter\\\">(.*?)<.*?data-odd=\\\"(.*?)\\.*?data-odd=\\\"(.*?)\\',
                            page)
            print(result)
            length_of_result = len(result)
            i += 1
            if length_of_result > 0:
                break
                print("Прошли ah")
        # print(result, type(result))
        for i in range(len(result)):
            # print(result[i][0], type(result[i][0]))
            stroka = result[i][0]
            length = len(stroka)
            if length > 4:
                decomposition = re.match(r"(.*), (.*)", stroka)
                # print(decomposition.group(1),type(decomposition.group(1)), decomposition.group(2))
                ah1 = float(decomposition.group(1))
                ah2 = float(decomposition.group(2))
                ah = (ah1 + ah2) / 2
            else:
                ah = float(result[i][0])
            kf1 = float(result[i][1])
            kf2 = float(result[i][2])
            mas.append([ah, kf1, kf2])
        # print(mas)
        for i in range(len(mas)):
            if mas[i][1] >= 2 >= mas[i + 1][1]:
                # print(mas[i][1], mas[i+1][1])
                margin1 = 1 / mas[i][1] + 1 / mas[i][2]
                margin2 = 1 / mas[i + 1][1] + 1 / mas[i + 1][2]
                kf1_with_margin = mas[i][1] * margin1
                kf2_with_margin = mas[i + 1][1] * margin2
                percentage1 = 1 / kf1_with_margin * 100
                percentage2 = 1 / kf2_with_margin * 100
                fora1 = mas[i][0]
                fora2 = mas[i + 1][0]
                # print(fora1,fora2,percentage1,percentage2)
                fora = fora1 + (fora2 - fora1) * (50 - percentage1) / (percentage2 - percentage1)
                # print(fora)
        return fora

    @staticmethod
    def get_total(page, url):
        print(f"Вошли в total {url}")
        total = 0
        list_of_bookmakers = ['Pinnacle', 'Betfair Exchange', '1xBet', 'bet365', '188BET']
        i = 0
        while list_of_bookmakers:
            result = re.findall(fr'{list_of_bookmakers[i]}.*?doubleparameter\\\">(.*?)<.*?data-odd=\\\"(.*?)\\.*?data-odd=\\\"(.*?)\\',
                                page)
            length_of_result = len(result)
            i += 1
            if length_of_result > 0:
                break
        # print(result)
        mas = []
        for i in range(len(result)):
            # print(result[i][0], type(result[i][0]))
            stroka = result[i][0]
            length = len(stroka)
            if length > 4:
                decomposition = re.match(r"(.*), (.*)", stroka)
                # print(decomposition.group(1),type(decomposition.group(1)), decomposition.group(2))
                ah1 = float(decomposition.group(1))
                ah2 = float(decomposition.group(2))
                ah = (ah1 + ah2) / 2
            else:
                ah = float(result[i][0])
            kf1 = float(result[i][1])
            kf2 = float(result[i][2])
            mas.append([ah, kf1, kf2])
        # print(mas)
        for i in range(len(mas)):
            if mas[i][1] <= 2 <= mas[i + 1][1]:
                # print(mas[i][1], mas[i+1][1])
                margin1 = 1 / mas[i][1] + 1 / mas[i][2]
                margin2 = 1 / mas[i + 1][1] + 1 / mas[i + 1][2]
                kf1_with_margin = mas[i][1] * margin1
                kf2_with_margin = mas[i + 1][1] * margin2
                percentage1 = 1 / kf1_with_margin * 100
                percentage2 = 1 / kf2_with_margin * 100
                total1 = mas[i][0]
                total2 = mas[i + 1][0]
                # print(fora1,fora2,percentage1,percentage2)
                total = total1 + (total2 - total1) * (50 - percentage1) / (percentage2 - percentage1)
                # print(fora)
        return total
