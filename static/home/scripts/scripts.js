document.addEventListener('DOMContentLoaded', function () {
    var images = document.images,
        totalImages = images.length,
        imagesLoaded = 0;

    // Verifica se todas as imagens foram carregadas
    function imageLoaded() {
        imagesLoaded++;
        if (imagesLoaded === totalImages) {
            document.getElementById("loader").style.display = "none";
            document.getElementById("page-content").style.display = "block";
        }
    }

    // Verifica o carregamento das imagens
    for (var i = 0; i < totalImages; i++) {
        if (images[i].complete) {
            imageLoaded();
        } else {
            images[i].addEventListener("load", imageLoaded);
            images[i].addEventListener("error", imageLoaded); // Contabiliza erros também
        }
    }
    
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

    button.addEventListener('click', function () {
        if (audio.paused) {
            audio.play().catch(function (error) {
                console.log('Autoplay foi bloqueado. Tentando reproduzir após interação do usuário.');
            });
        } else {
            audio.pause();
        }
        updateButton();
    });

    // Tentar reproduzir o áudio automaticamente
    audio.play().catch(function (error) {
        console.log('Autoplay foi bloqueado. Tentando reproduzir após interação do usuário.');
    });

    // Atualizar o botão inicialmente
    updateButton();

    document.addEventListener('click', function () {
        audio.play();
        button.textContent = '⏸️';
    }, { once: true });
});

function copyToClipboard(text) {
    navigator.clipboard.writeText(code);
    alert('Copiado para a área de transferência');
}