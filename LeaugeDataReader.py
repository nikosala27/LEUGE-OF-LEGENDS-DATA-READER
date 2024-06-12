from dotenv import load_dotenv
import pandas as pd
import openpyxl
import requests
import datetime
import time
import json
import os


class LeaugeDataReader():
    def __init__(self) -> None:
        load_dotenv()
        self.api_key = os.getenv('API_KEY')
        self.puuid_url = "https://europe.api.riotgames.com/riot/account/v1/accounts/by-riot-id/"
        self.game_ids_url = "https://europe.api.riotgames.com/lol/match/v5/matches/by-puuid/"

    def get_puuid(self, username, tag_line):
        url = f"{self.puuid_url}{username}/{tag_line}?api_key={self.api_key}"
        response = requests.get(url)
        self.check_request(response.status_code)

        return json.loads(response.text)['puuid']

    def get_games_ids(self, puuid:str, start_time:str, end_time:str, type:str, count:int):
        start_time = int(time.mktime(datetime.datetime.strptime(start_time, "%d/%m/%Y").timetuple()))
        end_time = int(time.mktime(datetime.datetime.strptime(end_time, "%d/%m/%Y").timetuple()))

        url = f"{self.game_ids_url}{puuid}/ids?startTime={start_time}&endTime={end_time}&type={type}&start=0&count={count}&api_key={self.api_key}"

        response = requests.get(url)
        if response.status_code == 429:
                print('EXCEEDED LIMIT OF REQUESTS, WE NEED TO WAIT')
                time.sleep(130.0)
                while True:
                    response = requests.get(url)
                    if response.status_code != 200:
                        print('TRYING TO RECCONECT...')
                        time.sleep(10)
                    else:
                        break
                    
        return json.loads(response.text)
    
    def gather_all_games_ids(self, puuid):
        games_codes = []

        for year in range(2021, 2025):
            for month in range(1, 13):
                if year == 2024 and month == 7:
                    break

                start_date = f"1/{str(month)}/{str(year)}"

                if month != 12:
                    end_date = f"1/{str((month+1))}/{str(year)}"
                else:
                    end_date = f"1/1/{str(year)}"

                games = self.get_games_ids(puuid, start_date, end_date, 'ranked', 100)
                if games != []:
                    for game in games:
                        if game not in games_codes:
                            games_codes.append(game)
        return games_codes
    
    def get_all_games_info(self, puuid):
        dataframe_data = []
        games_codes = self.gather_all_games_ids(puuid)
        for game_code in games_codes:
            url = f"https://europe.api.riotgames.com/lol/match/v5/matches/{game_code}?api_key={self.api_key}"

            response = requests.get(url)
            if response.status_code == 429:
                print('EXCEEDED LIMIT OF REQUESTS, WE NEED TO WAIT')
                time.sleep(130.0)
                while True:
                    response = requests.get(url)
                    if response.status_code != 200:
                        print('TRYING TO RECCONECT...')
                        time.sleep(10)
                    else:
                        break

            data = json.loads(response.text)

            game_id = game_code
            print(f"Kod gry:{game_id}")

            # Zbieranie statystyk
            #TODO Czasami nie ma klucza 'metadata' ja pominąłem ponieważ biorę z niego puuid i się wykrzaczało, a puuid jest potrzebny
            # żeby wykryć odpowiedniego uczestnika z 'info', można to obejść przeszukjąć całe participants i wypluć odpowiedni index, ale mi się nie chciało

            if 'metadata' in data.keys():
                index_of_participant = data['metadata']['participants'].index(puuid)
                game_duration = data['info']['gameDuration']
                participant_stats = data['info']['participants'][index_of_participant]
                played_champion = participant_stats['championName']
                kills = participant_stats['kills']
                deaths = participant_stats['deaths']
                assists = participant_stats['assists']
                is_win = participant_stats['win']
                team = participant_stats['teamId']
                position = participant_stats['teamPosition']
                damage_taken = participant_stats['totalDamageTaken']
                damage_dealt = int(participant_stats['physicalDamageDealtToChampions']) + int(participant_stats['magicDamageDealtToChampions'])
                minions_killed = participant_stats['totalMinionsKilled']
                gold_earned = participant_stats['goldEarned']
                gold_per_minute = int(gold_earned)/(game_duration/60)
                tower_dmg = participant_stats['damageDealtToTurrets']

                if int(deaths) == 0:
                    kda = (int(deaths)+int(assists))/1
                else:
                    kda = (int(deaths)+int(assists))/deaths

                data_string = f"{game_id}|{game_duration}|{played_champion}|{kills}|{deaths}|{assists}|{kda}|{is_win}|{team}|{position}|{damage_taken}|{damage_dealt}|{minions_killed}|{gold_earned}|{gold_per_minute}|{tower_dmg}"

                data_string_list = data_string.split('|')
                print(data_string_list)
                dataframe_data.append(data_string_list)

        columns = ['ID GRY', 'CZAS GRY', 'CHAMPION', 'ZABOJSTWA', 'SMIERCI', 'ASYSTY', 'KDA', 'CZY_WYGRANA', 'DRUZYNA', 'POZYCJA', 'OBRAZENIA PRZYJETE', 'OBRAZENIA ZADANE', 'ZABITE STWORY', 'ZDOBYTE ZŁOTO', 'ZŁOTO NA MIN', 'OBRAŻENIA DO WIEŻ']
        pd.DataFrame(dataframe_data, columns=columns).to_excel('VAR_KENARAH.xlsx', index=False)

    def check_request(self, status_code:int):
        if status_code == 404:
            raise('404 ERROR - BAD REQUEST')
        if status_code == 429:
            print('429 ERROR - EXCEEDED LIMIT WAITING A FEW MINUTES TO RETRY')
            time.sleep(130.0)
