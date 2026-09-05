function previewQuestionnaire(id) {
  const overlay = document.getElementById("previewOverlay");
  const modal = new bootstrap.Modal(document.getElementById("questionnairePreviewModal"));
  const content = document.getElementById("modalContent");

  overlay.style.display = "block";
  content.innerHTML = "<p>Wczytywanie...</p>";

  fetch(`/specialists/questionnaire-preview/${id}/`)
    .then(response => {
      if (!response.ok) throw new Error("Błąd ładowania podglądu.");
      return response.text();
    })
    .then(html => {
      content.innerHTML = html;
      modal.show();
    })
    .catch(() => {
      content.innerHTML = "<div class='text-danger'>Nie udało się załadować podglądu ankiety.</div>";
      overlay.style.display = "none";
    });
}

function previewFilledResponse(id) {
  const overlay = document.getElementById("previewOverlay");
  const modal = new bootstrap.Modal(document.getElementById("questionnairePreviewModal"));
  const content = document.getElementById("modalContent");

  overlay.style.display = "block";
  content.innerHTML = "<p>Wczytywanie odpowiedzi...</p>";

  fetch(`/specialists/response/${id}/`)
    .then(response => {
      if (!response.ok) throw new Error("Błąd ładowania odpowiedzi.");
      return response.text();
    })
    .then(html => {
      content.innerHTML = html;
      modal.show();
    })
    .catch(() => {
      content.innerHTML = "<div class='text-danger'>Nie udało się załadować odpowiedzi.</div>";
      overlay.style.display = "none";
    });
}

function closePreview() {
  document.getElementById("previewOverlay").style.display = "none";
  document.getElementById("modalContent").innerHTML = "";
  bootstrap.Modal.getInstance(document.getElementById("questionnairePreviewModal")).hide();
}

document.addEventListener("click", function (e) {
  const btn = e.target.closest(".preview-response-btn");
  if (btn) {
    const id = btn.getAttribute("data-id");
    previewFilledResponse(id);
  }
});
