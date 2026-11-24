import { cpSync, readFileSync, readdirSync, writeFileSync } from 'node:fs'
import { dirname, join } from 'node:path'

const [dir, skillsDir, themeFile, out] = process.argv.slice(2)
const here = import.meta.dirname
const read = path => readFileSync(path, 'utf8')

const readme = read(join(dir, 'README.md'))
const files = readdirSync(dir).filter(f => f.endsWith('.md') && f !== 'README.md')
const linked = [...readme.matchAll(/\]\(([a-z0-9-]+)\.md\)/g)].map(m => m[1] + '.md').filter((f, i, a) => files.includes(f) && a.indexOf(f) === i)
const order = [...linked, ...files.filter(f => !linked.includes(f)).sort()]
const titleOf = md => md.match(/^# (.+)$/m)?.[1] ?? ''

function playbookList() {
  return readdirSync(skillsDir).sort().map(name => {
    const md = read(join(skillsDir, name, 'SKILL.md'))
    const description = md.match(/^description: (.+)$/m)?.[1] ?? ''
    const steps = [...md.matchAll(/^\d+\. \*\*(.+?)\*\*/gm)].map((m, i) => `${i + 1}. ${m[1].replace(/[.:]$/, '')}`)
    return `## ${name}\n\n${description}\n\n${steps.join('\n')}\n`
  }).join('\n')
}

const expand = md => md.replace('{{playbooks}}', playbookList)
const pages = [{ id: 'how-kagestack-works', file: 'README.md', title: titleOf(readme), md: readme },
  ...order.map(f => { const md = expand(read(join(dir, f))); return { id: f.slice(0, -3), file: f, title: titleOf(md) || f, md } })]
const data = JSON.stringify({ pages }).replace(/</g, '\\u003c')
const style = read(join(here, 'site.css')) + '\n' + read(themeFile)
const script = read(join(here, 'site.js'))

writeFileSync(out, `<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>kagestack docs</title>
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 32 32%22%3E%3Crect width=%2232%22 height=%2232%22 fill=%22%230a0a0a%22/%3E%3Ctext x=%2216%22 y=%2222%22 font-family=%22monospace%22 font-size=%2216%22 fill=%22%23ffffff%22 text-anchor=%22middle%22%3Eks%3C/text%3E%3C/svg%3E">
<meta name="description" content="What kagestack does for coding agents, how it works, and why each change shipped.">
<style>${style}</style></head><body>
<a class="skip" href="#main">Skip to content</a>
<header><div class="bar">
 <a class="logo" href="#how-kagestack-works"><span class="word">kagestack</span><span class="t">docs</span></a>
 <div class="keys"><a href="#how-kagestack-works" class="on"><b>D</b>Docs</a><a href="#changes"><b>C</b>Changes</a><a href="https://github.com/aloki-alok/kagestack"><b>G</b>GitHub</a></div>
 <div class="tools"><button class="btn" id="sbtn">Search<kbd>/</kbd></button><button class="btn" id="theme" title="Theme (T)">Theme</button></div>
</div></header>
<div class="grid hero"><div class="sp"></div><div id="hero"></div></div><hr class="rule"><div class="grid"><nav class="tree" id="tree"></nav><main id="main"></main></div>
<div class="scrim" id="scrim"><div class="palette"><input id="q" placeholder="Search the docs" autocomplete="off"><div class="res" id="res"></div></div></div>
<div class="zoom" id="zoom"></div>
<script src="https://cdn.jsdelivr.net/npm/marked@12.0.2/marked.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/mermaid@10.9.1/dist/mermaid.min.js"></script>
<script>const D=${data};
${script}</script></body></html>
`)
cpSync(join(here, 'fonts'), join(dirname(out), 'fonts'), { recursive: true })
cpSync(out, join(dirname(out), '404.html'))
console.log('wrote', out, pages.length, 'pages')
