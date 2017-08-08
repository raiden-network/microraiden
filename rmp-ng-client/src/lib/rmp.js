"use strict";
var Web3 = require("web3");

export class RaidenMicropaymentsClient {

  constructor(web3url) {
    if (!web3url) {
      web3url = "http://localhost:8545";
    }
    if (web3url.currentProvider)
      this.web3 = new Web3(web3.currentProvider);
    else if (typeof web3url === 'string')
      this.web3 = new Web3(new Web3.providers.HttpProvider(web3url));
    console.log("RMP", this.web3);
  }

  getAccounts(cb) {
    return this.web3.eth.getAccounts(cb);
  }

  signMessage(msg, account, cb) {
    const encMsg = this.web3.fromAscii(msg);
    return this.web3.eth
      .sign(account, encMsg, cb);
  }

}

export default RaidenMicropaymentsClient;
