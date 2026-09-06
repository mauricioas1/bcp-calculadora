const form = document.querySelector('#bcp-form');
const currentTotal = document.querySelector('#current-total');
const sessionTotal = document.querySelector('#session-total');
const history = document.querySelector('#history');
const formMessage = document.querySelector('#form-message');
const classifyButton = document.querySelector('#classify-button');
const storyDescription = document.querySelector('#story-description');
const aiStatus = document.querySelector('#ai-status');
const justifications = document.querySelector('#ai-justifications');
const breakdownLabels = {
  business_rules: 'Regras de negócio',
  interface_elements: 'Elementos de interface',
  boundaries: 'Integrações e fronteiras',
};
let stories = [];

classifyButton.addEventListener('click', async () => {
  const story = storyDescription.value.trim();
  if (story.length < 20) {
    aiStatus.textContent = 'Descreva a história com pelo menos 20 caracteres.';
    return;
  }

  classifyButton.disabled = true;
  aiStatus.textContent = 'Analisando a história...';
  try {
    const response = await fetch('/api/classificar', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ story }),
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || 'Não foi possível classificar.');

    const values = {
      business_rules: result.classification.regras.nota,
      interface_elements: result.classification.interface.nota,
      boundaries: result.classification.integracoes.nota,
    };
    renderResult({ total: result.total, values });
    renderJustifications(result.classification);
    stories.push({ name: story.slice(0, 80), total: result.total, values });
    renderHistory();
    aiStatus.textContent = 'Classificação concluída. Revise as justificativas antes de usar a estimativa.';
  } catch (error) {
    aiStatus.textContent = error.message;
  } finally {
    classifyButton.disabled = false;
  }
});

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  formMessage.textContent = '';

  const selections = {};
  document.querySelectorAll('.dimension').forEach((dimension) => {
    selections[dimension.dataset.category] = dimension.querySelector('select').value;
  });

  try {
    const response = await fetch('/api/calculate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ selections }),
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || 'Não foi possível calcular.');

    const name = document.querySelector('#story-name').value.trim();
    stories.push({ name, total: result.total, values: result.values });
    renderResult(result);
    renderHistory();
    form.reset();
  } catch (error) {
    formMessage.textContent = error.message;
  }
});

function renderResult(result) {
  currentTotal.textContent = result.total;
  document.querySelectorAll('.breakdown div').forEach((row, index) => {
    const category = Object.keys(breakdownLabels)[index];
    row.querySelector('span').textContent = breakdownLabels[category];
    row.querySelector('b').textContent = `${result.values[category]} BCP`;
  });
}

function renderJustifications(classification) {
  const labels = { regras: 'Regras de negócio', interface: 'Elementos de interface', integracoes: 'Integrações e fronteiras' };
  justifications.hidden = false;
  justifications.innerHTML = Object.entries(labels).map(([key, label]) => `
    <div><strong>${label}: ${classification[key].nota}/3</strong><p>${escapeHtml(classification[key].justificativa)}</p></div>
  `).join('');
}

function renderHistory() {
  const total = stories.reduce((sum, story) => sum + story.total, 0);
  sessionTotal.textContent = `${total} BCP`;
  history.innerHTML = stories.map((story) => `
    <article class="history-item">
      <div><strong>${escapeHtml(story.name)}</strong><small>${story.values.business_rules} + ${story.values.interface_elements} + ${story.values.boundaries} BCP nas dimensões</small></div>
      <strong>${story.total} BCP</strong>
    </article>
  `).join('');
}

function escapeHtml(value) {
  return value.replace(/[&<>'"]/g, (character) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[character]));
}
