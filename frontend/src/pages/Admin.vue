<template>
  <Layout>
    <div class="h-full overflow-y-auto p-6">
      <h1 class="text-2xl font-bold text-gray-800 mb-6">管理后台</h1>

      <!-- 标签页 -->
      <div class="border-b border-gray-200 mb-6">
        <nav class="flex space-x-8">
          <button
            v-for="tab in tabs"
            :key="tab.id"
            @click="activeTab = tab.id"
            :class="[
              'py-2 px-1 border-b-2 font-medium text-sm',
              activeTab === tab.id
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            ]"
          >
            {{ tab.name }}
          </button>
        </nav>
      </div>

      <!-- 用户管理 -->
      <div v-if="activeTab === 'users'" class="space-y-4">
        <div class="bg-white rounded-lg shadow p-6">
          <div class="flex justify-between items-center mb-4">
            <h2 class="text-lg font-semibold">用户管理</h2>
            <button
              @click="showCreateUserModal = true"
              class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              创建用户
            </button>
          </div>
          <div class="overflow-x-auto">
            <table class="min-w-full divide-y divide-gray-200">
              <thead class="bg-gray-50">
                <tr>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    ID
                  </th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    用户名
                  </th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    邮箱
                  </th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    状态
                  </th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    配额
                  </th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    操作
                  </th>
                </tr>
              </thead>
              <tbody class="bg-white divide-y divide-gray-200">
                <tr v-for="user in users" :key="user.id">
                  <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {{ user.id }}
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {{ user.username }}
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {{ user.email }}
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap">
                    <span
                      :class="[
                        'px-2 inline-flex text-xs leading-5 font-semibold rounded-full',
                        user.is_active
                          ? 'bg-green-100 text-green-800'
                          : 'bg-red-100 text-red-800'
                      ]"
                    >
                      {{ user.is_active ? '激活' : '禁用' }}
                    </span>
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {{ formatNumber(user.monthly_quota_tokens) }} tokens
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <button
                      @click="toggleUserStatus(user)"
                      class="text-blue-600 hover:text-blue-900 mr-3"
                    >
                      {{ user.is_active ? '禁用' : '启用' }}
                    </button>
                    <button
                      @click="editUser(user)"
                      class="text-indigo-600 hover:text-indigo-900"
                    >
                      编辑
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- API Key管理 -->
      <div v-if="activeTab === 'keys'" class="space-y-4">
        <div class="bg-white rounded-lg shadow p-6">
          <div class="flex justify-between items-center mb-4">
            <h2 class="text-lg font-semibold">API Key 管理</h2>
            <button
              @click="showCreateKeyModal = true"
              class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              创建 Key
            </button>
          </div>
          <div class="overflow-x-auto">
            <table class="min-w-full divide-y divide-gray-200">
              <thead class="bg-gray-50">
                <tr>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Key
                  </th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    用户
                  </th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    状态
                  </th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    创建时间
                  </th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    操作
                  </th>
                </tr>
              </thead>
              <tbody class="bg-white divide-y divide-gray-200">
                <tr v-for="key in apiKeys" :key="key.id">
                  <td class="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-900">
                    {{ key.key.substring(0, 20) }}...
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {{ key.user?.username }}
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap">
                    <span
                      :class="[
                        'px-2 inline-flex text-xs leading-5 font-semibold rounded-full',
                        key.is_active
                          ? 'bg-green-100 text-green-800'
                          : 'bg-red-100 text-red-800'
                      ]"
                    >
                      {{ key.is_active ? '激活' : '禁用' }}
                    </span>
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {{ formatDate(key.created_at) }}
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <button
                      @click="toggleKeyStatus(key)"
                      class="text-blue-600 hover:text-blue-900 mr-3"
                    >
                      {{ key.is_active ? '禁用' : '启用' }}
                    </button>
                    <button
                      @click="deleteKey(key)"
                      class="text-red-600 hover:text-red-900"
                    >
                      删除
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- 用量统计 -->
      <div v-if="activeTab === 'usage'" class="space-y-4">
        <div class="bg-white rounded-lg shadow p-6">
          <h2 class="text-lg font-semibold mb-4">用量统计</h2>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div class="bg-blue-50 p-4 rounded-lg">
              <div class="text-sm text-gray-600">总请求数</div>
              <div class="text-2xl font-bold text-blue-600">{{ formatNumber(totalRequests) }}</div>
            </div>
            <div class="bg-green-50 p-4 rounded-lg">
              <div class="text-sm text-gray-600">总Token数</div>
              <div class="text-2xl font-bold text-green-600">{{ formatNumber(totalTokens) }}</div>
            </div>
            <div class="bg-purple-50 p-4 rounded-lg">
              <div class="text-sm text-gray-600">活跃用户</div>
              <div class="text-2xl font-bold text-purple-600">{{ activeUsers }}</div>
            </div>
          </div>
          <div class="overflow-x-auto">
            <table class="min-w-full divide-y divide-gray-200">
              <thead class="bg-gray-50">
                <tr>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    用户
                  </th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    请求数
                  </th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Token数
                  </th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    日期
                  </th>
                </tr>
              </thead>
              <tbody class="bg-white divide-y divide-gray-200">
                <tr v-for="record in usageRecords" :key="record.id">
                  <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {{ record.user?.username }}
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {{ record.total_requests }}
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {{ formatNumber(record.total_tokens) }}
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {{ record.date }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- 创建用户模态框 -->
      <div
        v-if="showCreateUserModal"
        class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
        @click.self="showCreateUserModal = false"
      >
        <div class="bg-white rounded-lg p-6 w-full max-w-md">
          <h3 class="text-lg font-semibold mb-4">创建用户</h3>
          <form @submit.prevent="createUser">
            <div class="space-y-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">用户名</label>
                <input
                  v-model="newUser.username"
                  type="text"
                  required
                  class="w-full px-3 py-2 border border-gray-300 rounded-md"
                />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">邮箱</label>
                <input
                  v-model="newUser.email"
                  type="email"
                  required
                  class="w-full px-3 py-2 border border-gray-300 rounded-md"
                />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Token配额</label>
                <input
                  v-model.number="newUser.monthly_quota_tokens"
                  type="number"
                  required
                  class="w-full px-3 py-2 border border-gray-300 rounded-md"
                />
              </div>
            </div>
            <div class="mt-6 flex justify-end gap-3">
              <button
                type="button"
                @click="showCreateUserModal = false"
                class="px-4 py-2 border border-gray-300 rounded-md"
              >
                取消
              </button>
              <button
                type="submit"
                class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                创建
              </button>
            </div>
          </form>
        </div>
      </div>

      <!-- 创建Key模态框 -->
      <div
        v-if="showCreateKeyModal"
        class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
        @click.self="showCreateKeyModal = false"
      >
        <div class="bg-white rounded-lg p-6 w-full max-w-md">
          <h3 class="text-lg font-semibold mb-4">创建 API Key</h3>
          <form @submit.prevent="createKey">
            <div class="space-y-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">用户</label>
                <select
                  v-model="newKey.user_id"
                  required
                  class="w-full px-3 py-2 border border-gray-300 rounded-md"
                >
                  <option value="">选择用户</option>
                  <option v-for="user in users" :key="user.id" :value="user.id">
                    {{ user.username }}
                  </option>
                </select>
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">名称</label>
                <input
                  v-model="newKey.name"
                  type="text"
                  class="w-full px-3 py-2 border border-gray-300 rounded-md"
                />
              </div>
            </div>
            <div class="mt-6 flex justify-end gap-3">
              <button
                type="button"
                @click="showCreateKeyModal = false"
                class="px-4 py-2 border border-gray-300 rounded-md"
              >
                取消
              </button>
              <button
                type="submit"
                class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                创建
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </Layout>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import Layout from '@/components/Layout.vue'
import api from '@/utils/api'

const tabs = [
  { id: 'users', name: '用户管理' },
  { id: 'keys', name: 'API Key' },
  { id: 'usage', name: '用量统计' }
]

const activeTab = ref('users')
const users = ref([])
const apiKeys = ref([])
const usageRecords = ref([])
const totalRequests = ref(0)
const totalTokens = ref(0)
const activeUsers = ref(0)

const showCreateUserModal = ref(false)
const showCreateKeyModal = ref(false)

const newUser = ref({
  username: '',
  email: '',
  monthly_quota_tokens: 1000000
})

const newKey = ref({
  user_id: '',
  name: ''
})

onMounted(() => {
  loadUsers()
  loadApiKeys()
  loadUsage()
})

const loadUsers = async () => {
  try {
    const response = await api.get('/admin/users')
    users.value = response.data
  } catch (error) {
    console.error('Failed to load users:', error)
  }
}

const loadApiKeys = async () => {
  try {
    const response = await api.get('/admin/api-keys')
    apiKeys.value = response.data
  } catch (error) {
    console.error('Failed to load API keys:', error)
  }
}

const loadUsage = async () => {
  try {
    const response = await api.get('/admin/usage')
    usageRecords.value = response.data.records || []
    totalRequests.value = response.data.total_requests || 0
    totalTokens.value = response.data.total_tokens || 0
    activeUsers.value = response.data.active_users || 0
  } catch (error) {
    console.error('Failed to load usage:', error)
  }
}

const toggleUserStatus = async (user) => {
  try {
    await api.patch(`/admin/users/${user.id}`, {
      is_active: !user.is_active
    })
    user.is_active = !user.is_active
  } catch (error) {
    console.error('Failed to toggle user status:', error)
    alert('操作失败')
  }
}

const toggleKeyStatus = async (key) => {
  try {
    await api.patch(`/admin/api-keys/${key.id}`, {
      is_active: !key.is_active
    })
    key.is_active = !key.is_active
  } catch (error) {
    console.error('Failed to toggle key status:', error)
    alert('操作失败')
  }
}

const deleteKey = async (key) => {
  if (!confirm('确定要删除这个API Key吗？')) return
  try {
    await api.delete(`/admin/api-keys/${key.id}`)
    await loadApiKeys()
  } catch (error) {
    console.error('Failed to delete key:', error)
    alert('删除失败')
  }
}

const createUser = async () => {
  try {
    await api.post('/admin/users', newUser.value)
    showCreateUserModal.value = false
    newUser.value = { username: '', email: '', monthly_quota_tokens: 1000000 }
    await loadUsers()
  } catch (error) {
    console.error('Failed to create user:', error)
    alert('创建失败')
  }
}

const createKey = async () => {
  try {
    await api.post('/admin/api-keys', newKey.value)
    showCreateKeyModal.value = false
    newKey.value = { user_id: '', name: '' }
    await loadApiKeys()
  } catch (error) {
    console.error('Failed to create key:', error)
    alert('创建失败')
  }
}

const editUser = (user) => {
  // TODO: 实现编辑用户功能
  alert('编辑功能待实现')
}

const formatNumber = (num) => {
  return new Intl.NumberFormat('zh-CN').format(num)
}

const formatDate = (date) => {
  return new Date(date).toLocaleString('zh-CN')
}
</script>
