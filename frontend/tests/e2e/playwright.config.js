import { mkdirSync } from 'node:fs'
import path from 'node:path'
import { defineConfig } from '@playwright/test'

const configDirectory = import.meta.dirname
const frontendDirectory = path.resolve(configDirectory, '../..')
const backendDirectory = path.resolve(configDirectory, '../../../backend')
const qaDirectory = path.resolve(configDirectory, '../../../qa-output')
const runName = `run-${new Date().toISOString().replaceAll(/[:.]/g, '-')}-${process.pid}`
const runDirectory = path.join(qaDirectory, runName)

mkdirSync(runDirectory, { recursive: true })
process.env.QA_OUTPUT_DIR = runDirectory

export default defineConfig({
  testDir: '.',
  testMatch: '**/*.spec.js',
  fullyParallel: false,
  workers: 1,
  retries: 0,
  timeout: 45_000,
  expect: { timeout: 8_000 },
  outputDir: path.join(runDirectory, 'playwright-artifacts'),
  reporter: [
    ['list'],
    ['json', { outputFile: path.join(runDirectory, 'playwright-results.json') }],
  ],
  use: {
    baseURL: 'http://127.0.0.1:5174',
    browserName: 'chromium',
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
    video: 'retain-on-failure',
  },
  webServer: [
    {
      command: './.venv/bin/python ../frontend/tests/e2e/mock_backend.py',
      cwd: backendDirectory,
      url: 'http://127.0.0.1:5101/api/health',
      reuseExistingServer: false,
      timeout: 30_000,
    },
    {
      command: 'npm run dev -- --config tests/e2e/vite.config.js --host 127.0.0.1 --port 5174 --strictPort',
      cwd: frontendDirectory,
      url: 'http://127.0.0.1:5174',
      reuseExistingServer: false,
      timeout: 30_000,
      env: {
        VITE_API_BASE_URL: 'http://127.0.0.1:5174',
      },
    },
  ],
})
