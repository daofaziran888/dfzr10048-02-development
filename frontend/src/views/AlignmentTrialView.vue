<template>
  <section class="page trial-page" data-testid="alignment-trial-view">
    <header class="page-head">
      <div>
        <h2>字幕受影响范围试算</h2>
        <p class="page-desc">
          按原片毫秒与原片时间排列受影响字幕；服务端保留标注原文、计算偏移并合并确认期间到达的更正。
        </p>
      </div>
      <div class="page-actions">
        <RouterLink class="btn" to="/subtitle_align">返回字幕对齐</RouterLink>
        <button class="btn" type="button" data-testid="reset-trial" @click="resetScenario">重置题设</button>
        <button class="btn" type="button" data-testid="refresh-trial" @click="reload">刷新试算</button>
        <button
          class="btn warning"
          type="button"
          data-testid="arrive-b-correction"
          :disabled="bArrived || busy"
          @click="arriveB"
        >
          {{ bArrived ? '乙的 80ms 更正已送达' : '模拟乙的 80ms 更正送达' }}
        </button>
      </div>
    </header>

    <div v-if="errorMessage" class="inline-error" data-testid="trial-error">{{ errorMessage }}</div>
    <div v-if="message" class="inline-success" data-testid="trial-message">{{ message }}</div>

    <template v-if="preview">
      <section class="context-grid">
        <article class="info-card mark-card" data-testid="trial-mark-4000">
          <h3>原片标注 · 4000ms</h3>
          <dl>
            <div><dt>标注编号</dt><dd>{{ String(preview.mark['标注点编号'] ?? '') }}</dd></div>
            <div><dt>标注毫秒</dt><dd data-testid="mark-ms">{{ String(preview.mark['标注毫秒'] ?? preview.boundary_ms) }}ms</dd></div>
            <div><dt>标注内容</dt><dd>{{ preview.annotation_text }}</dd></div>
            <div class="full"><dt>批注原文</dt><dd class="comment-original" data-testid="annotation-original">{{ preview.annotation_comment_original }}</dd></div>
          </dl>
        </article>

        <article class="info-card boundary-card" data-testid="boundary-assignment">
          <h3>交界归属与计算基准</h3>
          <p><strong>计算基准：</strong>原片毫秒（original_film_milliseconds）</p>
          <p>{{ preview.calculation_note }}</p>
          <p data-testid="boundary-rule">{{ preview.boundary_assignment.rule }}</p>
          <p>
            4000ms 标注唯一归入：
            <strong data-testid="assigned-interval">{{ preview.boundary_assignment.assigned_interval_id }}</strong>
            ；命中区间数 {{ preview.boundary_assignment.match_count }}，不重复计算。
          </p>
          <p>服务端修订版本：<strong data-testid="trial-revision">{{ preview.revision }}</strong></p>
        </article>
      </section>

      <ol class="story-steps" data-testid="story-steps">
        <li><strong>1.</strong> 第 5、6 行按原片毫秒命中区间，试算为双双后移 120ms。</li>
        <li><strong>2.</strong> 甲在 R1 打开确认；可先点“模拟乙的 80ms 更正送达”。</li>
        <li><strong>3.</strong> 甲仍按 R1 提交，服务端保留两笔来源并重算实际值。</li>
        <li><strong>4.</strong> 第 6 行可单独生效；第 5 行进入对齐详情判断是否再审。</li>
      </ol>

      <div class="trial-batch-bar">
        <label v-for="line in preview.rows" :key="line.line_number" class="check-pill">
          <input v-model="selectedLines" type="checkbox" :value="line.line_number" :data-testid="`select-line-${line.line_number}`" />
          第 {{ line.line_number }} 行
        </label>
        <button class="btn primary" type="button" data-testid="confirm-selected" :disabled="busy" @click="confirmSelected">
          甲提交选中行确认
        </button>
        <span class="hint">确认单按甲最初打开的 R1 试算版本提交；每行也可单独提交，第 6 行不依赖第 5 行结果。</span>
      </div>

      <table class="data-table trial-table" data-testid="trial-table">
        <thead>
          <tr>
            <th>原片时间/行号</th>
            <th>字幕与原标注区间</th>
            <th>变动前（原发行）</th>
            <th>甲看到的 +120ms 试算</th>
            <th>服务端当前结果</th>
            <th>变化来源</th>
            <th>确认与详情</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="line in preview.rows"
            :key="line.line_number"
            :data-testid="`trial-row-${line.line_number}`"
            :data-adopted="line.adopted"
            :data-needs-review="line.needs_review"
            class="trial-row"
          >
            <td>
              <strong>第 {{ line.line_number }} 行</strong>
              <div class="muted">{{ line.sort_ms }}ms 起</div>
            </td>
            <td class="text-cell">
              <p>{{ line.text }}</p>
              <span class="tag">{{ line.interval?.interval_id }} · {{ line.interval?.label }}</span>
              <span v-if="line.interval?.contained_by_original_interval" class="tag ok">仍在原标注区间</span>
            </td>
            <td>
              <div data-testid="before-values">
                <span data-testid="before-start">{{ line.before_start_ms }}</span>–<span data-testid="before-end">{{ line.before_end_ms }}</span>ms
              </div>
              <span class="muted">偏移 0ms</span>
            </td>
            <td>
              <div data-testid="trial-values">
                <span data-testid="trial-start">{{ line.trial_start_ms }}</span>–<span data-testid="trial-end">{{ line.trial_end_ms }}</span>ms
              </div>
              <span class="delta positive">后移 {{ line.trial_delta_ms }}ms</span>
            </td>
            <td>
              <div data-testid="server-values">
                <strong data-testid="after-start">{{ line.server_start_ms }}</strong>–<strong data-testid="after-end">{{ line.server_end_ms }}</strong>ms
              </div>
              <span :class="['delta', line.server_delta_ms < line.trial_delta_ms ? 'merged' : 'positive']" data-testid="net-delta">
                净偏移 {{ line.server_delta_ms >= 0 ? '+' : '' }}{{ line.server_delta_ms }}ms
              </span>
              <div v-if="line.has_late_correction" class="warning-text" data-testid="late-correction-flag">乙的更正刚到，已保留为独立来源</div>
            </td>
            <td>
              <ul class="source-list">
                <li v-for="source in line.sources" :key="source.adjustment_id" :data-testid="`source-${line.line_number}-${source.source_type}`">
                  <span class="source-dot" />
                  {{ source.source_label ?? source.label }}
                  <strong :class="(source.delta_ms ?? 0) >= 0 ? 'delta positive' : 'delta negative'">
                    {{ (source.delta_ms ?? 0) >= 0 ? '+' : '' }}{{ source.delta_ms }}ms
                  </strong>
                </li>
              </ul>
            </td>
            <td class="actions-cell">
              <span :class="['status-pill', line.needs_review ? 'review' : line.adopted ? 'done' : 'pending']" data-testid="row-result-status">
                {{ line.needs_review ? '已合并 · 需再审' : line.adopted ? '已生效' : line.status }}
              </span>
              <button
                class="link"
                type="button"
                :data-testid="`confirm-line-${line.line_number}`"
                :disabled="busy || line.adopted"
                @click="confirmOne(line.line_number)"
              >
                {{ line.adopted ? '已确认' : `甲提交第 ${line.line_number} 行确认` }}
              </button>
              <RouterLink class="link" :to="`/subtitle-align/line/${line.line_number}`" :data-testid="`open-detail-${line.line_number}`">
                打开对齐详情
              </RouterLink>
            </td>
          </tr>
        </tbody>
      </table>
    </template>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'

