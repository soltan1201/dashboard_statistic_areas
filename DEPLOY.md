# Deploy — Hugging Face Spaces

Guia completo para hospedar o dashboard MapBiomas Caatinga no Hugging Face Spaces usando Docker.

---

## Situação dos arquivos grandes

| Arquivo | Tamanho | Estratégia |
|---|---|---|
| `database.sqlite` | 112 MB | Git LFS |
| `vetor_biomas_250.geojson` | 48 MB | Git LFS |
| `br_estados_shp.geojson` | 22 MB | Git LFS |
| `bacias_caatinga*.geojson` | 16 MB | Git LFS |
| `semiarido2024.geojson` | 6.6 MB | Git normal |

---

## Passo 1 — Criar o Space no Hugging Face

1. Acesse [huggingface.co](https://huggingface.co) → **New Space**
2. Preencha:
   - **Space name**: `mapbiomas-caatinga-dashboard`
   - **SDK**: `Docker` → template **Blank**
   - **Visibility**: Public ou Private
3. Clique **Create Space**

---

## Passo 2 — Instalar dependências locais

```bash
# CLI do Hugging Face
pip install huggingface_hub hf

# Git LFS
sudo apt install git-lfs      # Linux
# brew install git-lfs        # macOS
```

---

## Passo 3 — Login e clone do Space

```bash
# Gere o token em: hf.co → Settings → Access Tokens → New token (write)
hf auth login

# Clonar o repo do Space
cd ~/
git clone https://huggingface.co/spaces/SEU_USER/mapbiomas-caatinga-dashboard
cd mapbiomas-caatinga-dashboard
```

---

## Passo 4 — Configurar Git LFS

```bash
git lfs install

git lfs track "*.sqlite"
git lfs track "*.db"
git lfs track "*.geojson"

git add .gitattributes
```

---

## Passo 5 — Copiar os arquivos do projeto

```bash
# Código, templates, static e dados
cp -r /caminho/para/dashboard_statistic_areas/src/* .

# Dockerfile (já existente na raiz do projeto)
cp /caminho/para/dashboard_statistic_areas/Dockerfile .
```

---

## Passo 6 — Criar o README.md com metadados do Space

```bash
cat > README.md << 'EOF'
---
title: MapBiomas Caatinga Dashboard
emoji: 🌿
colorFrom: green
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
---
EOF
```

---

## Passo 7 — Criar .gitignore do repo HF

O banco de dados precisa ser incluído no repo HF (via Git LFS), então o `.gitignore` aqui é mais simples:

```bash
cat > .gitignore << 'EOF'
.venv/
__pycache__/
*.py[cod]
.env
.DS_Store
EOF
```

---

## Passo 8 — Commit e Push

```bash
git add .
git commit -m "deploy: MapBiomas Caatinga Dashboard v1"
git push
```

O HF Spaces detecta o `Dockerfile` automaticamente, executa o build e em alguns minutos o app estará disponível em:

```
https://huggingface.co/spaces/SEU_USER/mapbiomas-caatinga-dashboard
```

Acompanhe o build na aba **Logs** do Space.

---

## Fluxo resumido

```
Projeto local                  HF Space repo
─────────────                  ─────────────────────────
src/              ──copy──►    run.py, app/, dados/
Dockerfile        ──copy──►    Dockerfile
database.sqlite   ──LFS──►     instance/database.sqlite
*.geojson         ──LFS──►     dados/geojson/*.geojson
                               README.md  ← metadados HF
                                    ↓
                          docker build + run (porta 7860)
                                    ↓
                  https://huggingface.co/spaces/SEU_USER/...
```

---

## Variáveis de ambiente relevantes

| Variável | Valor HF Spaces | Descrição |
|---|---|---|
| `PORT` | `7860` | Porta obrigatória do HF Spaces |
| `FLASK_DEBUG` | `false` | Desabilitar debug em produção |

---

## Problemas comuns

| Problema | Solução |
|---|---|
| Build falha em `libgdal` | Verificar se o `Dockerfile` inclui `apt-get install libgdal-dev` |
| App não abre (504) | Confirmar que Flask escuta em `host='0.0.0.0'` e `port=7860` |
| GeoJSON não carrega | Verificar se o arquivo foi commitado via Git LFS (`git lfs ls-files`) |
| Banco vazio após reinício | Normal — o storage é efêmero; o `.sqlite` deve estar no repo via LFS |
