/* ============================================
   GIFT LIST PAYMENTS v2.0
   Sistema de pagamentos para lista de presentes
   ============================================ */

(function () {
  "use strict";

  // Configurações globais
  const CONFIG = window.GIFT_LIST_CONFIG || {};
  let mp = null;
  const paymentMethodData = {};

  /**
   * Inicializa o Mercado Pago
   */
  function initMercadoPago() {
    if (!CONFIG.mercadoPagoPublicKey) {
      console.error("❌ Chave pública do Mercado Pago não configurada");
      return;
    }

    mp = new MercadoPago(CONFIG.mercadoPagoPublicKey, {
      locale: "pt-BR",
    });

    console.log("✅ Mercado Pago inicializado");
  }

  /**
   * Configura os listeners para seleção de método de pagamento
   */
  function setupPaymentMethodSelection() {
    document
      .querySelectorAll(".payment-options")
      .forEach((optionsContainer) => {
        const giftId = optionsContainer.dataset.giftId;
        const options = optionsContainer.querySelectorAll(".payment-option");

        options.forEach((option) => {
          option.addEventListener("click", function () {
            const method = this.dataset.paymentMethod;

            // Remove active de todas as opções deste presente
            options.forEach((opt) => opt.classList.remove("active"));

            // Adiciona active na opção clicada
            this.classList.add("active");

            // Mostra/esconde containers de pagamento
            const cardContainer = document.querySelector(
              `.card-payment-container[data-gift-id="${giftId}"]`
            );
            const pixContainer = document.querySelector(
              `.pix-payment-container[data-gift-id="${giftId}"]`
            );

            if (method === "card") {
              if (cardContainer) cardContainer.style.display = "block";
              if (pixContainer) pixContainer.style.display = "none";
            } else if (method === "pix") {
              if (cardContainer) cardContainer.style.display = "none";
              if (pixContainer) pixContainer.style.display = "block";
            }
          });
        });
      });
  }

  /**
   * Configura o botão de copiar código PIX
   */
  function setupPixCopyButtons() {
    document.querySelectorAll(".btn-copy-pix").forEach((button) => {
      button.addEventListener("click", function () {
        const pixCode = this.dataset.pixCode;

        if (!pixCode) {
          alert("Código PIX não disponível");
          return;
        }

        // Tentar usar a Clipboard API moderna
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard
            .writeText(pixCode)
            .then(() => {
              showPixCopyFeedback(this);
            })
            .catch((err) => {
              console.error("Erro ao copiar:", err);
              fallbackCopyPixCode(this);
            });
        } else {
          fallbackCopyPixCode(this);
        }
      });
    });
  }

  /**
   * Mostra feedback visual de cópia do PIX
   */
  function showPixCopyFeedback(button) {
    const originalHTML = button.innerHTML;
    button.innerHTML = '<i class="bi bi-check-circle-fill"></i> Copiado!';
    button.style.background = "#28a745";

    setTimeout(() => {
      button.innerHTML = originalHTML;
      button.style.background = "";
    }, 2000);
  }

  /**
   * Fallback para copiar código PIX em navegadores antigos
   */
  function fallbackCopyPixCode(button) {
    const input = button
      .closest(".pix-code-wrapper")
      .querySelector(".pix-code-input");

    if (input) {
      input.select();
      input.setSelectionRange(0, 99999); // Para mobile

      try {
        document.execCommand("copy");
        showPixCopyFeedback(button);
      } catch (err) {
        alert(
          "Não foi possível copiar automaticamente. Por favor, copie manualmente o código."
        );
      }
    }
  }

  /**
   * Formata número de cartão com espaços
   */
  function formatCardNumber(value) {
    const cleaned = value.replace(/\s/g, "");
    const chunks = cleaned.match(/.{1,4}/g);
    return chunks ? chunks.join(" ") : cleaned;
  }

  /**
   * Configura formatação de inputs do cartão
   */
  function setupCardInputFormatting(form) {
    const cardNumberInput = form.querySelector(".card-number");

    if (cardNumberInput) {
      cardNumberInput.addEventListener("input", function (e) {
        const cursorPosition = this.selectionStart;
        const oldValue = this.value;
        const newValue = formatCardNumber(this.value.replace(/\s/g, ""));

        this.value = newValue;

        // Ajustar posição do cursor após formatação
        if (newValue.length > oldValue.length) {
          const newCursorPosition =
            cursorPosition + (newValue.length - oldValue.length);
          this.setSelectionRange(newCursorPosition, newCursorPosition);
        }
      });
    }
  }

  /**
   * Busca informações do cartão (bandeira, parcelas, etc)
   */
  async function getCardInfo(form, giftId) {
    const cardNumberInput = form.querySelector(".card-number");
    const installmentsSelect = form.querySelector(".installments-select");
    const priceInput = form.querySelector('[name="gift_price"]');

    if (!cardNumberInput || !installmentsSelect || !priceInput) {
      console.error("Elementos do formulário não encontrados");
      return;
    }

    const cardNumber = cardNumberInput.value.replace(/\s/g, "");

    if (cardNumber.length < 6) {
      return;
    }

    try {
      const bin = cardNumber.substring(0, 6);
      const giftPrice = parseFloat(priceInput.value);

      // Buscar método de pagamento
      const paymentMethods = await mp.getPaymentMethods({ bin });

      if (paymentMethods.results && paymentMethods.results.length > 0) {
        const method = paymentMethods.results[0];

        // Armazenar dados do método de pagamento
        if (!paymentMethodData[giftId]) {
          paymentMethodData[giftId] = {};
        }

        paymentMethodData[giftId].payment_method_id = method.id;

        // Buscar emissor se necessário
        if (
          method.additional_info_needed &&
          method.additional_info_needed.includes("issuer_id")
        ) {
          const issuers = await mp.getIssuers({
            paymentMethodId: method.id,
            bin: bin,
          });

          if (issuers && issuers.length > 0) {
            paymentMethodData[giftId].issuer_id = issuers[0].id;
          }
        }

        // Buscar opções de parcelamento
        const installments = await mp.getInstallments({
          amount: giftPrice.toString(),
          bin: bin,
        });

        // Limpar e popular select de parcelas
        installmentsSelect.innerHTML = '<option value="">Selecione...</option>';

        if (installments && installments[0] && installments[0].payer_costs) {
          installments[0].payer_costs.forEach((option) => {
            const optElement = document.createElement("option");
            optElement.value = option.installments;

            let text = `${
              option.installments
            }x de R$ ${option.installment_amount.toFixed(2)}`;
            if (option.installment_rate === 0) {
              text += " sem juros";
            }

            optElement.textContent = text;
            installmentsSelect.appendChild(optElement);
          });
        }
      }
    } catch (error) {
      console.error("Erro ao buscar informações do cartão:", error);
    }
  }

  /**
   * Processa o pagamento com cartão
   */
  async function processCardPayment(form, giftId) {
    const errorDiv = form.querySelector(".error-message");
    const successDiv = form.querySelector(".success-message");
    const submitBtn = form.querySelector(".btn-submit");
    const spinner = submitBtn.querySelector(".spinner-border");
    const btnText = submitBtn.querySelector(".btn-text");

    // Limpar mensagens anteriores
    if (errorDiv) {
      errorDiv.style.display = "none";
      errorDiv.textContent = "";
    }
    if (successDiv) {
      successDiv.style.display = "none";
      successDiv.textContent = "";
    }

    // Mostrar loading
    submitBtn.disabled = true;
    if (spinner) spinner.style.display = "inline-block";
    if (btnText) btnText.textContent = "Processando...";

    try {
      // Verificar se temos os dados do método de pagamento
      if (
        !paymentMethodData[giftId] ||
        !paymentMethodData[giftId].payment_method_id
      ) {
        throw new Error("Por favor, verifique o número do cartão");
      }

      // Criar token do cartão
      const cardData = {
        cardNumber: form.querySelector(".card-number").value.replace(/\s/g, ""),
        cardholderName: form.querySelector(".card-holder").value,
        cardExpirationMonth: form.querySelector(".card-month").value,
        cardExpirationYear: form.querySelector(".card-year").value,
        securityCode: form.querySelector(".card-cvv").value,
        identificationType: form.querySelector(".doc-type").value,
        identificationNumber: form.querySelector(".doc-number").value,
      };

      const token = await mp.createCardToken(cardData);

      if (!token || !token.id) {
        throw new Error("Erro ao processar dados do cartão");
      }

      // Enviar pagamento para o servidor
      const paymentData = {
        gift_id: giftId,
        gift_type: "gift",
        token: token.id,
        payment_method_id: paymentMethodData[giftId].payment_method_id,
        issuer_id: paymentMethodData[giftId].issuer_id,
        installments: form.querySelector(".installments-select").value,
        payer_name: form.querySelector(".payer-name").value,
        email: form.querySelector(".payer-email").value,
        identification_type: form.querySelector(".doc-type").value,
        identification_number: form.querySelector(".doc-number").value,
      };

      const response = await fetch(CONFIG.processPaymentUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": CONFIG.csrfToken,
        },
        body: JSON.stringify(paymentData),
      });

      const result = await response.json();

      if (result.status === "success") {
        const statusDetail = result.status_detail;

        if (statusDetail === "approved" || statusDetail === "accredited") {
          if (successDiv) {
            successDiv.textContent = "✓ Pagamento aprovado! Redirecionando...";
            successDiv.style.display = "block";
          }

          setTimeout(() => {
            window.location.href = `${CONFIG.paymentSuccessUrl}?payment_id=${result.payment_id}`;
          }, 2000);
        } else if (
          statusDetail === "pending" ||
          statusDetail === "in_process"
        ) {
          if (successDiv) {
            successDiv.textContent =
              "⏳ Pagamento em análise... Redirecionando...";
            successDiv.style.display = "block";
          }

          setTimeout(() => {
            window.location.href = `${CONFIG.paymentPendingUrl}?payment_id=${result.payment_id}`;
          }, 2000);
        } else {
          setTimeout(() => {
            window.location.href = `${
              CONFIG.paymentFailureUrl
            }?status_detail=${encodeURIComponent(statusDetail)}`;
          }, 1000);
        }
      } else {
        throw new Error(result.message || "Erro ao processar pagamento");
      }
    } catch (error) {
      console.error("Erro no pagamento:", error);

      if (errorDiv) {
        errorDiv.textContent =
          error.message || "Erro ao processar pagamento. Tente novamente.";
        errorDiv.style.display = "block";
      }

      // Restaurar botão
      submitBtn.disabled = false;
      if (spinner) spinner.style.display = "none";
      if (btnText) btnText.textContent = "Finalizar Pagamento";
    }
  }

  /**
   * Configura os formulários de pagamento
   */
  function setupPaymentForms() {
    document.querySelectorAll(".payment-form").forEach((form) => {
      const giftId = form.dataset.giftId;

      if (!giftId) {
        console.error("Form sem gift ID:", form);
        return;
      }

      // Configurar formatação de inputs
      setupCardInputFormatting(form);

      // Buscar informações do cartão ao sair do campo
      const cardNumberInput = form.querySelector(".card-number");
      if (cardNumberInput) {
        cardNumberInput.addEventListener("blur", function () {
          getCardInfo(form, giftId);
        });
      }

      // Processar submit do formulário
      form.addEventListener("submit", async function (e) {
        e.preventDefault();
        await processCardPayment(form, giftId);
      });
    });
  }

  /**
   * Inicialização principal
   */
  function init() {
    console.log("🎁 Iniciando sistema de pagamentos...");

    // Inicializar Mercado Pago
    initMercadoPago();

    // Configurar seleção de método de pagamento
    setupPaymentMethodSelection();

    // Configurar botões de copiar PIX
    setupPixCopyButtons();

    // Configurar formulários de pagamento
    setupPaymentForms();

    console.log("✅ Sistema de pagamentos inicializado");
  }

  // Inicializar quando o DOM estiver pronto
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
