/**
 * admin.js — Painel administrativo do MC.
 * Consome os endpoints protegidos por Bearer Token (Prompt 3):
 *   GET   /api/v1/leads?status=...
 *   PATCH /api/v1/leads/{id}
 *   GET   /api/v1/leads/whatsapp-link/{id}
 *   GET/POST/DELETE /api/v1/availability
 *
 * O token é mantido apenas em memória (variável JS) — não é gravado em
 * localStorage/sessionStorage, por isso é pedido de novo a cada sessão.
 */
(() => {
  'use strict';

  const API_BASE_URL = window.MC_API_BASE_URL || 'http://localhost:8000/api/v1';

  let adminToken = null;
  let currentFilter = '';

  const loginScreen = document.getElementById('login-screen');
  const loginForm = document.getElementById('login-form');
  const loginError = document.getElementById('login-error');
  const tokenInput = document.getElementById('token-input');

  const adminPanel = document.getElementById('admin-panel');
  const logoutBtn = document.getElementById('logout-btn');

  const statusTabs = document.getElementById('status-tabs');
  const leadsList = document.getElementById('leads-list');

  const blockedForm = document.getElementById('blocked-date-form');
  const blockedDateInput = document.getElementById('blocked-date-input');
  const blockedReasonInput = document.getElementById('blocked-reason-input');
  const blockedDatesList = document.getElementById('blocked-dates-list');

  const profileForm = document.getElementById('profile-form');
  const profilePhotoUrlInput = document.getElementById('profile-photo-url');
  const profilePhotoFileInput = document.getElementById('profile-photo-file');
  const profilePhotoPreview = document.getElementById('profile-photo-preview');
  const profilePhotoStatus = document.getElementById('profile-photo-status');
  const profileFullNameInput = document.getElementById('profile-full-name');
  const profileLocationInput = document.getElementById('profile-location');
  const profileWhatsappInput = document.getElementById('profile-whatsapp');
  const profileBioInput = document.getElementById('profile-bio');
  const profileFeedback = document.getElementById('profile-feedback');

  const packageForm = document.getElementById('package-form');
  const packageNameInput = document.getElementById('package-name');
  const packageEventTypeInput = document.getElementById('package-event-type');
  const packageDescriptionInput = document.getElementById('package-description');
  const packagePriceInput = document.getElementById('package-price');
  const packageFeaturesInput = document.getElementById('package-features');
  const packageFeedback = document.getElementById('package-feedback');
  const packagesAdminList = document.getElementById('packages-admin-list');

  const eventInfoList = document.getElementById('event-info-list');

  const mediaForm = document.getElementById('media-form');
  const mediaTitleInput = document.getElementById('media-title');
  const mediaTypeInput = document.getElementById('media-type');
  const mediaFileInput = document.getElementById('media-file');
  const mediaUploadStatus = document.getElementById('media-upload-status');
  const mediaUploadProgressWrap = document.getElementById('media-upload-progress-wrap');
  const mediaUploadProgressBar = document.getElementById('media-upload-progress-bar');
  const mediaUrlInput = document.getElementById('media-url');
  const mediaThumbnailInput = document.getElementById('media-thumbnail');
  const mediaFeedback = document.getElementById('media-feedback');
  const mediaAdminList = document.getElementById('media-admin-list');

  const STATUS_LABELS = { pending: 'Pendente', contacted: 'Contactado', closed: 'Confirmado' };
  const STATUS_COLORS = {
    pending: 'text-goldsoft border-gold/40',
    contacted: 'text-blue-300 border-blue-400/40',
    closed: 'text-green-300 border-green-400/40',
  };

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
      return detail.map((e) => e.msg || JSON.stringify(e)).join(' | ');
    }
    return fallback;
  }

  // ---------------------------------------------------------------------
  // Upload de fotos/vídeos direto do telemóvel (Cloudinary, plano grátis)
  // Configurado em admin.html: window.CLOUDINARY_CLOUD_NAME / UPLOAD_PRESET
  // ---------------------------------------------------------------------
  const CLOUD_NAME = window.CLOUDINARY_CLOUD_NAME || '';
  const UPLOAD_PRESET = window.CLOUDINARY_UPLOAD_PRESET || '';
  const MAX_VIDEO_SECONDS = window.MAX_VIDEO_SECONDS || 60;

  function uploadNotConfigured() {
    return !CLOUD_NAME || !UPLOAD_PRESET;
  }

  /** Lê a duração de um ficheiro de vídeo (em segundos) sem o enviar para lado nenhum. */
  function getVideoDuration(file) {
    return new Promise((resolve, reject) => {
      const video = document.createElement('video');
      video.preload = 'metadata';
      video.onloadedmetadata = () => {
        URL.revokeObjectURL(video.src);
        resolve(video.duration);
      };
      video.onerror = () => {
        URL.revokeObjectURL(video.src);
        reject(new Error('Não foi possível ler este vídeo.'));
      };
      video.src = URL.createObjectURL(file);
    });
  }

  /**
   * Sobe um ficheiro para o Cloudinary com barra de progresso.
   * onProgress(percent) é chamado durante o envio.
   */
  function uploadToCloudinary(file, resourceType, onProgress) {
    return new Promise((resolve, reject) => {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('upload_preset', UPLOAD_PRESET);

      const xhr = new XMLHttpRequest();
      xhr.open('POST', `https://api.cloudinary.com/v1_1/${CLOUD_NAME}/${resourceType}/upload`);

      xhr.upload.onprogress = (e) => {
        if (e.lengthComputable && onProgress) onProgress(Math.round((e.loaded / e.total) * 100));
      };

      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          resolve(JSON.parse(xhr.responseText));
        } else {
          reject(new Error('Falha no envio. Verifique a ligação e tente novamente.'));
        }
      };
      xhr.onerror = () => reject(new Error('Falha no envio. Verifique a ligação e tente novamente.'));
      xhr.send(formData);
    });
  }

  /** Gera o link de miniatura de um vídeo do Cloudinary (primeiro frame). */
  function cloudinaryVideoThumbnail(secureUrl) {
    return secureUrl.replace(/\.(mp4|mov|webm|mkv)$/i, '.jpg');
  }

  const formatDate = (isoDate) => {
    const [y, m, d] = isoDate.split('-');
    return `${d}/${m}/${y}`;
  };

  function authHeaders() {
    return { Authorization: `Bearer ${adminToken}` };
  }

  /** Wrapper de fetch que trata 401 devolvendo ao ecrã de login. */
  async function authedFetch(path, options = {}) {
    const res = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      headers: { ...(options.headers || {}), ...authHeaders() },
    });
    if (res.status === 401) {
      adminToken = null;
      showLogin('Sessão expirada ou token inválido. Entre novamente.');
      throw new Error('unauthorized');
    }
    return res;
  }

  function showLogin(message) {
    adminPanel.classList.add('hidden');
    loginScreen.classList.remove('hidden');
    if (message) {
      loginError.textContent = message;
      loginError.classList.remove('hidden');
    }
  }

  let leadsAutoRefreshTimer = null;

  function showPanel() {
    loginScreen.classList.add('hidden');
    adminPanel.classList.remove('hidden');
    loadProfile();
    loadLeads();
    loadEventInfo();
    loadPackagesAdmin();
    loadMediaAdmin();
    loadBlockedDates();

    // Atualiza a lista de pedidos automaticamente a cada 3s, para o Alito
    // ver novos pedidos sem precisar de dar refresh manual à página.
    if (leadsAutoRefreshTimer) clearInterval(leadsAutoRefreshTimer);
    leadsAutoRefreshTimer = setInterval(() => {
      if (!document.hidden) loadLeads();
    }, 3000);
  }

  // ---------------------------------------------------------------------
  // Login / Logout
  // ---------------------------------------------------------------------
  loginForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    loginError.classList.add('hidden');

    const candidate = tokenInput.value.trim();
    if (!candidate) return;

    // Valida o token com um pedido real ao endpoint protegido.
    adminToken = candidate;
    try {
      const res = await fetch(`${API_BASE_URL}/leads`, { headers: authHeaders() });
      if (res.status === 401) {
        adminToken = null;
        loginError.textContent = 'Token inválido.';
        loginError.classList.remove('hidden');
        return;
      }
      showPanel();
    } catch (err) {
      console.error(err);
      loginError.textContent = 'Não foi possível ligar à API. Verifique a ligação.';
      loginError.classList.remove('hidden');
    }
  });

  logoutBtn.addEventListener('click', () => {
    adminToken = null;
    tokenInput.value = '';
    showLogin();
  });

  // ---------------------------------------------------------------------
  // Leads — listagem, filtros, mudança de estado, WhatsApp
  // ---------------------------------------------------------------------
  statusTabs.addEventListener('click', (event) => {
    const btn = event.target.closest('.tab-btn');
    if (!btn) return;

    statusTabs.querySelectorAll('.tab-btn').forEach((b) => {
      b.classList.remove('tab-active', 'border-gold');
      b.classList.add('border-line');
    });
    btn.classList.add('tab-active', 'border-gold');
    btn.classList.remove('border-line');

    currentFilter = btn.dataset.filter;
    loadLeads();
  });

  async function loadLeads() {
    leadsList.innerHTML = `<div class="h-24 rounded-xl bg-elev animate-pulse"></div>`;
    try {
      const qs = currentFilter ? `?status=${currentFilter}` : '';
      const res = await authedFetch(`/leads${qs}`);
      if (!res.ok) throw new Error('Falha ao carregar pedidos.');
      const leads = await res.json();
      renderLeads(leads);
    } catch (err) {
      if (err.message !== 'unauthorized') {
        console.error(err);
        leadsList.innerHTML = `<p class="text-muted text-sm">Não foi possível carregar os pedidos.</p>`;
      }
    }
  }

  function renderLeads(leads) {
    if (!leads.length) {
      leadsList.innerHTML = `<p class="text-muted text-sm">Nenhum pedido nesta categoria.</p>`;
      return;
    }

    leadsList.innerHTML = leads
      .map((lead) => {
        const statusColor = STATUS_COLORS[lead.status] || 'text-muted border-line';
        const statusOptions = Object.entries(STATUS_LABELS)
          .map(
            ([value, label]) =>
              `<option value="${value}" ${value === lead.status ? 'selected' : ''}>${label}</option>`
          )
          .join('');

        return `
          <article class="bg-elev border border-line rounded-xl p-4">
            <div class="flex items-start justify-between gap-3 mb-2">
              <div>
                <p class="font-semibold">${lead.client_name}</p>
                <p class="text-muted text-xs">${lead.client_phone}</p>
              </div>
              <select data-lead-id="${lead.id}"
                      class="status-select text-xs uppercase tracking-wide bg-transparent border rounded-full px-3 py-1.5 ${statusColor}">
                ${statusOptions}
              </select>
            </div>

            <div class="text-sm text-muted grid grid-cols-2 gap-y-1 mb-3">
              <span>Evento: <span class="text-ink">${lead.event_type}</span></span>
              <span>Data: <span class="text-ink">${formatDate(lead.event_date)}</span></span>
              <span>Pacote: <span class="text-ink">${lead.package_name || '—'}</span></span>
              <span>Valor: <span class="text-ink">${formatMT(lead.estimated_price)}</span></span>
            </div>

            <button data-lead-id="${lead.id}"
                    class="whatsapp-btn w-full text-center border border-gold text-gold rounded-lg px-4 py-2 text-sm hover:bg-gold hover:text-bg transition-colors">
              Abrir conversa no WhatsApp
            </button>
          </article>`;
      })
      .join('');

    // Mudança de estado
    leadsList.querySelectorAll('.status-select').forEach((select) => {
      select.addEventListener('change', () => updateLeadStatus(select.dataset.leadId, select.value));
    });

    // Abrir WhatsApp
    leadsList.querySelectorAll('.whatsapp-btn').forEach((btn) => {
      btn.addEventListener('click', () => openWhatsApp(btn.dataset.leadId, btn));
    });
  }

  async function updateLeadStatus(leadId, newStatus) {
    try {
      const res = await authedFetch(`/leads/${leadId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: newStatus }),
      });
      if (!res.ok) throw new Error('Falha ao atualizar estado.');
      // Se estivermos num filtro específico, o lead pode já não pertencer a ele.
      if (currentFilter) loadLeads();
    } catch (err) {
      if (err.message !== 'unauthorized') {
        console.error(err);
        alert('Não foi possível atualizar o estado do pedido.');
      }
    }
  }

  async function openWhatsApp(leadId, btn) {
    const originalText = btn.textContent;
    btn.textContent = 'A abrir…';
    btn.disabled = true;
    try {
      const res = await authedFetch(`/leads/whatsapp-link/${leadId}`);
      if (!res.ok) throw new Error('Falha ao gerar link do WhatsApp.');
      const { whatsapp_link } = await res.json();
      window.open(whatsapp_link, '_blank', 'noopener');
    } catch (err) {
      if (err.message !== 'unauthorized') {
        console.error(err);
        alert('Não foi possível abrir o WhatsApp.');
      }
    } finally {
      btn.textContent = originalText;
      btn.disabled = false;
    }
  }

  // ---------------------------------------------------------------------
  // Datas bloqueadas — listar, adicionar, remover
  // ---------------------------------------------------------------------
  async function loadBlockedDates() {
    blockedDatesList.innerHTML = `<div class="h-12 rounded-lg bg-elev animate-pulse"></div>`;
    try {
      const res = await authedFetch('/availability');
      if (!res.ok) throw new Error('Falha ao carregar agenda.');
      const dates = await res.json();
      renderBlockedDates(dates);
    } catch (err) {
      if (err.message !== 'unauthorized') {
        console.error(err);
        blockedDatesList.innerHTML = `<p class="text-muted text-sm">Não foi possível carregar a agenda.</p>`;
      }
    }
  }

  function renderBlockedDates(dates) {
    if (!dates.length) {
      blockedDatesList.innerHTML = `<p class="text-muted text-sm">Nenhuma data bloqueada.</p>`;
      return;
    }

    blockedDatesList.innerHTML = dates
      .map(
        (item) => `
        <div class="flex items-center justify-between bg-elev border border-line rounded-lg px-4 py-2.5">
          <div>
            <span class="text-sm font-medium">${formatDate(item.date)}</span>
            ${item.reason ? `<span class="text-muted text-xs ml-2">${item.reason}</span>` : ''}
          </div>
          <button data-id="${item.id}" class="unblock-btn text-xs text-red-400 hover:text-red-300">Remover</button>
        </div>`
      )
      .join('');

    blockedDatesList.querySelectorAll('.unblock-btn').forEach((btn) => {
      btn.addEventListener('click', () => removeBlockedDate(btn.dataset.id));
    });
  }

  blockedForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    const date = blockedDateInput.value;
    const reason = blockedReasonInput.value.trim();
    if (!date) return;

    try {
      const res = await authedFetch('/availability', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ date, reason: reason || null }),
      });
      if (!res.ok) {
        const detail = await res.json().catch(() => null);
        throw new Error(extractErrorMessage(detail, 'Falha ao bloquear data.'));
      }
      blockedDateInput.value = '';
      blockedReasonInput.value = '';
      loadBlockedDates();
    } catch (err) {
      if (err.message !== 'unauthorized') {
        console.error(err);
        alert(err.message);
      }
    }
  });

  async function removeBlockedDate(id) {
    try {
      const res = await authedFetch(`/availability/${id}`, { method: 'DELETE' });
      if (!res.ok && res.status !== 204) throw new Error('Falha ao remover data.');
      loadBlockedDates();
    } catch (err) {
      if (err.message !== 'unauthorized') {
        console.error(err);
        alert('Não foi possível remover a data.');
      }
    }
  }
  // ---------------------------------------------------------------------
  // Perfil público — GET/PUT /profile
  // ---------------------------------------------------------------------
  function showFeedback(el, message, isError = false) {
    el.textContent = message;
    el.classList.remove('hidden', 'text-green-400', 'text-red-400');
    el.classList.add(isError ? 'text-red-400' : 'text-green-400');
    setTimeout(() => el.classList.add('hidden'), 3000);
  }

  function updateProfilePhotoPreview(url) {
    profilePhotoPreview.innerHTML = url
      ? `<img src="${url}" alt="" class="w-full h-full object-cover">`
      : '—';
  }

  async function loadProfile() {
    try {
      const res = await authedFetch('/profile');
      if (!res.ok) throw new Error('Falha ao carregar perfil.');
      const profile = await res.json();
      profilePhotoUrlInput.value = profile.photo_url || '';
      updateProfilePhotoPreview(profile.photo_url);
      profileFullNameInput.value = profile.full_name || '';
      profileLocationInput.value = profile.location || '';
      profileWhatsappInput.value = profile.whatsapp_number || '';
      profileBioInput.value = profile.bio || '';
    } catch (err) {
      if (err.message !== 'unauthorized') console.error(err);
    }
  }

  profilePhotoUrlInput.addEventListener('input', () => updateProfilePhotoPreview(profilePhotoUrlInput.value.trim()));

  profilePhotoFileInput.addEventListener('change', async () => {
    const file = profilePhotoFileInput.files[0];
    if (!file) return;

    if (uploadNotConfigured()) {
      profilePhotoStatus.textContent = 'Upload direto ainda não está configurado — cole o link manualmente por agora.';
      profilePhotoStatus.classList.remove('hidden', 'text-green-400');
      profilePhotoStatus.classList.add('text-red-400');
      profilePhotoFileInput.value = '';
      return;
    }

    profilePhotoStatus.textContent = 'A enviar…';
    profilePhotoStatus.classList.remove('hidden', 'text-red-400', 'text-green-400');

    try {
      const result = await uploadToCloudinary(file, 'image');
      profilePhotoUrlInput.value = result.secure_url;
      updateProfilePhotoPreview(result.secure_url);
      profilePhotoStatus.textContent = 'Foto enviada — lembre-se de "Guardar perfil" abaixo.';
      profilePhotoStatus.classList.add('text-green-400');
    } catch (err) {
      console.error(err);
      profilePhotoStatus.textContent = err.message;
      profilePhotoStatus.classList.add('text-red-400');
    } finally {
      profilePhotoFileInput.value = '';
    }
  });

  profileForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    try {
      const res = await authedFetch('/profile', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          photo_url: profilePhotoUrlInput.value.trim() || null,
          full_name: profileFullNameInput.value.trim(),
          location: profileLocationInput.value.trim(),
          whatsapp_number: profileWhatsappInput.value.trim(),
          bio: profileBioInput.value.trim(),
        }),
      });
      if (!res.ok) {
        const detail = await res.json().catch(() => null);
        throw new Error(extractErrorMessage(detail, 'Falha ao guardar perfil.'));
      }
      showFeedback(profileFeedback, 'Perfil atualizado com sucesso.');
    } catch (err) {
      if (err.message !== 'unauthorized') {
        console.error(err);
        showFeedback(profileFeedback, err.message, true);
      }
    }
  });

  // ---------------------------------------------------------------------
  // Pacotes por tipo de evento — GET/POST/PATCH/DELETE /packages
  // ---------------------------------------------------------------------
  let allPackagesCache = []; // usado pelo botão "Editar" para pré-preencher o formulário
  let editingPackageId = null; // != null enquanto o formulário está em modo de edição

  async function loadPackagesAdmin() {
    packagesAdminList.innerHTML = `<div class="h-16 rounded-lg bg-elev animate-pulse"></div>`;
    try {
      const res = await authedFetch('/packages');
      if (!res.ok) throw new Error('Falha ao carregar pacotes.');
      const packages = await res.json();
      allPackagesCache = packages;
      renderPackagesAdmin(packages);
    } catch (err) {
      if (err.message !== 'unauthorized') {
        console.error(err);
        packagesAdminList.innerHTML = `<p class="text-muted text-sm">Não foi possível carregar os pacotes.</p>`;
      }
    }
  }

  function renderPackagesAdmin(packages) {
    if (!packages.length) {
      packagesAdminList.innerHTML = `<p class="text-muted text-sm">Ainda não há pacotes criados.</p>`;
      return;
    }

    // Agrupar por tipo de evento para facilitar a leitura
    const groups = {};
    for (const pkg of packages) {
      (groups[pkg.event_type] ||= []).push(pkg);
    }

    packagesAdminList.innerHTML = Object.entries(groups)
      .map(
        ([eventType, items]) => `
        <div>
          <p class="text-xs uppercase tracking-widest text-goldsoft mb-2">${eventType}</p>
          <div class="space-y-2">
            ${items
              .map(
                (pkg) => `
                <details class="bg-elev border border-line rounded-lg px-4 py-3 ${pkg.is_active ? '' : 'opacity-50'}">
                  <summary class="flex items-center justify-between gap-3 cursor-pointer list-none">
                    <div>
                      <p class="text-sm font-medium">${pkg.name}</p>
                      <p class="text-muted text-xs">${formatMT(pkg.base_price)}${pkg.is_active ? '' : ' · inativo'} · toque para ver tudo</p>
                    </div>
                    <div class="flex gap-2 shrink-0" onclick="event.stopPropagation()">
                      <button data-id="${pkg.id}" class="edit-package-btn text-xs text-goldsoft hover:text-gold">
                        Editar
                      </button>
                      <button data-id="${pkg.id}" data-active="${pkg.is_active}"
                              class="toggle-package-btn text-xs text-gold hover:text-goldsoft">
                        ${pkg.is_active ? 'Desativar' : 'Ativar'}
                      </button>
                      <button data-id="${pkg.id}" class="delete-package-btn text-xs text-red-400 hover:text-red-300">
                        Remover
                      </button>
                    </div>
                  </summary>
                  <div class="mt-3 pt-3 border-t border-line/60 text-sm">
                    <p class="text-ink/85 leading-relaxed whitespace-pre-line mb-3">${pkg.description}</p>
                    <ul class="space-y-1.5">
                      ${(pkg.features || [])
                        .map((f) => `<li class="flex gap-2"><span class="text-gold shrink-0">·</span><span class="text-ink/80">${f}</span></li>`)
                        .join('')}
                    </ul>
                  </div>
                </details>`
              )
              .join('')}
          </div>
        </div>`
      )
      .join('');

    packagesAdminList.querySelectorAll('.edit-package-btn').forEach((btn) => {
      btn.addEventListener('click', () => startEditPackage(btn.dataset.id));
    });
    packagesAdminList.querySelectorAll('.toggle-package-btn').forEach((btn) => {
      btn.addEventListener('click', () =>
        togglePackageActive(btn.dataset.id, btn.dataset.active !== 'true')
      );
    });
    packagesAdminList.querySelectorAll('.delete-package-btn').forEach((btn) => {
      btn.addEventListener('click', () => deletePackage(btn.dataset.id));
    });
  }

  // ---------------------------------------------------------------------
  // Descrição de cada tipo de evento — GET /event-info + PUT /event-info/{tipo}
  // ---------------------------------------------------------------------
  async function loadEventInfo() {
    eventInfoList.innerHTML = `<div class="h-16 rounded-lg bg-elev animate-pulse"></div>`;
    try {
      const res = await authedFetch('/event-info');
      if (!res.ok) throw new Error('Falha ao carregar.');
      const items = await res.json();
      renderEventInfo(items);
    } catch (err) {
      if (err.message !== 'unauthorized') {
        console.error(err);
        eventInfoList.innerHTML = `<p class="text-muted text-sm">Não foi possível carregar.</p>`;
      }
    }
  }

  function renderEventInfo(items) {
    eventInfoList.innerHTML = items
      .map(
        (item) => `
        <div class="bg-elev border border-line rounded-lg p-3">
          <p class="text-xs uppercase tracking-widest text-goldsoft mb-2">${item.event_type}</p>
          <textarea data-type="${item.event_type}" rows="2"
                    placeholder="Ex: O seu casamento vai ser um espetáculo do início ao fim…"
                    class="event-info-textarea w-full bg-elev2 border border-line rounded-lg px-3 py-2 text-sm placeholder:text-muted/60 focus:border-gold outline-none resize-y mb-2">${item.tagline}</textarea>
          <button data-type="${item.event_type}" class="save-event-info-btn text-xs text-gold hover:text-goldsoft">
            Guardar
          </button>
          <span class="save-event-info-feedback text-xs text-green-400 ml-2 hidden">Guardado ✓</span>
        </div>`
      )
      .join('');

    eventInfoList.querySelectorAll('.save-event-info-btn').forEach((btn) => {
      btn.addEventListener('click', () => saveEventInfo(btn));
    });
  }

  async function saveEventInfo(btn) {
    const eventType = btn.dataset.type;
    const textarea = eventInfoList.querySelector(`.event-info-textarea[data-type="${eventType}"]`);
    const feedback = btn.nextElementSibling;

    try {
      const res = await authedFetch(`/event-info/${encodeURIComponent(eventType)}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tagline: textarea.value.trim() }),
      });
      if (!res.ok) throw new Error('Falha ao guardar.');
      feedback.classList.remove('hidden');
      setTimeout(() => feedback.classList.add('hidden'), 2000);
    } catch (err) {
      if (err.message !== 'unauthorized') {
        console.error(err);
        alert('Não foi possível guardar esta descrição.');
      }
    }
  }

  const packageSubmitBtn = document.getElementById('package-submit-btn');
  const packageCancelEditBtn = document.getElementById('package-cancel-edit-btn');

  function startEditPackage(id) {
    const pkg = allPackagesCache.find((p) => p.id === id);
    if (!pkg) return;

    editingPackageId = id;
    packageNameInput.value = pkg.name;
    packageEventTypeInput.value = pkg.event_type;
    packageDescriptionInput.value = pkg.description;
    packagePriceInput.value = pkg.base_price;
    packageFeaturesInput.value = (pkg.features || []).join('\n');

    packageSubmitBtn.textContent = 'Guardar alterações';
    packageCancelEditBtn.classList.remove('hidden');
    packageForm.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  function stopEditPackage() {
    editingPackageId = null;
    packageForm.reset();
    packageSubmitBtn.textContent = 'Adicionar pacote';
    packageCancelEditBtn.classList.add('hidden');
  }

  packageCancelEditBtn.addEventListener('click', stopEditPackage);

  packageForm.addEventListener('submit', async (event) => {
    event.preventDefault();

    const features = packageFeaturesInput.value
      .split('\n')
      .map((f) => f.trim())
      .filter(Boolean);

    const payload = {
      name: packageNameInput.value.trim(),
      event_type: packageEventTypeInput.value,
      description: packageDescriptionInput.value.trim(),
      base_price: Number(packagePriceInput.value),
      features,
    };

    if (!payload.name || !payload.event_type || !payload.description || !payload.base_price) {
      showFeedback(packageFeedback, 'Preencha todos os campos obrigatórios.', true);
      return;
    }

    const isEditing = editingPackageId !== null;

    try {
      const res = await authedFetch(isEditing ? `/packages/${editingPackageId}` : '/packages', {
        method: isEditing ? 'PATCH' : 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const detail = await res.json().catch(() => null);
        throw new Error(extractErrorMessage(detail, isEditing ? 'Falha ao guardar alterações.' : 'Falha ao criar pacote.'));
      }
      showFeedback(packageFeedback, isEditing ? 'Pacote atualizado.' : 'Pacote adicionado.');
      stopEditPackage();
      loadPackagesAdmin();
    } catch (err) {
      if (err.message !== 'unauthorized') {
        console.error(err);
        showFeedback(packageFeedback, err.message, true);
      }
    }
  });

  async function togglePackageActive(id, newActive) {
    try {
      const res = await authedFetch(`/packages/${id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ is_active: newActive }),
      });
      if (!res.ok) throw new Error('Falha ao atualizar pacote.');
      loadPackagesAdmin();
    } catch (err) {
      if (err.message !== 'unauthorized') {
        console.error(err);
        alert('Não foi possível atualizar o pacote.');
      }
    }
  }

  async function deletePackage(id) {
    if (!confirm('Remover este pacote permanentemente?')) return;
    try {
      const res = await authedFetch(`/packages/${id}`, { method: 'DELETE' });
      if (!res.ok && res.status !== 204) throw new Error('Falha ao remover pacote.');
      loadPackagesAdmin();
    } catch (err) {
      if (err.message !== 'unauthorized') {
        console.error(err);
        alert('Não foi possível remover o pacote.');
      }
    }
  }
  // ---------------------------------------------------------------------
  // Galeria — GET/POST/PATCH/DELETE /gallery
  // ---------------------------------------------------------------------
  async function loadMediaAdmin() {
    mediaAdminList.innerHTML = `<div class="h-16 rounded-lg bg-elev animate-pulse"></div>`;
    try {
      const res = await authedFetch('/gallery?include_inactive=true');
      if (!res.ok) throw new Error('Falha ao carregar galeria.');
      const items = await res.json();
      renderMediaAdmin(items);
    } catch (err) {
      if (err.message !== 'unauthorized') {
        console.error(err);
        mediaAdminList.innerHTML = `<p class="text-muted text-sm">Não foi possível carregar a galeria.</p>`;
      }
    }
  }

  function renderMediaAdmin(items) {
    if (!items.length) {
      mediaAdminList.innerHTML = `<p class="text-muted text-sm">Ainda não há fotos/vídeos na galeria.</p>`;
      return;
    }

    mediaAdminList.innerHTML = items
      .map(
        (item) => `
        <div class="flex items-center gap-3 bg-elev border border-line rounded-lg px-4 py-2.5 ${item.is_active ? '' : 'opacity-50'}">
          <img src="${item.thumbnail_url || item.url}" alt="" class="w-12 h-12 rounded-md object-cover shrink-0 bg-elev2">
          <div class="flex-1 min-w-0">
            <p class="text-sm font-medium truncate">${item.title}</p>
            <p class="text-muted text-xs">${item.type === 'video' ? 'Vídeo' : 'Foto'}${item.is_active ? '' : ' · inativo'}</p>
          </div>
          <div class="flex gap-2 shrink-0">
            <button data-id="${item.id}" data-active="${item.is_active}"
                    class="toggle-media-btn text-xs text-gold hover:text-goldsoft">
              ${item.is_active ? 'Ocultar' : 'Mostrar'}
            </button>
            <button data-id="${item.id}" class="delete-media-btn text-xs text-red-400 hover:text-red-300">
              Remover
            </button>
          </div>
        </div>`
      )
      .join('');

    mediaAdminList.querySelectorAll('.toggle-media-btn').forEach((btn) => {
      btn.addEventListener('click', () => toggleMediaActive(btn.dataset.id, btn.dataset.active !== 'true'));
    });
    mediaAdminList.querySelectorAll('.delete-media-btn').forEach((btn) => {
      btn.addEventListener('click', () => deleteMedia(btn.dataset.id));
    });
  }

  // Ajusta o tipo de ficheiro aceite (foto/vídeo) consoante a escolha
  mediaTypeInput.addEventListener('change', () => {
    mediaFileInput.accept = mediaTypeInput.value === 'video' ? 'video/*' : 'image/*';
  });

  function showMediaUploadStatus(message, isError = false) {
    mediaUploadStatus.textContent = message;
    mediaUploadStatus.classList.remove('hidden', 'text-red-400', 'text-green-400');
    mediaUploadStatus.classList.add(isError ? 'text-red-400' : 'text-green-400');
  }

  mediaFileInput.addEventListener('change', async () => {
    const file = mediaFileInput.files[0];
    if (!file) return;

    if (uploadNotConfigured()) {
      showMediaUploadStatus('Upload direto ainda não está configurado — cole o link manualmente por agora.', true);
      mediaFileInput.value = '';
      return;
    }

    const isVideo = mediaTypeInput.value === 'video';

    if (isVideo) {
      try {
        const duration = await getVideoDuration(file);
        if (duration > MAX_VIDEO_SECONDS) {
          showMediaUploadStatus(
            `Este vídeo tem ${Math.round(duration)}s — o limite é ${MAX_VIDEO_SECONDS}s. Escolha um vídeo mais curto.`,
            true
          );
          mediaFileInput.value = '';
          return;
        }
      } catch (err) {
        showMediaUploadStatus(err.message, true);
        mediaFileInput.value = '';
        return;
      }
    }

    mediaUploadProgressWrap.classList.remove('hidden');
    mediaUploadProgressBar.style.width = '0%';
    showMediaUploadStatus('A enviar…');

    try {
      const result = await uploadToCloudinary(file, isVideo ? 'video' : 'image', (pct) => {
        mediaUploadProgressBar.style.width = `${pct}%`;
      });
      mediaUrlInput.value = result.secure_url;
      if (isVideo) mediaThumbnailInput.value = cloudinaryVideoThumbnail(result.secure_url);
      showMediaUploadStatus('Enviado — agora escolha "Adicionar à galeria".');
    } catch (err) {
      console.error(err);
      showMediaUploadStatus(err.message, true);
    } finally {
      mediaUploadProgressWrap.classList.add('hidden');
      mediaFileInput.value = '';
    }
  });

  mediaForm.addEventListener('submit', async (event) => {
    event.preventDefault();

    const payload = {
      title: mediaTitleInput.value.trim(),
      type: mediaTypeInput.value,
      url: mediaUrlInput.value.trim(),
      thumbnail_url: mediaThumbnailInput.value.trim() || null,
    };

    if (!payload.title || !payload.url) {
      showFeedback(mediaFeedback, 'Preencha o título e o link.', true);
      return;
    }

    try {
      const res = await authedFetch('/gallery', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const detail = await res.json().catch(() => null);
        throw new Error(extractErrorMessage(detail, 'Falha ao adicionar à galeria.'));
      }
      mediaForm.reset();
      showFeedback(mediaFeedback, 'Adicionado à galeria.');
      loadMediaAdmin();
    } catch (err) {
      if (err.message !== 'unauthorized') {
        console.error(err);
        showFeedback(mediaFeedback, err.message, true);
      }
    }
  });

  async function toggleMediaActive(id, newActive) {
    try {
      const res = await authedFetch(`/gallery/${id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ is_active: newActive }),
      });
      if (!res.ok) throw new Error('Falha ao atualizar item.');
      loadMediaAdmin();
    } catch (err) {
      if (err.message !== 'unauthorized') {
        console.error(err);
        alert('Não foi possível atualizar o item da galeria.');
      }
    }
  }

  async function deleteMedia(id) {
    if (!confirm('Remover este item da galeria permanentemente?')) return;
    try {
      const res = await authedFetch(`/gallery/${id}`, { method: 'DELETE' });
      if (!res.ok && res.status !== 204) throw new Error('Falha ao remover item.');
      loadMediaAdmin();
    } catch (err) {
      if (err.message !== 'unauthorized') {
        console.error(err);
        alert('Não foi possível remover o item da galeria.');
      }
    }
  }
})();
