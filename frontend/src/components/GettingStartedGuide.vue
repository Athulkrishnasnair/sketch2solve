<script setup>
import { computed, ref } from 'vue'

const emit = defineEmits(['close', 'finish'])

const currentStep = ref(0)

const steps = [
  {
    stepNumber: 1,
    title: 'Create a New Analysis',
    subtitle: 'Start with a clean project',
    badge: 'Step 1 of 6',
    summary:
      'Click "+ New analysis" in the sidebar navigation or on your dashboard. This creates a dedicated session for your truss project.',
    detail:
      'Each analysis tracks your raw input, candidate geometry, engineering review modifications, and deterministic solver results.',
  },
  {
    stepNumber: 2,
    title: 'Upload a Sketch or Describe with AI',
    subtitle: 'From pencil drawing to digital CAD',
    badge: 'Step 2 of 6',
    summary:
      'Drop a photo or scan of a hand-drawn truss sketch (JPEG, PNG, WebP up to 10 MB) onto the intake area.',
    detail:
      'Alternatively, use Natural Language Design to describe structures in plain text (e.g. "Warren truss with 4 panels, 10 m span and 3 m height") without drawing.',
  },
  {
    stepNumber: 3,
    title: 'Review & Correct Geometry',
    subtitle: 'Verify joints and members on canvas',
    badge: 'Step 3 of 6',
    summary:
      'Computer vision and AI models detect candidate joints and members from your sketch. Click "Edit geometry" to launch the CAD Truss Editor.',
    detail:
      'Drag joints to adjust vertex positions, draw new members, or use the Inspector panel for numeric precision coordinate adjustments.',
  },
  {
    stepNumber: 4,
    title: 'Add Supports & External Loads',
    subtitle: 'Set boundary conditions and forces',
    badge: 'Step 4 of 6',
    summary:
      'Select the Pin tool to fix horizontal and vertical movement, or the Roller tool for single-direction constraints.',
    detail:
      'Use the Load tool to apply concentrated nodal loads in kN, specify force directions, and confirm 3 independent reaction constraints for static stability.',
  },
  {
    stepNumber: 5,
    title: 'Validate & Run the Solver',
    subtitle: 'Deterministic matrix solution',
    badge: 'Step 5 of 6',
    summary:
      'The validation engine continuously verifies determinacy: 2j = m + r (where j = joints, m = members, r = reaction constraints).',
    detail:
      'Click "Solve Truss" in the top action bar. The method-of-joints solver computes equilibrium equations with residual verification below 1e-9 tolerance.',
  },
  {
    stepNumber: 6,
    title: 'Understand Results & Export',
    subtitle: 'Inspect forces and export deliverables',
    badge: 'Step 6 of 6',
    summary:
      'Solved results appear directly on-canvas: tension members in blue, compression members in red, and zero-force members in gray.',
    detail:
      'Open the Export menu to download high-resolution 200 DPI PNG diagrams, complete JSON models, or CSV schedules of member axial forces and reactions.',
  },
]

const currentStepData = computed(() => steps[currentStep.value])
const isFirst = computed(() => currentStep.value === 0)
const isLast = computed(() => currentStep.value === steps.length - 1)

function handleNext() {
  if (isLast.value) {
    emit('finish')
  } else {
    currentStep.value += 1
  }
}

function handlePrev() {
  if (!isFirst.value) {
    currentStep.value -= 1
  }
}

function jumpTo(idx) {
  currentStep.value = idx
}
</script>

