document.addEventListener("DOMContentLoaded", function () {
    window.STATIC_BASE_URL = document.body.dataset.staticBaseUrl || "";
    initEditableTitles();
    initCopyForms();
    initCreateFormToggle();
    initSearchLive();
    initSearchButton();
});

// === 1. EDYCJA NAZW ===
function initEditableTitles() {
    document.querySelectorAll(".editable-title").forEach(el => {
        el.replaceWith(el.cloneNode(true)); // usuwa stare eventy
    });

    document.querySelectorAll(".editable-title").forEach(el => {
        el.addEventListener("click", () => {
            const originalText = el.textContent.trim();
            const id = el.dataset.id;

            const input = document.createElement("input");
            input.type = "text";
            input.value = originalText;
            input.className = "form-control form-control-sm";
            input.style.width = "100%";

            const wrapper = el.closest(".editable-wrapper");
            wrapper.innerHTML = "";
            wrapper.appendChild(input);
            input.focus();

            function saveName() {
                const newName = input.value.trim();
                if (newName && newName !== originalText) {
                    fetch(`/ankiety/${id}/rename/`, {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/x-www-form-urlencoded",
                            "X-CSRFToken": getCookie("csrftoken"),
                        },
                        body: `name=${encodeURIComponent(newName)}`
                    })
                        .then(response => {
                            if (!response.ok) {
                                return response.json().then(err => {
                                    if (err.error === 'duplicate') {
                                        showToast("Taka nazwa już istnieje.", "danger");
                                    } else {
                                        showToast("Błąd przy zapisie.", "danger");
                                    }
                                    restoreEditable(wrapper, id, originalText);
                                });
                            }
                            return response.json().then(data => {
                                showToast("Zmieniono nazwę ankiety!", "success");
                                restoreEditable(wrapper, id, data.new_name);
                            });
                        })
                        .catch(() => {
                            showToast("Błąd sieci przy zapisie.", "danger");
                            restoreEditable(wrapper, id, originalText);
                        });
                } else {
                    restoreEditable(wrapper, id, originalText);
                }
            }

            function cancelEdit() {
                restoreEditable(wrapper, id, originalText);
            }

            input.addEventListener("blur", saveName);
            input.addEventListener("keydown", function (e) {
                if (e.key === "Enter") saveName();
                else if (e.key === "Escape") cancelEdit();
            });
        });
    });
}

function restoreEditable(wrapper, id, text) {
    wrapper.innerHTML = `
        <h5 class="card-title editable-title mb-0 pe-4" data-id="${id}">${text}</h5>
        <img src="${STATIC_BASE_URL}img/edit_icon.svg" alt="Edytuj" class="edit-hint position-absolute top-0 end-0 me-2 mt-1 d-none" width="16" height="16">
    `;
    initEditableTitles();
}

// === 2. KOPIOWANIE ===
function initCopyForms() {
    const forms = document.querySelectorAll("form[action*='copy']");
    forms.forEach(form => {
        form.addEventListener("submit", function (e) {
            e.preventDefault();
            const formData = new FormData(form);
            fetch(form.action, {
                method: "POST",
                headers: {
                    "X-CSRFToken": getCookie("csrftoken"),
                    "X-Requested-With": "XMLHttpRequest"
                },
                body: formData
            })
                .then(response => {
                    if (response.ok) {
                        showToast("Ankieta została skopiowana!", "success");
                        setTimeout(() => {
                            document.getElementById("searchButton")?.click();
                        }, 500);
                    } else {
                        showToast("Błąd podczas kopiowania.", "danger");
                    }
                })
                .catch(() => {
                    showToast("Błąd sieci.", "danger");
                });
        });
    });
}

// === 3. DODAWANIE NOWEJ ANKIETY ===
function initCreateFormToggle() {
    const showInputBtn = document.getElementById("showInputBtn");
    const nameInput = document.getElementById("questionnaireNameInput");
    const submitBtn = document.getElementById("createSubmitBtn");
    const createForm = document.getElementById("createForm");

    if (showInputBtn && nameInput && submitBtn && createForm) {
        showInputBtn.addEventListener("click", () => {
            nameInput.classList.remove("d-none");
            submitBtn.classList.remove("d-none");
            showInputBtn.classList.add("d-none");
            nameInput.focus();
        });

        createForm.addEventListener("submit", function (e) {
            e.preventDefault();

            const name = nameInput.value.trim();
            if (!name) {
                showToast("Podaj nazwę ankiety!", "warning");
                return;
            }

            const formData = new FormData();
            formData.append("name", name);
            formData.append("csrfmiddlewaretoken", getCookie("csrftoken"));

            fetch("/ankiety/create/", {
                method: "POST",
                headers: {
                    "X-Requested-With": "XMLHttpRequest"
                },
                body: formData
            })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        showToast("Dodano ankietę!", "success");
                        nameInput.value = "";
                        nameInput.classList.add("d-none");
                        submitBtn.classList.add("d-none");
                        showInputBtn.classList.remove("d-none");
                        document.getElementById("searchButton")?.click();
                    } else {
                        showToast("Błąd: " + (data.message || "nieznany."), "danger");
                    }
                })
                .catch(() => {
                    showToast("Błąd serwera!", "danger");
                });
        });
    }
}

// === 4. SZUKAJKA NA ŻYWO ===
function initSearchLive() {
    const input = document.getElementById("searchInput");
    if (!input) return;

    input.addEventListener("input", function () {
        const query = input.value.trim();

        fetch(`/ankiety/ajax/search/?q=${encodeURIComponent(query)}`, {
            headers: { "X-Requested-With": "XMLHttpRequest" }
        })
            .then(response => response.json())
            .then(data => {
                document.getElementById("questionnaireResults").innerHTML = data.html;
                initEditableTitles();
                initCopyForms();
            })
            .catch(err => {
                console.error("Błąd wyszukiwania:", err);
            });
    });
}

// === 5. SZUKAJKA PO KLIKNIĘCIU ===
function initSearchButton() {
    const searchBtn = document.getElementById('searchButton');
    const searchInput = document.getElementById('searchInput');
    const resultsContainer = document.getElementById('questionnaireResults');

    if (searchBtn && searchInput && resultsContainer) {
        searchBtn.addEventListener('click', function () {
            const query = searchInput.value;

            fetch(`/ankiety/?q=${encodeURIComponent(query)}`, {
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            })
                .then(res => res.text())
                .then(html => {
                    resultsContainer.innerHTML = html;
                    initEditableTitles();
                    initCopyForms();
                })
                .catch(err => {
                    console.error('Błąd podczas pobierania wyników:', err);
                });
        });
    }
}

// === 6. POBIERANIE CSRF ===
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
        const cookies = document.cookie.split(";");
        for (let cookie of cookies) {
            cookie = cookie.trim();
            if (cookie.startsWith(name + "=")) {
                cookieValue = decodeURIComponent(cookie.slice(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
