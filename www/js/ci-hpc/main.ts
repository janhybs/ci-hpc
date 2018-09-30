/// <reference path ="../typings/jquery/jquery.d.ts"/>
/// <reference path ="../typings/nunjucks/nunjucks.d.ts"/>
/// <reference path ="../typings/highcharts/index.d.ts"/>
/// <reference path ="filters.ts"/>



interface CIHPC {
    projectName: string;
    flaskApiUrl: string;
    paused?: boolean;
}

interface Window {
    showChart(testName: string, caseName: string, sender: HTMLElement);
    showChartDetail(uuids: string[], chartID: string);
    cihpc: CIHPC;
    lastQuery: any;
    moment: any;
}

interface ExtraData {
  _id: string[];
}

class Globals {
    static env: nunjucks.Environment;

    static initEnv() {
        this.env = nunjucks.configure({});
        this.env.addFilter('toFixed', (num, digits) => {
            return parseFloat(num).toFixed(digits || 2)
        });
        this.env.addFilter('cut', (str, digits) => {
            return str.substring(0, digits || 8)
        });
        this.env.addFilter('max', (values) => {
            return Math.max.apply(Math, values);
        });
        this.env.addFilter('aslist', (value: string) => {
            var s = ''
            value.split('/').forEach((element: string) => {
              if (element) {
                  s += '<li>'+element+'</li>';
              }
            })
            return '<ul>'+s+'</ul>';
        });
    }
}

class Templates {
    static testList: nunjucks.Template;
    static lineTooltip: nunjucks.Template;
    static chart: nunjucks.Template;
    static emptyResults: nunjucks.Template;
    static toggleOptions: nunjucks.Template;

    static cardChartSm: nunjucks.Template;
    static benchmarkList: nunjucks.Template;
    static groupToggle: nunjucks.Template;
    static barTooltip: nunjucks.Template;
    static dateSliders: nunjucks.Template;

    static loadTemplates() {
        var compileNow: boolean = true;
        // this.testList = Globals.env.getTemplate("templates/test-list.njk", compileNow);
        // this.lineTooltip = Globals.env.getTemplate("templates/line-tooltip.njk", compileNow);
        // this.barTooltip = Globals.env.getTemplate("templates/bar-tooltip.njk", compileNow);
        // this.chart = Globals.env.getTemplate("templates/chart.njk", compileNow);
        // this.emptyResults = Globals.env.getTemplate("templates/empty-results.njk", compileNow);
        // this.toggleOptions = Globals.env.getTemplate("templates/toggle-options.njk", compileNow);


        this.cardChartSm = Globals.env.getTemplate("templates/mdb/card-chart-sm.njk", compileNow);
        this.benchmarkList = Globals.env.getTemplate("templates/mdb/benchmark-list.njk", compileNow);
        this.groupToggle = Globals.env.getTemplate("templates/mdb/group-toggle.njk", compileNow);
        this.barTooltip = Globals.env.getTemplate("templates/mdb/bar-tooltip.njk", compileNow);
        this.dateSliders = Globals.env.getTemplate("templates/mdb/date-sliders.njk", compileNow);
        this.emptyResults = Globals.env.getTemplate("templates/mdb/empty-results.njk", compileNow);
    }
}