import {
  arriveBCorrection,
  confirmTrial,
  getTrialPreview,
  resetTrial,
  type TrialPreview,
} from '@/api/alignment-trial'

const route = useRoute()
const preview = ref<TrialPreview | null>(null)
const markRef = computed(() => {
  const value = route.query.markRef ?? route.query.mark_ref
  return Array.isArray(value) ? value[0] : value
})
const selectedLines = ref<number[]>([5, 6])
const busy = ref(false)
const errorMessage = ref('')
const message = ref('')
const bArrived = computed(() => Boolean(preview.value && preview.value.revision > 1))

async function reload() {
  errorMessage.value = ''
  try {
    preview.value = await getTrialPreview({ markRef: markRef.value ? String(markRef.value) : undefined })
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '试算数据读取失败'
  }
}

async function arriveB() {
  busy.value = true
  errorMessage.value = ''
  message.value = ''
  try {
    const result = await arriveBCorrection()
    message.value = result.message
    await reload()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '乙的更正送达失败'
  } finally {
    busy.value = false
  }
}

async function confirmOne(lineNumber: number) {
  busy.value = true
  errorMessage.value = ''
  message.value = ''
  try {
    // 甲的表单在修订版 1 打开；即使乙的修订版 2 已到，也把打开版本交给服务端识别。
    const result = await confirmTrial({
      line_numbers: [lineNumber],
      reviewer: '甲',
      client_revision: 1,
    })
    if (!result.ok) throw new Error(result.message)
    message.value = result.message
    await reload()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '确认失败'
  } finally {
    busy.value = false
  }
}

