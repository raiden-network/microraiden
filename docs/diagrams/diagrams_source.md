http://www.nomnoml.com/
https://bramp.github.io/js-sequence-diagrams/


# RDNMicroTransferChannels


## MicroRaiden UseCase Examples


### Client

 - m2mclient = DefaultHTTPClient(client, api_endpoint, api_port)
 - eth_ticker


### Server

- app = PaywalledProxy(CHANNEL_MANAGER_ADDRESS, private_key, tempfile)
- custom proxy


## HTTP Headers



```
RDN-Price
RDN-Contract-Address
RDN-Receiver-Address
RDN-Payment
RDN-Balance
RDN-Balance-Signature
RDN-Sender-Address
RDN-Sender-Balance
RDN-Gateway-Path
RDN-Insufficient-Funds
RDN-Insufficient-Confirmations
RDN-Cost
RDN-Open-Block

```

## Off-chain

## Off-chain micropayment

```sequence

participant Sender
participant WebApp
participant Proxy

Sender -> Proxy: request paywalled content
Proxy -> WebApp: serve paywall UI
Proxy -> Proxy: RDN-Balance-Signature \n not set

Note left of WebApp: STATE 402
Proxy -> WebApp: HTTP 402 PaymentRequired \n RDN-Contract-Address \n RDN-Receiver-Address \n RDN-Gateway-Path \n RDN-Price
WebApp -> WebApp: LocalStorage \n check if channel exists
Note over WebApp: channel found (sender, receiver, block)

WebApp->Sender: paywall UI
Sender -> WebApp: Buy resource
Note over WebApp: get balance proof hash \n from ChannelsContract

WebApp -> Sender: Ask for balance proof hash signing
Sender -> WebApp: Sign balance proof
WebApp -> Proxy: RDN-Open-Block \n RDN-Sender-Balance \n RDN-Balance-Signature

Proxy -> ChannelManager: verify balance proof \n receiver, block, \n balance, balance signature
ChannelManager -> ChannelManager: crypto.py \n verify_balance_proof

Note over Proxy, ChannelManager: Exception

ChannelManager -> Proxy: InsufficientConfirmations OR \n NoOpenChannel\n

Proxy -> WebApp: HTTP 402 PaymentRequired
Note left of WebApp: STATE 402


Note over ChannelManager,Proxy: channel found
Proxy -> ChannelManager: register_payment(receiver, block, \n balance, balance signature)

Note over Proxy, ChannelManager: Exception
ChannelManager -> Proxy: InvalidBalanceAmount OR \n InvalidBalanceProof\n
Proxy -> WebApp: HTTP 402 PaymentRequired
Note left of WebApp: STATE 402



Note over ChannelManager,Proxy: balance proof OK \n payment registered
Proxy -> WebApp: Serve premium content
WebApp -> Sender: Premium content


```

## Off-chain channel close

```sequence

participant Sender
participant WebApp
participant Proxy

Sender -> WebApp: close channel \n (receiver, block)

WebApp -> ChannelsContract: close(receiver, block, last balance, \n last balance_signature)
ChannelsContract -> ChannelsContract: challenge period

ChannelsContract -> Blockchain: ChannelCloseRequested (sender, \n receiver, block, balance)
Blockchain -> ChannelManager: receive \n ChannelCloseRequested
ChannelManager -> ChannelManager: crypto.py \n verify closing balance

Note over ChannelManager,ChannelsContract: incorrect balance
ChannelManager -> ChannelManager: close_channel()
ChannelManager -> ChannelsContract: close()
Note left of ChannelsContract: State CLOSED

Note over ChannelManager,ChannelsContract: correct balance
ChannelManager -> ChannelManager: set channel as closed \n set settle_timeout

Note over Sender, ChannelsContract: Challenge period ended
Sender -> WebApp: settle channel (receiver, block)
WebApp -> ChannelsContract: settle(receiver, block)
Note left of ChannelsContract: State CLOSED

ChannelsContract -> Blockchain: ChannelSettled (sender, \n receiver, block, balance)

Blockchain -> ChannelManager: receive \n ChannelSettled
ChannelManager -> ChannelManager: event_channel_settled()
ChannelManager -> ChannelManager: store state

Blockchain -> WebApp: receive \n ChannelSettled
WebApp -> Sender: show channel closed state


```


## Channel Manager



