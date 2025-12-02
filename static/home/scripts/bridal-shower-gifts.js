// ============================================
// Script do Chá de Panela - bridal-shower-gifts.js
// ============================================

document.addEventListener("DOMContentLoaded", function () {
  const giftsGrid = document.querySelector(".gifts-grid");

  if (!giftsGrid) {
    return; // Não está na página do chá de panela
  }

  // ============================================
  // Inicializar tooltips
  // ============================================
  var tooltipTriggerList = [].slice.call(
    document.querySelectorAll('[data-bs-toggle="tooltip"]')
  );
  tooltipTriggerList.forEach(function (tooltipTriggerEl) {
    new bootstrap.Tooltip(tooltipTriggerEl, {
      trigger: "hover",
    });
  });

  // ============================================
  // Gerenciar visibilidade do preço nos modais
  // ============================================
  var pickGiftModals = document.querySelectorAll('[id^="pickGift"]');

  pickGiftModals.forEach(function (modal) {
    var priceContainer = modal.querySelector(".price-container");

    if (priceContainer) {
      var wayToGiftRadios = modal.querySelectorAll('input[name="way_to_gift"]');

      function updatePriceVisibility() {
        var selectedRadio = modal.querySelector(
          'input[name="way_to_gift"]:checked'
        );
        if (selectedRadio && selectedRadio.value === "money") {
          priceContainer.style.display = "block";
        } else {
          priceContainer.style.display = "none";
        }
      }

      wayToGiftRadios.forEach(function (radio) {
        radio.addEventListener("change", updatePriceVisibility);
      });

      // Inicializar ao carregar
      updatePriceVisibility();
    }
  });

  // ============================================
  // Abrir modal PIX se houver parâmetro na URL
  // ============================================
  const urlParams = new URLSearchParams(window.location.search);
  const giftId = urlParams.get("gift");

  if (giftId) {
    const pixModalElement = document.getElementById("pix" + giftId);
    if (pixModalElement) {
      const pixModal = new bootstrap.Modal(pixModalElement);
      pixModal.show();

      // Scroll até o presente
      const giftCard = document.getElementById(giftId);
      if (giftCard) {
        setTimeout(() => {
          giftCard.scrollIntoView({ behavior: "smooth", block: "center" });
        }, 500);
      }
    }
  }

  // ============================================
  // Limpar backdrop ao fechar modais
  // ============================================
  document.addEventListener("hidden.bs.modal", function () {
    // Verificar se ainda há modais abertos
    if (!document.querySelector(".modal.show")) {
      document.body.classList.remove("modal-open");

      // Remover todos os backdrops
      var backdrops = document.querySelectorAll(".modal-backdrop");
      backdrops.forEach((backdrop) => backdrop.remove());

      // Restaurar scroll do body
      document.body.style.overflow = "";
      document.body.style.paddingRight = "";
    }
  });

  // ============================================
  // Navegação entre modais (botões Voltar)
  // ============================================
  var backButtons = document.querySelectorAll(
    '[data-bs-target][data-bs-toggle="modal"]'
  );

  backButtons.forEach((button) => {
    button.addEventListener("click", function (event) {
      const currentModalElement = this.closest(".modal");
      const currentModal = bootstrap.Modal.getInstance(currentModalElement);

      if (currentModal) {
        currentModal.hide();

        // Aguardar transição do modal atual
        setTimeout(() => {
          const targetModalElement = document.querySelector(
            this.getAttribute("data-bs-target")
          );
          if (targetModalElement) {
            const targetModal = new bootstrap.Modal(targetModalElement);
            targetModal.show();
          }
        }, 300);
      }
    });
  });

  // ============================================
  // Função para copiar código PIX
  // ============================================
  window.copyPixCode = function (giftId) {
    const input = document.getElementById("pixCode" + giftId);
    if (input) {
      input.select();
      input.setSelectionRange(0, 99999); // Para mobile

      // Tentar copiar usando a API moderna
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard
          .writeText(input.value)
          .then(() => {
            showToast("Código PIX copiado!", "success");
          })
          .catch((err) => {
            console.error("Erro ao copiar:", err);
            fallbackCopy(input);
          });
      } else {
        fallbackCopy(input);
      }
    }
  };

  // Fallback para navegadores antigos
  function fallbackCopy(input) {
    try {
      document.execCommand("copy");
      showToast("Código PIX copiado!", "success");
    } catch (err) {
      console.error("Erro ao copiar:", err);
      showToast("Erro ao copiar código", "error");
    }
  }

  // ============================================
  // Formatação automática de telefone
  // ============================================
  var phoneInputs = document.querySelectorAll(
    'input[type="tel"], input[name="phone_number"]'
  );

  phoneInputs.forEach((input) => {
    input.addEventListener("input", function (e) {
      let value = e.target.value.replace(/\D/g, "");

      // Limitar a 11 dígitos
      if (value.length > 11) {
        value = value.slice(0, 11);
      }

      // Formatar: (00) 00000-0000
      if (value.length > 6) {
        value = `(${value.slice(0, 2)}) ${value.slice(2, 7)}-${value.slice(7)}`;
      } else if (value.length > 2) {
        value = `(${value.slice(0, 2)}) ${value.slice(2)}`;
      } else if (value.length > 0) {
        value = `(${value}`;
      }

      e.target.value = value;
    });

    // Permitir apenas números e caracteres de formatação
    input.addEventListener("keypress", function (e) {
      const char = String.fromCharCode(e.which);
      if (!/[0-9]/.test(char)) {
        e.preventDefault();
      }
    });
  });

  // ============================================
  // Validação de formulários
  // ============================================
  const forms = document.querySelectorAll('form[method="POST"]');

  forms.forEach((form) => {
    form.addEventListener("submit", function (e) {
      // Validar campos obrigatórios
      const requiredFields = form.querySelectorAll("[required]");
      let isValid = true;

      requiredFields.forEach((field) => {
        if (!field.value.trim()) {
          isValid = false;
          field.classList.add("is-invalid");
        } else {
          field.classList.remove("is-invalid");
        }
      });

      if (!isValid) {
        e.preventDefault();
        showToast(
          "Por favor, preencha todos os campos obrigatórios",
          "warning"
        );
      }
    });
  });

  // ============================================
  // Animação ao carregar cards
  // ============================================
  const giftCards = document.querySelectorAll(".gift-card");

  if ("IntersectionObserver" in window) {
    const cardObserver = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.style.opacity = "0";
            entry.target.style.transform = "translateY(20px)";

            setTimeout(() => {
              entry.target.style.transition = "all 0.5s ease";
              entry.target.style.opacity = "1";
              entry.target.style.transform = "translateY(0)";
            }, 100);

            cardObserver.unobserve(entry.target);
          }
        });
      },
      {
        threshold: 0.1,
        rootMargin: "0px 0px -50px 0px",
      }
    );

    giftCards.forEach((card) => {
      cardObserver.observe(card);
    });
  }

  // ============================================
  // Filtrar presentes por categoria (se necessário)
  // ============================================
  window.filterGiftsByCategory = function (category) {
    const allCategories = document.querySelectorAll(".gift-card");

    allCategories.forEach((card) => {
      if (category === "all" || card.dataset.category === category) {
        card.style.display = "block";
      } else {
        card.style.display = "none";
      }
    });
  };

  // ============================================
  // Contador de presentes
  // ============================================
  function updateGiftCounter() {
    const totalGifts = document.querySelectorAll(".gift-card").length;
    const reservedGifts = document.querySelectorAll(".badge-paid").length;
    const availableGifts = totalGifts - reservedGifts;

    console.log(
      `📊 Presentes: ${totalGifts} total, ${reservedGifts} reservados, ${availableGifts} disponíveis`
    );
  }

  updateGiftCounter();

  // ============================================
  // Prevenir múltiplos submits
  // ============================================
  const submitButtons = document.querySelectorAll('button[type="submit"]');

  submitButtons.forEach((button) => {
    button.addEventListener("click", function () {
      if (this.disabled) return;

      const form = this.closest("form");
      if (form && form.checkValidity()) {
        this.disabled = true;
        this.innerHTML =
          '<span class="spinner-border spinner-border-sm me-2"></span>Enviando...';

        // Re-habilitar após 3 segundos (caso falhe)
        setTimeout(() => {
          this.disabled = false;
          this.innerHTML = this.dataset.originalText || "Confirmar";
        }, 3000);
      }
    });
  });

  // ============================================
  // Destacar presente na URL
  // ============================================
  if (window.location.hash) {
    const targetId = window.location.hash.substring(1);
    const targetElement = document.getElementById(targetId);

    if (targetElement) {
      setTimeout(() => {
        targetElement.scrollIntoView({ behavior: "smooth", block: "center" });
        targetElement.classList.add("highlight");

        setTimeout(() => {
          targetElement.classList.remove("highlight");
        }, 2000);
      }, 500);
    }
  }

  // Adicionar estilo para highlight
  const style = document.createElement("style");
  style.textContent = `
        .gift-card.highlight {
            animation: pulse 1s ease-in-out 2;
            box-shadow: 0 0 30px rgba(197, 157, 168, 0.6) !important;
        }
        @keyframes pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.02); }
        }
    `;
  document.head.appendChild(style);

  console.log("✨ Chá de panela inicializado com sucesso!");
});
