(function() {
  if (!location.href.includes('from_alice')) {
    return;
  }

  let selector;
  if (location.href.includes('immune.mos.ru')) {
    selector = '.nlk-button[type="submit"]';
  } else if (location.href.includes('gosuslugi.ru')) {
    selector = '[href="https://www.gosuslugi.ru/10600/1"],[href="https://www.gosuslugi.ru/10601/1"]';
  } else {
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
          if (node.matches(selector)) {
            node.click();
            observer.disconnect();
            return;
          } else {
            button = node.querySelector(selector);
            if (button) {
              button.click();
              observer.disconnect();
              return;
            }
          }
        }
      }
    };

    const observer = new MutationObserver(callback);
    observer.observe(document.body, {
        childList: true,
        subtree: true,
    });
  }

  if (document.readyState === 'complete') {
    if (!selectAndMaybeClickButton(selector)) {
      addObserver();
    }
  } else {
    document.addEventListener('load', () => {
      if (!selectAndMaybeClickButton(selector)) {
        addObserver();
      }
    });
  }
})();
