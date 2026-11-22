<template>
  <section class="page">
    <header class="page-head">
      <div>
        <h2>运营概览</h2>
        <p class="page-desc">汇总各业务模块的关键指标，先看总量再看异常。</p>
      </div>
    </header>
    <div class="stat-row">
      <article v-for="card in cards" :key="card.label" class="stat-card">
        <span class="stat-label">{{ card.label }}</span>
        <strong class="stat-value">{{ card.value }}</strong>
      </article>
    </div>
    <table class="data-table">
      <thead>
        <tr><th>业务模块</th><th>今日新增</th><th>待处理</th><th>异常量</th></tr>
      </thead>
      <tbody>
        <tr v-for="row in moduleRows" :key="row.name">
          <td>{{ row.name }}</td>
          <td>{{ row.created }}</td>
          <td>{{ row.pending }}</td>
          <td>{{ row.abnormal }}</td>
        </tr>
      </tbody>
    </table>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import { fetchJson } from '@/api/client'

type Overview = {
  cards: { label: string; value: number }[]
  modules: { name: string; created: number; pending: number; abnormal: number }[]
}

const cards = ref<Overview['cards']>([])
const moduleRows = ref<Overview['modules']>([])

onMounted(async () => {
  try {
    const payload = await fetchJson<Overview>('/api/overview')
    cards.value = payload.cards
    moduleRows.value = payload.modules
  } catch {
    cards.value = [{"label": "业务模块", "value": 0}, {"label": "今日新增", "value": 0}]
    moduleRows.value = [{"name": "媒体源", "created": 0, "pending": 0, "abnormal": 0}, {"name": "采集通道", "created": 0, "pending": 0, "abnormal": 0}, {"name": "媒体分片", "created": 0, "pending": 0, "abnormal": 0}, {"name": "转码作业", "created": 0, "pending": 0, "abnormal": 0}, {"name": "转写任务", "created": 0, "pending": 0, "abnormal": 0}, {"name": "语音分段", "created": 0, "pending": 0, "abnormal": 0}, {"name": "说话人标注", "created": 0, "pending": 0, "abnormal": 0}, {"name": "字幕对齐", "created": 0, "pending": 0, "abnormal": 0}, {"name": "时间轴标注", "created": 0, "pending": 0, "abnormal": 0}, {"name": "术语抽取", "created": 0, "pending": 0, "abnormal": 0}, {"name": "转写版本", "created": 0, "pending": 0, "abnormal": 0}, {"name": "置信复核", "created": 0, "pending": 0, "abnormal": 0}, {"name": "纠错回路", "created": 0, "pending": 0, "abnormal": 0}, {"name": "字幕包", "created": 0, "pending": 0, "abnormal": 0}, {"name": "媒体索引", "created": 0, "pending": 0, "abnormal": 0}, {"name": "分片水位", "created": 0, "pending": 0, "abnormal": 0}, {"name": "失败重投", "created": 0, "pending": 0, "abnormal": 0}, {"name": "转写配额", "created": 0, "pending": 0, "abnormal": 0}, {"name": "抽样质检", "created": 0, "pending": 0, "abnormal": 0}, {"name": "交付回执", "created": 0, "pending": 0, "abnormal": 0}, {"name": "归档架位", "created": 0, "pending": 0, "abnormal": 0}, {"name": "采集审计", "created": 0, "pending": 0, "abnormal": 0}]
  }
})
</script>
