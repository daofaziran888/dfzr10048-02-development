<template>
  <section class="adoption-panel" data-testid="alignment-adoption-panel">
    <header class="panel-head">
      <div>
        <h3>每行实际采纳的对齐确认结果</h3>
        <p>字幕对齐页直接显示服务端合并后的实际起止值、来源和再审状态；切换版本可按原发行边界复查。</p>
      </div>
      <div class="panel-actions">
        <label class="version-picker">
          <span>版本</span>
          <select v-model="version" data-testid="panel-version-select" @change="reload">
            <option value="WORKING">当前采纳版本</option>
            <option value="ORIG-RELEASE">原发行版本</option>
          </select>
        </label>
        <RouterLink class="btn primary" to="/alignment-trial" data-testid="open-trial-view">进入试算视图</RouterLink>
      </div>
    </header>

    <p v-if="errorMessage" class="panel-error">{{ errorMessage }}</p>
    <div class="panel-table-wrap">
      <table class="data-table adoption-table">
        <thead>
          <tr>
            <th>字幕行</th>
            <th>原片时间/文本</th>
            <th>{{ version === 'ORIG-RELEASE' ? '原发行起止（复查值）' : '实际采纳起止' }}</th>
            <th>净偏移</th>
            <th>采纳来源</th>
            <th>确认/再审</th>
            <th>详情</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="line in lines"
            :key="line.line_number"
            :data-testid="`adoption-row-${line.line_number}`"
            :data-needs-review="line.needs_review"
          >
            <td><strong>第 {{ line.line_number }} 行</strong><div class="muted">ID {{ line.entry_id }}</div></td>
            <td class="text-cell">{{ line.text }}</td>
            <td>
              <span data-testid="panel-actual-start">{{ line.actual_start_ms }}</span>–<span data-testid="panel-actual-end">{{ line.actual_end_ms }}</span>ms
              <div v-if="version !== 'ORIG-RELEASE'" class="muted">原发行 {{ line.released_start_ms }}–{{ line.released_end_ms }}ms</div>
            </td>
            <td :class="line.net_delta_ms >= 0 ? 'delta positive' : 'delta negative'">
              {{ line.net_delta_ms >= 0 ? '+' : '' }}{{ line.net_delta_ms }}ms
            </td>
            <td>
              <ul class="mini-sources">
                <li v-for="source in line.sources" :key="source.adjustment_id">
                  {{ source.source_label ?? source.label }}：{{ source.delta_ms && source.delta_ms >= 0 ? '+' : '' }}{{ source.delta_ms }}ms
                </li>
                <li v-if="!line.sources.length" class="muted">尚未采纳变化</li>
              </ul>
            </td>
            <td>
              <span :class="['status-pill', line.needs_review ? 'review' : line.adopted ? 'done' : 'pending']">
                {{ version === 'ORIG-RELEASE' ? '按原值复查' : line.needs_review ? '需再审' : line.adopted ? '已采纳' : line.status }}
              </span>
            </td>
            <td>
              <RouterLink class="link" :to="`/subtitle-align/line/${line.line_number}?version=${version}`" :data-testid="`panel-detail-${line.line_number}`">
                打开第 {{ line.line_number }} 行
              </RouterLink>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'

import { listAlignmentLines, type AlignmentDetail } from '@/api/alignment-trial'

const lines = ref<AlignmentDetail[]>([])
const version = ref('WORKING')
const errorMessage = ref('')

async function reload() {
  errorMessage.value = ''
  try {
    const payload = await listAlignmentLines(version.value)
    lines.value = payload.items
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '采纳结果读取失败'
  }
}

defineExpose({ reload })
onMounted(reload)
</script>

<style scoped>
.adoption-panel { background: #f8fafc; border: 1px solid var(--border); border-radius: 10px; padding: 14px; margin: 12px 0 16px; }
.panel-head { display: flex; justify-content: space-between; gap: 12px; align-items: flex-start; }
.panel-head h3 { margin: 0 0 4px; font-size: 16px; }
.panel-head p { margin: 0; color: var(--muted); font-size: 13px; }
.panel-actions { display: flex; align-items: end; gap: 10px; }
.version-picker { display: grid; gap: 4px; font-size: 12px; color: var(--muted); }
.version-picker select { border: 1px solid var(--border); border-radius: 6px; padding: 7px 10px; background: #fff; }
.panel-table-wrap { margin-top: 12px; overflow-x: auto; }
.text-cell { min-width: 220px; font-size: 13px; line-height: 1.6; }
.muted { color: var(--muted); font-size: 12px; }
.delta { font-weight: 700; white-space: nowrap; }
.delta.positive { color: #b45309; }
.delta.negative { color: #047857; }
.mini-sources { margin: 0; padding-left: 16px; font-size: 12px; line-height: 1.7; }
.status-pill { display: inline-block; padding: 3px 8px; border-radius: 999px; font-size: 12px; white-space: nowrap; }
.status-pill.pending { background: #e2e8f0; color: #475569; }
.status-pill.done { background: #d1fae5; color: #047857; }
.status-pill.review { background: #ffe4e6; color: #be123c; }
.panel-error { color: #b42318; font-size: 13px; }
</style>
