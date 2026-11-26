import { request } from './client'

export type TrialRow = {
  line_number: number
  entry_id: number
  align_id: string
  text?: string
  sort_ms: number
  original_start_ms: number
  original_end_ms: number
  before_start_ms: number
  before_end_ms: number
  trial_delta_ms: number
  trial_start_ms: number
  trial_end_ms: number
  server_delta_ms: number
  server_start_ms: number
  server_end_ms: number
  after_start_ms: number
  after_end_ms: number
  has_late_correction: boolean
  adopted: boolean
  needs_review: boolean
  status: string
  interval?: {
    interval_id?: string
    label?: string
    contained_by_original_interval?: boolean
  }
  sources: AlignmentSource[]
}

export type AlignmentSource = {
  adjustment_id?: string
  source_type?: string
  origin?: string
  source?: string
  source_id?: string
  source_label?: string
  label?: string
  author?: string
  delta_ms?: number
  note?: string
  status?: string
  revision?: number
  late?: boolean
}

export type TrialPreview = {
  ok: boolean
  trial_id: string
  media_id: string
  calculation_basis: string
  calculation_note: string
  revision: number
  boundary_ms: number
  mark: Record<string, unknown>
  annotation_text?: string
  annotation_comment_original?: string
  boundary_assignment: {
    assigned_interval_id?: string
    rule?: string
    match_count?: number
  }
  rows: TrialRow[]
}

export type AlignmentDetail = {
  ok: boolean
  message?: string
  line_number: number
  entry_id: number
  align_id: string
  text?: string
  version: string
  version_label: string
  version_notice: string
  available_versions: { key: string; label: string }[]
  original_start_ms: number
  original_end_ms: number
  released_start_ms: number
  released_end_ms: number
  actual_start_ms: number
  actual_end_ms: number
  current_start_ms: number
  current_end_ms: number
  net_delta_ms: number
  adopted: boolean
  needs_review: boolean
  review_required: boolean
  working_needs_review: boolean
  status: string
  alignment_method?: string
  adoption_summary?: string
  sources: AlignmentSource[]
  confirmations: Record<string, unknown>[]
  interval?: Record<string, unknown>
  boundary_assignment?: Record<string, unknown>
}

async function readJson<T>(response: Response, fallbackMessage: string): Promise<T> {
  if (!response.ok) throw new Error(fallbackMessage)
  return (await response.json()) as T
}

export async function getTrialPreview(options: { clientRevision?: number; markRef?: string } = {}): Promise<TrialPreview> {
  const params = new URLSearchParams()
  if (options.clientRevision) params.set('client_revision', String(options.clientRevision))
  if (options.markRef) params.set('mark_ref', options.markRef)
  const query = params.toString() ? `?${params.toString()}` : ''
  const response = await request(`/api/alignment-trial/preview${query}`)
  return readJson<TrialPreview>(response, '试算数据读取失败')
}

export async function arriveBCorrection(): Promise<{ ok: boolean; message: string }> {
  const response = await request('/api/alignment-trial/scenario/b-correction', { method: 'POST' })
  return readJson(response, '乙的更正送达失败')
}

export async function confirmTrial(payload: {
  line_numbers?: number[]
  line_number?: number
  reviewer?: string
  client_revision?: number
}): Promise<{ ok: boolean; message: string; results?: unknown[] }> {
  const response = await request('/api/alignment-trial/confirm', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
  return readJson(response, '试算确认失败')
}

export async function resetTrial(): Promise<{ ok: boolean }> {
  const response = await request('/api/alignment-trial/reset', { method: 'POST' })
  return readJson(response, '试算重置失败')
}

export async function completeReview(ref: string | number): Promise<{ ok: boolean; message: string }> {
  const response = await request(`/api/alignment-trial/lines/${encodeURIComponent(String(ref))}/complete-review`, {
    method: 'POST',
    body: JSON.stringify({ reviewer: '字幕对齐详情页' }),
  })
  return readJson(response, '完成再审失败')
}

export async function listAlignmentLines(version = 'WORKING'): Promise<{ items: AlignmentDetail[] }> {
  const response = await request(`/api/alignment-trial/lines?version=${encodeURIComponent(version)}`)
  return readJson(response, '对齐采纳结果读取失败')
}

export async function getAlignmentDetail(
  ref: string | number,
  version = 'WORKING',
  lookup: 'line' | 'entry' = 'line',
): Promise<AlignmentDetail> {
  const resource = lookup === 'entry' ? 'entries' : 'lines'
  const response = await request(
    `/api/alignment-trial/${resource}/${encodeURIComponent(String(ref))}?version=${encodeURIComponent(version)}`,
  )
  return readJson<AlignmentDetail>(response, '对齐详情读取失败')
}
