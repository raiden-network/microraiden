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
  $select.empty();

  $select.change(($event) => {
    rmpc.loadStoredChannel($event.target.value, RMPparams.receiver);

    if (rmpc.isChannelValid() &&
        rmpc.channel.account === $event.target.value &&
        rmpc.channel.receiver === RMPparams.receiver) {
      $(".main_switch#channel_present").show();
      $(".main_switch:not(#channel_present)").hide();
      $("#channel_present_desc").text(JSON.stringify(rmpc.channel, 2));
    } else {
      $(".main_switch#channel_missing").show();
      $(".main_switch:not(#channel_missing)").hide();
    }
  });

  rmpc.getAccounts((err, res) => $.each(res, (k,v) => {
    const o = $("<option></option>").attr("value", v).text(v);
    $select.append(o);
    if (k === 0) {
      o.change()
    };
  }));

  $("#channel_present_sign").click(() =>
    rmpc.incrementBalanceAndSign(RMPparams.amount, (err, res) => {
      if (err) {
        return window.alert("An error occurred trying to sign the transfer: "+err);
      }
      return window.alert("SIGNED: "+res);
    })
  );

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
    rmpc.openChannel(account, RMPparams.receiver, deposit, (err, res) => {
      if (err) {
        return window.alert("An error ocurred trying to open a channel: "+err);
      }
      return rmpc.incrementBalanceAndSign(RMPparams.amount, (err, res) => {
        if (err) {
          return window.alert("An error ocurred trying to sign the transfer: "+err);
        }
        return window.alert("SIGNED: "+res);
      });
    });
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
