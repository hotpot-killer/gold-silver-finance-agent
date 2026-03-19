const { createApp, ref, onMounted, computed, nextTick } = Vue

createApp({
  setup() {
    const allAlerts = ref([])
    const stats = ref({
      total: 0,
      by_asset: {},
      by_signal_type: {}
    })
    const loading = ref(true)
    const refreshing = ref(false)
    
    // 筛选条件
    const filterAsset = ref('')
    const filterType = ref('')
    
    // 分页
    const pageSize = ref(20)
    const currentPage = ref(1)
    
    // K线图相关
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
    
    // 中东局势沙盘数据
    const middleEastScenarios = ref([
      {
        name: '维持现状 (Status Quo)',
        type: 'status-quo',
        probability: 0.55,
        gold_price_range: '4800-5100',
        silver_price_range: '74-78',
        crude_price_range: '95-105',
        suggested_action: 'wait',
        action_text: '观望持有',
        trigger_signals: [
          '以色列与哈马斯停火协议继续生效',
          '伊朗不直接介入冲突',
          '霍尔木兹海峡航运正常'
        ]
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
        trigger_signals: [
          '中东多方达成长期和平协议',
          '美国解除对伊朗部分制裁',
          '也门胡塞武装停止袭击商船'
        ]
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
        trigger_signals: [
          '以色列扩大地面军事行动',
          '伊朗革命卫队直接参战',
          '霍尔木兹海峡航运受阻'
        ]
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
        trigger_signals: [
          '中东地区爆发全面战争',
          '美国直接军事介入',
          '霍尔木兹海峡完全封锁'
        ]
      }
    ])
    
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
        // 获取预警列表
        const resAlerts = await fetch('/api/alerts')
        const dataAlerts = await resAlerts.json()
        allAlerts.value = dataAlerts.alerts || []
        
        // 获取统计信息
        const resStats = await fetch('/api/stats')
        const dataStats = await resStats.json()
        stats.value = dataStats
        
        // 获取大佬观点
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
      
      // 销毁旧图表
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
      
      // 响应窗口大小变化
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
    
    // 仪表盘统计
    const recentAlerts = computed(() => {
      return allAlerts.value.slice(0, 5) // 最近5条预警
    })
    
    const hasRecentAlerts = computed(() => {
      return recentAlerts.value.length > 0
    })
    
    // 最近24小时预警数
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
    
    // 最近7天预警数
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
    
    onMounted(async () => {
      await fetchData()
      await switchAsset('gold')
    })
    
    // 资产选项列表
    const assetOptions = computed(() => {
      return Object.keys(stats.value.by_asset || {})
    })
    
    // 信号类型选项列表
    const typeOptions = computed(() => {
      return Object.keys(stats.value.by_signal_type || {})
    })
    
    // 筛选后的预警列表
    const filteredAlerts = computed(() => {
      let result = [...allAlerts.value]
      
      if (filterAsset.value) {
        result = result.filter(a => a.asset === filterAsset.value)
      }
      
      if (filterType.value) {
        result = result.filter(a => a.type === filterType.value)
      }
      
      return result
    })
    
    // 当前页显示的预警
    const paginatedAlerts = computed(() => {
      const start = 0
      const end = currentPage.value * pageSize.value
      return filteredAlerts.value.slice(start, end)
    })
    
    // 是否还有更多
    const hasMore = computed(() => {
      return paginatedAlerts.value.length < filteredAlerts.value.length
    })
    
    // 加载更多
    const loadMore = () => {
      currentPage.value++
    }
    
    // 刷新
    const refresh = async () => {
      currentPage.value = 1
      await fetchData()
      await fetchPrice(selectedAsset.value)
      initChart()
    }
    
    // 设置资产筛选
    const setFilterAsset = (asset) => {
      filterAsset.value = filterAsset.value === asset ? '' : asset
      currentPage.value = 1
    }
    
    // 设置类型筛选
    const setFilterType = (type) => {
      filterType.value = filterType.value === type ? '' : type
      currentPage.value = 1
    }
    
    // 获取badge class
    const getTypeBadgeClass = (type) => {
      return `badge badge-type-${type}`
    }
    
    // 获取情景卡片class
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
    
    // 滚动到底部（可选）
    const scrollToBottom = () => {
      window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' })
    }
    
    return {
      allAlerts,
      stats,
      loading,
      refreshing,
      guruViews,
      guruLoading,
      filterAsset,
      filterType,
      assetOptions,
      typeOptions,
      filteredAlerts,
      paginatedAlerts,
      hasMore,
      selectedAsset,
      currentPrice,
      priceChange,
      priceLoading,
      recentAlerts,
      hasRecentAlerts,
      last24hAlertsCount,
      last7dAlertsCount,
      getTypeBadgeClass,
      setFilterAsset,
      setFilterType,
      loadMore,
      refresh,
      switchAsset,
      formatPrice,
      middleEastScenarios,
      getScenarioCardClass,
      getProbClass,
      scrollToBottom
    }
  },
  template: `
    <div class="container">
      <!-- 顶部导航栏 - MiroFish 风格 -->
      <nav class="navbar">
        <div class="nav-brand">gold-silver-finance-agent</div>
        <div class="nav-links">
          <a href="https://github.com/your-github-repo" target="_blank" class="github-link">
            访问项目主页 <span class="arrow">↗</span>
          </a>
        </div>
      </nav>

      <!-- Hero 区域 - MiroFish 风格 -->
      <section class="hero-section">
        <div class="hero-left">
          <div class="decoration-square"></div>
          <div class="tag-row">
            <span class="orange-tag">黄金白银专用金融分析引擎</span>
            <span class="version-text">/ v1.0</span>
          </div>
          
          <h1 class="main-title">
            上传任意市场数据<br>
            <span class="gradient-text">即刻推演未来</span>
          </h1>
          
          <div class="hero-desc">
            <p>
              即使只有一段新闻或价格信号，<span class="gradient-text">gold-silver-finance-agent</span> 也能基于其中的现实种子，自动生成对应的多智能体推演。通过上帝视角注入变量，在复杂的市场环境中寻找<span class="gradient-text">“最优决策”</span>
            </p>
            <p class="slogan-text">
              让未来在数字沙盘中预演，让决策在百战模拟后胜出<span class="blinking-cursor">_</span>
            </p>
          </div>
        </div>
        
        <div class="hero-right">
          <!-- Logo/Emoji 区域 -->
          <div class="logo-container">
            <div class="hero-logo">🤖</div>
          </div>
          
          <button class="scroll-down-btn" @click="scrollToBottom" style="margin-top:24px; background:transparent; border:none; color:var(--text-muted); cursor:pointer; font-size:1.5rem;">
            ↓
          </button>
        </div>
      </section>

      <!-- 中东局势推演沙盘 - 核心重点，MiroFish 风格 -->
      <div class="sandbox-section">
        <div class="sandbox-title">
          🌍 中东局势推演沙盘
          <span style="font-size: 0.9rem; font-weight: 400; opacity: 0.8; margin-left: auto;">黄金价格最关键影响因素</span>
        </div>
        <div class="sandbox-grid">
          <div 
            v-for="s in middleEastScenarios" 
            :key="s.name"
            :class="getScenarioCardClass(s.type)"
          >
            <div class="sandbox-card-header">
              <div class="sandbox-card-name">{{ s.name }}</div>
              <div :class="getProbClass(s.probability)">{{ (s.probability * 100).toFixed(0) }}%</div>
            </div>
            <div class="sandbox-card-price">黄金: {{ s.gold_price_range }}</div>
            <div style="font-size: 0.9rem; color: var(--text-secondary); margin-bottom: 4px;">白银: {{ s.silver_price_range }}</div>
            <div style="font-size: 0.9rem; color: var(--text-secondary); margin-bottom: 12px;">原油: {{ s.crude_price_range }}</div>
            <div :class="['sandbox-card-action', s.suggested_action]">
              {{ s.action_text }}
            </div>
            <div class="sandbox-triggers">
              <div v-for="t in s.trigger_signals" :key="t" class="sandbox-trigger">
                {{ t }}
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 仪表盘概览 -->
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

        <!-- 知名宏观大佬最新观点 -->
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

      <!-- 价格和K线图区域 -->
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

      <!-- 筛选区 -->
      <div class="filters-section">
        <div class="filters-title">预警筛选</div>
        <div class="filters">
          <div class="filter-group" v-if="assetOptions.length > 0">
            <div class="filter-label">按资产</div>
            <div class="filter-buttons">
              <button 
                v-for="asset in assetOptions" 
                :key="asset"
                :class="['filter-btn', { active: filterAsset === asset }]"
                @click="setFilterAsset(asset)"
              >
                {{ asset }} ({{ stats.by_asset[asset] }})
              </button>
            </div>
          </div>
          
          <div class="filter-group" v-if="typeOptions.length > 0">
            <div class="filter-label">按预警类型</div>
            <div class="filter-buttons">
              <button 
                v-for="type in typeOptions" 
                :key="type"
                :class="['filter-btn', { active: filterType === type }]"
                @click="setFilterType(type)"
              >
                {{ type }} ({{ stats.by_signal_type[type] }})
              </button>
            </div>
          </div>
          
          <button class="refresh-btn" @click="refresh" :disabled="refreshing">
            {{ refreshing ? '刷新中...' : '刷新数据' }}
          </button>
        </div>
      </div>

      <!-- 预警列表 -->
      <div class="alert-list">
        <div v-if="loading" class="loading">加载中...</div>
        <div v-else-if="filteredAlerts.length === 0" class="empty-state">
          <div class="empty-state-icon">📭</div>
          <p>暂无符合条件的预警记录</p>
          <p style="margin-top: 8px; font-size: 0.9rem;">等待第一次信号触发...</p>
        </div>
        <div v-else>
          <div v-for="alert in paginatedAlerts" :key="alert.timestamp + alert.name" class="alert-item">
            <div class="alert-header">
              <span class="alert-title">{{ alert.name }}</span>
              <span :class="getTypeBadgeClass(alert.type)">{{ alert.type }}</span>
              <span class="badge badge-asset">{{ alert.asset }}</span>
              <span class="alert-time">{{ alert.timestamp }}</span>
            </div>
            <div class="alert-content">
              {{ alert.message }}
            </div>
            <div v-if="alert.suggestion" class="alert-suggestion">
              💡 {{ alert.suggestion }}
            </div>
          </div>
          
          <div class="load-more">
            <button 
              v-if="hasMore" 
              class="load-more-btn" 
              @click="loadMore"
            >
              加载更多
            </button>
            <div v-else-if="filteredAlerts.length > 0" class="no-more">
              已加载全部 {{ filteredAlerts.length }} 条预警
            </div>
          </div>
        </div>
      </div>

      <footer>
        <p>gold-silver-finance-agent | 黄金白银 AI 智能监控 · 专业金融分析平台</p>
      </footer>
    </div>
  `
}).mount('#app')
