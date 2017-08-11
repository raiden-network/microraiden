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
  }

  loadStoredChannel(account, receiver) {
    if (typeof localStorage === "undefined" || localStorage === null) {
      var LocalStorage = require('node-localstorage').LocalStorage;
      localStorage = new LocalStorage('./local_storage');
    }
    if (!localStorage) {
      this.channel = undefined;
      return;
    }
    const key = account + "|" + receiver;
    const value = localStorage.getItem(key);
    if (value) {
      this.channel = JSON.parse(value);
    } else {
      this.channel = undefined;
    }
  }

  forgetStoredChannel() {
    if (localStorage) {
      const key = this.channel.account + "|" + this.channel.receiver;
      localStorage.removeItem(key);
    }
    this.channel = undefined;
  }

  setChannelInfo(channel) {
    this.channel = channel;
    if (localStorage) {
      const key = channel.account + "|" + channel.receiver;
      localStorage.setItem(key, JSON.stringify(this.channel));
    }
  }

  getAccounts(callback) {
    return this.web3.eth.getAccounts(callback);
  }

  signHash(msg, account, callback) {
    try {
      console.log("Signing", msg, account);
      return this.web3.eth
        .sign(account, msg, callback);
    } catch (e) {
      return callback(e);
    }
  }

  isChannelValid() {
    if (!this.channel || !this.channel.receiver || !this.channel.openBlockNumber
      || isNaN(this.channel.balance) || !this.channel.account) {
      return false;
    }
    return true;
  }

  isChannelOpen(callback) {
    if (!this.isChannelValid()) {
      return callback(new Error("No valid channelInfo"));
    }
    this.contract.ChannelCloseRequested({
      _sender: this.channel.account,
      _receiver: this.channel.receiver,
      _open_block_number: this.channel.openBlockNumber,
    }, {
      fromBlock: this.channel.openBlockNumber,
      toBlock: 'latest'
    }).get((err, res) => {
      if (err) {
        return callback(err);
      } else if (!res || res.length === 0) {
        return callback(null, true);
      } else {
        return callback(null, false);
      }
    });
  }

  openChannel(account, receiver, deposit, callback) {
    if (this.isChannelValid()) {
      console.warn("Already valid channel will be forgotten:", this.channel);
    }
    // send 'approve' transaction
    this.token.approve.sendTransaction(
      this.contract.address,
      deposit,
      {from: account},
      (err, txHash) => {
        if (err) {
          return callback(err);
        }
        this.waitTx(txHash, (err, receipt) => {
          if (err) {
            return callback(err);
          }
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
              this.waitTx(createChannelTxHash, (err, receipt) => {
                if (err) {
                  return callback(err);
                }
                this.setChannelInfo({account, receiver, openBlockNumber: receipt.blockNumber, balance: 0});
                // return block
                return callback(null, this.channel);
              });
            }
          )
        });
      });
  }

  topUpChannel(deposit, callback) {
    if (!this.isChannelValid()) {
      return callback(new Error("No valid channelInfo"));
    }
    // send 'approve' transaction
    this.token.approve.sendTransaction(
      this.contract.address,
      deposit,
      {from: account},
      (err, res) => {
        if (err) {
          return callback(err);
        }
        // send 'createChannel' transaction
        this.contract.topUp.sendTransaction(
          this.channel.receiver,
          this.channel.openBlockNumber,
          deposit,
          {from: account},
          (err, res) => {
            if (err) {
              return callback(err);
            }
            const topUpTxHash = res;
            // wait for 'topUp' transaction to be mined
            this.waitTx(topUpTxHash, (err, receipt) => {
              if (err) {
                return callback(err);
              }
              // return block number
              return callback(null, receipt.blockNumber);
            });
          }
        )
      });
  }

  signBalance(newBalance, callback) {
    if (!this.isChannelValid()) {
      return callback(new Error("No valid channelInfo"));
    }
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
        const msgHash = res;
        // ask for signing of this message
        this.signHash(msgHash, this.channel.account, (err, res) => {
          if (err) {
            return callback(err);
          }
          const sign = res;
          // return signed message
          if (newBalance === this.channel.balance && !this.channel.sign) {
            this.channel.sign = sign;
          }
          return callback(null, sign);
        });
      });
  }

  incrementBalanceAndSign(amount, callback) {
    if (!this.isChannelValid()) {
      return callback(new Error("No valid channelInfo"));
    }
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
        console.log("Channel info:", res);
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
          const sign = res;
          this.setChannelInfo(Object.assign(
            {},
            this.channel,
            {
              balance: newBalance,
              sign: sign
            }
          ));
          return callback(null, sign);
        });
      });
  }

  closeChannel(receiverSig, callback) {
    if (!this.isChannelValid()) {
      return callback(new Error("No valid channelInfo"));
    }
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
        const sign = res;
        const params = [
          this.channel.receiver,
          this.channel.openBlockNumber,
          this.channel.balance,
          sign
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
            const txHash = res;
            return this.waitTx(txHash, (err, receipt) => {
              if (err) {
                return callback(err);
              }
              return callback(null, receipt.blockNumber);
            });
          }
        );
      });
    });
  }

  settleChannel(callback) {
    if (!this.isChannelValid()) {
      return callback(new Error("No valid channelInfo"));
    }
    return this.isChannelOpen((err, res) => {
      if (err) {
        return callback(err);
      } else if (res) {
        return callback(new Error("Tried settling open channel"));
      }
      return this.contract.settle.sendTransaction(
        this.channel.receiver,
        this.channel.openBlockNumber,
        {from: this.channel.account},
        (err, res) => {
          if (err) {
            return callback(err);
          }
          const txHash = res;
          return this.waitTx(txHash, (err, receipt) => {
            if (err) {
              return callback(err);
            }
            return callback(null, receipt.blockNumber);
          });
        }
      );
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
        return callback(new Error("Tx expired"));
      }
      // Get info about latest Ethereum block
      return this.web3.eth.getTransactionReceipt(txHash, (err, receipt) => {
        --blockCounter;
        if (err) {
          return callback(err);
        } else if (!receipt || !receipt.blockNumber) {
          return console.log('Waiting tx..', blockCounter);
        }
        // Tx is finished
        filter.stopWatching();
        filter = null;
        return callback(null, receipt);
      });
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

