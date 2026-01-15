import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('@/pages/Login.vue'),
      meta: { requiresAuth: false }
    },
    {
      path: '/register',
      name: 'Register',
      component: () => import('@/pages/Register.vue'),
      meta: { requiresAuth: false }
    },
    {
      path: '/chat',
      name: 'Chat',
      component: () => import('@/pages/Chat.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/',
      redirect: '/chat'
    }
  ]
})

// router.beforeEach((to, from, next) => {
//   const authStore = useAuthStore()
  
//   if (to.meta.requiresAuth && !authStore.isAuthenticated) {
//     next('/login')
//   } else if (to.meta.requiresAdmin && !authStore.isAdmin) {
//     next('/chat')
//   } else if ((to.path === '/login' || to.path === '/register') && authStore.isAuthenticated) {
//     next('/chat')
//   } else {
//     next()
//   }
// })

export default router
