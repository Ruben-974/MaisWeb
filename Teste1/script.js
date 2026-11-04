(() => {
  'use strict';

  const initialize = () => {
    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
    const currency = new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL',
      minimumFractionDigits: 0,
      maximumFractionDigits: 2,
    });

    // Keep every card visible in the stack, but only its front card interactive.
    const donationStack = document.querySelector('.donation-stack');
    const donationCards = donationStack
      ? Array.from(donationStack.querySelectorAll('.donation-card'))
      : [];
    const carouselStatus = document.getElementById('donationCarouselStatus');
    const donationDots = Array.from(
      donationStack?.closest('.donation-carousel')?.querySelectorAll('.donation-dots span') || [],
    );

    if (donationCards.length) {
      let currentCard = Number(donationStack.dataset.donationIndex) || 0;

      const displayDonationCard = (index, moveFocus = false) => {
        currentCard = (index + donationCards.length) % donationCards.length;
        donationStack.dataset.donationIndex = String(currentCard);

        donationCards.forEach((card, cardIndex) => {
          const position = (cardIndex - currentCard + donationCards.length) % donationCards.length;
          card.dataset.position = String(position);
          card.classList.toggle('is-active', position === 0);
          card.setAttribute('aria-hidden', position === 0 ? 'false' : 'true');
          card.inert = position !== 0;
        });
        donationDots.forEach((dot, dotIndex) => {
          dot.classList.toggle('is-active', dotIndex === currentCard);
        });

        if (carouselStatus) {
          carouselStatus.textContent = `Opção de doação ${currentCard + 1} de ${donationCards.length}`;
        }

        if (moveFocus) {
          donationCards[currentCard].querySelector('button, a')?.focus({ preventScroll: true });
        }
      };

      document.querySelectorAll('[data-donation-prev]').forEach((button) => {
        button.addEventListener('click', () => displayDonationCard(currentCard - 1));
      });
      document.querySelectorAll('[data-donation-next]').forEach((button) => {
        button.addEventListener('click', () => displayDonationCard(currentCard + 1));
      });

      donationStack.addEventListener('keydown', (event) => {
        if (event.key !== 'ArrowLeft' && event.key !== 'ArrowRight') return;
        event.preventDefault();
        displayDonationCard(currentCard + (event.key === 'ArrowRight' ? 1 : -1), true);
      });

      displayDonationCard(currentCard);
    }

    const modalElement = document.getElementById('donationModal');
    const amountLabel = document.getElementById('donationAmountLabel');
    const customAmount = document.getElementById('donationCustomAmount');
    const amountError = document.getElementById('donationAmountError');
    const whatsappLink = document.getElementById('donationWhatsapp');
    const amountButtons = Array.from(document.querySelectorAll('[data-donation-amount]'));
    const navigation = document.getElementById('mainNav');
    const navbarToggler = document.querySelector('.navbar-toggler[aria-controls="mainNav"]');
    let donationAmount = 50;
    let modalOpener = null;

    const isVisible = (element) => Boolean(
      element?.isConnected
      && element.getClientRects().length
      && window.getComputedStyle(element).visibility !== 'hidden'
      && !element.closest('[inert]'),
    );

    const isMobileMenuOpen = () => Boolean(
      navigation?.classList.contains('show')
      && navbarToggler
      && window.getComputedStyle(navbarToggler).display !== 'none',
    );

    const parseAmount = (value) => {
      const parsed = Number(String(value).trim().replace(',', '.'));
      const cents = Math.round(parsed * 100);
      const hasValidPrecision = Math.abs(parsed * 100 - cents) < 0.000001;
      return Number.isFinite(parsed) && parsed >= 1 && parsed <= 1000000
        && Number.isSafeInteger(cents) && hasValidPrecision
        ? cents / 100
        : null;
    };

    const updateDonationAmount = (value, updateInput = true) => {
      const amount = parseAmount(value);
      const isValid = amount !== null;

      if (amountError) {
        amountError.hidden = isValid;
        amountError.textContent = isValid
          ? ''
          : 'Informe um valor entre R$ 1 e R$ 1.000.000, com até duas casas decimais.';
      }
      if (customAmount) {
        customAmount.setAttribute('aria-invalid', isValid ? 'false' : 'true');
        if (isValid && updateInput) customAmount.value = String(amount);
      }

      amountButtons.forEach((button) => {
        const selected = isValid && parseAmount(button.dataset.donationAmount) === amount;
        button.classList.toggle('is-selected', selected);
        button.setAttribute('aria-pressed', selected ? 'true' : 'false');
      });

      if (whatsappLink) {
        whatsappLink.setAttribute('aria-disabled', isValid ? 'false' : 'true');
        whatsappLink.classList.toggle('disabled', !isValid);
        whatsappLink.tabIndex = isValid ? 0 : -1;

        if (isValid) {
          const message = `Olá! Gostaria de contribuir com uma doação de ${currency.format(amount)} para a AACI. Podem me orientar?`;
          whatsappLink.href = `https://wa.me/5532988559201?text=${encodeURIComponent(message)}`;
        } else {
          whatsappLink.removeAttribute('href');
        }
      }

      if (isValid) {
        donationAmount = amount;
        if (amountLabel) amountLabel.textContent = currency.format(amount);
      } else if (amountLabel) {
        amountLabel.textContent = 'Escolha um valor';
      }
    };

    document.querySelectorAll('.donate-trigger').forEach((button) => {
      button.addEventListener('click', (event) => {
        if (!modalElement || !window.bootstrap?.Modal) return;
        event.preventDefault();
        modalOpener = button;
        if (navigation?.contains(button) && isMobileMenuOpen() && window.bootstrap?.Collapse) {
          window.bootstrap.Collapse.getOrCreateInstance(navigation, { toggle: false }).hide();
        }
        updateDonationAmount(button.dataset.amount || donationAmount);
        window.bootstrap.Modal.getOrCreateInstance(modalElement).show(button);
      });
    });

    amountButtons.forEach((button) => {
      button.addEventListener('click', () => updateDonationAmount(button.dataset.donationAmount));
    });
    customAmount?.addEventListener('input', () => updateDonationAmount(customAmount.value, false));
    whatsappLink?.addEventListener('click', (event) => {
      if (whatsappLink.getAttribute('aria-disabled') === 'true') event.preventDefault();
    });

    if (modalElement) {
      modalElement.addEventListener('show.bs.modal', (event) => {
        if (event.relatedTarget instanceof HTMLElement) modalOpener = event.relatedTarget;
      });
      modalElement.addEventListener('hidden.bs.modal', () => {
        if (isVisible(modalOpener)) {
          modalOpener.focus({ preventScroll: true });
        } else if (modalOpener?.isConnected && navigation?.contains(modalOpener) && isVisible(navbarToggler)) {
          navbarToggler.focus({ preventScroll: true });
        }
        modalOpener = null;
      });
      updateDonationAmount(donationAmount);
    }

    const copyPixButton = document.getElementById('copyPix');
    const pixInput = document.getElementById('pixKey');
    const copyPixStatus = document.getElementById('copyPixStatus');

    if (copyPixButton) {
      const originalButtonContent = copyPixButton.innerHTML;
      let resetCopyTimer;

      copyPixButton.addEventListener('click', async () => {
        const pixKey = copyPixButton.dataset.pix || pixInput?.value;
        if (!pixKey) return;
        let copied = false;

        try {
          if (!navigator.clipboard?.writeText) throw new Error('Clipboard unavailable');
          await navigator.clipboard.writeText(pixKey);
          copied = true;
        } catch {
          if (pixInput) {
            pixInput.focus();
            pixInput.select();
            pixInput.setSelectionRange(0, pixInput.value.length);
            try {
              copied = document.execCommand('copy');
            } catch {
              copied = false;
            }
          }
        }

        if (copyPixStatus) {
          copyPixStatus.textContent = copied
            ? 'Chave Pix copiada.'
            : 'Selecione a chave acima e use a opção de copiar do seu dispositivo.';
        }

        if (copied) {
          window.clearTimeout(resetCopyTimer);
          copyPixButton.textContent = 'Copiado!';
          resetCopyTimer = window.setTimeout(() => {
            copyPixButton.innerHTML = originalButtonContent;
          }, 2500);
        }
      });
    }

    const impactAmount = document.getElementById('impactAmount');
    const impactDescription = document.getElementById('impactDescription');
    const impactButtons = Array.from(document.querySelectorAll('[data-impact-amount]'));

    impactButtons.forEach((button) => {
      button.addEventListener('click', () => {
        const amount = parseAmount(button.dataset.impactAmount);
        if (amount === null) return;

        impactButtons.forEach((option) => {
          const selected = option === button;
          option.classList.toggle('is-selected', selected);
          option.setAttribute('aria-pressed', selected ? 'true' : 'false');
        });
        if (impactAmount) impactAmount.textContent = currency.format(amount);
        if (impactDescription && button.dataset.impactDescription) {
          impactDescription.textContent = button.dataset.impactDescription;
        }

        document.querySelectorAll('[data-impact-donate]').forEach((trigger) => {
          trigger.dataset.amount = String(amount);
        });
      });
    });

    const newsTrack = document.getElementById('newsTrack');
    const previousNewsButtons = Array.from(document.querySelectorAll('[data-news-prev]'));
    const nextNewsButtons = Array.from(document.querySelectorAll('[data-news-next]'));

    if (newsTrack) {
      const updateNewsControls = () => {
        const maximumScroll = Math.max(0, newsTrack.scrollWidth - newsTrack.clientWidth);
        const atStart = newsTrack.scrollLeft <= 2;
        const atEnd = newsTrack.scrollLeft >= maximumScroll - 2;
        previousNewsButtons.forEach((button) => { button.disabled = atStart; });
        nextNewsButtons.forEach((button) => { button.disabled = atEnd; });
      };

      const moveNews = (direction) => {
        const card = newsTrack.firstElementChild;
        const gap = Number.parseFloat(window.getComputedStyle(newsTrack).columnGap) || 0;
        const distance = card ? card.getBoundingClientRect().width + gap : newsTrack.clientWidth;
        newsTrack.scrollBy({
          left: direction * distance,
          behavior: reducedMotion.matches ? 'instant' : 'smooth',
        });
      };

      previousNewsButtons.forEach((button) => button.addEventListener('click', () => moveNews(-1)));
      nextNewsButtons.forEach((button) => button.addEventListener('click', () => moveNews(1)));
      newsTrack.addEventListener('scroll', updateNewsControls, { passive: true });
      newsTrack.addEventListener('keydown', (event) => {
        if (event.target !== newsTrack || (event.key !== 'ArrowLeft' && event.key !== 'ArrowRight')) return;
        event.preventDefault();
        moveNews(event.key === 'ArrowRight' ? 1 : -1);
      });

      if ('ResizeObserver' in window) {
        new ResizeObserver(updateNewsControls).observe(newsTrack);
      } else {
        window.addEventListener('resize', updateNewsControls, { passive: true });
      }
      updateNewsControls();
    }

    navigation?.querySelectorAll('a[href^="#"]').forEach((link) => {
      link.addEventListener('click', (event) => {
        const id = link.getAttribute('href').slice(1);
        const target = id ? document.getElementById(id) : null;
        if (!target) return;

        const focusTarget = () => {
          if (!isVisible(target)) return;
          if (!target.hasAttribute('tabindex')) target.setAttribute('tabindex', '-1');
          target.focus({ preventScroll: true });
        };

        if (isMobileMenuOpen() && window.bootstrap?.Collapse) {
          event.preventDefault();
          navigation.addEventListener('hidden.bs.collapse', () => {
            if (!isVisible(target)) return;
            const hash = `#${id}`;
            if (window.location.hash !== hash) window.history.pushState(null, '', hash);
            target.scrollIntoView({
              behavior: reducedMotion.matches ? 'instant' : 'smooth',
              block: 'start',
            });
            focusTarget();
          }, { once: true });
          window.bootstrap.Collapse.getOrCreateInstance(navigation, { toggle: false }).hide();
        } else {
          window.requestAnimationFrame(focusTarget);
        }
      });
    });

    document.querySelectorAll('[data-current-year]').forEach((element) => {
      element.textContent = String(new Date().getFullYear());
    });
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initialize, { once: true });
  } else {
    initialize();
  }
})();
