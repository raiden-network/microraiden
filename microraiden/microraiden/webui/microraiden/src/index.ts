import * as Web3 from 'web3';
import BigNumber from 'bignumber.js';
import { typedSignatureHash, recoverTypedSignature } from 'eth-sig-util';

declare const localStorage; // possibly missing


// helper types
export interface MicroProof {
  balance: BigNumber;
  sign?: string;
}

export interface MicroChannel {
  /* MicroRaiden.channel data structure */
  account: string;
  receiver: string;
  block: number;
  proof: MicroProof;
  next_proof?: MicroProof;
  close_sign?: string;
}

export interface MicroChannelInfo {
  /* MicroRaiden.getChannelInfo result */
  state: string;
  block: number;
  deposit: BigNumber;
}

export interface MicroTokenInfo {
  /* MicroRaiden.getTokenInfo result */
  name: string;
  symbol: string;
  decimals: number;
  balance: BigNumber;
}

interface MsgParam {
  type: string;
  name: string;
  value: string;
}


// utils
function promisify<T>(obj: any, method: string): (...args: any[]) => Promise<T> {
  /* Convert a callback-based func to return a promise */
  return (...params) =>
    new Promise((resolve, reject) =>
      obj[method](...params, (err, res) => err ? reject(err) : resolve(res)));
}

class Deferred<T> {
  resolve: (res: T) => void;
  reject: (err: Error) => void;
  promise = new Promise<T>((resolve, reject) => {
    this.resolve = resolve;
    this.reject = reject;
  });
}

function encodeHex(val: string|number|BigNumber, zPadLength?: number): string {
  /* Encode a string or number as hexadecimal, without '0x' prefix */
  if (typeof val === 'number' || val instanceof BigNumber ) {
    val = val.toString(16);
  } else {
    val = Array.from(<string>val).map((char: string) =>
        char.charCodeAt(0).toString(16).padStart(2, '0'))
      .join('');
  }
  return val.padStart(zPadLength || 0, '0');
}


// main class
export class MicroRaiden {
  web3: Web3;
  channel: MicroChannel;
  token: Web3.ContractInstance;
  contract: Web3.ContractInstance;
  decimals: number = 0;

  constructor(
    web3: string | { currentProvider: any },
    contractAddr: string,
    contractABI: any[],
    tokenAddr: string,
    tokenABI: any[],
  ) {
    if (!web3) {
      web3 = 'http://localhost:8545';
    }
    if (typeof web3 === 'string') {
      this.web3 = new Web3(new Web3.providers.HttpProvider(web3));
    } else if (web3['currentProvider']) {
      this.web3 = new Web3(web3.currentProvider);
    } else {
      throw new Error('Invalid web3 provider');
    }

    this.contract = this.web3.eth.contract(contractABI).at(contractAddr);
    this.token = this.web3.eth.contract(tokenABI).at(tokenAddr);
  }

  // utils
  num2tkn(value: number|string): BigNumber {
    /* Convert number to BigNumber compatible with configured token,
     * taking in account the token decimals */
    return new BigNumber(value).shift(this.decimals);
  }

  tkn2num(bal: BigNumber): number {
    /* Convert BigNumber to number compatible with configured token,
     * taking in account the token decimals */
    return (new BigNumber(bal)).shift(-this.decimals).toNumber();
  }

  private async waitTx(txHash: string, confirmations: number): Promise<Web3.TransactionReceipt> {
    /* Watch for a particular transaction hash to have given confirmations
     * Inspired in: https://github.com/ethereum/web3.js/issues/393
     * Return promise to mined receipt of transaction */
    let blockCounter = 30;
    confirmations = +confirmations || 0;

    const defer = new Deferred<Web3.TransactionReceipt>();
    let filter = this.web3.eth.filter('latest');
    const firstBlockTimeout = setTimeout(() => {
      if (filter) {
        filter.stopWatching(null);
        filter = null;
      }
      defer.reject(new Error('No blocks seen in 30s. '+
        'You may need to restart your browser or check '+
        'if your node is synced!'));
    }, 30e3);

    // Wait for tx to be finished
    filter.watch(async (err, blockHash) => {
      if (err) {
        return defer.reject(err);
      }
      // on first block, stop timeout
      clearTimeout(firstBlockTimeout);

      if (blockCounter<=0) {
        if (filter) {
          filter.stopWatching(null);
          filter = null;
        }
        console.warn('!! Tx expired !!', txHash);
        return defer.reject(new Error('Tx expired: ' + txHash));
      }

      // Get info about latest Ethereum block
      const receipt = await promisify<Web3.TransactionReceipt>(this.web3.eth, 'getTransactionReceipt')(txHash);
      if (!receipt || !receipt.blockNumber) {
        console.log('Waiting tx..', blockCounter--);
        return;
      } else if (confirmations > 0) {
        console.log('Waiting confirmations...', confirmations--);
        return;
      }

      // Tx is finished
      if (filter) {
        filter.stopWatching(null);
        filter = null;
      }
      return defer.resolve(receipt);
    });

    return defer.promise;
  }

