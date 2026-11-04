<script setup>
import { nextTick, onMounted, ref } from 'vue'

const props = defineProps({
  currentName: {
    type: String,
    default: '',
  },
  isEditing: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['save', 'close'])

const inputName = ref(props.currentName || '')
const errorMessage = ref('')
const inputRef = ref(null)

onMounted(() => {
  nextTick(() => {
    if (inputRef.value) {
      inputRef.value.focus()
      if (inputName.value) {
        inputRef.value.select()
      }
    }
  })
})

function handleSave() {
  const trimmed = inputName.value.trim()
  if (!trimmed) {
    errorMessage.value = 'Please enter your name or an engineer alias.'
    return
  }
  localStorage.setItem('sketch2solve_username', trimmed)
  emit('save', trimmed)
}

function handleKeyDown(e) {
  if (e.key === 'Enter') {
    e.preventDefault()
    handleSave()
  } else if (e.key === 'Escape' && props.isEditing) {
    emit('close')
  }
}
</script>

<template>
  <div class="onboarding-overlay" @click.self="isEditing ? emit('close') : null">
    <div
      class="onboarding-card modal-animate"
      role="dialog"
      aria-modal="true"
      aria-labelledby="onboarding-title"
    >
      <div class="onboarding-header">
        <div class="brand-avatar-wrapper">
          <img src="/logo.png" alt="Sketch2Solve Logo" class="onboarding-logo" />
        </div>
        <h2 id="onboarding-title" class="onboarding-title">
          {{ isEditing ? 'Edit Profile Name' : 'Welcome to Sketch2Solve' }}
        </h2>
        <p class="onboarding-subtitle">
          {{
            isEditing
              ? 'Update the name displayed on your engineering reports and workspace.'
              : 'What should we call you?'
          }}
        </p>
      </div>

      <form class="onboarding-form" @submit.prevent="handleSave">
        <div class="input-group">
          <label for="engineer-name-input" class="input-label">Your Name or Engineering Callout</label>
          <input
            id="engineer-name-input"
            ref="inputRef"
            v-model="inputName"
            type="text"
            class="name-input"
            placeholder="e.g. Jane Doe, PE"
            maxlength="50"
            autocomplete="name"
            @keydown="handleKeyDown"
            @input="errorMessage = ''"
          />
          <span v-if="errorMessage" class="error-text" role="alert">{{ errorMessage }}</span>
        </div>

        <div class="onboarding-actions">
          <button
            v-if="isEditing"
            type="button"
            class="btn-secondary"
            @click="emit('close')"
          >
            Cancel
          </button>
          <button
            type="submit"
            class="btn-primary"
            :disabled="!inputName.trim()"
          >
            {{ isEditing ? 'Save Name' : 'Continue' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<style scoped>
.onboarding-overlay {
  position: fixed;
  inset: 0;
  background: rgba(37, 43, 44, 0.45);
  backdrop-filter: blur(4px);
  display: grid;
  place-items: center;
  z-index: 9500;
  padding: 16px;
}

.onboarding-card {
  width: 100%;
  max-width: 440px;
  background: #fffef8;
  border: 1px solid #e3e8e4;
  border-radius: 18px;
  padding: 32px 28px;
  box-shadow: 0 20px 45px rgba(31, 55, 44, 0.16), 0 4px 12px rgba(31, 55, 44, 0.06);
}

.onboarding-header {
  text-align: center;
  margin-bottom: 24px;
}

.brand-avatar-wrapper {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 68px;
  height: 68px;
  border-radius: 18px;
  background: #252b2c;
  border: 2px solid #e9e5d7;
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.08);
  margin-bottom: 16px;
  overflow: hidden;
}

.onboarding-logo {
  width: 52px;
  height: 52px;
  object-fit: contain;
}

.onboarding-title {
  font-family: var(--heading, sans-serif);
  font-size: 20px;
  font-weight: 700;
  color: #252b2c;
  margin: 0 0 6px;
  letter-spacing: -0.4px;
}

.onboarding-subtitle {
  font-size: 13px;
  line-height: 1.5;
  color: #68736f;
  margin: 0;
}

.onboarding-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.input-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
  text-align: left;
}

.input-label {
  font-size: 11px;
  font-weight: 600;
  color: #485650;
  letter-spacing: 0.3px;
}

.name-input {
  width: 100%;
  min-height: 42px;
  padding: 0 14px;
  border: 1px solid #dfe5e1;
  border-radius: 8px;
  font-size: 13px;
  font-family: inherit;
  background: #ffffff;
  color: #252b2c;
  outline: none;
  box-sizing: border-box;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

.name-input:focus {
  border-color: #0284c7;
  box-shadow: 0 0 0 3px rgba(2, 132, 199, 0.15);
}

.error-text {
  font-size: 11px;
  color: #dc2626;
  margin-top: 2px;
}

.onboarding-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 4px;
}

.btn-secondary {
  background: #ffffff;
  border: 1px solid #dfe5e1;
  color: #54615d;
  font-size: 12px;
  font-weight: 600;
  padding: 8px 14px;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.15s ease;
}

.btn-secondary:hover {
  background: #f8faf8;
}

.btn-primary {
  background: #252b2c;
  color: #fffef8;
  border: 1px solid transparent;
  font-size: 12px;
  font-weight: 700;
  padding: 9px 22px;
  border-radius: 8px;
  cursor: pointer;
  transition: background-color 0.15s ease, transform 0.1s ease;
}

.btn-primary:hover:not(:disabled) {
  background: #1d5559;
}

.btn-primary:active:not(:disabled) {
  transform: scale(0.98);
}

.btn-primary:disabled {
  opacity: 0.45;
  cursor: not-allowed;
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

