<script setup>
import { onMounted, onBeforeUnmount, ref } from 'vue'

const props = defineProps({
  title:        { type: String, default: 'Confirm' },
  message:      { type: String, default: '' },
  confirmLabel: { type: String, default: 'Confirm' },
  cancelLabel:  { type: String, default: 'Cancel' },
  variant:      { type: String, default: 'default' }, // 'default' | 'danger'
})

const emit = defineEmits(['confirm', 'cancel'])

const confirmBtnRef = ref(null)

function handleKeydown(e) {
  if (e.key === 'Escape')  emit('cancel')
  if (e.key === 'Enter')   emit('confirm')
}

onMounted(() => {
  window.addEventListener('keydown', handleKeydown)
  // Auto-focus confirm button so Enter works immediately
  confirmBtnRef.value?.focus()
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', handleKeydown)
})
</script>

<template>
  <!-- Backdrop -->
  <div class="cdialog-backdrop" role="dialog" aria-modal="true" @mousedown.self="emit('cancel')">
    <div class="cdialog-panel">
      <h2 class="cdialog-title">{{ title }}</h2>
      <p v-if="message" class="cdialog-message">{{ message }}</p>
      <div class="cdialog-actions">
        <button class="cdialog-btn cdialog-cancel" type="button" @click="emit('cancel')">
          {{ cancelLabel }}
        </button>
        <button
          ref="confirmBtnRef"
          class="cdialog-btn cdialog-confirm"
          :class="{ 'cdialog-confirm--danger': variant === 'danger' }"
          type="button"
          @click="emit('confirm')"
        >
          {{ confirmLabel }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.cdialog-backdrop {
  position: fixed;
  inset: 0;
  z-index: 9000;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(15, 23, 42, 0.4);
  backdrop-filter: blur(2px);
}

.cdialog-panel {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-lg);
  padding: var(--sp-6);
  min-width: 320px;
  max-width: 440px;
  width: 90%;
}

.cdialog-title {
  font-size: var(--text-md);
  font-weight: var(--weight-semibold);
  color: var(--color-text-primary);
  margin: 0 0 var(--sp-2);
}

.cdialog-message {
  font-size: var(--text-base);
  color: var(--color-text-secondary);
  line-height: 1.55;
  margin: 0 0 var(--sp-5);
}

.cdialog-actions {
  display: flex;
  gap: var(--sp-2);
  justify-content: flex-end;
}

.cdialog-btn {
  display: inline-flex;
  align-items: center;
  padding: 6px 16px;
  font-size: var(--text-base);
  font-weight: var(--weight-medium);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: background var(--transition-base), border-color var(--transition-base);
}

.cdialog-cancel {
  background: var(--color-neutral);
  color: var(--color-text-secondary);
  border: 1px solid var(--color-border-strong);
}
.cdialog-cancel:hover {
  background: var(--color-neutral-hover);
  color: var(--color-text-primary);
}

.cdialog-confirm {
  background: var(--color-accent);
  color: #fff;
  border: 1px solid transparent;
}
.cdialog-confirm:hover {
  background: var(--color-accent-hover);
}
.cdialog-confirm:focus-visible {
  outline: 2px solid var(--color-accent);
  outline-offset: 2px;
}

.cdialog-confirm--danger {
  background: var(--color-danger);
}
.cdialog-confirm--danger:hover {
  background: var(--color-danger-hover);
}
</style>

