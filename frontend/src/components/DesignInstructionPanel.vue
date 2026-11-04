<script setup>
import { computed, ref, watch } from 'vue'
import {
  Sparkles,
  Send,
  Loader2,
  AlertCircle,
  RefreshCw,
  HelpCircle,
  Layers,
  ArrowRight,
  Sliders,
  CheckCircle2,
} from 'lucide-vue-next'
import DesignProposalCard from './DesignProposalCard.vue'

const props = defineProps({
  analysisId: {
    type: String,
    default: '',
  },
  modelRevision: {
    type: Number,
    default: 1,
  },
  selectedElement: {
    type: Object,
    default: null,
  },
  isDirty: {
    type: Boolean,
    default: false,
  },
  proposal: {
    type: Object,
    default: null,
  },
  busy: {
    type: Boolean,
    default: false,
  },
  error: {
    type: String,
    default: '',
  },
  compact: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['submit', 'apply', 'reject', 'clear-error'])

const message = ref('')
const selectedIntent = ref('auto') // 'auto' | 'create' | 'modify' | 'explain'
const textareaRef = ref(null)

const placeholderText = computed(() => {
  if (props.selectedElement?.type === 'node') {
    return `Instruct modification for joint ${props.selectedElement.id} (e.g. "Move J${props.selectedElement.id} upwards by 0.5m", "Add pin support")...`
  }
  if (props.selectedElement?.type === 'member') {
    return `Instruct modification for member ${props.selectedElement.id} (e.g. "Remove member ${props.selectedElement.id}", "Explain member force")...`
  }
  if (selectedIntent.value === 'create') {
    return 'Describe the truss to create (e.g. "Create a triangular truss with 6 m span and 3 m height", "Warren truss with 4 panels")...'
  }
  if (selectedIntent.value === 'explain') {
    return 'Ask an engineering question (e.g. "Why is this structure unstable?", "Explain support reactions and determinacy")...'
  }
  return 'Describe structural change or question (e.g. "Add a diagonal between J1 and J3", "Move J2 up 0.5m", "Why unstable?")...'
})

const quickChips = computed(() => {
  if (props.selectedElement?.type === 'node') {
    const jId = props.selectedElement.id
    return [
      `Move ${jId} up by 0.5 m`,
      `Add pin support at ${jId}`,
      `Add roller support at ${jId}`,
      `Apply 10 kN downward load at ${jId}`,
    ]
  }
  if (props.selectedElement?.type === 'member') {
    const mId = props.selectedElement.id
    return [
      `Remove member ${mId}`,
      `Explain force in member ${mId}`,
    ]
  }
  if (selectedIntent.value === 'create') {
    return [
      'Create a triangular truss with 6 m span and 3 m height',
      'Warren truss with 4 panels and 10 m span',
      'Simple roof truss with pin and roller',
      'Triangular truss with 10 kN downward load at apex',
    ]
  }
  if (selectedIntent.value === 'explain') {
    return [
      'Why is this structure unstable?',
      'Explain degree of determinacy',
      'Explain support reactions',
      'Which members are in tension or compression?',
    ]
  }
  return [
    'Add a diagonal between J1 and J3',
    'Move J2 up by 0.5 m',
    'Add 10 kN downward load at top',
    'Why is this structure unstable?',
  ]
})

function handleKeydown(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    handleSubmit()
  }
}

function selectChip(text) {
  message.value = text
  handleSubmit()
}

function handleClarification({ question, answer }) {
  message.value = `${question.prompt}: ${answer}`
  handleSubmit()
}

function handleSubmit() {
  const text = message.value.trim()
  if (!text || props.busy) return
  emit('submit', {
    message: text,
    intent: selectedIntent.value,
  })
}

function handleClear() {
  message.value = ''
  emit('clear-error')
}
</script>

