<template>
  <div class="flex min-h-screen bg-[#fcfcfd] text-slate-800 overflow-hidden font-sans selection:bg-brand-500/20">
    <!-- --- Subtle Background Elements --- -->
    <div class="fixed inset-0 overflow-hidden pointer-events-none">
      <div class="absolute top-[-10%] left-[-5%] w-[40%] h-[40%] bg-brand-500/5 blur-[120px] rounded-full" />
      <div class="absolute bottom-[-5%] right-[-5%] w-[30%] h-[30%] bg-indigo-500/5 blur-[100px] rounded-full" />
    </div>

    <!-- --- Left Sidebar --- -->
    <aside :class="[
      'relative z-20 h-screen border-r border-slate-200 bg-white transition-all duration-500 flex flex-col items-center py-8',
      sidebarOpen ? 'w-72' : 'w-20'
    ]">
      <div class="flex items-center gap-3 mb-10 px-6">
        <div class="w-10 h-10 bg-brand-600 rounded-xl flex items-center justify-center shadow-lg shadow-brand-500/30 flex-shrink-0">
          <span class="text-white text-xl">✨</span>
        </div>
        <span v-if="sidebarOpen" class="text-xl font-bold tracking-tight text-slate-900 px-2 leading-none">
          黄金白银情报系统
        </span>
      </div>

      <nav class="flex-1 w-full px-4 space-y-1">
        <button
          v-for="tab in navigationTabs"
          :key="tab.id"
          @click="activeTab = tab.id"
          :class="[
            'w-full flex items-center gap-4 px-6 py-4 rounded-2xl transition-all group',
            activeTab === tab.id
              ? 'bg-slate-900 text-white shadow-lg shadow-slate-200'
              : 'text-slate-700 hover:bg-slate-50'
          ]"
        >
          <span class="text-2xl" :class="activeTab === tab.id ? 'text-white' : 'group-hover:text-brand-600'">
            {{ tab.icon }}
          </span>
          <span v-if="sidebarOpen" class="font-bold">
            {{ tab.label }}
          </span>
          <span v-if="sidebarOpen && activeTab === tab.id" class="ml-auto">→</span>
        </button>
      </nav>

      <div class="mt-auto px-4 w-full">
        <div class="p-4 rounded-2xl bg-slate-50 border border-slate-100 space-y-3">
          <div class="flex items-center gap-2 text-[10px] text-slate-900 uppercase tracking-widest font-bold">
            <span class="text-brand-600">⚡</span>
            <span>引擎状态</span>
          </div>
          <div class="flex items-center gap-2">
            <div class="w-1.5 h-1.5 rounded-full bg-green-600" />
            <span v-if="sidebarOpen" class="text-xs font-bold text-slate-800 uppercase tracking-tighter">
              System Active
            </span>
          </div>
        </div>
      </div>
    </aside>

    <!-- --- Main Content --- -->
    <main class="flex-1 relative z-10 h-screen flex flex-col">
      <!-- Header -->
      <header class="h-16 border-b border-slate-200 flex items-center justify-between px-8 bg-white/80 backdrop-blur-md">
        <div class="flex items-center gap-4">
          <button
            @click="sidebarOpen = !sidebarOpen"
            class="p-2 hover:bg-slate-100 rounded-lg transition-colors text-slate-900"
          >
            <span class="text-xl">☰</span>
          </button>
          <div class="h-4 w-px bg-slate-200 mx-1" />
          <h2 class="text-xs font-black text-slate-900 uppercase tracking-[0.2em]">
            {{ currentTabLabel }}
          </h2>
        </div>
        <div class="flex items-center gap-3">
          <button class="p-2 hover:bg-slate-100 rounded-full text-slate-900 transition-colors">
            <span class="text-xl">☀️</span>
          </button>
          <a
            href="https://github.com/hotpot-killer/gold-silver-finance-agent"
            target="_blank"
            class="flex items-center gap-2 px-4 py-1.5 bg-slate-900 text-white hover:bg-slate-800 rounded-full text-xs font-bold transition-all shadow-sm"
          >
            <span>⭐</span>
            <span>Star on Github</span>
          </a>
        </div>
      </header>

      <!-- Content Area -->
      <div class="flex-1 overflow-y-auto p-8 custom-scrollbar">
        <!-- Dashboard Tab -->
        <div v-if="activeTab === 'dashboard'" class="space-y-8">
          <!-- Hero Section - Intelligence System -->
          <section class="bg-gradient-to-br from-slate-900/10 via-slate-800/5 to-slate-700/10 rounded-3xl p-8 border border-slate-300">
            <div class="flex items-center gap-2 mb-4">
              <span class="px-3 py-1 bg-slate-900 text-white rounded-full text-xs font-bold">
                黄金白银情报系统
              </span>
              <span class="text-slate-500 text-sm">/ AI 辅助决策</span>
            </div>
            <h2 class="text-4xl font-bold text-slate-900 mb-4">
              多源情报融合，智能决策支持<br>
              <span class="bg-gradient-to-r from-brand-600 to-slate-600 bg-clip-text text-transparent">
                你的专属交易情报站
              </span>
            </h2>
            <p class="text-slate-600 text-lg max-w-2xl">
              融合实时价格信号、地缘政治情报、大佬观点和历史预警，
              AI 辅助人类完成黄金白银交易决策。
            </p>
          </section>

          <!-- Stats Cards -->
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div class="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm hover:shadow-md transition-shadow">
              <div class="flex items-center justify-between mb-4">
                <span class="text-3xl">🥇</span>
                <span class="text-xs font-bold text-slate-500 uppercase">黄金</span>
              </div>
              <div class="text-2xl font-bold text-slate-900">
                {{ formatPrice(priceData.gold.latest?.close) }}
              </div>
              <div :class="['text-sm font-medium', priceChange.gold?.direction === 'up' ? 'text-green-600' : 'text-red-600']">
                {{ priceChange.gold?.direction === 'up' ? '↑' : '↓' }}
                {{ priceChange.gold?.pct?.toFixed(2) }}%
              </div>
            </div>

            <div class="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm hover:shadow-md transition-shadow">
              <div class="flex items-center justify-between mb-4">
                <span class="text-3xl">🥈</span>
                <span class="text-xs font-bold text-slate-500 uppercase">白银</span>
              </div>
              <div class="text-2xl font-bold text-slate-900">
                {{ formatPrice(priceData.silver.latest?.close) }}
              </div>
              <div :class="['text-sm font-medium', priceChange.silver?.direction === 'up' ? 'text-green-600' : 'text-red-600']">
                {{ priceChange.silver?.direction === 'up' ? '↑' : '↓' }}
                {{ priceChange.silver?.pct?.toFixed(2) }}%
              </div>
            </div>

            <div class="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm hover:shadow-md transition-shadow">
              <div class="flex items-center justify-between mb-4">
                <span class="text-3xl">⚠️</span>
                <span class="text-xs font-bold text-slate-500 uppercase">预警数</span>
              </div>
              <div class="text-2xl font-bold text-slate-900">
                {{ stats.total || 0 }}
              </div>
              <div class="text-sm text-slate-500">
                今日预警
              </div>
            </div>

            <div class="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm hover:shadow-md transition-shadow">
              <div class="flex items-center justify-between mb-4">
                <span class="text-3xl">🧠</span>
                <span class="text-xs font-bold text-slate-500 uppercase">大佬</span>
              </div>
              <div class="text-2xl font-bold text-slate-900">
                {{ guruViews.length }}
              </div>
              <div class="text-sm text-slate-500">
                位专家观点
              </div>
            </div>
          </div>

          <!-- K线图 -->
          <div class="bg-white border border-slate-200 rounded-2xl p-6">
            <div class="flex items-center justify-between mb-6">
              <h3 class="text-lg font-bold text-slate-900">价格走势</h3>
              <div class="flex gap-2">
                <button
                  v-for="asset in ['gold', 'silver', 'crude_oil']"
                  :key="asset"
                  @click="switchAsset(asset)"
                  :class="[
                    'px-4 py-2 rounded-xl text-sm font-bold transition-all',
                    selectedAsset === asset
                      ? 'bg-slate-900 text-white'
                      : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                  ]"
                >
                  {{ asset === 'gold' ? '黄金' : asset === 'silver' ? '白银' : '原油' }}
                </button>
              </div>
            </div>
            <div ref="chartContainerRef" id="kline-chart" class="h-96 rounded-xl overflow-hidden"></div>
          </div>
        </div>

        <!-- Map Tab -->
        <div v-else-if="activeTab === 'map'" class="space-y-8">
          <div class="bg-white border border-slate-200 rounded-2xl p-6">
            <div class="flex items-center justify-between mb-6">
              <h3 class="text-lg font-bold text-slate-900">🌍 全球地缘政治风险地图</h3>
              <div class="flex items-center gap-4">
                <span class="text-sm text-slate-500">
                  更新于: {{ lastUpdateTime }}
                </span>
                <button
                  @click="refreshScenarios"
                  :disabled="scenariosLoading"
                  class="px-4 py-2 bg-slate-900 text-white rounded-xl text-sm font-bold hover:bg-slate-800 transition-colors disabled:opacity-50"
                >
                  {{ scenariosLoading ? '刷新中...' : '🔄 刷新' }}
                </button>
              </div>
            </div>

            <div class="grid grid-cols-1 lg:grid-cols-4 gap-6">
              <div class="lg:col-span-3">
                <div ref="mapContainerRef" id="middle-east-map" class="h-96 rounded-xl border border-slate-200 overflow-hidden"></div>
              </div>
              <div class="space-y-4">
                <div class="bg-slate-50 rounded-xl p-4">
                  <h4 class="text-sm font-bold text-slate-900 mb-3">热点图例</h4>
                  <div class="space-y-2">
                    <div class="flex items-center gap-2">
                      <span class="w-3 h-3 rounded-full bg-red-500"></span>
                      <span class="text-sm text-slate-700">高风险区域</span>
                    </div>
                    <div class="flex items-center gap-2">
                      <span class="w-3 h-3 rounded-full bg-yellow-500"></span>
                      <span class="text-sm text-slate-700">中风险区域</span>
                    </div>
                    <div class="flex items-center gap-2">
                      <span class="w-3 h-3 rounded-full bg-green-500"></span>
                      <span class="text-sm text-slate-700">低风险区域</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Scenario Cards -->
            <div class="mt-8 grid grid-cols-1 md:grid-cols-2 gap-6">
              <div
                v-for="(s, index) in middleEastScenarios"
                :key="s.name"
                @click="selectScenario(index)"
                :class="[
                  'bg-white border-2 rounded-2xl p-6 cursor-pointer transition-all hover:shadow-lg',
                  selectedScenarioIndex === index
                    ? 'border-brand-500 shadow-brand-500/20'
                    : 'border-slate-200 hover:border-slate-300'
                ]"
              >
                <div class="flex items-center justify-between mb-4">
                  <div class="flex items-center gap-2">
                    <span class="text-sm font-bold text-slate-500">#{{ index + 1 }}</span>
                    <span class="font-bold text-slate-900">{{ s.name }}</span>
                  </div>
                  <span class="px-3 py-1 rounded-full text-sm font-bold" :class="s.probability > 0.4 ? 'bg-red-100 text-red-700' : 'bg-slate-100 text-slate-700'">
                    {{ (s.probability * 100).toFixed(0) }}%
                  </span>
                </div>
                <div class="grid grid-cols-3 gap-4 mb-4">
                  <div class="text-center">
                    <div class="text-xs text-slate-500 mb-1">🥇 黄金</div>
                    <div class="font-bold text-slate-900">{{ s.gold_price_range || s.goldPriceRange || '4800-5100' }}</div>
                  </div>
                  <div class="text-center">
                    <div class="text-xs text-slate-500 mb-1">🥈 白银</div>
                    <div class="font-bold text-slate-900">{{ s.silver_price_range || s.silverPriceRange || '74-78' }}</div>
                  </div>
                  <div class="text-center">
                    <div class="text-xs text-slate-500 mb-1">🛢️ 原油</div>
                    <div class="font-bold text-slate-900">{{ s.crude_price_range || s.crudePriceRange || '95-105' }}</div>
                  </div>
                </div>
                <div class="text-center">
                  <span :class="[
                    'px-4 py-2 rounded-xl text-sm font-bold',
                    s.suggested_action === 'buy' ? 'bg-green-100 text-green-700' :
                    s.suggested_action === 'sell' ? 'bg-red-100 text-red-700' :
                    'bg-slate-100 text-slate-700'
                  ]">
                    {{ s.action_text || s.actionText || '观望持有' }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Alerts Tab -->
        <div v-else-if="activeTab === 'alerts'" class="space-y-6">
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <div
              v-for="(alert, idx) in allAlerts.slice(0, 12)"
              :key="idx"
              class="group bg-white border border-slate-200 rounded-2xl p-5 flex flex-col gap-4 hover:border-brand-500/40 hover:shadow-xl hover:shadow-brand-500/5 transition-all duration-300"
            >
              <div class="flex items-center justify-between">
                <span class="px-2 py-0.5 rounded-md text-[9px] font-black uppercase tracking-widest border-2 bg-black text-white border-black">
                  {{ alert.asset }}
                </span>
                <span class="text-[9px] text-slate-900 font-black">
                  {{ alert.timestamp }}
                </span>
              </div>
              <div class="h-32 overflow-hidden border-b border-slate-100 mb-2">
                <div class="text-sm text-black line-clamp-5 leading-relaxed font-bold">
                  {{ alert.message }}
                </div>
              </div>
              <div class="text-xs text-slate-600">
                {{ alert.suggestion }}
              </div>
            </div>
          </div>
          <div v-if="allAlerts.length === 0" class="col-span-full h-80 flex flex-col items-center justify-center text-slate-200 gap-4">
            <span class="text-5xl opacity-20">📊</span>
            <p class="text-xs uppercase tracking-[0.2em] font-black text-slate-300">No Alerts Found</p>
          </div>
        </div>

        <!-- Gurus Tab -->
        <div v-else-if="activeTab === 'gurus'" class="space-y-6">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-lg font-bold text-slate-900">大佬观点</h3>
            <button
              @click="fetchGuruViews"
              :disabled="guruLoading"
              class="px-4 py-2 bg-slate-900 text-white rounded-xl text-sm font-bold hover:bg-slate-800 transition-colors disabled:opacity-50"
            >
              {{ guruLoading ? '刷新中...' : '🔄 刷新' }}
            </button>
          </div>
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <div
              v-for="(guru, idx) in guruViews"
              :key="idx"
              class="bg-white border border-slate-200 rounded-2xl p-6 hover:shadow-lg transition-shadow"
            >
              <div class="flex items-center gap-4 mb-4">
                <div class="w-12 h-12 bg-gradient-to-br from-brand-500 to-purple-500 rounded-full flex items-center justify-center text-white text-xl font-bold">
                  {{ guru.name?.[0] || '?' }}
                </div>
                <div>
                  <h4 class="font-bold text-slate-900">{{ guru.name }}</h4>
                  <p class="text-sm text-slate-500">{{ guru.title }}</p>
                </div>
              </div>
              <p class="text-slate-700 leading-relaxed">
                {{ guru.view || guru.latest_view || guru.content }}
              </p>
              <div v-if="guru.date" class="mt-4 text-xs text-slate-400">
                {{ guru.date }}
              </div>
            </div>
          </div>
        </div>

        <!-- Chat Tab -->
        <div v-else-if="activeTab === 'chat'" class="h-full flex flex-col">
          <!-- Simplified Chat Interface -->
          <div class="flex-1 flex flex-col bg-white border border-slate-200 rounded-2xl overflow-hidden">
            <div class="p-4 border-b border-slate-200 bg-slate-50">
              <div class="flex items-center gap-3">
                <div class="w-10 h-10 bg-slate-900 rounded-xl flex items-center justify-center text-white text-xl">
                  🤖
                </div>
                <div>
                  <h3 class="font-bold text-slate-900">AI 分析</h3>
                  <p class="text-xs text-slate-500">基于当前市场信息，为你提供专业分析</p>
                </div>
                <div class="ml-auto">
                  <div class="flex items-center gap-2">
                    <div class="w-2 h-2 rounded-full bg-green-500"></div>
                    <span class="text-xs text-slate-500">在线</span>
                  </div>
                </div>
              </div>
            </div>
            
            <div ref="chatMessagesRef" class="flex-1 overflow-y-auto p-4 space-y-4">
              <div v-if="chatMessages.length === 0" class="flex flex-col items-center justify-center h-full text-slate-400 gap-4">
                <span class="text-4xl">💬</span>
                <div class="text-center">
                  <p class="text-base font-medium text-slate-700">有什么问题想问我吗？</p>
                  <p class="text-sm text-slate-500">试试问我关于黄金、白银或地缘政治的问题</p>
                </div>
              </div>
              <div v-for="(msg, idx) in chatMessages" :key="idx" :class="['chat-widget-message', msg.role]">
                {{ msg.content }}
              </div>
            </div>
            
            <div class="p-4 border-t border-slate-200 bg-slate-50">
              <div class="flex gap-3">
                <input
                  v-model="chatInput"
                  @keyup.enter="sendChatMessage"
                  :disabled="chatLoading"
                  placeholder="输入你的问题..."
                  class="flex-1 px-4 py-3 border border-slate-200 bg-white rounded-xl text-base focus:outline-none focus:border-slate-400 transition-all"
                />
                <button
                  @click="sendChatMessage"
                  :disabled="chatLoading"
                  class="px-5 py-3 bg-slate-900 text-white rounded-xl text-base font-medium hover:bg-slate-800 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {{ chatLoading ? '思考中...' : '发送' }}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, nextTick, onUnmounted, watch } from 'vue'
import * as LightweightCharts from 'lightweight-charts'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

// ==========================================
// 策略模式 (Strategy Pattern) - 导航配置
// ==========================================
const navigationTabs = [
  { id: 'dashboard', label: '情报总览', icon: '📊' },
  { id: 'chat', label: 'AI 分析', icon: '💬' },
  { id: 'map', label: '地缘情报', icon: '🌍' },
  { id: 'alerts', label: '预警情报', icon: '⚠️' },
  { id: 'gurus', label: '专家观点', icon: '🧠' },
]

// ==========================================
// 单例模式 (Singleton Pattern) - 图表管理器
// ==========================================
class ChartManager {
  static instance = null
  
  static getInstance() {
    if (!ChartManager.instance) {
      ChartManager.instance = {
        chartInstance: null,
        candlestickSeries: null,
        containerRef: null
      }
    }
    return ChartManager.instance
  }
  
  static reset() {
    if (ChartManager.instance?.chartInstance) {
      ChartManager.instance.chartInstance.remove()
    }
    ChartManager.instance = null
  }
}

// ==========================================
// 单例模式 (Singleton Pattern) - 地图管理器
// ==========================================
class MapManager {
  static instance = null
  
  static getInstance() {
    if (!MapManager.instance) {
      MapManager.instance = {
        mapInstance: null,
        containerRef: null
      }
    }
    return MapManager.instance
  }
  
  static reset() {
    if (MapManager.instance?.mapInstance) {
      MapManager.instance.mapInstance.remove()
    }
    MapManager.instance = null
  }
}

// ==========================================
// 状态管理
// ==========================================
const activeTab = ref('dashboard')
const sidebarOpen = ref(true)
const selectedAsset = ref('gold')
const priceLoading = ref(false)
const guruViews = ref([])
const guruLoading = ref(false)
const allAlerts = ref([])
const stats = ref({ total: 0 })
const loading = ref(false)
const refreshing = ref(false)
const middleEastScenarios = ref([])
const scenariosLoading = ref(false)
const selectedScenarioIndex = ref(null)
const lastUpdateTime = ref('')
const chatInput = ref('')
const chatMessages = ref([])
const chatLoading = ref(false)
const chatMessagesRef = ref(null)
const chartContainerRef = ref(null)
const mapContainerRef = ref(null)

// 定时器引用
let priceRefreshInterval = null
let guruRefreshInterval = null
let scenariosRefreshInterval = null

const priceData = ref({
  gold: { symbol: 'XAUUSD', data: [], latest: null },
  silver: { symbol: 'XAGUSD', data: [], latest: null },
  crude_oil: { symbol: 'CL', data: [], latest: null },
  brent_crude: { symbol: 'CO', data: [], latest: null },
})

// Middle East Hotspots
const middleEastHotspots = [
  { name: '伊朗', lat: 32.4279, lng: 53.6880, risk: 'high' },
  { name: '以色列', lat: 31.0461, lng: 34.8516, risk: 'high' },
  { name: '黎巴嫩', lat: 33.8547, lng: 35.8623, risk: 'high' },
  { name: '叙利亚', lat: 34.8021, lng: 38.9968, risk: 'high' },
  { name: '伊拉克', lat: 33.2232, lng: 43.6793, risk: 'medium' },
  { name: '沙特阿拉伯', lat: 23.8859, lng: 45.0792, risk: 'medium' },
  { name: '阿联酋', lat: 23.4241, lng: 53.8478, risk: 'low' },
  { name: '卡塔尔', lat: 25.3548, lng: 51.1839, risk: 'low' },
  { name: '科威特', lat: 29.3117, lng: 47.4818, risk: 'medium' },
  { name: '巴林', lat: 26.0667, lng: 50.5577, risk: 'low' },
  { name: '阿曼', lat: 21.5126, lng: 55.9233, risk: 'low' },
  { name: '也门', lat: 15.5527, lng: 48.5164, risk: 'medium' },
  { name: '约旦', lat: 30.5852, lng: 36.2384, risk: 'medium' },
  { name: '埃及', lat: 26.8206, lng: 30.8025, risk: 'low' },
  { name: '土耳其', lat: 38.9637, lng: 35.2433, risk: 'low' },
  { name: '霍尔木兹海峡', lat: 26.5600, lng: 56.5000, risk: 'high' },
]

// ==========================================
// 计算属性
// ==========================================
const currentTabLabel = computed(() => {
  const labelMap = {
    'dashboard': '情报总览',
    'chat': 'AI 分析',
    'map': '地缘情报',
    'alerts': '预警情报',
    'gurus': '专家观点'
  }
  return labelMap[activeTab.value]?.toUpperCase() || 'INTELLIGENCE'
})

const priceChange = computed(() => {
  const changes = {}
  for (const asset of ['gold', 'silver', 'crude_oil']) {
    const data = priceData.value[asset]
    if (!data.latest || data.data.length < 2) {
      changes[asset] = null
      continue
    }
    const prevClose = data.data[data.data.length - 2].close
    const change = data.latest.close - prevClose
    const changePct = (change / prevClose) * 100
    changes[asset] = {
      value: change,
      pct: changePct,
      direction: change >= 0 ? 'up' : 'down'
    }
  }
  return changes
})

const currentPrice = computed(() => {
  const data = priceData.value[selectedAsset.value]
  return data.latest ? data.latest.close : null
})

const recentAlerts = computed(() => {
  return allAlerts.value.slice(0, 5)
})

// ==========================================
// 工具函数
// ==========================================
const formatPrice = (price) => {
  if (price == null) return '-'
  return price.toFixed(2)
}

const selectScenario = (index) => {
  selectedScenarioIndex.value = selectedScenarioIndex.value === index ? null : index
}

// ==========================================
// 工厂方法 (Factory Method) - 初始化图表
// ==========================================
const initChart = () => {
  const container = chartContainerRef.value
  if (!container) {
    console.warn('Chart container not found')
    return
  }

  const manager = ChartManager.getInstance()
  
  if (manager.chartInstance) {
    manager.chartInstance.remove()
  }

  manager.containerRef = container
  manager.chartInstance = LightweightCharts.createChart(container, {
    layout: {
      background: { type: 'solid', color: '#f8fafc' },
      textColor: '#0f172a',
    },
    grid: {
      vertLines: { color: '#e2e8f0' },
      horzLines: { color: '#e2e8f0' },
    },
    priceScale: {
      borderColor: '#cbd5e1',
    },
    timeScale: {
      borderColor: '#cbd5e1',
    },
  })

  manager.candlestickSeries = manager.chartInstance.addCandlestickSeries({
    upColor: '#10b981',
    downColor: '#ef4444',
    borderVisible: false,
    wickUpColor: '#10b981',
    wickDownColor: '#ef4444',
  })

  updateChart()

  const resizeObserver = new ResizeObserver(() => {
    manager.chartInstance.applyAutoSize()
  })
  resizeObserver.observe(container)
}

const updateChart = () => {
  const manager = ChartManager.getInstance()
  if (!manager.candlestickSeries || !manager.chartInstance) return
  
  const data = priceData.value[selectedAsset.value].data.map(item => ({
    time: item.time,
    open: item.open,
    high: item.high,
    low: item.low,
    close: item.close,
  }))
  manager.candlestickSeries.setData(data)
  manager.chartInstance.timeScale().fitContent()
}

// ==========================================
// 工厂方法 (Factory Method) - 初始化地图
// ==========================================
const initMap = () => {
  const container = mapContainerRef.value
  if (!container) {
    console.warn('Map container not found')
    return
  }

  const manager = MapManager.getInstance()
  
  if (manager.mapInstance) {
    manager.mapInstance.remove()
  }

  manager.containerRef = container
  manager.mapInstance = L.map(container).setView([20.0, 0.0], 1.5)

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors',
    maxZoom: 18
  }).addTo(manager.mapInstance)

  middleEastHotspots.forEach(hotspot => {
    const color = hotspot.risk === 'high' ? '#ef4444' :
                  hotspot.risk === 'medium' ? '#f59e0b' : '#10b981'

    const circle = L.circle([hotspot.lat, hotspot.lng], {
      color: color,
      fillColor: color,
      fillOpacity: 0.3,
      radius: hotspot.risk === 'high' ? 150000 :
              hotspot.risk === 'medium' ? 100000 : 50000
    }).addTo(manager.mapInstance)

    const marker = L.marker([hotspot.lat, hotspot.lng]).addTo(manager.mapInstance)
    marker.bindPopup(`<b>${hotspot.name}</b><br>风险等级: ${hotspot.risk === 'high' ? '高' : hotspot.risk === 'medium' ? '中' : '低'}`)
  })
}

