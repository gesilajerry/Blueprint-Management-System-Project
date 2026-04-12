// API 基础配置
const API_BASE_URL = 'http://127.0.0.1:8000/api'

// 获取 Token
const getToken = () => {
  return localStorage.getItem('token')
}

// 通用请求方法
async function request(url, options = {}) {
  const token = getToken()
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers
  }

  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const response = await fetch(`${API_BASE_URL}${url}`, {
    ...options,
    headers
  })

  const data = await response.json()

  if (!response.ok) {
    // 处理验证错误（422）
    let errorMessage = data.detail || data.message || '请求失败'

    // 如果是验证错误，提取详细的字段错误
    if (response.status === 422 && Array.isArray(data.detail)) {
      errorMessage = data.detail.map(err => {
        const field = err.loc?.[1] || err.loc?.[0] || '字段'
        const msg = err.msg || '验证失败'
        return `${field}: ${msg}`
      }).join('; ')
    }

    throw new Error(errorMessage)
  }

  return data
}

// GET 请求
export function get(url, params = {}) {
  // 过滤掉 undefined 和 null 的参数
  const filteredParams = {}
  Object.keys(params).forEach(key => {
    if (params[key] !== undefined && params[key] !== null && params[key] !== '') {
      filteredParams[key] = params[key]
    }
  })
  const queryString = new URLSearchParams(filteredParams).toString()
  const fullUrl = queryString ? `${url}?${queryString}` : url
  return request(fullUrl, { method: 'GET' })
}

// POST 请求（JSON）
export function post(url, data = {}) {
  return request(url, {
    method: 'POST',
    body: JSON.stringify(data)
  })
}

// POST 请求（form 数据）
export function postForm(url, data = {}) {
  const params = new URLSearchParams()
  Object.keys(data).forEach(key => {
    if (data[key] !== undefined && data[key] !== null) {
      params.append(key, String(data[key]))
    }
  })

  return request(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: params.toString()
  })
}

// PUT 请求
export function put(url, data = {}) {
  return request(url, {
    method: 'PUT',
    body: JSON.stringify(data)
  })
}

// PUT 请求（form 数据）
export function putForm(url, data = {}) {
  const params = new URLSearchParams()
  Object.keys(data).forEach(key => {
    if (data[key] !== undefined && data[key] !== null) {
      params.append(key, String(data[key]))
    }
  })

  return request(url, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: params.toString()
  })
}

// DELETE 请求
export function del(url) {
  return request(url, { method: 'DELETE' })
}

// 文件上传
export async function uploadFile(url, file, formData = {}) {
  const token = getToken()
  const headers = {}

  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const formDataObj = new FormData()
  formDataObj.append('file', file)
  Object.keys(formData).forEach(key => {
    if (formData[key]) {
      formDataObj.append(key, formData[key])
    }
  })

  const response = await fetch(`${API_BASE_URL}${url}`, {
    method: 'POST',
    headers,
    body: formDataObj
  })

  const data = await response.json()

  if (!response.ok) {
    throw new Error(data.detail || data.message || '上传失败')
  }

  return data
}

