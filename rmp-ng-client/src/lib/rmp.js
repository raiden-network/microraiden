"use strict";
const Web3 = require("web3");

export class RaidenMicropaymentsClient {

  constructor(
      web3url,
      contractAddr,
      contractABI,
      tokenAddr,
      tokenABI,
  ) {
    if (!web3url) {
      web3url = "http://localhost:8545";
    }
    if (web3url.currentProvider)
      this.web3 = new Web3(web3.currentProvider);
    else if (typeof web3url === 'string')
      this.web3 = new Web3(new Web3.providers.HttpProvider(web3url));

    contractAddr = contractAddr || window["RDNcontractAddr"];
    contractABI = contractABI || window["RDNcontractABI"];
    this.contract = this.web3.eth.contract(contractABI).at(contractAddr);

    tokenAddr = tokenAddr || window["RDNtokenAddr"];
    tokenABI = tokenABI || window["RDNtokenABI"];
    this.token = this.web3.eth.contract(tokenABI).at(tokenAddr);
  }

  getAccounts(callback) {
    return this.web3.eth.getAccounts(callback);
  }

  signHash(msg, account, callback) {
    return this.web3.eth
      .sign(account, msg, callback);
  }

  setChannelInfo(channel) {
    this.channel = channel
  }

  isChannelOpen(callback) {
    if (!this.channel.receiver || !this.channel.openBlockNumber
        || isNaN(this.channel.balance) || !this.channel.account) {
      return callback(new Error("No valid channelInfo"));
    }
    this.contract.ChannelCloseRequested({
      sender: this.account,
      receiver: this.channel.receiver
    }, {
      fromBlock: this.channel.openBlockNumber,
      toBlock: 'latest'
    }).get((e, r) => {
      if (e) {
        return callback(e);
      } else if (!r || r.length === 0) {
        return callback(null, true);
      } else {
        return callback(null, false);
      }
    });
  }

  openChannel(account, receiver, deposit, callback) {
    // send 'approve' transaction
    this.token.approve.sendTransaction(
      this.contract.address,
      deposit,
      {from: account},
      (err, res) => {
        if (err) {
          return callback(err);
        }
        const approveTxHash = res;
        // send 'createChannel' transaction
        this.contract.createChannel.sendTransaction(
          receiver,
          deposit,
          {from: account},
          (err, res) => {
            if (err) {
              return callback(err);
            }
            const createChannelTxHash = res;
            // wait for 'createChannel' transaction to be mined
            this.waitTx(createChannelTxHash, (err, res) => {
              if (err) {
                return callback(err);
              }
              const block = res;
              this.setChannelInfo({account, receiver, openBlockNumber: block.number, balance: 0});
              // return block
              return callback(null, this.channel);
            });
          }
        )
    });
  }

  incrementBalanceAndSign(amount, callback) {
    const newBalance = this.channel.balance + amount;
    this.contract.getChannelInfo.call(
      this.channel.account,
      this.channel.receiver,
      this.channel.openBlockNumber,
      {from: this.channel.account},
      (err, res) => {
        if (err) {
          return callback(err);
        }
        const deposit = res[1];
        if (newBalance > deposit) {
          return callback(new Error("Insuficient funds"));
        }
        this.contract.balanceMessageHash.call(
          this.channel.receiver,
          this.channel.openBlockNumber,
          newBalance,
          {from: this.channel.account},
          (err, res) => {
            if (err) {
              return callback(err);
            }
            this.setChannelInfo(Object.assign({}, this.channel, {balance: newBalance}));
            return callback(null, res);
          });
      });
  }

  waitTx(txHash, callback) {
    /*
    * Watch for a particular transaction hash and call the awaiting function when done;
    * Got it from: https://github.com/ethereum/web3.js/issues/393
    */
    let blockCounter = 15;
    // Wait for tx to be finished
    let filter = this.web3.eth.filter('latest').watch((err, blockHash) => {
      if (blockCounter<=0) {
        filter.stopWatching();
        filter = null;
        console.warn('!! Tx expired !!');
        if (callback)
          return callback(new Error("Tx expired"));
        else
          return false;
      }
      // Get info about latest Ethereum block
      let block = this.web3.eth.getBlock(blockHash);
      --blockCounter;
      // Found tx hash?
      if (block.transactions.indexOf(txHash) > -1) {
        // Tx is finished
        filter.stopWatching();
        filter = null;
        if (callback)
          return callback(null, block);
        else
          return block;
      // Tx hash not found yet?
      } else {
        // console.log('Waiting tx..', blockCounter);
      }
    });
  }

}

export default RaidenMicropaymentsClient;