<template>
  <div class="design-instruction-panel" :class="{ compact }">
    <!-- Scrollable content area: Context bar, Active proposal, Error banner, Suggestions -->
    <div class="panel-content-area">
      <!-- Context Bar -->
      <div class="panel-context-bar">
        <div class="context-left">
          <span class="context-tag" :title="`Model revision ${modelRevision}`">
            <Layers :size="12" /> Rev {{ modelRevision }}
          </span>
          <span v-if="selectedElement" class="context-tag selected-tag">
            Selected: <strong>{{ selectedElement.id }}</strong> ({{ selectedElement.type }})
          </span>
          <span v-if="isDirty" class="context-tag dirty-tag" title="Canvas has unsaved changes that will be used as base context">
            Unsaved canvas edits included
          </span>
        </div>

        <!-- Intent Mode Pills -->
        <div class="intent-selector" role="radiogroup" aria-label="Design Intent">
          <button
            type="button"
            class="intent-btn"
            :class="{ active: selectedIntent === 'auto' }"
            @click="selectedIntent = 'auto'"
          >
            Auto
          </button>
          <button
            type="button"
            class="intent-btn"
            :class="{ active: selectedIntent === 'create' }"
            @click="selectedIntent = 'create'"
          >
            Create
          </button>
          <button
            type="button"
            class="intent-btn"
            :class="{ active: selectedIntent === 'modify' }"
            @click="selectedIntent = 'modify'"
          >
            Modify
          </button>
          <button
            type="button"
            class="intent-btn"
            :class="{ active: selectedIntent === 'explain' }"
            @click="selectedIntent = 'explain'"
          >
            Explain
          </button>
        </div>
      </div>

      <!-- Error Banner -->
      <div v-if="error" class="error-banner" role="alert">
        <AlertCircle :size="14" class="error-icon" />
        <div class="error-body">
          <strong>Design Service Notice</strong>
          <p>{{ error }}</p>
        </div>
        <button type="button" class="error-dismiss" aria-label="Dismiss error" @click="handleClear">✕</button>
      </div>

      <!-- Active Proposal Display -->
      <div v-if="proposal" class="proposal-container">
        <DesignProposalCard
          :proposal="proposal"
          :compact="compact"
          :is-busy="busy"
          @apply="emit('apply', $event)"
          @reject="emit('reject', $event)"
          @select-clarification="handleClarification"
        />
      </div>

      <!-- Suggested Quick Chips -->
      <div v-if="!proposal && quickChips.length > 0" class="chips-row">
        <button
          v-for="(chip, idx) in quickChips"
          :key="idx"
          type="button"
          class="prompt-chip"
          :disabled="busy"
          @click="selectChip(chip)"
        >
          {{ chip }}
        </button>
      </div>
    </div>

    <!-- Input Area (anchored at bottom) -->
    <div class="input-container">
      <textarea
        ref="textareaRef"
        v-model="message"
        class="design-textarea"
        :placeholder="placeholderText"
        rows="2"
        :disabled="busy"
        @keydown="handleKeydown"
      ></textarea>

      <div class="input-actions">
        <span class="keyboard-hint">Enter ↵ to submit · Shift+Enter for newline</span>
        <button
          class="btn-submit"
          type="button"
          :disabled="!message.trim() || busy"
          @click="handleSubmit"
        >
          <Loader2 v-if="busy" :size="13" class="spin-icon" />
          <Send v-else :size="13" />
          <span>{{ busy ? 'Analyzing...' : 'Generate' }}</span>
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.design-instruction-panel {
  display: flex;
  flex-direction: column;
  gap: 10px;
  background: #faf8f5;
  border: 1px solid #eae5d7;
  border-radius: 12px;
  padding: 12px 14px;
  box-shadow: 0 3px 12px rgba(41, 42, 40, 0.03);
  box-sizing: border-box;
}

.design-instruction-panel.compact {
  height: 100%;
  max-height: 100%;
  padding: 10px;
  gap: 8px;
  border: none;
  border-radius: 0;
  box-shadow: none;
  background: transparent;
  overflow: hidden;
}