```uml

#fill: #ffffff


[Blockchain
	|
	web3
	contract_proxy
	cm (channel_manager)
	n_confirmations
	log
	wait_sync_event
	|
	_run()
	wait_sync()
	_update()
]


[ChannelManagerState
	|
	contract_address
	receiver
	head_hash
	head_number
	channels
	filename
	log
	unconfirmed_channels
	|
	store()
	load()
]

[ChannelManager
	|
	Manages channels from the receiver's point of view.
	|
	blockchain
	receiver
	private_key
	contract_proxy
	log
	|
	_run()
	set_head()
	event_channel_opened()
	unconfirmed_event_channel_opened()
	event_channel_close_requested()
	event_channel_settled()
	unconfirmed_event_channel_topup()
	event_channel_topup()
	close_channel()
	force_close_channel()
	sign_close()
	get_token_balance()
	verifyBalanceProof()
	register_payment()
	channels_to_dict()
	unconfirmed_channels_to_dict()
	wait_sync()
]

[Channel
	|
	A channel between two parties
	|
	receiver
	sender
	deposit
	open_block_number
	balance
	is_closed
	last_signature
	settle_timeout
	mtime
	ctime
	|
	toJSON()
]

[ChannelManager]+->[Blockchain]
[ChannelManager]+->[ChannelManagerState]
[ChannelManager]+->[Channel]

```



## Proxy


```uml

#fill: #ffffff





[PaywalledProxy
	|
	app
	paywall_db: PaywallDatabase
	api: Api (Flask)
	rest_server: WSGIServer
	server_greenlet
	channel_manager
	|
	add_content(content)
	run()
	stop()
	join()
]

[ChannelManagementRoot
  |
  get()
]

[ChannelManagementListChannels
	|
	channel_manager
	|
	get_all_channels()
	get_channel_filter()
	get(sender_address)
	delete(sender_address)
]

[ChannelManagementAdmin
	|
	get()
	delete()
]

[ChannelManagementChannelInfo
	|
	channel_manager
	|
	get(sender_address,opening_block)
]

[StaticFilesServer
	|
	directory
	|
	get(content)
]


[PaywalledContent
	|
	path
	price
	|
	get(request)
]

[PaywalledFile
	|
	filepath
	|
	get(request)
]

[PaywalledProxyUrl
	|
	path
	price
	get_fn
	|
	get(request)
]

[PaywallDatabase
	|
	db
	|
	get_content(url)
	add_content(content)
]



[RequestData
	|
	sender_address
	|
	check_headers(headers)
]

[LightClientProxy
	|
	data
	|
	get(receiver, amount, token)
]

[Expensive
	|
	contract_address
	receiver_address
	channel_manager
	paywall_db
	light_client_proxy
	|
	get(content)
	reply_premium(content, sender_address, proxy_handle, sender_balance)
	reply_payment_required(content, proxy_handle)
	get_webUI_reply(price, headers)

]


[PaywalledProxy]+->[ChannelManager]
[PaywalledProxy]+->[PaywallDatabase]
[PaywalledProxy]+->[LightClientProxy]
[PaywalledProxy]+->[StaticFilesServer]
[PaywalledProxy]+->[Expensive]
[PaywalledProxy]+->[ChannelManagementListChannels]
[PaywalledProxy]+->[ChannelManagementChannelInfo]
[PaywalledProxy]+->[ChannelManagementAdmin]
[PaywalledProxy]+->[ChannelManagementRoot]


[PaywalledContent]<:-[PaywalledFile]
[PaywallDatabase]<:-[PaywalledProxyUrl]
[PaywallDatabase]<:-[PaywalledContent]


[Expensive]+->[RequestData]
[Expensive]+->[ChannelManager]
[Expensive]+->[PaywallDatabase]
[Expensive]+->[LightClientProxy]





```






```uml

#fill: #ffffff

[PublicAPI
	|
	cm (channel_manager)
	|
	_channel(sender)
	register_payment(msg)
	get_balance(sender_address)
	get_deposit(sender_address)
	get_credit(sender_address)
	settle(sender_address)
	sign_close(sender_address)
	get_addresses()
	outstanding_balance()
	settled_balance()
]

[PublicAPI]+->[ChannelManager]


```


```uml

#fill: #ffffff

[Exception]<:-[InvalidBalanceAmount]
[Exception]<:-[InvalidBalanceProof]
[Exception]<:-[NoOpenChannel]
[Exception]<:-[InsufficientConfirmations]
[Exception]<:-[NoBalanceProofReceived]
[Exception]<:-[StateContractAddrMismatch]
[Exception]<:-[StateReceiverAddrMismatch]



```



## JS Client


```uml
#fill: #ffffff


[RaidenMicropaymentsClient
	|
	web3
	contract
	token
	|
	loadStoredChannel(account, receiver)
	forgetStoredChannel()
	setChannel(channel)
	getAccounts(callback)
	signHash(msg, account, callback)
	encodeHex(str, zPadLength)
	isChannelValid()
	getChannelInfo(callback)
	openChannel(account, receiver, deposit, callback
	topUpChannel(deposit, callback)
	openChannel_ERC20(account, receiver, deposit, callback)
	topUpChannel_ERC20(deposit, callback)
	closeChannel(receiverSig, callback)
	settleChannel(callback)
	signBalance(newBalance, callback)
	incrementBalanceAndSign(amount, callback)
	waitTx(txHash, callback)

]


```


