require("dotenv").config();
const fs = require("fs");
const axios = require("axios");
const async = require("async");
const { Alchemy, Network, Utils } = require("alchemy-sdk");


// Optional Config object, but defaults to demo api-key and eth-mainnet.
const settings = {
  apiKey: process.env.ALCHEMY_API_KEY,
  network: Network.ETH_MAINNET,
};

const alchemy = new Alchemy(settings);

const etherscanApiKey = process.env.apiKey;

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}


// getnormalTxCount get normal tx count of one contract address
async function getnormalTxCount(contract_address) {
  // https://tokenview.io/api/search/0x1352809528bbffb0e4b0c55cba8fd72bcae6e76e
  try {
    const response = await axios.get(
      `https://tokenview.io/api/search/${contract_address}`
    );
    if (response.data.msg == "成功") {
      const normal_tx_count = response.data?.data[0]?.normalTxCount
      return normal_tx_count
    } else {
      console.log("response.data.msg !== 成功");
      return
    }
  } catch (error) {
    console.error("Get normalTxCount Failed Error:", error);
  }
}


// getContractAbi get abi of one contract address
async function getContractAbi(contract_address) {
  const apiKey = etherscanApiKey;
  const contractAddress = contract_address;

  try {
    await sleep(100);
    const response = await axios.get(
      `https://api.etherscan.io/api?module=contract&action=getabi&address=${contractAddress}&apikey=${apiKey}`
    );
    if (response.data.status == 1) {
      const abi = response.data.result;
      return abi;
    } else {
      console.log("Contract Is Not Verify:", contract_address);
      return;
    }
  } catch (error) {
    console.error("Get Contract Abi Failed Error:", error);
  }
}


// getFirstTransfer get first transfer of one contract address
const getFirstTransfer = async (contract_address) => {
  // Calling the getAssetTransfers function and filters using the following parameters
  const allTransfers = await alchemy.core.getAssetTransfers({
    fromBlock: "0x0",
    contractAddresses: [contract_address],
    excludeZeroValue: true,
    category: ["erc20"],
  });

  // printing the first indexed transfer event to console
  let hexValue = allTransfers.transfers[0].blockNum;
  let decimalValue = parseInt(hexValue, 16);

  return decimalValue;
};


// getAllNounsDaoProposalsEver get all proposals of one contract address
async function getAllNounsDaoProposalsEver(contract_address, alias) {
  console.log(`Start Get ${alias} Logs✅`);
  let TOKEN = {};
  if (fs.existsSync(`token/${alias}_${contract_address}.json`)) {
    const data = fs.readFileSync(`token/${alias}_${contract_address}.json`);
    TOKEN = JSON.parse(data);
  } else {
    fs.writeFileSync(`token/${alias}_${contract_address}.json`, "{}");
    console.log(
      `Create File token/${alias}_${contract_address}.json Success✅`
    );
  }

  const NOUNS_DAO_CONTRACT_ADDRESS = contract_address;
  const nounsDaoAbiString = await getContractAbi(contract_address);
  if (!nounsDaoAbiString) {
    return;
  }
  const NOUNS_DAO_INTERFACE = new Utils.Interface(nounsDaoAbiString);
  const NOUNS_DAO_PROPOSAL_CREATED_TOPICS =
    NOUNS_DAO_INTERFACE.encodeFilterTopics(
      "Transfer(address,address,uint256)",
      []
    );

  let fromBlock = await getFirstTransfer(contract_address);
  const latestBlock = await alchemy.core.getBlockNumber();
  // Except for some data that is too early
  while (fromBlock <= latestBlock) {
    const toBlock = Math.min(fromBlock + 2000, latestBlock);

    console.log("Get Logs Success✅");
    console.log(
      "schedule:",
      toBlock / latestBlock,
      "contract_address:",
      contract_address,
      "alias:",
      alias
    );

    const logs = await alchemy.core.getLogs({
      fromBlock: fromBlock,
      toBlock: toBlock,
      address: NOUNS_DAO_CONTRACT_ADDRESS,
      topics: NOUNS_DAO_PROPOSAL_CREATED_TOPICS,
    });
    for (const log of logs) {
      const add = "0x" + log.topics[2].slice(26);
      if (add.toLowerCase() in TOKEN) {
      } else {
        TOKEN[add.toLowerCase()] = "";
      }
    }
    const data = JSON.stringify(TOKEN, null, 2);
    fs.writeFileSync(`token/${alias}_${contract_address}.json`, data);

    fromBlock = toBlock + 1;
  }
}


// delete_file_line delete file second line
async function delete_file_line() {
  // Delete file second line
  const data = fs.readFileSync("token.json", "utf8").split("\n");

  data.splice(1, 1);

  fs.writeFileSync("token.json", data.join("\n"));

  console.log("Delete File Line Success✅");
}


// processAllAddresses process all addresses
async function processAllAddresses() {
  const data = fs.readFileSync("token.json");
  const jsonData = JSON.parse(data);
  const queue = async.queue(async (task) => {
    const { contract_address, alias } = task;
    await getAllNounsDaoProposalsEver(contract_address, alias);
    await delete_file_line();
  }, 1);
  queue.concurrency = 1;

  for (const key in jsonData) {
    const value = jsonData[key];
    // key and value
    // getAllNounsDaoProposalsEver get all logs of one contract address
    // Wait for all the logs of a address to get the log
    // Get normalTxCount
    const tx_count = await getnormalTxCount(key);
    console.log("tx_count:", tx_count);
    // sleep 4s
    sleep(4000)
    // Remove the address with less than 1024
    await queue.push({ contract_address: key, alias: value });
  }
}

processAllAddresses();
