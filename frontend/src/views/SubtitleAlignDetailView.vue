<template>
  <section class="page detail-page" data-testid="subtitle-align-detail">
    <header class="page-head">
      <div>
        <h2>字幕对齐详情 · 第 {{ detail?.line_number ?? route.params.ref }} 行</h2>
        <p class="page-desc">追踪原片标注试算、并发人工更正和服务端实际采纳结果；历史发行版本保持当时边界。</p>
      </div>
      <div class="page-actions">
        <RouterLink class="btn" to="/subtitle_align">返回字幕对齐页</RouterLink>
        <RouterLink class="btn primary" :to="`/alignment-trial`">返回试算视图</RouterLink>
      </div>
    </header>

    <div v-if="loading" class="state-box">正在读取对齐详情…</div>
    <div v-else-if="errorMessage" class="inline-error" data-testid="detail-error">{{ errorMessage }}</div>
    <template v-else-if="detail">
      <section class="detail-toolbar">
        <label>
          <span>查看版本</span>
          <select v-model="version" data-testid="version-select" @change="reload">
            <option v-for="item in detail.available_versions" :key="item.key" :value="item.key">{{ item.label }}</option>
          </select>
        </label>
        <span class="version-notice" data-testid="version-notice">{{ detail.version_notice }}</span>
      </section>

      <section class="summary-grid">
        <article class="value-card">
          <h3>{{ detail.version_label }} · 实际起止</h3>
          <div class="big-values">
            <span data-testid="actual-start">{{ detail.actual_start_ms }}</span>
            <span class="arrow">→</span>
            <span data-testid="actual-end">{{ detail.actual_end_ms }}</span>
            <small>毫秒</small>
          </div>
          <p>
            相对原发行边界净偏移
            <strong :class="detail.net_delta_ms >= 0 ? 'delta positive' : 'delta negative'" data-testid="net-delta">
              {{ detail.net_delta_ms >= 0 ? '+' : '' }}{{ detail.net_delta_ms }}ms
            </strong>
          </p>
          <p class="muted">对齐编号：{{ detail.align_id }}；资源 ID：{{ detail.entry_id }}</p>
        </article>

        <article class="value-card">
          <h3>再审结论</h3>
          <div
            :class="['review-badge', versionReview ? 'review' : 'done']"
            data-testid="review-required"
            :data-needs-review="versionReview"
          >
            {{ versionReview ? '该行仍需再审' : version === 'ORIG-RELEASE' ? '原发行版本按原值复查' : '暂不需要再审' }}
          </div>
          <p data-testid="adoption-summary">{{ detail.adoption_summary ?? '尚未产生新的采纳确认' }}</p>
          <p v-if="detail.working_needs_review && version === 'ORIG-RELEASE'" class="warning-text">
            当前工作版仍有并发合并项需要再审；切换到“当前采纳版本”可处理。
          </p>
          <button
            v-if="version === 'WORKING' && versionReview"
            class="btn primary review-action"
            type="button"
            data-testid="complete-review"
            :disabled="reviewBusy"
            @click="completeReviewForLine"
          >
            {{ reviewBusy ? '提交中…' : '标记再审完成' }}
          </button>
          <p v-if="reviewMessage" class="review-message" data-testid="review-message">{{ reviewMessage }}</p>
        </article>

        <article class="value-card">
          <h3>变动前后边界</h3>
          <dl class="boundary-list">
            <div><dt>原发行开始</dt><dd data-testid="released-start">{{ detail.released_start_ms }}ms</dd></div>
            <div><dt>原发行结束</dt><dd data-testid="released-end">{{ detail.released_end_ms }}ms</dd></div>
            <div><dt>当前开始</dt><dd>{{ detail.current_start_ms }}ms</dd></div>
            <div><dt>当前结束</dt><dd>{{ detail.current_end_ms }}ms</dd></div>
          </dl>
        </article>
      </section>

      <section class="detail-grid">
        <article class="info-card" data-testid="source-panel">
          <h3>两笔变化的来源</h3>
          <p v-if="version === 'ORIG-RELEASE'" class="historical-note">
            以下变化只属于当前工作版；原发行版本不包含这些偏移。
          </p>
          <ul class="source-cards">
            <li
              v-for="source in detail.sources"
              :key="source.adjustment_id"
              :data-testid="`source-card-${source.source_type}`"
              :data-source-id="source.source_id"
            >
              <header>
                <span class="source-kind">{{ sourceKindLabel(source.source_type) }}</span>
                <strong>{{ source.source_label ?? source.label }}</strong>
                <b :class="(source.delta_ms ?? 0) >= 0 ? 'delta positive' : 'delta negative'">
                  {{ (source.delta_ms ?? 0) >= 0 ? '后移 +' : '前移 ' }}{{ source.delta_ms }}ms
                </b>
              </header>
              <p>{{ source.note }}</p>
              <footer>
                <span>来源单号：{{ source.source_id }}</span>
                <span>处理人：{{ source.author }}</span>
                <span>修订：R{{ source.revision }}</span>
                <span v-if="source.late" class="late">确认期间到达</span>
              </footer>
            </li>
            <li v-if="!detail.sources.length" class="muted">暂无额外变化来源。</li>
          </ul>
        </article>

        <article class="info-card">
          <h3>原片交界与区间</h3>
          <dl class="boundary-list">
            <div><dt>交界毫秒</dt><dd data-testid="boundary-ms">{{ detail.boundary_assignment?.boundary_ms ?? 4000 }}ms</dd></div>
            <div><dt>唯一归属区间</dt><dd data-testid="assigned-interval">{{ detail.boundary_assignment?.assigned_interval_id }}</dd></div>
            <div><dt>归属规则</dt><dd>{{ detail.boundary_assignment?.rule }}</dd></div>
            <div><dt>原区间包含本行</dt><dd>{{ detail.interval?.contained_by_original_interval ? '是，仍按原片毫秒判定' : '否' }}</dd></div>
          </dl>
          <p class="muted">{{ detail.interval?.membership_basis }}</p>
        </article>
      </section>

      <section class="info-card confirmation-card" data-testid="confirmation-history">
        <h3>实际采纳的对齐确认结果</h3>
        <table class="data-table">
          <thead>
            <tr><th>确认单号</th><th>确认人</th><th>客户端/服务端修订</th><th>提交时前后值</th><th>实际结果</th><th>再审</th></tr>
          </thead>
          <tbody>
            <tr v-for="item in detail.confirmations" :key="String(item.confirmation_id)">
              <td>{{ String(item.confirmation_id) }}</td>
              <td>{{ String(item.reviewer) }}</td>
              <td>R{{ String(item.client_revision) }} / R{{ String(item.server_revision) }}<span v-if="item.stale_submission" class="warning-text">（旧表单提交）</span></td>
              <td>
                {{ Number((item.before as Record<string, number>)?.start_ms) }}–{{ Number((item.before as Record<string, number>)?.end_ms) }}
                →
                {{ Number((item.after as Record<string, number>)?.start_ms) }}–{{ Number((item.after as Record<string, number>)?.end_ms) }}ms
              </td>
              <td>{{ String(item.result) }}</td>
              <td>{{ item.needs_review ? '需要再审' : '无需再审' }}</td>
            </tr>
            <tr v-if="!detail.confirmations.length">
              <td colspan="6" class="empty-state">该行尚未确认；可从试算视图或字幕对齐列表执行确认。</td>
            </tr>
          </tbody>
        </table>
      </section>
    </template>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'

