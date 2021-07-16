# fetchAlmaWebGrades
This bot sends you your newest grades from the online platform AlmaWeb from the university of Leipzig to your telegram.  
It stores the already known grades to a SQLite DB, so it needs a first run for initialization.  
It can be used as a docker container or without.  


# Build
```
docker build -t almaweb-bot ./bot
```

# Run
Fill .env file with your credentials.
```
cp .env.example .env
docker run -it -v "$(pwd)/bot:/usr/src/app" --rm --env-file .env --name almaweb-bot-running almaweb-bot
```
