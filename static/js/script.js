const form = document.querySelector('#chat');
const input = document.querySelector('#question');
const send = document.querySelector('#send');
const clear = document.querySelector('#clear');
const messages = document.querySelector('#messages');
const status = document.querySelector('#status');
const welcome = document.querySelector('#welcome');
const suggestions = document.querySelector('#suggestions');
const panel = document.querySelector('#question-panel');
const topicButtons = [...document.querySelectorAll('[data-topic]')];
const nameDialog = document.querySelector('#name-dialog');
const nameInput = document.querySelector('#preferred-name');
const clearDialog = document.querySelector('#clear-dialog');

let busy = false;
let topics = [];
let displayName = '';
let conversationContext = { programs: [] };
let latestTurn = 0;
let hasKnowledge = false;

try {
  displayName = (sessionStorage.getItem('ccitDisplayName') || '').slice(0, 32);
} catch { /* Optional tab-local personalization. */ }

function updateGreeting() {
  document.querySelector('#greeting').textContent = `Hello, ${displayName || 'there'}!`;
  document.querySelector('#profile-name').textContent = displayName || 'Guest';
}

function resizeInput() {
  input.style.height = '28px';
  input.style.height = `${Math.min(input.scrollHeight, 140)}px`;
  send.disabled = busy || !input.value.trim();
}

function setBusy(value) {
  busy = value;
  clear.disabled = value;
  form.setAttribute('aria-busy', String(value));
  for (const button of document.querySelectorAll('.recovery-button')) button.disabled = value;
  resizeInput();
}

function scrollToLatest() {
  messages.scrollTop = messages.scrollHeight;
}

function beginConversation() {
  document.body.classList.add('has-conversation');
  welcome.hidden = true;
  suggestions.hidden = true;
  panel.hidden = true;
  messages.hidden = false;
}

// Build text/list elements without inserting user, model or source HTML.
function renderText(container, text, useLists = false) {
  if (!useLists) {
    const paragraph = document.createElement('p');
    paragraph.textContent = text;
    container.append(paragraph);
    return;
  }
  let list = null;
  for (const line of text.split('\n')) {
    const bullet = line.match(/^\s*[-•]\s+(.+)$/);
    const numbered = line.match(/^\s*\d+\.\s+(.+)$/);
    if (bullet || numbered) {
      const tag = numbered ? 'OL' : 'UL';
      if (!list || list.tagName !== tag) {
        list = document.createElement(tag.toLowerCase());
        container.append(list);
      }
      const item = document.createElement('li');
      item.textContent = (bullet || numbered)[1];
      list.append(item);
    } else {
      list = null;
      if (line.trim()) {
        const paragraph = document.createElement('p');
        paragraph.textContent = line;
        container.append(paragraph);
      }
    }
  }
}

function placeMessage(item, replacing = null) {
  if (replacing && replacing.isConnected) replacing.replaceWith(item);
  else messages.append(item);
  scrollToLatest();
  return item;
}

