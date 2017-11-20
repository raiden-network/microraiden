import * as Web3 from "web3";
import "web3-typescript-typings";
import * as BigNumber from "bignumber.js";
import { LocalStorage } from "node-localstorage";

function _(func: Function) {
  /* Convert a callback-based func to return a promise */
  return (...params): Promise<any> =>
    new Promise((resolve, reject) =>
      func(...params, (err, res) => err ? reject(err) : resolve(res)));
}

export interface MicroChannel {
  /* MicroRaiden.channel data structure */
  account: string;
  receiver: string;
  block: number;
  balance: number;
  sign?: string;
}

export interface MicroChannelInfo {
  /* MicroRaiden.getChannelInfo result */
  state: string;
  block: number;
  deposit: number;
}

export interface MicroTokenInfo {
  /* MicroRaiden.getTokenInfo result */
  name: string;
  symbol: string;
  decimals: number;
  balance: number;
}

export class MicroRaiden {
  web3: Web3;
  channel: MicroChannel;
  token: Web3.ContractInstance;
  contract: Web3.ContractInstance;
  decimals: number = 0;

  constructor(
    web3url: string | { currentProvider: any },
    contractAddr: string,
    contractABI: any[],
    tokenAddr: string,
    tokenABI: any[],
  ) {
    if (!web3url) {
      web3url = "ws://localhost:8546";
    }
    if (typeof web3url === 'string') {
      this.web3 = new Web3(new Web3.providers.HttpProvider(web3url));
    } else if (web3url["currentProvider"]) {
      this.web3 = new Web3(web3url.currentProvider);
    } else {
      throw new Error("Invalid web3 provider");
    }

    this.contract = this.web3.eth.contract(contractABI).at(contractAddr);
    this.token = this.web3.eth.contract(tokenABI).at(tokenAddr);
  }

  // "static" methods/utils
  private encodeHex(val: string|number, zPadLength?: number): string {
    /* Encode a string or number as hexadecimal, without '0x' prefix
     */
    if (typeof val === "number") {
      val = val.toString(16);
    } else {
      val = Array.from(val).map((char) =>
          char.charCodeAt(0).toString(16).padStart(2, '0'))
        .join('');
    }
    return val.padStart(zPadLength || 0, '0');
  }

  private num2tkn(value: number): BigNumber {
    return Math.floor(value * Math.pow(10, this.decimals));
  }

  private tkn2num(bal: BigNumber): number {
    return bal && bal.div ?
      bal.div(Math.pow(10, this.decimals)) :
      bal / Math.pow(10, this.decimals);
  }

  private async waitTx(txHash: string, confirmations: number): Promise<any> {
    /*
     * Watch for a particular transaction hash and call the awaiting function when done;
     * Got it from: https://github.com/ethereum/web3.js/issues/393
     */
    let blockCounter = 30;
    confirmations = +confirmations || 0;
    // Wait for tx to be finished
    return new Promise((resolve, reject) => {
      let filter = this.web3.eth.filter('latest');
      filter.watch(async (err, blockHash) => {
        if (err) {
          return reject(err);
        }
        if (blockCounter<=0) {
          if (filter) {
            filter.stopWatching(null);
            filter = null;
          }
          console.warn('!! Tx expired !!', txHash);
          return reject(new Error("Tx expired: " + txHash));
        }
        // Get info about latest Ethereum block
        let receipt;
        try {
          receipt = await _(this.web3.eth.getTransactionReceipt)(txHash);
        } catch (err) {
          if (filter) {
            filter.stopWatching(null);
            filter = null;
          }
          throw err;
        }
        if (!receipt || !receipt.blockNumber) {
          return console.log('Waiting tx..', blockCounter--);
        } else if (confirmations > 0) {
          console.log('Waiting confirmations...', confirmations--);
          return;
        }
        // Tx is finished
        if (filter) {
          filter.stopWatching(null);
          filter = null;
        }
        return resolve(receipt);
      });
    });
  }

  // instance methods
  loadStoredChannel(account: string, receiver: string) {
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
    if (!this.channel) {
      return;
    }
    if (localStorage) {
      const key = this.channel.account + "|" + this.channel.receiver;
      localStorage.removeItem(key);
    }
    this.channel = undefined;
  }

  setChannel(channel: MicroChannel) {
    this.channel = channel;
    if (localStorage) {
      const key = channel.account + "|" + channel.receiver;
      localStorage.setItem(key, JSON.stringify(this.channel));
    }
  }

  isChannelValid() {
    if (!this.channel || !this.channel.receiver || !this.channel.block
      || isNaN(this.channel.balance) || !this.channel.account) {
      return false;
    }
    return true;
  }

  async getAccounts(): Promise<string[]> {
    return await _(this.web3.eth.getAccounts)();
  }

  async getTokenInfo(account?: string): Promise<MicroTokenInfo> {
    const [name, symbol, decimals, balance] = await Promise.all([
      _(this.token.name.call)(),
      _(this.token.symbol.call)(),
      _(this.token.decimals.call)().then((d) => d.toNumber()),
      account ? _(this.token.balanceOf.call)(account) : null
    ]);
    this.decimals = decimals;
    return { name, symbol, decimals, balance: this.tkn2num(balance) };
  }

