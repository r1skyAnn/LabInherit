// Export utilities for notes — supports .md, .html, .docx, .pdf, mindmap
// Pure frontend: zero backend involvement, downloads directly in browser.

import { marked, Renderer } from 'marked'
import hljs from 'highlight.js/lib/core'
import 'highlight.js/styles/github-dark.css'

import javascript from 'highlight.js/lib/languages/javascript'
import typescript from 'highlight.js/lib/languages/typescript'
import python from 'highlight.js/lib/languages/python'
import java from 'highlight.js/lib/languages/java'
import bash from 'highlight.js/lib/languages/bash'
import json from 'highlight.js/lib/languages/json'
import xml from 'highlight.js/lib/languages/xml'
import css from 'highlight.js/lib/languages/css'
import sql from 'highlight.js/lib/languages/sql'
import markdown from 'highlight.js/lib/languages/markdown'
import go from 'highlight.js/lib/languages/go'
import rust from 'highlight.js/lib/languages/rust'
import yaml from 'highlight.js/lib/languages/yaml'
import shell from 'highlight.js/lib/languages/shell'

hljs.registerLanguage('javascript', javascript)
hljs.registerLanguage('js', javascript)
hljs.registerLanguage('typescript', typescript)
hljs.registerLanguage('ts', typescript)
hljs.registerLanguage('tsx', typescript)
hljs.registerLanguage('jsx', javascript)
hljs.registerLanguage('python', python)
hljs.registerLanguage('py', python)
hljs.registerLanguage('java', java)
hljs.registerLanguage('bash', bash)
hljs.registerLanguage('sh', bash)
hljs.registerLanguage('json', json)
hljs.registerLanguage('html', xml)
hljs.registerLanguage('xml', xml)
hljs.registerLanguage('vue', xml)
hljs.registerLanguage('css', css)
hljs.registerLanguage('sql', sql)
hljs.registerLanguage('markdown', markdown)
hljs.registerLanguage('md', markdown)
hljs.registerLanguage('go', go)
hljs.registerLanguage('rust', rust)
hljs.registerLanguage('rs', rust)
hljs.registerLanguage('yaml', yaml)
hljs.registerLanguage('yml', yaml)
hljs.registerLanguage('shell', shell)

const renderer = new Renderer()
const originalCode = renderer.code.bind(renderer)
renderer.code = (code: { text: string; lang?: string | undefined }, lang?: string) => {
  const codeText = typeof code === 'string' ? code : (code as any).text ?? ''
  const codeLang = (typeof code === 'object' ? (code as any).lang : lang) || ''
  if (codeLang && hljs.getLanguage(codeLang)) {
    try {
      const highlighted = hljs.highlight(codeText, { language: codeLang, ignoreIllegals: true }).value
      return `<pre><code class="hljs language-${codeLang}">${highlighted}</code></pre>`
    } catch {
      // fall through
    }
  }
  try {
    const auto = hljs.highlightAuto(codeText).value
    return `<pre><code class="hljs">${auto}</code></pre>`
  } catch {
    return originalCode(code, lang)
  }
}

marked.setOptions({ renderer, gfm: true, breaks: false })

function escapeHtml(s: string): string {
  return s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}

