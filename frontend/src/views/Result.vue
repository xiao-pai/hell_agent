<template>
  <div class="result-container">
    <div class="header">
      <a-button @click="$router.back()" class="back-btn">← 返回</a-button>
      <a-button type="primary" @click="regeneratePlan" :loading="regenerating" style="float: right;">
        重新规划
      </a-button>
    </div>
    
    <a-card v-if="plan" class="result-card">
      <div class="plan-header">
        <h2>🌆 {{ plan.city }} 旅行计划</h2>
        <p class="date-range">{{ plan.start_date }} 至 {{ plan.end_date }}</p>
      </div>
      
      <a-divider />
      
      <div v-if="plan.weather" class="weather-section">
        <h3>🌤️ 天气预报</h3>
        <a-descriptions bordered :column="1">
          <a-descriptions-item label="城市">{{ plan.weather.city }}</a-descriptions-item>
          <a-descriptions-item label="今日天气">
            {{ plan.weather.today?.weather || '暂无数据' }}，温度：{{ plan.weather.today?.low_temp || '-' }}°C ~ {{ plan.weather.today?.high_temp || '-' }}°C
          </a-descriptions-item>
          <a-descriptions-item label="出行建议">
            {{ plan.weather.today?.description || '暂无建议' }}
          </a-descriptions-item>
        </a-descriptions>
        <a-divider />
      </div>
      
      <div v-if="plan.hotels && plan.hotels.length > 0" class="hotels-section">
        <h3>🏨 推荐酒店</h3>
        <a-list :data-source="plan.hotels" :grid="{ gutter: 16, column: 3 }">
          <template #renderItem="{ item }">
            <a-list-item>
              <a-card hoverable>
                <template #title>{{ item.name }}</template>
                <p>📍 {{ item.address }}</p>
                <p>💰 ¥{{ item.price }}/晚</p>
                <p>⭐ {{ item.rating }}分</p>
                <p>🏷️ {{ item.type }}</p>
              </a-card>
            </a-list-item>
          </template>
        </a-list>
        <a-divider />
      </div>
      
      <div class="days-container">
        <div v-for="(day, idx) in plan.days" :key="idx" class="day-section">
          <div class="day-header">
            <a-tag color="blue" class="day-tag">第 {{ idx+1 }} 天</a-tag>
            <span class="day-date">{{ day.date }}</span>
          </div>
          <p v-if="day.description" class="day-desc">{{ day.description }}</p>
          
          <a-collapse :default-active-key="[String(idx)]" :bordered="false">
            <a-collapse-panel :key="idx" :header="`📍 今日景点（${day.attractions.length}个）`">
              <a-list :data-source="day.attractions" :grid="{ gutter: 16, column: 1 }">
                <template #renderItem="{ item }">
                  <a-card 
                    hoverable 
                    class="attraction-card"
                    :cover="item.image_url ? { src: item.image_url } : undefined"
                  >
                    <a-card-meta :title="item.name" :description="item.address">
                      <template #avatar>
                        <a-avatar icon="🏛️" />
                      </template>
                    </a-card-meta>
                    <div class="attraction-info">
                      <span class="info-item">🎫 ¥{{ item.ticket_price || '免费' }}</span>
                      <span class="info-item">⏱️ {{ item.visit_duration }} 分钟</span>
                    </div>
                    <p class="attraction-desc">{{ item.description }}</p>
                  </a-card>
                </template>
              </a-list>
            </a-collapse-panel>
          </a-collapse>
          
          <div v-if="day.hotel" class="hotel-info">
            <a-tag color="gold">🏨 推荐住宿</a-tag>
            <span>{{ day.hotel }}</span>
          </div>
        </div>
      </div>
      
      <a-divider />
      
      <div class="transport-section">
        <h3>🚗 交通规划</h3>
        
        <a-card title="🚆 长途出行（12306）" :bordered="false" class="transport-card">
          <div v-if="plan.transportation && plan.transportation.long_distance && plan.transportation.long_distance.length > 0">
            <a-list :data-source="plan.transportation.long_distance">
              <template #renderItem="{ item, index }">
                <a-list-item>
                  <a-list-item-meta
                    :title="`方案 ${index + 1}: ${item.mode} ${item.train_number || ''}`"
                    :description="`出发: ${item.departure_time || '未知'} · 到达: ${item.arrival_time || '未知'} · 价格: ${item.price || '待查询'}`"
                  />
                  <div>时长：{{ item.duration || '未知' }}</div>
                  <div v-if="item.seat_types && item.seat_types.length">座席：{{ item.seat_types.join('，') }}</div>
                </a-list-item>
              </template>
            </a-list>
          </div>
          <a-empty v-else description="暂无长途列车信息，请检查 MCP 12306 服务配置" />
        </a-card>

        <a-card title="🚇 目的城市内交通" :bordered="false" class="transport-card" style="margin-top: 16px;">
          <div v-if="plan.transportation && plan.transportation.local && plan.transportation.local.length > 0">
            <a-list :data-source="plan.transportation.local">
              <template #renderItem="{ item, index }">
                <a-list-item>
                  <a-list-item-meta :title="`方案 ${index + 1}: ${item.mode}`" :description="item.description" />
                  <div v-if="item.duration || item.distance">{{ item.distance || '未知距离' }} · {{ item.duration || '未知时长' }}</div>
                </a-list-item>
              </template>
            </a-list>
          </div>
          <a-empty v-else description="暂无目的城市内交通推荐" />
        </a-card>
        
        <a-card v-if="plan.tourist_routes && plan.tourist_routes.length > 0" title="🚂 旅游专列推荐" :bordered="false" class="transport-card" style="margin-top: 16px;">
          <a-list :data-source="plan.tourist_routes" :grid="{ gutter: 16, column: 2 }">
            <template #renderItem="{ item }">
              <a-list-item>
                <a-card hoverable>
                  <template #title>{{ item.name }}</template>
                  <p>{{ item.description }}</p>
                  <p>🏷️ 难度：{{ item.difficulty }}</p>
                  <p>⏱️ 推荐天数：{{ item.recommended_days }}天</p>
                  <p>🌸 最佳季节：{{ item.best_season }}</p>
                </a-card>
              </a-list-item>
            </template>
          </a-list>
        </a-card>
      </div>
      
      <a-divider />
      
      <div v-if="plan.budget" class="budget-section">
        <h3>💰 预算概览</h3>
        <a-statistic 
          title="预计总预算" 
          :value="plan.budget.total || 0" 
          precision="0" 
          :prefix="'¥'"
          class="budget-stat"
        />
      </div>
      
      <div v-if="plan.overall_suggestions" class="suggestions-section">
        <a-alert 
          :message="plan.overall_suggestions" 
          type="info" 
          show-icon
        />
      </div>
    </a-card>
    
    <a-empty v-else-if="!loading" description="未找到旅行计划，请返回首页重新规划" />
    <a-spin v-else tip="加载中..." class="loading-spin" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Statistic } from 'ant-design-vue'

