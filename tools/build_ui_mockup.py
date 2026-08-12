#!/usr/bin/env python3
"""Generate a standalone gallery of every SITTS UI primitive.

The gallery embeds the `<style>` block from `templates/ui/_styles.html` verbatim,
so what you see is what the app ships — the mockup cannot drift from the CSS.
Regenerate after editing tokens or component styles.

    python tools/build_ui_mockup.py
    open .claude/skills/sitts-ui/references/mockup.html
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STYLES = ROOT / "templates" / "ui" / "_styles.html"
OUT = ROOT / ".claude" / "skills" / "sitts-ui" / "references" / "mockup.html"

SECTIONS: list[tuple[str, str]] = [
    (
        "Buttons",
        """
        <div class="mk-row">
          <button class="ui-btn ui-btn--primary">Salvar</button>
          <button class="ui-btn ui-btn--secondary">Cancelar</button>
          <button class="ui-btn ui-btn--subtle">Filtros</button>
          <button class="ui-btn ui-btn--ghost">Limpar</button>
          <button class="ui-btn ui-btn--danger">Excluir</button>
          <button class="ui-btn ui-btn--primary" disabled>Indisponível</button>
        </div>
        <p class="mk-note">Sizes — <code>--sm</code> 36px for dense areas,
        default 44px, <code>--lg</code> 56px + <code>rounded-xl</code> for hero CTAs.</p>
        <div class="mk-row">
          <button class="ui-btn ui-btn--primary ui-btn--sm">Buscar</button>
          <button class="ui-btn ui-btn--primary">Buscar</button>
          <button class="ui-btn ui-btn--primary ui-btn--lg">Buscar</button>
        </div>
        """,
    ),
    (
        "Status pills — signal, not chrome",
        """
        <div class="mk-row">
          <span class="ui-status ui-status--success">Paga</span>
          <span class="ui-status ui-status--error">Não paga</span>
          <span class="ui-status ui-status--warning">Em análise</span>
          <span class="ui-status ui-status--info">Conciliada</span>
          <span class="ui-status ui-status--neutral">Rascunho</span>
          <span class="ui-status ui-status--dark">Finalizada</span>
        </div>
        <p class="mk-note">The only place semantic colour is required. Buttons and
        cards stay ink/canvas — see DESIGN.md &sect;"App surface".</p>
        """,
    ),
    (
        "Typography",
        """
        <p class="ui-display-xxl">Display xxl 52/64</p>
        <p class="ui-display-xl">Display xl 36/44</p>
        <p class="ui-display-lg">Display lg 32/40</p>
        <p class="ui-display-md">Display md 24/32</p>
        <p class="ui-display-sm">Display sm 20/28</p>
        <p class="ui-body-lg">Body lg 18/24 &mdash; lead paragraph.</p>
        <p class="ui-body-md">Body md 16/24 &mdash; default paragraph body.</p>
        <p class="ui-body-md-strong">Body md strong 16/20 &mdash; button labels, bold inline.</p>
        <p class="ui-body-sm">Body sm 14/20 &mdash; captions, table cells.</p>
        <p class="ui-body-sm-strong">Body sm strong 14/16 &mdash; chip labels.</p>
        <p class="ui-caption">Caption 12/20 &mdash; fine print.</p>
        """,
    ),
    (
        "Cards",
        """
        <div class="mk-grid">
          <div class="ui-card"><p class="ui-body-md-strong">ui-card</p><p class="ui-body-sm">Canvas, 16px radius, 24px padding.</p></div>
          <div class="ui-card ui-card--soft"><p class="ui-body-md-strong">--soft</p><p class="ui-body-sm">Tinted sub-region.</p></div>
          <div class="ui-card ui-card--softer"><p class="ui-body-md-strong">--softer</p><p class="ui-body-sm">Nested on white.</p></div>
          <div class="ui-card ui-card--dark"><p class="ui-body-md-strong" style="color:var(--color-on-dark)">--dark</p><p class="ui-body-sm" style="color:var(--color-on-dark)">Polarity flip.</p></div>
          <div class="ui-card ui-card--elevated"><p class="ui-body-md-strong">--elevated</p><p class="ui-body-sm">Level 1 shadow.</p></div>
        </div>
        """,
    ),
    (
        "Form controls",
        """
        <div class="ui-form mk-grid">
          <div class="ui-field">
            <label class="ui-field__label" for="mk-a">Número do contrato</label>
            <input class="ui-input" id="mk-a" type="text" placeholder="0001/2026">
            <span class="ui-field__hint">Formato 0000/AAAA.</span>
          </div>
          <div class="ui-field">
            <label class="ui-field__label" for="mk-b">Situação</label>
            <select class="ui-input" id="mk-b"><option>Em execução</option><option>Encerrado</option></select>
          </div>
          <div class="ui-field">
            <label class="ui-field__label" for="mk-c">Valor repassado</label>
            <input class="ui-input" id="mk-c" type="text" value="R$ 120.000,00" aria-invalid="true">
            <span class="ui-field__error">Informe um valor maior que zero.</span>
          </div>
        </div>
        <p class="mk-note">Form labels are <code>.ui-field__label</code> &mdash; 14px,
        weight 500, sentence case, ink. Dense app forms want
        <code>.ui-form--compact</code> for a 36&ndash;40px control height.
        The 11px uppercase style belongs to <code>.filter-field__label</code>,
        table headers, and <code>.ui-dl dt</code> &mdash; not to form fields.</p>
        """,
    ),
    (
        "Table",
        """
        <div class="ui-table-wrap">
          <table class="ui-table">
            <thead><tr><th>Favorecido</th><th>Natureza</th><th>Valor</th><th>Situação</th></tr></thead>
            <tbody>
              <tr><td>ZZZ Contabilidade ME</td><td>Serviços de terceiros</td><td>R$ 4.820,00</td><td><span class="ui-status ui-status--success">Paga</span></td></tr>
              <tr><td>Papelaria Central</td><td>Material de consumo</td><td>R$ 318,90</td><td><span class="ui-status ui-status--warning">Em análise</span></td></tr>
              <tr><td>Instituto Formar</td><td>Recursos humanos</td><td>R$ 22.140,00</td><td><span class="ui-status ui-status--info">Conciliada</span></td></tr>
            </tbody>
          </table>
        </div>
        <p class="mk-note">Wrap wide tables in <code>.ui-table-wrap</code> or
        <code>.ui-table-scroll</code>. Overflow belongs to the table, never to
        <code>&lt;body&gt;</code>.</p>
        """,
    ),
    (
        "Alerts",
        """
        <div class="ui-stack ui-stack--sm">
          <div class="ui-alert ui-alert--info"><span class="ui-alert__indicator"></span><div>Sua sessão expira em 5 minutos.</div></div>
          <div class="ui-alert ui-alert--success"><span class="ui-alert__indicator"></span><div>Prestação de contas enviada para análise.</div></div>
          <div class="ui-alert ui-alert--warning"><span class="ui-alert__indicator"></span><div>3 despesas sem documento anexado.</div></div>
          <div class="ui-alert ui-alert--error"><span class="ui-alert__indicator"></span><div>Não foi possível conciliar o extrato. Verifique o arquivo OFX.</div></div>
        </div>
        """,
    ),
    (
        "Badges, chips, empty state",
        """
        <div class="mk-row">
          <span class="ui-badge">Rascunho</span>
          <span class="ui-badge ui-badge--dark">Novo</span>
          <span class="ui-badge ui-badge--outline">2026</span>
          <span class="ui-chip">Todos</span>
          <span class="ui-chip ui-chip--warning">Pendente</span>
          <span class="ui-chip ui-chip--danger">Glosado</span>
        </div>
        <div class="ui-empty" style="margin-top:16px">
          <p class="ui-body-md-strong">Nenhuma despesa neste período</p>
          <p class="ui-body-sm">Importe um extrato ou lance manualmente.</p>
          <button class="ui-btn ui-btn--primary ui-btn--sm" style="margin-top:12px">Adicionar despesa</button>
        </div>
        <p class="mk-note">Empty state is one strong line plus one action.</p>
        """,
    ),
    (
        "Filter row",
        """
        <div class="ui-card ui-card--soft">
          <div class="filter-row">
            <div class="filter-field"><label class="filter-field__label" for="mk-f1">Exercício</label><select class="ui-input" id="mk-f1"><option>2026</option></select></div>
            <div class="filter-field"><label class="filter-field__label" for="mk-f2">Mês</label><select class="ui-input" id="mk-f2"><option>Agosto</option></select></div>
            <div class="filter-field"><label class="filter-field__label" for="mk-f3">Situação</label><select class="ui-input" id="mk-f3"><option>Todas</option></select></div>
            <div class="filter-row__actions">
              <button class="ui-btn ui-btn--ghost ui-btn--sm">Limpar</button>
              <button class="ui-btn ui-btn--primary ui-btn--sm">Aplicar</button>
            </div>
          </div>
        </div>
        <p class="mk-note">This is where the 11px uppercase label lives
        (<code>.filter-field__label</code>).</p>
        """,
    ),
    (
        "Tokens",
        """
        <p class="mk-note">Live values from <code>:root</code>. Radius and spacing
        swatches are rendered at their real size.</p>
        <div class="mk-row" id="mk-swatches"></div>
        """,
    ),
]

SWATCH_JS = """
<script>
(function () {
  var root = getComputedStyle(document.documentElement);
  var host = document.getElementById('mk-swatches');
  if (!host) return;
  var names = Array.prototype.slice
    .call(document.styleSheets)
    .reduce(function (acc, sheet) {
      var rules;
      try { rules = sheet.cssRules; } catch (e) { return acc; }
      Array.prototype.forEach.call(rules || [], function (rule) {
        if (!rule.style || rule.selectorText !== ':root') return;
        Array.prototype.forEach.call(rule.style, function (prop) {
          if (prop.indexOf('--color-') === 0) acc.push(prop);
        });
      });
      return acc;
    }, []);
  names.forEach(function (name) {
    var value = root.getPropertyValue(name).trim();
    var cell = document.createElement('div');
    cell.className = 'mk-swatch';
    cell.innerHTML =
      '<span class="mk-chip" style="background:' + value + '"></span>' +
      '<code>' + name + '</code><small>' + value + '</small>';
    host.appendChild(cell);
  });
})();
</script>
"""

MOCKUP_CSS = """
  body { background: var(--color-canvas-softer); padding: 32px; }
  .mk-wrap { max-width: 1100px; margin: 0 auto; }
  .mk-head { margin-bottom: 32px; }
  .mk-section { background: var(--color-canvas); border-radius: var(--rounded-xl);
                padding: var(--space-2xl); margin-bottom: var(--space-2xl); }
  .mk-section > h2 { font-family: var(--font-display); font-weight: 700;
                     font-size: 20px; line-height: 28px; margin: 0 0 16px; }
  .mk-row { display: flex; flex-wrap: wrap; gap: 12px; align-items: center; }
  .mk-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
             gap: 16px; }
  .mk-note { font-family: var(--font-text); font-size: 13px; line-height: 20px;
             color: var(--color-body); margin: 12px 0 0; }
  .mk-note code { font-family: var(--font-mono); font-size: 12px; }
  .mk-swatch { display: flex; flex-direction: column; gap: 4px; width: 150px; }
  .mk-swatch .mk-chip { display: block; height: 40px; border-radius: var(--rounded-md);
                        border: 1px solid var(--color-canvas-soft); }
  .mk-swatch code { font-family: var(--font-mono); font-size: 11px; color: var(--color-ink); }
  .mk-swatch small { font-family: var(--font-mono); font-size: 11px; color: var(--color-mute); }
