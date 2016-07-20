$(function(){
    var comment_factor = 5;
    var like_factor = 1;
    /*
    var posting_data = {
        'labels': raw_data.map(function(item){
            return item.timestamp;
        }),
        'datasets': [{
            'label': 'Total',
            'type': 'line',
            'fillColor': 'rgba(151,187,205,0.5)',
            'strokeColor': 'rgba(151,187,205,0.8)',
            'highlightFill': 'rgba(151,187,205,0.75)',
            'highlightStroke': 'rgba(151,187,205,1)',
            'data': raw_data.map(function(item){
                return item.total.images;
            }),
        },
        {
            'label': 'Interval',
            'type': 'bar',
            'fillColor': 'rgba(151,187,205,0.5)',
            'strokeColor': 'rgba(151,187,205,0.8)',
            'highlightFill': 'rgba(151,187,205,0.75)',
            'highlightStroke': 'rgba(151,187,205,1)',
            'data': raw_data.map(function(item){
                return item.interval.images;
            }),
        }],
    };
    var ctx = $('#images-graph').get(0).getContext('2d');
    var chart = new Chart(ctx).Overlay(posting_data, {
    });

    var engagement_data = {
        'labels': raw_data.map(function(item){
            return item.timestamp;
        }),
        'datasets': [{
            'label': 'Total',
            'type': 'line',
            'fillColor': 'rgba(151,187,205,0.5)',
            'strokeColor': 'rgba(151,187,205,0.8)',
            'highlightFill': 'rgba(151,187,205,0.75)',
            'highlightStroke': 'rgba(151,187,205,1)',
            'data': raw_data.map(function(item){
                return item.total.likes*like_factor
                    +item.total.comments*comment_factor;
            }),
        },
        {
            'label': 'Interval',
            'type': 'bar',
            'fillColor': 'rgba(151,187,205,0.5)',
            'strokeColor': 'rgba(151,187,205,0.8)',
            'highlightFill': 'rgba(151,187,205,0.75)',
            'highlightStroke': 'rgba(151,187,205,1)',
            'data': raw_data.map(function(item){
                return item.interval.likes*like_factor
                    +item.interval.comments*comment_factor;
            }),
        }],
    };
    var ctx = $('#engagement-graph').get(0).getContext('2d');
    var chart = new Chart(ctx).Overlay(engagement_data, {
    });
    */

    var image_data = [
        {
            'key':'Interval',
            'bar':true,
            'color': '#ccf',
            'values': raw_data.map(function(item){
                return [1000*item.unixtime, item.interval.images];
            }),
        },
        {
            'key':'Total',
            'color': '#333',
            'values': raw_data.map(function(item){
                return [1000*item.unixtime, item.total.images];
            }),
        },
    ];
    nv.addGraph(function() {
        var chart = nv.models.linePlusBarChart()
            .margin({top: 30, right: 40, bottom: 50, left: 40})
            //We can set x data accessor to use index. Reason? So the bars all appear evenly spaced.
            .x(function(d,i) { return i })
            .y(function(d,i) {return d[1] })
            ;

        chart.xAxis.tickFormat(function(d) {
            var dx = image_data[0].values[d] && image_data[0].values[d][0] || 0;
            return d3.time.format('%x')(new Date(dx))
        });

        chart.y1Axis
            .tickFormat(d3.format(',f'));

        chart.y2Axis
            .tickFormat(d3.format(',f'));

        chart.bars.forceY([0]);

        d3.select('#images-graph svg')
            .datum(image_data)
            .transition()
            .duration(0)
            .call(chart);

        nv.utils.windowResize(chart.update);

        return chart;
    });

    var engagement_data = [
        {
            'key':'Interval',
            'bar':true,
            'color': '#ccf',
            'values': raw_data.map(function(item){
                return [1000*item.unixtime, 
                    item.interval.likes*like_factor +
                    item.interval.comments*comment_factor
                ];
            }),
        },
        {
            'key':'Total',
            'color': '#333',
            'values': raw_data.map(function(item){
                return [1000*item.unixtime, 
                    item.total.likes*like_factor + 
                    item.total.comments*comment_factor
                ];
            }),
        },
    ];
    nv.addGraph(function() {
        var chart = nv.models.linePlusBarChart()
            .margin({top: 30, right: 40, bottom: 50, left: 40})
            //We can set x data accessor to use index. Reason? So the bars all appear evenly spaced.
            .x(function(d,i) { return i })
            .y(function(d,i) {return d[1] })
            ;

        chart.xAxis.tickFormat(function(d) {
            var dx = engagement_data[0].values[d] && engagement_data[0].values[d][0] || 0;
            return d3.time.format('%x')(new Date(dx))
        });

        chart.y1Axis
            .tickFormat(d3.format(',f'));

        chart.y2Axis
            .tickFormat(d3.format(',f'));

        chart.bars.forceY([0]);

        d3.select('#engagement-graph svg')
            .datum(engagement_data)
            .transition()
            .duration(0)
            .call(chart);

        nv.utils.windowResize(chart.update);

        return chart;
    });

    nv.addGraph(function() {
      var chart = nv.models.pieChart()
          .x(function(d) { return d.label })
          .y(function(d) { return d.value })
          .showLabels(false)     //Display pie labels
          .donut(true)          //Turn on Donut mode. Makes pie chart look tasty!
          .donutRatio(0.60)     //Configure how big you want the donut hole size to be.
          ;

        d3.select("#tag-graph svg")
            .datum(tag_data)
            .transition().duration(350)
            .call(chart);

      return chart;
    });

});
