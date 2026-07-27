/**
 * hunyuanGenerate 云函数 v2
 * 封装腾讯混元2.0文生图API（同步/异步双模式）
 *
 * 使用 Node.js 原生 https（不依赖 uniCloud.httpclient）
 */

const crypto = require('crypto')
const cloud = require('wx-server-sdk')
const https = require('https')

cloud.init({ env: cloud.DYNAMIC_CURRENT_ENV })
const db = cloud.database()

// ============ 配置（建议后续迁移到云函数环境变量）============
const SECRET_ID  = process.env.TENCENT_SECRET_ID || 'your_secret_id_here'
const SECRET_KEY = process.env.TENCENT_SECRET_KEY || 'your_secret_key_here'
const REGION     = 'ap-guangzhou'
const APP_ID     = 'wx9392877263062240'

// ============================================================
// 腾讯云 TC3-HMAC-SHA256 签名
// ============================================================
function sha256(data) {
  return crypto.createHash('sha256').update(data, 'utf8').digest('hex')
}
function hmacSha256(key, msg) {
  return crypto.createHmac('sha256', key).update(msg, 'utf8').digest('hex')
}
function tc3Sign(secretKey, date, service, strToSign) {
  const kDate    = hmacSha256('TC3' + secretKey, date)
  const kService = hmacSha256(kDate, service)
  const kSigning = hmacSha256(kService, 'tc3_request')
  return hmacSha256(kSigning, strToSign)
}

function buildAuth(params, action) {
  const now    = new Date()
  const ts     = Math.floor(now.getTime() / 1000)
  const date   = now.toISOString().split('T')[0]  // YYYY-MM-DD
  const service = 'hunyuan'

  const payload      = JSON.stringify(params)
  const hashedPayload = sha256(payload)

  const signedHeaders = 'content-type;host'
  const canonicalHeaders = `content-type:application/json\nhost:${service}.tencentcloudapi.com\n`

  const canonicalRequest = [
    'POST', '/', '',
    canonicalHeaders,
    signedHeaders,
    hashedPayload
  ].join('\n')

  const hashedCanonReq = sha256(canonicalRequest)

  const stringToSign = [
    'TC3-HMAC-SHA256',
    ts,
    `${date}/${service}/tc3_request`,
    hashedCanonReq
  ].join('\n')

  const sig = tc3Sign(SECRET_KEY, date, service, stringToSign)

  const auth = [
    `TC3-HMAC-SHA256 Credential=${SECRET_ID}/${date}/${service}/tc3_request, `,
    `SignedHeaders=${signedHeaders}, Signature=${sig}`
  ].join('')

  return { auth, ts }
}

// ============================================================
// 发送 HTTPS 请求（Node 原生，不依赖任何外部库）
// ============================================================
function httpsPost(endpoint, params, headers) {
  return new Promise((resolve, reject) => {
    const body = JSON.stringify(params)
    const url  = new URL(endpoint)

    const options = {
      hostname: url.hostname,
      path:     url.pathname,
      method:   'POST',
      headers:  {
        'Content-Type':  'application/json',
        'Content-Length': Buffer.byteLength(body),
        ...headers,
      },
      timeout: 30000,
    }

    const req = https.request(options, (res) => {
      let data = ''
      res.on('data', chunk => data += chunk)
      res.on('end', () => {
        try {
          resolve(JSON.parse(data))
        } catch {
          resolve({ raw: data })
        }
      })
    })

    req.on('error', reject)
    req.on('timeout', () => { req.destroy(); reject(new Error('请求超时')) })

    req.write(body)
    req.end()
  })
}

// ============================================================
// 混元文生图 API
// ============================================================
const PRODUCT_MAP = {
  bijou:      'bedding duvet cover pillowcase four-piece set',
  pillow:     'pillow cushion cover sofa cushion',
  curtain:    'curtain window drapery',
  cushion:    'throw pillow cushion',
  blanket:    'blanket throw blanket',
  tablecloth: 'tablecloth placemat',
}

