#!/usr/bin/env node
// ══════════════════════════════════════════════════════════════════════════════
// scripts/publish/generate_reference_docx.js
//
// Generates templates/docx_reference/reference.docx — the Pandoc reference
// document carrying firm brand styles, header (logo + firm name), and footer
// (firm name | RFP number | page number).
//
// Run once, or re-run any time brand styles change:
//   node scripts/publish/generate_reference_docx.js
//   node scripts/publish/generate_reference_docx.js --rfp "RFP-2025-001"
//
// Dependencies: npm install -g docx
// ══════════════════════════════════════════════════════════════════════════════

const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  ImageRun, Header, Footer, AlignmentType, LevelFormat, BorderStyle,
  WidthType, ShadingType, VerticalAlign, PageNumber, NumberFormat,
  TabStopType, TabStopPosition, HeadingLevel, convertInchesToTwip,
  PageBreak
} = require('docx');
const fs = require('fs');
const path = require('path');

// ── Args ──────────────────────────────────────────────────────────────────────
const args = process.argv.slice(2);
const rfpArg = args.indexOf('--rfp');
const RFP_NUMBER = rfpArg !== -1 ? args[rfpArg + 1] : 'RFP NUMBER';

// ── Paths ─────────────────────────────────────────────────────────────────────
const REPO_ROOT = path.resolve(__dirname, '../..');
const LOGO_PATH = path.join(REPO_ROOT, 'assets/logos/firm_logo.png');
const OUT_PATH  = path.join(REPO_ROOT, 'templates/docx_reference/reference.docx');

// ── Brand Tokens ──────────────────────────────────────────────────────────────
const BRAND = {
  primary:      '561A1A',   // Deep burgundy — headings, footer firm name
  primaryDark:  '4D1C1B',   // Slightly darker for footer accent
  subtext:      '404040',   // Dark grey for secondary header text
  rule:         'A6A6A6',   // Footer top rule / light borders
  bodyText:     '000000',
  white:        'FFFFFF',
  tableHeader:  '561A1A',   // Dark fill for table header rows
  tableAlt:     'F5EDED',   // Light burgundy tint for alternating rows
  tableBorder:  'C8A0A0',   // Muted burgundy for table borders
  fontHeading:  'Source Sans Pro',
  fontBody:     'Calibri',
  fontUI:       'Segoe UI',
};

// Page: US Letter, margins matching brand template
// T=0.30" R=0.70" B=1.00" L=0.75"
const PAGE = {
  width:  12240,  // 8.5" in DXA
  height: 15840,  // 11" in DXA
  top:    convertInchesToTwip(0.30),
  right:  convertInchesToTwip(0.70),
  bottom: convertInchesToTwip(1.00),
  left:   convertInchesToTwip(0.75),
  // Content width = 8.5 - 0.70 - 0.75 = 7.05" = 10152 DXA
  contentWidth: Math.round((8.5 - 0.70 - 0.75) * 1440),
};

// ── Logo ──────────────────────────────────────────────────────────────────────
let logoData = null;
if (fs.existsSync(LOGO_PATH)) {
  logoData = fs.readFileSync(LOGO_PATH);
} else {
  console.warn(`⚠ Logo not found at ${LOGO_PATH} — header will omit logo`);
}

