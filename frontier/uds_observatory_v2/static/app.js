/* SPDX-License-Identifier: Apache-2.0 */
'use strict';

const byId = (id) => document.getElementById(id);
const inventoryGrid = byId('inventory-grid');
const topology = byId('topology');
const form = byId('validator-form');
const manifest = byId('manifest');
const encoder = new TextEncoder();

function element(tag, className, text) {
  const value = document.createElement(tag);
  if (className) value.className = className;
  if (text !== undefined) value.textContent = text;
  return value;
}

function badge(text, state) {
  return element('span', `badge badge-${state.toLowerCase()}`, text);
}

function countReferences(item) {
  return item?.inspection?.references?.length || 0;
}

function countUnpinned(item) {
  const findings = item?.inspection?.findings || [];
  return findings.filter((finding) => finding.code === 'REFERENCE_NOT_DIGEST_PINNED').length;
}

function addDefinition(list, term, value) {
  list.append(element('dt', '', term), element('dd', '', value ?? 'UNAVAILABLE'));
}

function renderInventory(items) {
  inventoryGrid.replaceChildren();
  items.forEach((item) => {
    const article = element('article', 'manifest-card');
    const head = element('div', 'card-head');
    head.append(badge(item.state, item.state === 'INVALID' ? 'invalid' : 'declared'), element('span', 'manifest-id', item.id));
    const title = element('h3', '', item.path);
    const facts = element('dl', 'facts');
    addDefinition(facts, 'Bytes', String(item.bytes));
    addDefinition(facts, 'SHA-256', item.sha256);
    addDefinition(facts, 'References', String(countReferences(item)));
    addDefinition(facts, 'Deployment', item?.inspection?.deployment || 'NOT_ATTEMPTED');
    article.append(head, title, facts);

    const findings = item?.inspection?.findings || [];
    if (findings.length) {
      const list = element('ul', 'finding-list');
      findings.slice(0, 8).forEach((finding) => {
        const li = element('li', `finding-${finding.severity}`);
        li.append(element('strong', '', finding.code), element('span', '', finding.message));
        list.append(li);
      });
      article.append(list);
    }
    inventoryGrid.append(article);
  });
  byId('empty-state').hidden = items.length !== 0;
}

function renderTopology(items) {
  topology.replaceChildren();
  if (!items.length) {
    topology.append(element('p', 'topology-empty', 'No recognized local manifest nodes.'));
    return;
  }
  items.slice(0, 16).forEach((item, index) => {
    const group = element('div', 'topology-group');
    group.style.setProperty('--order', String(index));
    const packageNode = element('div', 'package-node');
    packageNode.append(element('span', 'node-kicker', 'MANIFEST'), element('strong', '', item.path));
    group.append(packageNode);
    const refs = item?.inspection?.references || [];
    refs.slice(0, 5).forEach((reference) => {
      const refNode = element('div', `reference-node ${reference.digest_pinned ? 'is-pinned' : 'is-declared'}`);
      refNode.append(
        element('span', 'node-kicker', reference.digest_pinned ? 'DIGEST PINNED' : 'DECLARED'),
        element('span', '', reference.value),
      );
      group.append(refNode);
    });
    topology.append(group);
  });
}

async function loadSource() {
  try {
    const response = await fetch('/api/source', { headers: { Accept: 'application/json' }, credentials: 'same-origin' });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const payload = await response.json();
    const source = payload.source || {};
    byId('source-state').textContent = source.state === 'MEASURED'
      ? String(source.revision).slice(0, 12).toUpperCase()
      : 'UNAVAILABLE';
  } catch (_error) {
    byId('source-state').textContent = 'UNAVAILABLE';
  }
}

async function loadInventory() {
  try {
    const response = await fetch('/api/bundles', { headers: { Accept: 'application/json' }, credentials: 'same-origin' });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || `HTTP ${response.status}`);
    const items = Array.isArray(payload.items) ? payload.items : [];
    const references = items.reduce((sum, item) => sum + countReferences(item), 0);
    const unpinned = items.reduce((sum, item) => sum + countUnpinned(item), 0);
    const invalid = items.filter((item) => item.state === 'INVALID').length;
    byId('bundle-count').textContent = String(items.length);
    byId('reference-count').textContent = String(references);
    byId('unpinned-count').textContent = String(unpinned);
    byId('invalid-count').textContent = String(invalid);
    byId('inventory-state').textContent = `${items.length} local manifest${items.length === 1 ? '' : 's'} · ${payload.deployment}`;
    renderInventory(items);
    renderTopology(items);
  } catch (error) {
    byId('inventory-state').textContent = `Inventory unavailable: ${String(error.message || error)}`;
    byId('empty-state').hidden = false;
    renderTopology([]);
  }
}

function updateByteCount() {
  const bytes = encoder.encode(manifest.value).byteLength;
  byId('byte-count').value = `${bytes.toLocaleString()} bytes`;
  byId('byte-count').textContent = `${bytes.toLocaleString()} bytes`;
}

function renderValidation(payload, ok) {
  const wrapper = byId('validation-result');
  const summary = byId('validation-summary');
  const inspection = payload.inspection || {};
  wrapper.hidden = false;
  summary.replaceChildren();
  if (ok) {
    summary.append(
      badge(inspection.state || 'DECLARED', inspection.state === 'INVALID' ? 'invalid' : 'declared'),
      element('strong', '', `${inspection.references?.length || 0} declared references`),
      element('span', '', `Receipt ${String(payload.receipt_sha256 || '').slice(0, 16)}`),
    );
  } else {
    summary.append(badge('REJECTED', 'invalid'), element('strong', '', payload.detail || 'Manifest validation failed'));
  }
  byId('validation-json').textContent = JSON.stringify(payload, null, 2);
  wrapper.scrollIntoView({ behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth', block: 'nearest' });
}

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  const submit = form.querySelector('button[type="submit"]');
  submit.disabled = true;
  submit.textContent = 'Validating…';
  try {
    const response = await fetch('/api/validate', {
      method: 'POST',
      credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify({ text: manifest.value, format: byId('format').value }),
    });
    const payload = await response.json();
    renderValidation(payload, response.ok);
  } catch (error) {
    renderValidation({ detail: String(error.message || error), state: 'UNAVAILABLE' }, false);
  } finally {
    submit.disabled = false;
    submit.textContent = 'Validate locally';
  }
});

byId('load-example').addEventListener('click', () => {
  manifest.value = [
    'kind: ZarfPackageConfig',
    'metadata:',
    '  name: bounded-example',
    '  version: 0.1.0',
    'components:',
    '  - name: api',
    '    required: true',
    '    images:',
    '      - registry.example.test/szl/api@sha256:' + 'a'.repeat(64),
  ].join('\n');
  updateByteCount();
  manifest.focus();
});

manifest.addEventListener('input', updateByteCount);
updateByteCount();
Promise.all([loadSource(), loadInventory()]);
