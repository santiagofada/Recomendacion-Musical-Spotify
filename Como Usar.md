# Spotify Recommendation System

Este proyecto implementa un sistema de recomendación de Spotify utilizando Python y la API de Spotify.


## Configuración

1. Ve a [Spotify Developer](https://developer.spotify.com/) e inicia sesión.
2. En la pestaña superior derecha, selecciona tu nombre y luego selecciona "Dashboard".
3. Crea una nueva aplicación con un nombre, descripción y una URI como la siguiente: http://localhost:8888.
4. Una vez que la aplicación esté creada, ve a la sección de "Settings".
5. Copia el Client ID y el Client Secret.
6. En el archivo `credentials.py`, agrega las siguientes líneas:
    ```python
    cid = 'tu_client_id'
    secret = 'tu_client_secret'
    ```


7. Instala las dependencias que se encuentran en el archivo `requirements.txt`:

    ```bash
    pip install -r requirements.txt
    ```

Ahora estás listo para ejecutar el proyecto y explorar las recomendaciones de Spotify.

Para ejecutar correr el archivo
    ```
    main.py
    ```

