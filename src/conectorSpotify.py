import spotipy
import spotipy.util as util
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import linear_kernel
import numpy as np

import warnings
import logging



class ConectorSpotify():

    username = None
    spotipy_cient =None
    def __init__(self, client_id=None, client_secret=None, redirect_uri="http://localhost:8888"
                 ,scope = "playlist-modify-public playlist-modify-private user-library-read  user-read-playback-position  user-top-read  user-read-recently-played  playlist-read-private  playlist-read-collaborative  user-read-currently-playing"):
        self.__client_id = client_id
        self.__client_secret = client_secret
        self.__redirect_uri = redirect_uri
        self.__scope = scope
        self.__username = self.__find_username(client_id,client_secret,redirect_uri,scope)

        self.__spotipy_client = self.__autentication()

    def __autentication(self):

        # Esto me genera un token para el usuario, con determinados permisos(scope) y con id y clave
        token = util.prompt_for_user_token(self.__username,self.__scope,
            self.__client_id,self.__client_secret,self.__redirect_uri)

        return spotipy.Spotify(auth=token)


    def __find_username(self, cid, secret, redirect_uri, scope):
        try:
            # Ignorar DeprecationWarning específicamente
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", category=DeprecationWarning)

                sp_oauth = SpotifyOAuth(client_id=cid, client_secret=secret, redirect_uri=redirect_uri, scope=scope)
                token_info = sp_oauth.get_access_token()

                self.__spotipy_client = spotipy.Spotify(auth=token_info['access_token'])

                user_info = self.__spotipy_client.current_user()
                username = user_info['id']

                return username

        except spotipy.SpotifyException as e:
            # Manejar excepción específica de spotipy
            logging.error(f"Error en la autenticación de Spotify: {e}")
        except Exception as e:
            logging.error(f"Error no especificado: {e}")

    def __find_top_canciones(self, plazo="short_term", limite=20):
        """
        Obtiene el listado de pistas más escuchadas en un determinado plazo.

        Parameters:
        - plazo (str): Define el plazo de tiempo para obtener las pistas más escuchadas. Puede ser "short_term" (a corto plazo),
          "medium_term" (a mediano plazo) o "long_term" (a largo plazo).
        - limite (int): Número máximo de pistas a obtener.

        Returns:
        - dict: Diccionario con información sobre las pistas más escuchadas en el plazo especificado.
        """
        return self.__spotipy_client.current_user_top_tracks(time_range=plazo, limit=limite)

    def __create_songs_dataframe(self, top_songs):
        """
        Obtén las características de audio de las canciones más escuchadas y crea un DataFrame con las mismas.

        Parameters:
        - top_songs (dict): Diccionario que contiene las canciones más escuchadas.

        Returns:
        - pd.DataFrame: DataFrame con las características de audio ordenadas.
        """
        try:
            # Obtener ids de las canciones
            ids_canciones = [cancion["id"] for cancion in top_songs["items"]]

            # Obtener audio features
            audio_features = self.__spotipy_client.audio_features(ids_canciones)

            # Crear DataFrame directamente con el orden deseado
            columns = ["id", "acousticness", "danceability", "duration_ms", "energy", "instrumentalness",
                       "key", "liveness", "loudness", "mode", "speechiness", "tempo", "valence"]

            top_songs_df = pd.DataFrame.from_records(audio_features, columns=columns)

            return top_songs_df

        except Exception as e:
            print(f"Error al obtener audio features: {e}")
            return pd.DataFrame()

    def __find_artistas(self,top_songs):
        """
        Obtén los IDs de los artistas de las canciones más escuchadas.

        Parameters:
        - top_songs (dict): Diccionario que contiene las canciones más escuchadas.

        Returns:
        - list: Lista de IDs de los artistas sin duplicados.
        """
        ids_artistas = [item["artists"][0]["id"] for item in top_songs["items"]]
        ids_artistas = list(set(ids_artistas))
        return ids_artistas
    def __find_artistas_similares(self, artistas):
        """
        Pimera parte del sistema de recomendacion
        Amplía el listado de artistas añadiendo artistas relacionados a cada artista en la lista.

        Parameters:
        - artistas (list): Lista de IDs de artistas.

        Returns:
        - list: Lista actualizada de IDs de artistas sin duplicados.
        """
        artistas_similares = []

        for id_artista in artistas:
            relacionados = self.__spotipy_client.artist_related_artists(id_artista)["artists"]
            for artista_relacionado in relacionados:
                id_arista = artista_relacionado["id"]
                artistas_similares.append(id_arista)

        artistas.extend(artistas_similares)

        # Filtrar lista para evitar duplicados
        artistas = list(set(artistas))

        return artistas
    def __find_artistas_nuevos(self, artistas,limite=20):
        # Segunda parte del sistema de recomendacion 1.2
        # Ampliar al listado anterior(artistas en mi top y aristas relacionados) a artistas con nuevos lanzamientos
        
        # Se puede omitir si uno no esta interesado en obtener nuevas canciones, 
        # de todas formas el modelo deberia filtrarlas si a uno no le gustan la musica nueva

        nuevos_albumes = self.__spotipy_client.new_releases(limit=limite)["albums"]
        
        for album in nuevos_albumes["items"]:
            id_arista = album["artists"][0]["id"]
            artistas.append(id_arista)

        #Filtrar lista para evitar duplicados
        artistas = list(set(artistas))

        return artistas
    def __find_albumes(self, artistas, limite=1):
        """
        Obtiene IDs de álbumes para cada artista en la lista.

        Parameters:
        - artistas (list): Lista de IDs de artistas.
        - limite (int): Número máximo de álbumes a obtener por artista. Predeterminado es 1.

        Returns:
        - list: Lista de IDs de álbumes.
        """
        albumes = []
        for artista in artistas:
            album = self.__spotipy_client.artist_albums(artista, limit=limite)["items"][0]
            albumes.append(album["id"]) #Solo nos interesa el ID

        return albumes
    def __find_canciones_del_album(self, albumes,limite=1):
        """
        Obtiene IDs de canciones para cada álbum en la lista.

        Parameters:
        - albumes (list): Lista de IDs de álbumes.
        - limite (int): Número máximo de canciones a obtener por álbum. Predeterminado es 1.

        Returns:
        - list: Lista de IDs de canciones.
        """
        ids_canciones = []
        for album in albumes:
            canciones_album = self.__spotipy_client.album_tracks(album, limit=limite)["items"]
            for cancion in canciones_album:
                ids_canciones.append(cancion["id"])

        return ids_canciones
    def __find_audio_features(self, canciones):
        """
        Obtiene "audio features" de la lista de canciones pre-seleccionadas.

        Parameters:
        - canciones (list): Lista de IDs de canciones.

        Returns:
        - pd.DataFrame: DataFrame con los "audio features" de las canciones.
        """

        n_songs = len(canciones)

        if n_songs > 100:
            # Crear batches de 100 canciones (limitacion de audio_features)
            m = n_songs//100
            n = n_songs%100
            lotes = [None]*(m+1)
            for i in range(m):
                lotes[i] = canciones[i*100:i*100+100]
            if n != 0:
                lotes[i+1] = canciones[(i+1)*100:]
        else:
            lotes = [canciones]


        # Iterar sobre los lotes y agregar audio features
        audio_features = []
        for lote in lotes:
            features = self.__spotipy_client.audio_features(lote)
            audio_features.append(features)

        audio_features = [item for sublist in audio_features for item in sublist]
        audio_features = list(filter(lambda item: item is not None, audio_features))


        candidates_df = pd.DataFrame(audio_features)

        candidates_df = candidates_df[["id", "acousticness", "danceability", "duration_ms",
              "energy", "instrumentalness",  "key", "liveness", "loudness", "mode",
            "speechiness", "tempo", "valence"]]

        return candidates_df
    def __distancia_coseno(self, df_top, df_pre_seleccionados):
        """
        Calcula la distancia coseno entre las canciones del top y las canciones pre-seleccionadas.

        Parameters:
        - df_top (pd.DataFrame): DataFrame con las canciones del top.
        - df_pre_seleccionados (pd.DataFrame): DataFrame con las canciones pre-seleccionadas.

        Returns:
        - np.ndarray: Matriz de similitud coseno entre las canciones del top y las pre-seleccionadas.
        """


        # El algoritmo se llama content based filtering

        # Consiste en filtrar el listado de canciones pre-seleccionadas de acuerdo a la similaridad
        # con las canciones que ya estan en el top de mas escuchadas

        # Para ver la similaridad lo que se hace es plantear a cada cancion como un vector y plantear
        # la distancia coseno entre cada cancion del top contra cada cancion preseleccionada

        # lo importante es que la distancia coseno sera un vaor que oscila entre -1 y 1
        # siendo cercano a 1 cuando las canciones sean similares


        # nos quedamos solo con las columnas numericas, no me interesa el nombre
        top_canciones_mtx = df_top.iloc[:,1:].values
        candidatos_mtx = df_pre_seleccionados.iloc[:,1:].values

        # Estandarizar cada columna para que los atributos tenga la misma escala
        # en particular buscamos un metodo de escalado para que cada atributo tenga media 0 y desviacion 1
        scaler = StandardScaler()
        top_canciones_scaled = scaler.fit_transform(top_canciones_mtx)
        candidatos_scaled = scaler.fit_transform(candidatos_mtx)

        # Normalizar cada vector por norma euclidia
        top_canciones_norm = np.sqrt((top_canciones_scaled**2).sum(axis=1))
        candidatos_norm = np.sqrt((candidatos_scaled**2).sum(axis=1))

        n_top_canciones = top_canciones_norm.shape[0]
        n_candidatos = candidatos_norm.shape[0]

        top_canciones = top_canciones_scaled/top_canciones_norm.reshape(n_top_canciones,1)
        candidatos = candidatos_scaled/candidatos_norm.reshape(n_candidatos,1)

        # Calcular similitudes del coseno
        dist_coseno = linear_kernel(top_canciones,candidatos)

        return dist_coseno
    def __content_based_filtering(self, song_index, cos_sim, n, umbral = 0.8):
        """
            Obtener canciones candidatas similares a una pista dada.

            Parameters:
            - song_index (int): Índice de la cancion en el top20.
            - cos_sim (numpy.ndarray): Matriz de similitud coseno entre todas las pistas.
            - n (int): Número máximo de canciones candidatas a retornar.
            - umbral (float): Umbral de similitud para considerar una canción como candidata.
                             El valor predeterminado es 0.8.

            Returns:
            - cands (numpy.ndarray): Índices de las pistas consideradas como candidatas.
            """

        #obtener los indices de las canciones que cumplan la condicion
        idx = np.where(cos_sim[song_index,:]>=umbral)[0]

        #Retornar las canciones en forma descendente (similitud de mayor a menor)
        idx = idx[np.argsort(cos_sim[song_index,idx])[::-1]]

        #retornar un maximo de n canciones
        if len(idx) >= n:
            cands = idx[0:n]
        else:
            cands = idx

        return cands
    def create_recommended_playlist(self,titulo='Sistema de Recomendacion',descricpcion="by santiago Fada",top=20,
                                    max_nuevos_artistas=20,max_albumes=1,max_canciones_album=3,
                                    similaridad = 0.8,max_canciones_relacionadas=5):
        """
        Crea una playlist recomendada utilizando content based filtering.

        Parameters:
        - top (int): Número de canciones en el top a considerar.
        - max_nuevos_artistas (int): Número máximo de nuevos artistas a considerar.
        - max_albumes (int): Número máximo de álbumes por artista.
        - max_canciones_album (int): Número máximo de canciones por álbum a considerar.
        - similaridad (float): Umbral de similitud para considerar una canción como candidata.
        - max_canciones_relacionadas (int): Número máximo de canciones relacionadas a considerar.

        Returns:
        - None
        """


        #######
        # Este metodo llama a todos los metodos anteriores, de forma tal que
        # primero busca lo mas escuchado y lo almacena en un dataframe
        # luego obtiene artistas relacionados y nuevos
        # luego obtiene albumes de dichos artitas y de esos albumes saca canciones
        # para finalmente calcular la distancia y filtrar por un indice de similaridad

        # Obtener candidatos y compararlos (distancias coseno) con las pistas
        # del playlist original

        top_canciones = self.__find_top_canciones(limite=top)
        top_canciones_df = self.__create_songs_dataframe(top_canciones)
        print('1/8 Top canciones traidas con exito')

        artistas = self.__find_artistas(top_canciones)
        artistas = self.__find_artistas_similares(artistas)
        artistas = self.__find_artistas_nuevos(artistas,limite=max_nuevos_artistas)
        print('2/8 Artistas traidos con exito')

        albumes = self.__find_albumes(artistas,limite=max_albumes)
        print("3/8 Albumes encontrados")

        canciones_candidatas = self.__find_canciones_del_album(albumes,limite=max_canciones_album)
        print("4/8 Canciones candidatas")

        canciones_candidatas_df = self.__find_audio_features(canciones_candidatas)
        print('5/8 Caracteristicas extraidas')

        distancias = self.__distancia_coseno(top_canciones_df, canciones_candidatas_df)
        print("6/8 Distancias calculadas")

        # Crear listado de ids con las recomendaciones
        ids_top_canciones = []
        ids_playlist = []

        for i in range(top_canciones_df.shape[0]):
            ids_top_canciones.append(top_canciones_df['id'][i])

            # Obtener las canciones mas cercanas a la cancion
            canciones_agregar = self.__content_based_filtering(i, distancias,n = max_canciones_relacionadas, umbral=similaridad)

            # agregar las canciones
            if len(canciones_agregar) !=0 :
                for j in canciones_agregar:
                    id_cand = canciones_candidatas_df['id'][j]
                    ids_playlist.append(id_cand)

        ids_playlist_dep = [x for x in ids_playlist if x not in ids_top_canciones]

        ids_playlist_dep = list(set(ids_playlist_dep))

        print('7/8 Creando playlist')

        pl = self.__spotipy_client.user_playlist_create(user = self.__username,
            name = titulo,
            description = descricpcion)
        self.__spotipy_client.playlist_add_items(pl['id'],ids_playlist_dep)
        print("8/8 Playlist creada")


    def __find_user_playlist(self):
        return self.__spotipy_client.user_playlists(self.__username)["items"]
    def __find_user_liked_songs(self,full=True):

        if full:
            limit = 50
            mg = []

            total_canciones = self.total_liked_songs()

            for offset in range(0, total_canciones, limit):
                current_page_tracks = self.__spotipy_client.current_user_saved_tracks(limit=limit, offset=offset)['items']
                mg.extend(current_page_tracks)
        else:
            mg = self.__spotipy_client.current_user_saved_tracks(limit=20)['items']

        return mg
    def total_playlist(self):
        return len(self.__find_user_playlist())
    def total_liked_songs(self):
        return self.__spotipy_client.current_user_saved_tracks(limit=1)['total']
    def liked_songs(self,full=True):
        print("Canciones Guardadas")
        if not(full):
            print("version reducida")
        print("*"*15)
        mg = self.__find_user_liked_songs(full=full)
        for i, song in enumerate(mg):
            cadena = ""
            cadena += f"    {i+1}){song['track']['name']}  --- "
            for j,artist in enumerate(mg[i]['track']['artists']):
                cadena += artist['name']
                if j+1 < len(mg[i]['track']['artists']):
                    cadena += ", "

            print(cadena)
    def playlist(self):

        cadena = "playlist\n"
        playlists = self.__find_user_playlist()

        for i, item in enumerate(playlists):
            cadena += f"    {i + 1}){item['name']} -- canciones: {item['tracks']['total']}\n"

        return cadena
    def user_info(self):

        print(f"Usuario: {self.__username}")

        print(f"Playlist: {self.total_playlist()}")
        print(f"Canciones guardas: {self.total_liked_songs()}")
    def __canciones_playlist(self, playlist_name):
        playlists = self.__spotipy_client.user_playlists(self.__spotipy_client.me()['id'])

        playlist_id = ''
        for playlist in playlists['items']:
            if playlist['name'] == playlist_name:
                playlist_id = playlist['id']

        if playlist_id=='':
            print("PLAYLIST NO ECONTRDA")


        playlist_tracks = []
        results = self.__spotipy_client.playlist_tracks(playlist_id)
        playlist_tracks.extend(results['items'])

        while results['next']:
            results = self.__spotipy_client.next(results)
            playlist_tracks.extend(results['items'])

        return playlist_tracks
    def __find_missing_tracks(self, source_tracks, target_tracks):
        source_ids = {track['track']['id'] for track in source_tracks}
        target_ids = {track['track']['id'] for track in target_tracks}

        missing_tracks = source_ids - target_ids
        missing_track_info = [track for track in source_tracks if track['track']['id'] in missing_tracks]

        return missing_track_info
    def __check_saved_vs_playlist(self, playlist_name):
        saved_tracks = self.__find_user_liked_songs()
        playlist_tracks = self.__canciones_playlist(playlist_name)

        missing_in_playlist = self.__find_missing_tracks(saved_tracks, playlist_tracks)
        missing_in_saved = self.__find_missing_tracks(playlist_tracks, saved_tracks)

        return missing_in_playlist, missing_in_saved
    def playlist_vs_liked(self, playlist=""):
        """
        Compara las canciones entre la playlist especificada y las canciones guardadas.

        Parameters:
        - playlist (str): Nombre de la playlist a comparar.

        Returns:
        - None
        """
        no_todo, no_guardadas = self.__check_saved_vs_playlist(playlist)

        print("Canciones en TODO pero no en Guardadas:")
        for cancion in no_guardadas:
            print(cancion['track']['name'])

        print("\nCanciones Guardadas pero no en TODO:")
        for cancion in no_todo:
            print(cancion['track']['name'])
    def top_artistas(self,limite=50,plazo="short_term"):
        artistas = self.__spotipy_client.current_user_top_artists(time_range=plazo,limit=limite)['items']

        for i,artsita in enumerate(artistas):
            print(f"{i+1}){artsita['name']}")
    def top_canciones(self,plazo="short_term",limite=50):
        canciones = self.__find_top_canciones(limite=limite, plazo=plazo)['items']

        for i,cancion in enumerate(canciones):
            print(f"{i+1}){cancion['name']}")

    def create_liked_songs_playlist(self, playlist_name="Canciones Guardadas",
                                    descripcion="Playlist generada con canciones guardadas"):
        """
        Crea una playlist nueva con todas las canciones guardadas (me gusta) del usuario.

        Parameters:
        - playlist_name (str): Nombre de la nueva playlist.
        - descripcion (str): Descripción de la playlist.

        Returns:
        - None
        """
        print("Obteniendo canciones guardadas...")
        saved_tracks = self.__find_user_liked_songs(full=True)

        # Extraer los IDs de las canciones
        ids = [track['track']['id'] for track in saved_tracks if track['track'] is not None]

        if not ids:
            print("No habia canciones guardadas.")
            return

        print(f"{len(ids)} canciones encontradas. Creando playlist...")

        # Crear nueva playlist
        playlist = self.__spotipy_client.user_playlist_create(user=self.__username, name=playlist_name,
                                                              description=descripcion)

        # Agregar en lotes de 100
        for i in range(0, len(ids), 100):
            self.__spotipy_client.playlist_add_items(playlist_id=playlist['id'], items=ids[i:i + 100])

        print("Playlist creada con éxito.")