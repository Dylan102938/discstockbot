window.onload = function() {
    document.getElementById('exp_date').value = getExpiration();
}

document.getElementById("command").onchange = function() {
    let cmd = document.getElementById("command").value;
    if (cmd === "in" || cmd === "close") {
        document.getElementById("pct").value = 1;
    } else if (cmd === "trim") {
        document.getElementById("pct").value = 0.5;
    }

    if (cmd === "close" || cmd === "trim") {
        document.getElementById("exp_date").disabled = true;
    } else if (cmd === "in") {
        document.getElementById("exp_date").disabled = false;
    }
}

$(function() {
    $('[data-toggle="datepicker"]').datepicker({
        autoHide: true,
        zIndex: 2048,
        format: 'yyyy-mm-dd'
    });
});

function getExpiration() {
    var request = new XMLHttpRequest();
    request.open('GET', url + '/get_exp_date', false);
    request.send(null);

    return request.responseText
}

function updateLimitPrice() {
    let ticker = document.getElementById('ticker').value;
    let strike_price = document.getElementById('strike_price').value;
    let option_type = document.getElementById('order_type').value;
    let exp_date = document.getElementById('exp_date').value;

    if (ticker && strike_price && exp_date) {
        $.ajax({
            type: "POST",
            url: url + "/get_option",
            contentType: 'application/json;charset=UTF-8',
            data: JSON.stringify({
                'ticker': ticker,
                'strike_price': strike_price,
                'option_type': option_type,
                'exp_date': exp_date,
            }),
            error: function(jqXHR, textStatus, errorThrown) {
                console.log('Could not get option limit price because invalid info was passed.')
            },
            success: function(data) {
                data = data.results[0]
                console.log(data)
                if (document.getElementById('command').value === 'in') {
                    document.getElementById('price').value = parseFloat(data.ask_price).toFixed(2);
                } else {
                    document.getElementById('price').value = parseFloat(data.bid_price).toFixed(2);
                }
            }
        });
    }
}

document.getElementById('command').addEventListener('change', updateLimitPrice);
document.getElementById('ticker').addEventListener('change', updateLimitPrice);
document.getElementById('strike_price').addEventListener('change', updateLimitPrice);
document.getElementById('order_type').addEventListener('change', updateLimitPrice);
document.getElementById('exp_date').addEventListener('change', updateLimitPrice);
