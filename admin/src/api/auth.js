import request from '@/utils/request'

// 获取验证码
export const getCaptcha = () => {
  return new Promise((resolve, reject) => {
    fetch('/api/auth/captcha', {
      method: 'GET',
      credentials: 'include'
    })
      .then(response => {
        const captchaId = response.headers.get('X-Captcha-ID')
        return response.blob().then(blob => {
          const url = URL.createObjectURL(blob)
          resolve({ url, captchaId })
        })
      })
      .catch(reject)
  })
}

export const login = (data) => {
  return request.post('/auth/login', data)
}

export const getUserInfo = () => {
  return request.get('/auth/info')
}

export const changePassword = (data) => {
  return request.post('/auth/change-password', data)
}