  async getChannelInfo(): Promise<MicroChannelInfo> {
    if (!this.isChannelValid()) {
      throw new Error("No valid channelInfo");
    }

    const closeEvents: any[] = await _(this.contract.ChannelCloseRequested({
      _sender: this.channel.account,
      _receiver: this.channel.receiver,
      _open_block_number: this.channel.block,
    }, {
      fromBlock: this.channel.block,
      toBlock: 'latest'
    }).get)();

    let closed: number;
    if (!closeEvents || closeEvents.length === 0) {
      closed = 0;
    } else {
      closed = closeEvents[0].blockNumber;
    }

    const settleEvents: any[] = await _(this.contract.ChannelSettled({
      _sender: this.channel.account,
      _receiver: this.channel.receiver,
      _open_block_number: this.channel.block,
    }, {
      fromBlock: closed || this.channel.block,
      toBlock: 'latest'
    }).get)();

    let settled: number;
    if (!settleEvents || settleEvents.length === 0) {
      settled = 0;
    } else {
      settled = settleEvents[0].blockNumber;
    }
    // for settled channel, getChannelInfo call will fail, so we return before
    if (settled) {
      return {"state": "settled", "block": settled, "deposit": 0};
    }

    const info = await _(this.contract.getChannelInfo.call)(
      this.channel.account,
      this.channel.receiver,
      this.channel.block,
      { from: this.channel.account });

    if (!(info[1] > 0)) {
      throw new Error("Invalid channel deposit: "+JSON.stringify(info));
    }
    return {
      "state": closed ? "closed" : "opened",
      "block": closed || this.channel.block,
      "deposit": this.tkn2num(info[1]),
    };
  }

  async openChannel(account: string, receiver: string, deposit: number): Promise<MicroChannel> {
    if (this.isChannelValid()) {
      console.warn("Already valid channel will be forgotten:", this.channel);
    }

    // in this method, deposit is already multiplied by decimals
    const tkn_deposit = this.num2tkn(deposit);

    // first, check if there's enough balance
    const balance = await _(this.token.balanceOf.call)(account, { from: account });
    if (!(balance >= tkn_deposit)) {
      throw new Error(`Not enough tokens.
        Token balance = ${this.tkn2num(balance)}, required = ${deposit}`);
    }
    console.log('Token balance', this.token.options.address, this.tkn2num(balance));

    // call transfer to make the deposit, automatic support for ERC20/223 token
    let transferTxHash: string;
    if (typeof this.token.transfer["address,uint256,bytes"] === "function") {
      // ERC223
      // transfer tokens directly to the channel manager contract
      transferTxHash = await _(this.token.transfer["address,uint256,bytes"].sendTransaction)(
        this.contract.options.address,
        tkn_deposit,
        receiver, // bytes _data (3rd param) is the receiver
        { from: account });
    } else {
      // ERC20
      // send 'approve' transaction to token contract
      const approveTxHash = await _(this.token.approve.sendTransaction)(
        this.contract.options.address,
        tkn_deposit,
        { from: account });
      // send 'createChannel' transaction to channel manager contract
      transferTxHash = await _(this.contract.createChannelERC20.sendTransaction)(
        receiver,
        tkn_deposit,
        { from: account });
    }
    console.log('transferTxHash', transferTxHash);

    // wait for 'transfer' transaction to be mined
    const receipt = await this.waitTx(transferTxHash, 1);

    // call getChannelInfo to be sure channel was created
    const info = await _(this.contract.getChannelInfo.call)(
      account,
      receiver,
      receipt.blockNumber,
      { from: account });
    if (!(info[1] > 0)) {
      throw new Error("No deposit found!");
    }
    this.setChannel({account, receiver, block: receipt.blockNumber, balance: 0});

    // return channel
    return this.channel;
  }

  async topUpChannel(deposit: number): Promise<number> {
    if (!this.isChannelValid()) {
      throw new Error("No valid channelInfo");
    }

    const account = this.channel.account;

    // in this method, deposit is already multiplied by decimals
    const tkn_deposit = this.num2tkn(deposit);

    // first, check if there's enough balance
    const balance = await _(this.token.balanceOf.call)(account, { from: account });
    if (!(balance >= tkn_deposit)) {
      throw new Error(`Not enough tokens.
        Token balance = ${this.tkn2num(balance)}, required = ${deposit}`);
    }
    console.log('Token balance', this.token.options.address, this.tkn2num(balance));

    // automatically support both ERC20 and ERC223 tokens
    let transferTxHash: string;
    if (typeof this.token.transfer["address,uint256,bytes"] === "function") {
      // ERC223, just send token.transfer transaction
      // transfer tokens directly to the channel manager contract
      transferTxHash = await _(this.token.transfer["address,uint256,bytes"].sendTransaction)(
        this.contract.options.address,
        tkn_deposit,
        // receiver goes as 3rd param, 20 bytes, plus blocknumber, 4bytes
        this.channel.receiver + this.encodeHex(this.channel.block, 8),
        { from: account });
    } else {
      // ERC20, approve channel manager contract to handle our tokens, then topUp
      // send 'approve' transaction to token contract
      const approveTxHash = await _(this.token.approve.sendTransaction)(
        this.contract.options.address,
        tkn_deposit,
        { from: account });
      // send 'topUp' transaction to channel manager contract
      transferTxHash = await _(this.contract.topUpERC20.sendTransaction)(
        this.channel.receiver,
        this.channel.block,
        tkn_deposit,
        { from: account });
    }
    console.log('transferTxHash', transferTxHash);

    // wait for 'transfer' transaction to be mined
    const receipt = await this.waitTx(transferTxHash, 1);

    // return current deposit
    return (await this.getChannelInfo()).deposit;
  }

