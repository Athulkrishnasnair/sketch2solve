import assert from 'node:assert/strict'
import { readFileSync, existsSync } from 'node:fs'
import { test } from 'node:test'

const appFile = readFileSync(new URL('../../src/App.vue', import.meta.url), 'utf8')
const shellFile = readFileSync(new URL('../../src/styles/shell.css', import.meta.url), 'utf8')
const indexFile = readFileSync(new URL('../../index.html', import.meta.url), 'utf8')
const onboardingFile = readFileSync(new URL('../../src/components/UserOnboardingModal.vue', import.meta.url), 'utf8')
const guideFile = readFileSync(new URL('../../src/components/GettingStartedGuide.vue', import.meta.url), 'utf8')
const dashboardFile = readFileSync(new URL('../../src/pages/DashboardPage.vue', import.meta.url), 'utf8')

test('1. Layout and Scrolling: Zero document/browser-level scrollbars across application', () => {
  // html, body have overflow: hidden and fixed viewport height
  assert.match(shellFile, /html,\s*body\s*\{[^}]*overflow:\s*hidden/s)
  assert.match(shellFile, /height:\s*100vh/)
  // app-frame has full viewport height
  assert.match(shellFile, /\.app-frame\s*\{[^}]*height:\s*100vh/s)
  // sidebar is stable with its own internal scroll
  assert.match(shellFile, /\.sidebar\s*\{[^}]*overflow-y:\s*auto/s)
  // topbar is fixed/pinned
  assert.match(shellFile, /\.topbar\s*\{[^}]*flex:\s*0 0 59px/s)
  // main-content-viewport handles internal vertical scrolling for non-editor pages
  assert.match(shellFile, /\.main-content-viewport\s*\{[^}]*overflow-y:\s*auto/s)
  assert.match(shellFile, /\.main-content-viewport\s*\{[^}]*overflow-x:\s*hidden/s)
  assert.match(appFile, /class="main-content-viewport"/)
  // editor frame layout preserved
  assert.match(shellFile, /\.app-frame\.in-editor-frame/)
})

test('2. First-time user name onboarding: "What should we call you?" modal and persistence', () => {
  assert.match(onboardingFile, /What should we call you\?/)
  assert.match(onboardingFile, /localStorage\.setItem\('sketch2solve_username'/)
  assert.match(onboardingFile, /name-input/)
  assert.match(onboardingFile, /Please enter your name/)
  // App.vue connects onboarding and displays user name
  assert.match(appFile, /localStorage\.getItem\('sketch2solve_username'\)/)
  assert.match(appFile, /<UserOnboardingModal/)
  assert.match(appFile, /class="user-profile-btn"/)
  assert.match(appFile, /class="user-name-text"/)
  assert.match(appFile, /handleOpenRename/)
})

test('3. Getting Started guide: 6-step beginner workflow guide', () => {
  // 6 specific steps
  assert.match(guideFile, /Create a New Analysis/)
  assert.match(guideFile, /Upload a Sketch or Describe with AI/)
  assert.match(guideFile, /Review & Correct Geometry/)
  assert.match(guideFile, /Add Supports & External Loads/)
  assert.match(guideFile, /Validate & Run the Solver/)
  assert.match(guideFile, /Understand Results & Export/)
  // accessible from Dashboard and sidebar
  assert.match(dashboardFile, /dashboard-guide-btn/)
  assert.match(appFile, /<GettingStartedGuide/)
  assert.match(appFile, /sidebar-guide-card/)
  assert.match(appFile, /btn-topbar-guide/)
})

test('4. Removal of developer-facing messaging and generic avatars', () => {
  // "Private by default" removed
  assert.doesNotMatch(appFile, /Private by default/)
  assert.doesNotMatch(dashboardFile, /Private by default/)
  // "Local review workspace" removed
  assert.doesNotMatch(appFile, /Local review workspace/)
  assert.doesNotMatch(dashboardFile, /Local review workspace/)
  // Avatar UI removed from header
  assert.doesNotMatch(appFile, /<span class="avatar"[^>]*>S<\/span>/)
  assert.doesNotMatch(appFile, /<button class="avatar"/)
})

test('5. Branding & Official Logo Assets: logo.png and favicon paths', () => {
  assert.ok(existsSync(new URL('../../public/logo.png', import.meta.url)))
  assert.ok(existsSync(new URL('../../public/favicon.png', import.meta.url)))
  assert.ok(existsSync(new URL('../../public/favicon-32x32.png', import.meta.url)))
  // favicon references in index.html
  assert.match(indexFile, /href="\/favicon-32x32\.png"/)
  assert.match(indexFile, /href="\/favicon\.png"/)
  assert.match(indexFile, /href="\/logo\.png"/)
  // App.vue brand mark uses logo
  assert.match(appFile, /<img src="\/logo\.png"/)
})

