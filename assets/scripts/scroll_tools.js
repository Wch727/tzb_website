(function () {
  const parentWindow = window.parent;
  const anchorId = $anchor_id_json;

  const resetScroll = () => {
    try {
      parentWindow.scrollTo({ top: 0, left: 0, behavior: "auto" });
      parentWindow.document.documentElement.scrollTop = 0;
      parentWindow.document.body.scrollTop = 0;

      const anchor = parentWindow.document.getElementById(anchorId);
      if (anchor) {
        anchor.scrollIntoView({ block: "start", inline: "nearest", behavior: "auto" });
      }

      const selectors = [
        "[data-testid='stAppViewContainer']",
        "[data-testid='stMain']",
        "[data-testid='stMainBlockContainer']",
        "section.main",
        "div[data-testid='stAppViewBlockContainer']",
        "main",
        ".main"
      ];

      selectors.forEach((selector) => {
        const target = parentWindow.document.querySelector(selector);
        if (target) {
          target.scrollTo({ top: 0, left: 0, behavior: "auto" });
          target.scrollTop = 0;
        }
      });
    } catch (error) {
      try {
        parentWindow.scrollTo(0, 0);
      } catch (_) {}
    }
  };

  resetScroll();
  requestAnimationFrame(resetScroll);
  [60, 180, 360, 720].forEach((delay) => setTimeout(resetScroll, delay));

  let attempts = 0;
  const timer = setInterval(() => {
    resetScroll();
    attempts += 1;
    if (attempts >= 12) {
      clearInterval(timer);
    }
  }, 160);
})();
