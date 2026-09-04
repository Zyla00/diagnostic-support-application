document.addEventListener('DOMContentLoaded', function () {
  let formIndex = parseInt(document.getElementById('id_form-TOTAL_FORMS')?.value || '0');
  let sectionIndex = 1000;

  const updateUnloadWarning = () => window.onbeforeunload = () => true;
  const clearUnloadWarning = () => window.onbeforeunload = null;

  document.querySelectorAll('form input, form select, form textarea, .section-title, #questionnaire-name')
    .forEach(el => el.addEventListener('input', updateUnloadWarning));

  const backButton = document.getElementById('back-button');
  if (backButton) {
    backButton.addEventListener('click', function (e) {
      if (window.onbeforeunload) {
        if (!confirm("Masz niezapisane zmiany. Czy na pewno chcesz wyjść?")) {
          e.preventDefault();
        }
      }
    });
  }

  // Synchronizacja edytowalnych tytułów sekcji z ukrytymi inputami
  document.addEventListener('input', function (e) {
    if (e.target.classList.contains('section-title')) {
      const hiddenInput = e.target.nextElementSibling;
      if (hiddenInput && hiddenInput.name === 'section_titles[]') {
        hiddenInput.value = e.target.textContent;
      }
    }
  });

  // Dodawanie nowej sekcji
  document.getElementById('add-section-btn')?.addEventListener('click', function () {
    const sectionName = "Nowa sekcja";
    const sectionId = `temp-${sectionIndex++}`;

    const sectionHTML = `
      <div class="section border rounded p-3 mb-4 bg-white" data-section-id="${sectionId}">
        <div class="d-flex justify-content-between align-items-center mb-3">
          <h5 class="mb-0 section-title" contenteditable="true">${sectionName}</h5>
          <input type="hidden" name="section_titles[]" value="${sectionName}" />
          <div class="d-flex gap-2">
            <button type="button" class="btn btn-sm btn-outline-secondary add-question-btn">+ Dodaj pytanie</button>
            <button type="button" class="btn btn-sm btn-outline-danger delete-section-btn">Usuń sekcję</button>
          </div>
        </div>
        <div class="questions-container"></div>
      </div>
    `;
    document.getElementById('sections-container').insertAdjacentHTML('beforeend', sectionHTML);
    updateUnloadWarning();
  });

  // Dodawanie pytania
  document.addEventListener('click', function (e) {
    if (e.target.closest('.add-question-btn')) {
      const section = e.target.closest('.section');
      const sectionId = section.dataset.sectionId || '';
      const container = section.querySelector('.questions-container');

      const questionHTML = `
        <div class="question-item card mb-3" data-form-index="${formIndex}">
          <div class="card-body">
            <div class="d-flex justify-content-between align-items-center">
              <button type="button" class="btn btn-link toggle-details text-decoration-none text-primary">
                <i class="bi bi-caret-down-fill"></i> Pytanie (nowe)
              </button>
              <button type="button" class="btn btn-sm btn-outline-danger btn-delete-question">Usuń</button>
            </div>
            <div class="question-details mt-3">
              <input type="hidden" name="form-${formIndex}-id" value="" />
              <input type="hidden" name="form-${formIndex}-DELETE" value="" />
              <input type="hidden" name="form-${formIndex}-section" value="${sectionId}" />
              <div class="mb-2">
                <input type="text" name="form-${formIndex}-question_text" class="form-control" placeholder="Treść pytania" required />
              </div>
              <div class="mb-2">
                <select name="form-${formIndex}-question_type" class="form-select" required>
                  <option value="">-- Wybierz typ --</option>
                  <option value="text">Text</option>
                  <option value="single_choice">Single Choice</option>
                  <option value="multiple_choice">Multiple Choice</option>
                </select>
              </div>
              <div class="mb-2">
                <input type="text" name="form-${formIndex}-choices_text" class="form-control" placeholder="np. Tak, Nie" />
                <div class="form-text">Podaj rozdzielone przecinkami (jeśli dotyczy)</div>
              </div>
            </div>
          </div>
        </div>
      `;

      container.insertAdjacentHTML('beforeend', questionHTML);
      formIndex++;
      const totalFormsInput = document.getElementById('id_form-TOTAL_FORMS');
      if (totalFormsInput) {
        totalFormsInput.value = formIndex;
      }
      updateUnloadWarning();
    }
  });

  // Usuwanie pytania
  document.addEventListener('click', function (e) {
    if (e.target.closest('.btn-delete-question')) {
      const card = e.target.closest('.question-item');
      const deleteField = card.querySelector('input[name$="-DELETE"]');
      if (deleteField) deleteField.checked = true;
      card.style.display = 'none';
      updateUnloadWarning();
    }
  });

  // Usuwanie sekcji
  document.addEventListener('click', function (e) {
    if (e.target.closest('.delete-section-btn')) {
      const section = e.target.closest('.section');
      const sectionId = section?.dataset.sectionId;
      if (!section) return;

      const confirmed = confirm("Czy na pewno chcesz usunąć tę sekcję?");
      if (!confirmed) return;

      if (sectionId && !sectionId.startsWith('temp-')) {
        const input = document.createElement('input');
        input.type = 'hidden';
        input.name = 'deleted_sections[]';
        input.value = sectionId;
        document.getElementById('questionnaire-form').appendChild(input);
      }

      section.remove();
      updateUnloadWarning();
    }
  });

  // Rozwijanie i zwijanie pytania
  document.addEventListener('click', function (e) {
    if (e.target.closest('.toggle-details')) {
      const button = e.target.closest('.toggle-details');
      const details = button.closest('.card-body').querySelector('.question-details');
      details.style.display = (details.style.display === 'none' || !details.style.display) ? 'block' : 'none';
      const icon = button.querySelector('i');
      if (icon) {
        icon.classList.toggle('bi-caret-down-fill');
        icon.classList.toggle('bi-caret-up-fill');
      }
    }
  });

  // Submit formularza – wyłącz ostrzeżenie
  document.getElementById('questionnaire-form')?.addEventListener('submit', function () {
    console.log("Formularz submitowany");
    clearUnloadWarning();
  });
});
