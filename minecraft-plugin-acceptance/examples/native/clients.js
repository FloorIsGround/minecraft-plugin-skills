// Fictional local fixture; the launcher supplies a loopback port and run directory.
const fs = require('fs')
const path = require('path')
const mc = require(process.argv[2])
const directory = process.argv[3]
const port = Number(process.argv[4])
const version = process.argv[5]
const count = Number(process.argv[6])
const clients = []
const result = { ready: [], errors: [], ended: [], stages_sent: [] }
let closing = false
function save () {
  const target = path.join(directory, 'clients.json')
  fs.writeFileSync(target + '.tmp', JSON.stringify(result, null, 2))
  fs.renameSync(target + '.tmp', target)
}
function close () {
  closing = true
  clearInterval(timer)
  for (const client of clients) client.end('Fixture complete')
  save()
  setTimeout(() => process.exit(0), 500)
}
async function connect () {
  for (let i = 0; i < count; i++) {
    const username = 'Workshop' + String(i).padStart(3, '0')
    const client = mc.createClient({ host: '127.0.0.1', port, username, version, auth: 'offline', keepAlive: true })
    clients.push(client)
    client.on('login', () => { result.ready.push(username); save() })
    client.on('error', error => { result.errors.push({ username, error: String(error) }); save() })
    client.on('end', reason => { if (!closing) result.ended.push({ username, reason: String(reason) }); save() })
    await new Promise(resolve => setTimeout(resolve, 60))
  }
}
const timer = setInterval(() => {
  const control = path.join(directory, 'send.json')
  if (!fs.existsSync(control)) return
  let stage
  try { stage = JSON.parse(fs.readFileSync(control)).stage } catch { return }
  if (result.stages_sent.includes(stage) || result.ready.length !== count) return
  result.stages_sent.push(stage)
  for (const client of clients) client.chat('/workshop claim')
  save()
}, 100)
process.on('SIGTERM', close)
process.on('SIGINT', close)
save()
connect().catch(error => { result.errors.push({ error: String(error) }); save(); close() })
