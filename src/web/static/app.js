const { createApp, ref, onMounted, computed } = Vue

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
      } catch (e) {
        console.error('Failed to fetch data:', e)
      } finally {
        loading.value = false
        refreshing.value = false
      }
    }
    
    onMounted(async () => {
      await fetchData()
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
    
    // 统计卡片数据
    const statsList = computed(() => {
      const result = [
        { label: '总预警数', value: stats.value.total }
      ]
      return result
    })
    
    return {
      allAlerts,
      stats,
      loading,
      refreshing,
      filterAsset,
      filterType,
      assetOptions,
      typeOptions,
      filteredAlerts,
      paginatedAlerts,
      hasMore,
      getTypeBadgeClass,
      setFilterAsset,
      setFilterType,
      loadMore,
      refresh
    }
  },
  template: `
    <div class="container">
      <header>
        <h1>🤖 gold-silver-finance-agent</h1>
        <div class="subtitle">📊 AI 赋能黄金白银主动监控 - 历史预警中心</div>
      </header>

      <!-- 统计卡片 -->
      <div class="stats-row">
        <div class="stat-card">
          <div class="stat-number">{{ stats.total }}</div>
          <div class="stat-label">总预警条数</div>
        </div>
        <div v-for="[asset, count] in Object.entries(stats.by_asset || {})" :key="asset" class="stat-card">
          <div class="stat-number">{{ count }}</div>
          <div class="stat-label">{{ asset }}</div>
        </div>
      </div>

      <!-- 筛选区 -->
      <div class="filters-section">
        <div class="filters-title">筛选</div>
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
