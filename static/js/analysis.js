const classifyForm = document.querySelector('#classify-form');
if (classifyForm) {
  classifyForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    const button = classifyForm.querySelector('button');
    const question = document.querySelector('#classify-question');
    const status = document.querySelector('#classify-status');
    const results = document.querySelector('#classify-results');
    if (button.disabled || !question.value.trim()) return;
    button.disabled = true;
    results.replaceChildren();
    status.textContent = 'Predicting the FAQ topic…';
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 10000);
    try {
      const response = await fetch('/api/classify', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: question.value.trim() }), signal: controller.signal,
      });
      const data = await response.json();
      if (!response.ok || !data.success) throw new Error(data.error || 'Prediction unavailable.');
      for (const prediction of data.predictions) {
        const item = document.createElement('li');
        const title = document.createElement('strong');
        title.textContent = prediction.title;
        item.append(title, document.createTextNode(` — ${prediction.faq_id}; relative score ${prediction.score.toFixed(3)}`));
        results.append(item);
      }
      status.textContent = data.predictions.length ? data.note : 'No known vocabulary was found. Try a public CCIT question.';
    } catch (error) {
      status.textContent = error.name === 'AbortError' ? 'Prediction timed out. Try again.' : error.message;
    } finally {
      clearTimeout(timer);
      button.disabled = false;
    }
  });
}
