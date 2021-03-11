# fetchAlmaWebGrades

# Build
```
docker build -t almaweb-bot ./bot
```

# Staging & Deployment
```
cp .env.example .env
cp bot/grades.db.example bot/grades.db
docker run -it -v "$(pwd)/bot:/usr/src/app" --rm --env-file .env --name almaweb-bot-running almaweb-bot
```