import { completeReview, getAlignmentDetail, type AlignmentDetail } from '@/api/alignment-trial'

const route = useRoute()
const detail = ref<AlignmentDetail | null>(null)
const initialVersion = Array.isArray(route.query.version) ? route.query.version[0] : route.query.version
const version = ref(typeof initialVersion === 'string' ? initialVersion : 'WORKING')
const loading = ref(false)
const reviewBusy = ref(false)
const reviewMessage = ref('')
const errorMessage = ref('')
const routeRef = computed(() => String(route.params.lineNumber ?? route.params.entryId ?? route.params.ref ?? '5'))
const lookupKind = computed<'line' | 'entry'>(() => route.name === 'subtitle-entry-detail' ? 'entry' : 'line')
const versionReview = computed(() => Boolean(detail.value?.needs_review))

async function reload() {
  loading.value = true
  errorMessage.value = ''
  try {
    detail.value = await getAlignmentDetail(routeRef.value, version.value, lookupKind.value)
    if (detail.value.ok === false) errorMessage.value = detail.value.message ?? '详情不存在'
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '对齐详情读取失败'
  } finally {
    loading.value = false
  }
}

async function completeReviewForLine() {
  reviewBusy.value = true
  reviewMessage.value = ''
  errorMessage.value = ''
  try {
    const result = await completeReview(routeRef.value)
    reviewMessage.value = result.message
    await reload()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '完成再审失败'
  } finally {
    reviewBusy.value = false
  }
}

