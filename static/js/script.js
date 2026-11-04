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

// Personalization is local to the tab; this is not an account or a login.
try {
  displayName = (sessionStorage.getItem('ccitDisplayName') || '').slice(0, 32);
} catch { /* Storage can be unavailable in private browsing. */ }

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

function addMessage(text, kind = 'assistant', sources = [], mode = '') {
  const item = document.createElement('article');
  item.className = `message ${kind}`;
  const label = document.createElement('span');
  label.className = 'message-label';
  label.textContent = kind === 'user' ? 'You' : 'CCIThink';
  const content = document.createElement('div');
  content.className = 'message-text';
  content.textContent = text;
  item.append(label, content);

  if (mode === 'faq') {
    const modeLabel = document.createElement('small');
    modeLabel.className = 'message-mode';
    modeLabel.textContent = 'FAQ retrieval only · not AI generated';
    item.append(modeLabel);
  }

  if (sources.length) {
    const sourceLabel = document.createElement('small');
    sourceLabel.className = 'message-sources';
    sourceLabel.textContent = 'Source: ' + sources.map(source => `${source.source || 'About CCIT'} · ${source.id} — ${source.title}`).join('; ');
    item.append(sourceLabel);
  }

  messages.append(item);
  scrollToLatest();
  return item;
}

function addTypingIndicator() {
  const item = addMessage('');
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

async function submit() {
  const question = input.value.trim();
  if (busy || !question || question.length > 1000) return;

  setBusy(true);
  beginConversation();
  addMessage(question, 'user');
  input.value = '';
  resizeInput();
  const waiting = addTypingIndicator();
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 35000);

  try {
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: question }),
      signal: controller.signal,
    });
    const data = await response.json();
    waiting.remove();
    if (!response.ok || !data.success) {
      addMessage(data.error || 'Unable to answer. Please try again.', 'error');
    } else {
      addMessage(data.reply, 'assistant', data.sources || [], data.mode);
    }
  } catch (error) {
    waiting.remove();
    addMessage(error.name === 'AbortError'
      ? 'This is taking longer than expected. Please try again.'
      : 'The request could not be completed. Please try again.', 'error');
  } finally {
    clearTimeout(timer);
    setBusy(false);
    input.focus();
  }
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
    status.classList.toggle('status-error', !health.ready);
    status.textContent = health.ready
      ? (health.mode === 'faq'
        ? 'FAQ mode · answers from the department document, not AI generated.'
        : 'AI mode · answers grounded in the department document.')
      : 'Setup incomplete: ' + (!health.verified_records
        ? 'reviewed About CCIT information is required.'
        : 'the AI service must be configured.');
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
    for (const button of topicButtons) {
      button.disabled = !topics.some(topic => topic.id === button.dataset.topic);
    }
  } catch {
    // Typing a question still works when optional suggestions cannot be loaded.
    for (const button of topicButtons) button.title = 'Suggested questions are temporarily unavailable.';
  }
}

updateGreeting();
resizeInput();
loadHealth();
loadTopics();
