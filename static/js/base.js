class SidebarToggle {
    constructor(toggleButtonId, sidebarId, containerClass) {
        this.toggleButton = document.getElementById(toggleButtonId);
        this.sidebar = document.getElementById(sidebarId);
        this.container = document.querySelector(`.${containerClass}`);
        this.addEventListeners();
    }

    addEventListeners() {
        this.toggleButton?.addEventListener('click', (e) => {
            e.stopPropagation();  // <== ZAPOBIEGA innym efektom kliknięcia
            this.toggleSidebar();
        });
    }

    toggleSidebar() {
        this.sidebar?.classList.toggle('sidebar-collapsed');
        if (this.sidebar?.classList.contains('sidebar-collapsed')) {
            this.toggleButton.style.left = '15px';
            this.container?.classList.add('content-expanded');
        } else {
            this.toggleButton.style.left = '245px';
            this.container?.classList.remove('content-expanded');
        }
    }
}




function initializeSidebarToggle() {
    new SidebarToggle('toggle-button', 'sidebar', 'content');
}

function openOffcanvas(selector, contentHTML, title = '') {
    const canvas = document.querySelector(selector);
    if (!canvas) return;

    const titleEl = canvas.querySelector('.offcanvas-title');
    const bodyEl = canvas.querySelector('.offcanvas-body');

    if (titleEl && title) titleEl.textContent = title;
    if (bodyEl) bodyEl.innerHTML = contentHTML;

    new bootstrap.Offcanvas(canvas).show();
}

function initializeEditProfileButton() {
    const editBtn = document.getElementById("editProfileBtn");
    if (!editBtn) return;

    editBtn.addEventListener("click", function (e) {
        e.preventDefault();
        fetch('/profile/edit/')
            .then(response => response.text())
            .then(html => {
                const container = document.querySelector('#profileContainer');
                if (container) {
                    container.innerHTML = html;
                    initializeProfileForm();
                }
            })
            .catch(error => {
                console.error("Błąd ładowania formularza edycji:", error);
                window.alertManager?.error("Nie udało się załadować formularza.");
            });
    });
}

function initializeProfileForm() {
    const form = document.querySelector('#user-form');
    if (!form) return;

    form.addEventListener('submit', function (e) {
        e.preventDefault();

        const formData = new FormData(form);
        const csrf = formData.get('csrfmiddlewaretoken');

        fetch(form.action, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrf,
            },
            body: formData,
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                const offcanvasEl = document.getElementById('editProfileCanvas');
                const offcanvasInstance = bootstrap.Offcanvas.getInstance(offcanvasEl);
                offcanvasInstance?.hide();

                window.alertManager?.success('Zapisano zmiany.');

                fetch('/profile/')
                    .then(res => res.text())
                    .then(html => {
                        const container = document.querySelector('#profileContainer');
                        if (container) {
                            container.innerHTML = html;
                        }
                    });
            } else {
                Object.keys(data.errors).forEach(field => {
                    const msg = data.errors[field].join(', ');
                    window.alertManager?.error(`${field}: ${msg}`);
                });
            }
        })
        .catch(() => {
            window.alertManager?.error('Błąd zapisu profilu.');
        });
    });
}



function initializeChangePasswordTrigger() {
    const link = document.getElementById('changePasswordLink');
    if (!link) return;

    link.addEventListener('click', (e) => {
        e.preventDefault();
        fetch('/edit-password/')
            .then(res => res.text())
            .then(html => {
                openOffcanvas('#offcanvasElement', html, 'Zmiana hasła');
                initializePasswordForm();
            })
            .catch(err => {
                console.error('Błąd ładowania formularza hasła:', err);
                window.alertManager?.error('Nie udało się załadować formularza.');
            });
    });
}

function initializePasswordForm(retries = 10) {
    const form = document.getElementById('user-form');

    if (!form) {
        if (retries > 0) {
            setTimeout(() => initializePasswordForm(retries - 1), 100);
        } else {
            console.warn('Nie znaleziono formularza #user-form do zmiany hasła.');
        }
        return;
    }

    console.log('initializePasswordForm zadziałał');

    form.addEventListener('submit', function (e) {
        e.preventDefault();

        const csrftoken = getCookie('csrftoken');
        const formData = new FormData(form);

        fetch('/edit-password/', {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': csrftoken,
            },
            body: formData
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                window.alertManager.success('Password changed successfully!');
                bootstrap.Offcanvas.getInstance(document.getElementById('offcanvasElement'))?.hide();
            } else {
                Object.keys(data.errors).forEach(field => {
                    const message = `${field}: ${data.errors[field].join(', ')}`;
                    window.alertManager.error(message);
                });
            }
        })
        .catch(() => {
            window.alertManager.error('Something went wrong. Please try again.');
        });
    });
}


