# Sistema Escolar Demo

MVP demonstrativo de um sistema escolar em Django cujo objetivo central é provar um modelo de arquitetura:

> **Sistema web → Google Drive / Google Sheets do cliente**

O sistema cadastra alunos, turmas, documentos e notas, mas **não guarda arquivos permanentemente no servidor**. Todo upload é enviado diretamente para a conta do **Google Drive do cliente**, organizado automaticamente em pastas. O banco de dados local (PostgreSQL) armazena apenas metadados e os IDs dos arquivos/pastas no Drive — nunca uma cópia do conteúdo. Notas de turma também podem ser espelhadas em uma planilha do Google Sheets, guardada dentro da pasta da turma correspondente.

O objetivo **não** é ser um ERP escolar completo — é demonstrar, de forma simples e profissional, que o cliente mantém total custódia dos seus próprios arquivos, mesmo que este sistema seja substituído no futuro.

---

## 1. Sumário

- [Arquitetura](#2-arquitetura)
- [Stack](#3-stack)
- [Como executar](#4-como-executar)
- [Configurar PostgreSQL](#5-configurar-postgresql)
- [Criar projeto no Google Cloud](#6-criar-projeto-no-google-cloud)
- [Habilitar Google Drive API](#7-habilitar-google-drive-api)
- [Habilitar Google Sheets API](#8-habilitar-google-sheets-api)
- [Configurar OAuth 2.0](#9-configurar-oauth-20)
- [Configurar a pasta raiz do Drive](#10-configurar-a-pasta-raiz-do-drive)
- [Migrations](#11-migrations)
- [Superusuário](#12-superusuário)
- [Testes](#13-testes)
- [Como funciona o upload](#14-como-funciona-o-upload)
- [Como funciona a organização dos arquivos](#15-como-funciona-a-organização-dos-arquivos)
- [Como funciona o Google Sheets](#16-como-funciona-o-google-sheets)
- [Segurança](#17-segurança)
- [Evoluindo para produção](#18-evoluindo-para-produção)

---

## 2. Arquitetura

O sistema é uma aplicação Django monolítica, renderizada no servidor (Django Templates + HTMX, sem frontend SPA), organizada em apps de domínio que **nunca** chamam a API do Google diretamente. Toda a integração passa por uma única camada de serviço, na app `google_drive`.

```mermaid
flowchart TB
    subgraph Navegador
        UI["Django Templates + HTMX + Tailwind"]
    end

    subgraph Django["Aplicação Django"]
        Views["Views das apps de domínio<br/>students · classes · documents · grades · dashboard"]
        Models["Modelos<br/>(guardam apenas metadados + IDs do Drive)"]
        Services["apps.google_drive.services<br/>GoogleAuthService · GoogleDriveService<br/>FolderStructureService · GoogleSheetsService"]
    end

    DB[(PostgreSQL)]
    Google["Google Drive API v3<br/>Google Sheets API"]
    Drive["Google Drive do cliente"]

    UI <--> Views
    Views --> Models
    Views --> Services
    Models <--> DB
    Services --> Google
    Google <--> Drive
```

Princípios:

- **Nenhuma app de domínio (`students`, `classes`, `documents`, `grades`) importa `googleapiclient`.** Apenas `apps/google_drive/services/*` fala com o Google.
- **O banco nunca guarda o conteúdo dos arquivos**, apenas `google_drive_file_id`, `google_drive_folder_id` e `google_drive_url`.
- **Consistência "Drive primeiro, banco depois"** no upload (ver seção 14).
- **Idempotência de pastas**: a mesma estrutura nunca é criada duas vezes (ver seção 15).

### Estrutura de diretórios

```text
config/
  settings/        base.py, local.py, production.py, test.py
apps/
  accounts/        autenticação de usuários do sistema (não confundir com OAuth do Google)
  students/        CRUD de alunos
  classes/         CRUD de turmas
  documents/       upload/download/exclusão de documentos
  grades/          notas por turma + sincronização com Google Sheets
  google_drive/    única app que fala com a API do Google
    services/        drive_service.py, sheets_service.py, folder_service.py, auth_service.py
    models.py         GoogleDriveFolder, GoogleSheet, GoogleCredential
    exceptions.py      hierarquia de erros amigáveis
  dashboard/       página inicial com métricas agregadas
templates/         Django Templates (uma pasta por app + partials/)
static/            Tailwind (via CDN) + HTMX
```

---

## 3. Stack

- Python 3.12, Django 5.1, Django REST Framework
- PostgreSQL 16
- google-api-python-client, google-auth, google-auth-oauthlib (Google Drive API v3 e Sheets API v4)
- Django Templates + HTMX + Tailwind CSS (via CDN — ver seção 18 sobre build para produção), com um pequeno design system próprio (paleta `brand`/`ink`, tipografia Inter, componentes reutilizáveis `.btn-*`, `.card`, `.badge-*`, `.field-*` definidos em `templates/base.html`) para manter a interface consistente em todas as telas
- Docker e Docker Compose
- pytest, pytest-django, pytest-mock, factory-boy

---

## 4. Como executar

> Para colocar em produção em um VPS (nginx do host + docker-compose.prod.yml + certbot), veja o runbook completo em [`DEPLOY.md`](DEPLOY.md). Esta seção cobre apenas o ambiente local de desenvolvimento.

Pré-requisitos: Docker e Docker Compose instalados.

```bash
cp .env.example .env
# edite o .env — para rodar localmente sem conectar ao Google de verdade, os
# valores padrão de FIELD_ENCRYPTION_KEY/SECRET_KEY do .env.example já funcionam,
# mas GERE valores próprios antes de qualquer uso real (ver seção 17).

docker compose up --build
```

Por padrão a aplicação sobe em `http://localhost:8010` (porta configurável via `WEB_HOST_PORT` no `.env`, caso a 8000 já esteja em uso na sua máquina) e o PostgreSQL fica exposto em `localhost:5433` (configurável via `POSTGRES_HOST_PORT`).

Em outro terminal, rode as migrations e crie um usuário:

```bash
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
```

Acesse `http://localhost:8010/` e faça login.

---

## 5. Configurar PostgreSQL

O `docker-compose.yml` já sobe um serviço `db` (Postgres 16) configurado via variáveis de ambiente `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` (padrão: `escolar` / `escolar` / `escolar_demo`). A aplicação se conecta usando a variável `DATABASE_URL` do `.env`:

```env
DATABASE_URL=postgres://escolar:escolar@db:5432/escolar_demo
```

Para rodar fora do Docker, aponte `DATABASE_URL` para uma instância PostgreSQL local (`postgres://usuario:senha@localhost:5432/escolar_demo`).

---

## 6. Criar projeto no Google Cloud

1. Acesse [console.cloud.google.com](https://console.cloud.google.com/) **com a conta Google do cliente** (não a do desenvolvedor — é nela que os arquivos ficarão armazenados).
2. Crie um novo projeto (ex: "Sistema Escolar").
3. No menu **APIs e serviços → Tela de consentimento OAuth**, configure um app do tipo "Externo" (ou "Interno" se a conta for Google Workspace), preenchendo nome do app e e-mail de suporte.

---

## 7. Habilitar Google Drive API

Em **APIs e serviços → Biblioteca**, busque por **Google Drive API** e clique em **Ativar**.

---

## 8. Habilitar Google Sheets API

Da mesma forma, busque por **Google Sheets API** na Biblioteca e clique em **Ativar**.

---

## 9. Configurar OAuth 2.0

1. Em **APIs e serviços → Credenciais → Criar credenciais → ID do cliente OAuth**.
2. Tipo de aplicativo: **Aplicativo da Web**.
3. Em **URIs de redirecionamento autorizados**, adicione exatamente a mesma URL configurada em `GOOGLE_REDIRECT_URI` no `.env`, por exemplo:
   ```text
   http://localhost:8010/google-drive/oauth2callback/
   ```
4. Copie o **Client ID** e o **Client Secret** gerados e preencha no `.env`:
   ```env
   GOOGLE_CLIENT_ID=xxxxxxxx.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=xxxxxxxx
   GOOGLE_REDIRECT_URI=http://localhost:8010/google-drive/oauth2callback/
   ```
5. Reinicie o container web (`docker compose restart web`) e acesse **Configurações** no sistema → **Conectar ao Google Drive**. Você será redirecionado à tela de consentimento do Google; aprove o acesso com a conta do cliente.

O sistema solicita apenas os escopos mínimos necessários (`drive.file` — acesso só aos arquivos que o próprio app cria — e `spreadsheets`), seguindo o princípio do menor privilégio.

> Enquanto o app estiver em modo de teste na tela de consentimento OAuth, apenas contas Google cadastradas como "usuários de teste" no Google Cloud Console conseguirão concluir o login.

---

## 10. Configurar a pasta raiz do Drive

1. No Google Drive da conta do cliente, crie uma pasta chamada, por exemplo, **"Sistema Escolar"**.
2. Abra a pasta e copie o ID da URL: `https://drive.google.com/drive/folders/`**`ESTE_TRECHO_É_O_ID`**.
3. Preencha no `.env`:
   ```env
   GOOGLE_DRIVE_ROOT_FOLDER_ID=1AbCdEfGhIjKlMnOpQrStUvWxYz
   ```

A partir daí, o sistema cria automaticamente as subpastas `Alunos`, `Turmas` e `Relatórios` dentro dessa pasta raiz, na primeira vez que forem necessárias.

---

## 11. Migrations

```bash
docker compose exec web python manage.py makemigrations   # ao alterar modelos
docker compose exec web python manage.py migrate
```

A migration `apps/grades/migrations/0002_seed_default_subjects.py` já popula cinco matérias padrão (Matemática, Português, História, Geografia, Ciências) para a demonstração.

---

## 12. Superusuário

```bash
docker compose exec web python manage.py createsuperuser
```

O superusuário acessa tanto o sistema (`/`) quanto o Django Admin (`/admin/`).

---

## 13. Testes

```bash
docker compose run --rm web pytest
docker compose run --rm web pytest --cov=apps
```

A suíte inteira (mais de 100 testes, ~97% de cobertura em `apps/`) **não depende de nenhuma credencial Google real** — todas as chamadas à API do Drive/Sheets são mockadas com `pytest-mock`/`unittest.mock`, incluindo simulações de erros HTTP (401, 403, 404, 429, 5xx) e timeout. Isso cobre: CRUD de alunos e turmas, criação idempotente de pastas, upload com sucesso e com falha, limpeza de arquivo órfão quando o banco falha após o upload no Drive ter funcionado, criação/reuso de planilha de notas, e os fluxos de conexão/erro do OAuth.

---

## 14. Como funciona o upload

```mermaid
sequenceDiagram
    participant U as Usuário
    participant D as Django (view)
    participant V as Validação
    participant G as Google Drive API
    participant B as Banco de dados

    U->>D: Envia arquivo (multipart, via HTMX)
    D->>V: Valida extensão, tamanho e mimetype real
    alt Validação falha
        V-->>U: Erro amigável, nada é enviado
    else Validação ok
        D->>G: upload_file(...)
        alt Google Drive falha
            G-->>D: erro (rede, permissão, timeout...)
            D-->>U: "Não foi possível enviar o arquivo. Nenhum registro foi criado."
        else Upload no Drive concluído
            D->>B: cria Document (file_id, folder_id, url)
            alt Banco falha ao salvar
                D->>G: delete_file(...) — limpeza best-effort
                D-->>U: erro amigável (arquivo órfão é logado como CRITICAL para reconciliação manual)
            else Banco salva com sucesso
                D-->>U: arquivo aparece na lista, com link "Abrir no Google Drive"
            end
        end
    end
```

O arquivo enviado **nunca é gravado em disco de forma persistente**: o Django mantém o upload em memória (`InMemoryUploadedFile`) ou em um arquivo temporário do sistema operacional (`TemporaryUploadedFile`, para uploads maiores que 2.5 MB), que é automaticamente removido ao final do request — em nenhum momento o conteúdo é copiado para um `MEDIA_ROOT` do servidor.

**Estratégia de consistência** ("Drive primeiro, banco depois"): o registro `Document` só é criado **depois** que o Google Drive confirma o upload. Se o Drive falhar, nada é gravado no banco. Se o Drive funcionar mas o `INSERT` no banco falhar (situação rara), o sistema tenta apagar o arquivo recém-criado no Drive (cleanup best-effort); se essa limpeza também falhar, um log `CRITICAL` registra o `file_id` órfão para reconciliação manual. Essa ordem foi escolhida deliberadamente: um arquivo órfão no Drive é invisível e inofensivo (não aparece em lugar nenhum da interface), enquanto um registro `Document` sem arquivo correspondente no Drive quebraria a própria promessa central do produto — mostrar ao cliente que ele tem acesso real aos arquivos.

---

## 15. Como funciona a organização dos arquivos

Dentro da pasta raiz (`GOOGLE_DRIVE_ROOT_FOLDER_ID`), a estrutura é criada automaticamente:

```text
Sistema Escolar
├── Alunos
│   └── {Nome do aluno} - {Matrícula}
│       ├── Documentos
│       ├── Fotos
│       └── Outros
├── Turmas
│   └── {Nome da turma}          ← contém a planilha "Notas - {Turma}"
└── Relatórios
```

A criação é **idempotente**: `FolderStructureService` primeiro consulta um cache local (`GoogleDriveFolder`, que guarda o `folder_id` de cada pasta lógica) e, na ausência de cache, pergunta à própria API do Drive se a pasta já existe por nome dentro do pai antes de criar uma nova — isso evita pastas duplicadas mesmo que o cache local seja perdido (ex.: reset do banco em ambiente de demonstração).

As pastas do aluno e da turma são criadas automaticamente logo após o cadastro (via signal `post_save`, disparado depois do commit da transação). Se a criação falhar (Drive indisponível, por exemplo), o cadastro do aluno/turma **não é revertido** — apenas fica com a estrutura de pastas pendente, sem travar o uso do sistema.

---

## 16. Como funciona o Google Sheets

Na tela **Notas → {Turma}**, os professores lançam notas em uma matriz Aluno × Matéria (cada célula salva direto no banco local ao perder o foco, via HTMX). A sincronização com o Google Sheets **é uma ação explícita** — botão "Sincronizar com Google Sheets" — e não acontece a cada nota digitada, para manter o fluxo simples e evitar exceder cotas da API.

Ao sincronizar:

1. Garante que a pasta da turma existe no Drive.
2. Se ainda não existe uma planilha para a turma, cria uma via Sheets API (`Notas - {Turma}`) e a move para dentro da pasta da turma (a API do Sheets sempre cria a planilha na raiz do Drive; o sistema a reposiciona em seguida via Drive API).
3. Se a planilha já existe, ela é **reaproveitada** — nunca duplicada.
4. Sobrescreve a aba principal com a matriz atual de notas.

O `google_sheet_id` e a `google_drive_url` ficam salvos no modelo `GoogleSheet`, vinculado 1:1 à turma.

---

## 17. Segurança

- **Segredos apenas em `.env`**, nunca hardcoded. `.env`, `credentials.json`, `token.json`, `*.pem`, `*.key` estão no `.gitignore`.
- **Tokens OAuth cifrados em repouso**: `access_token` e `refresh_token` de `GoogleCredential` são armazenados com criptografia Fernet (`FIELD_ENCRYPTION_KEY`), nunca em texto plano no banco.
- **Autenticação obrigatória** em todas as views de domínio (`LoginRequiredMixin`); CSRF ativo em todos os formulários e requisições HTMX.
- **Validação de upload**: whitelist de extensões, inspeção do **conteúdo binário real** do arquivo via `python-magic` (nunca confia apenas no `Content-Type` enviado pelo navegador), limite de tamanho configurável.
- **Sanitização de nomes de arquivo**: remove sequências de path traversal e caracteres de controle antes de exibir/enviar o nome.
- **Escopo OAuth mínimo**: `drive.file` (o app só acessa arquivos que ele mesmo cria) em vez do escopo completo do Drive.
- **Erros da API do Google nunca vazam stack trace ao usuário** — toda exceção do SDK é traduzida para uma hierarquia de exceções de domínio (`apps/google_drive/exceptions.py`) com mensagens amigáveis em português; o detalhe técnico vai só para o log.

Gere valores próprios antes de qualquer uso real (nunca reutilize os do `.env.example`):

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

**Limitação conhecida do MVP**: a conexão ao Google Drive é um singleton (uma única conta Google por instalação) e não há RBAC — qualquer usuário autenticado do sistema vê todos os dados. Ambas são simplificações conscientes de escopo para a demonstração (ver seção 18).

---

## 18. Evoluindo para produção

Este MVP prioriza clareza e simplicidade para uma demonstração comercial. Para evoluir para um ambiente de produção real, considere:

- **Upload assíncrono**: hoje o upload é síncrono dentro do request/response (aceitável para o volume de uma demo). Em produção, mover para uma fila (Celery + Redis) evita bloquear workers em uploads grandes ou Drive lento.
- **Multi-conta Google**: hoje `GoogleCredential` é um singleton (uma conta Drive por instalação). Um SaaS multi-cliente precisaria de uma credencial por tenant/escola.
- **RBAC**: perfis diferenciados (secretaria, professor, coordenação, responsável) em vez do modelo atual "todo usuário autenticado vê tudo".
- **Build de produção do Tailwind**: a interface usa o Tailwind via CDN (`cdn.tailwindcss.com`) para eliminar a dependência de Node.js neste MVP. Antes de produção, trocar por um build compilado (Tailwind CLI ou `django-tailwind`), servido via Whitenoise/CDN próprio.
- **Rate limiting** nas views de upload e nos endpoints de autenticação.
- **Backup/observabilidade**: métricas de erro da API do Google (taxa de falhas, latência), alertas para o log `CRITICAL` de arquivos órfãos, backups do PostgreSQL.
- **HTTPS obrigatório**: `config/settings/production.py` já ativa `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE` e `CSRF_COOKIE_SECURE` — falta apenas o certificado/proxy reverso na infraestrutura de deploy.
- **Verificação do app OAuth pelo Google**: para uso além da lista de testadores, o app OAuth precisa passar pelo processo de verificação do Google (necessário para escopos sensíveis em produção com usuários externos).
