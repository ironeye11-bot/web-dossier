# Auftrag: web-dossier public machen

Du bist als **ironeye11-bot** im Browser angemeldet. Dieser Ordner ist das fertige Repo.

Nicht den Code umschreiben. Tests nicht löschen. Keine Cloud-APIs.  
Nicht erwähnen: Hybrid-Eye, Kai, Bolt, Rivet.

```bash
cd web-dossier
PYTHONPATH=src python -m unittest discover -s tests -v
```

Alle Tests müssen OK sein.

Dann:

```bash
git init
git checkout -b main
git add .
git commit -m "Initial public release of web-dossier"
gh repo create ironeye11-bot/web-dossier --public --source . --remote origin --push \
  --description "Public URL in. Markdown plus images out. Localhost stays out."
gh repo edit ironeye11-bot/web-dossier \
  --add-topic cli --add-topic crawler --add-topic markdown --add-topic python --add-topic ssrf --add-topic local-first
gh release create v1.0.0 --title "v1.0.0" --notes "Public URL to dossier.md plus images. LAN and odd ports blocked."
```

Social preview: `docs/hero.jpg`  
Issues an, Wiki und Projects aus.

Danach nur die Repo-URL und die Testausgabe. Schluss.
