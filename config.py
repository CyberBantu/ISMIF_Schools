import matplotlib.colors as mcolors

CORES_RISCO = {
    "Muito Baixo": "#1a7a1a",
    "Baixo":       "#8cc63f",
    "Médio":       "#ffe066",
    "Alto":        "#ff8c00",
    "Muito Alto":  "#cc1100",
}
ORDEM_RISCO = ["Muito Baixo", "Baixo", "Médio", "Alto", "Muito Alto"]

CMAP_ISMIF = mcolors.LinearSegmentedColormap.from_list(
    "ismif", ["#1a7a1a", "#8cc63f", "#ffe066", "#ff8c00", "#cc1100"]
)

CREDITO_HTML = """
<div class="credit-card">
  <div class="label">Elaborado por</div>
  <div class="name">Christian Basilio</div>
  <div style="margin-top:6px;">
    <span style="font-size:0.75rem">🔗 </span>
    <a href="https://www.linkedin.com/in/christianbasilioo/" target="_blank">
      linkedin.com/in/christianbasilioo
    </a>
  </div>
</div>
"""
# Configuração de CSS
APP_CSS = """
<style>
  .block-container { padding-top: 5rem; }

  .stTabs [data-baseweb="tab-list"] {
    gap: 2px;
    border-bottom: 2px solid #e0e0e0;
  }
  .stTabs [data-baseweb="tab"] {
    padding: 10px 24px;
    font-size: 0.95rem;
    font-weight: 600;
  }
  .stTabs [data-baseweb="tab-highlight"] {
    background-color: #ff8c00 !important;
    height: 3px !important;
  }

  .credit-card {
    background: linear-gradient(135deg, #1a2940 0%, #24415e 100%);
    border-radius: 10px;
    padding: 14px 16px;
    margin-top: 8px;
    color: white;
    font-size: 0.80rem;
    line-height: 1.6;
    box-shadow: 0 2px 8px rgba(0,0,0,0.25);
  }
  .credit-card .name  { font-size:0.95rem; font-weight:700; letter-spacing:0.02em; color:#f0c060; }
  .credit-card a      { color:#8ec8f8; text-decoration:none; font-size:0.78rem; }
  .credit-card .label { font-size:0.68rem; color:#aaccee; text-transform:uppercase;
                        letter-spacing:0.07em; margin-bottom:2px; }

  div[data-testid="metric-container"] { text-align: center; }
</style>
"""
# Configuração de legendas 
LEGEND_HTML = """
<div style='position:fixed;bottom:30px;right:10px;z-index:9999;
            background:rgba(255,255,255,0.96);border-radius:10px;
            padding:12px 14px;font-size:11.5px;
            box-shadow:0 2px 8px rgba(0,0,0,0.18);
            border:1px solid #ddd;min-width:185px;font-family:Arial,sans-serif;'>
  <div style='font-size:12px;font-weight:700;color:#222;
              border-bottom:2px solid #eee;padding-bottom:6px;margin-bottom:8px;'>
    Suscetibilidade ISMIF
  </div>
  <div style='font-size:9px;color:#aaa;font-weight:600;
              text-transform:uppercase;letter-spacing:0.05em;margin-bottom:5px;'>Escolas</div>
  <div style='display:flex;flex-direction:column;gap:4px;margin-bottom:10px'>
    <div style='display:flex;align-items:center;gap:7px'>
      <span style='width:11px;height:11px;border-radius:50%;background:#cc1100;border:1px solid #bbb;flex-shrink:0;display:inline-block'></span>
      <span><b>Muito Alto</b> <span style='color:#999;font-size:10px'>&gt; 0,80</span></span>
    </div>
    <div style='display:flex;align-items:center;gap:7px'>
      <span style='width:11px;height:11px;border-radius:50%;background:#ff8c00;border:1px solid #bbb;flex-shrink:0;display:inline-block'></span>
      <span><b>Alto</b> <span style='color:#999;font-size:10px'>0,61–0,80</span></span>
    </div>
    <div style='display:flex;align-items:center;gap:7px'>
      <span style='width:11px;height:11px;border-radius:50%;background:#ffe066;border:1px solid #bbb;flex-shrink:0;display:inline-block'></span>
      <span><b>Médio</b> <span style='color:#999;font-size:10px'>0,41–0,60</span></span>
    </div>
    <div style='display:flex;align-items:center;gap:7px'>
      <span style='width:11px;height:11px;border-radius:50%;background:#8cc63f;border:1px solid #bbb;flex-shrink:0;display:inline-block'></span>
      <span><b>Baixo</b> <span style='color:#999;font-size:10px'>0,21–0,40</span></span>
    </div>
    <div style='display:flex;align-items:center;gap:7px'>
      <span style='width:11px;height:11px;border-radius:50%;background:#1a7a1a;border:1px solid #bbb;flex-shrink:0;display:inline-block'></span>
      <span><b>Muito Baixo</b> <span style='color:#999;font-size:10px'>&le; 0,20</span></span>
    </div>
  </div>
  <div style='border-top:1px dashed #e0e0e0;margin-bottom:7px'></div>
  <div style='font-size:9px;color:#aaa;font-weight:600;
              text-transform:uppercase;letter-spacing:0.05em;margin-bottom:5px;'>Raster ISMIF</div>
  <div style='width:100%;height:11px;
              background:linear-gradient(to right,#1a7a1a,#8cc63f,#ffe066,#ff8c00,#cc1100);
              border-radius:3px;border:1px solid #ccc'></div>
  <div style='display:flex;justify-content:space-between;font-size:9px;color:#888;margin-top:2px'>
    <span>0,0</span><span>0,5</span><span>1,0</span>
  </div>
</div>
"""

# Zoom
ZOOM_JS = """
<script>
(function() {
  function applyRadius(map) {
    var zoom = map.getZoom();
    var r = Math.max(2, Math.min(7, zoom - 7));
    map.eachLayer(function(layer) {
      if (layer instanceof L.CircleMarker) { layer.setRadius(r); }
    });
  }
  document.addEventListener('DOMContentLoaded', function() {
    setTimeout(function() {
      var keys = Object.keys(window).filter(function(k) { return k.startsWith('map_'); });
      if (!keys.length) return;
      var map = window[keys[keys.length - 1]];
      map.on('zoomend', function() { applyRadius(map); });
      applyRadius(map);
    }, 800);
  });
})();
</script>
"""