function addMessage(text, kind = 'assistant', data = {}, replacing = null) {
  const item = document.createElement('article');
  item.className = `message ${kind}`;
  const label = document.createElement('span');
  label.className = 'message-label';
  label.textContent = kind === 'user' ? 'You' : 'CCIThink';
  const content = document.createElement('div');
  content.className = 'message-text';
  renderText(content, text, kind === 'assistant');
  item.append(label, content);

  if (data.mode === 'faq') {
    const modeLabel = document.createElement('small');
    modeLabel.className = 'message-mode';
    modeLabel.textContent = 'FAQ retrieval only · not AI generated';
    item.append(modeLabel);
  }
  for (const warning of data.warnings || []) {
    const note = document.createElement('small');
    note.className = 'source-warning';
    note.textContent = warning;
    item.append(note);
  }
  if ((data.sources || []).length) {
    const sourceLabel = document.createElement('small');
    sourceLabel.className = 'message-sources';
    sourceLabel.textContent = 'Source: ' + data.sources.map(source => `${source.source || 'About CCIT'} · ${source.id}`).join('; ');
    item.append(sourceLabel);

    const disclosure = document.createElement('details');
    disclosure.className = 'source-details';
    const summary = document.createElement('summary');
    summary.textContent = 'View source and full details';
    disclosure.append(summary);
    for (const source of data.sources) {
      const heading = document.createElement('h3');
      heading.textContent = source.title;
      disclosure.append(heading);
      const detail = (data.details || []).find(entry => entry.id === source.id);
      if (detail) {
        const quote = document.createElement('p');
        quote.className = 'source-quote';
        quote.textContent = detail.answer;
        disclosure.append(quote);
      }
      const provenance = document.createElement('p');
      provenance.className = 'source-provenance';
      provenance.textContent = [
        source.reviewed_at ? `Checked against source: ${source.reviewed_at}.` : '',
        source.currency_status === 'unconfirmed' ? 'Current department details are unconfirmed.' : '',
      ].filter(Boolean).join(' ');
      disclosure.append(provenance);
    }
    item.append(disclosure);
  }
  if (kind === 'assistant' && text) {
    const copy = document.createElement('button');
    copy.type = 'button';
    copy.className = 'copy-answer';
    copy.textContent = 'Copy answer';
    copy.addEventListener('click', async () => {
      try {
        await navigator.clipboard.writeText(text);
        copy.textContent = 'Copied';
      } catch {
        const range = document.createRange();
        range.selectNodeContents(content);
        const selection = window.getSelection();
        selection.removeAllRanges();
        selection.addRange(range);
        copy.textContent = 'Text selected — copy it';
      }
    });
    item.append(copy);
  }
  return placeMessage(item, replacing);
}

function addTypingIndicator(replacing) {
  const item = addMessage('', 'assistant', {}, replacing);
  item.classList.add('typing');
  const dots = document.createElement('span');
  dots.className = 'typing-dots';
  dots.setAttribute('aria-hidden', 'true');
  for (let i = 0; i < 3; i++) dots.append(document.createElement('span'));
  const announcement = document.createElement('span');
  announcement.className = 'sr-only';
  announcement.textContent = 'Preparing an answer…';
  item.querySelector('.message-text').append(dots, announcement);
  scrollToLatest();
  return item;
}

function addError(text, state, replacing, canUseFaq) {
  const item = addMessage(text, 'error', {}, replacing);
  const actions = document.createElement('div');
  actions.className = 'recovery-actions';
  const retry = document.createElement('button');
  retry.type = 'button';
  retry.className = 'recovery-button secondary-button';
  retry.textContent = 'Retry';
  retry.addEventListener('click', () => sendRequest(state, item));
  actions.append(retry);
  if (canUseFaq && state.mode !== 'faq') {
    const faq = document.createElement('button');
    faq.type = 'button';
    faq.className = 'recovery-button primary-button';
    faq.textContent = 'Read FAQ answer instead';
    faq.addEventListener('click', () => sendRequest({ ...state, mode: 'faq' }, item));
    actions.append(faq);
  }
  item.append(actions);
  scrollToLatest();
}

async function sendRequest(state, replacing = null) {
  if (busy) return;
  setBusy(true);
  beginConversation();
  const waiting = addTypingIndicator(replacing);
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 35000);
  try {
    const body = { message: state.message, context: state.context };
    if (state.mode) body.mode = state.mode;
    const response = await fetch('/api/chat', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body), signal: controller.signal,
    });
    const data = await response.json();
    if (!response.ok || !data.success) {
      addError(data.error || 'Unable to answer. Please try again.', state, waiting, data.can_use_faq === true);
    } else {
      addMessage(data.reply, 'assistant', data, waiting);
      // Retrying an older turn must not overwrite the newer topic context.
      if (state.turn === latestTurn) conversationContext = data.context || { programs: [] };
    }
  } catch (error) {
    addError(error.name === 'AbortError'
      ? 'This is taking longer than expected. Please try again.'
      : 'The request could not be completed. Please try again.', state, waiting, hasKnowledge);
  } finally {
    clearTimeout(timer);
    setBusy(false);
    input.focus();
  }
}

function submit() {
  const question = input.value.trim();
  if (busy || !question || question.length > 1000) return;
  const state = { message: question, context: structuredClone(conversationContext), turn: ++latestTurn };
  beginConversation();
  addMessage(question, 'user');
  input.value = '';
  resizeInput();
  sendRequest(state);
}

