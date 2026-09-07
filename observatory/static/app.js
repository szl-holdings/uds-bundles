"use strict";

const state = { items: [] };
const $ = (selector) => document.querySelector(selector);

function text(value) {
  return document.createTextNode(String(value ?? "UNAVAILABLE"));
}

function badge(value) {
  const node = document.createElement("span");
  node.className = `badge badge-${String(value).toLowerCase()}`;
  node.append(text(value));
  return node;
}

function render(items) {
  const grid = $("#bundle-grid");
  grid.replaceChildren();
  if (!items.length) {
    const empty = document.createElement("p");
    empty.className = "empty";
    empty.append(text("No matching bundle manifests."));
    grid.append(empty);
    return;
  }

  for (const item of items) {
    const card = document.createElement("article");
    card.className = "bundle-card";
    card.tabIndex = 0;

    const head = document.createElement("div");
    head.className = "card-head";
    const title = document.createElement("h3");
    title.append(text(item.slug));
    const root = document.createElement("small");
    root.append(text(item.source_root));
    head.append(title, root);

    const manifests = document.createElement("ul");
    for (const manifest of item.manifests) {
      const row = document.createElement("li");
      const left = document.createElement("span");
      left.append(text(manifest.name));
      row.append(left, badge(manifest.status));
      manifests.append(row);
    }

    const digest = document.createElement("code");
    digest.append(text(item.manifests[0]?.sha256?.slice(0, 16) ?? "UNAVAILABLE"));
    card.append(head, manifests, digest);
    grid.append(card);
  }
}

async function loadCatalog() {
  const status = $("#runtime-status");
  status.textContent = "Reading source";
  try {
    const response = await fetch("/api/bundles", { headers: { Accept: "application/json" }, cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const catalog = await response.json();
    state.items = Array.isArray(catalog.items) ? catalog.items : [];
    $("#bundle-count").textContent = String(catalog.bundle_count ?? 0);
    $("#manifest-count").textContent = String(catalog.manifest_count ?? 0);
    $("#valid-count").textContent = String(catalog.manifest_states?.VALID ?? 0);
    $("#receipt").textContent = `sha256:${String(catalog.receipt_sha256 ?? "UNAVAILABLE").slice(0, 16)}`;
    render(state.items);
    status.textContent = "Source measured";
    status.dataset.state = "ready";
  } catch (error) {
    status.textContent = "Source unavailable";
    status.dataset.state = "error";
    render([]);
    $("#receipt").textContent = String(error.message || error);
  }
}

$("#search").addEventListener("input", (event) => {
  const query = event.target.value.trim().toLowerCase();
  render(state.items.filter((item) => item.slug.toLowerCase().includes(query)));
});

$("#refresh").addEventListener("click", loadCatalog);

$("#validate").addEventListener("click", async () => {
  const output = $("#validation-output");
  output.textContent = "Validating…";
  try {
    const response = await fetch("/api/validate", {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify({ filename: $("#filename").value, manifest: $("#manifest").value }),
    });
    const payload = await response.json();
    output.textContent = JSON.stringify(payload, null, 2);
    output.focus();
  } catch (error) {
    output.textContent = JSON.stringify({ status: "UNAVAILABLE", detail: String(error.message || error) }, null, 2);
  }
});

loadCatalog();