  async closeChannel(receiverSig?: string): Promise<number> {
    if (!this.isChannelValid()) {
      throw new Error("No valid channelInfo");
    }
    const info = await  this.getChannelInfo();
    if (info.state !== "opened") {
      throw new Error("Tried closing already closed channel");
    }
    console.log(`Closing channel. Cooperative = ${receiverSig}`);

    let sign;
    if (!this.channel.sign) {
      sign = await this.signBalance(this.channel.balance);
    } else {
      sign = this.channel.sign;
    }
    let params = [
      this.channel.receiver,
      this.channel.block,
      this.num2tkn(this.channel.balance),
      sign
    ];
    let paramsTypes = "address,uint32,uint192,bytes";
    if (receiverSig) {
      params.push(receiverSig);
      paramsTypes += ",bytes";
    }
    const txHash = await _(this.contract.close[paramsTypes].sendTransaction)(
      ...params,
      { from: this.channel.account });

    console.log('closeTxHash', txHash);
    const receipt = await this.waitTx(txHash, 0);
    return receipt.blockNumber;
  }

  async settleChannel(): Promise<number> {
    if (!this.isChannelValid()) {
      throw new Error("No valid channelInfo");
    }
    const info = await this.getChannelInfo();
    if (info.state !== "closed") {
      throw new Error("Tried settling opened or settled channel");
    }
    const txHash = await _(this.contract.settle.sendTransaction)(
      this.channel.receiver,
      this.channel.block,
      { from: this.channel.account });

    console.log('settleTxHash', txHash);
    const receipt = await this.waitTx(txHash, 0);
    return receipt.blockNumber;
  }

  async signMessage(msg: string): Promise<string> {
    if (!this.isChannelValid()) {
      throw new Error("No valid channelInfo");
    }
    const hex = '0x' + this.encodeHex(msg);
    console.log(`Signing "${msg}" => ${hex}, account: ${this.channel.account}`);

    let sign: string;
    try {
      sign = await _(this.web3.personal.sign)(hex, this.channel.account);
    } catch (err) {
      if (err.message &&
        (err.message.includes('Method not found') ||
          err.message.includes('is not a function'))) {
        sign = await _(this.web3.eth.sign)(this.channel.account, hex);
      } else {
        throw err;
      }
    }
    return sign;
  }

  async signBalance(newBalance: number): Promise<string> {
    if (!this.isChannelValid()) {
      throw new Error("No valid channelInfo");
    }
    console.log("signBalance", newBalance, this.channel);
    if (newBalance === null) {
      newBalance = this.channel.balance;
    }
    if (newBalance === this.channel.balance && this.channel.sign) {
      return this.channel.sign;
    }

    const msg = await _(this.contract.getBalanceMessage.call)(
      this.channel.receiver,
      this.channel.block,
      this.num2tkn(newBalance),
      { from: this.channel.account });

    // ask for signing of this message
    const sign = await _(this.signMessage)(msg);

    // return signed message
    if (newBalance === this.channel.balance && !this.channel.sign) {
      this.setChannel(Object.assign({}, this.channel, { sign }));
    }
    return sign;
  }

  async incrementBalanceAndSign(amount: number): Promise<string> {
    if (!this.isChannelValid()) {
      throw new Error("No valid channelInfo");
    }
    const newBalance = this.channel.balance + +amount;
    // get current deposit
    const info = await this.getChannelInfo();
    if (info.state !== "opened") {
      throw new Error("Tried signing on closed channel");
    } else if (newBalance > info.deposit) {
      throw new Error(`Insuficient funds: current = ${info.deposit} , required = ${newBalance}`);
    }
    // get hash for new balance proof
    const sign = await this.signBalance(newBalance);
    this.setChannel(Object.assign(
      {},
      this.channel,
      { balance: newBalance, sign }
    ));
    return sign;
  }

  async buyToken(account: string): Promise<Web3.TransactionReceipt> {
    const txHash = await _(this.token.mint.sendTransaction)({
      from: account,
      value: this.web3.toWei(0.1, "ether")
    });
    console.log('mintTxHash', txHash);
    return await this.waitTx(txHash, 1);
  }

}