// ==========================================
// 策略模式 (Strategy Pattern) - 资产切换
// ==========================================
const switchAsset = async (asset) => {
  selectedAsset.value = asset
  await nextTick()
  if (priceData.value[asset].data.length === 0) {
    await fetchPrice(asset)
  }
  await nextTick()
  initChart()
}

// ==========================================
// 数据获取
// ==========================================
const refreshScenarios = async () => {
  scenariosLoading.value = true
  await fetchMiddleEastScenarios()
  scenariosLoading.value = false
}

const fetchMiddleEastScenarios = async () => {
  try {
    const res = await fetch('/api/middle-east-scenarios')
    const data = await res.json()
    if (data.success) {
      middleEastScenarios.value = data.data
      lastUpdateTime.value = new Date().toLocaleString('zh-CN')
    }
  } catch (e) {
    console.error('Failed to fetch Middle East scenarios:', e)
    middleEastScenarios.value = [
      {
        name: '维持现状 (Status Quo)',
        type: 'status-quo',
        probability: 0.55,
        gold_price_range: '4800-5100',
        silver_price_range: '74-78',
        crude_price_range: '95-105',
        suggested_action: 'wait',
        action_text: '观望持有',
        trigger_signals: ['伊朗局势保持稳定']
      },
      {
        name: '局势缓和 (De-escalation)',
        type: 'de-escalation',
        probability: 0.2,
        gold_price_range: '4600-4900',
        silver_price_range: '71-75',
        crude_price_range: '88-98',
        suggested_action: 'sell',
        action_text: '减持黄金',
        trigger_signals: ['地缘紧张局势缓解']
      },
      {
        name: '局势升级 (Escalation)',
        type: 'escalation',
        probability: 0.2,
        gold_price_range: '5100-5400',
        silver_price_range: '78-83',
        crude_price_range: '105-115',
        suggested_action: 'buy',
        action_text: '增持黄金',
        trigger_signals: ['伊朗革命卫队发动军事行动']
      },
      {
        name: '重大危机 (Major Crisis)',
        type: 'major-crisis',
        probability: 0.05,
        gold_price_range: '5400-5900',
        silver_price_range: '83-92',
        crude_price_range: '115-130',
        suggested_action: 'buy',
        action_text: '重仓做多',
        trigger_signals: ['中东地区爆发大规模战争']
      }
    ]
  }
}

