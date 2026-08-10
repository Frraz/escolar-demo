# Deploy — VPS Ferzion (warley.dev.ferzion.com.br)

Runbook para colocar o Sistema Escolar Demo no ar em `https://escolar-demo.ferzion.com.br`, seguindo exatamente as convenções já usadas nos outros sistemas do servidor (ver `README.md` do servidor em `/var/www/docker-instances/README.md`):

- **Nenhum container mapeia as portas 80/443** — só o nginx do host faz isso.
- App Docker escuta apenas em `127.0.0.1:8011` (porta livre — não conflita com nenhum sistema existente: 8001-8006, 8010, 8080, 8110, 9000 já estão em uso).
- `staticfiles/` fica em bind mount no host, servido diretamente pelo nginx (mesmo padrão do ConfTech).
- SSL via certbot, mesmo fluxo dos outros domínios `.ferzion.com.br`.

---

## 0. Pré-requisitos

- [ ] DNS: um registro **A** de `escolar-demo.ferzion.com.br` apontando para `147.93.15.214` (propagação pode levar alguns minutos).
- [ ] Você tem um repositório Git remoto (GitHub/GitLab) para este projeto.
- [ ] Acesso SSH ao servidor (`ssh deploy@warley.dev.ferzion.com.br`).

Este projeto ainda **não está conectado ao Google Cloud** (sem `GOOGLE_CLIENT_ID`/`GOOGLE_CLIENT_SECRET` reais) — isso não impede o deploy. O sistema sobe normalmente e mostra "Google Drive desconectado"; você conecta depois pela tela **Configurações**, seguindo o README (seções 6-10), com o `GOOGLE_REDIRECT_URI` já apontando para o domínio de produção (passo 3 abaixo).

---

## 1. Enviar o código para o repositório remoto

No seu computador, dentro da pasta do projeto:

```bash
git add -A
git commit -m "Versão inicial do Sistema Escolar Demo"
git remote add origin <URL_DO_SEU_REPOSITORIO>
git push -u origin main
```

---

## 2. Clonar no servidor

```bash
ssh deploy@warley.dev.ferzion.com.br
cd /var/www/docker-instances
git clone <URL_DO_SEU_REPOSITORIO> escolar-demo
cd escolar-demo
```

---

## 3. Configurar o `.env` de produção

```bash
cp .env.example .env
nano .env
```

Gere valores únicos (não reutilize os do `.env.example`):

```bash
docker run --rm python:3.12-slim python -c "from secrets import token_urlsafe; print(token_urlsafe(50))"
docker run --rm python:3.12-slim bash -c "pip install cryptography -q && python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
```

Preencha o `.env` assim (valores específicos deste deploy, o resto pode manter o padrão do `.env.example`):

```env
SECRET_KEY=<gerado acima>
DEBUG=False
ALLOWED_HOSTS=escolar-demo.ferzion.com.br,localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=https://escolar-demo.ferzion.com.br
DJANGO_SETTINGS_MODULE=config.settings.production

DATABASE_URL=postgres://escolar:<senha-forte-própria>@db:5432/escolar_demo
POSTGRES_USER=escolar
POSTGRES_PASSWORD=<a mesma senha forte usada no DATABASE_URL>
POSTGRES_DB=escolar_demo

FIELD_ENCRYPTION_KEY=<gerado acima>

GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=https://escolar-demo.ferzion.com.br/google-drive/oauth2callback/
GOOGLE_OAUTH_SCOPES=https://www.googleapis.com/auth/drive.file,https://www.googleapis.com/auth/spreadsheets
GOOGLE_DRIVE_ROOT_FOLDER_ID=

MAX_UPLOAD_SIZE_MB=15
ALLOWED_UPLOAD_EXTENSIONS=.pdf,.jpg,.jpeg,.png,.doc,.docx,.xls,.xlsx,.txt,.csv
TIME_ZONE=America/Sao_Paulo
```

> `localhost` em `ALLOWED_HOSTS` é necessário para o healthcheck interno do container (`docker ps` mostra "healthy"/"unhealthy") — ele não fica exposto publicamente porque a porta só faz bind em `127.0.0.1`.
> Preencha `GOOGLE_CLIENT_ID`/`GOOGLE_CLIENT_SECRET`/`GOOGLE_DRIVE_ROOT_FOLDER_ID` depois, seguindo o `README.md` (seções 6-10) — o sistema funciona normalmente sem eles, só mostra "Drive desconectado".