  // instance methods
  loadStoredChannel(account: string, receiver: string): void {
    /* If localStorage is available, try to load a channel from it,
     * indexed by given account and receiver */
    if (!localStorage) {
      delete this.channel;
      return;
    }
    const key = [account, receiver].join('|');
    const value = localStorage.getItem(key);
    if (value) {
      const channel = JSON.parse(value);
      if (!channel || !channel.proof || !channel.proof.balance) {
        return;
      }
      channel.proof.balance = new BigNumber(channel.proof.balance);
      if (channel.next_proof)
        channel.next_proof.balance = new BigNumber(channel.next_proof.balance);
      this.channel = channel;
    } else {
      delete this.channel;
    }
  }

  forgetStoredChannel(): void {
    /* Forget current channel and remove it from localStorage, if available */
    if (!this.channel) {
      return;
    }
    if (localStorage) {
      const key = [this.channel.account, this.channel.receiver].join('|');
      localStorage.removeItem(key);
    }
    delete this.channel;
  }

  setChannel(channel: MicroChannel): void {
    /* Set channel info. Can be used to externally [re]store channel info */
    this.channel = channel;
    if (localStorage) {
      const key = [this.channel.account, this.channel.receiver].join('|');
      localStorage.setItem(key, JSON.stringify(this.channel));
    }
  }

  isChannelValid(): boolean {
    /* Health check for currently configured channel info */
    if (!this.channel || !this.channel.receiver || !this.channel.block
      || !this.channel.proof || isNaN(this.channel.proof.balance)
      || !this.channel.account) {
      return false;
    }
    return true;
  }

  async getAccounts(): Promise<string[]> {
    /* Get available accounts from web3 providers.
     * Returns promise to accounts addresses array */
    return await promisify<string[]>(this.web3.eth, 'getAccounts')();
  }

  async getTokenInfo(account?: string): Promise<MicroTokenInfo> {
    /* Get token details such as name, symbol and decimals.
     * If account is provided, returns also account balance for this token.
     * Returns promise to MicroTokenInfo object */
    const [name, symbol, decimals, balance] = await Promise.all([
      promisify<string>(this.token.name, 'call')(),
      promisify<string>(this.token.symbol, 'call')(),
      promisify<BigNumber>(this.token.decimals, 'call')().then((d) => d.toNumber()),
      account ? promisify<BigNumber>(this.token.balanceOf, 'call')(account) : null
    ]);
    this.decimals = decimals;
    return { name, symbol, decimals, balance };
  }

