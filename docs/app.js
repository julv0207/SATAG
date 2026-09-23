"use strict";
(() => {
  const data = window.SATAG_SAMPLES;
  if (!data) return;
  const escape = value => String(value).replace(/[&<>"']/g, char => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[char]));
  const title = sample => sample.events.map(event => event.name).join(" + ");
  const times = sample => sample.events.map(event => `${event.name} from ${event.start.toFixed(2)} to ${event.end.toFixed(2)} s`).join("; ");
  const timeline = sample => `<div class="event-legend">${sample.events.map(event => `<span><b>${escape(event.name)}</b><time>${event.start.toFixed(2)}–${event.end.toFixed(2)} s</time></span>`).join("")}</div><div class="timeline" role="img" aria-label="Target intervals: ${escape(times(sample))}">${sample.events.map((event, index) => `<i class="event-bar ${index ? "second" : ""}" style="left:${event.start / sample.duration * 100}%;width:${(event.end - event.start) / sample.duration * 100}%"></i>`).join("")}<i class="playhead" aria-hidden="true"></i></div><div class="timeline-axis" aria-hidden="true"><span>0 s</span><span>2</span><span>4</span><span>6</span><span>8</span><span>10 s</span></div>`;
  const cropWidth = crop => crop.width - (crop.left || 0) - (crop.right || 0);
  const cropHeight = crop => crop.height - crop.top - (crop.bottom || 0);
  const frameStyle = crop => crop?.left ? `position:relative;overflow:hidden;aspect-ratio:${cropWidth(crop)}/${cropHeight(crop)};` : "";
  const imageStyle = crop => crop?.left ? `position:absolute;max-width:none;max-height:none;width:${crop.width / cropWidth(crop) * 100}%;height:auto;left:${-crop.left / cropWidth(crop) * 100}%;top:${-crop.top / cropHeight(crop) * 100}%;` : crop ? `aspect-ratio:${crop.width}/${crop.height - crop.top};object-fit:cover;object-position:bottom;` : "";
  const spectrogram = (source, label) => source.image ? `<button class="zoom-button" type="button" data-image="${escape(source.image)}" data-crop="${escape(JSON.stringify(source.imageCrop || null))}" data-caption="${escape(label)}" aria-label="Enlarge spectrogram: ${escape(label)}"><span class="spectrogram-crop" style="${frameStyle(source.imageCrop)}"><img class="mel-image" src="${escape(source.image)}" style="${imageStyle(source.imageCrop)}" alt="Mel spectrogram: ${escape(label)}" loading="lazy"></span></button>` : "";
  const player = (source, label, note) => `<div class="audio-wrap"><audio controls preload="none" src="${escape(source.audio)}" aria-label="${escape(label)}"></audio><p class="audio-error" hidden>Audio could not be loaded.</p><div class="player-meta"><span>${escape(note)}</span></div></div>`;

  const figureCell = sample => {
    const label = `Figure 1 (${sample.panel}), ${sample.method}, ${title(sample)}, ${sample.overlap}% overlap`;
    return `<td class="figure-cell ${sample.method === "SATAG" ? "figure-ours" : ""}"><article class="sample-card" id="${escape(sample.id)}" aria-labelledby="${escape(sample.id)}-title"><div class="figure-cell-heading"><h3 id="${escape(sample.id)}-title"><span class="figure-panel">(${escape(sample.panel)})</span> ${escape(sample.method)}</h3><span class="figure-overlap">${sample.overlap}% overlap</span></div>${timeline(sample)}${spectrogram(sample, label)}<div class="audio-wrap"><audio controls preload="metadata" src="${escape(sample.audio)}" aria-label="${escape(label)}"></audio><p class="audio-error" hidden>Audio could not be loaded.</p></div></article></td>`;
  };
  const figureRows = ["keyboard-bird", "speech-cat"].map(pairId => {
    const samples = data.figure.filter(sample => sample.pair === pairId);
    const columns = [
      samples.find(sample => sample.method === "DegDiT" && sample.overlap === 0),
      samples.find(sample => sample.method === "DegDiT" && sample.overlap > 0),
      samples.find(sample => sample.method === "SATAG")
    ];
    const names = samples[0].events.map(event => escape(event.name));
    return `<tr><th scope="row" class="figure-pair"><span>${names[0]}</span><span class="figure-pair-plus">+</span><span>${names[1]}</span></th>${columns.map(figureCell).join("")}</tr>`;
  });
  document.getElementById("figure-grid").innerHTML = `<table class="figure-table"><caption class="sr-only">Figure 1 audio examples, grouped by event pair. DegDiT with no overlap, DegDiT with overlap, and SATAG with overlap.</caption><thead><tr><th scope="col">Event pair</th><th scope="col">DegDiT<span>Non-overlapping</span></th><th scope="col">DegDiT<span>Overlapping</span></th><th scope="col" class="figure-ours">SATAG <small>(Ours)</small><span>Overlapping</span></th></tr></thead><tbody>${figureRows.join("")}</tbody></table>`;

  const datasetColors = ["#2563eb", "#dc2626", "#059669", "#9333ea"];
  const datasetRanges = event => event.intervals.map(([start, end]) => `${start}–${end}`).join(", ");
  const datasetTimeline = sample => `<div class="dataset-timeline" role="img" aria-label="SpotSound event intervals for ${escape(sample.id)}">${sample.events.map((event, eventIndex) => `<div class="dataset-event"><div class="dataset-event-label"><span><i style="background:${datasetColors[eventIndex % datasetColors.length]}"></i>${escape(event.name)}</span><time>${datasetRanges(event)} s</time></div><div class="dataset-track">${event.intervals.map(([start, end]) => `<i style="left:${start / sample.duration * 100}%;width:${(end - start) / sample.duration * 100}%;background:${datasetColors[eventIndex % datasetColors.length]}"></i>`).join("")}<span class="playhead" aria-hidden="true"></span></div></div>`).join("")}<div class="timeline-axis" aria-hidden="true"><span>0 s</span><span>2</span><span>4</span><span>6</span><span>8</span><span>10 s</span></div></div>`;
  document.getElementById("dataset-grid").innerHTML = window.SATAG_AUDIOCAPS_SAMPLES.map((sample, index) => `<article class="dataset-card" id="dataset-${escape(sample.id)}" data-duration="${sample.duration}"><div class="dataset-card-head"><h3 class="dataset-number">Sample ${index + 1}</h3></div><div class="dataset-caption"><span>Original AudioCaps caption</span><p>${escape(sample.caption)}</p></div><div class="dataset-annotations"><h4>Event annotations <span>(seconds)</span></h4>${datasetTimeline(sample)}</div>${player(sample, `AudioCapsT sample ${index + 1}: ${sample.caption}`, "Original dataset audio")}</article>`).join("");

  const amplitudeRows = data.mixing.map(sample => {
    const cells = sample.variants.map((variant, index) => {
      variant = {...variant, imageCrop: {width: 660, height: 235, left: 64, right: 10, top: 4, bottom: 43}};
      const label = `${sample.main} + ${sample.background}, ${variant.label}`;
      return `<td class="amplitude-cell ${variant.weights ? "amplitude-weighted" : ""}"><article class="amplitude-clip" id="${escape(sample.id)}-condition-${index}" aria-label="${escape(label)}"><h3 class="amplitude-mobile-label">${escape(variant.label)}</h3>${spectrogram(variant, label)}${player(variant, label, variant.weights ? `Main : Background = ${variant.weights.join(" : ")}` : "Unnormalized reference")}</article></td>`;
    }).join("");
    return `<tr><th scope="row" class="amplitude-pair"><span class="amplitude-role">Main event</span><strong>${escape(sample.main)}</strong><span class="amplitude-role">Background event</span><strong>${escape(sample.background)}</strong><span class="amplitude-interval">${sample.start.toFixed(2)}–${sample.end.toFixed(2)} s · 100% overlap</span></th>${cells}</tr>`;
  }).join("");
  document.getElementById("mixing-content").innerHTML = `<table class="amplitude-table"><caption class="sr-only">Relative amplitude control: raw summation, main/background weights 7 to 3, and main/background weights 3 to 7 for two event pairs.</caption><thead><tr><th scope="col">Event pair</th><th scope="col">Raw summation<span>Without peak normalization</span></th><th scope="col" class="amplitude-weighted"><strong>7 : 3</strong><span>Main : Background</span></th><th scope="col" class="amplitude-weighted"><strong>3 : 7</strong><span>Main : Background</span></th></tr></thead><tbody>${amplitudeRows}</tbody></table>`;

  const comparisonPairs = window.SATAG_OVERLAP_SAMPLES;
  const comparisonTimes = sample => `<div class="comparison-times">${sample.events.map((event, index) => `<span><b class="event-code event-${index}">${index ? "B" : "A"}</b>${event.start.toFixed(2)}–${event.end.toFixed(2)} s</span>`).join("")}</div>`;
  const comparisonTrack = sample => `<div class="comparison-track" role="img" aria-label="Requested intervals: ${escape(times(sample))}">${sample.events.map((event, index) => `<i class="comparison-bar event-${index}" style="left:${event.start / sample.duration * 100}%;width:${(event.end - event.start) / sample.duration * 100}%"></i>`).join("")}<i class="playhead" aria-hidden="true"></i></div><div class="comparison-axis" aria-hidden="true"><span>0 s</span><span>5</span><span>10 s</span></div>`;
  const comparisonCell = sample => {
    const label = `${title(sample)}, ${sample.method}, ${sample.overlap}% overlap`;
    return `<td class="comparison-cell ${sample.method === "SATAG" ? "comparison-ours" : ""}"><article class="comparison-clip" id="${escape(sample.id)}" aria-label="${escape(label)}"><div class="comparison-mobile-heading"><h3>${sample.overlap === 0 ? "0% overlap · DegDiT" : `${escape(sample.method)} · ${sample.overlap}% overlap`}</h3>${comparisonTimes(sample)}</div>${spectrogram(sample, label)}${comparisonTrack(sample)}<div class="audio-wrap"><audio controls preload="none" src="${escape(sample.audio)}" aria-label="${escape(label)}"></audio><p class="audio-error" hidden>Audio could not be loaded.</p></div></article></td>`;
  };
  const comparisonHeads = comparisonPairs[0].clips.map(sample => `<th scope="col" class="${sample.method === "SATAG" ? "comparison-ours" : ""}"><strong>${sample.overlap === 0 ? "0% overlap" : escape(sample.method)}</strong><span class="comparison-condition">${sample.overlap === 0 ? "DegDiT · shared baseline" : `${sample.overlap}% overlap`}</span>${comparisonTimes(sample)}</th>`).join("");
  const comparisonRows = comparisonPairs.map((pair, index) => `<tr><th scope="row" class="comparison-pair"><span class="comparison-number">${index + 1}</span>${pair.events.map((name, eventIndex) => `<span class="comparison-event"><b class="event-code event-${eventIndex}">${eventIndex ? "B" : "A"}</b>${escape(name)}</span>`).join("")}</th>${pair.clips.map(comparisonCell).join("")}</tr>`).join("");
  document.getElementById("comparison-content").innerHTML = `<table class="overlap-table"><caption class="sr-only">${comparisonPairs.length} event pairs with five conditions: shared DegDiT 0% baseline, DegDiT 50%, DegDiT 100%, SATAG 50%, and SATAG 100%.</caption><thead><tr><th scope="col">Event pair</th>${comparisonHeads}</tr></thead><tbody>${comparisonRows}</tbody></table>`;

  // Capture handles dynamically rendered players; never allow two examples to play together.
  document.addEventListener("play", event => {
    if (!(event.target instanceof HTMLAudioElement)) return;
    document.querySelectorAll("audio").forEach(audio => { if (audio !== event.target) audio.pause(); });
  }, true);
  document.addEventListener("timeupdate", event => {
    if (!(event.target instanceof HTMLAudioElement)) return;
    const scope = event.target.closest(".sample-card") || event.target.closest(".dataset-card") || event.target.closest(".mixing-example-card") || event.target.closest(".comparison-clip");
    scope?.querySelectorAll(".playhead").forEach(head => {
      head.style.left = `${Math.min(100, event.target.currentTime / Number(scope.dataset.duration || 10) * 100)}%`;
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
    const crop = JSON.parse(button.dataset.crop || "null");
    image.style.cssText = imageStyle(crop);
    if (crop) image.style.maxHeight = "none";
    const frame = document.getElementById("dialog-image-frame");
    frame.style.cssText = frameStyle(crop);
    frame.style.maxWidth = crop ? `calc(65vh * ${cropWidth(crop) / cropHeight(crop)})` : "";
    image.src = button.dataset.image;
    image.alt = button.dataset.caption;
    document.getElementById("dialog-caption").textContent = button.dataset.caption;
    dialog.showModal();
  });
  dialog.querySelector(".dialog-close").addEventListener("click", () => dialog.close());
  document.getElementById("copy-bibtex").addEventListener("click", async () => {
    const status = document.getElementById("bibtex-status");
    try {
      await navigator.clipboard.writeText(document.getElementById("bibtex-code").textContent);
      status.textContent = "BibTeX copied.";
    } catch {
      status.textContent = "Select the citation text and copy it manually.";
    }
  });
  dialog.addEventListener("click", event => { if (event.target === dialog) { const rect = dialog.getBoundingClientRect(); if (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom) dialog.close(); } });
})();