// ── Header — Small variant (interior pages) ───────────────────────────────────
// Logo left (~0.57" wide) | Firm name + address right (right-aligned)
// Thin bottom border rule in primary colour
function makeHeader() {
  const logoCell = new TableCell({
    width: { size: 4500, type: WidthType.DXA },
    borders: {
      top:    { style: BorderStyle.NONE, size: 0 },
      left:   { style: BorderStyle.NONE, size: 0 },
      right:  { style: BorderStyle.NONE, size: 0 },
      bottom: { style: BorderStyle.SINGLE, size: 4, color: BRAND.rule },
    },
    verticalAlign: VerticalAlign.BOTTOM,
    children: [
      new Paragraph({
        children: logoData ? [
          new ImageRun({
            data: logoData,
            transformation: { width: 57, height: 38 },  // ~0.57" × 0.38" at 100dpi
            type: 'png',
          }),
        ] : [new TextRun({ text: 'YOUR FIRM NAME', bold: true, font: BRAND.fontHeading, size: 18, color: BRAND.primary })],
      }),
    ],
  });

  const firmCell = new TableCell({
    width: { size: PAGE.contentWidth - 4500, type: WidthType.DXA },
    borders: {
      top:    { style: BorderStyle.NONE, size: 0 },
      left:   { style: BorderStyle.NONE, size: 0 },
      right:  { style: BorderStyle.NONE, size: 0 },
      bottom: { style: BorderStyle.SINGLE, size: 4, color: BRAND.rule },
    },
    verticalAlign: VerticalAlign.BOTTOM,
    margins: { top: 0, bottom: 40, left: 120, right: 0 },
    children: [
      new Paragraph({
        alignment: AlignmentType.RIGHT,
        spacing: { before: 0, after: 0, line: 200, lineRule: 'exact' },
        children: [
          new TextRun({ text: 'CONSULTING ENGINEERS', bold: true, font: BRAND.fontHeading, size: 18, color: BRAND.bodyText }),
        ],
      }),
      new Paragraph({
        alignment: AlignmentType.RIGHT,
        spacing: { before: 0, after: 0, line: 200, lineRule: 'exact' },
        children: [
          new TextRun({ text: 'PLACEHOLDER: Street, City, State, ZIP', font: BRAND.fontHeading, size: 16, color: BRAND.subtext }),
        ],
      }),
    ],
  });

  const headerTable = new Table({
    width: { size: PAGE.contentWidth, type: WidthType.DXA },
    columnWidths: [4500, PAGE.contentWidth - 4500],
    borders: {
      top:      { style: BorderStyle.NONE, size: 0 },
      left:     { style: BorderStyle.NONE, size: 0 },
      right:    { style: BorderStyle.NONE, size: 0 },
      bottom:   { style: BorderStyle.NONE, size: 0 },
      insideH:  { style: BorderStyle.NONE, size: 0 },
      insideV:  { style: BorderStyle.NONE, size: 0 },
    },
    rows: [
      new TableRow({
        height: { value: 600, rule: 'atLeast' },
        children: [logoCell, firmCell],
      }),
    ],
  });

  return new Header({ children: [headerTable] });
}