const fetchGuruViews = async () => {
  guruLoading.value = true
  try {
    const res = await fetch('/api/guru-views')
    const data = await res.json()
    if (data.success) {
      guruViews.value = data.data
    } else {
      guruViews.value = [
        { name: 'Peter Schiff', title: '金虫之王', view: '黄金是唯一的真正货币，美联储印钞将导致金价飙升。', date: '2026-03-19' },
        { name: 'Ray Dalio', title: '桥水创始人', view: '在动荡时期，黄金是投资组合的重要组成部分。', date: '2026-03-18' },
        { name: 'Jim Rickards', title: '货币战争作者', view: '地缘政治风险上升，黄金将迎来重要机会。', date: '2026-03-17' },
        { name: '谢爱民', title: '闪电资管', view: '国内经济复苏，贵金属有望迎来阶段性行情。', date: '2026-03-16' },
        { name: '张明', title: '社科院金融所', view: '全球货币政策转向，黄金配置价值凸显。', date: '2026-03-15' },
      ]
    }
  } catch (e) {
    console.error('Failed to fetch guru views:', e)
  } finally {
    guruLoading.value = false
  }
}

const fetchData = async () => {
  loading.value = true
  refreshing.value = true
  try {
    const resAlerts = await fetch('/api/alerts')
    const dataAlerts = await resAlerts.json()
    allAlerts.value = dataAlerts.alerts || []

    const resStats = await fetch('/api/stats')
    const dataStats = await resStats.json()
    stats.value = dataStats

    await fetchGuruViews()
  } catch (e) {
    console.error('Failed to fetch data:', e)
  } finally {
    loading.value = false
    refreshing.value = false
  }
}

