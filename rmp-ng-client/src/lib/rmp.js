"use strict";
var Web3 = require("web3");

export class RaidenMicropaymentsClient {
  constructor(web3url) {
    if (!web3url) {
      web3url = "http://localhost:8545";
    }
    this._web3 = new Web3(new Web3.providers.HttpProvider(web3url));
    console.log("RMP", this.web3);
  }

  get web3() {
    return (window && window.web3) || this._web3;
  }

  getAccounts() {
    return this.web3.eth.accounts;
  }

  signMessage(msg, account, cb) {
    console.log('C', this.getAccounts(), msg, account);
    return this.web3.eth
      .sign(account, msg, cb);
  }
}

export default RaidenMicropaymentsClient;
