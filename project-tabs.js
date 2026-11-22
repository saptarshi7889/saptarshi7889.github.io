(() => {
  const tabs = document.querySelectorAll('[data-project]');

  function selectProject(project) {
    tabs.forEach((tab) => {
      const selected = tab.dataset.project === project;
      document.getElementById(tab.dataset.project).hidden = !selected;
      if (selected) {
        tab.setAttribute('aria-current', 'page');
      } else {
        tab.removeAttribute('aria-current');
      }
    });
  }

  tabs.forEach((tab) => {
    tab.addEventListener('click', (event) => {
      event.preventDefault();
      selectProject(tab.dataset.project);
    });
  });

  function selectFromHash() {
    const project = window.location.hash.slice(1);
    if (Array.from(tabs).some((tab) => tab.dataset.project === project)) {
      selectProject(project);
    }
  }

  selectFromHash();
  window.addEventListener('hashchange', selectFromHash);
})();
