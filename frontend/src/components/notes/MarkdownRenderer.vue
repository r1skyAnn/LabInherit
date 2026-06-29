<script setup lang="ts">
import { computed } from 'vue'
import { marked, Renderer } from 'marked'
import hljs from 'highlight.js/lib/core'
import 'highlight.js/styles/github-dark.css'

// Register common languages — full set would bloat the bundle; these cover 95% of use cases
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

// Custom renderer: hand off code blocks to highlight.js
const renderer = new Renderer()
const originalCode = renderer.code.bind(renderer)
renderer.code = (code: { text: string; lang?: string | undefined }, lang?: string) => {
  // marked v18 passes a Code object
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
  // Auto-detect for common languages
  try {
    const auto = hljs.highlightAuto(codeText).value
    return `<pre><code class="hljs">${auto}</code></pre>`
  } catch {
    return originalCode(code, lang)
  }
}

marked.setOptions({ renderer, gfm: true, breaks: false })

const props = defineProps<{
  content: string
}>()

const html = computed(() => {
  if (!props.content) return ''
  return marked(props.content) as string
})
</script>

<template>
  <div class="markdown-body" v-html="html" />
</template>

<style scoped>
.markdown-body {
  line-height: 1.75;
  color: var(--el-text-color-regular);
  font-size: 0.95rem;
}

/* Headings */
.markdown-body :deep(h1),
.markdown-body :deep(h2),
.markdown-body :deep(h3),
.markdown-body :deep(h4) {
  margin-top: 1.6em;
  margin-bottom: 0.5em;
  font-weight: 600;
  line-height: 1.3;
}
.markdown-body :deep(h1) { font-size: 1.6rem; padding-bottom: 0.3em; border-bottom: 1px solid var(--el-border-color-lighter); }
.markdown-body :deep(h2) { font-size: 1.35rem; padding-bottom: 0.3em; border-bottom: 1px solid var(--el-border-color-lighter); }
.markdown-body :deep(h3) { font-size: 1.15rem; }
.markdown-body :deep(h4) { font-size: 1rem; }

.markdown-body :deep(p) { margin: 0.7em 0; }
.markdown-body :deep(strong) { font-weight: 600; color: var(--el-text-color-primary); }
.markdown-body :deep(em) { font-style: italic; }
.markdown-body :deep(del) { color: var(--el-text-color-secondary); }

/* Inline code */
.markdown-body :deep(code) {
  background: var(--el-fill-color-light);
  padding: 0.15em 0.45em;
  border-radius: 4px;
  font-size: 0.88em;
  font-family: 'JetBrains Mono', 'Fira Code', Consolas, Monaco, monospace;
  color: #e64980;
}

/* Code blocks — github-dark via global css */
.markdown-body :deep(pre) {
  background: #0d1117;
  padding: 1rem 1.1rem;
  border-radius: 8px;
  overflow-x: auto;
  margin: 0.8em 0;
  border: 1px solid #30363d;
  line-height: 1.6;
}
.markdown-body :deep(pre code) {
  background: none;
  padding: 0;
  color: inherit;
  font-size: 0.85em;
  border-radius: 0;
  font-family: 'JetBrains Mono', 'Fira Code', Consolas, Monaco, monospace;
}

/* Lists */
.markdown-body :deep(ul),
.markdown-body :deep(ol) {
  padding-left: 1.8em;
  margin: 0.6em 0;
}
.markdown-body :deep(li) { margin: 0.25em 0; }
.markdown-body :deep(li > p) { margin: 0.3em 0; }
.markdown-body :deep(ul ul),
.markdown-body :deep(ol ol),
.markdown-body :deep(ul ol),
.markdown-body :deep(ol ul) {
  margin: 0.2em 0;
}

/* Blockquote */
.markdown-body :deep(blockquote) {
  border-left: 4px solid var(--el-color-primary);
  padding: 0.4em 1em;
  margin: 0.8em 0;
  color: var(--el-text-color-secondary);
  background: var(--el-fill-color-light);
  border-radius: 0 6px 6px 0;
}
.markdown-body :deep(blockquote > :first-child) { margin-top: 0; }
.markdown-body :deep(blockquote > :last-child) { margin-bottom: 0; }

/* Tables */
.markdown-body :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin: 0.8em 0;
  font-size: 0.9em;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 6px;
  overflow: hidden;
}
.markdown-body :deep(th),
.markdown-body :deep(td) {
  border: 1px solid var(--el-border-color-lighter);
  padding: 0.5em 0.9em;
  text-align: left;
}
.markdown-body :deep(th) {
  background: var(--el-fill-color);
  font-weight: 600;
}
.markdown-body :deep(tr:nth-child(2n)) {
  background: var(--el-fill-color-light);
}

/* Links */
.markdown-body :deep(a) {
  color: var(--el-color-primary);
  text-decoration: none;
  border-bottom: 1px solid transparent;
  transition: border-color 0.15s;
}
.markdown-body :deep(a:hover) {
  border-bottom-color: var(--el-color-primary);
}

/* Images */
.markdown-body :deep(img) {
  max-width: 100%;
  border-radius: 6px;
  margin: 0.5em 0;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

/* Horizontal rule */
.markdown-body :deep(hr) {
  border: none;
  border-top: 1px solid var(--el-border-color-lighter);
  margin: 1.5em 0;
}

/* Task list */
.markdown-body :deep(input[type="checkbox"]) {
  margin-right: 0.4em;
}
</style>