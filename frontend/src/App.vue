<template>
  <div class="app-container">
    <!-- 左侧主内容区 -->
    <main class="main-content">
      <!-- 顶部导航栏 -->
      <header class="top-header">
        <div class="header-left">
          <h1 class="app-title">gold-silver-finance-agent</h1>
        </div>
        <div class="header-right">
          <a href="https://github.com/hotpot-killer/gold-silver-finance-agent" target="_blank" class="github-link">
            访问项目主页
          </a>
        </div>
      </header>

      <!-- 内容区 -->
      <div class="content-area">
        <!-- 仪表盘区域 -->
        <div class="dashboard-section-main">
          <!-- Hero 区域 -->
          <section class="hero-section">
            <div class="hero-content">
              <div class="hero-tag-row">
                <span class="hero-tag">黄金白银专用金融分析引擎</span>
                <span class="version-text">/ v1.0</span>
              </div>
              
              <h2 class="hero-title">
                实时市场数据分析<br>
                <span class="gradient-text">智能推演未来</span>
              </h2>
              
              <p class="hero-desc">
                基于最新新闻和价格信号，gold-silver-finance-agent 自动生成多智能体推演。
                通过中东局势沙盘、大佬观点和市场预警，在复杂环境中寻找<span class="gradient-text">“最优决策”</span>
              </p>
            </div>
          </section>

          <!-- 全球地缘政治风险地图 -->
          <div class="sandbox-section">
            <div class="sandbox-header">
              <div class="sandbox-title">
                🌍 全球地缘政治风险地图
              </div>
              <div class="sandbox-controls">
                <span class="sandbox-update-time">
                  更新于: {{ lastUpdateTime }}
                </span>
                <button class="sandbox-refresh-btn" @click="refreshScenarios" :disabled="scenariosLoading">
                  {{ scenariosLoading ? '刷新中...' : '🔄 刷新' }}
                </button>
              </div>
            </div>
            
            <!-- 交互式地图 -->
            <div class="map-section">
              <div id="middle-east-map" class="map-container"></div>
              <div class="map-legend">
                <div class="legend-title">热点图例</div>
                <div class="legend-item">
                  <span class="legend-dot legend-high"></span>
                  <span>高风险区域</span>
                </div>
                <div class="legend-item">
                  <span class="legend-dot legend-medium"></span>
                  <span>中风险区域</span>
                </div>
                <div class="legend-item">
                  <span class="legend-dot legend-low"></span>
                  <span>低风险区域</span>
                </div>
              </div>
            </div>
            
            <!-- 情景卡片 -->
            <div class="sandbox-grid">
              <div 
                v-for="(s, index) in middleEastScenarios" 
                :key="s.name"
                :class="getScenarioCardClass(s.type)"
                class="sandbox-card-interactive"
                @click="selectScenario(index)"
                :data-selected="selectedScenarioIndex === index"
              >
                <div class="sandbox-card-header">
                  <div class="sandbox-card-name">
                    <span class="scenario-number">#{{ index + 1 }}</span>
                    {{ s.name }}
                  </div>
                  <div :class="getProbClass(s.probability)">
                    {{ (s.probability * 100).toFixed(0) }}%
                  </div>
                </div>
                
                <div class="sandbox-card-body">
                  <div class="price-grid">
                    <div class="price-item">
                      <span class="price-label">🥇 黄金</span>
                      <span class="price-value">{{ s.gold_price_range }}</span>
                    </div>
                    <div class="price-item">
                      <span class="price-label">🥈 白银</span>
                      <span class="price-value">{{ s.silver_price_range }}</span>
                    </div>
                    <div class="price-item">
                      <span class="price-label">🛢️ 原油</span>
                      <span class="price-value">{{ s.crude_price_range }}</span>
                    </div>
                  </div>
                </div>
                
                <div class="sandbox-card-action-row">
                  <div :class="['sandbox-card-action', s.suggested_action]">
                    {{ s.action_text }}
                  </div>
                </div>
                
                <div class="sandbox-triggers">
                  <div class="triggers-title">⚠️ 触发信号</div>
                  <div v-for="t in s.trigger_signals" :key="t" class="sandbox-trigger">
                    {{ t }}
                  </div>
                </div>
              </div>
            </div>
            
            <!-- 情景详情面板 -->
            <div v-if="selectedScenarioIndex !== null" class="scenario-detail-panel">
              <div class="detail-header">
                <h3 class="detail-title">情景分析 #{{ selectedScenarioIndex + 1 }}</h3>
                <button class="detail-close-btn" @click="selectedScenarioIndex = null">×</button>
              </div>
              <div class="detail-content">
                <div class="detail-section">
                  <span class="detail-label">情景名称</span>
                  <span class="detail-value">{{ middleEastScenarios[selectedScenarioIndex]?.name }}</span>
                </div>
                <div class="detail-section">
                  <span class="detail-label">发生概率</span>
                  <span class="detail-value">{{ (middleEastScenarios[selectedScenarioIndex]?.probability * 100).toFixed(0) }}%</span>
                </div>
                <div class="detail-section">
                  <span class="detail-label">建议操作</span>
                  <span :class="['detail-action', middleEastScenarios[selectedScenarioIndex]?.suggested_action]">
                    {{ middleEastScenarios[selectedScenarioIndex]?.action_text }}
                  </span>
                </div>
              </div>
            </div>
          </div>

          <!-- 仪表盘统计 -->
          <div class="dashboard-section">
            <div class="dashboard-stats">
              <div class="stat-card">
                <div class="stat-number">{{ stats.total }}</div>
                <div class="stat-label">历史总预警</div>
              </div>
              <div class="stat-card">
                <div class="stat-number">{{ last24hAlertsCount }}</div>
                <div class="stat-label">24小时预警</div>
              </div>
              <div class="stat-card">
                <div class="stat-number">{{ last7dAlertsCount }}</div>
                <div class="stat-label">近7天预警</div>
              </div>
              <div class="stat-card">
                <div v-if="currentPrice" class="stat-number">{{ formatPrice(currentPrice) }}</div>
                <div v-else class="stat-number">-</div>
                <div class="stat-label">当前 {{ 
                  selectedAsset === 'gold' ? '黄金' : 
                  selectedAsset === 'silver' ? '白银' : 
                  selectedAsset === 'crude_oil' ? 'WTI原油' : 
                  '布伦特原油' }} 价格</div>
              </div>
            </div>

            <!-- 大佬观点 -->
            <div class="recent-alerts-card" style="margin-bottom: 32px;">
              <div class="card-title">🤔 知名宏观大佬最新黄金观点</div>
              <div v-if="guruLoading" style="text-align:center; padding:20px; color:var(--text-muted);">加载中...</div>
              <div v-else style="display:grid; grid-template-columns: repeat(auto-fit, minmax(360px, 1fr)); gap:20px;">
                <div v-for="guru in guruViews" :key="guru.name" style="border:1px solid var(--border); border-radius:12px; padding:20px; background: linear-gradient(135deg, rgba(30,41,59,0.95) 0%, rgba(15,23,42,0.95) 100%);">
                  <div style="font-size:1.1rem; font-weight:700; color:var(--primary);">{{ guru.name }}</div>
                  <div style="font-size:0.85rem; color:var(--text-muted); margin-bottom:10px;">{{ guru.title }}</div>
                  <div style="font-size:0.95rem; line-height:1.6; color:var(--text-secondary);">📝 最新 ({{ guru.updated_at }}): {{ guru.latest_view }}</div>
                  <span :style="guru.tone === 'bullish' ? 'background:rgba(16,185,129,0.2); color:#34d399; border:1px solid rgba(16,185,129,0.3);' : guru.tone === 'bearish' ? 'background:rgba(239,68,68,0.2); color:#f87171; border:1px solid rgba(239,68,68,0.3);' : 'background:rgba(245,158,11,0.2); color:#fbbf24; border:1px solid rgba(245,158,11,0.3);'" style="display:inline-block; font-size:0.78rem; padding:4px 12px; border-radius:20px; font-weight:600; margin-top:10px;">
                    {{ guru.tone === 'bullish' ? '看多' : guru.tone === 'bearish' ? '看空' : '中性' }}
                  </span>
                </div>
              </div>
            </div>

            <div class="recent-alerts-card">
              <div class="card-title">⏱️ 最近触发的预警</div>
              <div v-if="hasRecentAlerts">
                <div class="recent-alert-item" v-for="alert in recentAlerts" :key="alert.timestamp + alert.name">
                  <div class="recent-alert-header">
                    <span class="recent-alert-name">{{ alert.name }}</span>
                    <span :class="getTypeBadgeClass(alert.type)" style="display:inline-block">{{ alert.type }}</span>
                    <span class="badge badge-asset">{{ alert.asset }}</span>
                  </div>
                  <div class="recent-alert-message">{{ alert.message }}</div>
                  <div class="recent-alert-time">{{ alert.timestamp }}</div>
                </div>
              </div>
              <div v-else class="empty-recent">暂无预警记录</div>
            </div>
          </div>

          <!-- 价格和K线图 -->
          <div class="price-section">
            <div class="price-tabs">
              <div 
                class="price-tab" 
                :class="{ active: selectedAsset === 'gold' }"
                @click="switchAsset('gold')"
              >
                黄金 (XAUUSD)
              </div>
              <div 
                class="price-tab" 
                :class="{ active: selectedAsset === 'silver' }"
                @click="switchAsset('silver')"
              >
                白银 (XAGUSD)
              </div>
              <div 
                class="price-tab" 
                :class="{ active: selectedAsset === 'crude_oil' }"
                @click="switchAsset('crude_oil')"
              >
                WTI原油 (CL)
              </div>
              <div 
                class="price-tab" 
                :class="{ active: selectedAsset === 'brent_crude' }"
                @click="switchAsset('brent_crude')"
              >
                布伦特原油 (CO)
              </div>
            </div>
            
            <div v-if="priceLoading" class="price-loading">加载价格数据中...</div>
            <div v-else>
              <div class="current-price-card">
                <div class="current-price">{{ formatPrice(currentPrice) }}</div>
                <div v-if="priceChange" :class="['price-change', priceChange.direction]">
                  {{ priceChange.direction === 'up' ? '↑' : '↓' }} 
                  {{ formatPrice(Math.abs(priceChange.value)) }} 
                  ({{ formatPrice(Math.abs(priceChange.pct)) }}%)
                </div>
              </div>
              <div id="kline-chart" class="kline-container"></div>
            </div>
          </div>
        </div>
      </div>

      <!-- 页脚 -->
      <footer class="app-footer">
        <p>gold-silver-finance-agent | 黄金白银 AI 智能监控 · 专业金融分析平台</p>
      </footer>
    </main>

    <!-- 右侧导航栏 -->
    <aside class="sidebar">
      <div class="sidebar-brand">
        <div class="brand-icon">💰</div>
        <span class="brand-text">金融分析</span>
      </div>

      <nav class="sidebar-nav">
        <div class="sidebar-section">
          <div class="sidebar-section-title">核心功能</div>
          <div class="sidebar-item active">
            <span class="sidebar-icon">📊</span>
            <span class="sidebar-label">市场分析</span>
          </div>
        </div>
        
        <div class="sidebar-section" style="margin-top: 24px;">
          <div class="sidebar-section-title">AI 助手</div>
          
          <!-- 聊天窗口 -->
          <div class="chat-widget">
            <div class="chat-widget-header">
              <span class="chat-widget-title">🤖 快速对话</span>
            </div>
            
            <div class="chat-widget-messages" ref="chatMessagesRef">
              <div v-if="chatMessages.length === 0" class="chat-widget-empty">
                问我任何问题...
              </div>
              <div 
                v-for="(msg, i) in chatMessages" 
                :key="i" 
                :class="['chat-widget-message', msg.role]"
              >
                {{ msg.content }}
              </div>
            </div>
            
            <div class="chat-widget-input-area">
              <input 
                type="text" 
                class="chat-widget-input" 
                v-model="chatInput" 
                placeholder="输入问题..."
                @keyup.enter="sendChatMessage"
                :disabled="chatLoading"
              />
              <button 
                class="chat-widget-send-btn" 
                @click="sendChatMessage"
                :disabled="chatLoading"
              >
                {{ chatLoading ? '...' : '→' }}
              </button>
            </div>
          </div>
        </div>
      </nav>

      <div class="sidebar-footer">
        <div class="status-indicator">
          <div class="status-dot"></div>
          <span class="status-text">系统在线</span>
        </div>
      </div>
    </aside>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, nextTick, onUnmounted } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

