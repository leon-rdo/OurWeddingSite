// ============================================
// Script da Galeria - gallery.js
// ============================================

document.addEventListener("DOMContentLoaded", function () {
  const galleryGrid = document.querySelector(".gallery-grid");

  if (!galleryGrid) {
    return; // Não está na página da galeria
  }

  const galleryImages = document.querySelectorAll(".gallery-item");
  const modal = document.getElementById("imageModal");
  const modalImage = document.getElementById("modalImage");

  let currentImageIndex = 0;
  let bsModal;

  if (!modal || !modalImage) {
    console.error("Elementos do modal não encontrados");
    return;
  }

  // Inicializar modal do Bootstrap
  bsModal = new bootstrap.Modal(modal, {
    keyboard: true,
    backdrop: "static",
  });

  // ============================================
  // Abrir modal ao clicar em imagem
  // ============================================
  galleryImages.forEach((item, index) => {
    item.addEventListener("click", function () {
      openModal(index);
    });
  });

  // ============================================
  // Função para abrir modal
  // ============================================
  window.openModal = function (index) {
    currentImageIndex = index;
    updateModalImage();
    bsModal.show();
  };

  // ============================================
  // Atualizar imagem do modal
  // ============================================
  function updateModalImage() {
    if (galleryImages.length === 0) return;

    const currentItem = galleryImages[currentImageIndex];
    const img = currentItem.querySelector("img");

    if (img) {
      // Animação de fade out
      modalImage.style.opacity = "0";

      setTimeout(() => {
        modalImage.src = img.src;
        modalImage.alt = img.alt || "Imagem da galeria";

        // Animação de fade in
        modalImage.style.opacity = "1";
      }, 150);
    }
  }

  // ============================================
  // Navegação - Próxima imagem
  // ============================================
  window.nextImage = function () {
    currentImageIndex = (currentImageIndex + 1) % galleryImages.length;
    updateModalImage();
  };

  // ============================================
  // Navegação - Imagem anterior
  // ============================================
  window.previousImage = function () {
    currentImageIndex =
      (currentImageIndex - 1 + galleryImages.length) % galleryImages.length;
    updateModalImage();
  };

  // ============================================
  // Navegação por teclado
  // ============================================
  document.addEventListener("keydown", function (e) {
    if (!modal.classList.contains("show")) return;

    switch (e.key) {
      case "ArrowRight":
        e.preventDefault();
        nextImage();
        break;
      case "ArrowLeft":
        e.preventDefault();
        previousImage();
        break;
      case "Escape":
        e.preventDefault();
        bsModal.hide();
        break;
    }
  });

  // ============================================
  // Navegação por swipe (mobile)
  // ============================================
  let touchStartX = 0;
  let touchEndX = 0;

  modalImage.addEventListener(
    "touchstart",
    function (e) {
      touchStartX = e.changedTouches[0].screenX;
    },
    false
  );

  modalImage.addEventListener(
    "touchend",
    function (e) {
      touchEndX = e.changedTouches[0].screenX;
      handleSwipe();
    },
    false
  );

  function handleSwipe() {
    const swipeThreshold = 50;
    const diff = touchStartX - touchEndX;

    if (Math.abs(diff) > swipeThreshold) {
      if (diff > 0) {
        // Swipe left - próxima
        nextImage();
      } else {
        // Swipe right - anterior
        previousImage();
      }
    }
  }

  // ============================================
  // Estilo para transição suave
  // ============================================
  modalImage.style.transition = "opacity 0.3s ease";

  // ============================================
  // Lazy loading para imagens da galeria
  // ============================================
  if ("IntersectionObserver" in window) {
    const imageObserver = new IntersectionObserver(function (
      entries,
      observer
    ) {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          const img = entry.target.querySelector("img");
          if (img && img.dataset.src) {
            img.src = img.dataset.src;
            img.removeAttribute("data-src");
            entry.target.classList.add("loaded");
            observer.unobserve(entry.target);
          }
        }
      });
    });

    galleryImages.forEach((item) => {
      imageObserver.observe(item);
    });
  }

  // ============================================
  // Informações de navegação
  // ============================================
  function updateNavigationInfo() {
    if (galleryImages.length > 1) {
      console.log(`Imagem ${currentImageIndex + 1} de ${galleryImages.length}`);
    }
  }

  // ============================================
  // Event listener para quando o modal é mostrado
  // ============================================
  modal.addEventListener("shown.bs.modal", function () {
    updateNavigationInfo();
    // Focar no modal para capturar eventos de teclado
    modal.focus();
  });

  // ============================================
  // Limpar backdrop ao fechar
  // ============================================
  modal.addEventListener("hidden.bs.modal", function () {
    // Remover qualquer backdrop que possa ter ficado
    const backdrops = document.querySelectorAll(".modal-backdrop");
    backdrops.forEach((backdrop) => {
      backdrop.remove();
    });
    document.body.classList.remove("modal-open");
    document.body.style.overflow = "";
    document.body.style.paddingRight = "";
  });

  // ============================================
  // Preload de imagens adjacentes
  // ============================================
  function preloadAdjacentImages() {
    const nextIndex = (currentImageIndex + 1) % galleryImages.length;
    const prevIndex =
      (currentImageIndex - 1 + galleryImages.length) % galleryImages.length;

    [nextIndex, prevIndex].forEach((index) => {
      const img = galleryImages[index].querySelector("img");
      if (img && img.src) {
        const preloadImg = new Image();
        preloadImg.src = img.src;
      }
    });
  }

  // Preload ao mudar de imagem
  modal.addEventListener("shown.bs.modal", preloadAdjacentImages);

  console.log(`✨ Galeria inicializada com ${galleryImages.length} imagens`);
});
