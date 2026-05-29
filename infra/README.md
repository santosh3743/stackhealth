# Deploying StackHealth on a free Oracle Cloud VM

Total cost: **$0/month, forever** (Oracle's Always Free tier).

You get a 4-core ARM (Ampere) VM with 24 GB RAM and 200 GB disk that
runs Postgres, Redis, the API, the worker, the Next.js frontend, and
Caddy (for TLS) all on one box via docker-compose.

## What you need before starting

1. An Oracle Cloud account — sign up at https://cloud.oracle.com (the
   credit card is for identity verification; you'll stay on Always Free).
2. A domain name you control (any registrar — Cloudflare, Namecheap,
   Porkbun, etc.). The deploy assumes you serve from `${DOMAIN}` and
   `api.${DOMAIN}`.
3. An SSH client.

## Step 1 — Provision the VM (10 min)

1. In the Oracle console, **Compute → Instances → Create Instance**.
2. Image: **Canonical Ubuntu 24.04**.
3. Shape: **VM.Standard.A1.Flex** — set to **4 OCPUs, 24 GB memory**
   (Always Free allowance).
4. Add your SSH public key.
5. Create.
6. Once it boots, note the public IP.

### Open ports 80 and 443

Oracle blocks all inbound traffic by default. In the instance's VCN
security list, add ingress rules:

| Source | Protocol | Destination Port |
|--------|----------|------------------|
| 0.0.0.0/0 | TCP | 80 |
| 0.0.0.0/0 | TCP | 443 |

Also on the VM itself (Oracle's Ubuntu images include iptables rules
that need updating):

```bash
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT
sudo netfilter-persistent save
```

## Step 2 — Point DNS at the VM

At your DNS provider, create two A records:

| Name | Type | Value |
|------|------|-------|
| `stackhealth.example.com` (your apex) | A | `<vm-ip>` |
| `api.stackhealth.example.com` | A | `<vm-ip>` |

Let propagation finish (usually under a minute). Verify with `dig` or
`https://dnschecker.org`.

## Step 3 — Install Docker on the VM (5 min)

SSH in and run:

```bash
sudo apt update && sudo apt upgrade -y
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
newgrp docker
# Log out and back in so the group takes effect.
```

## Step 4 — Clone + configure (3 min)

```bash
git clone https://github.com/santosh3743/stackhealth.git
cd stackhealth
cp infra/.env.prod.example .env
nano .env          # fill in DOMAIN, ACME_EMAIL, POSTGRES_PASSWORD, GITHUB_TOKEN
```

Generate a strong Postgres password: `openssl rand -base64 32`.

The `GITHUB_TOKEN` is optional but **strongly recommended** — without
it, the worker hits GitHub's 60 requests/hour anonymous limit and most
scans will fail. Create a [fine-grained PAT](https://github.com/settings/tokens?type=beta)
with read access to public repositories.

## Step 5 — Deploy (5 min for first build, faster after)

```bash
./infra/deploy.sh
```

This:

1. Builds three Docker images (API, worker, web).
2. Boots Postgres + Redis with persistent volumes.
3. Runs Alembic migrations as a one-shot init container.
4. Starts API, worker, web, and Caddy.
5. Caddy automatically fetches Let's Encrypt certs for both
   `${DOMAIN}` and `api.${DOMAIN}`.

Watch the logs:

```bash
./infra/deploy.sh logs
```

Look for `certificate obtained successfully` from Caddy on first boot.

## Step 6 — Verify

```bash
curl https://api.your-domain.com/api/health
# {"status":"ok","version":"0.0.1","formula_version":"v1.0"}

open https://your-domain.com   # or visit in browser
```

## Operating it

```bash
./infra/deploy.sh status   # service health
./infra/deploy.sh logs     # tail all logs
./infra/deploy.sh pull     # git pull + rebuild + restart
./infra/deploy.sh down     # stop everything (data is preserved)
```

### Backups

Postgres data lives in the `postgres-data` named volume. To back it up
nightly via cron:

```bash
docker exec stackhealth-postgres-1 \
  pg_dump -U stackhealth stackhealth | gzip > "backup-$(date +%F).sql.gz"
```

Even better: copy to a free Cloudflare R2 bucket (10 GB free).

### Cold start expectations

None. Unlike free Render or free Vercel functions, this VM is always
on. Cold start = 0 seconds.

### When you need more capacity

Always Free covers a *lot* — well over 1000 scans/hour at the current
sizing. If you outgrow it: bump the VM shape, or split the worker into
multiple instances behind the same Redis queue. Both are non-invasive
changes; the architecture is already horizontally scalable.

## What about CI auto-deploy?

`.github/workflows/deploy.yml` already supports push-to-deploy via
SSH. It stays dormant until you add three repo secrets:

| Secret | Value |
|--------|-------|
| `DEPLOY_HOST` | The VM's public IP or DNS name |
| `DEPLOY_USER` | The SSH user (usually `ubuntu`) |
| `DEPLOY_SSH_KEY` | A private key whose public half is in `~/.ssh/authorized_keys` on the VM |

Optional: `DEPLOY_PATH` (defaults to `~/stackhealth`) if the repo
lives somewhere other than the home directory.

Once those are set, every push to `main` will SSH into the VM and run
`./infra/deploy.sh pull` — which `git pull`s the latest commit, rebuilds
the images, and rolls the services.

## Troubleshooting

**`Caddy: tls: failed to get certificate`** — port 80/443 isn't
reachable. Re-check VCN ingress rules *and* `iptables` on the VM.

**`migrate exited (1) — psycopg DuplicateObject`** — your Postgres
volume already has a half-applied schema from an earlier failed run.
Drop the volume (`docker compose -f infra/docker-compose.prod.yml down -v`)
and redeploy. **Only safe before you have real data.**

**Build runs out of memory on the VM** — give the swap a bump:
```bash
sudo fallocate -l 4G /swapfile && sudo chmod 600 /swapfile
sudo mkswap /swapfile && sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```