  async getChannelInfo(): Promise<MicroChannelInfo> {
    /* Get channel details such as current state (one of opened, closed or
     * settled), block in which it was set and current deposited amount
     * Returns promise to MicroChannelInfo object */
    if (!this.isChannelValid()) {
      throw new Error('No valid channelInfo');
    }

    const closeEvents = await promisify<{ blockNumber: number }[]>(this.contract.ChannelCloseRequested({
      _sender: this.channel.account,
      _receiver: this.channel.receiver,
      _open_block_number: this.channel.block,
    }, {
      fromBlock: this.channel.block,
      toBlock: 'latest'
    }), 'get')();

    let closed: number;
    if (!closeEvents || closeEvents.length === 0) {
      closed = 0;
    } else {
      closed = closeEvents[0].blockNumber;
    }

    const settleEvents = await promisify<{ blockNumber: number }[]>(this.contract.ChannelSettled({
      _sender: this.channel.account,
      _receiver: this.channel.receiver,
      _open_block_number: this.channel.block,
    }, {
      fromBlock: closed || this.channel.block,
      toBlock: 'latest'
    }), 'get')();

    let settled: number;
    if (!settleEvents || settleEvents.length === 0) {
      settled = 0;
    } else {
      settled = settleEvents[0].blockNumber;
    }
    // for settled channel, getChannelInfo call will fail, so we return before
    if (settled) {
      return {'state': 'settled', 'block': settled, 'deposit': new BigNumber(0)};
    }

    const info = await promisify<BigNumber[]>(this.contract.getChannelInfo, 'call')(
      this.channel.account,
      this.channel.receiver,
      this.channel.block,
      { from: this.channel.account });

    if (!(info[1].gt(0))) {
      throw new Error('Invalid channel deposit: '+JSON.stringify(info));
    }
    return {
      'state': closed ? 'closed' : 'opened',
      'block': closed || this.channel.block,
      'deposit': info[1],
    };
  }

  async openChannel(account: string, receiver: string, deposit: BigNumber): Promise<MicroChannel> {
    /* Open a channel for account to receiver, depositing some tokens in it.
     * Should work with both ERC20/ERC223 tokens.
     * Returns promise to MicroChannel info object */
    if (this.isChannelValid()) {
      console.warn('Already valid channel will be forgotten:', this.channel);
    }

    // first, check if there's enough balance
    const balance = await promisify<BigNumber>(this.token.balanceOf, 'call')(account, { from: account });
    if (!(balance.gte(deposit))) {
      throw new Error(`Not enough tokens.
        Token balance = ${balance}, required = ${deposit}`);
    }
    console.log('Token balance', this.token.address, balance);

    // call transfer to make the deposit, automatic support for ERC20/223 token
    let transferTxHash: string;
    if (typeof this.token.transfer['address,uint256,bytes'] === 'function') {
      // ERC223
      // transfer tokens directly to the channel manager contract
      transferTxHash = await promisify<string>(this.token.transfer['address,uint256,bytes'], 'sendTransaction')(
        this.contract.address,
        deposit,
        receiver, // bytes _data (3rd param) is the receiver
        { from: account });
    } else {
      // ERC20
      // send 'approve' transaction to token contract
      await promisify<string>(this.token.approve, 'sendTransaction')(
        this.contract.address,
        deposit,
        { from: account });
      // send 'createChannel' transaction to channel manager contract
      transferTxHash = await promisify<string>(this.contract.createChannelERC20, 'sendTransaction')(
        receiver,
        deposit,
        { from: account });
    }
    console.log('transferTxHash', transferTxHash);

    // wait for 'transfer' transaction to be mined
    const receipt = await this.waitTx(transferTxHash, 1);

    // call getChannelInfo to be sure channel was created
    const info = await promisify<BigNumber[]>(this.contract.getChannelInfo, 'call')(
      account,
      receiver,
      receipt.blockNumber,
      { from: account });
    if (!(info[1].gt(0))) {
      throw new Error('No deposit found!');
    }
    this.setChannel({
      account,
      receiver,
      block: receipt.blockNumber,
      proof: { balance: new BigNumber(0) },
    });

    // return channel
    return this.channel;
  }

