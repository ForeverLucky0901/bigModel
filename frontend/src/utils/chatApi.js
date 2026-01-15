import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api'

export const chatCompletions = async (messages, options = {}) => {
  const response = await axios.post(
    `${API_BASE}/v1/chat/completions`,
    {
      model: options.model || 'gpt-3.5-turbo',
      messages,
      stream: options.stream || false,
      temperature: options.temperature,
      max_tokens: options.max_tokens
    },
    {
      headers: {
        'Authorization': `Bearer ${options.apiKey}`,
        'Content-Type': 'application/json'
      },
      responseType: options.stream ? 'stream' : 'json'
    }
  )
  return response
}

export const chatCompletionsStream = async (messages, options = {}) => {
  const response = await fetch(`${API_BASE}/v1/chat/completions`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${options.apiKey}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      model: options.model || 'gpt-3.5-turbo',
      messages,
      stream: true,
      temperature: options.temperature,
      max_tokens: options.max_tokens
    })
  })

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`)
  }

  return response.body
}
