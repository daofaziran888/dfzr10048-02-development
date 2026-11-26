import { createRouter, createWebHistory } from 'vue-router'

import AlignmentTrialView from '@/views/AlignmentTrialView.vue'
import Overview from '@/views/Overview.vue'
import SubtitleAlignDetailView from '@/views/SubtitleAlignDetailView.vue'
import WorkbenchView from '@/views/WorkbenchView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'overview', component: Overview },
    { path: '/alignment-trial', name: 'alignment-trial', component: AlignmentTrialView },
    { path: '/timeline_mark/trial', component: AlignmentTrialView },
    { path: '/timeline-mark/trial', component: AlignmentTrialView },
    { path: '/trial', redirect: '/alignment-trial' },
    {
      path: '/subtitle-align/line/:lineNumber',
      name: 'subtitle-line-detail',
      component: SubtitleAlignDetailView,
    },
    {
      path: '/subtitle-align/entry/:entryId',
      name: 'subtitle-entry-detail',
      component: SubtitleAlignDetailView,
    },
    { path: '/subtitle_align/detail/:entryId', redirect: '/subtitle-align/entry/:entryId' },
    { path: '/subtitle_align/line/:lineNumber', redirect: '/subtitle-align/line/:lineNumber' },
    { path: '/:moduleKey', name: 'module', component: WorkbenchView, props: true },
  ],
})

export default router
