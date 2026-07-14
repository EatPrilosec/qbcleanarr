# qbcleanarr

A lightweight Dockerized Python script that interacts with the qBittorrent API to remove completed (not seeding) downloads from specific categories.

## Configuration

Copy the `config.ini.example` to `config.ini` and edit it to match your setup:

```ini
[qbseeder]
address=glutun
port=8180
apikey=qbt_BW5XAsxvvqy38hKs7t8J7GHzWnKh
categories=sonarr-imported,radarr-imported
cleanmode=remove

[qbrss]
address=glutun
port=8280
apikey=qbt_LUnCLhwu9VIFPUZUejkgt8EXkdaU
categories=JustSeedin
cleanmode=delete
```

- `address`: The hostname or IP of your qBittorrent instance.
- `port`: The port of your qBittorrent instance.
- `apikey`: Your qBittorrent API key (available in qBittorrent v5.2.0+). Leave blank if not using one.
- `categories`: Comma-separated list of categories to clean.
- `cleanmode`:
  - `remove`: Removes the torrent from qBittorrent but keeps the files.
  - `delete`: Removes the torrent from qBittorrent and deletes the downloaded files.

## Docker Compose Example

```yaml
version: '3.8'

services:
  qbcleanarr:
    image: ghcr.io/<your-github-username>/qbcleanarr:latest
    container_name: qbcleanarr
    restart: unless-stopped
    environment:
      - RUN_INTERVAL_MINUTES=5
      - TZ=UTC
    volumes:
      - ./config.ini:/config/config.ini:ro
```

Replace `<your-github-username>` with your actual GitHub username (lowercase).

## Environment Variables

- `RUN_INTERVAL_MINUTES`: How often the cleaner should run in minutes (default: 5).
- `CONFIG_PATH`: Path to the configuration file (default: `/config/config.ini` inside Docker).
