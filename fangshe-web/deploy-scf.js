#!/usr/bin/env node
/**
 * 纺设云 - 腾讯云SCF云函数部署脚本
 */

const https = require('https');
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

// ============ 配置 ============
const CONFIG = {
  secretId: process.env.TENCENT_SECRET_ID || 'your_secret_id_here',
  secretKey: process.env.TENCENT_SECRET_KEY || 'your_secret_key_here',
  region: 'ap-guangzhou',
  functionName: 'hunyuan-generate',
  namespace: 'default',
};

// 读取云函数代码
const functionCode = fs.readFileSync(path.join(__dirname, 'generate.js'), 'utf8');

// ============ 签名函数 ============
function sha256(data) {
  return crypto.createHash('sha256').update(data, 'utf8').digest('hex');
}

function hmacSha256(key, msg) {
  return crypto.createHmac('sha256', key).update(msg, 'utf8').digest('hex');
}

function tc3Sign(secretKey, date, service, strToSign) {
  const kDate = hmacSha256('TC3' + secretKey, date);
  const kService = hmacSha256(kDate, service);
  const kSigning = hmacSha256(kService, 'tc3_request');
  return hmacSha256(kSigning, strToSign);
}

function signTC3(secretId, secretKey, service, host, action, payload, region) {
  const now = Math.floor(Date.now() / 1000);
  const date = new Date(now * 1000).toISOString().split('T')[0];
  
  const payloadHash = sha256(JSON.stringify(payload));
  
  const httpRequestMethod = 'POST';
  const canonicalUri = '/';
  const canonicalQueryString = '';
  const canonicalHeaders = `content-type:application/json\nhost:${host}\n`;
  const signedHeaders = 'content-type;host';
  
  const canonicalRequest = [
    httpRequestMethod,
    canonicalUri,
    canonicalQueryString,
    canonicalHeaders,
    signedHeaders,
    payloadHash
  ].join('\n');
  
  const algorithm = 'TC3-HMAC-SHA256';
  const credentialScope = `${date}/${service}/tc3_request`;
  const hashedCanonicalRequest = sha256(canonicalRequest);
  
  const stringToSign = [
    algorithm,
    now,
    credentialScope,
    hashedCanonicalRequest
  ].join('\n');
  
  const signature = tc3Sign(secretKey, date, service, stringToSign);
  
  const authorization = `${algorithm} ` +
    `Credential=${secretId}/${credentialScope}, ` +
    `SignedHeaders=${signedHeaders}, ` +
    `Signature=${signature}`;
  
  return { authorization, now, date };
}

// ============ 发送请求 ============
function callAPI(action, payload, callback) {
  const service = 'scf';
  const host = `scf.${CONFIG.region}.myqcloud.com`;
  const endpoint = `https://${host}`;
  
  const { authorization, now } = signTC3(
    CONFIG.secretId, 
    CONFIG.secretKey, 
    service, 
    host, 
    action, 
    payload,
    CONFIG.region
  );
  
  const body = JSON.stringify(payload);
  
  const options = {
    hostname: host,
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Host': host,
      'X-TC-Action': action,
      'X-TC-Version': '2018-04-16',
      'X-TC-Timestamp': now.toString(),
      'X-TC-Region': CONFIG.region,
      'Authorization': authorization,
      'Content-Length': Buffer.byteLength(body)
    }
  };
  
  console.log(`\n📡 调用 API: ${action}`);
  
  const req = https.request(options, (res) => {
    let data = '';
    res.on('data', chunk => data += chunk);
    res.on('end', () => {
      try {
        const result = JSON.parse(data);
        callback(result);
      } catch (e) {
        callback({ error: data });
      }
    });
  });
  
  req.on('error', (e) => {
    callback({ error: e.message });
  });
  
  req.write(body);
  req.end();
}

// ============ 部署流程 ============
async function deploy() {
  console.log('🚀 开始部署云函数...\n');
  console.log(`📦 函数名: ${CONFIG.functionName}`);
  console.log(`📍 区域: ${CONFIG.region}`);
  
  // 1. 检查函数是否存在
  console.log('\n1️⃣ 检查现有函数...');
  
  return new Promise((resolve) => {
    callAPI('GetFunction', {
      FunctionName: CONFIG.functionName,
      Namespace: CONFIG.namespace
    }, (result) => {
      if (result.Response && !result.Response.FunctionName) {
        // 函数不存在，需要创建
        console.log('   ℹ️ 函数不存在，准备创建...');
        createFunction(resolve);
      } else if (result.Response && result.Response.FunctionName) {
        console.log('   ✅ 函数已存在，准备更新...');
        updateFunction(resolve);
      } else if (result.Error) {
        console.log(`   ❌ 检查失败: ${result.Error.Message || JSON.stringify(result)}`);
        createFunction(resolve);
      } else {
        console.log('   ❌ 未知响应:', JSON.stringify(result));
        resolve();
      }
    });
  });
}

