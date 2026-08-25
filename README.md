# MC Alito Mucavel — Site Portfólio & Sistema de Reservas

Projeto completo para o **Alito Mucavel**, Mestre de Cerimónias em Moçambique:
site de portfólio com formulário de reserva, e painel administrativo para
gerir os pedidos pelo telemóvel.

Contacto configurado: **+258 87 605 0602** (WhatsApp).

## Estrutura

```
alito-mucavel-mc/
├── backend/          # API FastAPI (Python)
│   ├── app/
│   │   ├── main.py, config.py, database.py, models.py, auth.py
│   │   ├── schemas/  (package, media, lead, availability)
│   │   └── routers/  (packages, gallery, leads, availability)
│   ├── requirements.txt
│   └── .env.example
└── frontend/          # Site público + painel admin (HTML/JS puro)
    ├── index.html      # Site do cliente (portfólio + formulário de reserva)
    ├── app.js
    ├── admin.html       # Painel administrativo (uso do próprio Alito)
    └── admin.js
```

- **Secção de pacotes redesenhada** (formato "deslizar", como a galeria):
  o cliente escolhe a categoria (Casamento, Corporativo, etc.) em separadores
  deslizáveis; por baixo aparece uma pequena descrição/motivação da
  categoria, e os pacotes dessa categoria em cartões deslizáveis com o
  **texto completo** (descrição inteira + todas as características) — sem
  resumos. Editável em dois sítios do admin:
  - "Descrição de cada tipo de evento" — o texto de motivação por categoria.
  - "Pacotes e preços" — cada pacote agora expande (toque para abrir) e
    mostra a descrição e as características por inteiro, exatamente como
    aparecem no site do cliente.

## Novidades desta versão

- **Perfil do MC**: círculo com foto (ou iniciais) + nome no canto superior
  esquerdo do site. Ao clicar, abre um modal com nome completo, localização
  e biografia. Editado pelo Alito no painel admin (`admin.html` → secção
  "O seu perfil") — incluindo o link da foto, já que este projeto não inclui
  um servidor de upload de imagens: o Alito cola o link de uma foto já
  publicada (Google Drive, Imgur, etc.).
- **Número de WhatsApp editável no admin**: deixou de estar fixo no `.env`.
  Agora vive no perfil (base de dados) e é editável na mesma secção "O seu
  perfil" — o Alito pode trocar de número sem precisar de mexer no Render.
- **Pacotes por tipo de evento**: cada `Package` está ligado a um
  `event_type` (Casamento, Corporativo, Graduação, Aniversário, Xitique,
  Outro). Casamento tem dois pacotes (Diamante e Ouro); os restantes
  eventos têm um pacote simples cada. Todos geridos no painel admin,
  secção "Pacotes e preços" (criar, editar preço/descrição, ativar/
  desativar, remover) — **sem precisar de tocar em código**.
- **Galeria com gestão completa no admin**: antes só existia leitura;
  agora o Alito adiciona/remove fotos e vídeos diretamente no painel,
  secção "Galeria", colando o link de onde já estão publicados.
- **`backend/scripts/seed_packages.py`**: script de arranque único, que
  insere os 7 pacotes iniciais (2 de Casamento + 1 por cada outro evento)
  com **preços placeholder** — claramente marcados no código como valores
  de exemplo. Corre-se uma vez (ver secção abaixo); depois disso, todas as
  alterações de preço/conteúdo são feitas no admin, nunca mais precisando
  deste script.

### O que ainda precisa de acesso ao código/Render (por segurança, não por limitação)

- `DATABASE_URL` e `ADMIN_TOKEN` — são credenciais de infraestrutura,
  ficam nas variáveis de ambiente do Render por segurança (não deve ser
  possível a alguém trocar a palavra-passe do admin a partir do próprio
  painel admin sem confirmação da password antiga — isso não foi implementado
  nesta versão). Tudo o resto (perfil, WhatsApp, pacotes, preços,
  galeria, leads, agenda) é 100% editável pelo painel, sem tocar em código.

## Upload de fotos/vídeos direto do telemóvel (Cloudinary)

O botão "Escolher do telemóvel/galeria" (perfil e galeria) precisa de uma
conta grátis no Cloudinary para funcionar — sem isto configurado, continua
a dar para colar o link manualmente, mas não para enviar o ficheiro
diretamente.

**Porquê um serviço externo:** o Render não guarda ficheiros de forma
permanente (o servidor reinicia e perde tudo). O Cloudinary guarda a foto/
vídeo de forma estável e devolve-nos só o link — o resto do sistema
continua igual.

**Configurar (5 minutos, sem cartão de crédito):**
1. Criar conta grátis em https://cloudinary.com/users/register/free
2. No Dashboard, copiar o **Cloud name**.
3. Ir a **Settings → Upload → Upload presets → Add upload preset**.
   Pôr **Signing Mode** como **Unsigned**, guardar, e copiar o **nome do preset**.