  async topUpChannel(deposit: BigNumber): Promise<number> {
    /* Top up current channel, by depositing some tokens to it
     * Should work with both ERC20/ERC223 tokens
     * Returns promise block number */
    if (!this.isChannelValid()) {
      throw new Error('No valid channelInfo');
    }

    const account = this.channel.account;

    // first, check if there's enough balance
    const balance = await promisify<BigNumber>(this.token.balanceOf, 'call')(account, { from: account });
    if (!(balance.gte(deposit))) {
      throw new Error(`Not enough tokens.
        Token balance = ${balance}, required = ${deposit}`);
    }
    console.log('Token balance', this.token.address, balance);

    // automatically support both ERC20 and ERC223 tokens
    let transferTxHash: string;
    if (typeof this.token.transfer['address,uint256,bytes'] === 'function') {
      // ERC223, just send token.transfer transaction
      // transfer tokens directly to the channel manager contract
      transferTxHash = await promisify<string>(this.token.transfer['address,uint256,bytes'], 'sendTransaction')(
        this.contract.address,
        deposit,
        // receiver goes as 3rd param, 20 bytes, plus blocknumber, 4bytes
        this.channel.receiver + encodeHex(this.channel.block, 8),
        { from: account });
    } else {
      // ERC20, approve channel manager contract to handle our tokens, then topUp
      // send 'approve' transaction to token contract
      await promisify<string>(this.token.approve, 'sendTransaction')(
        this.contract.address,
        deposit,
        { from: account });
      // send 'topUp' transaction to channel manager contract
      transferTxHash = await promisify<string>(this.contract.topUpERC20, 'sendTransaction')(
        this.channel.receiver,
        this.channel.block,
        deposit,
        { from: account });
    }
    console.log('transferTxHash', transferTxHash);

    // wait for 'transfer' transaction to be mined
    const receipt = await this.waitTx(transferTxHash, 1);

    return receipt.blockNumber;
  }

  async closeChannel(receiverSign?: string): Promise<number> {
    /* Close current channel.
     * Optional parameter is signed cooperative close from receiver.
     * If cooperative close was successful, channel is already settled after.
     * Else, it enters 'closed' state, and may be settled after settlement
     * period configured in contract.
     * Returns promise to block number in which channel was closed */
    if (!this.isChannelValid()) {
      throw new Error('No valid channelInfo');
    }
    const info = await this.getChannelInfo();
    if (info.state !== 'opened') {
      throw new Error('Tried closing already closed channel');
    }

    if (this.channel.close_sign) {
      receiverSign = this.channel.close_sign;
    } else if (receiverSign) {
      this.setChannel(Object.assign(
        {},
        this.channel,
        { close_sign: receiverSign },
      ));
    }
    console.log(`Closing channel. Cooperative = ${receiverSign}`);


    let proof: MicroProof;
    if (!this.channel.proof.sign) {
      proof = await this.signNewProof(this.channel.proof);
    } else {
      proof = this.channel.proof;
    }

    const txHash = receiverSign ?
      await promisify<string>(this.contract.cooperativeClose, 'sendTransaction')(
        this.channel.receiver,
        this.channel.block,
        proof.balance,
        proof.sign,
        receiverSign,
        { from: this.channel.account }) :
      await promisify<string>(this.contract.uncooperativeClose, 'sendTransaction')(
        this.channel.receiver,
        this.channel.block,
        proof.balance,
        proof.sign,
        { from: this.channel.account });

    console.log('closeTxHash', txHash);
    const receipt = await this.waitTx(txHash, 0);
    return receipt.blockNumber;
  }

  async settleChannel(): Promise<number> {
    /* If channel was not cooperatively closed, and after settlement period,
     * this function settles the channel, distributing the tokens to sender and
     * receiver.
     * Returns promise to blockNumber of settlement tx */
    if (!this.isChannelValid()) {
      throw new Error('No valid channelInfo');
    }
    const info = await this.getChannelInfo();
    if (info.state !== 'closed') {
      throw new Error('Tried settling opened or settled channel');
    }
    const txHash = await promisify<string>(this.contract.settle, 'sendTransaction')(
      this.channel.receiver,
      this.channel.block,
      { from: this.channel.account });

    console.log('settleTxHash', txHash);
    const receipt = await this.waitTx(txHash, 0);
    return receipt.blockNumber;
  }

  async signMessage(msg: string): Promise<string> {
    /* Ask user for signing a string.
     * Returns a promise for signed data */
    if (!this.isChannelValid()) {
      throw new Error('No valid channelInfo');
    }
    const hex = msg.startsWith('0x') ? msg : ( '0x' + encodeHex(msg) );
    console.log(`Signing "${msg}" => ${hex}, account: ${this.channel.account}`);

    let sign: string;
    try {
      sign = await promisify<string>(this.web3.personal, 'sign')(hex, this.channel.account);
    } catch (err) {
      if (err.message &&
        (err.message.includes('Method not found') ||
          err.message.includes('is not a function'))) {
        sign = await promisify<string>(this.web3.eth, 'sign')(this.channel.account, hex);
      } else {
        throw err;
      }
    }
    return sign;
  }

