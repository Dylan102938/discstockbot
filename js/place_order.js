var count = 0;

document.getElementById('submit').onclick = function(e) {
    e.preventDefault();

    let command = document.getElementById('command').value;
    let ticker = document.getElementById('ticker').value.toUpperCase();
    let strike_price = document.getElementById('strike_price').value;
    let option_type = document.getElementById('order_type').value;
    let price = document.getElementById('price').value;
    let exp_date = document.getElementById('exp_date').value;
    let pct = document.getElementById('pct').value;
    let watch_price = document.getElementById('watch_price').value;

    let d = new Date().toLocaleTimeString();
    let html = "<tr id='" + count + "'> \
    <td>Queued</td> \
    <td>"+ command +"</td> \
    <td>"+ ticker +"</td> \
    <td>"+ strike_price +"</td> \
    <td>"+ option_type +"</td> \
    <td>"+ price +"</td> \
    <td>"+ pct +"</td> \
    <td>0 / 0</td> \
    <td>"+ d +"</td></tr>";

    document.getElementById("past_trades").innerHTML += html;

    var current_count = count;
    $.ajax({
        type: "POST",
        url: url + "/exec_order",
        contentType: 'application/json;charset=UTF-8',
        data: JSON.stringify({
            'command': command,
            'ticker': ticker,
            'strike_price': strike_price,
            'option_type': option_type,
            'price': price,
            'exp_date': exp_date,
            'pct': pct,
            'watch_price': watch_price
        }),
        error: function(jqXHR, textStatus, errorThrown) {
            errorHelper(jqXHR, textStatus, errorThrown);
        },
        success: function(data) {
            let html = "\
            <td>Completed</td> \
            <td>"+ command +"</td> \
            <td>"+ ticker +"</td> \
            <td>"+ strike_price +"</td> \
            <td>"+ option_type +"</td> \
            <td>"+ price +"</td> \
            <td>"+ pct +"</td>";

            let passed = 0
            let total = 0
            for (let i = 0; i < data.order_statuses.length; i++) {
                if (data.order_statuses[i].hasOwnProperty('created_at')) {
                    passed++;
                }

                total++;
            }

            html += "<td>" + passed + " / " + total + "</td>";
            let d = new Date().toLocaleTimeString();
            html += "<td>" + d + "</td>";
            document.getElementById(current_count.toString()).innerHTML = html;
        }
    });

    let msg = "\n\nCommand: " + command.toUpperCase() +
    "\nSymbol: " + ticker +
    "\nStrike Price: " + strike_price +
    "\nOption Type: " + option_type.toUpperCase();

    if (command === 'in' || command === 'watch') {
        msg += "\nExpiration Date: " + exp_date;
    }

    if (watch_price && option_type === 'call') {
        "\nExpiration Date: " + exp_date;
        msg += "\nWatch Price: " + " Over " + watch_price;
    } else if (watch_price && option_type === 'put') {
        msg += "\nWatch Price: " + " Under " + watch_price;
    }

    sendMessage(msg);
    count++;
}

function sendMessage(msg) {
    let webhook = "https://discord.com/api/webhooks/792231664138846249/bJ3s9oZbjkdSDWVuueJS_1DfbgXqf852nIG21tfEVSL_HCQGkyGSQYpVl_KuR9lWSiCk";
    var payload = JSON.stringify({content: msg});
    $.ajax({
        type: "POST",
        url: webhook,
        contentType: 'application/json;charset=UTF-8',
        data: payload,
        error: function(jqXHR, textStatus, errorThrown) {
            errorHelper(jqXHR, textStatus, errorThrown);
        },
    });
}
