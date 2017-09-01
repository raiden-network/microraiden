function pageReady(json) {
  window.rmpc = new RaidenMicropaymentsClient(
    window.web3,
    json["contractAddr"],
    json["contractABI"],
    json["tokenAddr"],
    json["tokenABI"],
  );

  // you can set this variable in a new 'script' tag, for example
  if (!window.RMPparams && Cookies.get("RDN-Price")) {
    window.RMPparams = {
      receiver: Cookies.get("RDN-Receiver-Address"),
      amount: +(Cookies.get("RDN-Price")),
      token: json["tokenAddr"],
    };
  } else if (!window.RMPparams) {
    window.RMPparams = {
      receiver: json["receiver"],
      amount: json["amount"],
      token: json["tokenAddr"],
    };
  }

  rmpc.getTokenInfo((err, token) => {
    if (err) {
      return console.log('Error getting token info', err);
    }
    $('.tkn-name').text(token.name);
    $('.tkn-symbol').text(token.symbol);
  });

  $("#amount").text(RMPparams["amount"]);
  $("#token").text(RMPparams.token);

  let $select = $("#accounts");

  function mainSwitch(id) {
    $(".main_switch"+id).show();
    $(".main_switch:not("+id+")").hide();
    $(".container").show();
  }

  $select.change(($event) => {
    rmpc.loadStoredChannel($event.target.value, RMPparams.receiver);

    if (rmpc.isChannelValid() &&
        rmpc.channel.account === $event.target.value &&
        rmpc.channel.receiver === RMPparams.receiver) {
      mainSwitch("#channel_present");
      rmpc.getChannelInfo((err, info) => {
        if (err) {
          console.error(err);
          info = { state: "error", deposit: 0 }
        } else if (Cookies.get('RDN-Nonexisting-Channel')) {
          console.error("Server won't accept this channel. " +
            "Please, close+settle+forget, and open a new channel");
          info.state = "invalid";
        }

        $(`#channel_present .on-state.on-state-${info.state}`).show();
        $(`#channel_present .on-state:not(.on-state-${info.state})`).hide();

        let remaining = 0;
        if (info.deposit > 0 && rmpc.channel && !isNaN(rmpc.channel.balance)) {
          remaining = info.deposit - rmpc.channel.balance;
        }
        $("#channel_present #channel_present_balance").text(balance);
        $("#channel_present #channel_present_deposit").attr("value", info.deposit);
        $(".btn-bar").show()
        if (info.state === 'opened') {
          signRetry();
        }
      });
    } else {
      mainSwitch("#channel_missing");
    }
  });

  function refreshAccounts() {
    $(`#channel_present .on-state.on-state-opened`).show();
    $(`#channel_present .on-state:not(.on-state-opened)`).hide();

    $select.empty();
    rmpc.getAccounts((err, accounts) => {
      if (err || !accounts || !accounts.length) {
        mainSwitch("#no_accounts");
        // retry after 1s
        setTimeout(refreshAccounts, 1000);
      } else {
        $.each(accounts, (k,v) => {
          const o = $("<option></option>").attr("value", v).text(v);
          $select.append(o);
          if (k === 0) {
            o.change()
          };
        });
      }
    });
  }

  refreshAccounts();

  function signRetry() {
    rmpc.incrementBalanceAndSign(RMPparams.amount, (err, sign) => {
      if (err && err.message && err.message.includes('Insuficient funds')) {
        console.error(err);
        const current = +(err.message.match(/current ?= ?(\d+)/gi)[0]);
        const required = +(err.message.match(/required ?= ?(\d+)/gi)[0]);
        $('#deposited').text(current);
        $('#required').text(required);
        $('#remaining').text(current - rmpc.channel.balance);
        return mainSwitch("#topup");
      } else if (err && err.message && err.message.includes('User denied message signature')) {
        console.error(err);
        $('.channel_present_sign').addClass('green-btn');
        return window.alert('User denied message signature');
      } else if (err) {
        console.error(err);
        return window.alert(`An error occurred trying to sign the transfer: ${err.message}`);
      }
      $('.channel_present_sign').removeClass('green-btn')
      console.log("SIGNED!", sign);
      Cookies.set("RDN-Sender-Address", rmpc.channel.account);
      Cookies.set("RDN-Open-Block", rmpc.channel.block);
      Cookies.set("RDN-Sender-Balance", rmpc.channel.balance);
      Cookies.set("RDN-Balance-Signature", sign);
      location.reload();
    });
  }

  $("#channel_missing_deposit").bind("input", ($event) => {
    if (+$event.target.value > 0) {
      $("#channel_missing_start").attr("disabled", false);
    } else {
      $("#channel_missing_start").attr("disabled", true);
    }
  });
  $("#channel_missing_start").attr("disabled", false);

  $("#channel_missing_start").click(() => {
    const deposit = +$("#channel_missing_deposit").val();
    const account = $("#accounts").val();
    mainSwitch("#channel_opening");
    rmpc.openChannel(account, RMPparams.receiver, deposit, (err, channel) => {
      if (err) {
        refreshAccounts();
        return window.alert(`An error ocurred trying to open a channel: ${err.message}`);
      }
      return signRetry();
    });
  });

  $(".channel_present_sign").click(signRetry);

  function closeChannel(closeSign) {
    rmpc.closeChannel(closeSign, (err, res) => {
      if (err) {
        return window.alert(`An error occurred trying to close the channel: ${err.message}`);
      }
      window.alert("CLOSED");
      refreshAccounts();
    });
  }

  $(".channel_present_close").click(() => {
    if (!window.confirm("Are you sure you want to close this channel?")) {
      return;
    }
    // signBalance without balance, sign current balance only if needed
    rmpc.signBalance(null, (err, sign) => {
      if (err) {
        return window.alert(`An error occurred trying to get balance signature: ${err.message}`);
      }
      // call cooperative-close URL, and closeChannel with close_signature data
      $.ajax({
        url: `/api/1/channels/${rmpc.channel.account}/${rmpc.channel.block}`,
        method: 'DELETE',
        contentType: 'application/json',
        dataType: 'json',
        data: JSON.stringify({ 'balance': rmpc.channel.balance }),
        success: (result) => {
          let closeSign = null;
          if (result && typeof result === 'object' && result['close_signature']) {
            closeSign = result['close_signature'];
          } else {
            console.warn('Invalid cooperative-close response', result);
          }
          closeChannel(closeSign);
        },
        error: (request, msg, error) => {
          console.warn('Error calling cooperative-close', request, msg, error);
          closeChannel(null);
        }
      });
    });
  });

  $(".channel_present_settle").click(() => {
    if (!window.confirm("Are you sure you want to settle this channel?")) {
      return;
    }
    rmpc.settleChannel((err, res) => {
      if (err) {
        return window.alert(`An error occurred trying to settle the channel: ${err.message}`);
      }
      window.alert("SETTLED");
      refreshAccounts();
    });
  });

  $(".channel_present_forget").click(() => {
    if (!window.confirm("Are you sure you want to forget this channel? Warning: channel will be left in an unsettled state.")) {
      return;
    }
    rmpc.forgetStoredChannel();
    refreshAccounts();
  });

  $("#topup_deposit").bind("input", ($event) => {
    if (+$event.target.value > 0) {
      $("#topup_start").attr("disabled", false);
    } else {
      $("#topup_start").attr("disabled", true);
    }
  });

  $("#topup_start").click(() => {
    const deposit = +$("#topup_deposit").val();
    mainSwitch("#channel_opening");
    rmpc.topUpChannel(deposit, (err, block) => {
      if (err) {
        refreshAccounts();
        console.error(err);
        return window.alert(`An error ocurred trying to deposit to channel: ${err.message}`);
      }
      return signRetry();
    });
  });

};

$.getJSON("/js/parameters.json", (json) => {
  let cnt = 20;
  // wait up to 20*200ms for web3 and call ready()
  const pollingId = setInterval(() => {
    if (Cookies.get("RDN-Insufficient-Confirmations")) {
      clearInterval(pollingId);
      $("body").html('<h1>Waiting confirmations...</h1>');
      setTimeout(() => location.reload(), 5000);
    } else if (cnt < 0 || window.web3) {
      clearInterval(pollingId);
      pageReady(json);
    } else {
      --cnt;
    }
  }, 200);
});