// API 方法
export const api = {
  // 认证
  auth: {
    login: (username, password) => post('/auth/login', { username, password }),
    logout: () => post('/auth/logout'),
    me: () => get('/auth/me')
  },

  // 用户管理
  users: {
    list: (params) => get('/users', params),
    get: (id) => get(`/users/${id}`),
    create: (data) => post('/users', data),
    update: (id, data) => put(`/users/${id}`, data),
    delete: (id) => del(`/users/${id}`),
    getMyProjectGroups: () => get('/users/me/project-groups'),
    export: () => {
      const token = localStorage.getItem('token')
      return fetch(`${API_BASE_URL}/users/export`, {
        method: 'GET',
        headers: { 'Authorization': `Bearer ${token}` }
      }).then(r => r.blob())
    },
    import: (file) => {
      const token = localStorage.getItem('token')
      const formData = new FormData()
      formData.append('file', file)
      return fetch(`${API_BASE_URL}/users/import`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData
      }).then(r => r.json())
    }
  },

  // 角色管理
  roles: {
    list: (params) => get('/roles', params),
    create: (data) => post('/roles', data),
    update: (id, data) => put(`/roles/${id}`, data),
    delete: (id) => del(`/roles/${id}`)
  },

  // 部门管理（项目组）
  departments: {
    list: (params) => get('/departments', params),
    create: (data) => postForm('/departments', data),
    update: (id, data) => postForm(`/departments/${id}`, data),
    delete: (id) => del(`/departments/${id}`)
  },

  // 产品管理
  products: {
    list: (params) => get('/products', params),
    create: (data) => postForm('/products', data),
    update: (id, data) => putForm(`/products/${id}`, data),
    delete: (id) => del(`/products/${id}`)
  },

  // 图纸管理
  drawings: {
    list: (params) => get('/drawings', params),
    get: (id) => get(`/drawings/${id}`),
    create: (data) => postForm('/drawings', data),
    update: (id, data) => postForm(`/drawings/${id}`, data),
    delete: (id) => del(`/drawings/${id}`),
    reactivate: (id) => post(`/drawings/${id}/reactivate`),
    getVersions: (id) => get(`/drawings/${id}/versions`),
    uploadVersion: (id, file, data) => uploadFile(`/drawings/${id}/versions`, file, data),
    download: (id) => `${API_BASE_URL}/drawings/${id}/download`,
    exportCsv: (params) => get('/drawings/export/csv', params)
  },

  // 保密审核
  reviews: {
    getPending: () => get('/reviews/pending'),
    approve: (id, data) => postForm(`/reviews/${id}/approve`, data),
    reject: (id, data) => postForm(`/reviews/${id}/reject`, data),
    getHistory: (id) => get(`/reviews/${id}/history`),
    getAllHistory: (params) => get('/reviews/history/all', params)
  },

  // 核心部件词库
  coreParts: {
    list: (params) => get('/core-parts', params),
    create: (data) => post('/core-parts', data),
    delete: (id) => del(`/core-parts/${id}`),
    export: () => {
      const token = localStorage.getItem('token')
      return fetch(`${API_BASE_URL}/core-parts/export`, {
        method: 'GET',
        headers: { 'Authorization': `Bearer ${token}` }
      }).then(r => r.blob())
    },
    import: (file) => {
      const token = localStorage.getItem('token')
      const formData = new FormData()
      formData.append('file', file)
      return fetch(`${API_BASE_URL}/core-parts/import`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData
      }).then(r => r.json())
    }
  },

  // 项目组管理
  projectGroups: {
    list: (params) => get('/project-groups', params),
    get: (id) => get(`/project-groups/${id}`),
    create: (data) => postForm('/project-groups', data),
    update: (id, data) => postForm(`/project-groups/${id}`, data),
    delete: (id) => del(`/project-groups/${id}`),
    addMember: (groupId, userId, roleType) => postForm(`/project-groups/${groupId}/members`, { user_id: userId, role_type: roleType }),
    removeMember: (groupId, userId) => del(`/project-groups/${groupId}/members/${userId}`)
  },

  // 系统日志
  logs: {
    list: (params) => get('/logs', params)
  },

  // 统计看板
  dashboard: {
    getStats: () => get('/dashboard/stats'),
    getProductStats: () => get('/dashboard/product-stats'),
    getWeeklyTrend: () => get('/dashboard/weekly-trend'),
    getRecentUploads: () => get('/dashboard/recent-uploads')
  },

  // 工作量统计
  workload: {
    getStats: (startDate, endDate) => get('/workload/stats', { start_date: startDate, end_date: endDate }),
    getSummary: (startDate, endDate) => get('/workload/summary', { start_date: startDate, end_date: endDate })
  }
}

export default api
