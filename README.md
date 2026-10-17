# PyTune - Reproductor de Musica de Escritorio

Reproductor de musica local con gestion de playlists, construido en Python con
CustomTkinter (UI), python-vlc (audio), mutagen (metadatos) y persistencia JSON.

## Funcionalidades

- Play / Pausa / Detener / Siguiente / Anterior
- Barra de progreso interactiva (seek) y control de volumen con mute
- Modos aleatorio (shuffle) y repeticion (loop)
- Multiples playlists: crear, eliminar, cambiar
- Agregar/quitar canciones desde el explorador de archivos
- Lectura automatica de titulo, artista, album y duracion; extraccion de caratulas
- Autoguardado en `data/playlists.json` (no se pierde al cerrar)
- Resaltado de la cancion en reproduccion
- Dark mode por defecto

## Requisito previo: VLC

El motor de audio usa `python-vlc`, que necesita **VLC Media Player instalado**
en el sistema (no basta con el paquete de Python):

- Descarga: https://www.videolan.org/vlc/
- Instala la version de 64 bits que coincida con tu Python.
- Si VLC esta instalado en una ruta no estandar, agrega su carpeta a la variable
  de entorno `PATH` (por ejemplo `C:\Program Files\VideoLAN\VLC`).

## Instalacion

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Ejecucion

```powershell
python main.py
```

## Estructura del proyecto

```
music_player/
├── main.py
├── requirements.txt
├── README.md
├── data/                       # creado en tiempo de ejecucion
│   ├── playlists.json
│   └── covers/
└── src/
    ├── config.py               # constantes y rutas
    ├── models.py               # Track, Playlist
    ├── audio/engine.py         # wrapper de python-vlc
    ├── data/
    │   ├── metadata.py         # lectura con mutagen
    │   └── storage.py          # repositorio JSON (escritura atomica)
    └── ui/
        ├── app.py              # ventana principal y orquestacion
        ├── controls.py         # panel de reproduccion
        ├── tracklist.py        # tabla de canciones
        └── sidebar.py          # lista de playlists
```

## Notas de arquitectura

- La UI nunca llama a VLC directamente: todo pasa por `AudioEngine`.
- El estado de reproduccion (indice actual, shuffle, loop) vive en `app.py`.
- Los datos de playlists se guardan de forma atomica para evitar corrupcion.
- El tick del slider usa `after()` de Tkinter (sin hilos adicionales).
