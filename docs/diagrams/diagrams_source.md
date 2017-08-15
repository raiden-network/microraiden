http://www.nomnoml.com/
https://bramp.github.io/js-sequence-diagrams/


# RDNMicroTransferChannels



## HTTPHeaders


```uml

#fill: #ffffff

[HTTPHeaders
	|
	PRICE = 'RDN-Price'
    CONTRACT_ADDRESS = 'RDN-Contract-Address'
    RECEIVER_ADDRESS = 'RDN-Receiver-Address'
    PAYMENT = 'RDN-Payment'
    BALANCE = 'RDN-Balance'
    BALANCE_SIGNATURE = 'RDN-Balance-Signature'
    SENDER_ADDRESS = 'RDN-Sender-Address'
    GATEWAY_PATH = 'RDN-Gateway-Path'
    INSUF_FUNDS = 'RDN-Insufficient-Funds'
    INSUF_CONFS = 'RDN-Insufficient-Confirmations'
    COST = 'RDN-Cost'
    OPEN_BLOCK = 'RDN-Open-Block'
]



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
	|
	_run()
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
	close_channel()
	sign_close()
	get_token_balance()
	verifyBalanceProof()
	register_payment()
	channels_to_dict()
	unconfirmed_channels_to_dict()
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
]

[ChannelManager]->[Blockchain]
[ChannelManager]->[ChannelManagerState]
[ChannelManager]->[Channel]

```



## Proxy


```uml

#fill: #ffffff





[PaywalledProxy
	|
	app
	paywall_db: PaywallDatabase
	config
	api
	web3
	channel_manager
	|
	add_content(content)
	run()
	|
	  [ChannelManagementRoot
	  |
	  get()
  ]

  [ChannelManagementListChannels
	  |
	  channel_manager
	  |
	  get(channel_id)
	  delete(sender_address)
  ]

  [ChannelManagementAdmin
	  |
	  get()
	  delete()
  ]

  [StaticFilesServer
	  |
	  directory
	  |
	  get(content)
  ]
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

]


[Expensive]->[RequestData]

[PaywalledProxy]->[ChannelContractProxy]
[PaywalledProxy]->[LightClientProxy]
[PaywalledProxy]->[ChannelManager]

[PaywalledProxy]->[Expensive]
[PaywalledProxy]->[PaywallDatabase]

[PaywalledContent]<:-[PaywalledFile]
[PaywallDatabase]<:-[PaywalledProxyUrl]
[PaywallDatabase]<:-[PaywalledContent]

[ContractProxy]<:-[ChannelContractProxy]




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

[PublicAPI]->[ChannelManager]


```


```uml

#fill: #ffffff

[Exception]<:-[InvalidBalanceProof]
[Exception]<:-[NoOpenChannel]
[Exception]<:-[NoBalanceProofReceived]


```



## JS Client


```uml
#fill: #ffffff


[RaidenMicroTransferJSClient
	|
	|
	loadStoredChannel(account, receiver)
	forgetStoredChannel()
	setChannelInfo(channel)
	getAccounts(callback)
	signHash(msg, account, callback)
	isChannelValid()
	isChannelOpen(callback)
	openChannel(account, receiver, deposit, callback
	topUpChannel(deposit, callback)
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

[RMPClient
	|
	key_path
	rpc_endpoint
	rpc_port
	datadir
	dry_run
	channel_manager_address
	contract_abi_path
	token_address
	channels
	account
	rpc
	web3
	channel_manager_proxy
	token_proxy
	|
	load_channels()
	sync_channels()
	store_channels()
	open_channel(receiver, deposit)
	topup_channel()
	close_channel(channel, balance)
	settle_channel(channel)
	create_transfer(channel, value)

]

[M2MClient
	|
	rmp_client
	api_endpoint
	api_port
	|
	request_resource(resource, tries_max)
	request_resource_x(resource)
	perform_payment(receiver, value)
	perform_request(resource, channel)
]

[ChannelInfo
	|
	sender
	receiver
	deposit
	block
	balance
	balance_sig
	state
	|
	from_json(file)
	to_json(channel, file)
	from_event(event, state)
	merge_infos(stored, created, settling, closed)


]

[M2MClient]->[RMPClient]
[RMPClient]+->0..*[ChannelInfo]



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
	ChannelCreated
	ChannelToppedUp
	ChannelCloseRequested
	ChannelSettled
	|
	------- constant -------
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
	createChannel(receiver, deposit)
	topUp(receiver, open_block_number, added_deposit)
	close(address _receiver, uint32 _open_block_number, uint192 _balance, bytes _balance_msg_sig, *bytes _closing_sig)
	settle(receiver, open_block_number)
	|
	------- private ----------------
	createChannelPrivate()
	initChallengePeriod()
	settleChannel()

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



### Opening a transfer channel ERC20


```sequence

Sender -> WebApp: Open Channel with Receiver, \n deposit = 10
WebApp -> Token: approve \n (ChannelsContract, 10)
WebApp -> ChannelsContract: createChannel \n (receiver, deposit)
ChannelsContract -> Token: transferFrom \n (sender, contract, 10)
Note over ChannelsContract,Token: ChannelCreated
ChannelsContract -> WebApp: ChannelCreated \n (sender, receiver, 10)

```



### Opening a transfer channel ERC223


```sequence

Sender -> WebApp: Open Channel with Receiver, \n deposit = 10
WebApp -> Token: transfer \n (ChannelsContract, 10, data)
Token -> ChannelsContract: tokenFallback \n (sender, 10, data)
ChannelsContract -> ChannelsContract: get receiver \n from data
ChannelsContract -> ChannelsContract: createChannel \n (receiver, 10)
Note over ChannelsContract: ChannelCreated
ChannelsContract -> WebApp: ChannelCreated \n (sender, receiver, 10)

```
