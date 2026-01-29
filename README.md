![Build and Push Docker Image](https://github.com/v1nsai/curseforge-updater/actions/workflows/build_and_push.yaml/badge.svg)
![Version](https://img.shields.io/github/v/tag/v1nsai/curseforge-updater?label=version)
![Docker](https://img.shields.io/docker/v/doctor3w/curseforge-updater?label=docker)
# Curseforge Updater

This is a Dockerized script that scans your game's mod folder and updates mods found in there.  So far it is only tested with Hytale but likely works with other games (adjust the file types if your game uses mods in files other than `.jar` or `.zip`).

## Usage
### Docker Quickstart
```
git clone https://github.com/v1nsai/curseforge-updater.git`
cd curseforge-updater
cp .env.example .env
cp docker-compose.example.yaml docker-compose.yaml
```
* Fill in values for vars in `.env`.  I have only tested with Hytale `GAME_ID` but should work with any other game in Curseforge.
* Update `docker-compose.yaml` with the location of your mods folder in volumes.
* `docker compose up -d && docker compose logs -f`

### Python Quickstart
```
git clone https://github.com/v1nsai/curseforge-updater.git
cd curseforge-updater
python3 -m venv .venv
source .venv/bin/activate
# inside venv shell
pip install -r requirements.txt
cp .env.example .env
```
* Fill in values for vars in `.env`.  I have only tested with Hytale `GAME_ID` but should work with any other game in Curseforge.
* Run the script with the location of your mods (still inside the venv environment)  
  `python3 src/init.py <</path/to/your/mod/folder>>`

### Integrate with Dockerized server
If your server is already using Docker, you can update your mods every time you restart to automatically always have the latest versions. 

* Copy the [.env.example](https://github.com/v1nsai/curseforge-updater/blob/develop/.env.example) file into the same folder as your `docker-compose.yaml` file as `.env` and fill in the vars (or add the vars to your existing `.env` file)
* Copy the `curseforge-updater` service from the `docker-compose.example.yaml` in this repo to your `docker-compose.yaml` file
* To ensure mods get updated before starting the server, add the following to your game server's service in your `docker-compose.yaml`:
    ```yaml
    services:
        my-game-service:
            // the rest of your service definition
            depends_on:
                curseforge-updater:
                    condition: service_completed_successfully
    ```
    See the [docker-compose.example.yaml](https://github.com/v1nsai/curseforge-updater/blob/develop/docker-compose.example.yaml) for a full example
* Map the `/mods` folder to the folder containing all your game's mods in `curseforge-updater`'s volumes.  See [docker-compose.example.yaml](https://github.com/v1nsai/curseforge-updater/blob/develop/docker-compose.example.yaml) for details

## Development
Uncomment the `$.services.curseforge-updater.build.context` to use your local Dockerfile instead of the latest in git.  See [docker-compose.example.yaml](https://github.com/v1nsai/curseforge-updater/blob/develop/docker-compose.example.yaml) for details

The `./scripts` directory has a few helper scripts for clean rebuilding and clean recreating.
