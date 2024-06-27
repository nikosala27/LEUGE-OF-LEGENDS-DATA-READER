from LeaugeDataReader import LeaugeDataReader

reader = LeaugeDataReader()
nick = ''
puuid = reader.get_puuid(nick, 'EUNE')
print(puuid)
reader.get_all_games_info(puuid)