## Python Client


```uml

#fill: #ffffff


[HTTPClient
	|
	client
	api_endpoint
	api_port
	channel
	requested_resource
	retry
	|
	run(requested_resource)
	_request_resource()
	on_init()
	on_exit()
	on_success(resource, cost)
	on_insufficient_funds()
	on_insufficient_confirmations()
	approve_payment()
	on_payment_approved()
]

[DefaultHTTPClient
	|
	initial_deposit
	topup_deposit
	|
	approve_payment(receiver,price,confirmed_balance,channel_manager_address)
	on_payment_approved(receiver,price,confirmed_balance)
	is_suitable_channel(channel, receiver, value)
]

[Client
	|
	privkey
	datadir
	channel_manager_address
	token_address: ContractProxy
	web3
	channel_manager_proxy: ChannelContractProxy
	token_proxy
	account
	channels
	contract_abi_path
	|
	load_channels()
	sync_channels()
	store_channels()
	open_channel(receiver, deposit)
]

[Channel
	|
	sender
	receiver
	deposit
	block
	balance
	balance_sig
	state
	|
	topup(deposit)
	close(balance)
	close_cooperatively(closing_sig)
	settle()
	create_transfer(value)


	from_json(file)
	to_json(channel, file)
	from_event(event, state)
	merge_infos(stored, created, settling, closed)


]

[ContractProxy
	|
	web3
	privkey
	caller_address
	address
	abi
	contract
	gas_price
	gas_limit
	|
	create_transaction()
	get_logs()
	get_event_blocking()
]

[ChannelContractProxy
	|
	|
	get_channel_created_logs()
	get_channel_close_requested_logs()
	get_channel_settled_logs()
	get_channel_created_event_blocking()
	get_channel_requested_close_event_blocking()
	get_channel_settle_event_blocking()
	get_settle_timeout()
	sign_balance_proof()
	sign_close()


]

[ContractProxy]<:-[ChannelContractProxy]

[HTTPClient]<:-[DefaultHTTPClient]
[HTTPClient]+->0..*[Channel]
[HTTPClient]+->[Client]
[Client]+->[ChannelContractProxy]
[Client]+->[ContractProxy]

```



## RaidenMicroTransferChannels Smart Contract


### Class



```uml

#fill: #ffffff

[RaidenMicroTransferChannels
	|
	[.
		|
		address public owner
		address public token_address
	  uint8 public challenge_period
	  Token token
	  mapping (bytes32 => Channel) channels
	  mapping (bytes32 => ClosingRequest) closing_requests
	]
	[Channel
		|
		uint192 deposit
        uint32 open_block_number
	]
	[ClosingRequest
		|
		uint32 settle_block_number
        uint192 closing_balance
	]
	|
	RaidenMicroTransferChannels(address _token, uint8 _challenge_period)
	|
	------- events -----------------
	ChannelCreated (_sender*,_receiver*,_deposit)
	ChannelToppedUp (_sender*,_receiver*,_open_block_number*,_added_deposit,_deposit)
	ChannelCloseRequested (_sender*,_receiver*,_open_block_number*,_balance)
	ChannelSettled (_sender*,_receiver*,_open_block_number*,_balance)
	|
	------- public constant -------
	getChannelInfo(address _sender, address _receiver, uint32 _open_block_number)
	getKey(address _sender, address _receiver, uint32 _open_block_number)
	balanceMessageHash(address _receiver, uint32 _open_block_number, uint192 _balance)
	closingAgreementMessageHash(bytes _balance_msg_sig)
	verifyBalanceProof(address _receiver, uint32 _open_block_number, uint192 _balance, bytes _balance_msg_sig)
	verifyClosingSignature(bytes _balance_msg_sig, bytes _closing_sig)
	|
	------- public -----------------
	tokenFallback(address _sender, uint256 _deposit, bytes _data)
	|
	------- external ---------------
	createChannelERC20(receiver, deposit)
	topUpERC20(receiver, open_block_number, added_deposit)
	close(address _receiver, uint32 _open_block_number, uint192 _balance, bytes _balance_msg_sig, *bytes _closing_sig)
	settle(receiver, open_block_number)
	|
	------- private ----------------
	createChannelPrivate()
	topUpPrivate()
	initChallengePeriod()
	settleChannel()
	|
	------- internal ----------------
	max(a,b)
	min(a,b)
	addressFromData(bytes b)
	blockNumberFromData(bytes b)
]



```





## Channel Cycle




