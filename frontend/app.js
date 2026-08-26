/**
 * app.js — Lógica do site do MC.
 * Consome a API FastAPI: /profile, /packages (filtrável por event_type),
 * /gallery, /leads. Sem frameworks — vanilla JS para manter o site leve.
 */
(() => {
  'use strict';

  // Ajustar para o domínio real da API em produção (ex: https://api.seudominio.co.mz)
  const API_BASE_URL = window.MC_API_BASE_URL || 'http://localhost:8000/api/v1';

  const galleryRow = document.getElementById('gallery-row');
  const categoryTabs = document.getElementById('category-tabs');
  const categoryTagline = document.getElementById('category-tagline');
  const packagesRow = document.getElementById('packages-row');
  const eventTypeSelect = document.getElementById('event_type');
  const packageSelect = document.getElementById('package_id');
  const priceDisplay = document.getElementById('price-display');
  const form = document.getElementById('booking-form');
  const submitBtn = document.getElementById('submit-btn');
  const errorEl = document.getElementById('form-error');

  const profileTrigger = document.getElementById('profile-trigger');
  const profileModal = document.getElementById('profile-modal');
  const profileBackdrop = document.getElementById('profile-backdrop');
  const profileClose = document.getElementById('profile-close');
  const profileAvatar = document.getElementById('profile-avatar');
  const profileAvatarLgBtn = document.getElementById('profile-avatar-lg-btn');
  const profileAvatarLg = document.getElementById('profile-avatar-lg');
  const profileModalName = document.getElementById('profile-modal-name');
  const profileModalLocation = document.getElementById('profile-modal-location');
  const profileModalWhatsapp = document.getElementById('profile-modal-whatsapp');
  const profileModalBio = document.getElementById('profile-modal-bio');

  /** Cache local dos pacotes do tipo de evento atualmente selecionado, por id. */
  let currentEventPackages = {};

  const formatMT = (value) =>
    new Intl.NumberFormat('pt-MZ', { minimumFractionDigits: 0 }).format(value) + ' MT';

  /**
   * Extrai uma mensagem de erro legível da resposta da API — que tanto pode
   * vir como texto simples (as nossas exceções) como uma lista de erros de
   * validação do Pydantic (ex: campo em falta ou mal formatado).
   */
  function extractErrorMessage(payload, fallback) {
    const detail = payload?.detail;
    if (!detail) return fallback;
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail)) {
      return detail
        .map((e) => e.msg || JSON.stringify(e))
        .join(' | ');
    }
    return fallback;
  }

  const initials = (name) =>
    name
      .split(' ')
      .filter(Boolean)
      .slice(0, 2)
      .map((w) => w[0].toUpperCase())
      .join('');

  function showError(message) {
    errorEl.textContent = message;
    errorEl.classList.remove('hidden');
  }

  function clearError() {
    errorEl.classList.add('hidden');
    errorEl.textContent = '';
  }

  // ---------------------------------------------------------------------
  // Perfil — GET /profile + modal "Sobre o MC"
  // ---------------------------------------------------------------------
  async function loadProfile() {
    try {
      const res = await fetch(`${API_BASE_URL}/profile`);
      if (!res.ok) throw new Error('Falha ao carregar perfil');
      const profile = await res.json();

      const avatarContent = profile.photo_url
        ? `<img src="${profile.photo_url}" alt="${profile.full_name}" class="w-full h-full object-cover">`
        : initials(profile.full_name || 'MC');

      profileAvatar.innerHTML = avatarContent;
      profileAvatarLg.innerHTML = avatarContent;
      profileAvatarLgBtn.dataset.photoUrl = profile.photo_url || '';
      profileModalName.textContent = profile.full_name || '—';
      profileModalLocation.textContent = profile.location || '—';
      profileModalBio.textContent = profile.bio || 'Em breve, mais sobre o meu percurso por aqui.';

      if (profile.whatsapp_number) {
        const digits = profile.whatsapp_number.replace(/\D/g, '');
        profileModalWhatsapp.href = `https://wa.me/${digits}`;
        profileModalWhatsapp.textContent = `📞 ${profile.whatsapp_number}`;
        profileModalWhatsapp.classList.remove('hidden');
      } else {
        profileModalWhatsapp.classList.add('hidden');
      }
    } catch (err) {
      console.error(err);
      profileAvatar.textContent = 'MC';
      profileAvatarLg.textContent = 'MC';
    }
  }

  profileAvatarLgBtn.addEventListener('click', () => {
    const url = profileAvatarLgBtn.dataset.photoUrl;
    if (!url) return; // sem foto carregada, não há nada para abrir
    closeProfileModal();
    openLightbox(url, 'image', profileModalName.textContent);
  });

  function openProfileModal() {
    profileModal.classList.remove('hidden');
    document.body.style.overflow = 'hidden';
  }

  function closeProfileModal() {
    profileModal.classList.add('hidden');
    document.body.style.overflow = '';
  }

  profileTrigger.addEventListener('click', openProfileModal);
  profileClose.addEventListener('click', closeProfileModal);
  profileBackdrop.addEventListener('click', closeProfileModal);
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeProfileModal();
  });

  // ---------------------------------------------------------------------
  // Galeria — GET /gallery
  // ---------------------------------------------------------------------
  async function loadGallery() {
    try {
      const res = await fetch(`${API_BASE_URL}/gallery`);
      if (!res.ok) throw new Error('Falha ao carregar galeria');
      const items = await res.json();

      if (!items.length) {
        galleryRow.innerHTML = `<p class="text-muted text-sm px-1">Galeria em atualização — volte em breve.</p>`;
        return;
      }

      galleryRow.innerHTML = items
        .map((item) => {
          const isVideo = item.type === 'video';
          const cover = item.thumbnail_url || item.url;
          return `
            <button type="button" data-url="${item.url}" data-type="${item.type}" data-title="${item.title}"
               class="gallery-item snap-item shrink-0 w-[78vw] sm:w-72 aspect-[4/5] rounded-xl overflow-hidden relative bg-elev group text-left">
              <img src="${cover}" alt="${item.title}" loading="lazy"
                   class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500">
              <div class="absolute inset-0 bg-gradient-to-t from-bg/90 via-transparent to-transparent"></div>
              ${isVideo ? '<span class="absolute top-3 right-3 text-[10px] uppercase tracking-widest bg-gold text-bg px-2 py-1 rounded-full">Vídeo</span>' : ''}
              <span class="absolute bottom-3 left-3 right-3 text-sm font-medium">${item.title}</span>
            </button>`;
        })
        .join('');

      galleryRow.querySelectorAll('.gallery-item').forEach((btn) => {
        btn.addEventListener('click', () => openLightbox(btn.dataset.url, btn.dataset.type, btn.dataset.title));
      });
    } catch (err) {
      console.error(err);
      galleryRow.innerHTML = `<p class="text-muted text-sm px-1">Não foi possível carregar a galeria neste momento.</p>`;
    }
  }

  // ---------------------------------------------------------------------
  // Lightbox — mostra a foto/vídeo dentro do site, sem redirecionar para
  // o domínio onde o ficheiro está hospedado (o cliente nunca vê isso)
  // ---------------------------------------------------------------------
  const lightboxModal = document.getElementById('lightbox-modal');
  const lightboxContent = document.getElementById('lightbox-content');
  const lightboxClose = document.getElementById('lightbox-close');

  function openLightbox(url, type, title) {
    lightboxContent.innerHTML =
      type === 'video'
        ? `<video src="${url}" controls autoplay playsinline class="max-w-full max-h-[90svh] rounded-lg"></video>`
        : `<img src="${url}" alt="${title}" class="max-w-full max-h-[90svh] rounded-lg object-contain">`;
    lightboxModal.classList.remove('hidden');
    document.body.style.overflow = 'hidden';
  }

  function closeLightbox() {
    lightboxModal.classList.add('hidden');
    lightboxContent.innerHTML = ''; // pára o vídeo, se estiver a tocar
    document.body.style.overflow = '';
  }

  lightboxClose.addEventListener('click', closeLightbox);
  lightboxModal.addEventListener('click', (e) => {
    if (e.target === lightboxModal) closeLightbox();
  });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeLightbox();
  });

  // ---------------------------------------------------------------------
  // Pacotes — categorias deslizáveis + pacotes deslizáveis com texto completo
  // ---------------------------------------------------------------------
  let packagesByEventType = {}; // { "Casamento": [pkg, pkg], "Xitique": [pkg] }
  let taglinesByEventType = {}; // { "Casamento": "..." }
  let currentCategory = null;

  // Ordem fixa em que as categorias aparecem no site (independente da ordem
  // de inserção na base de dados). Tipos fora desta lista aparecem no fim.
  const CATEGORY_ORDER = ['Aniversário', 'Casamento', 'Corporativo', 'Graduação', 'Xitique', 'Outro'];

  function sortByCategoryOrder(types) {
    return [...types].sort((a, b) => {
      const ia = CATEGORY_ORDER.indexOf(a);
      const ib = CATEGORY_ORDER.indexOf(b);
      return (ia === -1 ? 999 : ia) - (ib === -1 ? 999 : ib);
    });
  }

  async function loadPackagesOverview() {
    try {
      const [packagesRes, taglinesRes] = await Promise.all([
        fetch(`${API_BASE_URL}/packages`),
        fetch(`${API_BASE_URL}/event-info`),
      ]);
      if (!packagesRes.ok) throw new Error('Falha ao carregar pacotes');

      const packages = await packagesRes.json();
      const taglines = taglinesRes.ok ? await taglinesRes.json() : [];
      taglinesByEventType = Object.fromEntries(taglines.map((t) => [t.event_type, t.tagline]));

      if (!packages.length) {
        categoryTabs.innerHTML = '';
        packagesRow.innerHTML = `<p class="text-muted text-sm px-1">Pacotes em atualização — contacte-nos diretamente.</p>`;
        return;
      }

      // Agrupar por tipo de evento, depois ordenar pela sequência fixa
      packagesByEventType = {};
      const seenTypes = [];
      for (const pkg of packages) {
        if (!(pkg.event_type in packagesByEventType)) {
          packagesByEventType[pkg.event_type] = [];
          seenTypes.push(pkg.event_type);
        }
        packagesByEventType[pkg.event_type].push(pkg);
      }
      const orderedTypes = sortByCategoryOrder(seenTypes);

      // Separadores de categoria
      // Mantém a categoria que o cliente já estava a ver (importante porque
      // esta função corre também automaticamente a cada 3s).
      const targetType = currentCategory && orderedTypes.includes(currentCategory)
        ? currentCategory
        : orderedTypes[0];

      categoryTabs.innerHTML = orderedTypes
        .map(
          (type) =>
            `<button data-type="${type}" class="cat-tab snap-item ${type === targetType ? 'cat-tab-active' : ''}">${type}</button>`
        )
        .join('');

      categoryTabs.querySelectorAll('.cat-tab').forEach((btn) => {
        btn.addEventListener('click', () => selectCategory(btn.dataset.type));
      });

      selectCategory(targetType);
    } catch (err) {
      console.error(err);
      packagesRow.innerHTML = `<p class="text-muted text-sm px-1">Não foi possível carregar os pacotes neste momento.</p>`;
    }
  }

  function selectCategory(eventType) {
    const categoryChanged = currentCategory !== eventType;
    currentCategory = eventType;

    categoryTabs.querySelectorAll('.cat-tab').forEach((btn) => {
      btn.classList.toggle('cat-tab-active', btn.dataset.type === eventType);
    });

    categoryTagline.textContent = taglinesByEventType[eventType] || '';
    categoryTagline.classList.toggle('hidden', !taglinesByEventType[eventType]);

    const items = packagesByEventType[eventType] || [];
    packagesRow.innerHTML = items
      .map(
        (pkg) => `
        <article class="snap-item shrink-0 w-[88vw] sm:w-[500px] rounded-xl p-6 border border-gold/40 bg-elev flex flex-col">
          <h4 class="font-display italic text-xl mb-2">${pkg.name}</h4>
          <p class="text-ink/85 text-sm leading-relaxed mb-4 whitespace-pre-line">${pkg.description}</p>
          <p class="font-display text-2xl text-goldsoft mb-4">${formatMT(pkg.base_price)}</p>
          <ul class="text-sm space-y-2.5 mb-6 flex-1">
            ${(pkg.features || [])
              .map((f) => `<li class="flex gap-2"><span class="text-gold shrink-0">·</span><span>${f}</span></li>`)
              .join('')}
          </ul>
          <a href="#reserva" data-event-type="${pkg.event_type}" data-package-id="${pkg.id}"
             class="package-select-link text-center border border-ink/25 rounded-lg px-4 py-2.5 text-sm hover:bg-gold hover:text-bg hover:border-gold transition-colors">
            Escolher este pacote
          </a>
        </article>`
      )
      .join('');

    packagesRow.querySelectorAll('.package-select-link').forEach((link) => {
      link.addEventListener('click', async () => {
        eventTypeSelect.value = link.dataset.eventType;
        await loadPackagesForEventType(link.dataset.eventType);
        packageSelect.value = link.dataset.packageId;
        updatePriceDisplay();
      });
    });

    // Volta ao início do carrossel só quando a categoria muda de facto
    // (evita saltos indesejados durante a atualização automática a cada 3s).
    if (categoryChanged) {
      packagesRow.scrollTo({ left: 0, behavior: 'instant' in window ? 'instant' : 'auto' });
    }
  }

  // ---------------------------------------------------------------------
  // Pacotes — carregamento dinâmico no formulário, conforme o evento escolhido
  // ---------------------------------------------------------------------
  async function loadPackagesForEventType(eventType) {
    currentEventPackages = {};
    priceDisplay.textContent = '—';

    if (!eventType) {
      packageSelect.disabled = true;
      packageSelect.innerHTML = `<option value="">Escolha primeiro o tipo de evento</option>`;
      return;
    }

    packageSelect.disabled = true;
    packageSelect.innerHTML = `<option value="">A carregar pacotes…</option>`;

    try {
      const res = await fetch(`${API_BASE_URL}/packages?event_type=${encodeURIComponent(eventType)}`);
      if (!res.ok) throw new Error('Falha ao carregar pacotes');
      const packages = await res.json();

      currentEventPackages = Object.fromEntries(packages.map((p) => [p.id, p]));

      if (!packages.length) {
        packageSelect.innerHTML = `<option value="">Sem pacotes disponíveis para este evento</option>`;
        return;
      }

      packageSelect.innerHTML =
        (packages.length > 1 ? `<option value="">Selecione…</option>` : '') +
        packages
          .map(
            (pkg, i) =>
              `<option value="${pkg.id}" ${packages.length === 1 ? 'selected' : ''}>${pkg.name} — ${formatMT(pkg.base_price)}</option>`
          )
          .join('');

      packageSelect.disabled = false;
      updatePriceDisplay();
    } catch (err) {
      console.error(err);
      packageSelect.innerHTML = `<option value="">Erro ao carregar pacotes</option>`;
    }
  }

  eventTypeSelect.addEventListener('change', () => loadPackagesForEventType(eventTypeSelect.value));
  packageSelect.addEventListener('change', updatePriceDisplay);

  function updatePriceDisplay() {
    const pkg = currentEventPackages[packageSelect.value];
    priceDisplay.textContent = pkg ? formatMT(pkg.base_price) : '—';
  }

  // ---------------------------------------------------------------------
  // Submissão do formulário — POST /leads → GET /leads/whatsapp-link/{id}
  // ---------------------------------------------------------------------
  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    clearError();

    const pkg = currentEventPackages[packageSelect.value];
    if (!pkg) {
      showError('Por favor selecione o tipo de evento e o pacote.');
      return;
    }

    const payload = {
      client_name: document.getElementById('client_name').value.trim(),
      client_phone: document.getElementById('client_phone').value.trim(),
      event_date: document.getElementById('event_date').value,
      event_type: eventTypeSelect.value,
      selected_package_id: packageSelect.value,
      estimated_price: pkg.base_price,
    };

    if (!payload.client_name || !payload.client_phone || !payload.event_date || !payload.event_type) {
      showError('Por favor preencha todos os campos.');
      return;
    }

    submitBtn.disabled = true;
    submitBtn.textContent = 'A processar…';

    try {
      const createRes = await fetch(`${API_BASE_URL}/leads`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!createRes.ok) {
        const detail = await createRes.json().catch(() => null);
        throw new Error(extractErrorMessage(detail, 'Não foi possível submeter o pedido.'));
      }

      const lead = await createRes.json();

      const linkRes = await fetch(`${API_BASE_URL}/leads/whatsapp-link/${lead.id}`);
      if (!linkRes.ok) throw new Error('Pedido gravado, mas falhou ao gerar o link do WhatsApp.');

      const { whatsapp_link } = await linkRes.json();

      // Abre o WhatsApp numa nova janela/app em vez de navegar a página atual —
      // em telemóvel isto evita que o botão fique "preso" em 'A processar…'
      // quando o telemóvel troca para a app do WhatsApp.
      window.open(whatsapp_link, '_blank');

      submitBtn.textContent = 'Pedido enviado ✓';
      showError('');
      form.reset();
      priceDisplay.textContent = '—';
      packageSelect.innerHTML = '<option value="">Escolha primeiro o tipo de evento</option>';
      packageSelect.disabled = true;

      // Repõe o botão ao fim de alguns segundos, para permitir um novo pedido.
      setTimeout(() => {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Continuar no WhatsApp';
      }, 4000);
    } catch (err) {
      console.error(err);
      showError(err.message || 'Ocorreu um erro. Tente novamente.');
      submitBtn.disabled = false;
      submitBtn.textContent = 'Continuar no WhatsApp';
    }
  });

  // ---------------------------------------------------------------------
  // Data mínima do input = hoje
  // ---------------------------------------------------------------------
  document.getElementById('event_date').min = new Date().toISOString().split('T')[0];

  // ---------------------------------------------------------------------
  // Init
  // ---------------------------------------------------------------------
  loadProfile();
  loadGallery();
  loadPackagesOverview();

  // Atualiza galeria e pacotes a cada 3s, para o cliente ver alterações
  // feitas pelo Alito no painel admin sem precisar de dar refresh manual.
  setInterval(() => {
    if (!document.hidden) {
      loadGallery();
      loadPackagesOverview();
    }
  }, 3000);
})();