const fetchPrice = async (asset) => {
  const symbolMap = {
    gold: 'XAUUSD',
    silver: 'XAGUSD',
    crude_oil: 'CL',
    brent_crude: 'CO'
  }
  const symbol = symbolMap[asset]
  priceLoading.value = true
  try {
    const res = await fetch(`/api/price/${symbol}`)
    const data = await res.json()
    if (!data.error && data.data) {
      priceData.value[asset].data = data.data
      priceData.value[asset].latest = data.latest
    } else {
      const now = Math.floor(Date.now() / 1000)
      const mockData = []
      let basePrice = asset === 'gold' ? 5000 : asset === 'silver' ? 75 : 100
      for (let i = 100; i >= 0; i--) {
        const time = now - i * 86400
        const change = (Math.random() - 0.5) * (asset === 'gold' ? 50 : asset === 'silver' ? 2 : 5)
        basePrice += change
        mockData.push({
          time: time,
          open: basePrice - Math.random() * 10,
          high: basePrice + Math.random() * 15,
          low: basePrice - Math.random() * 15,
          close: basePrice,
          volume: Math.floor(Math.random() * 1000000)
        })
      }
      priceData.value[asset].data = mockData
      priceData.value[asset].latest = mockData[mockData.length - 1]
    }
  } catch (e) {
    console.error('Failed to fetch price:', e)
  } finally {
    priceLoading.value = false
  }
}

