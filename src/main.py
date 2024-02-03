from src.conectorSpotify import ConectorSpotify
from src.credentials import CLIENT_ID, CLIENT_SECRET

sp = ConectorSpotify(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
print(sp.playlist())
