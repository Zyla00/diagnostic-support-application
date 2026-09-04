// static/predictions/modele.js
(function () {
  function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return decodeURIComponent(parts.pop().split(';').shift());
  }
  const csrftoken = getCookie('csrftoken');

  const cfg = document.getElementById("aiConfig");
  if (!cfg) return;
  const runUrl = cfg.dataset.runUrl;

  const runBtn = document.getElementById("runAnalysisBtn");
  const clearBtn = document.getElementById("clearResultsBtn");
  const loading = document.getElementById("analysisLoading");

  function pickChecked(selector) {
    return Array.from(document.querySelectorAll(selector + ":checked")).map(el => Number(el.value));
  }

  function show(el) { if (el) el.style.display = ""; }
  function hide(el) { if (el) el.style.display = "none"; }

  function resetResults() {
    hide(document.getElementById("resultsGeneral"));
    hide(document.getElementById("resultsClassification"));
    hide(document.getElementById("resultsLLMConfidence"));
    hide(document.getElementById("rawPayload"));
    document.getElementById("generalText") && (document.getElementById("generalText").innerHTML = "");
    document.getElementById("predictedClass") && (document.getElementById("predictedClass").textContent = "—");
    const classProbs = document.getElementById("classProbs");
    if (classProbs) classProbs.innerHTML = "";
    const extra = document.getElementById("llmExtraSignals");
    if (extra) extra.innerHTML = "";
    const bar = document.getElementById("llmHeuristicBar");
    if (bar) { bar.style.width = "0%"; bar.setAttribute("aria-valuenow", "0"); }
    const scoreText = document.getElementById("llmHeuristicScoreText");
    if (scoreText) scoreText.textContent = "—";
    const raw = document.getElementById("rawJson");
    if (raw) raw.textContent = "";
  }

  clearBtn?.addEventListener("click", resetResults);

  runBtn?.addEventListener("click", async () => {
    resetResults();

    const model = document.getElementById("aiModel")?.value;
    const survey_ids = pickChecked(".survey-checkbox");
    const lab_ids = pickChecked(".lab-checkbox");

    if (!model) {
      alert("Wybierz model.");
      return;
    }
    if (survey_ids.length === 0 && lab_ids.length === 0) {
      alert("Zaznacz co najmniej jedną ankietę lub badanie.");
      return;
    }

    show(loading);
    try {
      const res = await fetch(runUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrftoken,
        },
        body: JSON.stringify({ model, survey_ids, lab_ids })
      });
      const data = await res.json();
      hide(loading);

      if (!data.ok) {
        alert(data.error || "Błąd analizy.");
        return;
      }

      // MODELE KLASYFIKACYJNE
      if (model === "xgboost" || model === "herbert") {
        show(document.getElementById("resultsClassification"));
        document.getElementById("predictedClass").textContent = data.predicted_class || "—";
        const cont = document.getElementById("classProbs");
        cont.innerHTML = "";
        (data.probs || []).forEach(p => {
          const pct = Math.round((p.prob || 0) * 100);
          cont.insertAdjacentHTML("beforeend", `
            <div class="mb-2">
              <div class="d-flex justify-content-between">
                <small>${p.label}</small><small>${pct}%</small>
              </div>
              <div class="progress">
                <div class="progress-bar" role="progressbar" style="width:${pct}%;" aria-valuenow="${pct}" aria-valuemin="0" aria-valuemax="100"></div>
              </div>
            </div>
          `);
        });
      } else {
        // LLM / RAG
        show(document.getElementById("resultsGeneral"));
        document.getElementById("generalText").innerText = data.summary || "";

        show(document.getElementById("resultsLLMConfidence"));
        const val = Math.round(((data.llm_confidence || 0) * 100));
        const bar = document.getElementById("llmHeuristicBar");
        bar.style.width = val + "%";
        bar.setAttribute("aria-valuenow", String(val));
        document.getElementById("llmHeuristicScoreText").textContent = val + "%";

        const extra = document.getElementById("llmExtraSignals");
        extra.innerHTML = "";
        (data.extra_signals || []).forEach(t => {
          extra.insertAdjacentHTML("beforeend", `<li class="list-group-item px-0"><small>${t}</small></li>`);
        });
      }

      // RAW
      if (data.raw) {
        show(document.getElementById("rawPayload"));
        document.getElementById("rawJson").textContent = JSON.stringify(data.raw, null, 2);
      }
    } catch (e) {
      hide(loading);
      alert("Nie udało się uruchomić analizy.");
    }
  });
})();
