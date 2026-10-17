const { chromium } = require('playwright');
(async () => {
  const [html, png, pdf] = process.argv.slice(2);
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1587, height: 1123 }, deviceScaleFactor: 2 });
  await p.goto('file://' + html, { waitUntil: 'networkidle' });
  await p.evaluate(() => document.fonts.ready);
  await p.screenshot({ path: png, fullPage: false });
  await p.pdf({ path: pdf, width: '420mm', height: '297mm', printBackground: true, margin: {top:0,right:0,bottom:0,left:0}, preferCSSPageSize: true });
  await b.close();
  console.log('ok');
})();