function sourceKindLabel(kind?: string): string {
  if (kind === 'timeline_annotation') return '原片标注偏移'
  if (kind === 'manual_correction') return '人工/并发更正'
  return kind ?? '其他来源'
}

watch(routeRef, reload)
onMounted(reload)
</script>

<style scoped>
.detail-toolbar { display: flex; gap: 14px; align-items: end; background: #fff; border: 1px solid var(--border); border-radius: 8px; padding: 10px 14px; margin: 12px 0; }
.detail-toolbar label { display: grid; gap: 4px; font-size: 12px; color: var(--muted); }
.detail-toolbar select { border: 1px solid var(--border); border-radius: 6px; padding: 7px 10px; min-width: 180px; }
.version-notice { font-size: 13px; }
.summary-grid, .detail-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 12px; }
.detail-grid { grid-template-columns: 1.2fr .8fr; }
.value-card, .info-card { background: #fff; border: 1px solid var(--border); border-radius: 8px; padding: 14px 16px; }
.value-card h3, .info-card h3 { margin: 0 0 10px; font-size: 15px; }
.big-values { display: flex; align-items: baseline; gap: 8px; font-size: 28px; font-weight: 700; }
.big-values small { font-size: 12px; color: var(--muted); font-weight: 400; }
.arrow { color: var(--muted); font-size: 20px; }
.delta { font-weight: 700; }
.delta.positive { color: #b45309; }
.delta.negative { color: #047857; }
.muted { color: var(--muted); font-size: 12px; line-height: 1.6; }
.review-badge { display: inline-block; border-radius: 999px; padding: 7px 12px; font-weight: 700; font-size: 14px; margin-bottom: 8px; }
.review-badge.review { background: #fff1f2; color: #be123c; border: 1px solid #fecdd3; }
.review-badge.done { background: #ecfdf5; color: #047857; border: 1px solid #a7f3d0; }
.boundary-list { display: grid; grid-template-columns: 1fr 1fr; gap: 8px 12px; margin: 0; }
.boundary-list div { display: grid; gap: 2px; }
.boundary-list dt { color: var(--muted); font-size: 12px; }
.boundary-list dd { margin: 0; font-size: 13px; }
.source-cards { list-style: none; margin: 0; padding: 0; display: grid; gap: 10px; }
.source-cards li { border: 1px solid var(--border); border-radius: 8px; padding: 10px 12px; background: #fbfdff; }
.source-cards header { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; font-size: 13px; }
.source-kind { background: #e0e7ff; color: #3730a3; border-radius: 999px; padding: 2px 8px; font-size: 12px; }
.source-cards p { margin: 8px 0; font-size: 13px; line-height: 1.6; }
.source-cards footer { display: flex; gap: 12px; flex-wrap: wrap; color: var(--muted); font-size: 12px; }
.late { color: #be123c; font-weight: 700; }
.historical-note { background: #f8fafc; border-left: 3px solid #94a3b8; padding: 8px 10px; font-size: 13px; }
.warning-text { color: #b42318; font-size: 12px; }
.review-action { margin-top: 8px; }
.review-message { color: #047857; font-size: 13px; margin: 8px 0 0; }
.confirmation-card { margin-bottom: 16px; }
.state-box { padding: 30px; text-align: center; color: var(--muted); }
.inline-error { background: #fef2f2; color: #b42318; border: 1px solid #fecaca; border-radius: 6px; padding: 10px 12px; }
@media (max-width: 1100px) { .summary-grid, .detail-grid { grid-template-columns: 1fr; } }
</style>