$(document).ready(() => {
    Globals.initEnv();
    Templates.loadTemplates();
    window.lastQuery = {};


    (function(old) {
      $.fn.attr = function() {
        if(arguments.length === 0) {
          if(this.length === 0) {
            return null;
          }

          var obj = {};
          $.each(this[0].attributes, function() {
            if(this.specified) {
              obj[this.name] = this.value;
            }
          });
          return obj;
        }

        return old.apply(this, arguments);
      };
    })($.fn.attr);

    $('html > head').append('<style type="text/css" id="cihpc-css"></style>');
    var globalCSS = $('#cihpc-css');
    console.log(globalCSS);
    var cntrlIsPressed: boolean = false;
    var tooltipEnabled: boolean = true;
    $(document).keydown((event: JQuery.Event) => {

        if (event.which == 17) {
          cntrlIsPressed = true;

        } else if(event.which == 16) {
          tooltipEnabled = !tooltipEnabled;
          if (tooltipEnabled) {
            globalCSS.html('');
          } else {
            globalCSS.html('.highcharts-tooltip { display: none !important;}');
          }

        }

    });
    $(document).keyup((event: JQuery.Event) => {
        cntrlIsPressed = false;
    });

    // var grapOptions = function () {
    //     var options: string[] = [];
    //     var inputs = $('#options .cihpc-option');
    //     inputs.each(function (index, elem) {
    //         var $elem = $(elem);
    //         var optionValue: Number = $elem.attr('checked') == 'checked' ? 1 : 0;
    //         var optionName = $(elem).attr('cihpc-option-name');
    //         options.push(optionName + '=' + optionValue)
    //     });
    //     return options.join(',');
    // };


    window.cihpc = {
      // projectName: 'hello-world',
      projectName: 'flow123d',
      flaskApiUrl: 'http://hybs.nti.tul.cz:5000',
    }

    var url_base = window.cihpc.flaskApiUrl + '/' + window.cihpc.projectName;
    var testDict = {};

    var grabFilter = function (elem: HTMLElement) {
      var $data = $(elem);
      var filters = {};
      var data = (<any> $data).attr();
      for (let key in data) {
          if (key.indexOf('data-filter') == 0) {
            if (key.substring(12)) {
              filters[key.substring(5)] = data[key];
            } else {
              if (data['data-level']) {
                filters[data['data-level']] = data[key];
              }
            }
          }
      }
      return filters;
    }

    var obj2str = function (o:Object, separator:string=",", glue:string="=") {
        return $.map(Object.getOwnPropertyNames(o), function(k) { return [k, o[k]].join(glue) }).join(separator);
    }

    var obj2arr = function (o:Object, glue:string="=") {
        return $.map(Object.getOwnPropertyNames(o), function(k) { return [k, o[k]].join(glue) });
    }

    var createArgParams = function(obj:Object, prefix:string='ff=') {
      return obj2arr(obj).map(v => prefix + v);
    }

    var grabOptions = function () {
      var opts = {};
      $('#cihpc-option-holder input[type="checkbox"]').each(function (index, item) {
          var isChecked = $(this).is(':checked');
          var optGroup = $(this).data('key');
          if (optGroup) {
            if (!opts[optGroup]) {
                opts[optGroup] = {};
            }
            opts[optGroup][$(this).attr('name')] = isChecked;
          } else {
            opts[$(this).attr('name')] = isChecked;
          }
      });
      $('#cihpc-option-holder input[type="radio"]:checked').each(function (index, item) {
        var optGroup = $(this).data('key');
        if (optGroup) {
          if (!opts[optGroup]) {
              opts[optGroup] = {};
          }
          opts[optGroup][$(this).attr('name')] = $(this).val();
        } else {
          opts[$(this).attr('name')] = $(this).val();
        }
      });
      $('#cihpc-option-holder .cihpc-slider input').each(function (index, item) {
        var optGroup = $(this).data('key');
        if (optGroup) {
          if (!opts[optGroup]) {
              opts[optGroup] = {};
          }
          opts[optGroup][$(this).attr('name')] = $(this).val();
        } else {
          opts[$(this).attr('name')] = $(this).val();
        }
      });
      console.log(opts);
      return opts;
    }

    var grabFilters = function(elem:HTMLElement) {
      return testDict[elem.id];
    };

    var tryToExtractFilters = function(element: HTMLElement) {
      if ($(element).hasClass('list-group-item')) {
          return grabFilter(element);
      }
      return {};
    };

    var createDateSliders = function(){
      $('.cihpc-slider').each(function(){
        var $this = $(this);
        var $text = $this.find('.text');
        var $value = $this.find('.value');
        var min, max;

        if ($this.data('type') == 'number') {
          var defval = $value.data('default');
          if (defval) {
            $value.val(defval);
          }

          $value.on('input', function() {
            $text.html((<HTMLInputElement> this).value);
          });
          $value.trigger('input');

        } else if ($this.data('type') == 'date') {
          if (!$value.attr('min')) {
            min = window.moment().subtract(5, 'months').format('X')
            $value.attr('min', min);
          }
          if (!$value.attr('max')) {
            max = (new Date().getTime()/1000).toFixed();
            $value.attr('max', max);
          }
          var defval = $value.data('default');
          if (defval) {
            if (defval === 'min') {
              $value.val(min);
            } else if (defval === 'max') {
              $value.val(max);
            } else {
              $value.val(defval);
            }
          }

          $value.on('input', function() {
            var m = window.moment((<HTMLInputElement> this).value, 'X');
            var abs = m.format('DD.MM YYYY');
            var rel = m.fromNow();
            $text.html(abs +' <small>'+rel+'</small>');
          });
          $value.trigger('input');
        }
      });
    };


    $.ajax({
        url: url_base + '/config',

        success: function(config) {
            document.title = config.name;
            var commit_url = config['git-url'] +
                        (!!config['git-url'].indexOf('https://bitbucket.org') ? '/commit/' : '/commits/');
            var compare_url = !!config['git-url'].indexOf('https://bitbucket.org') ? config['git-url'] + '/compare/': null;

            if (config.logo) {
                $('#logo').attr('src', config.logo);
            }

            var testView:any = config['test-view'];
            var fields:any = config['fields'];
            $('#cihpc-option-holder').empty();

            $('#cihpc-option-holder').append(
              Templates.dateSliders.render({
                text: 'Commit range',
                key: 'range',
                items: [
                  {name: 'from', value: 'min', title: 'From'},
                  {name: 'to', value: 'max', title: 'To'},
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

              groupby = groupby.concat(ConfigureViewFilters.filterGroupBy(fields));

              $('#cihpc-option-holder').append(
                Templates.groupToggle.render({
                  text: 'Group by',
                  key: 'groupby',
                  items: groupby
                })
              );
            }

            $('#cihpc-option-holder').append('<hr />');

            $('#cihpc-option-holder').append(
              Templates.groupToggle.render(
                ConfigureViewFilters.filterSeries
              )
            );


            // render tests list
            $('#benchmark-list').empty();
            $('#benchmark-list').html(
                Templates.benchmarkList.render({
                    title: config.name,
                    tests: config.tests,
                })
            );

            var getFilters = function (opts: any, level: string) {
              var result: object = $.extend({}, opts.filters);
              if (level === null) {
                  return result;
              }
              result[level] = opts.name;
              return result;
            };


            var updateOptionGroups = function () {
              var mode = $('#form-mode input:checked').val();
              var cls1 = 'disabled btn-light',
                  cls2 = 'btn-primary';

              if (mode == 'time-series') {
                  $('#groupby-commit').prop('disabled', true);
                  $('#groupby-cpus').prop('disabled', false);
                  $('#groupby-size').prop('disabled', false);

              } else if (mode == 'scale-view') {
                $('#groupby-commit').prop('disabled', false);
                $('#groupby-cpus').prop('disabled', true);
                $('#groupby-size').prop('disabled', true);

              }
            };

            var testLevelName = config.fields['problem.test'],
                caseLevelName = config.fields['problem.case'],
                subCaseLevelName = config.fields['problem.subcase'];

            for (let testLevel in config.tests) {
              var testItem = config.tests[testLevel];
              testDict['test-'+testItem.name] = $.extend({},
                getFilters(testItem, testItem.level === undefined ? testLevelName : testItem.level),
              );
              for (let caseLevel in testItem.tests) {
                var caseItem = testItem.tests[caseLevel];
                testDict['test-'+testItem.name+'-'+caseItem.name] = $.extend(
                  getFilters(caseItem, caseItem.level === undefined ? caseLevelName : caseItem.level),
                  getFilters(testItem, testItem.level === undefined ? testLevelName : testItem.level),
                );
                for (let subcaseLevel in caseItem.tests) {
                  var subcaseItem = caseItem.tests[subcaseLevel];
                  testDict['test-'+testItem.name+'-'+caseItem.name+'-'+subcaseItem.name] = $.extend(
                    getFilters(subcaseItem, subcaseItem.level === undefined ? subCaseLevelName : subcaseItem.level),
                    getFilters(caseItem, caseItem.level === undefined ? caseLevelName : caseItem.level),
                    getFilters(testItem, testItem.level === undefined ? testLevelName : testItem.level),
                  );
                }
              }
            }

            $('#modal-options').on('hide.bs.modal', function(){
              updateOptionGroups();
              showChart(
                window.lastQuery.sender,
              );
            });

            $('#benchmark-list a.list-group-item').click(function (e) {
                var $this = $(this);
                $('#benchmark-list a.list-group-item').removeClass('active');
                $this.addClass('active');

                window.cihpc.paused = true;
                if ($this.data('mode')) {
                    $('#mode-' + $this.data('mode')).click();
                }
                window.cihpc.paused = false;
                showChart(this);
            });

            $('#cihpc-option-holder input').change(function (e) {
                updateOptionGroups();
            });

            updateOptionGroups();
            createDateSliders();

            // (<any> $)('[data-toggle="tooltip"]').tooltip();

            var showChart = function (sender: HTMLElement) {
              if (window.cihpc.paused) {
                  return;
              }

              if (!sender) {
                  return;
              }

              var options = grabOptions();
              var filters = grabFilters(sender);

              window.lastQuery.sender = sender;

              options['filters'] = filters;
              var strOptions = btoa(JSON.stringify(options));
              $('#loader').show();
              $('#charts-sm').empty();

              $.ajax({
                  url: url_base + '/sparkline-view/' + strOptions,
                  // url: url_base + '/scale-view/' + strOptions,

                  error: function (result) {
                    $('#loader').hide();
                    alert('fatal error');
                    console.log(result);
                  },

                  success: function(result) {
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
                       console.log(chart);

                       var id = 'chart-' + (Number(i) + 1);
                       $('#charts-sm').append(
                           Templates.cardChartSm.render({id: id, title: chart.title, extra: extra})
                       );

                       chart.xAxis.labels = {
                          formatter: function() {
                              var commits: string[] = this.axis.series[this.axis.series.length-1].userOptions.extra.commits[this.pos][0];
                              if (commits.length == 1) {
                                var link = commit_url + commits[0];
                                return '<a class="xaxis-link pt-4" href="' + link + '" target="_blank">' + this.value + '</a>';
                              } else {
                                var links = [];
                                var atonce = [];
                                for (let commit of commits) {
                                    var link = commit_url + commit;
                                    links.push('<a class="xaxis-link" href="' + link + '" target="_blank">' + commit.substr(0, 6) + '</a>');
                                    atonce.push("window.open('" + link + "')");
                                }
                                return this.value + ' <a href="#" onclick="' + atonce.join('; ') + '">open all</a> <br /> (' +
                                (links.join(', ')) + ')';
                              }
                           }
                       };

                       // display the chart
                       (<any> $('#'+id)).highcharts('SparkMedium', chart);

                       $('#'+id).on('point-select', function (target, point: Highcharts.PointObject) {
                          var id:string = this.id;
                          var points = point.series.chart.getSelectedPoints();
                          points.push(point);

                          var _ids = [];
                          for (let point of points) {
                            var extra: ExtraData = (<any> point.series).userOptions.extra;
                            _ids = _ids.concat(extra._id[point.index]);
                          }


                          var options = grabOptions();
                          var filters = grabFilters(window.lastQuery.sender);
                          options['filters'] = filters;
                          options['_ids'] = _ids;
                          var strOptions = btoa(JSON.stringify(options));

                          $.ajax({
                            url: url_base + '/frame-view/' + strOptions,
                            error: function (error) {
                                alert(error);
                            },
                            success: function (result) {
                              $('.bd-sidebar').animate({scrollTop: 0}, 300);
                              var opts = result.data[0];
                              opts.tooltip = {
                                formatter: function(){
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
                              (<any> $('#frame-detail-'+id)).highcharts('SparkBar', opts);
                              $('#col-'+id).trigger('updateFullscreen', [true]);
                            }
                          })
                       });
                    }

                    $('.spark-holder').on('updateFullscreen', function(event, value){
                      var $col = $(this);
                      var cls = 'col-xl-6';
                      var chart = $col.find('.chart-holder.main').highcharts();
                      var detail = $col.find('.chart-holder.detail').highcharts();

                      if (value) {
                        $col.removeClass(cls).addClass('expanded');
                        chart.setSize(null, 640, false);
                        if (detail) {
                            detail.setSize(null, 500, false);
                        }
                      } else {
                        $col.addClass(cls).removeClass('expanded');
                        chart.setSize(null, 340, false);
                        if (detail) {
                            detail.setSize(null, 250, false);
                        }
                      }
                    });

                    $('.sparkline-fullscreen').click(function(e) {
                      var $col = $($(this).data('target'));
                      $col.trigger('updateFullscreen', [!$col.hasClass('expanded')])
                    });

                    if (result.data.length == 1) {
                        $('.sparkline-fullscreen').click();
                    }
                  }
              });
            };
        }
    });
});
