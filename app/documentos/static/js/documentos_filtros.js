(function () {
  const go = (params) => {
    const url = new URL(window.__LIST_URL__, window.location.origin);
    Object.entries(params).forEach(([k, v]) => {
      if (v) url.searchParams.set(k, v); else url.searchParams.delete(k);
    });
    window.location.href = url.toString();
  };

  const f_ini = document.getElementById("f_ini");
  const f_fin = document.getElementById("f_fin");
  const term = document.getElementById("term");
  const btnF = document.getElementById("btnFiltrar");
  const btnL = document.getElementById("btnLimpiar");

  if (btnF) btnF.addEventListener("click", (e) => {
    e.preventDefault();
    go({
      fecha_inicio: f_ini && f_ini.value || "",
      fecha_fin: f_fin && f_fin.value || "",
      q: term && term.value || ""
    });
  });

  if (btnL) btnL.addEventListener("click", (e) => {
    e.preventDefault();
    go({});
  });

  // Búsqueda al vuelo (enter)
  if (term) term.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      btnF && btnF.click();
    }
  });
})();
