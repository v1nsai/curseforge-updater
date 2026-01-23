# Curseforge Updater
This is a Dockerized script that scans your game's mod folder and updates mods found in there.  So far it is only tested with Hytale but likely works with other games (adjust the file types if your game uses mods in files other than `.jar` or `.zip`).

Use with caution since it isn't highly tested yet.  At the moment it will loudly fail if anything unexpected happens, rather than letting silent failures cause a bigger problem.

## Usage
The easiest way to get started is to copy the `docker-compose.yaml` file into your project's compose file, it will pull and build the latest from the `develop` branch of this repo.

* Copy the [.env.example](https://github.com/v1nsai/curseforge-updater/blob/develop/.env.example) file into the same folder as your `docker-compose.yaml` file as `.env` and fill in the variables
* Copy the `curseforge-updater` service from the `docker-compose.yaml` in this repo to your `docker-compose.yaml` file
* To make sure `curseforge-updater` runs and completes successfully before your service starts, add the following to your game server's service in your `docker-compose.yaml`:
    ```yaml
    services:
        my-game-service:
            // the rest of your service definition
            depends_on:
                curseforge-updater:
                    condition: service_completed_successfully
    ```
    See the [docker-compose.yaml](https://github.com/v1nsai/curseforge-updater/blob/develop/docker-compose.yaml) for a full example
* Map the `/mods` folder to the folder containing all your game's mods in `curseforge-updater`'s volumes.  See [docker-compose.yaml](https://github.com/v1nsai/curseforge-updater/blob/develop/docker-compose.yaml) for details

## Development
Uncomment the `$.services.curseforge-updater.build.context` to use your local Dockerfile instead of the latest in git.  See [docker-compose.yaml](https://github.com/v1nsai/curseforge-updater/blob/develop/docker-compose.yaml) for details

Clean rebuild one-liner:  
`docker compose down && docker compose build --no-cache && docker compose up -d --force-recreate && docker compose logs -f`