const { createApp, ref, onMounted, computed } = Vue

createApp({
  setup() {
    const alerts = ref([])
    const stats = ref({
      total: 0,
      by_asset: {},
      by_signal_type: {}
    })
    const loading = ref(true)
    
    const fetchAlerts = async () => {
      loading.value = true
      try {
        const res = await fetch('/api/alerts')
        const data = await res.json()
        alerts.value = data.alerts
        stats.value.total = data.count
        loading.value = false
      } catch (e) {
        console.error('Failed to fetch alerts:', e)
        loading.value = false
      }
    }
    
    const fetchStats = async () => {
      try {
        const res = await fetch('/api/stats')
        const data = await res.json()
        stats.value = data
      } catch (e) {
        console.error('Failed to fetch stats:', e)
      }
    }
    
    onMounted(async () => {
      await fetchAlerts()
      await fetchStats()
    })
    
    const assetEntries = computed(() => {
      return Object.entries(stats.value.by_asset || {})
    })
    
    const signalEntries = computed(() => {
      return Object.entries(stats.value.by_signal_type || {})
    })
    
    return {
      alerts,
      stats,
      loading,
      assetEntries,
      signalEntries,
      fetchAlerts
    }
  },
  template: `
    <div class="container">
      <header>
        <h1>gold-silver-finance-agent</h1>
        <div class="subtitle">📊 历史预警查询 - AI 赋能黄金白银主动监控 Agent</div>
      </header>

      <div class="stats">
        <div class="stat-card">
          <div class="stat-number">{{ stats.total }}</div>
          <div class="stat-label">总预警条数</div>
        </div>
      </div>
      
      <div v-if="assetEntries.length > 0" class="stats">
        <div v-for="[asset, count] in assetEntries" :key="asset" class="stat-card">
          <div class="stat-number">{{ count }}</div>
          <div class="stat-label">{{ asset }}</div>
        </div>
      </div>

      <div class="alert-list">
        <div v-if="loading" class="loading">加载中...</div>
        <div v-else-if="alerts.length === 0" class="empty-state">
          <p>暂无预警记录，等待第一次信号触发...</p>
        </div>
        <div v-else>
          <div v-for="alert in alerts" :key="alert.timestamp" class="alert-item">
            <div class="alert-header">
              <span class="alert-title">{{ alert.name }}</span>
              <span class="alert-asset">{{ alert.asset }}</span>
              <span class="alert-time">{{ alert.timestamp }}</span>
            </div>
            <div v-if="alert.message" class="alert-content">
              {{ alert.message }}
            </div>
          </div>
        </div>
      </div>

      <footer>
        <p>gold-silver-finance-agent | MIT License</p>
      </footer>
    </div>
  `
}).mount('#app')