const sendChatMessage = async () => {
  if (!chatInput.value.trim()) return

  const userMessage = chatInput.value
  chatMessages.value.push({
    role: 'user',
    content: userMessage
  })
  chatInput.value = ''
  chatLoading.value = true

  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: userMessage,
        context: {
          middleEastScenarios: middleEastScenarios.value,
          guruViews: guruViews.value,
          recentAlerts: recentAlerts.value,
          currentPrice: currentPrice.value
        }
      })
    })

    const data = await res.json()

    if (data.success) {
      chatMessages.value.push({
        role: 'assistant',
        content: data.message
      })
    } else {
      chatMessages.value.push({
        role: 'assistant',
        content: '你好！我是黄金白银 AI 助手。我可以帮你分析市场、解读预警、或者回答任何相关问题。请问有什么可以帮你的吗？'
      })
    }
  } catch (e) {
    console.error('Chat failed:', e)
    chatMessages.value.push({
      role: 'assistant',
      content: '抱歉，发生了错误，请稍后再试。'
    })
  } finally {
    chatLoading.value = false
    await nextTick()
    if (chatMessagesRef.value) {
      chatMessagesRef.value.scrollTop = chatMessagesRef.value.scrollHeight
    }
  }
}

// ==========================================
// 策略模式 (Strategy Pattern) - 标签页切换策略
// ==========================================
watch(activeTab, async (newTab) => {
  await nextTick()
  await nextTick()
  
  if (newTab === 'map' && mapContainerRef.value) {
    initMap()
  } else if (newTab === 'dashboard' && chartContainerRef.value) {
    initChart()
  }
})