.panel-content-area {
  display: flex;
  flex-direction: column;
  gap: 8px;
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
  padding-right: 2px;
}

.panel-content-area::-webkit-scrollbar {
  width: 5px;
}
.panel-content-area::-webkit-scrollbar-track {
  background: transparent;
}
.panel-content-area::-webkit-scrollbar-thumb {
  background: #dcd7c9;
  border-radius: 4px;
}
.panel-content-area::-webkit-scrollbar-thumb:hover {
  background: #c5bfae;
}

/* Context Bar */
.panel-context-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  flex-wrap: wrap;
}

.context-left {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.context-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font: 9px var(--mono, monospace);
  color: #6d7065;
  background: #ede9dc;
  padding: 2px 6px;
  border-radius: 4px;
}

.context-tag.selected-tag {
  background: #e0f2fe;
  color: #0369a1;
  border: 1px solid #bae6fd;
}

.context-tag.dirty-tag {
  background: #fef3c7;
  color: #b45309;
  border: 1px solid #fde68a;
}

/* Intent Selector */
.intent-selector {
  display: inline-flex;
  background: #ede9dc;
  border-radius: 6px;
  padding: 2px;
  gap: 2px;
}

.intent-btn {
  border: none;
  background: transparent;
  color: #63665c;
  font-size: 10px;
  font-weight: 600;
  padding: 2px 7px;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.intent-btn:hover {
  color: #292a28;
}

.intent-btn.active {
  background: #fff;
  color: #292a28;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

/* Input Area */
.input-container {
  display: flex;
  flex-direction: column;
  background: #fff;
  border: 1px solid #dcd7c9;
  border-radius: 8px;
  overflow: hidden;
  transition: border-color 0.15s ease;
}

.input-container:focus-within {
  border-color: #0284c7;
  box-shadow: 0 0 0 2px rgba(2, 132, 199, 0.15);
}

.design-textarea {
  width: 100%;
  border: none;
  outline: none;
  resize: vertical;
  min-height: 48px;
  padding: 8px 10px;
  font-family: inherit;
  font-size: 12px;
  color: #292a28;
  line-height: 1.45;
  background: transparent;
}

.design-textarea::placeholder {
  color: #9ea094;
}

.input-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 5px 10px;
  background: #faf9f6;
  border-top: 1px solid #f0ece1;
}

.keyboard-hint {
  font-size: 9px;
  color: #9ea094;
}

.btn-submit {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 4px 10px;
  border-radius: 5px;
  border: 1px solid #292a28;
  background: #292a28;
  color: #fff;
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s ease;
}

.btn-submit:hover:not(:disabled) {
  background: #42453e;
}

.btn-submit:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.spin-icon {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  100% { transform: rotate(360deg); }
}

/* Prompt Chips */
.chips-row {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}

.prompt-chip {
  background: #fff;
  border: 1px solid #e0dcd0;
  color: #55584e;
  border-radius: 999px;
  padding: 3px 8px;
  font-size: 10px;
  cursor: pointer;
  transition: all 0.15s ease;
  white-space: nowrap;
}

.prompt-chip:hover:not(:disabled) {
  background: #f4efe4;
  border-color: #c9c4b7;
  color: #292a28;
}

/* Error Banner */
.error-banner {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 8px;
  padding: 8px 10px;
  color: #991b1b;
}

.error-icon {
  flex-shrink: 0;
  margin-top: 2px;
}

.error-body {
  flex: 1;
  font-size: 11px;
}

.error-body strong {
  display: block;
  font-size: 11px;
  margin-bottom: 2px;
}

.error-body p {
  margin: 0;
  color: #b91c1c;
}

.error-dismiss {
  border: none;
  background: transparent;
  color: #991b1b;
  font-size: 12px;
  cursor: pointer;
  padding: 0 4px;
}

/* Proposal Container */
.proposal-container {
  margin-top: 2px;
}
</style>
