/* Prefere as mídias públicas e mantém as cópias locais como alternativa. */
(() => {
  const fallbackImage = (image) => {
    const local = image.dataset.localSrc;
    if (!local || image.src === new URL(local, document.baseURI).href) return;
    image.removeAttribute('srcset');
    image.src = local;
  };

  const fallbackVideo = (video) => {
    const local = video.dataset.localSrc || video.querySelector('source[data-local-src]')?.dataset.localSrc;
    if (!local || video.src === new URL(local, document.baseURI).href) return;
    const shouldPlay = !video.paused;
    video.src = local;
    if (video.dataset.localPoster) video.poster = video.dataset.localPoster;
    video.load();
    if (shouldPlay) video.play().catch(() => {});
  };

  // Captura também falhas de imagens abertas depois, como as da galeria.
  document.addEventListener('error', (event) => {
    const element = event.target;
    if (element instanceof HTMLImageElement) fallbackImage(element);
    else if (element instanceof HTMLVideoElement) fallbackVideo(element);
    else if (element instanceof HTMLSourceElement && element.parentElement instanceof HTMLVideoElement) {
      fallbackVideo(element.parentElement);
    }
  }, true);

  const checkInitialImages = () => {
    document.querySelectorAll('img[data-local-src]').forEach((image) => {
      if (image.complete && !image.naturalWidth) fallbackImage(image);
    });
    document.querySelectorAll('video[data-local-poster]').forEach((video) => {
      const remote = video.poster;
      const poster = new Image();
      poster.addEventListener('error', () => {
        if (video.poster === remote) video.poster = video.dataset.localPoster;
      }, { once: true });
      poster.src = remote;
    });
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', checkInitialImages, { once: true });
  else checkInitialImages();
})();
