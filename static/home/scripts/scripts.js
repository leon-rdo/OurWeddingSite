// ============================================
// Scripts principais do site - VERSÃO 2.0
// Sistema anti-duplo clique e loading states
// ============================================

document.addEventListener("DOMContentLoaded", function () {
  // ============================================
  // SISTEMA ANTI-DUPLO CLIQUE
  // ============================================

  /**
   * Classe para gerenciar estado de loading de botões
   */
  class ButtonLoadingManager {
    constructor() {
      this.activeButtons = new Map();
      this.init();
    }

    init() {
      // Interceptar todos os formulários
      this.setupFormSubmitHandlers();

      // Interceptar botões que fazem requisições AJAX
      this.setupAjaxButtonHandlers();

      // Prevenir múltiplos cliques em links de ação
      this.setupActionLinkHandlers();

      console.log('✅ Sistema anti-duplo clique inicializado');
    }

    /**
     * Desabilita botão e mostra loading
     */
    disableButton(button, originalText = null) {
      if (!button) return;

      // Salvar estado original
      const buttonId = this.getButtonId(button);

      if (!this.activeButtons.has(buttonId)) {
        this.activeButtons.set(buttonId, {
          originalText: originalText || button.innerHTML,
          originalDisabled: button.disabled,
          timestamp: Date.now()
        });
      }

      // Desabilitar botão
      button.disabled = true;
      button.style.opacity = '0.6';
      button.style.cursor = 'not-allowed';

      // Adicionar spinner
      const hasSpinner = button.querySelector('.btn-spinner');
      if (!hasSpinner) {
        const spinner = document.createElement('span');
        spinner.className = 'btn-spinner spinner-border spinner-border-sm me-2';
        spinner.setAttribute('role', 'status');
        spinner.setAttribute('aria-hidden', 'true');

        button.insertBefore(spinner, button.firstChild);
      }

      // Atualizar texto se fornecido
      const textNode = Array.from(button.childNodes).find(
        node => node.nodeType === Node.TEXT_NODE
      );

      if (textNode) {
        textNode.textContent = ' Processando...';
      }

      console.log(`🔒 Botão bloqueado: ${buttonId}`);
    }

    /**
     * Re-habilita botão
     */
    enableButton(button, delay = 0) {
      if (!button) return;

      const buttonId = this.getButtonId(button);
      const savedState = this.activeButtons.get(buttonId);

      setTimeout(() => {
        // Remover spinner
        const spinner = button.querySelector('.btn-spinner');
        if (spinner) {
          spinner.remove();
        }

        // Restaurar estado original
        if (savedState) {
          button.innerHTML = savedState.originalText;
          button.disabled = savedState.originalDisabled;
        } else {
          button.disabled = false;
        }

        button.style.opacity = '';
        button.style.cursor = '';

        this.activeButtons.delete(buttonId);
        console.log(`🔓 Botão liberado: ${buttonId}`);
      }, delay);
    }

    /**
     * Gera ID único para botão
     */
    getButtonId(button) {
      if (button.id) return button.id;
      if (button.name) return button.name;

      // Gerar ID baseado em posição no DOM
      const form = button.closest('form');
      const index = Array.from(
        (form || document).querySelectorAll('button, input[type="submit"]')
      ).indexOf(button);

      return `btn_${form?.id || 'global'}_${index}`;
    }

    /**
     * Verifica se botão está bloqueado
     */
    isButtonLocked(button) {
      const buttonId = this.getButtonId(button);
      return this.activeButtons.has(buttonId);
    }

    /**
     * Setup para formulários regulares
     */
    setupFormSubmitHandlers() {
      document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', (e) => {
          const submitButton = form.querySelector('button[type="submit"], input[type="submit"]');

          if (submitButton && !this.isButtonLocked(submitButton)) {
            // Validar formulário antes de bloquear
            if (!form.checkValidity()) {
              return; // Deixar HTML5 validation funcionar
            }

            this.disableButton(submitButton);

            // Se for AJAX, não fazer nada mais
            // Se for submit normal, será re-habilitado no page load
            if (!form.hasAttribute('data-ajax')) {
              // Timeout de segurança para submits normais
              setTimeout(() => {
                this.enableButton(submitButton);
              }, 30000); // 30 segundos
            }
          }
        });

        // Re-habilitar em caso de erro de validação
        form.addEventListener('invalid', (e) => {
          const submitButton = form.querySelector('button[type="submit"], input[type="submit"]');
          if (submitButton) {
            this.enableButton(submitButton, 500);
          }
        }, true);
      });
    }

    /**
     * Setup para botões AJAX
     */
    setupAjaxButtonHandlers() {
      document.querySelectorAll('[data-ajax-action]').forEach(button => {
        button.addEventListener('click', (e) => {
          if (this.isButtonLocked(button)) {
            e.preventDefault();
            e.stopPropagation();
            return false;
          }

          this.disableButton(button);

          // Auto re-habilitar após timeout (safety)
          setTimeout(() => {
            if (this.isButtonLocked(button)) {
              this.enableButton(button);
              console.warn('⚠️ Botão desbloqueado por timeout de segurança');
            }
          }, 15000); // 15 segundos
        });
      });
    }

    /**
     * Setup para links de ação
     */
    setupActionLinkHandlers() {
      document.querySelectorAll('a[data-action]').forEach(link => {
        link.addEventListener('click', (e) => {
          if (this.isButtonLocked(link)) {
            e.preventDefault();
            e.stopPropagation();
            return false;
          }

          this.disableButton(link);
        });
      });
    }

    /**
     * Limpar botões órfãos (com mais de 30s)
     */
    cleanupOrphanedButtons() {
      const now = Date.now();
      const timeout = 30000; // 30 segundos

      this.activeButtons.forEach((state, buttonId) => {
        if (now - state.timestamp > timeout) {
          console.warn(`⚠️ Limpando botão órfão: ${buttonId}`);

          // Tentar encontrar o botão
          const button = document.getElementById(buttonId) ||
            document.querySelector(`[name="${buttonId}"]`);

          if (button) {
            this.enableButton(button);
          } else {
            this.activeButtons.delete(buttonId);
          }
        }
      });
    }
  }

  // Instância global
  window.buttonManager = new ButtonLoadingManager();

  // Cleanup periódico
  setInterval(() => {
    window.buttonManager.cleanupOrphanedButtons();
  }, 10000); // A cada 10 segundos

  // ============================================
  // API PÚBLICA PARA OUTROS SCRIPTS
  // ============================================

  /**
   * Desabilitar botão manualmente
   * Uso: window.disableButton(button);
   */
  window.disableButton = function (button) {
    window.buttonManager.disableButton(button);
  };

  /**
   * Habilitar botão manualmente
   * Uso: window.enableButton(button);
   */
  window.enableButton = function (button, delay = 0) {
    window.buttonManager.enableButton(button, delay);
  };

  /**
   * Verificar se botão está bloqueado
   * Uso: if (window.isButtonLocked(button)) { ... }
   */
  window.isButtonLocked = function (button) {
    return window.buttonManager.isButtonLocked(button);
  };

  // ============================================
  // Loader de imagens (código original mantido)
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
    const loader = document.getElementById("loader");
    const content = document.getElementById("page-content");

    if (loader) loader.style.display = "none";
    if (content) content.style.display = "block";
  }

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

  setTimeout(hideLoader, 5000);

  // ============================================
  // Controle de áudio de fundo (código original mantido)
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
        audio.play().catch((error) => console.log("Autoplay bloqueado:", error));
      } else {
        audio.pause();
      }
      updateButton();
    });

    audio.play().catch(() => {
      console.log("Autoplay bloqueado. Aguardando interação.");
    });

    updateButton();

    document.addEventListener("click", function () {
      if (audio.paused) {
        audio.play();
        updateButton();
      }
    }, { once: true });
  }

  // ============================================
  // Tooltips Bootstrap
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
// Função para copiar para clipboard (mantida)
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
// Sistema de notificações toast (mantido)
// ============================================
function showToast(message, type = "info") {
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

// Estilos para toast (mantido)
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
    
    /* Estilos para spinner de botão */
    .btn-spinner {
        display: inline-block;
        vertical-align: middle;
    }
`;
document.head.appendChild(toastStyles);

// ============================================
// Animações de scroll (mantido)
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