function createFunction(resolve) {
  console.log('\n2️⃣ 创建云函数...');
  
  const handler = 'index.main_handler';
  
  // 压缩代码
  const codeZip = require('zlib').gzipSync(
    Buffer.from(`const https = require('https');
const crypto = require('crypto');

${functionCode.replace("const CONFIG = {", `const CONFIG = {
  secretId: '${CONFIG.secretId}',`).replace("  secretKey: process.env.TENCENT_SECRET_KEY || 'your_secret_key_here'", `  secretKey: '${CONFIG.secretKey}'`)}`)
  );
  
  // 尝试直接创建
  callAPI('CreateFunction', {
    FunctionName: CONFIG.functionName,
    Handler: handler,
    Runtime: 'Nodejs18.x',
    Code: {
      ZipFile: codeZip.toString('base64')
    },
    Description: '纺设云定制 - AI生图云函数',
    Timeout: 60,
    MemorySize: 256,
    Namespace: CONFIG.namespace
  }, (result) => {
    if (result.Response && result.Response.FunctionName) {
      console.log('   ✅ 云函数创建成功!');
      console.log(`   📛 函数名: ${result.Response.FunctionName}`);
      createTrigger(resolve);
    } else if (result.Error) {
      console.log(`   ❌ 创建失败: ${result.Error.Message}`);
      console.log('   💡 请手动在控制台创建，或检查配额');
      resolve();
    } else {
      console.log('   📋 响应:', JSON.stringify(result));
      resolve();
    }
  });
}

function updateFunction(resolve) {
  console.log('\n2️⃣ 更新云函数代码...');
  
  const codeZip = require('zlib').gzipSync(
    Buffer.from(`const https = require('https');
const crypto = require('crypto');

${functionCode}`)
  );
  
  callAPI('UpdateFunctionCode', {
    FunctionName: CONFIG.functionName,
    ZipFile: codeZip.toString('base64'),
    Handler: 'index.main_handler',
    Namespace: CONFIG.namespace
  }, (result) => {
    if (result.Response) {
      console.log('   ✅ 云函数更新成功!');
      createTrigger(resolve);
    } else if (result.Error) {
      console.log(`   ❌ 更新失败: ${result.Error.Message}`);
      resolve();
    } else {
      console.log('   📋 响应:', JSON.stringify(result));
      resolve();
    }
  });
}

function createTrigger(resolve) {
  console.log('\n3️⃣ 创建API网关触发器...');
  
  // 生成随机触发器名称
  const triggerName = `hunyuan-trigger-${Date.now()}`;
  
  callAPI('CreateTrigger', {
    FunctionName: CONFIG.functionName,
    TriggerName: triggerName,
    Type: 'apigw',
    TriggerDesc: JSON.stringify({
      api陵号: 'service-xxxx',
      integratedResponse: true
    }),
    Namespace: CONFIG.namespace
  }, (result) => {
    if (result.Response) {
      console.log('   ✅ 触发器创建成功!');
      getAPIGateway(resolve);
    } else if (result.Error) {
      if (result.Error.Message && result.Error.Message.includes('already exists')) {
        console.log('   ℹ️ 触发器已存在');
        getAPIGateway(resolve);
      } else {
        console.log(`   ⚠️ 触发器创建: ${result.Error.Message || JSON.stringify(result)}`);
        console.log('   💡 请手动在控制台创建API网关触发器');
        resolve();
      }
    } else {
      console.log('   📋 响应:', JSON.stringify(result));
      resolve();
    }
  });
}

function getAPIGateway(resolve) {
  console.log('\n4️⃣ 获取API网关地址...');
  
  callAPI('ListTriggers', {
    FunctionName: CONFIG.functionName,
    Namespace: CONFIG.namespace
  }, (result) => {
    if (result.Response && result.Response.Triggers) {
      const apigwTrigger = result.Response.Triggers.find(t => t.Type === 'apigw');
      if (apigwTrigger) {
        console.log('   ✅ API网关触发器信息:');
        console.log(`   📍 地址格式: https://${apigwTrigger.TriggerName}.service.dsmarket.com`);
      } else {
        console.log('   ℹ️ 未找到API网关触发器');
        console.log('   💡 请手动创建: 控制台 → 云函数 → 触发管理 → 新建触发器');
      }
    }
    console.log('\n📝 下一步:');
    console.log('   1. 访问 https://console.cloud.tencent.com/scf');
    console.log('   2. 找到函数 ' + CONFIG.functionName);
    console.log('   3. 触发管理 → 创建API网关触发器');
    console.log('   4. 把生成的访问地址发给我，我帮您填入配置');
    resolve();
  });
}

// 运行
deploy().then(() => {
  console.log('\n✨ 部署流程完成');
  process.exit(0);
}).catch(e => {
  console.error('❌ 部署失败:', e);
  process.exit(1);
});
