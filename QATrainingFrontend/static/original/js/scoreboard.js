function updatescores () {
  $.get(script_root + '/scores', function( data ) {
    users = $.parseJSON(JSON.stringify(data));
    $('#scoreboard > tbody').empty()
    for (var i = 0; i < users['standings'].length; i++) {
      row = "<tr><td>{0}</td><td><a href='/user/{1}'>{2}</a></td><td>{3}</td></tr>".format(i+1, users['standings'][i].id, htmlentities(users['standings'][i].user), users['standings'][i].score)
      $('#scoreboard > tbody').append(row)
    };
  });
}

function cumulativesum (arr) {
    var result = arr.concat();
    for (var i = 0; i < arr.length; i++){
        result[i] = arr.slice(0, i + 1).reduce(function(p, i){ return p + i; });
    }
    return result
}

function UTCtoDate(utc){
    var d = new Date(0)
    d.setUTCSeconds(utc)
    return d;
}
function scoregraph () {
    $.get(script_root + '/top/10', function( data ) {
        var scores = $.parseJSON(JSON.stringify(data));
        scores = scores['scores'];
        if (Object.keys(scores).length == 0 ){
            return;
        }

        var users = Object.keys(scores);
        var traces = [];
        for(var i = 0; i < users.length; i++){
            var user_score = [];
            var times = [];
            for(var j = 0; j < scores[users[i]].length; j++){
                user_score.push(scores[users[i]][j].value);
                var date = moment(scores[users[i]][j].time * 1000);
                times.push(date.toDate());
            }
            user_score = cumulativesum(user_score);
            var trace = {
                x: times,
                y: user_score,
                mode: 'lines+markers',
                name: users[i]
            }
            traces.push(trace);
        }

        var layout = {
            title: 'Top 10 Users'
        };
        console.log(traces);

        Plotly.newPlot('score-graph', traces, layout);


        $('#score-graph').show()
    });
}

function update(){
  updatescores();
  scoregraph();
}

setInterval(update, 300000); // Update scores every 5 minutes
scoregraph();

window.onresize = function () {
    Plotly.Plots.resize(document.getElementById('score-graph'));
};