// ── Footer — Firm name | RFP number (centre) | Page X of Y (right) ────────────
function makeFooter() {
  const leftCell = new TableCell({
    width: { size: Math.round(PAGE.contentWidth * 0.45), type: WidthType.DXA },
    borders: {
      top:    { style: BorderStyle.SINGLE, size: 4, color: BRAND.rule },
      left:   { style: BorderStyle.NONE, size: 0 },
      right:  { style: BorderStyle.NONE, size: 0 },
      bottom: { style: BorderStyle.NONE, size: 0 },
    },
    verticalAlign: VerticalAlign.CENTER,
    margins: { top: 60, bottom: 0, left: 0, right: 80 },
    children: [
      new Paragraph({
        spacing: { before: 0, after: 0 },
        children: [
          new TextRun({ text: 'YOUR FIRM ', bold: true, font: BRAND.fontHeading, size: 16, color: BRAND.primaryDark }),
          new TextRun({ text: '\u25C6 ', font: BRAND.fontHeading, size: 16, color: BRAND.rule }),  // ◆
          // Customize: replace with your firm's website
          new TextRun({ text: 'WWW.EXAMPLE.COM', font: BRAND.fontHeading, size: 16, color: BRAND.subtext }),
        ],
      }),
    ],
  });

  const centreWidth = Math.round(PAGE.contentWidth * 0.30);
  const centreCell = new TableCell({
    width: { size: centreWidth, type: WidthType.DXA },
    borders: {
      top:    { style: BorderStyle.SINGLE, size: 4, color: BRAND.rule },
      left:   { style: BorderStyle.NONE, size: 0 },
      right:  { style: BorderStyle.NONE, size: 0 },
      bottom: { style: BorderStyle.NONE, size: 0 },
    },
    verticalAlign: VerticalAlign.CENTER,
    margins: { top: 60, bottom: 0, left: 80, right: 80 },
    children: [
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { before: 0, after: 0 },
        children: [
          new TextRun({ text: RFP_NUMBER, font: BRAND.fontHeading, size: 16, color: BRAND.subtext, italics: true }),
        ],
      }),
    ],
  });

  const rightWidth = PAGE.contentWidth - Math.round(PAGE.contentWidth * 0.45) - centreWidth;
  const rightCell = new TableCell({
    width: { size: rightWidth, type: WidthType.DXA },
    borders: {
      top:    { style: BorderStyle.SINGLE, size: 4, color: BRAND.rule },
      left:   { style: BorderStyle.NONE, size: 0 },
      right:  { style: BorderStyle.NONE, size: 0 },
      bottom: { style: BorderStyle.NONE, size: 0 },
    },
    verticalAlign: VerticalAlign.CENTER,
    margins: { top: 60, bottom: 0, left: 80, right: 0 },
    children: [
      new Paragraph({
        alignment: AlignmentType.RIGHT,
        spacing: { before: 0, after: 0 },
        children: [
          new TextRun({ text: 'Page ', font: BRAND.fontHeading, size: 16, color: BRAND.subtext }),
          new TextRun({ children: [PageNumber.CURRENT], font: BRAND.fontHeading, size: 16, color: BRAND.subtext }),
          new TextRun({ text: ' of ', font: BRAND.fontHeading, size: 16, color: BRAND.subtext }),
          new TextRun({ children: [PageNumber.TOTAL_PAGES], font: BRAND.fontHeading, size: 16, color: BRAND.subtext }),
        ],
      }),
    ],
  });

  const footerTable = new Table({
    width: { size: PAGE.contentWidth, type: WidthType.DXA },
    columnWidths: [
      Math.round(PAGE.contentWidth * 0.45),
      centreWidth,
      rightWidth,
    ],
    borders: {
      top:     { style: BorderStyle.NONE, size: 0 },
      left:    { style: BorderStyle.NONE, size: 0 },
      right:   { style: BorderStyle.NONE, size: 0 },
      bottom:  { style: BorderStyle.NONE, size: 0 },
      insideH: { style: BorderStyle.NONE, size: 0 },
      insideV: { style: BorderStyle.NONE, size: 0 },
    },
    rows: [
      new TableRow({
        height: { value: 360, rule: 'atLeast' },
        children: [leftCell, centreCell, rightCell],
      }),
    ],
  });

  return new Footer({ children: [footerTable] });
}

// ── Styles ────────────────────────────────────────────────────────────────────
const styles = {
  default: {
    document: {
      run: { font: BRAND.fontBody, size: 22 },  // 11pt body
    },
  },
  paragraphStyles: [
    {
      id: 'Normal', name: 'Normal', quickFormat: true,
      run:       { font: BRAND.fontBody, size: 22, color: BRAND.bodyText },
      paragraph: { spacing: { after: 120, line: 276, lineRule: 'auto' } },
    },
    {
      id: 'Heading1', name: 'Heading 1', basedOn: 'Normal', next: 'Normal', quickFormat: true,
      run: { font: BRAND.fontHeading, size: 32, bold: true, color: BRAND.primary },
      paragraph: {
        spacing: { before: 320, after: 120 }, outlineLevel: 0,
        border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: BRAND.primary, space: 4 } },
      },
    },
    {
      id: 'Heading2', name: 'Heading 2', basedOn: 'Normal', next: 'Normal', quickFormat: true,
      run: { font: BRAND.fontHeading, size: 26, bold: true, color: BRAND.primary },
      paragraph: { spacing: { before: 240, after: 80 }, outlineLevel: 1 },
    },
    {
      id: 'Heading3', name: 'Heading 3', basedOn: 'Normal', next: 'Normal', quickFormat: true,
      run: { font: BRAND.fontHeading, size: 22, bold: true, color: BRAND.primary },
      paragraph: { spacing: { before: 200, after: 60 }, outlineLevel: 2 },
    },
    {
      id: 'Heading4', name: 'Heading 4', basedOn: 'Normal', next: 'Normal', quickFormat: true,
      run: { font: BRAND.fontHeading, size: 22, bold: true, italics: true, color: BRAND.subtext },
      paragraph: { spacing: { before: 160, after: 40 }, outlineLevel: 3 },
    },
    {
      id: 'Caption', name: 'Caption', basedOn: 'Normal',
      run: { font: BRAND.fontBody, size: 18, italics: true, color: BRAND.subtext },
      paragraph: { alignment: AlignmentType.CENTER, spacing: { before: 60, after: 120 } },
    },
    {
      id: 'Header', name: 'Header', basedOn: 'Normal',
      run: { font: BRAND.fontHeading, size: 18 },
      paragraph: { spacing: { before: 0, after: 0 } },
    },
    {
      id: 'Footer', name: 'Footer', basedOn: 'Normal',
      run: { font: BRAND.fontHeading, size: 16, color: BRAND.subtext },
      paragraph: { spacing: { before: 0, after: 0 } },
    },
    {
      id: 'TableHeader', name: 'Table Header', basedOn: 'Normal',
      run: { font: BRAND.fontBody, size: 20, bold: true, color: BRAND.white },
      paragraph: { spacing: { before: 60, after: 60 } },
    },
    {
      id: 'TableBody', name: 'Table Body', basedOn: 'Normal',
      run: { font: BRAND.fontBody, size: 20, color: BRAND.bodyText },
      paragraph: { spacing: { before: 60, after: 60 } },
    },
  ],
};