function initializeProfileTrigger() {
    const profileLinks = document.querySelectorAll('.open-profile-btn');

    profileLinks.forEach(link => {
        link.addEventListener('click', function (e) {
            e.preventDefault();
            const url = link.getAttribute('data-url') || '/profile/';

            fetch(url)
                .then(response => response.text())
                .then(html => {
                    const canvas = document.getElementById('editProfileCanvas');
                    const container = canvas.querySelector('#profileContainer');
                    if (container) {
                        container.innerHTML = html;
                        new bootstrap.Offcanvas(canvas).show();
                        initializeEditProfileButton();
                    }
                })
                .catch(error => {
                    console.error('Błąd ładowania profilu:', error);
                    window.alertManager?.error('Nie udało się wczytać profilu.');
                });
        });
    });
}

function initializeSettingsTrigger() {
    console.log('Kliknięto Settings');

    const settingsLink = document.getElementById('openSettingsForm');
    if (settingsLink) {
        settingsLink.addEventListener('click', function (e) {
            e.preventDefault();
            fetch('/settings/edit/')
                .then(response => response.text())
                .then(html => {
                    const canvas = document.getElementById('editProfileCanvas');
                    const container = canvas.querySelector('#profileContainer');
                    if (container) {
                        container.innerHTML = html;
                        new bootstrap.Offcanvas(canvas).show();
                        initializeProfileForm(); // jeśli ten formularz jest taki sam
                    }
                })
                .catch(error => {
                    console.error("Błąd ładowania ustawień:", error);
                    window.alertManager?.error("Nie udało się załadować ustawień.");
                });
        });
    }
}

function initializeSlider(sliderId, valueId) {
    const slider = document.getElementById(sliderId);
    const label = document.getElementById(valueId);
    if (!slider || !label) return;

    const updateValue = () => {
        const value = slider.value;
        label.textContent = value;

        const rangeWidth = slider.offsetWidth;
        const thumbWidth = 20;
        const offset = ((value - slider.min) / (slider.max - slider.min)) * (rangeWidth - thumbWidth);
        label.style.left = `${offset + thumbWidth / 1}px`;

        slider.style.setProperty('--slider-before-width', `${offset}px`);
    };

    slider.addEventListener('input', updateValue);
    updateValue();
}

function setupModalCleanup() {
    const modal = document.getElementById('modalElement');
    if (!modal) return;

    modal.addEventListener('hidden.bs.modal', () => {
        document.getElementById('modalElementTitle').textContent = '';
        document.getElementById('modalElementBody').innerHTML = '';
        document.getElementById('modalElementFooter').innerHTML = '';
    });
}

function getCookie(name) {
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
        cookie = cookie.trim();
        if (cookie.startsWith(name + '=')) {
            return decodeURIComponent(cookie.substring(name.length + 1));
        }
    }
    return null;
}

window.addEventListener('DOMContentLoaded', () => {
    setTimeout(() => {
        new SidebarToggle('toggle-button', 'sidebar', 'content');
        initializeChangePasswordTrigger();
        window.alertManager = new AlertManager();
        initializeProfileTrigger();
        initializeSettingsTrigger();
        setupModalCleanup();

        document.addEventListener('hidden.bs.offcanvas', () => {
            document.body.classList.remove('offcanvas-backdrop');
            const backdrop = document.querySelector('.offcanvas-backdrop');
            if (backdrop) backdrop.remove();
        });
    }, 100);
});

function updateUnreadBadge() {
  fetch('/messages/unread-count/')
    .then(response => response.json())
    .then(data => {
      const badge = document.getElementById('unreadBadge');
      if (!badge) return;

      const count = data.count;
      if (count > 0) {
        badge.textContent = count;
        badge.classList.remove('d-none');
      } else {
        badge.classList.add('d-none');
      }
    })
    .catch(err => {
      console.warn('Błąd przy pobieraniu nieprzeczytanych:', err);
    });
}

document.addEventListener('DOMContentLoaded', function () {
  updateUnreadBadge();
  setInterval(updateUnreadBadge, 10000); // Odśwież co 10s
});

document.addEventListener("DOMContentLoaded", function () {
  const link = document.getElementById("recommendationLink");
  const dot = document.getElementById("recDot");

  if (link && dot) {
    const unreadCount = parseInt(link.dataset.unread);

    if (!isNaN(unreadCount) && unreadCount > 0) {
      dot.style.display = "inline-block";
    }

    const currentPath = window.location.pathname;
    if (currentPath.includes("/my-recommendations") || currentPath.includes("/recommendations")) {
      dot.style.display = "none";
    }
  }
});