const allAlerts = ref([])
const stats = ref({
  total: 0,
  by_asset: {},
  by_signal_type: {}
})
const loading = ref(true)
const refreshing = ref(false)

const filterAsset = ref('')
const filterType = ref('')
const pageSize = ref(20)
const currentPage = ref(1)
const selectedAsset = ref('gold')
const priceLoading = ref(false)
const guruViews = ref([])
const guruLoading = ref(false)
const priceData = ref({
  gold: { symbol: 'XAUUSD', data: [], latest: null },
  silver: { symbol: 'XAGUSD', data: [], latest: null },
  crude_oil: { symbol: 'CL', data: [], latest: null },
  brent_crude: { symbol: 'CO', data: [], latest: null },
})
let chartInstance = null
let candlestickSeries = null
let mapInstance = null

const chatInput = ref('')
const chatMessages = ref([])
const chatLoading = ref(false)
const chatMessagesRef = ref(null)
const middleEastScenarios = ref([])
const scenariosLoading = ref(false)
const selectedScenarioIndex = ref(null)
const lastUpdateTime = ref('')

// 中东热点位置
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

const refreshScenarios = async () => {
  scenariosLoading.value = true
  await fetchMiddleEastScenarios()
  scenariosLoading.value = false
}

const selectScenario = (index) => {
  if (selectedScenarioIndex.value === index) {
    selectedScenarioIndex.value = null
  } else {
    selectedScenarioIndex.value = index
  }
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
  }
}

