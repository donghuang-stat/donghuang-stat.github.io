(() => {
  const picker = document.querySelector('[data-theme-picker]');
  if (picker) {
    try { picker.value = localStorage.getItem('dong-page-theme') || 'system'; } catch (_) {}
    function applyTheme() {
      if (picker.value === 'system') document.documentElement.removeAttribute('data-theme');
      else document.documentElement.dataset.theme = picker.value;
      try { localStorage.setItem('dong-page-theme', picker.value); } catch (_) {}
    }
    picker.addEventListener('change', applyTheme);
    applyTheme();
  }
})();
