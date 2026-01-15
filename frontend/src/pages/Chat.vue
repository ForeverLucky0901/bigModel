<template>
  <Layout>
    <div class="flex flex-col h-full bg-gray-50">
      <!-- 聊天区域 -->
      <div class="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50">
        <div
          v-for="(message, index) in messages"
          :key="index"
          class="flex"
          :class="message.role === 'user' ? 'justify-end' : 'justify-start'"
        >
          <div
            class="max-w-3xl rounded-lg px-4 py-2"
            :class="
              message.role === 'user'
                ? 'bg-blue-600 text-white'
                : 'bg-white text-gray-800 border border-gray-200'
            "
          >
            <div class="whitespace-pre-wrap">{{ message.content }}</div>
            <div
              v-if="message.role === 'assistant' && message.loading"
              class="mt-2 text-sm text-gray-500"
            >
              正在输入...
            </div>
          </div>
        </div>
        <div v-if="loading" class="flex justify-start">
          <div class="bg-white border border-gray-200 rounded-lg px-4 py-2">
            <div class="flex items-center gap-2">
              <div class="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
              <span class="text-gray-500">思考中...</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 输入区域 -->
      <div class="border-t border-gray-200 p-4 bg-white">
        <form @submit.prevent="sendMessage" class="flex gap-2">
          <textarea
            v-model="inputMessage"
            @keydown.enter.exact.prevent="sendMessage"
            @keydown.enter.shift.exact="inputMessage += '\n'"
            rows="3"
            class="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
            placeholder="输入消息... (Enter发送, Shift+Enter换行)"
          ></textarea>
          <button
            type="submit"
            :disabled="loading || !inputMessage.trim()"
            class="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            发送
          </button>
        </form>
        <div class="mt-2 text-xs text-gray-500">
          使用模型: {{ selectedModel }}
        </div>
      </div>
    </div>
  </Layout>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import Layout from '@/components/Layout.vue'
import { useAuthStore } from '@/stores/auth'
import api from '@/utils/api'

const authStore = useAuthStore()

const messages = ref([])
const inputMessage = ref('')
const loading = ref(false)
const selectedModel = ref('gpt-3.5-turbo')
const apiKey = ref('')

// 获取用户的API Key
onMounted(async () => {
  try {
    const response = await api.get('/admin/api-keys')
    if (response.data.length > 0) {
      apiKey.value = response.data[0].key
    } else {
      // 如果没有API Key，创建一个
      const createResponse = await api.post('/admin/api-keys', {
        name: 'Default Key'
      })
      apiKey.value = createResponse.data.key
    }
  } catch (error) {
    console.error('Failed to get API key:', error)
  }
})

const sendMessage = async () => {
  if (!inputMessage.value.trim() || loading.value) return

  const userMessage = {
    role: 'user',
    content: inputMessage.value
  }

  messages.value.push(userMessage)
  const currentInput = inputMessage.value
  inputMessage.value = ''

  // 添加助手消息占位符
  const assistantMessage = {
    role: 'assistant',
    content: '',
    loading: true
  }
  messages.value.push(assistantMessage)

  loading.value = true

  try {
    const response = await fetch('/api/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${apiKey.value}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        model: selectedModel.value,
        messages: messages.value
          .filter(m => m.role !== 'assistant' || !m.loading)
          .map(m => ({ role: m.role, content: m.content })),
        stream: true
      })
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6)
          if (data === '[DONE]') {
            assistantMessage.loading = false
            loading.value = false
            return
          }

          try {
            const parsed = JSON.parse(data)
            const delta = parsed.choices?.[0]?.delta?.content
            if (delta) {
              assistantMessage.content += delta
            }
          } catch (e) {
            // 忽略解析错误
          }
        }
      }
    }

    assistantMessage.loading = false
  } catch (error) {
    console.error('Error:', error)
    assistantMessage.content = '抱歉，发生了错误：' + error.message
    assistantMessage.loading = false
  } finally {
    loading.value = false
  }
}
</script>