// ==========================================
// 实时刷新功能
// ==========================================
const startPriceRefresh = () => {
  if (priceRefreshInterval) return
  
  // 每30秒刷新一次价格
  priceRefreshInterval = setInterval(async () => {
    for (const asset of ['gold', 'silver', 'crude_oil']) {
      await fetchPrice(asset)
    }
  }, 30000)
}

const startGuruRefresh = () => {
  if (guruRefreshInterval) return
  
  // 每4小时刷新一次大佬观点
  guruRefreshInterval = setInterval(async () => {
    await fetchGuruViews()
  }, 4 * 60 * 60 * 1000)
}

const startScenariosRefresh = () => {
  if (scenariosRefreshInterval) return
  
  // 每10分钟刷新一次地缘事件
  scenariosRefreshInterval = setInterval(async () => {
    await fetchMiddleEastScenarios()
  }, 10 * 60 * 1000)
}

const stopAllRefresh = () => {
  if (priceRefreshInterval) {
    clearInterval(priceRefreshInterval)
    priceRefreshInterval = null
  }
  if (guruRefreshInterval) {
    clearInterval(guruRefreshInterval)
    guruRefreshInterval = null
  }
  if (scenariosRefreshInterval) {
    clearInterval(scenariosRefreshInterval)
    scenariosRefreshInterval = null
  }
}

// ==========================================
// 生命周期
// ==========================================
onMounted(async () => {
  await fetchData()
  await fetchMiddleEastScenarios()
  await nextTick()
  await nextTick()
  await switchAsset('gold')
  
  // 启动实时刷新
  startPriceRefresh()
  startGuruRefresh()
  startScenariosRefresh()
})

onUnmounted(() => {
  stopAllRefresh()
  ChartManager.reset()
  MapManager.reset()
})
</script>

