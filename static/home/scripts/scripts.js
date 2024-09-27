document.addEventListener('DOMContentLoaded', function() {
    var audio = document.getElementById('background-audio');
    audio.volume = 0.5;
    var button = document.getElementById('audio-control-button');

    function updateButton() {
        if (audio.paused) {
            button.textContent = '▶️';
        } else {
            button.textContent = '⏸️';
        }
    }

    button.addEventListener('click', function() {
        if (audio.paused) {
            audio.play().catch(function(error) {
                console.log('Autoplay foi bloqueado. Tentando reproduzir após interação do usuário.');
            });
        } else {
            audio.pause();
        }
        updateButton();
    });

    // Tentar reproduzir o áudio automaticamente
    audio.play().catch(function(error) {
        console.log('Autoplay foi bloqueado. Tentando reproduzir após interação do usuário.');
    });

    // Atualizar o botão inicialmente
    updateButton();

    document.addEventListener('click', function() {
        audio.play();
        button.textContent = '⏸️';
    }, { once: true });
});