function safeFilename(name: string, ext: string): string {
  const safe = name.replace(/[\\/:*?"<>|]/g, '_').trim() || 'note'
  const stamp = new Date().toISOString().slice(0, 10)
  return `${safe}-${stamp}.${ext}`
}

// ── 1) Markdown source ─────────────────────────────────────────
export function exportMarkdown(title: string, content: string): void {
  const body = `# ${title}\n\n${content}\n`
  const blob = new Blob([body], { type: 'text/markdown;charset=utf-8' })
  downloadBlob(blob, safeFilename(title, 'md'))
}

// ── 2) Standalone HTML ─────────────────────────────────────────
export function exportHTML(title: string, content: string): void {
  const html = marked(content) as string
  const document = `<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>${escapeHtml(title)}</title>
<style>
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif; line-height: 1.75; max-width: 860px; margin: 2rem auto; padding: 0 1rem; color: #24292f; }
  h1, h2, h3, h4 { margin-top: 1.6em; font-weight: 600; line-height: 1.3; }
  h1 { font-size: 1.8rem; padding-bottom: 0.3em; border-bottom: 1px solid #d0d7de; }
  h2 { font-size: 1.5rem; padding-bottom: 0.3em; border-bottom: 1px solid #d0d7de; }
  h3 { font-size: 1.25rem; }
  h4 { font-size: 1.05rem; }
  p { margin: 0.7em 0; }
  code { background: rgba(175, 184, 193, 0.2); padding: 0.15em 0.45em; border-radius: 4px; font-size: 0.88em; font-family: 'JetBrains Mono', Consolas, Monaco, monospace; color: #e64980; }
  pre { background: #0d1117; padding: 1rem 1.1rem; border-radius: 8px; overflow-x: auto; margin: 0.8em 0; border: 1px solid #30363d; }
  pre code { background: none; padding: 0; color: inherit; border-radius: 0; }
  ul, ol { padding-left: 1.8em; margin: 0.6em 0; }
  li { margin: 0.25em 0; }
  blockquote { border-left: 4px solid #0969da; padding: 0.4em 1em; margin: 0.8em 0; color: #57606a; background: #f6f8fa; border-radius: 0 6px 6px 0; }
  table { border-collapse: collapse; width: 100%; margin: 0.8em 0; font-size: 0.92em; }
  th, td { border: 1px solid #d0d7de; padding: 0.5em 0.9em; text-align: left; }
  th { background: #f6f8fa; font-weight: 600; }
  a { color: #0969da; text-decoration: none; }
  a:hover { text-decoration: underline; }
  img { max-width: 100%; border-radius: 6px; }
  hr { border: none; border-top: 1px solid #d0d7de; margin: 1.5em 0; }
</style>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github-dark.min.css" />
</head>
<body>
<h1>${escapeHtml(title)}</h1>
${html}
</body>
</html>`
  const blob = new Blob([document], { type: 'text/html;charset=utf-8' })
  downloadBlob(blob, safeFilename(title, 'html'))
}

// ── 3) Word (.docx) ────────────────────────────────────────────
// Use the `docx` library; convert markdown to a sequence of paragraph/heading
// objects. Code blocks become monospace runs. Tables/lists/quote simplified.
export async function exportDocx(title: string, content: string): Promise<void> {
  const {
    Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType,
    Table, TableRow, TableCell, WidthType, BorderStyle,
  } = await import('docx')

  const lines = content.split('\n')
  const blocks: any[] = []
  let i = 0
  while (i < lines.length) {
    const line = lines[i]

    // Code block
    if (line.startsWith('```')) {
      const lang = line.slice(3).trim()
      i++
      const buf: string[] = []
      while (i < lines.length && !lines[i].startsWith('```')) {
        buf.push(lines[i])
        i++
      }
      i++ // skip closing fence
      blocks.push(
        new Paragraph({
          children: buf.map((l, idx) => new TextRun({
            text: l,
            font: 'Consolas',
            size: 18,
            break: idx > 0 ? 1 : 0,
          })),
          shading: { fill: '0d1117' },
          spacing: { before: 100, after: 100 },
        }),
      )
      continue
    }

    // Heading
    const headingMatch = /^(#{1,6})\s+(.+)$/.exec(line)
    if (headingMatch) {
      const level = headingMatch[1].length
      const text = headingMatch[2].trim()
      const levelMap: Record<number, (typeof HeadingLevel)[keyof typeof HeadingLevel]> = {
        1: HeadingLevel.HEADING_1, 2: HeadingLevel.HEADING_2,
        3: HeadingLevel.HEADING_3, 4: HeadingLevel.HEADING_4,
        5: HeadingLevel.HEADING_5, 6: HeadingLevel.HEADING_6,
      }
      blocks.push(new Paragraph({
        heading: levelMap[level],
        children: parseInline(text),
      }))
      i++
      continue
    }

    // Table (collect lines until blank)
    if (line.startsWith('|') && line.includes('|')) {
      const tableLines: string[] = []
      while (i < lines.length && lines[i].startsWith('|')) {
        tableLines.push(lines[i])
        i++
      }
      // Skip separator line if present (e.g. |---|---|)
      const filtered = tableLines.filter(l => !/^\|[\s\-:|]+\|$/.test(l.trim()))
      if (filtered.length >= 1) {
        const rows = filtered.map(parseTableRow)
        blocks.push(
          new Table({
            width: { size: 100, type: WidthType.PERCENTAGE },
            rows: rows.map(r => new TableRow({
              children: r.map(cell => new TableCell({
                children: [new Paragraph({ children: [new TextRun({ text: cell })] })],
              })),
            })),
          }),
        )
      }
      continue
    }

    // Blank line
    if (line.trim() === '') {
      blocks.push(new Paragraph({ children: [new TextRun('')] }))
      i++
      continue
    }

    // List item
    const listMatch = /^(\s*)([-*+]|\d+\.)\s+(.+)$/.exec(line)
    if (listMatch) {
      const indent = Math.floor(listMatch[1].length / 2)
      const text = listMatch[3]
      blocks.push(new Paragraph({
        bullet: { level: indent },
        children: parseInline(text),
      }))
      i++
      continue
    }

    // Blockquote
    if (line.startsWith('> ')) {
      const text = line.slice(2)
      blocks.push(new Paragraph({
        indent: { left: 360 },
        children: parseInline(text),
      }))
      i++
      continue
    }

    // Regular paragraph (may span multiple lines until blank)
    const buf = [line]
    i++
    while (i < lines.length && lines[i].trim() !== '' && !isSpecialLine(lines[i])) {
      buf.push(lines[i])
      i++
    }
    blocks.push(new Paragraph({ children: parseInline(buf.join(' ')) }))
  }

  const doc = new Document({
    creator: 'LabInherit',
    title,
    styles: {
      default: {
        document: {
          run: { font: 'Calibri', size: 22 },
        },
      },
    },
    sections: [{
      properties: {},
      children: [
        new Paragraph({
          heading: HeadingLevel.TITLE,
          children: [new TextRun({ text: title, bold: true, size: 36 })],
          alignment: AlignmentType.CENTER,
          spacing: { after: 240 },
        }),
        ...blocks,
      ],
    }],
  })

  const blob = await Packer.toBlob(doc)
  downloadBlob(blob, safeFilename(title, 'docx'))
}

function isSpecialLine(line: string): boolean {
  return /^(#{1,6}\s|```|\||>\s|[-*+]\s|\d+\.\s)/.test(line)
}

function parseTableRow(line: string): string[] {
  // | a | b | c |
  const inner = line.replace(/^\||\|$/g, '')
  return inner.split('|').map(s => s.trim())
}

function parseInline(text: string): TextRun[] {
  // Very simple inline parser: **bold**, *italic*, `code`, [text](url)
  const runs: TextRun[] = []
  let buf = ''
  let i = 0
  const flush = (opts: any = {}) => {
    if (buf) {
      runs.push(new TextRun({ text: buf, ...opts }))
      buf = ''
    }
  }
  while (i < text.length) {
    // Inline code
    if (text[i] === '`') {
      flush()
      const end = text.indexOf('`', i + 1)
      if (end === -1) { buf += text[i]; i++; continue }
      runs.push(new TextRun({ text: text.slice(i + 1, end), font: 'Consolas' }))
      i = end + 1
      continue
    }
    // Bold **
    if (text[i] === '*' && text[i + 1] === '*') {
      flush()
      const end = text.indexOf('**', i + 2)
      if (end === -1) { buf += text[i]; i++; continue }
      runs.push(new TextRun({ text: text.slice(i + 2, end), bold: true }))
      i = end + 2
      continue
    }
    // Italic *
    if (text[i] === '*') {
      flush()
      const end = text.indexOf('*', i + 1)
      if (end === -1) { buf += text[i]; i++; continue }
      runs.push(new TextRun({ text: text.slice(i + 1, end), italics: true }))
      i = end + 1
      continue
    }
    buf += text[i]
    i++
  }
  flush()
  return runs
}

// ── 4) PDF ─────────────────────────────────────────────────────
export async function exportPDF(title: string, content: string): Promise<void> {
  const html = marked(content) as string
  const container = document.createElement('div')
  container.innerHTML = `
    <style>
      body { font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Microsoft YaHei', sans-serif; line-height: 1.75; color: #24292f; padding: 20px; }
      h1, h2, h3, h4 { font-weight: 600; }
      h1 { font-size: 24px; border-bottom: 1px solid #d0d7de; padding-bottom: 6px; }
      h2 { font-size: 20px; }
      h3 { font-size: 16px; }
      code { background: #f6f8fa; padding: 1px 4px; border-radius: 3px; font-family: Consolas, monospace; }
      pre { background: #0d1117; color: #cdd6f4; padding: 10px; border-radius: 6px; font-size: 11px; }
      table { border-collapse: collapse; width: 100%; }
      th, td { border: 1px solid #d0d7de; padding: 4px 8px; }
      th { background: #f6f8fa; }
      blockquote { border-left: 3px solid #0969da; padding-left: 10px; color: #57606a; margin-left: 0; }
      img { max-width: 100%; }
    </style>
    <h1>${escapeHtml(title)}</h1>
    ${html}
  `
  container.style.position = 'fixed'
  container.style.left = '-9999px'
  container.style.top = '0'
  container.style.width = '760px'
  container.style.background = '#fff'
  document.body.appendChild(container)

  try {
    const html2pdf = (await import('html2pdf.js')).default
    await html2pdf()
      .set({
        margin: 10,
        filename: safeFilename(title, 'pdf'),
        image: { type: 'jpeg', quality: 0.95 },
        html2canvas: { scale: 2, useCORS: true },
        jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' },
        pagebreak: { mode: ['avoid-all', 'css', 'legacy'] },
      })
      .from(container)
      .save()
  } finally {
    document.body.removeChild(container)
  }
}

// ── 5) Mindmap (markmap) ───────────────────────────────────────
export async function renderMindmap(content: string, target: HTMLElement): Promise<void> {
  const { Markmap, loadCSS, loadJS } = await import('markmap-view')
  const { Transformer } = await import('markmap-lib')
  const transformer = new Transformer()
  const { root } = transformer.transform(content)
  // Load markmap assets
  loadCSS()
  loadJS()
  // Clear previous
  target.innerHTML = '<svg style="width: 100%; height: 600px;" />'
  const svg = target.querySelector('svg') as SVGElement
  const mm = Markmap.create(svg)
  mm.setData(root)
  mm.fit()
}

export async function exportMindmapSVG(content: string, title: string): Promise<void> {
  const { Transformer } = await import('markmap-lib')
  const { Markmap } = await import('markmap-view')
  const transformer = new Transformer()
  const { root } = transformer.transform(content)
  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg')
  svg.setAttribute('width', '1600')
  svg.setAttribute('height', '1200')
  svg.style.background = '#fff'
  document.body.appendChild(svg)
  try {
    const mm = Markmap.create(svg)
    mm.setData(root)
    mm.fit()
    // Allow layout
    await new Promise(r => setTimeout(r, 300))
    const serializer = new XMLSerializer()
    const source = serializer.serializeToString(svg)
    const blob = new Blob([source], { type: 'image/svg+xml;charset=utf-8' })
    downloadBlob(blob, safeFilename(title, 'svg'))
  } finally {
    document.body.removeChild(svg)
  }
}