  async signNewProof(proof?: MicroProof): Promise<MicroProof> {
    /* Ask user for signing a channel balance.
     * Notice it's the final balance, not the increment, and that the new
     * balance is set in channel data in next_*, requiring confirmPayment
     * call to persist it, after successful request.
     * Returns promise to signed data */
    if (!this.isChannelValid()) {
      throw new Error('No valid channelInfo');
    }
    console.log('signNewProof', proof);
    if (!proof) {
      proof = this.channel.proof;
    }
    if (proof.sign) {
      return proof;
    }

    const params: MsgParam[] = [
      {
        name: 'receiver',
        type: 'address',
        value: this.channel.receiver,
      },
      {
        name: 'block_created',
        type: 'uint32',
        value: '' + this.channel.block,
      },
      {
        name: 'balance',
        type: 'uint192',
        value: proof.balance.toString(),
      },
      {
        name: 'contract',
        type: 'address',
        value: this.contract.address,
      },
    ];
    let sign: string;
    try {
      const result = await promisify<{ result: string, error: Error }>(
        this.web3.currentProvider, 'sendAsync'
      )({
        method: 'eth_signTypedData',
        params: [params, this.channel.account],
        from: this.channel.account
      });
      if (result.error)
        throw result.error;
      sign = result.result;
    } catch (err) {
      if (err.message && err.message.includes('User denied')) {
        throw err;
      }
      console.log('Error on signTypedData', err);
      const hash = typedSignatureHash(params);
      // ask for signing of the hash
      sign = await this.signMessage(hash);
    }
    //debug
    const recovered = recoverTypedSignature({ data: params, sig: sign  });
    console.log('signTypedData =', sign, recovered);

    proof.sign = sign;

    // return signed message
    if (proof.balance.equals(this.channel.proof.balance)) {
      this.setChannel(Object.assign(
        {},
        this.channel,
        { proof, next_proof: proof }
      ));
    } else {
      this.setChannel(Object.assign(
        {},
        this.channel,
        { next_proof: proof }
      ));
    }
    return proof;
  }

  async incrementBalanceAndSign(amount: BigNumber): Promise<MicroProof> {
    /* Ask user for signing a new balance, which is previous balance added
     * of a given amount.
     * Notice that it doesn't replace signed balance proof, but next_* balance
     * proof. You must call confirmPayment with the signature after confirming
     * successful request, to persist it.
     * Returns promise to signed data */
    if (!this.isChannelValid()) {
      throw new Error('No valid channelInfo');
    }
    const proof: MicroProof = { balance: this.channel.proof.balance.plus(amount) };
    // get current deposit
    const info = await this.getChannelInfo();
    if (info.state !== 'opened') {
      throw new Error('Tried signing on closed channel');
    } else if (proof.balance.gt(info.deposit)) {
      const err = new Error(`Insuficient funds: current = ${info.deposit} , required = ${proof.balance}`);
      err['current'] = info.deposit;
      err['required'] = proof.balance;
      throw err;
    }
    // get hash for new balance proof
    return await this.signNewProof(proof);
  }

  confirmPayment(proof: MicroProof): void {
    /* This method must be used after successful payment request.
     * It will persist this.channel's next_{balance,sign} to balance,sign */
    if (!this.channel.next_proof
      || !this.channel.next_proof.sign
      || this.channel.next_proof.sign !== proof.sign) {
      throw new Error('Invalid provided or stored next signature');
    }
    const channel = Object.assign(
      {},
      this.channel,
      { proof: this.channel.next_proof },
    );
    delete channel.next_proof;
    this.setChannel(channel);
  }

  async buyToken(account: string): Promise<Web3.TransactionReceipt> {
    /* For testing. Send 0.1 ETH to mint method of contract.
     * On TKN tests, it'll yield 50 TKNs.
     * Returns promise to tx receipt */
    const txHash = await promisify<string>(this.token.mint, 'sendTransaction')({
      from: account,
      value: this.web3.toWei(0.1, 'ether')
    });
    console.log('mintTxHash', txHash);
    return await this.waitTx(txHash, 1);
  }

}
