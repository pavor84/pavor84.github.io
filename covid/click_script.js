(function() {
  if (!location.href.includes('from_alice')) {
    return;
  }

  let selector;
  if (location.href.includes('immune.mos.ru')) {
    selector = '.nlk-button[type="submit"]';
  } else if (location.href.includes('gosuslugi.ru')) {
    selector = 'div.cert-block > div:nth-of-type(2) > a';
  } else {
    console.log('selector not found');
    return;
  }

  const selectAndMaybeClickButton = (selector) => {
    const button = document.querySelector(selector);
    if (button) {
      button.click();
      return true;
    }
    return false;
  };

  const addObserver = () => {
    const callback = function(mutationsList, observer) {
      for (const mutation of mutationsList) {
        if (mutation.type !== 'childList') {
          return;
        }
        for (node of mutation.addedNodes) {
          if (node.nodeType !== Node.ELEMENT_NODE) {
            continue;
          }
          if (node.matches(selector) || node.querySelector(selector)) {
            setTimeout(() => selectAndMaybeClickButton(selector), 1000);
            observer.disconnect();
            return;
          }
        }
      }
    };

    const observer = new MutationObserver(callback);
    observer.observe(document.body, {
        childList: true,
        subtree: true,
    });
  };

  if (document.readyState === 'complete' || document.readyState === 'interactive') {
    if (!selectAndMaybeClickButton(selector)) {
      addObserver();
    }
  } else {
    window.addEventListener('load', () => {
      if (!selectAndMaybeClickButton(selector)) {
        addObserver();
      }
    });
  }
})();