"""


def extract_style_block(styles_html: str) -> str:
    match = re.search(r"<style>(.*?)</style>", styles_html, re.DOTALL)
    if not match:
        raise SystemExit(
            f"No <style> block found in {STYLES.relative_to(ROOT)}. "
            "Did the file's structure change?"
        )
    return match.group(1)


def build() -> str:
    css = extract_style_block(STYLES.read_text(encoding="utf-8"))
    body = "\n".join(
        f'    <section class="mk-section">\n      <h2>{title}</h2>{markup}\n    </section>'
        for title, markup in SECTIONS
    )
    return f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>SITTS UI primitives</title>
<!-- GENERATED by tools/build_ui_mockup.py — do not edit by hand.
     The CSS below is copied verbatim from templates/ui/_styles.html. -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>{css}</style>
<style>{MOCKUP_CSS}</style>
</head>
<body>
  <div class="mk-wrap">
    <header class="mk-head">
      <p class="ui-display-lg">SITTS UI primitives</p>
      <p class="ui-body-md">Every shipped component, rendered with the real CSS.
      Generated from <code>templates/ui/_styles.html</code> by
      <code>tools/build_ui_mockup.py</code>. The app is light-only &mdash; there
      is no dark theme.</p>
    </header>
{body}
  </div>
{SWATCH_JS}
</body>
</html>
"""


def main() -> int:
    if not STYLES.exists():
        raise SystemExit(f"Missing {STYLES.relative_to(ROOT)}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(build(), encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
