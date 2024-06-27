from LeaugeDataReader import LeaugeDataReader

reader = LeaugeDataReader()
nick = ''
tag_line = ''
puuid = reader.get_puuid(nick, tag_line)
print(puuid)
reader.get_all_games_info(puuid)
