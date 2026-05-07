(function () {
  const parentWindow = window.parent;
  const doc = parentWindow && parentWindow.document;
  if (!doc) {
    return;
  }

  const root = doc.documentElement;
  root.classList.add("tzb-js-ready");

  const markEnhancedCards = () => {
    const selectors = [
      ".platform-level-card",
      ".game-chapter-mission",
      ".game-map-node",
      ".game-option-card",
      ".game-collectible-wall-card",
      ".role-loadout-card",
      ".figure-archive-card",
      ".home-node-card",
      ".hero-banner"
    ];

    doc.querySelectorAll(selectors.join(",")).forEach((element) => {
      element.setAttribute("data-js-enhanced", "true");
    });
  };

  const markActiveButtons = () => {
    doc.querySelectorAll("button[kind='primary']").forEach((button) => {
      button.setAttribute("data-primary-action", "true");
    });
  };

  markEnhancedCards();
  markActiveButtons();
  requestAnimationFrame(() => {
    markEnhancedCards();
    markActiveButtons();
  });
  setTimeout(markEnhancedCards, 250);
  setTimeout(markActiveButtons, 250);
})();