const router = useRouter()
const plan = ref(null)
const loading = ref(true)
const regenerating = ref(false)
const activeDayKeys = ref([0])

const loadPlan = () => {
  try {
    const stored = sessionStorage.getItem('tripPlan')
    if (stored) {
      plan.value = JSON.parse(stored)
    } else {
      const state = history.state
      if (state && state.tripPlan) {
        plan.value = state.tripPlan
        sessionStorage.setItem('tripPlan', JSON.stringify(state.tripPlan))
      }
    }
  } catch (e) {
    console.error('Failed to load trip plan:', e)
  } finally {
    loading.value = false
  }
}

const regeneratePlan = () => {
  sessionStorage.removeItem('tripPlan')
  router.push('/')
}

onMounted(() => {
  loadPlan()
  if (!plan.value && !loading.value) {
    setTimeout(() => {
      if (!plan.value) {
        router.push('/')
      }
    }, 1000)
  }
})
</script>

<style scoped>
.result-container {
  max-width: 900px;
  margin: 0 auto;
  padding: 20px;
}
.header {
  margin-bottom: 20px;
}
.back-btn {
  margin-right: 16px;
}
.result-card {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}
.plan-header {
  text-align: center;
  margin-bottom: 16px;
}
.plan-header h2 {
  margin: 0 0 8px 0;
  font-size: 24px;
}
.date-range {
  margin: 0;
  color: #8c8c8c;
}
.weather-section {
  margin-bottom: 16px;
}
.hotels-section {
  margin-bottom: 16px;
}
.day-section {
  margin-bottom: 24px;
}
.day-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}
.day-tag {
  font-size: 14px;
}
.day-date {
  font-size: 14px;
  color: #666;
}
.day-desc {
  margin: 0 0 12px 0;
  color: #666;
}
.attraction-card {
  margin-bottom: 12px;
}
.attraction-info {
  display: flex;
  gap: 16px;
  margin: 12px 0;
}
.info-item {
  font-size: 13px;
  color: #666;
}
.attraction-desc {
  margin: 0;
  font-size: 13px;
  color: #8c8c8c;
}
.hotel-info {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 12px;
  padding: 8px 12px;
  background: #fffbe6;
  border-radius: 4px;
}
.transport-section {
  margin-top: 16px;
}
.transport-card {
  background: #fafafa;
}
.budget-section {
  margin-top: 16px;
}
.budget-stat {
  display: inline-block;
}
.suggestions-section {
  margin-top: 16px;
}
.loading-spin {
  display: flex;
  justify-content: center;
  padding: 40px;
}
@media (max-width: 768px) {
  .result-container {
    padding: 12px;
  }
  .plan-header h2 {
    font-size: 20px;
  }
}
</style>