4. Abrir `frontend/admin.html`, encontrar o bloco `CLOUDINARY_CLOUD_NAME`
   perto do topo, e preencher os dois valores:
   ```html
   <script>
     window.CLOUDINARY_CLOUD_NAME = "dxyz1234";
     window.CLOUDINARY_UPLOAD_PRESET = "mc_alito_uploads";
     window.MAX_VIDEO_SECONDS = 60;
   </script>
   ```
5. Pronto — não precisa de nenhuma outra alteração de código.

O limite de duração dos vídeos (`MAX_VIDEO_SECONDS`) é verificado no
telemóvel antes de o vídeo sequer começar a enviar-se (poupa dados).

## Testar sem o token do admin (fase de testes)

Enquanto ainda estás a testar (antes de dares o link ao Alito ou publicares),
podes desligar a exigência do token sem tocar em código:

No `backend/.env`:
```
ADMIN_AUTH_ENABLED=false
```

Com isto, o `admin.html` deixa entrar com qualquer coisa escrita no campo do
token (ou até vazio, se ajustares o formulário). Assim que acabares de
testar, **volta a pôr `ADMIN_AUTH_ENABLED=true`** (ou remove a linha —
o padrão já é `true`) antes de publicares o site, senão qualquer pessoa
consegue ver os pedidos dos clientes e mudar preços sem precisar de token.

## Como correr o script de seed (uma única vez)

```bash
cd backend
source venv/bin/activate
python -m scripts.seed_packages
```

Isto insere os pacotes com preços placeholder. Depois, entra no painel
admin (`admin.html` → "Pacotes e preços") e corrige os valores reais.

## Como as três partes se encaixam

1. **`backend/`** — expõe a API que tanto o site público como o painel admin consomem.
2. **`frontend/index.html`** — o cliente vê pacotes e galeria (via API pública),
   preenche o formulário, e é redirecionado automaticamente para o WhatsApp
   do Alito com a mensagem já preenchida.
3. **`frontend/admin.html`** — o Alito entra com um token, vê os pedidos
   recebidos, muda o estado (pendente → contactado → confirmado) e gere
   datas em que já não está disponível.

## Pôr a correr localmente

### 1. Backend
```bash
cd backend
pip install -r requirements.txt --break-system-packages   # ou usar venv
cp .env.example .env
# editar .env: DATABASE_URL (Supabase/Neon), ADMIN_TOKEN
uvicorn app.main:app --reload
```
A API fica em `http://localhost:8000`. Documentação automática em `/docs`.

### 2. Frontend
Os ficheiros `index.html` e `admin.html` são estáticos — basta abrir num
browser ou servir com qualquer servidor estático:
```bash
cd frontend
python3 -m http.server 5500
```
Por defeito, `app.js` e `admin.js` apontam para `http://localhost:8000/api/v1`.
Antes de publicar, define o domínio real da API no topo da página, por exemplo:
```html
<script>window.MC_API_BASE_URL = "https://api.alitomucavel.co.mz/api/v1";</script>
<script src="app.js"></script>
```

## Antes de publicar (checklist)

- [ ] Trocar `DATABASE_URL` para a instância real (Supabase ou Neon).
- [ ] Trocar `ADMIN_TOKEN` por um valor forte (`openssl rand -hex 32`), e
      guardá-lo só com o Alito — é a "palavra-passe" do painel admin.
- [ ] Substituir a foto de fundo do hero em `index.html` (secção `<!-- Fundo -->`)
      por uma foto real do Alito em palco.
- [ ] Carregar pacotes reais na base de dados (o endpoint `POST /packages`
      não está exposto publicamente propositadamente — inserir via `/docs`
      autenticado, script, ou pequeno seed inicial).
- [ ] Confirmar o número de WhatsApp em `backend/.env` (`WHATSAPP_NUMBER`)
      — já configurado como `258876050602`.
- [ ] Restringir `CORS_ORIGINS` no `.env` ao domínio real do site (em vez de `["*"]`).

## Nota sobre o nome/marca

Usei **"Alito Mucavel"** como identidade principal no hero e no rodapé, e
**"MC Alito Mucavel"** no separador do browser e no cabeçalho de navegação
(onde a sigla funciona como selo de marca). Isto evita repetir "MC" a mais
no meio do texto, mas é uma escolha de gosto — se preferires "MC" sempre
junto ao nome, é só pesquisar/substituir "Alito Mucavel" por
"MC Alito Mucavel" nos três ficheiros HTML.

## Tipos de evento configurados

Casamento · Corporativo · Graduação · Aniversário · Xitique · Outro
(campo `event_type` é texto livre na API — a lista no formulário é apenas
a lista de sugestões mostrada ao cliente, podes adicionar mais em
`frontend/index.html`, dentro do `<select id="event_type">`).
