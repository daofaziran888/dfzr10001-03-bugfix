import { createRouter, createWebHistory } from 'vue-router'

import Overview from '@/views/Overview.vue'
const Source = () => import('@/views/source/index.vue')
const Website = () => import('@/views/website/index.vue')
const Task = () => import('@/views/task/index.vue')
const Schedule = () => import('@/views/schedule/index.vue')
const Increment = () => import('@/views/increment/index.vue')
const Rpa = () => import('@/views/rpa/index.vue')
const Log = () => import('@/views/log/index.vue')
const Retry = () => import('@/views/retry/index.vue')
const Proxy = () => import('@/views/proxy/index.vue')
const Parser = () => import('@/views/parser/index.vue')
const Dedup = () => import('@/views/dedup/index.vue')
const Release = () => import('@/views/release/index.vue')
const Alert = () => import('@/views/alert/index.vue')
const Dashboard = () => import('@/views/dashboard/index.vue')
const Storage = () => import('@/views/storage/index.vue')
const Audit = () => import('@/views/audit/index.vue')

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'overview', component: Overview },
    { path: '/source', name: 'source', component: Source },
    { path: '/website', name: 'website', component: Website },
    { path: '/task', name: 'task', component: Task },
    { path: '/schedule', name: 'schedule', component: Schedule },
    { path: '/increment', name: 'increment', component: Increment },
    { path: '/rpa', name: 'rpa', component: Rpa },
    { path: '/log', name: 'log', component: Log },
    { path: '/retry', name: 'retry', component: Retry },
    { path: '/proxy', name: 'proxy', component: Proxy },
    { path: '/parser', name: 'parser', component: Parser },
    { path: '/dedup', name: 'dedup', component: Dedup },
    { path: '/release', name: 'release', component: Release },
    { path: '/alert', name: 'alert', component: Alert },
    { path: '/dashboard', name: 'dashboard', component: Dashboard },
    { path: '/storage', name: 'storage', component: Storage },
    { path: '/audit', name: 'audit', component: Audit },
  ],
})

export default router
