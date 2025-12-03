/* ============================================
   COUNTDOWN FIX PARA SAFARI/iOS
   O Safari não aceita alguns formatos de data
   ============================================ */

(function () {
  "use strict";

  /**
   * Parse de data compatível com Safari
   * Safari não aceita formato "YYYY-MM-DD HH:mm:ss"
   * Precisa converter para "YYYY/MM/DD HH:mm:ss" ou usar Date constructor
   */
  function parseSafariDate(dateString) {
    // Remove espaços extras
    dateString = dateString.trim();

    // Se já está no formato ISO completo, usar diretamente
    if (dateString.includes("T")) {
      return new Date(dateString);
    }

    // Converter "YYYY-MM-DD HH:mm:ss" para formato Safari-friendly
    // Safari prefere "/" ao invés de "-"
    const safariDateString = dateString.replace(/-/g, "/");

    return new Date(safariDateString);
  }

  /**
   * Formata número com zero à esquerda
   */
  function padZero(num) {
    return num < 10 ? "0" + num : num.toString();
  }

  /**
   * Inicializa o countdown
   */
  function initCountdown() {
    const countdownEl = document.getElementById("countdown");

    if (!countdownEl) {
      console.log("Elemento countdown não encontrado");
      return;
    }

    const dateTimeAttr = countdownEl.getAttribute("data-wedding-datetime");

    if (!dateTimeAttr) {
      console.error("Atributo data-wedding-datetime não encontrado");
      return;
    }

    console.log("Data original:", dateTimeAttr);

    // Parse da data de forma compatível com Safari
    const weddingDate = parseSafariDate(dateTimeAttr);

    // Verificar se a data é válida
    if (isNaN(weddingDate.getTime())) {
      console.error("Data inválida:", dateTimeAttr);
      countdownEl.innerHTML =
        '<p class="text-center" style="color: #fff;">Data inválida</p>';
      return;
    }

    const weddingTimestamp = weddingDate.getTime();
    console.log("Data parseada:", weddingDate);
    console.log("Timestamp:", weddingTimestamp);

    // Elementos do contador
    const daysEl = document.getElementById("days");
    const hoursEl = document.getElementById("hours");
    const minutesEl = document.getElementById("minutes");
    const secondsEl = document.getElementById("seconds");

    // Verificar se todos os elementos existem
    if (!daysEl || !hoursEl || !minutesEl || !secondsEl) {
      console.error("Elementos do countdown não encontrados");
      return;
    }

    /**
     * Atualiza o countdown
     */
    function updateCountdown() {
      const now = new Date().getTime();
      const distance = weddingTimestamp - now;

      // Se o casamento já passou
      if (distance < 0) {
        countdownEl.innerHTML =
          '<p class="text-center fs-4" style="color: #fff; margin: 0;">O casamento já começou! 🎉</p>';
        return;
      }

      // Calcular tempo restante
      const days = Math.floor(distance / (1000 * 60 * 60 * 24));
      const hours = Math.floor(
        (distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60)
      );
      const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
      const seconds = Math.floor((distance % (1000 * 60)) / 1000);

      // Atualizar DOM
      daysEl.textContent = padZero(days);
      hoursEl.textContent = padZero(hours);
      minutesEl.textContent = padZero(minutes);
      secondsEl.textContent = padZero(seconds);
    }

    // Executar imediatamente
    updateCountdown();

    // Atualizar a cada segundo
    const intervalId = setInterval(updateCountdown, 1000);

    // Limpar intervalo quando sair da página
    window.addEventListener("beforeunload", function () {
      clearInterval(intervalId);
    });

    console.log("✅ Countdown inicializado com sucesso");
  }

  // Inicializar quando DOM estiver pronto
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initCountdown);
  } else {
    initCountdown();
  }
})();
