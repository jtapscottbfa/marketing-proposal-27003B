#!/usr/bin/env node
// ══════════════════════════════════════════════════════════════════════════════
// scripts/publish/post_process_tables.js
//
// Fixes ONE thing Pandoc cannot do via reference.docx:
//   → Locks every table to full content width and distributes column widths
//     evenly, preventing the column collapse that occurs on Markdown import.
//
// All appearance (colours, fonts, borders, shading) is owned by the Word
// template at templates/docx_reference/reference.docx — do not add style
// overrides here.
//
// USAGE (called automatically by build_docx.sh):
//   node scripts/publish/post_process_tables.js input.docx output.docx
// ══════════════════════════════════════════════════════════════════════════════

const fs   = require('fs');
const path = require('path');
const AdmZip = require('adm-zip');
const { DOMParser, XMLSerializer } = require('@xmldom/xmldom');

// ── Args ──────────────────────────────────────────────────────────────────────
const [,, INPUT, OUTPUT] = process.argv;

if (!INPUT || !OUTPUT) {
  console.error('Usage: node post_process_tables.js input.docx output.docx');
  process.exit(1);
}
if (!fs.existsSync(INPUT)) {
  console.error(`✖ Input not found: ${INPUT}`);
  process.exit(1);
}

// Page content width in DXA: 8.5" - 0.70"(R) - 0.75"(L) = 7.05" × 1440
const CONTENT_WIDTH = Math.round(7.05 * 1440); // 10152 DXA

const W_NS = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main';

function setAttr(el, attr, val) {
  el.setAttributeNS(W_NS, `w:${attr}`, val);
}

function removeChildren(parent, tagName) {
  Array.from(parent.childNodes)
    .filter(n => n.localName === tagName)
    .forEach(n => parent.removeChild(n));
}

function getOrCreate(parent, tag, doc) {
  const existing = Array.from(parent.childNodes).find(n => n.localName === tag);
  if (existing) return existing;
  const el = doc.createElementNS(W_NS, `w:${tag}`);
  parent.insertBefore(el, parent.firstChild);
  return el;
}

function wElem(doc, tag, attrs = {}) {
  const el = doc.createElementNS(W_NS, `w:${tag}`);
  for (const [k, v] of Object.entries(attrs)) el.setAttributeNS(W_NS, `w:${k}`, v);
  return el;
}

// ── Width fix ─────────────────────────────────────────────────────────────────
function fixWidths(xmlString) {
  const doc = new DOMParser().parseFromString(xmlString, 'text/xml');
  const tables = Array.from(doc.getElementsByTagNameNS(W_NS, 'tbl'));

  tables.forEach(tbl => {
    // 1. Lock table width
    const tblPr = getOrCreate(tbl, 'tblPr', doc);
    removeChildren(tblPr, 'tblW');
    tblPr.appendChild(wElem(doc, 'tblW', { w: String(CONTENT_WIDTH), type: 'dxa' }));

    // 2. Redistribute column widths evenly across full content width
    const tblGrid = tbl.getElementsByTagNameNS(W_NS, 'tblGrid')[0];
    const gridCols = tblGrid
      ? Array.from(tblGrid.getElementsByTagNameNS(W_NS, 'gridCol'))
      : [];
    const colCount = gridCols.length || 1;
    const colW = Math.floor(CONTENT_WIDTH / colCount);
    const remainder = CONTENT_WIDTH - colW * colCount;

    gridCols.forEach((gc, i) => {
      setAttr(gc, 'w', String(colW + (i === colCount - 1 ? remainder : 0)));
    });

    // 3. Lock each cell width to match its grid column
    Array.from(tbl.getElementsByTagNameNS(W_NS, 'tr')).forEach(tr => {
      Array.from(tr.getElementsByTagNameNS(W_NS, 'tc')).forEach((tc, colIdx) => {
        const tcPr = getOrCreate(tc, 'tcPr', doc);
        removeChildren(tcPr, 'tcW');
        const cellW = colW + (colIdx === colCount - 1 ? remainder : 0);
        tcPr.appendChild(wElem(doc, 'tcW', { w: String(cellW), type: 'dxa' }));
      });
    });
  });

  return { xml: new XMLSerializer().serializeToString(doc), tableCount: tables.length };
}

// ── Main ──────────────────────────────────────────────────────────────────────
try {
  console.log(`  Fixing table widths: ${path.basename(INPUT)}`);

  const zip = new AdmZip(INPUT);
  const docEntry = zip.getEntry('word/document.xml');

  if (!docEntry) {
    console.warn('  ⚠ No document.xml found — skipping');
    fs.copyFileSync(INPUT, OUTPUT);
    process.exit(0);
  }

  const { xml, tableCount } = fixWidths(zip.readAsText(docEntry));
  zip.updateFile('word/document.xml', Buffer.from(xml, 'utf8'));
  zip.writeZip(OUTPUT);

  console.log(tableCount > 0
    ? `  ✔ ${tableCount} table(s) locked to ${CONTENT_WIDTH} DXA (${(CONTENT_WIDTH / 1440).toFixed(2)}")`
    : `  ℹ No tables found`
  );
} catch (err) {
  console.error(`  ✖ Width fix failed: ${err.message}`);
  fs.copyFileSync(INPUT, OUTPUT); // non-fatal fallback
  process.exit(0);
}
