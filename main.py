from LeaugeDataReader import LeaugeDataReader

reader = LeaugeDataReader()
puuid = reader.get_puuid('Var Kenarah', 'EUNE')
print(puuid)
reader.get_all_games_info(puuid)