// ── Numbering (bullets + numbered lists) ──────────────────────────────────────
const numbering = {
  config: [
    {
      reference: 'bullets',
      levels: [
        {
          level: 0, format: LevelFormat.BULLET, text: '\u2022', alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } },
                   run: { font: 'Symbol', size: 22 } },
        },
        {
          level: 1, format: LevelFormat.BULLET, text: '\u25E6', alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 1080, hanging: 360 } },
                   run: { font: 'Courier New', size: 22 } },
        },
      ],
    },
    {
      reference: 'numbered',
      levels: [
        {
          level: 0, format: LevelFormat.DECIMAL, text: '%1.', alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } },
        },
        {
          level: 1, format: LevelFormat.LOWER_LETTER, text: '%2.', alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 1080, hanging: 360 } } },
        },
      ],
    },
  ],
};

// ── Document — one placeholder section so Pandoc can extract styles ───────────
const doc = new Document({
  styles,
  numbering,
  sections: [
    {
      properties: {
        page: {
          size:   { width: PAGE.width, height: PAGE.height },
          margin: { top: PAGE.top, right: PAGE.right, bottom: PAGE.bottom, left: PAGE.left },
        },
        titlePage: false,
      },
      headers: { default: makeHeader() },
      footers: { default: makeFooter() },
      children: [
        new Paragraph({
          heading: HeadingLevel.HEADING_1,
          children: [new TextRun('Reference Document — Firm Brand Styles')],
        }),
        new Paragraph({
          children: [new TextRun({ text: 'This file is used as a Pandoc --reference-doc. Do not add content. Styles only.', italics: true, color: BRAND.subtext, size: 18 })],
        }),
        new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun('Heading 2 Sample')] }),
        new Paragraph({ heading: HeadingLevel.HEADING_3, children: [new TextRun('Heading 3 Sample')] }),
        new Paragraph({ children: [new TextRun('Body text — Calibri 11pt. Normal paragraph spacing.')] }),
      ],
    },
  ],
});

// ── Write ─────────────────────────────────────────────────────────────────────
const outDir = path.dirname(OUT_PATH);
if (!fs.existsSync(outDir)) fs.mkdirSync(outDir, { recursive: true });

Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync(OUT_PATH, buf);
  const kb = Math.round(buf.length / 1024);
  console.log(`✔ reference.docx written → ${OUT_PATH} (${kb} KB)`);
  console.log(`  Brand: #${BRAND.primary} · ${BRAND.fontHeading} headings · ${BRAND.fontBody} body`);
  console.log(`  RFP in footer: ${RFP_NUMBER}`);
  console.log(`  To update RFP number: node scripts/publish/generate_reference_docx.js --rfp "RFP-2025-001"`);
}).catch(err => {
  console.error('✖ Failed to generate reference.docx:', err.message);
  process.exit(1);
});
