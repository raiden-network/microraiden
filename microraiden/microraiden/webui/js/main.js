function mainSwitch(id) {
  $(".main_switch"+id).show();
  $(".main_switch:not("+id+")").hide();
  $(".container").show();
}

function pageReady(json) {

  // ==== BASIC INITIALIZATION ====

  // you can set this variable in a new 'script' tag, for example
  if (!window.uRaidenParams && Cookies.get("RDN-Price")) {
    window.uRaidenParams = {
      contract: Cookies.get("RDN-Contract-Address"),
      token: Cookies.get("RDN-Token-Address"),
      receiver: Cookies.get("RDN-Receiver-Address"),
      amount: +(Cookies.get("RDN-Price")),
    };
  } else if (!window.uRaidenParams) {
    window.uRaidenParams = {
      contract: json["contractAddr"],
      token: json["tokenAddr"],
      receiver: json["receiver"],
      amount: json["amount"],
    };
  }

  window.uraiden = new microraiden.MicroRaiden(
    window.web3,
    uRaidenParams.contract,
    json["contractABI"],
    uRaidenParams.token,
    json["tokenABI"],
  );

  // ==== MAIN VARIABLES ====

  var $accounts = $("#accounts");
  var autoSign = false;

  // ==== FUNCTIONS ====

  function errorDialog(text, err) {
    var msg = err && err.message ?
      err.message.split(/\r?\n/)[0] :
      typeof err === "string" ?
        err.split(/\r?\n/)[0] :
        JSON.stringify(err);
    return window.alert(text+ ':\n' + msg);
  }

  function refreshAccounts(_autoSign) {

    autoSign = !!_autoSign;

    $accounts.empty();
    uraiden.getAccounts()
      .then(function(accounts) {
        if (!accounts || !accounts.length) {
          throw new Error('No account');
        }
        mainSwitch("#channel_loading");
        $.each(accounts, function(k,v) {
          var o = $("<option></option>").attr("value", v).text(v);
          $accounts.append(o);
          if (k === 0) {
            $accounts.change();
          };
        });
      })
      .catch(function(err) {
        mainSwitch("#no_accounts");
        // retry after 1s
        setTimeout(refreshAccounts, 1000);
      });
  }

  function signRetry() {
    autoSign = false;
    uraiden.incrementBalanceAndSign(uRaidenParams.amount)
      .then(function(sign) {
        $('.channel_present_sign').removeClass('green-btn')
        console.log("SIGNED!", sign);
        Cookies.set("RDN-Sender-Address", uraiden.channel.account);
        Cookies.set("RDN-Open-Block", uraiden.channel.block);
        Cookies.set("RDN-Sender-Balance", uraiden.channel.balance);
        Cookies.set("RDN-Balance-Signature", sign);
        Cookies.remove("RDN-Nonexisting-Channel");
        $('html').load(location.href, function(res, status, xhr) {
          if ( status === 'error' ) {
            errorDialog("An error ocurred re-sending request", xhr.statusText);
          } else {
            uraiden.confirmPayment(sign);
          }
        });
      })
      .catch(function(err) {
        if (err.message && err.message.includes('Insuficient funds')) {
          console.error(err);
          var current = +(err.message.match(/current ?= ?([\d.,]+)/i)[1]);
          var required = +(err.message.match(/required ?= ?([\d.,]+)/i)[1]) - current;
          $('#deposited').text(current);
          $('#required').text(required);
          $('#remaining').text(current - uraiden.channel.balance);
          mainSwitch("#topup");
        } else if (err.message && err.message.includes('User denied message signature')) {
          console.error(err);
          $('.channel_present_sign').addClass('green-btn');
        } else {
          console.error(err);
          errorDialog("An error occurred trying to sign the transfer", err);
          refreshAccounts();
        }
      });
  }

  function closeChannel(closeSign) {
    return uraiden.closeChannel(closeSign)
      .then(function(res) {
        console.log("CLOSED", res);
        refreshAccounts();
        return res;
      })
      .catch(function(err) {
        errorDialog("An error occurred trying to close the channel", err);
        refreshAccounts();
        throw err;
      });
  }

  // ==== BINDINGS ====

  $accounts.change(function($event) {
    var account = $event.target.value;

    uraiden.loadStoredChannel(account, uRaidenParams.receiver);

    uraiden.getTokenInfo(account)
      .then(function(token) {
        $('.tkn-name').text(token.name);
        $('.tkn-symbol').text(token.symbol);
        $('.tkn-balance').attr("value", (token.balance || 0) + ' ' + token.symbol);
        $('.tkn-decimals')
          .attr("min", Math.pow(10, -token.decimals).toFixed(token.decimals));

        if (uraiden.isChannelValid() &&
            uraiden.channel.account === $event.target.value &&
            uraiden.channel.receiver === uRaidenParams.receiver) {

          return uraiden.getChannelInfo()
            .then(function(info) {
              if (Cookies.get("RDN-Nonexisting-Channel")) {
                Cookies.remove("RDN-Nonexisting-Channel");
                window.alert("Server won't accept this channel.\n" +
                  "Please, close+settle+forget, and open a new channel");
                $('#channel_present .channel_present_sign').attr("disabled", true);
                autoSign = false;
              }
              return info;
            })
            .catch(function(err) {
              console.error(err);
              return { state: "error", deposit: 0 }
            })
            .then(function(info) {
              $('#channel_present .on-state.on-state-' + info.state).show();
              $('#channel_present .on-state:not(.on-state-'+ info.state + ')').hide();

              var remaining = 0;
              if (info.deposit > 0 && uraiden.channel && !isNaN(uraiden.channel.balance)) {
                remaining = info.deposit - uraiden.channel.balance;
              }
              $("#channel_present #channel_present_balance").text(remaining);
              $("#channel_present #channel_present_deposit").attr("value", info.deposit);
              $(".btn-bar").show()
              if (info.state === 'opened' && autoSign) {
                signRetry();
              }
              mainSwitch("#channel_present");
            });
        } else {
          mainSwitch("#channel_missing");
        }
      })
      .catch(function(err) {
         console.error('Error getting token info', err);
      });
  });

  $("#channel_missing_deposit").bind("input", function($event) {
    if (+$event.target.value > 0) {
      $("#channel_missing_start").attr("disabled", false);
    } else {
      $("#channel_missing_start").attr("disabled", true);
    }
  });
  $("#channel_missing_start").attr("disabled", false);

  $("#channel_missing_start").click(function() {
    var deposit = +$("#channel_missing_deposit").val();
    var account = $("#accounts").val();
    mainSwitch("#channel_opening");
    uraiden.openChannel(account, uRaidenParams.receiver, deposit)
      .then(function(channel) {
        Cookies.remove("RDN-Nonexisting-Channel");
        refreshAccounts(true);
      })
      .catch(function(err) {
        console.error(err);
        errorDialog("An error ocurred trying to open a channel", err);
        refreshAccounts();
      });
  });

  $(".channel_present_sign").click(signRetry);

  $(".channel_present_close").click(function() {
    if (!window.confirm("Are you sure you want to close this channel?")) {
      return;
    }
    mainSwitch("#channel_opening");
    // if cooperative close signature exists, use it (api will fail)
    if (uraiden.channel.close_sign) {
      return closeChannel(uraiden.channel.close_sign);
    }
    // signBalance without balance, sign (if needed) and return current balance
    return uraiden.signBalance(null)
      .catch(function(err) {
        errorDialog("An error occurred trying to get balance signature", err);
        refreshAccounts();
        throw err;
      })
      .then(function(sign) {
        // call cooperative-close URL, and closeChannel with close_signature data
        return $.ajax({
          url: '/api/1/channels/' + uraiden.channel.account + '/' + uraiden.channel.block,
          method: 'DELETE',
          contentType: 'application/json',
          dataType: 'json',
          data: JSON.stringify({ 'balance': uraiden.channel.balance }),
        })
        .done(function(result) {
          var closeSign = null;
          if (result && typeof result === 'object' && result['close_signature']) {
            closeSign = result['close_signature'];
          } else {
            console.warn('Invalid cooperative-close response', result);
          }
          return closeChannel(closeSign);
        })
        .fail(function(request, msg, error) {
          console.warn('Error calling cooperative-close', request, msg, error);
          return closeChannel(null);
        });
      });
  });

  $(".channel_present_settle").click(function() {
    if (!window.confirm("Are you sure you want to settle this channel?")) {
      return;
    }
    mainSwitch("#channel_opening");
    uraiden.settleChannel()
      .then(function(res) {
        console.log("SETTLED", res);
        refreshAccounts();
      })
      .catch(function(err) {
        errorDialog("An error occurred trying to settle the channel", err);
        refreshAccounts();
      });
  });

  $(".channel_present_forget").click(function() {
    if (!window.confirm("Are you sure you want to forget this channel?" +
        ($('.on-state-settled').is(':visible') ? "" :
         "\nWarning: channel will be left in an unsettled state."))) {
      return;
    }
    Cookies.remove("RDN-Sender-Address");
    Cookies.remove("RDN-Open-Block");
    Cookies.remove("RDN-Sender-Balance");
    Cookies.remove("RDN-Balance-Signature");
    Cookies.remove("RDN-Nonexisting-Channel");
    uraiden.forgetStoredChannel();
    refreshAccounts();
  });

  $("#topup_deposit").bind("input", function($event) {
    if (+$event.target.value > 0) {
      $("#topup_start").attr("disabled", false);
    } else {
      $("#topup_start").attr("disabled", true);
    }
  });

  $("#topup_start").click(function() {
    var deposit = +$("#topup_deposit").val();
    mainSwitch("#channel_opening");
    uraiden.topUpChannel(deposit)
      .then(function() {
        refreshAccounts(true);
      })
      .catch(function(err) {
        refreshAccounts();
        console.error(err);
        errorDialog("An error ocurred trying to deposit to channel", err);
      });
  });

  $(".token_buy").click(function() {
    var account = $accounts.val();
    mainSwitch("#channel_opening");
    uraiden.buyToken(account)
      .then(refreshAccounts)
      .catch(function(err) {
        console.error(err);
        errorDialog("An error ocurred trying to buy tokens", err);
      });
  });

  // ==== FINAL SETUP ====

  $("#amount").text(uRaidenParams["amount"]);
  refreshAccounts(true);
  $('[data-toggle="tooltip"]').tooltip();

};


mainSwitch("#channel_loading");

$.getJSON("/js/parameters.json", function(json) {
  var cnt = 20;
  // wait up to 20*200ms for web3 and call ready()
  var pollingId = setInterval(function() {
    if (Cookies.get("RDN-Insufficient-Confirmations")) {
      Cookies.remove("RDN-Insufficient-Confirmations");
      clearInterval(pollingId);
      $("body").html('<h1>Waiting confirmations...</h1>');
      setTimeout(function() { location.reload(); }, 5000);
    } else if (cnt < 0 || window.web3) {
      clearInterval(pollingId);
      pageReady(json);
    } else {
      --cnt;
    }
  }, 200);
});