async function confirmSelected() {
  if (!selectedLines.value.length) {
    errorMessage.value = '请先勾选至少一行'
    return
  }
  busy.value = true
  errorMessage.value = ''
  message.value = ''
  try {
    const result = await confirmTrial({
      line_numbers: selectedLines.value,
      reviewer: '甲',
      client_revision: 1,
    })
    if (!result.ok) throw new Error(result.message)
    message.value = result.message
    await reload()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '批量确认失败'
  } finally {
    busy.value = false
  }
}

async function resetScenario() {
  busy.value = true
  errorMessage.value = ''
  message.value = ''
  try {
    await resetTrial()
    selectedLines.value = [5, 6]
    message.value = '题设已重置：第 5、6 行恢复为待确认的 +120ms 试算'
    await reload()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '重置失败'
  } finally {
    busy.value = false
  }
}

onMounted(reload)
</script>

<style scoped>
.context-grid { display: grid; grid-template-columns: minmax(320px, 1.1fr) minmax(320px, .9fr); gap: 12px; margin: 12px 0; }
.info-card { background: #fff; border: 1px solid var(--border); border-radius: 8px; padding: 14px 16px; }
.info-card h3 { margin: 0 0 10px; font-size: 15px; }
.info-card dl { display: grid; grid-template-columns: 90px 1fr; gap: 8px 10px; margin: 0; }
.info-card .full { grid-column: 1 / -1; }
.info-card dt { color: var(--muted); font-size: 12px; }
.info-card dd { margin: 0; font-size: 13px; }
.comment-original { background: #fff7ed; border-left: 3px solid #f59e0b; padding: 8px 10px; border-radius: 4px; line-height: 1.7; }
.trial-batch-bar { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; background: #fff; border: 1px solid var(--border); border-radius: 8px; padding: 10px 12px; margin-bottom: 12px; }
.story-steps { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; padding: 0; margin: 0 0 12px; list-style: none; }
.story-steps li { background: #eef6ff; border: 1px solid #bfdbfe; border-radius: 8px; padding: 9px 10px; font-size: 12px; line-height: 1.6; }
.story-steps strong { color: var(--brand); margin-right: 4px; }
.check-pill { display: inline-flex; align-items: center; gap: 4px; font-size: 13px; }
.hint { color: var(--muted); font-size: 12px; }
.trial-table { background: #fff; }
.text-cell { min-width: 220px; }
.text-cell p { margin: 0 0 6px; line-height: 1.6; }
.tag { display: inline-block; margin: 2px 4px 2px 0; padding: 2px 7px; border-radius: 999px; background: #eef2ff; color: #3730a3; font-size: 12px; }
.tag.ok { background: #ecfdf5; color: #047857; }
.muted { color: var(--muted); font-size: 12px; }
.delta { display: inline-block; margin-top: 4px; font-size: 12px; font-weight: 600; }
.delta.positive { color: #b45309; }
.delta.negative { color: #047857; }
.delta.merged { color: #1d4ed8; }
.warning-text { color: #b42318; font-size: 12px; margin-top: 4px; }
.source-list { list-style: none; padding: 0; margin: 0; display: grid; gap: 5px; font-size: 12px; }
.source-list li { display: flex; align-items: center; gap: 5px; flex-wrap: wrap; }
.source-dot { width: 7px; height: 7px; border-radius: 50%; background: var(--brand); display: inline-block; }
.actions-cell { min-width: 170px; }
.actions-cell .link { display: block; margin-top: 6px; }
.status-pill { display: inline-block; padding: 3px 8px; border-radius: 999px; font-size: 12px; margin-bottom: 4px; }
.status-pill.pending { background: #f1f5f9; color: #475569; }
.status-pill.done { background: #ecfdf5; color: #047857; }
.status-pill.review { background: #fff1f2; color: #be123c; }
.inline-error, .inline-success { border-radius: 6px; padding: 9px 12px; margin: 10px 0; font-size: 13px; }
.inline-error { background: #fef2f2; color: #b42318; border: 1px solid #fecaca; }
.inline-success { background: #ecfdf5; color: #047857; border: 1px solid #a7f3d0; }
.btn.warning { border-color: #f59e0b; color: #b45309; background: #fffbeb; }
@media (max-width: 1100px) { .context-grid { grid-template-columns: 1fr; } .story-steps { grid-template-columns: 1fr 1fr; } }
@media (max-width: 640px) { .story-steps { grid-template-columns: 1fr; } }
</style>
