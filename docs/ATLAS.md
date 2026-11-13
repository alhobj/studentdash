# Atlas testing without manual pulls/builds

The full Python application runs on Atlas. GitHub Pages alone cannot run it.
This Docker setup creates a separate **fictional sandbox**, not your real class data.

After creating the new repository, put `deploy/atlas-update.sh` on Atlas, for example
at `/mnt/user/appdata/arborsynapse-test/update.sh`. In Unraid **User Scripts**, add:

```sh
export ARBOR_REPO_URL="https://github.com/alhobj/ArborSynapse.git"
export ARBOR_BRANCH="main"
export ARBOR_BIND_IP="YOUR_ATLAS_LAN_IP"
export ARBOR_TEST_HOSTS="atlas,atlas.local,YOUR_ATLAS_LAN_IP"
bash /mnt/user/appdata/arborsynapse-test/update.sh
```

Replace both IP placeholders with Atlas's LAN IP. For a private repository, first
configure read access on Atlas (a read-only deploy key and SSH URL are suitable).
Do not put a token in the script or commit credentials.

Run once, then schedule it every minute (`* * * * *`). Open
`http://YOUR_ATLAS_LAN_IP:5080/classes` through your existing network access.
After a push, the script fetches and rebuilds only a new revision. A failed build
keeps the old site running. Once the update finishes, refresh the browser.
The first build takes longer; Docker caches later builds.

Keep the managed `source` checkout free of edits. Sandbox state lives in Docker
volumes across updates. The default bind is loopback until you explicitly supply
Atlas's LAN IP. No router forwarding or real student-data mount is included.

Troubleshoot on Atlas:

```sh
cd /mnt/user/appdata/arborsynapse-test/source
docker compose -f deploy/compose.yaml logs --tail=80
```

Deployment is prepared, not active: the new repository and Atlas access must exist first.