const initMap = () => {
  const container = document.getElementById('middle-east-map')
  if (!container) return
  
  if (mapInstance) {
    mapInstance.remove()
  }
  
  // 初始化地图，中心在世界视图
  mapInstance = L.map('middle-east-map').setView([20.0, 0.0], 2)
  
  // 添加 OpenStreetMap 瓦片层
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors',
    maxZoom: 18
  }).addTo(mapInstance)
  
  // 添加热点标记
  middleEastHotspots.forEach(hotspot => {
    const color = hotspot.risk === 'high' ? '#ef4444' : 
                  hotspot.risk === 'medium' ? '#f59e0b' : '#10b981'
    
    const circle = L.circle([hotspot.lat, hotspot.lng], {
      color: color,
      fillColor: color,
      fillOpacity: 0.3,
      radius: hotspot.risk === 'high' ? 150000 : 
              hotspot.risk === 'medium' ? 100000 : 50000
    }).addTo(mapInstance)
    
    const marker = L.marker([hotspot.lat, hotspot.lng]).addTo(mapInstance)
    marker.bindPopup(`<b>${hotspot.name}</b><br>风险等级: ${hotspot.risk === 'high' ? '高' : hotspot.risk === 'medium' ? '中' : '低'}`)
  })
}

const fetchGuruViews = async () => {
  guruLoading.value = true
  try {
    const res = await fetch('/api/guru-views')
    const data = await res.json()
    if (data.success) {
      guruViews.value = data.data
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
    }
  } catch (e) {
    console.error('Failed to fetch price:', e)
  } finally {
    priceLoading.value = false
  }
}

