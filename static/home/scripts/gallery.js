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

function changeImage(direction) {
    // Add fade-out class to start fade-out animation
    modalImage.classList.add('fade-out');

    // Wait for the fade-out animation to finish
    modalImage.addEventListener('animationend', function handler() {
        // Remove the event listener to prevent multiple triggers
        modalImage.removeEventListener('animationend', handler);

        // Update the current image index
        if (direction === 'next') {
            currentImage = (currentImage + 1) % images.length;
        } else if (direction === 'prev') {
            currentImage = (currentImage - 1 + images.length) % images.length;
        }

        // Update the image source and title
        var titleElement = images[currentImage].querySelector('.u-text-3');
        modalTitle.textContent = titleElement ? titleElement.textContent : 'Foto';
        modalImage.src = images[currentImage].querySelector('img').src;

        // Remove the fade-out class and add fade-in class
        modalImage.classList.remove('fade-out');
        modalImage.classList.add('fade-in');

        // Remove the fade-in class after the animation completes
        modalImage.addEventListener('animationend', function handler2() {
            modalImage.removeEventListener('animationend', handler2);
            modalImage.classList.remove('fade-in');
        });
    });
}

previousButton.addEventListener('click', () => {
    changeImage('prev');
});

nextButton.addEventListener('click', () => {
    changeImage('next');
});
