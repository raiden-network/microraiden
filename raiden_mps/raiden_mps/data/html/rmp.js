"use strict";
//const Web3 = require("web3");

class RaidenMicropaymentsClient {

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
    if (web3url.currentProvider) {
      this.web3 = new Web3(web3.currentProvider);
    }
    else if (typeof web3url === 'string') {
      this.web3 = new Web3(new Web3.providers.HttpProvider(web3url));
    }

    contractAddr = contractAddr || window["RDNcontractAddr"];
    contractABI = contractABI || window["RDNcontractABI"];
    this.contract = this.web3.eth.contract(contractABI).at(contractAddr);

    tokenAddr = tokenAddr || window["RDNtokenAddr"];
    tokenABI = tokenABI || window["RDNtokenABI"];
    this.token = this.web3.eth.contract(tokenABI).at(tokenAddr);

    this.loadStoredChannel();
  }

  loadStoredChannel() {
    if (typeof localStorage === "undefined" || localStorage === null) {
      var LocalStorage = require('node-localstorage').LocalStorage;
      localStorage = new LocalStorage('./local_storage');
    }
    if (localStorage.channel) {
      this.channel = JSON.parse(localStorage.channel);
    }
  }

  getAccounts(callback) {
    return this.web3.eth.getAccounts(callback);
  }

  signHash(msg, account, callback) {
    return this.web3.eth
      .sign(account, msg, callback);
  }

  setChannelInfo(channel) {
    this.channel = channel;
    if (localStorage) {
      localStorage.channel = JSON.stringify(this.channel);
    }
  }

  isChannelOpen(callback) {
    if (!this.channel.receiver || !this.channel.openBlockNumber
      || isNaN(this.channel.balance) || !this.channel.account) {
      return callback(new Error("No valid channelInfo"));
    }
    this.contract.ChannelCloseRequested({
      _sender: this.account,
      _receiver: this.channel.receiver,
      _open_block_number: this.channel.openBlockNumber,
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

  signBalance(newBalance, callback) {
    if (newBalance === null) {
      newBalance = this.channel.balance;
    }
    if (newBalance === this.channel.balance && this.channel.sign) {
      return callback(null, this.channel.sign);
    }
    return this.contract.balanceMessageHash.call(
      this.channel.receiver,
      this.channel.openBlockNumber,
      newBalance,
      {from: this.channel.account},
      (err, res) => {
        if (err) {
          return callback(err);
        }
        // ask for signing of this message
        this.signHash(res, this.account, (err, res) => {
          if (err) {
            return callback(err);
          }
          // return signed message
          if (newBalance === this.channel.balance && !this.channel.sign) {
            this.channel.sign = res;
          }
          return callback(null, res);
        });
      });
  }

  incrementBalanceAndSign(amount, callback) {
    const newBalance = this.channel.balance + amount;
    // get current deposit
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
          return callback(new Error("Insuficient funds: current = "+deposit+
            ", required = +"+newBalance-deposit));
        }
        // get hash for new balance proof
        return this.signBalance(newBalance, (err, res) => {
          if (err) {
            return callback(err);
          }
          this.setChannelInfo(Object.assign(
            {},
            this.channel,
            {
              balance: newBalance,
              sign: res
            }
          ));
          return callback(null, res);
        });
      });
  }

  closeChannel(receiverSig, callback) {
    return this.isChannelOpen((err, res) => {
      if (err) {
        return callback(err);
      } else if (!res) {
        return callback(new Error("Tried closing already closed channel"));
      }
      let func;
      if (!this.channel.sign) {
        func = (cb) => this.signBalance(this.channel.balance, cb);
      } else {
        func = (cb) => cb(null, this.channel.sign);
      }
      return func((err, res) => {
        if (err) {
          return callback(err);
        }
        const params = [
          this.channel.receiver,
          this.channel.openBlockNumber,
          this.channel.balance,
          res
        ];
        if (receiverSig) {
          params.push(receiverSig);
        }
        return this.contract.close.sendTransaction(
          ...params,
          {from: this.channel.account},
          (err, res) => {
            if (err) {
              return callback(err);
            }
            return this.waitTx(res, (err, res) => {
              if (err) {
                return callback(err);
              }
              return callback(null, res.number);
            });
          }
        );
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
          console.log('Waiting tx..', blockCounter);
        }
    });
  }

}

if (typeof module !== 'undefined' && typeof module.exports !== 'undefined') {
  module.exports.RaidenMicropaymentsClient = RaidenMicropaymentsClient;
} else if (typeof define === 'function' && define.amd) {
  define([], function() {
    return RaidenMicropaymentsClient;
  });
} else {
  window.RaidenMicropaymentsClient = RaidenMicropaymentsClient;
}

