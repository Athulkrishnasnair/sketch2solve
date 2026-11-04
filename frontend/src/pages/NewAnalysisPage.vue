<script setup>
import { onBeforeUnmount, ref, watch } from 'vue'
import { createAnalysis } from '../api/analyses'

const emit = defineEmits(['created'])
const fileInput = ref(null)
const selectedFile = ref(null)
const previewUrl = ref('')
const provider = ref('meta')
const dragging = ref(false)
const submitting = ref(false)
const errorMessage = ref('')

watch(selectedFile, (file) => {
  if (previewUrl.value) URL.revokeObjectURL(previewUrl.value)
  previewUrl.value = file ? URL.createObjectURL(file) : ''
})

function chooseFile() { fileInput.value?.click() }

function acceptFile(file) {
  errorMessage.value = ''
  if (!file) return
  if (!file.size) {
    selectedFile.value = null
    errorMessage.value = 'The selected file is empty. Choose a readable JPEG, PNG, or WebP image.'
    return
  }
  if (file.size > 10 * 1024 * 1024) {
    selectedFile.value = null
    errorMessage.value = 'This image is larger than the 10 MiB upload limit.'
    return
  }
  selectedFile.value = file
}

function handleFileChange(event) {
  acceptFile(event.target.files?.[0])
  event.target.value = ''
}

function handleDrop(event) {
  dragging.value = false
  acceptFile(event.dataTransfer?.files?.[0])
}

function humanizeError(error) {
  const messages = {
    MISSING_GEMINI_API_KEY: 'The interpretation service is not configured with an API key.',
    MISSING_MODEL_API_KEY: 'The interpretation service is not configured with an API key.',
    INVALID_IMAGE: 'The uploaded file could not be read as a supported sketch image.',
    IMAGE_TOO_LARGE: 'The image exceeds the 10 MiB upload limit.',
    UNSUPPORTED_IMAGE_TYPE: 'Choose a JPEG, PNG, or WebP image.',
    GEMINI_API_ERROR: 'The AI model could not complete the interpretation request.',
    MUSE_API_ERROR: 'The AI model could not complete the interpretation request.',
    GEMINI_AUTHENTICATION_FAILED: 'The AI service rejected the backend credential or account access.',
    MUSE_AUTHENTICATION_FAILED: 'The AI service rejected the backend credential or account access.',
    GEMINI_INVALID_MODEL: 'The AI service did not recognize the configured model.',
    MUSE_INVALID_MODEL: 'The AI service did not recognize the configured model.',
    GEMINI_RATE_LIMITED: 'The AI service rate limit or quota was reached. Try again later.',
    MUSE_RATE_LIMITED: 'The AI service rate limit or quota was reached. Try again later.',
    GEMINI_NETWORK_ERROR: 'The backend could not reach the AI service. Check the backend network connection.',
    MUSE_NETWORK_ERROR: 'The backend could not reach the AI service. Check the backend network connection.',
    GEMINI_TIMEOUT: 'The AI interpretation request timed out. Try again with a smaller image.',
    MUSE_TIMEOUT: 'The AI interpretation request timed out. Try again with a smaller image.',
    INVALID_GEMINI_RESPONSE: 'The AI model returned a response that did not match the expected interpretation format.',
    INVALID_MUSE_RESPONSE: 'The AI model returned a response that did not match the expected interpretation format.',
    IMAGE_STORAGE_FAILED: 'The backend could not save the uploaded image.',
    ANALYSIS_HISTORY_UNAVAILABLE: 'The backend could not save or retrieve analysis history.',
  }
  return messages[error.body?.error_code] || error.message || 'The analysis could not be completed.'
}

async function submit() {
  if (!selectedFile.value || submitting.value) return
  submitting.value = true
  errorMessage.value = ''
  try {
    const result = await createAnalysis(selectedFile.value, 'meta')
    selectedFile.value = null
    emit('created', result.analysis_id)
  } catch (error) {
    errorMessage.value = humanizeError(error)
    if (error.body?.analysis_id) emit('created', error.body.analysis_id)
  } finally {
    submitting.value = false
  }
}

onBeforeUnmount(() => { if (previewUrl.value) URL.revokeObjectURL(previewUrl.value) })
</script>

