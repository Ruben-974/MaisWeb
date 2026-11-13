(() => {
  'use strict';

  const normalize = (value) => String(value).normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().trim();

  const copyText = async (value, existingInput) => {
    try {
      if (!navigator.clipboard?.writeText) throw new Error('Clipboard unavailable');
      await navigator.clipboard.writeText(value);
      return true;
    } catch {
      const input = existingInput || document.createElement('textarea');
      const temporary = !existingInput;
      if (temporary) {
        input.value = value;
        input.setAttribute('readonly', '');
        input.style.cssText = 'position:fixed;left:-9999px;top:0;';
        document.body.append(input);
      }
      input.focus();
      input.select();
      input.setSelectionRange(0, input.value.length);
      let copied = false;
      try { copied = document.execCommand('copy'); } catch { copied = false; }
      if (temporary) input.remove();
      return copied;
    }
  };

  const initialize = () => {
    document.querySelectorAll('[data-filter-scope]').forEach((scope) => {
      const input = scope.querySelector('[data-filter-search]');
      const year = scope.querySelector('[data-filter-year]');
      const buttons = [...scope.querySelectorAll('[data-filter-category]')];
      const items = [...scope.querySelectorAll('[data-filter-item]')];
      const count = scope.querySelector('[data-filter-count]');
      const empty = scope.querySelector('[data-filter-empty]');
      let category = '';

      const update = () => {
        const query = normalize(input?.value || '');
        let visible = 0;
        items.forEach((item) => {
          const matches = (!query || normalize(item.dataset.search || item.textContent).includes(query))
            && (!category || item.dataset.category === category)
            && (!year?.value || item.dataset.year === year.value);
          item.hidden = !matches;
          if (matches) visible += 1;
        });
        if (count) count.textContent = `${visible} ${visible === 1 ? 'resultado' : 'resultados'}`;
        if (empty) empty.hidden = visible !== 0;
      };

      input?.addEventListener('input', update);
      year?.addEventListener('change', update);
      buttons.forEach((button) => {
        button.addEventListener('click', () => {
          category = button.dataset.filterCategory;
          buttons.forEach((option) => {
            const selected = option === button;
            option.classList.toggle('is-selected', selected);
            option.setAttribute('aria-pressed', String(selected));
          });
          update();
        });
      });
      update();
    });

    // Players are loaded only after the visitor chooses to watch.
    document.querySelectorAll('[data-youtube]').forEach((container) => {
      const button = container.querySelector('.video-facade');
      const id = container.dataset.youtube;
      if (!button || !/^[A-Za-z0-9_-]{11}$/.test(id)) return;
      const watchUrl = `https://www.youtube.com/watch?v=${id}`;
      if (window.location.protocol === 'file:') {
        const label = button.querySelector('[data-video-button-label]');
        if (label) label.textContent = 'Assistir no YouTube';
        button.setAttribute('aria-label', `Assistir ${container.dataset.videoTitle || 'vídeo da AACI'} no YouTube (abre em nova aba)`);
      }
      button.addEventListener('click', () => {
        if (window.location.protocol === 'file:') {
          window.open(watchUrl, '_blank', 'noopener,noreferrer');
          return;
        }
        const iframe = document.createElement('iframe');
        iframe.src = `https://www.youtube-nocookie.com/embed/${id}?autoplay=1&rel=0&playsinline=1`;
        iframe.title = container.dataset.videoTitle || 'Vídeo da AACI';
        iframe.allow = 'accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share';
        iframe.allowFullscreen = true;
        iframe.referrerPolicy = 'strict-origin-when-cross-origin';
        iframe.tabIndex = 0;
        container.replaceChildren(iframe);
        iframe.focus({ preventScroll: true });
      });
    });

    const localVideos = [...document.querySelectorAll('video')];
    localVideos.forEach((video) => {
      video.addEventListener('play', () => {
        localVideos.forEach((other) => {
          if (other !== video && !other.paused) other.pause();
        });
      });
    });

    document.querySelectorAll('[data-copy-pix]').forEach((button) => {
      button.addEventListener('click', async () => {
        const input = document.getElementById(button.dataset.copyTarget);
        const status = document.getElementById(button.dataset.copyStatus);
        const copied = await copyText(button.dataset.copyPix, input);
        if (status) status.textContent = copied ? 'Chave Pix copiada.' : 'Selecione a chave e use a opção de copiar do seu dispositivo.';
        if (copied) button.focus({ preventScroll: true });
      });
    });

    document.querySelectorAll('[data-share-page]').forEach((button) => {
      button.addEventListener('click', async () => {
        const url = window.location.protocol === 'file:' ? button.dataset.shareUrl : window.location.href;
        const copied = await copyText(url);
        const status = button.closest('.article-share')?.querySelector('[data-share-status]');
        if (status) status.textContent = copied ? 'Link da história copiado.' : 'Copie o endereço desta página pela barra do navegador.';
        button.focus({ preventScroll: true });
      });
    });

    const gallery = document.getElementById('galleryModal');
    const fullImage = document.getElementById('galleryFullImage');
    const caption = document.getElementById('galleryCaption');
    const galleryLinks = [...document.querySelectorAll('[data-gallery-link]')];
    let galleryOpener = null;
    let currentImage = 0;
    let visibleGalleryLinks = [];

    const displayImage = (index) => {
      if (!visibleGalleryLinks.length || !fullImage) return;
      currentImage = (index + visibleGalleryLinks.length) % visibleGalleryLinks.length;
      const link = visibleGalleryLinks[currentImage];
      if (link.dataset.localHref) fullImage.dataset.localSrc = link.dataset.localHref;
      else delete fullImage.dataset.localSrc;
      fullImage.src = link.href;
      fullImage.alt = link.dataset.galleryTitle || 'Registro da AACI';
      if (caption) caption.textContent = `${currentImage + 1} de ${visibleGalleryLinks.length} · ${fullImage.alt}`;
      gallery.querySelectorAll('[data-gallery-prev], [data-gallery-next]').forEach((button) => {
        button.disabled = visibleGalleryLinks.length < 2;
      });
    };

    galleryLinks.forEach((link) => {
      link.addEventListener('click', (event) => {
        if (!gallery || !window.bootstrap?.Modal) return;
        event.preventDefault();
        visibleGalleryLinks = galleryLinks.filter((item) => !item.closest('[hidden]'));
        galleryOpener = link;
        displayImage(visibleGalleryLinks.indexOf(link));
        window.bootstrap.Modal.getOrCreateInstance(gallery).show(link);
      });
    });
    gallery?.querySelector('[data-gallery-prev]')?.addEventListener('click', () => displayImage(currentImage - 1));
    gallery?.querySelector('[data-gallery-next]')?.addEventListener('click', () => displayImage(currentImage + 1));
    gallery?.addEventListener('keydown', (event) => {
      if (event.key !== 'ArrowLeft' && event.key !== 'ArrowRight') return;
      event.preventDefault();
      displayImage(currentImage + (event.key === 'ArrowRight' ? 1 : -1));
    });
    gallery?.addEventListener('hidden.bs.modal', () => {
      if (fullImage) fullImage.removeAttribute('src');
      if (galleryOpener?.isConnected && !galleryOpener.closest('[hidden]')) galleryOpener.focus({ preventScroll: true });
      galleryOpener = null;
    });

    const contactForm = document.getElementById('contactForm');
    if (contactForm) {
      const name = document.getElementById('contactName');
      const email = document.getElementById('contactEmail');
      const subject = document.getElementById('contactSubject');
      const message = document.getElementById('contactMessage');
      const result = document.getElementById('contactResult');
      const status = document.getElementById('contactFormStatus');
      const whatsapp = document.getElementById('contactWhatsapp');
      const fields = [...contactForm.querySelectorAll('input, select, textarea')];
      fields.forEach((field) => {
        const feedback = field.parentElement.querySelector('.invalid-feedback');
        if (feedback) {
          feedback.id = `${field.id}Error`;
          field.setAttribute('aria-describedby', feedback.id);
        }
      });

      const invalidateDraft = () => {
        result.hidden = true;
        whatsapp.removeAttribute('href');
        fields.forEach((field) => field.setCustomValidity(''));
      };
      contactForm.addEventListener('input', invalidateDraft);
      contactForm.addEventListener('change', invalidateDraft);
      contactForm.addEventListener('submit', (event) => {
        event.preventDefault();
        name.setCustomValidity(name.value.trim().length < 2 ? 'Informe seu nome.' : '');
        message.setCustomValidity(message.value.trim().length < 10 ? 'Escreva uma mensagem com pelo menos 10 caracteres.' : '');
        contactForm.classList.add('was-validated');
        fields.forEach((field) => field.setAttribute('aria-invalid', String(!field.checkValidity())));
        if (!contactForm.checkValidity()) {
          result.hidden = true;
          whatsapp.removeAttribute('href');
          contactForm.querySelector(':invalid')?.focus();
          return;
        }
        const lines = ['Olá, AACI!', `Meu nome é ${name.value.trim()}.`, `Assunto: ${subject.value}`];
        if (email.value.trim()) lines.push(`E-mail para contato: ${email.value.trim()}`);
        lines.push('', message.value.trim());
        whatsapp.href = `https://wa.me/5532988559201?text=${encodeURIComponent(lines.join('\n'))}`;
        status.textContent = 'Sua mensagem está preparada. Continue no WhatsApp para revisar e enviar.';
        result.hidden = false;
        whatsapp.focus({ preventScroll: true });
      });
      contactForm.querySelector('[type="submit"]').disabled = false;
    }

    const backToTop = document.querySelector('.back-to-top');
    if (backToTop) {
      let scheduled = false;
      const update = () => {
        const visible = window.scrollY > 650;
        backToTop.classList.toggle('is-visible', visible);
        backToTop.tabIndex = visible ? 0 : -1;
        scheduled = false;
      };
      window.addEventListener('scroll', () => {
        if (scheduled) return;
        scheduled = true;
        window.requestAnimationFrame(update);
      }, { passive: true });
      update();
    }
  };

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', initialize, { once: true });
  else initialize();
})();
