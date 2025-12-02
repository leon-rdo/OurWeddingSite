// ============================================
// Scripts principais do site
// ============================================

document.addEventListener("DOMContentLoaded", function () {
  // ============================================
  // Loader de imagens
  // ============================================
  var images = document.images,
    totalImages = images.length,
    imagesLoaded = 0;

  function imageLoaded() {
    imagesLoaded++;
    if (imagesLoaded === totalImages) {
      hideLoader();
    }
  }

  function hideLoader() {
    document.getElementById("loader").style.display = "none";
    document.getElementById("page-content").style.display = "block";
  }

  // Se não houver imagens, mostra conteúdo imediatamente
  if (totalImages === 0) {
    hideLoader();
  } else {
    for (var i = 0; i < totalImages; i++) {
      if (images[i].complete) {
        imageLoaded();
      } else {
        images[i].addEventListener("load", imageLoaded);
        images[i].addEventListener("error", imageLoaded);
      }
    }
  }

  // Timeout de segurança - 5 segundos
  setTimeout(hideLoader, 5000);

  // ============================================
  // Controle de áudio de fundo
  // ============================================
  var audio = document.getElementById("background-audio");
  if (audio) {
    audio.volume = 0.5;
    var button = document.getElementById("audio-control-button");

    function updateButton() {
      if (audio.paused) {
        button.innerHTML = '<i class="bi bi-play-fill"></i>';
        button.setAttribute("aria-label", "Reproduzir música");
      } else {
        button.innerHTML = '<i class="bi bi-pause-fill"></i>';
        button.setAttribute("aria-label", "Pausar música");
      }
    }

    button.addEventListener("click", function () {
      if (audio.paused) {
        audio
          .play()
          .catch((error) => console.log("Autoplay bloqueado:", error));
      } else {
        audio.pause();
      }
      updateButton();
    });

    // Tentar reproduzir automaticamente
    audio.play().catch(() => {
      console.log("Autoplay bloqueado. Aguardando interação.");
    });

    updateButton();

    // Reproduzir após primeira interação
    document.addEventListener(
      "click",
      function () {
        if (audio.paused) {
          audio.play();
          updateButton();
        }
      },
      { once: true }
    );
  }

  // ============================================
  // Inicializar tooltips do Bootstrap
  // ============================================
  var tooltipTriggerList = [].slice.call(
    document.querySelectorAll('[data-bs-toggle="tooltip"]')
  );
  tooltipTriggerList.forEach(function (tooltipTriggerEl) {
    new bootstrap.Tooltip(tooltipTriggerEl);
  });

  // ============================================
  // Auto-dismiss alerts
  // ============================================
  var alerts = document.querySelectorAll(".alert:not(.alert-permanent)");
  alerts.forEach(function (alert) {
    setTimeout(function () {
      var bsAlert = new bootstrap.Alert(alert);
      bsAlert.close();
    }, 5000);
  });

  // ============================================
  // Smooth scroll
  // ============================================
  document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
    anchor.addEventListener("click", function (e) {
      const targetId = this.getAttribute("href");
      if (targetId !== "#" && targetId !== "#!") {
        e.preventDefault();
        const target = document.querySelector(targetId);
        if (target) {
          target.scrollIntoView({
            behavior: "smooth",
            block: "start",
          });
        }
      }
    });
  });
});

// ============================================
// Função para copiar para clipboard
// ============================================
function copyToClipboard(text) {
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard
      .writeText(text)
      .then(function () {
        showToast("Copiado com sucesso!", "success");
      })
      .catch(function (err) {
        console.error("Erro ao copiar:", err);
        fallbackCopyToClipboard(text);
      });
  } else {
    fallbackCopyToClipboard(text);
  }
}

// Fallback para navegadores antigos
function fallbackCopyToClipboard(text) {
  var textArea = document.createElement("textarea");
  textArea.value = text;
  textArea.style.position = "fixed";
  textArea.style.top = 0;
  textArea.style.left = 0;
  textArea.style.opacity = 0;
  document.body.appendChild(textArea);
  textArea.focus();
  textArea.select();

  try {
    document.execCommand("copy");
    showToast("Copiado com sucesso!", "success");
  } catch (err) {
    console.error("Erro ao copiar:", err);
    showToast("Erro ao copiar", "error");
  }

  document.body.removeChild(textArea);
}

// ============================================
// Sistema de notificações toast
// ============================================
function showToast(message, type = "info") {
  // Remove toasts antigos
  var oldToasts = document.querySelectorAll(".custom-toast");
  oldToasts.forEach((toast) => toast.remove());

  var toast = document.createElement("div");
  toast.className = "custom-toast custom-toast-" + type;
  toast.innerHTML =
    '<i class="bi bi-' + getToastIcon(type) + '"></i> ' + message;

  document.body.appendChild(toast);

  setTimeout(() => toast.classList.add("show"), 10);

  setTimeout(() => {
    toast.classList.remove("show");
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

function getToastIcon(type) {
  const icons = {
    success: "check-circle-fill",
    error: "x-circle-fill",
    warning: "exclamation-triangle-fill",
    info: "info-circle-fill",
  };
  return icons[type] || "info-circle-fill";
}

// Estilos para toast
var toastStyles = document.createElement("style");
toastStyles.textContent = `
    .custom-toast {
        position: fixed;
        bottom: 20px;
        right: 20px;
        padding: 1rem 1.5rem;
        background: white;
        border-radius: 10px;
        box-shadow: 0 5px 20px rgba(0,0,0,0.2);
        z-index: 9999;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-weight: 600;
        opacity: 0;
        transform: translateY(20px);
        transition: all 0.3s ease;
    }
    .custom-toast.show {
        opacity: 1;
        transform: translateY(0);
    }
    .custom-toast-success {
        border-left: 4px solid #28a745;
        color: #28a745;
    }
    .custom-toast-error {
        border-left: 4px solid #dc3545;
        color: #dc3545;
    }
    .custom-toast-warning {
        border-left: 4px solid #ffc107;
        color: #856404;
    }
    .custom-toast-info {
        border-left: 4px solid #17a2b8;
        color: #17a2b8;
    }
    @media (max-width: 576px) {
        .custom-toast {
            bottom: 10px;
            right: 10px;
            left: 10px;
        }
    }
`;
document.head.appendChild(toastStyles);

// ============================================
// Animações de scroll
// ============================================
if ("IntersectionObserver" in window) {
  const observerOptions = {
    threshold: 0.1,
    rootMargin: "0px 0px -50px 0px",
  };

  const observer = new IntersectionObserver(function (entries) {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add("animated");
        observer.unobserve(entry.target);
      }
    });
  }, observerOptions);

  document.querySelectorAll(".animate-on-scroll").forEach((el) => {
    observer.observe(el);
  });
}

// ============================================
// Log inicial
// ============================================
console.log(
  "%c🎉 Site carregado com sucesso!",
  "color: #c59da8; font-size: 16px; font-weight: bold;"
);
