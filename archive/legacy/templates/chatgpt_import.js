document.querySelector('#copy-chatgpt-prompt')?.addEventListener('click', async () => {
  const prompt = document.querySelector('#chatgpt-prompt');
  const status = document.querySelector('#chatgpt-copy-status');
  try {
    await navigator.clipboard.writeText(prompt.value);
    status.textContent = 'Prompt copied. Attach your test and mark scheme in ChatGPT.';
  } catch (_) {
    prompt.focus(); prompt.select();
    status.textContent = 'Prompt selected. Press Ctrl+C (Command+C on Mac) to copy it.';
  }
});
