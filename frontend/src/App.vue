<template>
  <div class="app-shell">
    <aside class="app-side">
      <h1 class="app-title">数据采集调度中心</h1>
      <nav class="nav-list">
        <RouterLink v-for="item in navItems" :key="item.path" :to="item.path" class="nav-item">
          {{ item.label }}
        </RouterLink>
      </nav>
    </aside>
    <main class="app-main">
      <header class="app-head">
        <span class="head-desc">面向互联网数据采集、网页爬虫调度、RPA自动化流程与采集结果校验的集中管理平台。支持多源接入、增量采集、抓取规则配置、采集任务编排、失败重试与结果质量稽核。</span>
        <span class="head-user">当前值班：{{ store.operator }} · {{ store.shiftLabel }}</span>
      </header>
      <RouterView />
    </main>
  </div>
</template>

<script setup lang="ts">
import { useSessionStore } from '@/stores/session'

const store = useSessionStore()

const navItems = [{ label: "运营概览", path: "/" }, { label: "采集源管理", path: "/source" }, { label: "网页抓取规则", path: "/website" }, { label: "采集任务", path: "/task" }, { label: "调度编排", path: "/schedule" }, { label: "增量采集游标", path: "/increment" }, { label: "RPA流程配置", path: "/rpa" }, { label: "采集日志", path: "/log" }, { label: "失败重试策略", path: "/retry" }, { label: "代理与请求控制", path: "/proxy" }, { label: "数据解析模板", path: "/parser" }, { label: "采集去重", path: "/dedup" }, { label: "采集版本管理", path: "/release" }, { label: "采集告警", path: "/alert" }, { label: "采集看板", path: "/dashboard" }, { label: "采集数据存储", path: "/storage" }, { label: "采集审计", path: "/audit" }]
</script>
