document.addEventListener('DOMContentLoaded', function () {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    })
    // Select all modals with id starting with 'pickGift'
    var modals = document.querySelectorAll('[id^="pickGift"]');

    modals.forEach(function (modal) {
        var priceContainer = modal.querySelector('.price-container');
        if (priceContainer) {
            var wayToGiftRadios = modal.querySelectorAll('input[name="way_to_gift"]');
            function updatePriceContainer() {
                var selectedValue = modal.querySelector('input[name="way_to_gift"]:checked').value;
                if (selectedValue === 'money') {
                    priceContainer.style.display = 'block';
                } else {
                    priceContainer.style.display = 'none';
                }
            }
            wayToGiftRadios.forEach(function (radio) {
                radio.addEventListener('change', updatePriceContainer);
            });
            // Initialize on page load
            updatePriceContainer();
        }
    });
});
document.addEventListener('hidden.bs.modal', function () {
    if (!document.querySelector('.modal.show')) {
        document.body.classList.remove('modal-open');
        const backdrop = document.querySelector('.modal-backdrop');
        if (backdrop) {
            backdrop.remove();
        }
    }
});
const modals = document.querySelectorAll('.modal');
modals.forEach(modal => {
    modal.addEventListener('hidden.bs.modal', function () {
        const backdrop = document.querySelector('.modal-backdrop');
        if (backdrop) {
            backdrop.remove();
        }
    });
});
document.addEventListener('hidden.bs.modal', function () {
    if (!document.querySelector('.modal.show')) {
        const backdrop = document.querySelector('.modal-backdrop');
        if (backdrop) {
            backdrop.remove();
        }
    }
});
const backButtons = document.querySelectorAll('[data-bs-target][data-bs-toggle="modal"]');

backButtons.forEach(button => {
    button.addEventListener('click', function (event) {
        const currentModal = bootstrap.Modal.getInstance(this.closest('.modal'));
        currentModal.hide();
        setTimeout(() => {
            const targetModal = new bootstrap.Modal(document.querySelector(this.getAttribute('data-bs-target')));
            targetModal.show();
        }, 500);
    });
});