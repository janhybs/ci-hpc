/**
 * Create a constructor for sparklines that takes some sensible defaults and merges in the individual
 * chart options. This function is also available from the jQuery plugin as $(element).highcharts('SparkLine').
 */
Highcharts.SparkMedium = function(a, b, c) {
  var hasRenderToArg = typeof a === 'string' || a.nodeName,
    options = arguments[hasRenderToArg ? 1 : 0],
    defaultOptions = {
      chart: {
        renderTo: (options.chart && options.chart.renderTo) || this,
        backgroundColor: null,
        borderWidth: 0,
        type: 'area',
        width: null,
        height: 340,
        style: {
          overflow: 'visible'
        },
        // small optimalization, saves 1-2 ms each sparkline
        skipClone: true,
        // marginBottom: 100
      },
      legend: {
        enabled: false,
        align: 'center',
        verticalAlign: 'bottom',
        x: 0,
        y: 0
      },
      title: {
        text: ''
      },
      credits: {
        enabled: false
      },
      xAxis: {
        labels: {
          enabled: false
        },
        // title: {
        //   text: null
        // },
        // startOnTick: false,
        // endOnTick: false,
        // tickPositions: []
      },
      yAxis: {
        labels: {
          enabled: false
        },
        // endOnTick: false,
        // startOnTick: false,
        // title: {
        //   text: null
        // },
        // tickPositions: [0]
      },
      tooltip: {
        borderWidth: 0,
        shadow: false,
        useHTML: true,
        hideDelay: 200,
        shared: true,
        padding: 5,
        positioner: function(w, h, point) {
          return {
            x: point.plotX - w / 2,
            y: point.plotY - h
          };
        }
      },
      plotOptions: {
        series: {
          animation: false,
          lineWidth: 1,
          shadow: false,
          states: {
            hover: {
              lineWidth: 1
            }
          },
          marker: {
            radius: 1,
            states: {
              hover: {
                radius: 2
              }
            }
          },
          fillOpacity: 0.25
        },
        column: {
          negativeColor: '#910000',
          borderColor: 'silver'
        }
      },
      
      responsive: {
          rules: [{
              condition: {
                  minHeight: 500
              },
              chartOptions: {
                  legend: {
                      enabled: true
                  },
                  yAxis: {
                      labels: { 
                          enabled: true
                      }
                  },
                  xAxis: {
                      labels: { 
                          enabled: true
                      }
                  }
              }
          }]
      }
    };

  options = Highcharts.merge(defaultOptions, options);

  return hasRenderToArg ?
    new Highcharts.Chart(a, options, c) :
    new Highcharts.Chart(options, b);
    
  return hasRenderToArg ?
    new Highcharts.stockChart(a, options, c) :
    new Highcharts.stockChart(options, b);
};


/**
 * Create a constructor for sparklines that takes some sensible defaults and merges in the individual
 * chart options. This function is also available from the jQuery plugin as $(element).highcharts('SparkLine').
 */
Highcharts.SparkLine = function(a, b, c) {
  var hasRenderToArg = typeof a === 'string' || a.nodeName,
    options = arguments[hasRenderToArg ? 1 : 0],
    defaultOptions = {
      chart: {
        renderTo: (options.chart && options.chart.renderTo) || this,
        backgroundColor: null,
        borderWidth: 0,
        type: 'area',
        // margin: [2, 0, 2, 0],
        // padding: [2, 0, 2, 0],
        width: null,
        height: 120,
        style: {
          overflow: 'visible'
        },

        // small optimalization, saves 1-2 ms each sparkline
        skipClone: true
      },
      title: {
        text: ''
      },
      credits: {
        enabled: false
      },
      xAxis: {
        labels: {
          enabled: false
        },
        title: {
          text: null
        },
        startOnTick: false,
        endOnTick: false,
        tickPositions: []
      },
      yAxis: {
        endOnTick: false,
        startOnTick: false,
        labels: {
          enabled: false
        },
        title: {
          text: null
        },
        tickPositions: [0]
      },
      legend: {
        enabled: false
      },
      tooltip: {
        borderWidth: 0,
        shadow: false,
        useHTML: true,
        hideDelay: 5000,
        shared: true,
        padding: 5,
        positioner: function(w, h, point) {
          return {
            x: point.plotX - w / 2,
            y: point.plotY - h
          };
        }
      },
      plotOptions: {
        series: {
          animation: false,
          lineWidth: 1,
          shadow: false,
          states: {
            hover: {
              lineWidth: 1
            }
          },
          marker: {
            radius: 1,
            states: {
              hover: {
                radius: 2
              }
            }
          },
          fillOpacity: 0.25
        },
        column: {
          negativeColor: '#910000',
          borderColor: 'silver'
        }
      }
    };

  options = Highcharts.merge(defaultOptions, options);

  return hasRenderToArg ?
    new Highcharts.Chart(a, options, c) :
    new Highcharts.Chart(options, b);
};
