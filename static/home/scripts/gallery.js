var images = document.querySelectorAll('.u-repeater-item');
var modal = new bootstrap.Modal(document.getElementById('pictureModal'));
var modalTitle = document.querySelector('.modal-title');
var modalImage = document.getElementById('picture');
var previousButton = document.querySelector('.modal-footer button.btn-secondary');
var nextButton = document.querySelector('.modal-footer button.btn-primary');
var currentImage = 0;

images.forEach((image, index) => {
    image.addEventListener('click', () => {
        currentImage = index;
        var titleElement = image.querySelector('.u-text-3');
        modalTitle.textContent = titleElement ? titleElement.textContent : 'Foto';
        modalImage.src = image.querySelector('img').src;
        modal.show();
    });
});

previousButton.addEventListener('click', () => {
    currentImage = currentImage === 0 ? images.length - 1 : currentImage - 1;
    var titleElement = images[currentImage].querySelector('.u-text-3');
    modalTitle.textContent = titleElement ? titleElement.textContent : 'Foto';
    modalImage.src = images[currentImage].querySelector('img').src;
});

nextButton.addEventListener('click', () => {
    currentImage = currentImage === images.length - 1 ? 0 : currentImage + 1;
    var titleElement = images[currentImage].querySelector('.u-text-3');
    modalTitle.textContent = titleElement ? titleElement.textContent : 'Foto';
    modalImage.src = images[currentImage].querySelector('img').src;
});