function openTopic(button) {
  const topic = topics.find(item => item.id === button.dataset.topic);
  if (!topic || busy) return;
  const opening = button.getAttribute('aria-expanded') !== 'true';
  for (const card of topicButtons) card.setAttribute('aria-expanded', 'false');
  panel.hidden = !opening;
  if (!opening) return;
  button.setAttribute('aria-expanded', 'true');
  document.querySelector('#topic-title').textContent = topic.title;
  document.querySelector('#topic-note').textContent = topic.note;
  const list = document.querySelector('#question-list');
  list.replaceChildren();
  for (const question of topic.questions) {
    const suggestion = document.createElement('button');
    suggestion.type = 'button';
    suggestion.textContent = question;
    suggestion.addEventListener('click', () => {
      input.value = question;
      resizeInput();
      submit();
    });
    list.append(suggestion);
  }
  if (!topic.questions.length) {
    const empty = document.createElement('p');
    empty.className = 'topic-note';
    empty.textContent = 'No reviewed questions are available for this topic yet.';
    list.append(empty);
  }
  panel.scrollIntoView({ block: 'nearest' });
}

form.addEventListener('submit', event => { event.preventDefault(); submit(); });
input.addEventListener('input', resizeInput);
input.addEventListener('keydown', event => {
  if (event.key === 'Enter' && !event.shiftKey && !event.isComposing) {
    event.preventDefault();
    submit();
  }
});
for (const button of topicButtons) button.addEventListener('click', () => openTopic(button));
clear.addEventListener('click', () => {
  if (messages.childElementCount) clearDialog.showModal();
  else input.focus();
});
document.querySelector('#cancel-clear').addEventListener('click', () => clearDialog.close());
document.querySelector('#confirm-clear').addEventListener('click', () => {
  messages.replaceChildren();
  messages.hidden = true;
  input.value = '';
  conversationContext = { programs: [] };
  latestTurn++;
  document.body.classList.remove('has-conversation');
  welcome.hidden = false;
  suggestions.hidden = false;
  panel.hidden = true;
  for (const card of topicButtons) card.setAttribute('aria-expanded', 'false');
  clearDialog.close();
  resizeInput();
  input.focus();
});
document.querySelector('#profile').addEventListener('click', () => {
  nameInput.value = displayName;
  nameDialog.showModal();
  nameInput.focus();
});
document.querySelector('#cancel-name').addEventListener('click', () => nameDialog.close());
document.querySelector('#name-form').addEventListener('submit', event => {
  event.preventDefault();
  displayName = nameInput.value.trim().replace(/\s+/g, ' ').slice(0, 32);
  try { sessionStorage.setItem('ccitDisplayName', displayName); } catch { /* Optional storage. */ }
  updateGreeting();
  nameDialog.close();
});

async function loadHealth() {
  try {
    const response = await fetch('/api/health');
    if (!response.ok) throw new Error('Unavailable');
    const health = await response.json();
    hasKnowledge = health.verified_records > 0;
    status.classList.toggle('status-error', !health.ready);
    status.textContent = health.ready
      ? (health.mode === 'faq'
        ? 'FAQ mode · answers from the department document, not AI generated.'
        : 'AI mode · answers grounded in the department document.')
      : 'Setup incomplete: ' + (!health.verified_records
        ? 'reviewed About CCIT information is required.'
        : 'the AI service must be configured. FAQ answers are available.');
  } catch {
    status.classList.add('status-error');
    status.textContent = 'Cannot connect to the assistant. Please try again later.';
  }
}

async function loadTopics() {
  try {
    const response = await fetch('/api/suggestions');
    if (!response.ok) throw new Error('Unavailable');
    const data = await response.json();
    topics = data.topics || [];
    for (const button of topicButtons) button.disabled = !topics.some(topic => topic.id === button.dataset.topic);
  } catch {
    for (const button of topicButtons) button.title = 'Suggested questions are temporarily unavailable.';
  }
}

updateGreeting();
resizeInput();
loadHealth();
loadTopics();
