"use strict";
(() => {
  const data = window.SATAG_SAMPLES;
  if (!data) return;
  const escape = value => String(value).replace(/[&<>"']/g, char => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[char]));
  const title = sample => sample.events.map(event => event.name).join(" + ");
  const times = sample => sample.events.map(event => `${event.name} from ${event.start.toFixed(2)} to ${event.end.toFixed(2)} s`).join("; ");
  const badge = sample => `<span class="overlap-badge overlap-${sample.overlap}">${sample.overlap === 0 ? "No overlap" : sample.overlap + "% overlap"}</span>`;
  const timeline = sample => `<div class="event-legend">${sample.events.map(event => `<span><b>${escape(event.name)}</b><time>${event.start.toFixed(2)}–${event.end.toFixed(2)} s</time></span>`).join("")}</div><div class="timeline" role="img" aria-label="Target intervals: ${escape(times(sample))}">${sample.events.map((event, index) => `<i class="event-bar ${index ? "second" : ""}" style="left:${event.start / sample.duration * 100}%;width:${(event.end - event.start) / sample.duration * 100}%"></i>`).join("")}<i class="playhead" aria-hidden="true"></i></div><div class="timeline-axis" aria-hidden="true"><span>0 s</span><span>2</span><span>4</span><span>6</span><span>8</span><span>10 s</span></div>`;
  const spectrogram = (source, label) => source.image ? `<button class="zoom-button" type="button" data-image="${escape(source.image)}" data-caption="${escape(label)}" aria-label="Enlarge spectrogram: ${escape(label)}"><img class="mel-image" src="${escape(source.image)}" alt="Mel spectrogram: ${escape(label)}" loading="lazy"></button>` : "";
  const player = (source, label, note) => `<div class="audio-wrap"><audio controls preload="none" src="${escape(source.audio)}" aria-label="${escape(label)}"></audio><p class="audio-error" hidden>Audio could not be loaded. Please try the download link.</p><div class="player-meta"><span>${escape(note)}</span><a href="${escape(source.audio)}" download aria-label="Download ${escape(label)}">Download audio ↓</a></div></div>`;

  document.getElementById("figure-grid").innerHTML = data.figure.map(sample => `<article class="sample-card" id="${escape(sample.id)}"><div class="card-header"><h3><span class="panel-label">FIG. 1 (${escape(sample.panel.toUpperCase())})</span>${escape(title(sample))}</h3>${badge(sample)}</div><div class="card-body">${timeline(sample)}${spectrogram(sample, `${title(sample)}, ${sample.overlap}% overlap, masked DegDiT`)}${player(sample, `Figure 1 (${sample.panel}), ${title(sample)}, ${sample.overlap}% overlap`, "DegDiT · Masked figure clip · s00")}</div></article>`).join("");

  const datasetColors = ["#2563eb", "#dc2626", "#059669", "#9333ea"];
  const datasetRanges = event => event.intervals.map(([start, end]) => `${start.toFixed(2)}–${end.toFixed(2)}`).join(", ");
  const datasetTimeline = sample => `<div class="dataset-timeline" role="img" aria-label="SpotSound event intervals for ${escape(sample.id)}">${sample.events.map((event, eventIndex) => `<div class="dataset-event"><div class="dataset-event-label"><span><i style="background:${datasetColors[eventIndex % datasetColors.length]}"></i>${escape(event.name)}</span><time>${datasetRanges(event)} s</time></div><div class="dataset-track">${event.intervals.map(([start, end]) => `<i style="left:${start / sample.duration * 100}%;width:${(end - start) / sample.duration * 100}%;background:${datasetColors[eventIndex % datasetColors.length]}"></i>`).join("")}<span class="playhead" aria-hidden="true"></span></div></div>`).join("")}<div class="timeline-axis" aria-hidden="true"><span>0 s</span><span>2</span><span>4</span><span>6</span><span>8</span><span>10 s</span></div></div>`;
  document.getElementById("dataset-grid").innerHTML = data.dataset.map((sample, index) => `<article class="dataset-card" id="dataset-${escape(sample.id)}"><div class="dataset-card-head"><span class="dataset-number">EXAMPLE ${String(index + 1).padStart(2, "0")}</span><code>${escape(sample.id)}</code></div><div class="dataset-caption"><span>AudioCaps caption</span><p>${escape(sample.caption)}</p></div>${datasetTimeline(sample)}${player(sample, `AudioCaps-T example ${sample.id}: ${sample.caption}`, "AudioCaps source audio · SpotSound timestamps")}</article>`).join("");

  let pair = "keyboard-bird";
  let overlap = 50;
  function renderComparison() {
    const container = document.getElementById("comparison-content");
    container.querySelectorAll("audio").forEach(audio => audio.pause());
    const sample = data.comparisons.find(item => item.pair === pair && item.overlap === overlap);
    if (!sample) {
      container.innerHTML = '<p class="caption">No sample is available for these conditions.</p>';
      return;
    }
    const label = `${title(sample)}, ${overlap}% overlap`;
    const satag = sample.satag?.audio;
    container.innerHTML = `<div class="condition-panel"><p class="eyebrow">INPUT EVENT CONDITIONS</p><p class="condition-prompt">${escape(times(sample))}</p>${timeline(sample)}</div><div class="model-grid"><article class="model-column"><div class="model-heading"><h3>DegDiT</h3></div><p class="model-description">Joint generation · Baseline</p>${spectrogram(sample.baseline, `DegDiT, ${label}`)}${player(sample.baseline, `DegDiT, ${label}`, "Original output · s00")}</article><article class="model-column ours-column"><div class="model-heading"><h3>DegDiT + SATAG</h3><span class="ours-tag">Ours</span></div><p class="model-description">${overlap === 0 ? "Original generation procedure · No overlap" : "Source-wise generation + waveform superposition"}</p>${satag ? spectrogram(sample.satag, `SATAG, ${label}`) + player(sample.satag, `SATAG, ${label}`, sample.satag.note || "SATAG output") : `<div class="pending-sample"><span class="pending-mark" aria-hidden="true">▂ ▅ ▃ ▆ ▂</span><h4>Audio coming soon</h4><p>${overlap === 0 ? "SATAG keeps the original generation procedure when events do not overlap." : "Matched SATAG samples for these event conditions will be added here."}</p></div>`}</article></div>`;
  }
  renderComparison();
  document.getElementById("pair-select").addEventListener("change", event => { pair = event.target.value; renderComparison(); });
  document.querySelectorAll("[data-overlap]").forEach(button => button.addEventListener("click", () => {
    overlap = Number(button.dataset.overlap);
    document.querySelectorAll("[data-overlap]").forEach(other => other.setAttribute("aria-pressed", String(other === button)));
    renderComparison();
  }));

  // Capture handles dynamically rendered players; never allow two examples to play together.
  document.addEventListener("play", event => {
    if (!(event.target instanceof HTMLAudioElement)) return;
    document.querySelectorAll("audio").forEach(audio => { if (audio !== event.target) audio.pause(); });
  }, true);
  document.addEventListener("timeupdate", event => {
    if (!(event.target instanceof HTMLAudioElement)) return;
    const scope = event.target.closest(".sample-card") || event.target.closest(".dataset-card") || event.target.closest("#comparison-content");
    scope?.querySelectorAll(".playhead").forEach(head => {
      head.style.left = `${Math.min(100, event.target.currentTime / 10 * 100)}%`;
      head.style.opacity = event.target.currentTime > 0 ? "1" : "0";
    });
  }, true);
  document.addEventListener("error", event => {
    if (event.target instanceof HTMLAudioElement) event.target.parentElement.querySelector(".audio-error").hidden = false;
  }, true);
  const dialog = document.getElementById("image-dialog");
  document.addEventListener("click", event => {
    const button = event.target.closest("button[data-image]");
    if (!button) return;
    const image = document.getElementById("dialog-image");
    image.src = button.dataset.image;
    image.alt = button.dataset.caption;
    document.getElementById("dialog-caption").textContent = button.dataset.caption;
    dialog.showModal();
  });
  dialog.querySelector(".dialog-close").addEventListener("click", () => dialog.close());
  dialog.addEventListener("click", event => { if (event.target === dialog) { const rect = dialog.getBoundingClientRect(); if (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom) dialog.close(); } });
})();
