<template>
  <div class="home-container">
    <div class="header">
      <h1>✈️ 智能旅行助手</h1>
      <p class="subtitle">输入您的旅行需求，AI 为您规划完美行程</p>
    </div>
    <a-card class="form-card">
      <a-form ref="formRef" :model="form" :rules="formRules" @finish="onSubmit">
        <a-form-item label="出发地城市" name="departure">
          <a-input 
            v-model:value="form.departure" 
            placeholder="例如：上海"
            :status="formErrors.departure ? 'error' : undefined"
          />
        </a-form-item>
        <a-form-item label="目的地城市" name="city">
          <a-input 
            v-model:value="form.city" 
            placeholder="例如：北京"
            :status="formErrors.city ? 'error' : undefined"
          />
        </a-form-item>
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="开始日期" name="start_date">
              <a-date-picker 
                v-model:value="form.start_date" 
                style="width:100%"
                :disabled-date="disabledStartDate"
              />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="结束日期" name="end_date">
              <a-date-picker 
                v-model:value="form.end_date" 
                style="width:100%"
                :disabled-date="disabledEndDate"
              />
            </a-form-item>
          </a-col>
        </a-row>
        <a-form-item label="游玩天数" name="days">
          <a-input-number 
            v-model:value="form.days" 
            :min="1" 
            :max="30" 
            style="width:100%"
          />
        </a-form-item>
        <a-form-item label="旅行偏好" name="preferences">
          <a-select v-model:value="form.preferences" style="width:100%">
            <a-select-option value="历史文化">历史文化</a-select-option>
            <a-select-option value="自然风光">自然风光</a-select-option>
            <a-select-option value="现代建筑">现代建筑</a-select-option>
            <a-select-option value="美食探索">美食探索</a-select-option>
            <a-select-option value="休闲度假">休闲度假</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="预算水平" name="budget">
          <a-select v-model:value="form.budget" style="width:100%">
            <a-select-option value="经济">经济</a-select-option>
            <a-select-option value="中等">中等</a-select-option>
            <a-select-option value="豪华">豪华</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="交通方式" name="transportation">
          <a-select v-model:value="form.transportation" style="width:100%">
            <a-select-option value="公共交通">公共交通</a-select-option>
            <a-select-option value="自驾">自驾</a-select-option>
            <a-select-option value="打车">打车</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="住宿类型" name="accommodation">
          <a-select v-model:value="form.accommodation" style="width:100%">
            <a-select-option value="经济型酒店">经济型酒店</a-select-option>
            <a-select-option value="星级酒店">星级酒店</a-select-option>
            <a-select-option value="民宿">民宿</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item>
          <a-button type="primary" html-type="submit" :loading="loading" block>
            {{ loading ? '正在生成行程...' : '开始规划' }}
          </a-button>
        </a-form-item>
      </a-form>
    </a-card>
    <a-alert 
      v-if="errorMessage" 
      :message="errorMessage" 
      type="error" 
      closable 
      @close="errorMessage = ''"
      style="margin-top: 16px;"
    />
  </div>
</template>

<script setup>
import { ref, computed, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { generateTripPlan } from '../services/api'
import dayjs from 'dayjs'

const router = useRouter()
const formRef = ref(null)
const loading = ref(false)
const errorMessage = ref('')
const formErrors = reactive({
  departure: '',
  city: ''
})

const form = ref({
  departure: '',
  city: '',
  start_date: dayjs(),
  end_date: dayjs().add(2, 'day'),
  days: 3,
  preferences: '历史文化',
  budget: '中等',
  transportation: '公共交通',
  accommodation: '经济型酒店'
})

const formRules = {
  departure: [
    { required: true, message: '请输入出发地城市', trigger: 'blur' },
    { min: 2, max: 20, message: '城市名称长度应在 2-20 个字符之间', trigger: 'blur' }
  ],
  city: [
    { required: true, message: '请输入目的地城市', trigger: 'blur' },
    { min: 2, max: 20, message: '城市名称长度应在 2-20 个字符之间', trigger: 'blur' }
  ],
  start_date: [
    { required: true, message: '请选择开始日期', trigger: 'change' }
  ],
  end_date: [
    { required: true, message: '请选择结束日期', trigger: 'change' }
  ],
  days: [
    { required: true, message: '请输入游玩天数', trigger: 'blur' },
    { type: 'number', min: 1, max: 30, message: '游玩天数应在 1-30 天之间', trigger: 'blur' }
  ]
}

const disabledStartDate = (current) => {
  return current && current < dayjs().startOf('day')
}

const disabledEndDate = (current) => {
  return current && (current < form.value.start_date || current > dayjs().add(1, 'year'))
}

const validateForm = () => {
  let isValid = true
  formErrors.departure = ''
  formErrors.city = ''

  if (!form.value.departure.trim()) {
    formErrors.departure = '请输入出发地城市'
    isValid = false
  }
  if (!form.value.city.trim()) {
    formErrors.city = '请输入目的地城市'
    isValid = false
  }
  if (form.value.start_date && form.value.end_date && 
      form.value.end_date.isBefore(form.value.start_date)) {
    errorMessage.value = '结束日期不能早于开始日期'
    isValid = false
  }

  return isValid
}

const onSubmit = async () => {
  errorMessage.value = ''
  
  if (!validateForm()) {
    return
  }

  loading.value = true
  try {
    const request = {
      departure: form.value.departure.trim(),
      city: form.value.city.trim(),
      start_date: form.value.start_date.format('YYYY-MM-DD'),
      end_date: form.value.end_date.format('YYYY-MM-DD'),
      days: form.value.days,
      preferences: form.value.preferences,
      budget: form.value.budget,
      transportation: form.value.transportation,
      accommodation: form.value.accommodation
    }
    const plan = await generateTripPlan(request)
    sessionStorage.setItem('tripPlan', JSON.stringify(plan))
    router.push({ name: 'Result' })
  } catch (err) {
    console.error(err)
    const errMsg = err.response?.data?.detail || err.message || '生成失败，请重试'
    errorMessage.value = errMsg
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.home-container {
  max-width: 600px;
  margin: 0 auto;
  padding: 20px;
}
.header {
  text-align: center;
  margin-bottom: 24px;
}
.header h1 {
  margin: 0 0 8px 0;
  font-size: 28px;
  color: #1890ff;
  background-color: var(--tw-ring-offset-color);
}
.subtitle {
  margin: 0;
  color: #8c8c8c;
  font-size: 14px;
}
.form-card {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}
@media (max-width: 768px) {
  .home-container {
    padding: 12px;
  }
  .header h1 {
    font-size: 24px;
  }
}
</style>