<template>
  <div class="guide-overlay" @click.self="emit('close')">
    <div
      class="guide-card modal-animate"
      role="dialog"
      aria-modal="true"
      aria-labelledby="guide-step-title"
    >
      <!-- Header -->
      <div class="guide-header">
        <div class="guide-header-brand">
          <img src="/logo.png" alt="Sketch2Solve Logo" class="guide-logo" />
          <div>
            <h3 class="guide-app-name">Sketch2Solve</h3>
            <span class="guide-caption">Getting Started Guide</span>
          </div>
        </div>
        <button
          type="button"
          class="btn-close-guide"
          aria-label="Close Getting Started guide"
          @click="emit('close')"
        >
          ✕
        </button>
      </div>

      <!-- Step Progress Dots -->
      <div class="guide-dots-row">
        <button
          v-for="(st, idx) in steps"
          :key="st.stepNumber"
          type="button"
          class="step-dot"
          :class="{ active: idx === currentStep, completed: idx < currentStep }"
          :aria-label="`Go to step ${idx + 1}: ${st.title}`"
          @click="jumpTo(idx)"
        >
          {{ idx + 1 }}
        </button>
      </div>

      <!-- Body -->
      <div class="guide-body">
        <div class="step-badge-row">
          <span class="step-badge">{{ currentStepData.badge }}</span>
        </div>
        <h2 id="guide-step-title" class="step-title">
          {{ currentStepData.title }}
        </h2>
        <h4 class="step-subtitle">{{ currentStepData.subtitle }}</h4>
        <p class="step-summary">{{ currentStepData.summary }}</p>
        <div class="step-detail-card">
          <span class="detail-icon" aria-hidden="true">💡</span>
          <p class="step-detail-text">{{ currentStepData.detail }}</p>
        </div>
      </div>

      <!-- Footer -->
      <div class="guide-footer">
        <button
          type="button"
          class="btn-guide-back"
          :disabled="isFirst"
          @click="handlePrev"
        >
          ← Back
        </button>
        <div class="footer-right">
          <button
            type="button"
            class="btn-guide-dismiss"
            @click="emit('close')"
          >
            Dismiss
          </button>
          <button
            type="button"
            class="btn-guide-primary"
            @click="handleNext"
          >
            {{ isLast ? 'Get Started' : 'Next Step →' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.guide-overlay {
  position: fixed;
  inset: 0;
  background: rgba(37, 43, 44, 0.45);
  backdrop-filter: blur(4px);
  display: grid;
  place-items: center;
  z-index: 9500;
  padding: 16px;
}

.guide-card {
  width: 100%;
  max-width: 520px;
  background: #fffef8;
  border: 1px solid #e3e8e4;
  border-radius: 18px;
  box-shadow: 0 24px 50px rgba(31, 55, 44, 0.18), 0 4px 14px rgba(31, 55, 44, 0.06);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.guide-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px 12px;
  border-bottom: 1px solid #edf0ed;
}

.guide-header-brand {
  display: flex;
  align-items: center;
  gap: 10px;
}

.guide-logo {
  width: 28px;
  height: 28px;
  object-fit: contain;
  border-radius: 6px;
}

.guide-app-name {
  margin: 0;
  font-family: var(--heading, sans-serif);
  font-size: 14px;
  font-weight: 700;
  color: #252b2c;
  line-height: 1.2;
}

.guide-caption {
  font-size: 10px;
  color: #68736f;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-family: var(--mono, monospace);
}

.btn-close-guide {
  border: none;
  background: transparent;
  width: 28px;
  height: 28px;
  border-radius: 6px;
  display: grid;
  place-items: center;
  color: #68736f;
  font-size: 14px;
  cursor: pointer;
  transition: background 0.15s ease, color 0.15s ease;
}

.btn-close-guide:hover {
  background: #f0f4f1;
  color: #252b2c;
}

.guide-dots-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px 20px 6px;
}

.step-dot {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  border: 1px solid #dce5e0;
  background: #ffffff;
  color: #68736f;
  font-family: var(--mono, monospace);
  font-size: 10px;
  font-weight: 700;
  display: grid;
  place-items: center;
  cursor: pointer;
  transition: all 0.15s ease;
  padding: 0;
}

.step-dot:hover {
  border-color: #0284c7;
  color: #0284c7;
}

.step-dot.active {
  background: #0284c7;
  border-color: #0284c7;
  color: #ffffff;
  transform: scale(1.1);
  box-shadow: 0 0 0 3px rgba(2, 132, 199, 0.18);
}

.step-dot.completed {
  background: #eef7f3;
  border-color: #57a186;
  color: #388780;
}

.guide-body {
  padding: 16px 24px 20px;
  display: flex;
  flex-direction: column;
  min-height: 200px;
}

.step-badge-row {
  margin-bottom: 6px;
}

.step-badge {
  font-size: 9px;
  font-family: var(--mono, monospace);
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.6px;
  color: #0369a1;
  background: #e0f2fe;
  padding: 2px 7px;
  border-radius: 4px;
}

.step-title {
  margin: 0 0 4px;
  font-family: var(--heading, sans-serif);
  font-size: 18px;
  font-weight: 700;
  color: #252b2c;
  letter-spacing: -0.3px;
}

.step-subtitle {
  margin: 0 0 10px;
  font-size: 11px;
  font-weight: 600;
  color: #0284c7;
}

.step-summary {
  margin: 0 0 12px;
  font-size: 13px;
  line-height: 1.55;
  color: #334155;
}

.step-detail-card {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  background: #f8faf8;
  border: 1px solid #e3ece6;
  border-radius: 8px;
  padding: 10px 12px;
  margin-top: auto;
}

.detail-icon {
  font-size: 14px;
  flex-shrink: 0;
  margin-top: 1px;
}

.step-detail-text {
  margin: 0;
  font-size: 11px;
  line-height: 1.5;
  color: #55625d;
}

.guide-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px 16px;
  border-top: 1px solid #edf0ed;
}

.btn-guide-back {
  background: transparent;
  border: 1px solid #dfe5e1;
  color: #54615d;
  font-size: 11px;
  font-weight: 600;
  padding: 7px 14px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-guide-back:hover:not(:disabled) {
  background: #f8faf8;
  color: #252b2c;
}

.btn-guide-back:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

.footer-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.btn-guide-dismiss {
  background: transparent;
  border: none;
  color: #68736f;
  font-size: 11px;
  font-weight: 600;
  padding: 7px 10px;
  cursor: pointer;
}

.btn-guide-dismiss:hover {
  color: #252b2c;
}

.btn-guide-primary {
  background: #252b2c;
  color: #fffef8;
  border: 1px solid transparent;
  font-size: 11px;
  font-weight: 700;
  padding: 8px 18px;
  border-radius: 7px;
  cursor: pointer;
  transition: background-color 0.15s ease;
}

.btn-guide-primary:hover {
  background: #1d5559;
}

@keyframes modal-pop {
  from {
    opacity: 0;
    transform: scale(0.96) translateY(6px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

.modal-animate {
  animation: modal-pop 0.18s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}
</style>