function buildPrompt(raw, productType, styleTags) {
  const prod = PRODUCT_MAP[productType] || 'home textile fabric'
  const style = styleTags?.length ? styleTags.join(', ') : 'high quality fabric texture'
  const neg = 'low quality, blurry, watermark, text, logo, deformed, ugly, bad anatomy, extra fingers'
  return {
    Prompt: `${raw}, ${prod}, seamless pattern, detailed texture, ${style}, 4K`,
    NegativePrompt: neg,
    Width: 1024,
    Height: 1024,
    Style: 'photo',
    CfgScale: 7.5,
    Steps: 25,
  }
}

async function callHunyuan(prompt, productType, styleTags) {
  const endpoint = 'https://hunyuan.tencentcloudapi.com'
  const action   = 'GenerateImages'
  const version  = '2023-09-01'
  const params   = buildPrompt(prompt, productType, styleTags)
  const { auth, ts } = buildAuth(params, action)

  const data = await httpsPost(endpoint, params, {
    'Authorization': auth,
    'X-TC-Action':   action,
    'X-TC-Version':  version,
    'X-TC-Timestamp': String(ts),
    'X-TC-Region':   REGION,
  })

  console.log('[hunyuan] response:', JSON.stringify(data).substring(0, 500))

  if (!data?.Response) throw new Error(`API异常: ${JSON.stringify(data).substring(0, 200)}`)
  const { Error: err, Images, TaskId } = data.Response
  if (err) throw new Error(`混元错误: ${err.Code} - ${err.Message}`)

  // 同步返回图片
  if (Images?.length > 0) {
    return {
      status: 'completed',
      taskId: TaskId || '',
      images: Images.map((img, i) => ({ url: img.Url || img.ImageUrl, index: i })),
    }
  }

  // 异步模式：返回 taskId 供前端轮询
  if (TaskId) {
    return { status: 'pending', taskId: TaskId, images: [] }
  }

  throw new Error('混元API返回无可用数据')
}

async function queryTask(taskId) {
  const endpoint = 'https://hunyuan.tencentcloudapi.com'
  const action    = 'QueryImages'
  const version   = '2023-09-01'
  const params   = { TaskId: taskId }
  const { auth, ts } = buildAuth(params, action)

  const data = await httpsPost(endpoint, params, {
    'Authorization': auth,
    'X-TC-Action':   action,
    'X-TC-Version':  version,
    'X-TC-Timestamp': String(ts),
    'X-TC-Region':   REGION,
  })

  if (!data?.Response) return { taskId, status: 'failed', images: [], error: JSON.stringify(data) }
  const { Error: err, Images, Status } = data.Response
  if (err) return { taskId, status: 'failed', images: [], error: err.Message }

  const statusMap = { 0: 'pending', 1: 'completed', 2: 'failed' }
  return {
    taskId,
    status: statusMap[Status] || 'pending',
    images: Images?.map((img, i) => ({ url: img.Url || img.ImageUrl, index: i })) || [],
  }
}

// ============================================================
// 云函数入口
// ============================================================
exports.main = async (event, context) => {
  const { action = 'generate', ...params } = event

  try {
    if (action === 'generate') {
      const { prompt, productType = 'bijou', styleTags = [], referenceImage } = params

      if (!prompt?.trim()) return { code: -1, msg: '请输入设计描述' }

      // TODO: referenceImage 需先上传至云存储获得 URL，再传给混元
      if (referenceImage) console.log('[hunyuan] referenceImage provided:', referenceImage.substring(0, 80))

      const result = await callHunyuan(prompt, productType, styleTags)

      if (result.status === 'completed') {
        return {
          code: 0,
          msg: '生成成功',
          data: {
            images: result.images,
            taskId: result.taskId,
            prompt,
            productType,
          }
        }
      }

      // 异步模式：返回 taskId，告知前端轮询间隔
      return {
        code: 0,
        msg: '任务已提交，请等待',
        data: {
          taskId: result.taskId,
          status: 'pending',
          pollInterval: 3000,
          prompt,
          productType,
        }
      }
    }

    if (action === 'query') {
      const { taskId } = params
      if (!taskId) return { code: -1, msg: '缺少 taskId' }
      const result = await queryTask(taskId)
      return {
        code: 0,
        msg: result.status === 'completed' ? '生成完成' : '生成中...',
        data: result,
      }
    }

    return { code: -1, msg: `未知操作: ${action}` }

  } catch (err) {
    console.error('[hunyuanGenerate] error:', err)
    return { code: -1, msg: err.message || '生成失败，请重试' }
  }
}