const initChart = () => {
  const container = document.getElementById('kline-chart')
  if (!container) return
  
  if (chartInstance) {
    chartInstance.remove()
  }
  
  chartInstance = LightweightCharts.createChart(container, {
    layout: {
      background: { type: 'solid', color: '#020617' },
      textColor: '#cbd5e1',
    },
    grid: {
      vertLines: { color: '#1e293b' },
      horzLines: { color: '#1e293b' },
    },
    priceScale: {
      borderColor: '#334155',
    },
    timeScale: {
      borderColor: '#334155',
    },
  })
  
  candlestickSeries = chartInstance.addCandlestickSeries({
    upColor: '#ef4444',
    downColor: '#10b981',
    borderVisible: false,
    wickUpColor: '#ef4444',
    wickDownColor: '#10b981',
  })
  
  updateChart()
  chartInstance.timeScale().fitContent()
  
  const resizeObserver = new ResizeObserver(() => {
    chartInstance.applyAutoSize()
  })
  resizeObserver.observe(container)
}

const updateChart = () => {
  if (!candlestickSeries) return
  const data = priceData.value[selectedAsset.value].data.map(item => ({
    time: item.time,
    open: item.open,
    high: item.high,
    low: item.low,
    close: item.close,
  }))
  candlestickSeries.setData(data)
}

