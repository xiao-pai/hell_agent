import { createApp } from 'vue'
import App from './App.vue'
import Antd from 'ant-design-vue'
import 'ant-design-vue/dist/reset.css'
import router from './router'
import zhCN from 'ant-design-vue/es/locale/zh_CN'
import dayjs from 'dayjs'
import 'dayjs/locale/zh-cn'

dayjs.locale('zh-cn')

const app = createApp(App)
app.use(router)
app.use(Antd)
app.use(Antd.ConfigProvider, {
  locale: zhCN
})
app.mount('#app')
