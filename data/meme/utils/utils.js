import { LoadingAnimation } from "./Loading.js"
import { printBanner } from "./banner.js"
import { config } from "../config.js"
import { ethers } from "ethers"
import dotenv from "dotenv"
import chalk from "chalk"
import fs from "fs"

dotenv.config(".env")

let provider = new ethers.providers.WebSocketProvider(
  `wss://eth-mainnet.alchemyapi.io/v2/${process.env.ALCHEMY_API_KEY}`
)
let loader = new LoadingAnimation("🌍 requesting...")

export async function findKing(
  address
) {
  printBanner(
    `Configuration Info`,
    [
      {
        label: "🌕 Token Address ",
        content: `${address}`,
      },
    ],
    80
  )
  console.log(
    chalk.red(
      "If this is your first time running the script, please be patient and take a cup of coffee☕️"
    )
  )
  let Minters = await getMEMELogs(address)
  // 写入文件
  fs.writeFileSync("meme.json", JSON.stringify(Minters, null, 4))

  console.log("---------------------------------------------------")
  console.log(Minters)
  console.log(`✅ Finish!`)
  process.exit(0)
}

const getMEMELogs = async (address) => {
  if (!address) return
  let Minters = []
    let prjMinters = []
    loader.start()
    console.log(`🔍 getting logs of ${address}...`)
    let logs = await getLogs(address)
    loader.stop()
    console.log(
      chalk.green(
        `✅ logs' length: ${logs.length}, successful writting in locale`
      )
    )
    if (logs) {
      for (let log of logs) {
        let add = "0x" + log.topics[2].slice(26)
        if (prjMinters.findIndex((e) => e.address == add) < 0)
          prjMinters.push({
            address: add,
            amount: 1,
          })
        else
          prjMinters.map((e) => {
            if (e.address == add) e.amount++
            return e
          })
      }
      Minters.push(prjMinters)
    }
  return Minters
}

const getLogs = async (address) => {
  let logs = []
  let path = `./meme/${address}.json`
  if (fs.existsSync(path)) logs = await readFromLocale(path)
  else {
    try {
      logs = await provider.getLogs({
        address,
        fromBlock: config.fromBlock,
        topics: [
          null,
          "0x0000000000000000000000000000000000000000000000000000000000000000",
          null,
          null,
        ],
      })
      writeToLocale(address, logs)
    } catch (error) {
      if (error.code == "-32602" || error.code == "-32000") {
        loader.stop()
        logs = await fragment(address)
        writeToLocale(address, logs)
      }
    }
  }
  return logs
}
const fragment = async (address) => {
  console.log(chalk.yellow("⏬ segmented downloading...please be patient..."))
  loader.start()
  let fromBlock = config.fromBlock
  let toBlock = await provider.getBlockNumber()
  let logs = []
  while (fromBlock + 4001 < toBlock) {
    fromBlock += 2001
    let _logs = await provider.getLogs({
      fromBlock: fromBlock,
      toBlock: fromBlock + 2000,
      address,
      topics: [
        null,
        "0x0000000000000000000000000000000000000000000000000000000000000000",
        null,
        null,
      ],
    })
    logs = [...logs, ..._logs]
  }
  logs = [
    ...logs,
    ...(await provider.getLogs({
      fromBlock: fromBlock + 2001,
      toBlock,
      address,
      topics: [
        null,
        "0x0000000000000000000000000000000000000000000000000000000000000000",
      ],
    })),
  ]
  loader.stop()
  return logs
}

const readFromLocale = async (path) => {
  return new Promise((resolve) => {
    let logs = []
    fs.readFile(path, (err, data) => {
      if (err) console.error(err)
      if (data.length) logs = JSON.parse(data)
      resolve(logs)
    })
  })
}

const writeToLocale = (address, logs) => {
  let path = `./meme/${address}.json`
  fs.writeFile(path, JSON.stringify(logs, null, 4), () => {
    console.log(`successful writting in locale`)
  })
}

export const formatTxt = (path) => {
  let res = fs.readFileSync(path, "utf8")
  let my_address = []
  res.split(/\r?\n/).forEach((add) => {
    my_address.push(add.trim())
  })
  return my_address
}