const switchAsset = async (asset) => {
  selectedAsset.value = asset
  await nextTick()
  if (priceData.value[asset].data.length === 0) {
    await fetchPrice(asset)
  }
  initChart()
}

const formatPrice = (price) => {
  if (price == null) return '-'
  return price.toFixed(2)
}

const priceChange = computed(() => {
  const data = priceData.value[selectedAsset.value]
  if (!data.latest || data.data.length < 2) return null
  const prevClose = data.data[data.data.length - 2].close
  const change = data.latest.close - prevClose
  const changePct = (change / prevClose) * 100
  return {
    value: change,
    pct: changePct,
    direction: change >= 0 ? 'up' : 'down'
  }
})

const currentPrice = computed(() => {
  const data = priceData.value[selectedAsset.value]
  return data.latest ? data.latest.close : null
})

const recentAlerts = computed(() => {
  return allAlerts.value.slice(0, 5)
})

const hasRecentAlerts = computed(() => {
  return recentAlerts.value.length > 0
})

const last24hAlertsCount = computed(() => {
  const now = new Date()
  const oneDayAgo = now.getTime() - 24 * 60 * 60 * 1000
  let count = 0
  allAlerts.value.forEach(alert => {
    const [datePart, timePart] = alert.timestamp.split(' ')
    const [year, month, day] = datePart.split('-')
    const [hour, minute] = timePart.split(':')
    const alertTime = new Date(year, month - 1, day, hour, minute).getTime()
    if (alertTime >= oneDayAgo) count++
  })
  return count
})

const last7dAlertsCount = computed(() => {
  const now = new Date()
  const sevenDaysAgo = now.getTime() - 7 * 24 * 60 * 60 * 1000
  let count = 0
  allAlerts.value.forEach(alert => {
    const [datePart, timePart] = alert.timestamp.split(' ')
    const [year, month, day] = datePart.split('-')
    const [hour, minute] = timePart.split(':')
    const alertTime = new Date(year, month - 1, day, hour, minute).getTime()
    if (alertTime >= sevenDaysAgo) count++
  })
  return count
})

const sendChatMessage = async () => {
  if (!chatInput.value.trim() || chatLoading.value) return
  
  chatMessages.value.push({
    role: 'user',
    content: chatInput.value
  })
  
  const userMessage = chatInput.value
  chatInput.value = ''
  chatLoading.value = true
  
  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
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
        content: '抱歉，发生了错误，请稍后再试。'
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

const getTypeBadgeClass = (type) => {
  return `badge badge-type-${type}`
}

const getScenarioCardClass = (type) => {
  if (type === 'major-crisis' || type === 'escalation') {
    return 'sandbox-card danger'
  }
  return 'sandbox-card'
}

const getProbClass = (prob) => {
  if (prob > 0.4) {
    return 'sandbox-card-prob'
  }
  return 'sandbox-card-prob high'
}

onMounted(async () => {
  await fetchData()
  await fetchMiddleEastScenarios()
  await switchAsset('gold')
  await nextTick()
  initMap()
})

onUnmounted(() => {
  if (mapInstance) {
    mapInstance.remove()
    mapInstance = null
  }
})
</script>
