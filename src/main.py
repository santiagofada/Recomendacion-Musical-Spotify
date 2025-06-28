from src.conectorSpotify import ConectorSpotify
from src.credentials import CLIENT_ID, CLIENT_SECRET

sp = ConectorSpotify(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
##print(sp.playlist())

#print(sp.playlist_vs_liked("TODO"))
#print(sp.liked_songs())

sp.create_liked_songs_playlist(playlist_name="Mis Me Gusta", descripcion="Todas las canciones que me gustaron")

print("Done")



