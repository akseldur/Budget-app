# Drift

Kjører på en DigitalOcean-droplet (Frankfurt, $6/mnd), Docker Compose:
Postgres + FastAPI-backend + Caddy (automatisk HTTPS via Let's Encrypt).

HTTPS-adresse: `https://206-81-22-59.nip.io` (nip.io-triks for gratis TLS
uten eget domene - `<ip-med-bindestrek>.nip.io` peker alltid på IP-en).

## Oppdatere serveren

```bash
ssh -i ~/.ssh/id_ed25519_budsjett root@206.81.22.59
cd /opt/budsjett-app
git pull
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

## Automatisk banksynk

Crontab på serveren kjører `backend/scripts/sync_all_accounts.py` hver time
inne i backend-containeren - henter nye transaksjoner for alle registrerte
kontoer uten at noen må trigge det manuelt.

## Backup

Crontab kjører `scripts/backup-db.sh` hver natt: dumper Postgres til
`/opt/budsjett-app/backups/`, beholder siste 7 dager. Ligger foreløpig kun
på serveren selv (beskytter mot data-feil, ikke mot at hele serveren går tapt).

## Crontab-oppsett (kjørt én gang ved oppsett)

```bash
crontab -e
```

```
0 * * * * cd /opt/budsjett-app && docker compose -f docker-compose.prod.yml exec -T backend python scripts/sync_all_accounts.py >> /var/log/budsjett-sync.log 2>&1
0 3 * * * /opt/budsjett-app/scripts/backup-db.sh >> /var/log/budsjett-backup.log 2>&1
```
