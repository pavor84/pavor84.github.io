(function() {
  if (location.href.includes('immune.mos.ru')) {
    const svg = document.querySelector('svg#qrCode');
    if (svg) {
      let svgContent = svg.outerHTML;
      const svgPrefix = '<svg';
      if (!svgContent.startsWith(svgPrefix)) {
        return;
      }
      const svgXmlns = 'xmlns="http://www.w3.org/2000/svg"';
      if (!svgContent.includes(svgXmlns)) {
        svgContent = svgPrefix + ' ' + svgXmlns + svgContent.substr(svgPrefix.length);
      }
      return 'data:image/svg+xml;base64,' + window.btoa(svgContent);
    }
  } else if (location.href.includes('gosuslugi.ru')) {
    const img = document.querySelector('img.vaccine-qr-img');
    if (!img) return;
    return img.src;
  }
})();
