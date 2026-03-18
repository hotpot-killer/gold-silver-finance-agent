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
      gold: { symbol: 'AU9999', data: [], latest: null },
      silver: { symbol: 'AG9999', data: [], latest: null },
    })
    let chartInstance = null
    let candlestickSeries = null
    
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
      const symbol = asset === 'gold' ? 'XAUUSD' : 'XAGUSD'
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
          background: { color: '#ffffff' },
          textColor: '#333333',
        },
        grid: {
          vertLines: { color: '#f0f0f0' },
          horzLines: { color: '#f0f0f0' },
        },
        priceScale: {
          borderColor: '#cccccc',
        },
        timeScale: {
          borderColor: '#cccccc',
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
      formatPrice
    }
  },
  template: `
    <div class="container">
      <header>
        <h1>🤖 gold-silver-finance-agent</h1>
        <div class="subtitle">📊 AI 赋能黄金白银主动监控 - 市场仪表盘</div>
        <div class="forward-markets">
          <h3>🔮 前瞻预测市场（点击查看最新市场概率）</h3>
          <div class="market-links">
            <a href="https://polymarket.com/predictions/gold" target="_blank" class="market-link">Polymarket (长周期预测)</a>
            <a href="https://kalshi.com/markets" target="_blank" class="market-link">Kalshi (短期/周月级)</a>
            <a href="https://www.cmegroup.com/markets/metals/precious.html" target="_blank" class="market-link">CME 贵金属</a>
            <a href="https://www.ishares.com/us/products/239751/gld-spdr-gold-trust" target="_blank" class="market-link">GLD 持仓</a>
            <a href="https://www.ishares.com/us/products/239728/slv-isharess-silver-trust" target="_blank" class="market-link">SLV 持仓</a>
          </div>
        </div>
      </header>

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
            <div class="stat-label">当前 {{ selectedAsset === 'gold' ? '黄金' : '白银' }} 价格</div>
          </div>
        </div>

        <!-- 知名宏观大佬最新观点 -->
        <div class="guru-section">
          <div class="card-title">🤔 知名宏观大佬最新黄金观点（人群智慧参考）</div>
          <div v-if="guruLoading" style="text-align:center; padding:20px; color:var(--text-secondary);">加载中...</div>
          <div class="guru-grid" v-else>
            <div class="guru-card" v-for="guru in guruViews" :key="guru.name">
              <div class="guru-name">{{ guru.name }}</div>
              <div class="guru-title">{{ guru.title }}</div>
              <div class="guru-view">📝 最新 ({{ guru.updated_at }}): {{ guru.latest_view }}</div>
              <span :class="['guru-tone', guru.tone === 'bullish' ? 'tone-bullish' : guru.tone === 'bearish' ? 'tone-bearish' : 'tone-neutral']">
                {{ guru.tone === 'bullish' ? '看多' : guru.tone === 'bearish' ? '看空' : '中性' }}
              </span>
              <a v-if="guru.source_url" :href="guru.source_url" target="_blank" style="display:inline-block; margin-left:8px; font-size:0.8rem; color:var(--primary);">查看原文 →</a>
            </div>
          </div>
          <div style="margin-top: 12px; font-size: 0.85rem; color: var(--text-secondary);">
            💡 提示：每天自动抓取Twitter最新观点，点击"查看原文"看完整内容
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
            黄金 (AU9999)
          </div>
          <div 
            class="price-tab" 
            :class="{ active: selectedAsset === 'silver' }"
            @click="switchAsset('silver')"
          >
            白银 (AG9999)
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
        <p>gold-silver-finance-agent | 黄金白银 AI 智能监控</p>
      </footer>
    </div>
  `
}).mount('#app')
