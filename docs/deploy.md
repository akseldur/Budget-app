# Drift

Kjører på en DigitalOcean-droplet (Frankfurt, $6/mnd), Docker Compose:
Postgres + FastAPI-backend + Caddy (automatisk HTTPS via Let's Encrypt).

HTTPS-adresser: `https://206-81-22-59.nip.io` (API) og
`https://app.206-81-22-59.nip.io` (web-app/PWA) - nip.io-triks for gratis TLS
uten eget domene, enhver `<noe>.<ip-med-bindestrek>.nip.io` peker på IP-en.

## Oppdatere serveren

```bash
ssh -i ~/.ssh/id_ed25519_budsjett root@206.81.22.59
cd /opt/budsjett-app
git pull
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

## Automatisk banksynk

Crontab på serveren kjører `backend/scripts/sync_all_accounts.py` hver 6.
time (4 ganger/døgn) inne i backend-containeren - henter nye transaksjoner
for alle registrerte kontoer uten at noen må trigge det manuelt.

Hyppigheten er *ikke* vilkårlig: PSD2 sin RTS artikkel 36(5)(b) begrenser
AISP-tilgang uten aktiv brukerinvolvering til maks 4 ganger per 24 timer med
mindre banken og TPP-en har avtalt noe annet spesifikt. Enable Banking sin
egen anbefaling ved `ASPSP_RATE_LIMIT_EXCEEDED` er å vente minst 6 timer
mellom bakgrunnskall - derav `0 */6 * * *`, ikke hver time.

## Backup

Crontab kjører `scripts/backup-db.sh` hver natt: dumper Postgres til
`/opt/budsjett-app/backups/`, beholder siste 7 dager. Ligger foreløpig kun
på serveren selv (beskytter mot data-feil, ikke mot at hele serveren går tapt).

## Crontab-oppsett (kjørt én gang ved oppsett)

```bash
crontab -e
```

```
0 */6 * * * cd /opt/budsjett-app && docker compose -f docker-compose.prod.yml exec -T backend python scripts/sync_all_accounts.py >> /var/log/budsjett-sync.log 2>&1
0 3 * * * /opt/budsjett-app/scripts/backup-db.sh >> /var/log/budsjett-backup.log 2>&1
```

## Web-app (PWA)

`mobile/` bygges også som en statisk web-eksport og driftes på
`app.206-81-22-59.nip.io` (egen Caddy-container, se `mobile/Dockerfile` og
`mobile/Caddyfile.web`) - dette er veien til å få appen på iPhonen uten
Apple Developer-konto ($99/år): åpne adressen i Safari én gang og
"Legg til på Hjem-skjerm". Åpnes deretter i fullskjerm uten nettleser-UI.

`EXPO_PUBLIC_API_URL`/`EXPO_PUBLIC_API_KEY` bakes inn i JS-bunten ved bygg
(se `WEB_API_URL`/`WEB_API_KEY` i rot-`.env` på serveren, brukt av
`docker-compose.prod.yml`s `web`-tjeneste). Siden dette er en statisk
web-eksport er API-nøkkelen synlig for alle som åpner siden og ser på
nettverkstrafikken - annerledes enn native-appen, der den kun lå lokalt på
telefonen. Akseptabelt her siden appen kun eksponerer denne ene brukerens
egne data og adressen ikke er publisert noe sted, men verdt å vite.