---

## 4. Subir os containers

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

O `entrypoint.sh` já roda `migrate` e `collectstatic` automaticamente toda vez que o container `web` inicia — não é preciso rodar esses comandos manualmente.

Verifique:

```bash
docker ps --filter "name=escolar"
docker logs escolar_web --tail 50
```

Se `staticfiles` estiver vazio ou o nginx retornar 403 nos arquivos estáticos, corrija a permissão (mesmo problema conhecido do ConfTech — ver README do servidor):

```bash
sudo chown -R 1000:1000 /var/www/docker-instances/escolar-demo/staticfiles
docker restart escolar_web
```

---

## 5. Criar o superusuário

```bash
docker exec -it escolar_web python manage.py createsuperuser
```

---

## 6. Configurar o nginx do host

```bash
sudo cp /var/www/docker-instances/escolar-demo/deploy/nginx/escolar-demo.ferzion.com.br.conf \
  /etc/nginx/sites-available/escolar-demo.ferzion.com.br
sudo ln -s /etc/nginx/sites-available/escolar-demo.ferzion.com.br /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

## 7. Emitir o certificado SSL

```bash
sudo certbot --nginx -d escolar-demo.ferzion.com.br
```

O certbot edita o arquivo do nginx automaticamente, adicionando o bloco `443` e o redirecionamento de `80` para `443`.

---

## 8. Verificar

```bash
curl -I https://escolar-demo.ferzion.com.br/contas/login/
docker ps --filter "name=escolar"
```

Acesse `https://escolar-demo.ferzion.com.br` no navegador e faça login com o superusuário criado no passo 5.

**Adicione o domínio ao UptimeRobot** (mesmo painel usado para os outros sistemas) para ficar dentro do monitoramento padrão do servidor.

---

## Atualizações futuras (deploy padrão)

Igual ao fluxo já documentado no `README.md` do servidor:

```bash
cd /var/www/docker-instances/escolar-demo
git pull origin main
docker compose -f docker-compose.prod.yml build web
docker compose -f docker-compose.prod.yml up -d
docker logs escolar_web --tail 20
```

---

## Backups

O servidor não tem política de backup automática ("ambiente de sistemas de teste"). Os dados deste sistema vivem em dois lugares:

1. **PostgreSQL** (volume Docker `escolar-demo_postgres_data`) — alunos, turmas, notas, metadados de documentos e a credencial OAuth do Google.
2. **Google Drive do cliente** — os arquivos em si (não vivem no servidor).

Se quiser um backup periódico do banco, um cron simples:

```bash
# /etc/cron.d/escolar-demo-backup (exemplo)
0 3 * * * root docker exec escolar_db pg_dump -U escolar escolar_demo | gzip > /var/backups/escolar-demo-$(date +\%F).sql.gz
```

---

## Troubleshooting

| Sintoma | Causa provável | Solução |
|---|---|---|
| `Bad Request (400)` ao acessar o domínio | `ALLOWED_HOSTS` não inclui `escolar-demo.ferzion.com.br` | Corrija o `.env` e `docker compose -f docker-compose.prod.yml up -d` |
| `CSRF verification failed` ao logar/enviar formulário | `CSRF_TRUSTED_ORIGINS` vazio ou sem `https://` | Corrija o `.env` (deve ser a URL completa com `https://`) |
| CSS/JS/estáticos não carregam (404) | `collectstatic` não rodou ou nginx apontando para pasta errada | Confira `docker logs escolar_web` e o `alias` no bloco `/static/` do nginx |
| Estáticos com 403 | Permissão do bind mount | `sudo chown -R 1000:1000 staticfiles/` (ver passo 4) |
| `docker ps` mostra `unhealthy` | Healthcheck não consegue acessar `localhost` internamente | Confirme que `ALLOWED_HOSTS` inclui `localhost` |
| Upload sempre falha com "Drive ainda não foi conectado" | Esperado até você conectar a conta Google em Configurações | Siga o `README.md`, seções 6-10 |
| Todos os domínios do servidor caem juntos | Algum compose subiu com `"80:80"`/`"443:443"` | Ver seção "Incidentes Conhecidos" do README do servidor — **não é este projeto**, que nunca mapeia essas portas |
