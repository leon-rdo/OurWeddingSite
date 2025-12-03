/* ============================================
   GIFT LIST PAYMENTS v3.0
   Sistema de pagamentos com anti-duplo clique
   ============================================ */

(function () {
  "use strict";

  const CONFIG = window.GIFT_LIST_CONFIG || {};
  let mp = null;
  const paymentMethodData = {};
  const processingPayments = new Set(); // Rastrear pagamentos em processo

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
    document.querySelectorAll(".payment-options").forEach((optionsContainer) => {
      const giftId = optionsContainer.dataset.giftId;
      const options = optionsContainer.querySelectorAll(".payment-option");

      options.forEach((option) => {
        option.addEventListener("click", function () {
          const method = this.dataset.paymentMethod;

          options.forEach((opt) => opt.classList.remove("active"));
          this.classList.add("active");

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
          showToast("Código PIX não disponível", "error");
          return;
        }

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
   * Fallback para copiar código PIX
   */
  function fallbackCopyPixCode(button) {
    const input = button
      .closest(".pix-code-wrapper")
      .querySelector(".pix-code-input");

    if (input) {
      input.select();
      input.setSelectionRange(0, 99999);

      try {
        document.execCommand("copy");
        showPixCopyFeedback(button);
      } catch (err) {
        showToast("Não foi possível copiar. Copie manualmente.", "warning");
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

        if (newValue.length > oldValue.length) {
          const newCursorPosition =
            cursorPosition + (newValue.length - oldValue.length);
          this.setSelectionRange(newCursorPosition, newCursorPosition);
        }
      });
    }
  }

  /**
   * Busca informações do cartão
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

      const paymentMethods = await mp.getPaymentMethods({ bin });

      if (paymentMethods.results && paymentMethods.results.length > 0) {
        const method = paymentMethods.results[0];

        if (!paymentMethodData[giftId]) {
          paymentMethodData[giftId] = {};
        }

        paymentMethodData[giftId].payment_method_id = method.id;

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

        const installments = await mp.getInstallments({
          amount: giftPrice.toString(),
          bin: bin,
        });

        installmentsSelect.innerHTML = '<option value="">Selecione...</option>';

        if (installments && installments[0] && installments[0].payer_costs) {
          installments[0].payer_costs.forEach((option) => {
            const optElement = document.createElement("option");
            optElement.value = option.installments;

            let text = `${option.installments}x de R$ ${option.installment_amount.toFixed(2)}`;
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
   * ATUALIZADO: Com prevenção de duplo clique
   */
  async function processCardPayment(form, giftId) {
    // NOVO: Verificar se já está processando este presente
    if (processingPayments.has(giftId)) {
      console.warn('⚠️ Pagamento já está sendo processado para este presente');
      return;
    }

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

    // NOVO: Marcar como processando
    processingPayments.add(giftId);

    // NOVO: Usar sistema global de desabilitar botão
    if (window.buttonManager) {
      window.buttonManager.disableButton(submitBtn);
    } else {
      // Fallback se sistema global não estiver disponível
      submitBtn.disabled = true;
      if (spinner) spinner.style.display = "inline-block";
      if (btnText) btnText.textContent = "Processando...";
    }

    try {
      // Verificar dados do método de pagamento
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

        if (successDiv) {
          successDiv.style.display = "block";
        }

        if (statusDetail === "approved" || statusDetail === "accredited") {
          if (successDiv) {
            successDiv.textContent = "✓ Pagamento aprovado! Redirecionando...";
          }

          setTimeout(() => {
            window.location.href = `${CONFIG.paymentSuccessUrl}?payment_id=${result.payment_id}`;
          }, 2000);
        } else if (
          statusDetail === "pending" ||
          statusDetail === "in_process"
        ) {
          if (successDiv) {
            successDiv.textContent = "⏳ Pagamento em análise... Redirecionando...";
          }

          setTimeout(() => {
            window.location.href = `${CONFIG.paymentPendingUrl}?payment_id=${result.payment_id}`;
          }, 2000);
        } else {
          // NOVO: Limpar processamento antes de redirecionar para erro
          processingPayments.delete(giftId);

          setTimeout(() => {
            window.location.href = `${CONFIG.paymentFailureUrl}?status_detail=${encodeURIComponent(statusDetail)}`;
          }, 1000);
        }
      } else {
        throw new Error(result.message || "Erro ao processar pagamento");
      }
    } catch (error) {
      console.error("Erro no pagamento:", error);

      // NOVO: Remover do set de processamento
      processingPayments.delete(giftId);

      if (errorDiv) {
        errorDiv.textContent =
          error.message || "Erro ao processar pagamento. Tente novamente.";
        errorDiv.style.display = "block";
      }

      // NOVO: Re-habilitar botão usando sistema global
      if (window.buttonManager) {
        window.buttonManager.enableButton(submitBtn, 500);
      } else {
        // Fallback
        setTimeout(() => {
          submitBtn.disabled = false;
          if (spinner) spinner.style.display = "none";
          if (btnText) btnText.textContent = "Finalizar Pagamento";
        }, 500);
      }

      // Scroll para o erro
      errorDiv.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  }

  /**
   * Configura os formulários de pagamento
   * ATUALIZADO: Com prevenção de duplo submit
   */
  function setupPaymentForms() {
    document.querySelectorAll(".payment-form").forEach((form) => {
      const giftId = form.dataset.giftId;

      if (!giftId) {
        console.error("Form sem gift ID:", form);
        return;
      }

      // Marcar como AJAX para o sistema global
      form.setAttribute('data-ajax', 'true');

      // Configurar formatação de inputs
      setupCardInputFormatting(form);

      // Buscar informações do cartão
      const cardNumberInput = form.querySelector(".card-number");
      if (cardNumberInput) {
        cardNumberInput.addEventListener("blur", function () {
          getCardInfo(form, giftId);
        });
      }

      // ATUALIZADO: Submit com prevenção de duplo clique
      form.addEventListener("submit", async function (e) {
        e.preventDefault();
        e.stopPropagation();

        // Verificar se já está processando
        if (processingPayments.has(giftId)) {
          console.warn('⚠️ Aguarde o processamento do pagamento atual');
          showToast('Aguarde o processamento do pagamento', 'warning');
          return false;
        }

        // Validar formulário
        if (!form.checkValidity()) {
          form.reportValidity();
          return false;
        }

        await processCardPayment(form, giftId);
      });
    });
  }

  /**
   * Limpa formulário após sucesso
   */
  function clearForm(form) {
    if (!form) return;

    // Resetar formulário
    form.reset();

    // Limpar mensagens
    const errorDiv = form.querySelector(".error-message");
    const successDiv = form.querySelector(".success-message");

    if (errorDiv) errorDiv.style.display = "none";
    if (successDiv) successDiv.style.display = "none";

    // Resetar select de parcelas
    const installmentsSelect = form.querySelector(".installments-select");
    if (installmentsSelect) {
      installmentsSelect.innerHTML = '<option value="">Selecione...</option>';
    }

    console.log('🧹 Formulário limpo');
  }

  /**
   * Inicialização principal
   */
  function init() {
    console.log("🎁 Iniciando sistema de pagamentos v3.0...");

    initMercadoPago();
    setupPaymentMethodSelection();
    setupPixCopyButtons();
    setupPaymentForms();

    // Limpar processamentos órfãos após timeout
    setInterval(() => {
      if (processingPayments.size > 0) {
        console.warn(`⚠️ ${processingPayments.size} pagamento(s) em processo há muito tempo`);
      }
    }, 60000); // Check a cada 60 segundos

    console.log("✅ Sistema de pagamentos inicializado");
  }

  // Inicializar
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

  // NOVO: Limpar ao sair da página
  window.addEventListener('beforeunload', function () {
    processingPayments.clear();
  });
})();