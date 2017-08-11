function pageReady(json) {
  window.rmpc = new RaidenMicropaymentsClient(
    window.web3,
    json["contractAddr"],
    json["contractABI"],
    json["tokenAddr"],
    json["tokenABI"],
  );

  // you can set this variable in a new 'script' tag, for example
  if (!window.RMPparams) {
    window.RMPparams = {
      receiver: json["receiver"],
      amount: json["amount"],
      token: json["tokenAddr"],
    };
  }

  $("#amount").text(RMPparams["amount"]);
  $("#token").text(RMPparams.token);

  let $select = $("#accounts");

  function pageSwitch(id) {
    $(".page_switch"+id).show();
    $(".page_switch:not("+id+")").hide();
  }
  pageSwitch("#payment_window");

  function mainSwitch(id) {
    $(".main_switch"+id).show();
    $(".main_switch:not("+id+")").hide();
  }

  function retrySigned() {
    Cookies.set("RDN-Sender-Balance", rmpc.channel.balance);
    Cookies.set("RDN-Balance-Signature", rmpc.channel.sign);
    location.reload();
  }

  $select.change(($event) => {
    rmpc.loadStoredChannel($event.target.value, RMPparams.receiver);

    if (rmpc.isChannelValid() &&
        rmpc.channel.account === $event.target.value &&
        rmpc.channel.receiver === RMPparams.receiver) {
      $("#channel_present_desc").text(JSON.stringify(rmpc.channel, null, 2));
      mainSwitch("#channel_present");
    } else {
      mainSwitch("#channel_missing");
    }
  });

  function refreshAccounts() {
    $select.empty();
    rmpc.getAccounts((err, accounts) =>
      $.each(accounts, (k,v) => {
        const o = $("<option></option>").attr("value", v).text(v);
        $select.append(o);
        if (k === 0) {
          o.change()
        };
      })
    );
  }

  refreshAccounts();

  $("#channel_missing_deposit").bind("input", ($event) => {
    if (+$event.target.value > 0) {
      $("#channel_missing_start").attr("disabled", false);
    } else {
      $("#channel_missing_start").attr("disabled", true);
    }
  });
  $("#channel_missing_start").attr("disabled", true);

  $("#channel_missing_start").click(() => {
    const deposit = +$("#channel_missing_deposit").val();
    const account = $("#accounts").val();
    mainSwitch("#channel_opening");
    rmpc.openChannel(account, RMPparams.receiver, deposit, (err, sign) => {
      if (err) {
        refreshAccounts();
        return window.alert("An error ocurred trying to open a channel: "+err);
      }
      return rmpc.incrementBalanceAndSign(RMPparams.amount, (err, res) => {
        refreshAccounts();
        if (err) {
          console.error(err);
          return window.alert("An error ocurred trying to sign the transfer: "+err);
        }
        console.log("SIGNED!", sign);
        return retrySigned();
      });
    });
  });

  $("#channel_present_sign").click(() => {
    rmpc.incrementBalanceAndSign(RMPparams.amount, (err, res) => {
      if (err) {
        console.error(err);
        return window.alert("An error occurred trying to sign the transfer: "+err);
      }
      console.log("SIGNED!", res);
      return retrySigned();
    });
  });

  $("#channel_present_close").click(() => {
    if (!window.confirm("Are you sure you want to close this channel?")) {
      return;
    }
    rmpc.closeChannel(null, (err, res) => {
      if (err) {
        return window.alert("An error occurred trying to close the channel: "+err);
      }
      window.alert("CLOSED");
      refreshAccounts();
    });
  });

  $("#channel_present_settle").click(() => {
    if (!window.confirm("Are you sure you want to settle this channel?")) {
      return;
    }
    rmpc.settleChannel((err, res) => {
      if (err) {
        return window.alert("An error occurred trying to settle the channel: "+err);
      }
      window.alert("SETTLED");
      refreshAccounts();
    });
  });

  $("#channel_present_forget").click(() => {
    if (!window.confirm("Are you sure you want to forget this channel?")) {
      return;
    }
    rmpc.forgetStoredChannel();
    refreshAccounts();
  });

};

$.getJSON("parameters.json", (json) => {
  let cnt = 20;
  // wait up to 20*200ms for web3 and call ready()
  const pollingId = setInterval(() => {
    if (cnt < 0 || window.web3) {
      clearInterval(pollingId);
      pageReady(json);
    } else {
      --cnt;
    }
  }, 200);
});