```uml

#fill: #ffffff

[RaidenMicroTransferChannels |
  [<start>start]->[<state>Sender wants Channel with Receiver]
  [<state>Sender wants Channel with Receiver]->[<state>Transfer Sender tokens to Contract]
  [<state>Transfer Sender tokens to Contract]->[<state>Channel created ; (sender, receiver, open_block_number)]

  [<state>Channel created ; (sender, receiver, open_block_number)]->[<state>Off-Chain transfers enabled]

  [<state>topUp(tokens)]->[<state>Off-Chain transfers enabled]

 [<state>Off-Chain transfers enabled]->[<choice>Party ; wants to close ; Channel]



  [<choice>Party ; wants to close ; Channel]->sender[<state>Sender ; called CLOSE]

  [<choice>Party ; wants to close ; Channel]->receiver[<state>Receiver ; called CLOSE]

  [<state>Receiver ; called CLOSE]->1[<state>settleChannel private]

  [<state>Sender ; called CLOSE]->[<choice>Balance ; signed by Sender + ; Receiver?]


   [<choice>Balance ; signed by Sender + ; Receiver?]->1[<state>settleChannel private]

   [<choice>Balance ; signed by Sender + ; Receiver?]->0[Non Cooperative Case |
   	[<start>start]->[<state>Challenge period start; settle_block_number]
   	[<state>Challenge period start; settle_block_number]->[<choice>Challenge ; period pending ; ?]

	[<choice>Challenge ; period pending ; ?]->0[<state>Challenge period ended]
	[<choice>Challenge ; period pending ; ?]->1[<state>Challenge period]

  	[<state>Challenge period ended]->[<choice>Sender ; calls SETTLE or ; Receiver calls ; CLOSE?]
	[<state>Challenge period]->[<choice>Receiver calls ; CLOSE?]

	[<choice>Sender ; calls SETTLE or ; Receiver calls ; CLOSE?]->1[<end>end]
	[<choice>Receiver calls ; CLOSE?]->1[<end>end]

	[<choice>Receiver calls ; CLOSE?]->0[<choice>Challenge ; period pending ; ?]
	[<choice>Sender ; calls SETTLE or ; Receiver calls ; CLOSE?]->0[<choice>Sender ; calls SETTLE or ; Receiver calls ; CLOSE?]

   ]

  [Non Cooperative Case]->[<state>settleChannel private]

  [<state>settleChannel private]->[<state>Receiver gets ; min(last balance, deposit)]
  [<state>Receiver gets ; min(last balance, deposit)]->[<state>Sender gets max(deposit-balance,0)]
  [<state>Sender gets max(deposit-balance,0)]->[<state>Channel closed]


  [<state>Channel closed]->[<end>end]
]

```



### Opening a transfer channel ERC223


```sequence

Sender -> WebApp: Open Channel with Receiver, \n deposit = 10
WebApp -> Token: transfer \n (ChannelsContract, 10, data)
Token -> ChannelsContract: tokenFallback \n (sender, 10, data)
Note over ChannelsContract: receiver address \n from data
ChannelsContract -> ChannelsContract: createChannelPrivate \n (sender, receiver, 10)
Note over ChannelsContract: ChannelCreated
ChannelsContract -> WebApp: ChannelCreated \n (sender, receiver, 10)

```



### Topping Up a channel ERC223


```sequence

Sender -> WebApp: Top Up Channel \n Receiver, open_block_number, \n add 10 tokens \n existing deposit = 20
WebApp -> Token: transfer \n (ChannelsContract, 10, data)
Note over Token: data = msg.data \n for topUp
Token -> ChannelsContract: tokenFallback \n (sender, 10, data)
Note over ChannelsContract: receiver address + open_block_number \n from data
ChannelsContract -> ChannelsContract: topUpPrivate \n (sender, receiver, \n open_block_number, 10)
Note over ChannelsContract: ChannelToppedUp
ChannelsContract -> WebApp: ChannelToppedUp \n (sender, receiver, \n open_block_number, 10, 30)

```


### Opening a transfer channel ERC20




```sequence

Sender -> WebApp: Open Channel with Receiver, \n deposit = 10
WebApp -> Token: approve \n (ChannelsContract, 10)
WebApp -> ChannelsContract: createChannelERC20 \n (receiver, deposit)
ChannelsContract -> Token: transferFrom \n (sender, contract, 10)
Note over ChannelsContract,Token: ChannelCreated
ChannelsContract -> WebApp: ChannelCreated \n (sender, receiver, 10)

```




### Topping Up a channel ERC20

```sequence

Sender -> WebApp: Top Up Channel \n Receiver, open_block_number, \n add 10 tokens \n existing deposit = 20
WebApp -> Token: approve \n (ChannelsContract, 10)
WebApp -> ChannelsContract: topUpERC20 \n (receiver, deposit)
ChannelsContract -> Token: transferFrom \n (sender, contract, 10)
Note over ChannelsContract,Token: ChannelToppedUp
ChannelsContract -> WebApp: ChannelToppedUp \n (sender, receiver, \n open_block_number, 10, 30)

```