<template>
  <section class="page-content">
    <div class="page-heading">
      <div><div class="eyebrow">SKETCH INTERPRETATION</div><h1>Review a structure, <em>before</em> you solve it.</h1><p>Compare computer vision evidence with a model interpretation. Each proposal requires a human review before it can reach the solver.</p></div>
      <div class="heading-stamp"><span class="stamp-line"></span><span>01 / INTAKE</span></div>
    </div>

    <div v-if="errorMessage" class="alert alert-error" role="alert"><span class="alert-icon">!</span><div><strong>Could not start analysis</strong><p>{{ errorMessage }}</p></div><button type="button" aria-label="Dismiss error" @click="errorMessage = ''">×</button></div>

    <div class="intake-grid">
      <section class="upload-card card-surface">
        <div class="card-heading"><div><div class="eyebrow">STEP 1</div><h2>Add a sketch</h2></div><span class="file-limit">MAX 10 MiB</span></div>
        <input ref="fileInput" class="visually-hidden" type="file" accept="image/jpeg,image/png,image/webp" @change="handleFileChange" />
        <div :class="['dropzone', { dragging, 'has-file': selectedFile }]" role="button" tabindex="0" @click="chooseFile" @keydown.enter.prevent="chooseFile" @keydown.space.prevent="chooseFile" @dragover.prevent="dragging = true" @dragleave.prevent="dragging = false" @drop.prevent="handleDrop">
          <div class="upload-icon"><svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M12 15V4m0 0L7.5 8.5M12 4l4.5 4.5M5 14v5h14v-5" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" /></svg></div>
          <template v-if="selectedFile"><strong>{{ selectedFile.name }}</strong><span>{{ (selectedFile.size / 1024 / 1024).toFixed(2) }} MiB · {{ selectedFile.type }}</span></template>
          <template v-else><strong>Drop your sketch here</strong><span>or <u>browse files</u> on your device</span></template>
          <small>JPEG, PNG or WebP</small>
        </div>
        <div v-if="previewUrl" class="upload-preview"><img :src="previewUrl" alt="Preview of selected truss sketch" /><span>Local preview · not uploaded yet</span><button type="button" @click="selectedFile = null">Remove</button></div>
        <button style="margin-top: 12px;" class="button button-primary upload-submit" type="button" :disabled="!selectedFile || submitting" @click="submit"><span v-if="submitting" class="button-spinner"></span>{{ submitting ? 'Analysing sketch…' : 'Start analysis' }}<svg v-if="!submitting" viewBox="0 0 20 20" fill="none" aria-hidden="true"><path d="M4 10h12m-5-5 5 5-5 5" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" /></svg></button>
        <p class="credential-note"><svg viewBox="0 0 16 16" fill="none" aria-hidden="true"><rect x="3" y="7" width="10" height="7" rx="1.5" stroke="currentColor"/><path d="M5.5 7V5a2.5 2.5 0 0 1 5 0v2" stroke="currentColor"/></svg> Provider credentials stay on the backend.</p>
      </section>

      <section class="workflow-card card-surface">
        <div class="card-heading"><div><div class="eyebrow">A CONTROLLED WORKFLOW</div><h2>Evidence stays distinct</h2></div><span class="workflow-icon">⌁</span></div>
        <div class="workflow-step"><span class="step-number">01</span><div><strong>Visual evidence</strong><p>OpenCV reports candidate lines and endpoint clusters. These are not verified truss members.</p></div><span class="step-tag tag-vision">VISION</span></div>
        <div class="workflow-step"><span class="step-number">02</span><div><strong>AI interpretation</strong><p>The AI model interprets the sketch and proposes candidate joints, members, supports and loads for human review.</p></div><span class="step-tag tag-ai">AI</span></div>
        <div class="workflow-step"><span class="step-number">03</span><div><strong>Human review</strong><p>Correct a separate draft, check its units, then explicitly mark it reviewed before solver submission.</p></div><span class="step-tag tag-review">REVIEW</span></div>
        <div class="workflow-note"><span>i</span><p>Nothing is solved automatically from the AI proposal. Solver output describes only the geometry you explicitly reviewed and submitted.</p></div>
      </section>
    </div>
  </section>
</template>
