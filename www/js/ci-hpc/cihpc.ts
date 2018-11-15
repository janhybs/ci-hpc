class CIHPC {

  static url_base: string;
  static git_url: string;
  static commit_url: string;

  static testDict: object;
  static paused: boolean = false;
  static sender: HTMLElement;
  static layout: string = 'medium';
  static layouts: string[] = ['medium', 'large', 'small'];
  
  
  static getFilters = function(opts: any, level: string) {
    var result: object = $.extend({}, opts.filters);
    if (level === null) {
      return result;
    }
    result[level] = opts.name;
    return result;
  };



  static grabFilters = function(elem: HTMLElement) {
    return CIHPC.testDict[elem.id];
  };

  private static _getCommitUrl(git_url: string) {
    var tmp = git_url.replace('http://', '').replace('https://', '');
    if (!!~tmp.indexOf('bitbucket.org')) {
      return git_url + '/commits';
    }

    return git_url + '/commit';
  }

  static addTestList(config: any) {
    $('#benchmark-list').empty();
    $('#benchmark-list').html(
      Templates.benchmarkList.render({
        title: config.name,
        desc: config.desc,
        git_url: config['git-url'],
        tests: config.tests,
      })
    );
  };

  static addFilters(config: any) {
    var testView: any = config['test-view'];
    var fields: any = config['fields'];


    $('#cihpc-option-holder').empty();
    $('#cihpc-option-holder').append(
      Templates.dateSliders.render({
        text: 'Commit range',
        key: 'range',
        items: [
          { name: 'from', value: 'min', title: 'From' },
          { name: 'to', value: 'max', title: 'To' },
        ]
      })
    );
    $('#cihpc-option-holder').append(
      Templates.dateSliders.render(
        ConfigureViewFilters.filterCommitSqueeze
      )
    );

    $('#cihpc-option-holder').append('<hr />');

    if (fields['problem.cpu']) {
      $('#cihpc-option-holder').append(
        Templates.groupToggle.render(
          ConfigureViewFilters.filterMode
        )
      );
    }

    $('#cihpc-option-holder').append('<hr />');

    if (testView.groupby) {
      var groupby = [];
      for (let key in testView.groupby) {
        groupby.push({
          text: testView.groupby[key],
          name: key,
          checked: true,
          desc: '[user option] if checked, will split the results into groups' +
            'based on <code>' + key + '</code> value each group will have its own chart.'
        });
      }

      $('#cihpc-option-holder').append(
        Templates.groupToggle.render({
          text: 'Group by',
          key: 'groupby',
          items: groupby.concat(ConfigureViewFilters.filterGroupBy(fields))
        })
      );
    }

    $('#cihpc-option-holder').append('<hr />');

    $('#cihpc-option-holder').append(
      Templates.groupToggle.render(
        ConfigureViewFilters.filterSeries
      )
    );
  };


  static init(config: any) {
    CIHPC.git_url = config['git-url'];
    CIHPC.commit_url = CIHPC._getCommitUrl(CIHPC.git_url);
    CIHPC.testDict = {};

    document.title = config.name;

    if (config.logo) {
      $('#logo').attr('src', config.logo);
    }

    var testLevelName = config.fields['problem.test'],
      caseLevelName = config.fields['problem.case'],
      subCaseLevelName = config.fields['problem.subcase'];

    for (let testLevel in config.tests) {
      var testItem = config.tests[testLevel];
      CIHPC.testDict['test-' + testItem.name] = $.extend({},
        CIHPC.getFilters(testItem, testItem.level === undefined ? testLevelName : testItem.level),
      );
      for (let caseLevel in testItem.tests) {
        var caseItem = testItem.tests[caseLevel];
        CIHPC.testDict['test-' + testItem.name + '-' + caseItem.name] = $.extend(
          CIHPC.getFilters(caseItem, caseItem.level === undefined ? caseLevelName : caseItem.level),
          CIHPC.getFilters(testItem, testItem.level === undefined ? testLevelName : testItem.level),
        );
        for (let subcaseLevel in caseItem.tests) {
          var subcaseItem = caseItem.tests[subcaseLevel];
          CIHPC.testDict['test-' + testItem.name + '-' + caseItem.name + '-' + subcaseItem.name] = $.extend(
            CIHPC.getFilters(subcaseItem, subcaseItem.level === undefined ? subCaseLevelName : subcaseItem.level),
            CIHPC.getFilters(caseItem, caseItem.level === undefined ? caseLevelName : caseItem.level),
            CIHPC.getFilters(testItem, testItem.level === undefined ? testLevelName : testItem.level),
          );
        }
      }
    }
  };
  
  static showHistory  = function() {
    $('#loader').show();
    $('#charts-sm').empty();
    
    $.ajax({
      url: CIHPC.url_base + '/commit-history',

      error: function(error) {
        console.log({error});
        $('#loader').hide();
        alert('fatal error');
      },

      success: function(result) {
        console.log(result[0]);
        $('#loader').hide();
        $('#charts-sm').html(
          Templates.commitHistory.render({
            id:'commit-history-table',
            commit_url: CIHPC.commit_url,
            keys: Object.keys(result[0]),
            items: result
          })
        );
        $('#commit-history-table').DataTable({
          searching: false,
          paging: false,
          autoWidth: false,
        });
      }
    });
  };

  static destroyAllCharts = function() {
    if (Highcharts.charts) {
      for (let chart of Highcharts.charts) {
        if (chart) {
          chart.destroy();
        }
      }
    }
  }
  static updateAllCharts = function() {
    if (Highcharts.charts) {
      for (let chart of Highcharts.charts) {
        if (chart) {
          chart.setSize(null, null, false);
        }
      }
    }
  }

  static showChart = function(sender: HTMLElement) {
    if (CIHPC.paused) {
      return;
    }

    if (!sender) {
      return;
    }
    CIHPC.destroyAllCharts()
    CIHPC.sender = sender;

    var options = $.extend(Utils.grabOptions(), {
      filters: CIHPC.grabFilters(sender)
    });

    var strOptions = btoa(JSON.stringify(options));
    $('#loader').show();
    $('#charts-sm').empty();

    $.ajax({
      url: CIHPC.url_base + '/sparkline-view/' + strOptions,

      error: function(error) {
        console.log({error});
        $('#loader').hide();
        alert('fatal error');
      },

      success: function(result) {
        console.log({result});
        $('#loader').hide();

        if (result.status != 200) {
          $('#charts-sm').html(
            Templates.emptyResults.render(result)
          );
          return;
        }

        $('#charts-sm').empty();
        for (var i in result.data) {
          var chart = result.data[i];
          var extra = chart.extra;

          var id = 'chart-' + (Number(i) + 1);
          $('#charts-sm').append(
            Templates.cardChartSm.render({ id: id, title: chart.title, extra: extra })
          );

          chart.xAxis.labels = {
            formatter: function() {
              var commits: string[] = this.axis.series[this.axis.series.length - 1].userOptions.extra.commits[this.pos][0];
              if (commits.length == 1) {
                var link = CIHPC.commit_url + '/' + commits[0];
                return '<a class="xaxis-link pt-4" href="' + link + '" target="_blank">' + this.value + '</a>';
              } else {
                var links = [];
                var atonce = [];
                for (let commit of commits) {
                  var link = CIHPC.commit_url + '/' + commit;
                  links.push('<a class="xaxis-link" href="' + link + '" target="_blank">' + commit.substr(0, 6) + '</a>');
                  atonce.push("window.open('" + link + "')");
                }
                return this.value + ' <a href="#" onclick="' + atonce.join('; ') + '">open all</a> <br /> (' +
                  (links.join(', ')) + ')';
              }
            }
          };

          // display the chart
          (<any>$('#' + id)).highcharts('SparkMedium', chart);

          $('#' + id).on('point-select', function(target, point: Highcharts.PointObject) {
            var chartID: string = this.id;
            var points = point.series.chart.getSelectedPoints();
            points.push(point);

            var selectedIDs: string[] = [];
            for (let point of points) {
              var extra: ExtraData = (<any>point.series).userOptions.extra;
              selectedIDs = selectedIDs.concat(extra._id[point.index]);
            }
            CIHPC.showFrameViewChart(chartID, selectedIDs);
          });
        }

        $('.spark-holder').on('updateFullscreen', function(event, value) {
          var $col = $(this);
          var chart = $col.find('.chart-holder.main').highcharts();
          var detail = $col.find('.chart-holder.detail').highcharts();
          
          console.log($col.find('.chart-holder.main').width());
          if (value) {
            $col.addClass('expanded fullscreen p-1');
          } else {
            $col.removeClass('expanded fullscreen p-1');
          }
          console.log($col.find('.chart-holder.main').width());
          chart.reflow();
          if (detail) {
              detail.reflow();
          }
          console.log($col.find('.chart-holder.main').width());
          chart.reflow();
          if (detail) {
              detail.reflow();
          }
          // window.dispatchEvent(new Event('resize'));
          // chart.reflow();
        });

        $('.sparkline-fullscreen').click(function(e) {
          var $col = $($(this).data('target'));
          $col.trigger('updateFullscreen', [!$col.hasClass('expanded')])
          // window.dispatchEvent(new Event('resize'));
        });

        if (result.data.length == 1) {
          $('.sparkline-fullscreen').click();
        }
      }
    });
  };



  static showFrameViewChart(chartID: string, selectedIDs: string[]) {
    var options = $.extend(Utils.grabOptions(), {
      filters: CIHPC.grabFilters(CIHPC.sender),
      _ids: selectedIDs
    });
    var strOptions = btoa(JSON.stringify(options));

    $.ajax({
      url: CIHPC.url_base + '/frame-view/' + strOptions,
      error: function(error) {
        console.log({error});
        alert(error);
      },
      success: function(result) {
        console.log({result});
        $('.bd-sidebar').animate({ scrollTop: 0 }, 300);
        var opts = result.data[0];
        opts.tooltip = {
          formatter: function() {
            console.log(this);
            if (this.hasOwnProperty('points')) {
              return Templates.barTooltip.render(this);
            } else {
              return Templates.barTooltip.render({
                points: [this],
                x: this.x,
                y: this.y
              });
            }
          }
        };
        (<any>$('#frame-detail-' + chartID)).highcharts('SparkBar', opts);
        $('#col-' + chartID).addClass('has-detail');
        $('#col-' + chartID).trigger('updateFullscreen', [true]);
      }
    })
  };

}
