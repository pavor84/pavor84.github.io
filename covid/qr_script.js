(function() {
  if (location.href.includes('immune.mos.ru')) {
    const svg = document.querySelector('svg#qrCode');
    if (svg) {
      svg.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
      return 'data:image/svg+xml;base64,' + window.btoa(svg.outerHTML);
    }
  } else if (location.href.includes('gosuslugi.ru')) {
    let img = document.querySelector('img.vaccine-qr-img');
    if (!img) {
      img = document.querySelector('img[alt="QR-code"]');
    }

    if (img) {
      return img.src;
    }
  }
})();
