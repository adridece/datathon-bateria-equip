// L'informe es mostra en una pàgina pròpia (report.html) per veure'l abans de desar-lo en PDF.
// l'informe surt del mateix mode que es veu al dashboard
window.Report = { open() { window.open("report.html" + location.hash, "_blank"); } };
