/// <reference path ="../typings/jquery/jquery.d.ts"/>
/// <reference path ="../typings/nunjucks/nunjucks.d.ts"/>
/// <reference path ="../typings/highcharts/index.d.ts"/>


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
    }
}

class Templates {
    static testList: nunjucks.Template;
    static lineTooltip: nunjucks.Template;
    static barTooltip: nunjucks.Template;
    static chart: nunjucks.Template;
    static emptyResults: nunjucks.Template;
    static toggleOptions: nunjucks.Template;
    
    static cardChartSm: nunjucks.Template;
    static benchmarkList: nunjucks.Template;
    static groupToggle: nunjucks.Template;

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
    }
}

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

    var cntrlIsPressed: boolean = false;
    $(document).keydown((event: JQuery.Event) => {
        if (event.which == 17)
            cntrlIsPressed = true;
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
    var commit_url = null;
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
      console.log(opts);
      $('#cihpc-option-holder .btn input[type="checkbox"]').each(function (index, item) {
          console.log(item);
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
      console.log(opts);
      $('#cihpc-option-holder .btn input[type="radio"]:checked').each(function (index, item) {
        console.log(item);
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
      // var $this = $(elem);
      // var f0 = tryToExtractFilters(this);
      // var f1 = tryToExtractFilters($this.parent().prev().get(0));
      // var f2 = tryToExtractFilters($this.parent().prev().parent().prev().get(0));
      // var filters = $.extend({}, f2, f1, f0);
      // return filters;
    };
    
    var tryToExtractFilters = function(element: HTMLElement) {
      if ($(element).hasClass('list-group-item')) {
          return grabFilter(element);
      }
      return {};
    };

    
    $.ajax({
        url: url_base + '/config',
    
        success: function(config) {
            document.title = config.name;
            var commit_url = config['git-url'] +
                        (!!config['git-url'].indexOf('https://bitbucket.org') ?'/commit/' : '/commits/');
            
            if (config.logo) {
                $('#logo').attr('src', config.logo);
            }
            
            var testView:any = config['test-view'];
            
            if (testView.groupby) {
              var groupby = [];
              for (let key in testView.groupby) {
                  groupby.push(
                    {text: key, name: testView.groupby[key], checked: true}
                  );
              }
              $('#cihpc-option-holder').empty();
              $('#cihpc-option-holder').append(
                Templates.groupToggle.render({
                  name: 'grouping',
                  key: 'groups',
                  items: groupby
                })
              );
            }
            
            if (testView['cpu-property']) {
              $('#cihpc-option-holder').append(
                Templates.groupToggle.render({
                  name: 'scaling',
                  desc: 'Choose the display mode',
                  radio: true,
                  items: [
                    {text: 'none', name: 'none', checked: true},
                    {text: 'strong', name: 'strong', checked: false},
                    {text: 'weak', name: 'weak', checked: false},
                  ]
                })
              );
            }
            
            $('#cihpc-option-holder').append(
              Templates.groupToggle.render({
                name: 'options',
                desc: 'Turn off additional series to save space and computing time',
                items: [
                  {text: 'show boxplot', name: 'show-boxplot', checked: false},
                  {text: 'show errorbar', name: 'show-errorbar', checked: true},
                ]
              })
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
            
            for (let testLevel in config.tests) {
              var testItem = config.tests[testLevel];
              testDict['test-'+testItem.name] = $.extend({},
                getFilters(testItem, testItem.level === undefined ? '.test' : testItem.level),
              );
              for (let caseLevel in testItem.tests) {
                var caseItem = testItem.tests[caseLevel];
                testDict['test-'+testItem.name+'-'+caseItem.name] = $.extend(
                  getFilters(caseItem, caseItem.level === undefined ? '.case' : caseItem.level),
                  getFilters(testItem, testItem.level === undefined ? '.test' : testItem.level),
                );
                for (let scaleLevel in caseItem.tests) {
                  var scaleItem = caseItem.tests[scaleLevel];
                  testDict['test-'+testItem.name+'-'+caseItem.name+'-'+scaleItem.name] = $.extend(
                    getFilters(scaleItem, scaleItem.level === undefined ? '.scale' : scaleItem.level),
                    getFilters(caseItem, caseItem.level === undefined ? '.case' : caseItem.level),
                    getFilters(testItem, testItem.level === undefined ? '.test' : testItem.level),
                  );
                }
              }
            }
            
            $('#benchmark-list a.list-group-item').click(function (e) {
                var $this = $(this);
                window.cihpc.paused = true;
                if ($this.data('mode')) {
                    $('#' + $this.data('mode')).click();
                }
                window.cihpc.paused = false;
                showChart(this);
            });
            
            $('#cihpc-option-holder .btn input').change(function (e) {
              showChart(
                window.lastQuery.sender,
              );
            });
            // (<any> window).componentHandler.upgradeDom();
            (<any> $)('[data-toggle="tooltip"]').tooltip();
            
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
              console.log(options);
              
              $.ajax({
                  url: url_base + '/sparkline-view/' + strOptions,

                  error: function (result) {
                      alert(result);
                  },
                  
                  success: function(opts) {
                    $('#charts-sm').empty();
                    for (var i in opts.data) {
                      var size = opts.data[i].size;
                      var opt = opts.data[i].data;
                      var id = 'chart-' + (Number(i) + 1);
                      
                      $('#charts-sm').append(
                          Templates.cardChartSm.render({ id: id, title: opt.title.text})
                      );
                      
                      opt.title.text = null;
                      opt.xAxis.labels = {
                          useHTML: true,
                          formatter: function() {
                              var commit = this.axis.series[0].options.commits[this.pos];
                              var link = commit_url + commit;
                              return '<a href="' + link + '" target="_blank">' + this.value + '</a>';
                          }
                      };
                      
                      (<any> $('#'+id)).highcharts('SparkMedium', opt);
                    }
                    
                    $('.sparkline-fullscreen').click(function(e) {
                      var cls = 'col-xl-6';
                      var $col = $($(this).data('target'));
                      var chart = $col.find('.chart-holder').highcharts();
                      
                      if ($col.hasClass(cls)) {
                          $col.removeClass(cls);
                          chart.setSize(null, 640, false);
                      }else{
                        $col.addClass(cls);
                        chart.setSize(null, 340, false);
                      }
                    });
                    
                    if (opts.data.length == 1) {
                        $('.sparkline-fullscreen').click();
                    }
                  }
              });
            };
                        
            // $.ajax({
            //     url: url_base + '/scale-view/' + 'ff=.name=01_square_regular_grid,ff=.case=transport',
            // 
            //     error: function (result) {
            //         alert(result);
            //     },
            // 
            //     success: function(opts) {
            //       // alert(opts);
            //     }
            //   });
            // showChart(null, null);
        }
    });
    
    // 
    // $.ajax({
    //     url: url_base + '/config',
    // 
    //     success: function(config) {
    //         document.title = config.name;
    //         var commit_url = config['git-url'] +
    //                     (!!config['git-url'].indexOf('https://bitbucket.org') ?'/commit/' : '/commits/');
    // 
    //         if (config['test-view']['cpu-property']) {
    //           $('#options').empty();
    // 
    //             $('#options').append(
    //               Templates.toggleOptions.render({options: [
    //                 {
    //                   name: 'show-scale',
    //                   text: 'Show scaling',
    //                   checked: false,
    //                 },
    //                 {
    //                   name: 'separate',
    //                   text: 'Show separately',
    //                   checked: true,
    //                 }
    //               ]})
    //             );
    // 
    //             (<any> window).componentHandler.upgradeDom('MaterialCheckbox');
    //             $('.cihpc-option').change(function (event) {
    //                 showChart(
    //                   window.lastQuery.testName,
    //                   window.lastQuery.caseName,
    //                   window.lastQuery.sender,
    //                 );
    //             })
    //         }
    // 
    // 
    //         var lineTooltip = function(event) {
    //             if (cntrlIsPressed)
    //                 return false;
    // 
    //             var commit = null,
    //                 date = null;
    //             for (var context of this.points) {
    //                   var index = context.point.index;
    //                   var commit = context.series.options.commits[index];
    //                   var date = context.point.name;
    //                   break;
    //             }
    // 
    //             // return html to be rendered
    //             return Templates.lineTooltip.render({
    //                 commit: commit,
    //                 date: date,
    //                 points: this.points
    //             });
    //         }
    // 
    // 
    //         var barTooltip = function(event) {
    //             if (cntrlIsPressed)
    //                 return false;
    // 
    //             var ys = [];
    //             var result = '';
    //             for (var context of this.points) {
    //                 var index = context.point.index;
    //                 var path = context.series.options.data[index].path;
    //                 var name = context.series.options.data[index].name;
    //                 break;
    //             }
    // 
    // 
    //             // return html to be rendered
    //             return Templates.barTooltip.render({
    //                 path: path.split('/').join('<br />'),
    //                 name: name,
    //                 points: this.points,
    //                 props: config['frame-view'].groupby,
    //             });
    //         }
    // 
    // 
    // 
    //         var showChartDetail = function(uuids: string[], chartID: string) {
    //             $.ajax({
    //                 url: url_base + '/case-view-detail/' + (uuids.join(',')) + '',
    //                 success: function(opt) {
    //                     opt['xAxis']['labels'] = {
    //                         formatter: function() {
    //                             return this.value.substring(0, 24)
    //                         }
    //                     }
    //                     opt.tooltip.formatter = barTooltip;
    // 
    //                     $('#' + chartID).parent().removeClass('full-width');
    //                     $('#' + chartID + '-detail').parent().removeClass('hidden');
    //                     $('#' + chartID).highcharts().setSize(undefined, undefined);
    //                     Highcharts.chart(chartID + '-detail', opt);
    //                 },
    //             });
    //         };
    // 
    // 
    // 
    //         var showChart = function(testName: string, caseName: string, sender: HTMLElement) {
    //             window.lastQuery.testName = testName;
    //             window.lastQuery.caseName = caseName;
    //             window.lastQuery.sender = sender;
    // 
    //             if (sender) {
    //                 var clss = 'mdl-button--raised';
    //                 $('.testItem').removeClass(clss);
    //                 $(sender).addClass(clss);
    //             }
    //             $('#chartsHolder').empty();
    //             $('#loading').removeClass('hidden');
    //             // componentHandler.upgradeAllRegistered();
    // 
    //             var options = 'ff=test-name=' + testName + ',ff=case-name=' + caseName + ',' + grapOptions();
    //             $.ajax({
    //                 url: url_base + '/case-view/' + options,
    // 
    //                 error: function (result) {
    //                     $('#loading').addClass('hidden');
    //                     $('#warning-msg .fs-inner-container').html(
    //                       Templates.emptyResults.render({
    //                           error: 'Error while fetching data from the server',
    //                           description: 'Possible reasons are: <ol>'+
    //                                           '<li>The Flask server is not running.</li>'+
    //                                           '<li>Invalid configuration of the project.</li>'+
    //                                         '</ol>'
    //                         })
    //                     );
    //                     $('#warning-msg').removeClass('hidden');
    //                     $('#page-content').addClass('hidden');
    //                     return;
    //                 },
    //                 success: function(opts) {
    //                   $('#loading').addClass('hidden');
    //                   $('#chartTitle').html(testName + ' / ' + caseName);
    //                   if (!Array.isArray(opts)) {
    //                       $('#warning-msg .fs-inner-container').html(
    //                           Templates.emptyResults.render(opts)
    //                       );
    //                       $('#warning-msg').removeClass('hidden');
    //                       $('#page-content').addClass('hidden');
    //                       return;
    //                     }
    //                     $('#warning-msg').addClass('hidden');
    //                     $('#page-content').removeClass('hidden');
    // 
    //                     for (var i in opts) {
    //                         var size = opts[i].size;
    //                         var opt = opts[i].data;
    //                         var id = 'chart-' + (Number(i) + 1);
    // 
    //                         $('#chartsHolder').append(
    //                             Templates.chart.render({ testName: testName, caseName: caseName, id: id })
    //                         );
    //                         opt.xAxis.labels = {
    //                             useHTML: true,
    //                             formatter: function() {
    //                                 var commit = this.axis.series[0].options.commits[this.pos];
    //                                 var link = commit_url + commit;
    //                                 return '<a href="' + link + '" target="_blank">' + this.value + '</a>';
    //                             },
    //                             events: {
    //                                 click: function() {
    //                                 },
    //                             }
    //                         }
    //                         for (var i in opt.series) {
    //                             if (!opt.series[i].point)
    //                                 continue;
    // 
    //                             opt.series[i].point.events = {
    //                                 select: function(event) {
    //                                     var chartID = this.series.chart.renderTo.getAttribute('id');
    //                                     var chart = $('#' + chartID).highcharts();
    //                                     var selectedPoints: any[] = chart.getSelectedPoints();
    //                                     selectedPoints.push(this);
    //                                     var uuids = [];
    //                                     for (var point of selectedPoints) {
    //                                         var index = point.index;
    //                                         var commit = point.series.userOptions.commits[index];
    //                                         var uuid = point.series.userOptions.uuids[index];
    //                                         uuids.push(uuid);
    //                                     }
    //                                     showChartDetail(uuids, chartID);
    //                                 },
    //                             }
    //                         }
    //                         opt.tooltip.formatter = lineTooltip;
    //                         Highcharts.chart(id, opt);
    //                     }
    //                 },
    //             });
    //         };
    // 
    // 
    //         // render tests list
    //         $('#testsRendered').html(
    //             Templates.testList.render({
    //                 title: config.name,
    //                 tests: config.tests,
    //             })
    //         );
    //         (<any> window).componentHandler.upgradeDom();
    // 
    // 
    // 
    //         window.showChart = showChart;
    //         window.showChartDetail = showChartDetail;
    // 
    //         showChart('*', '*', $('.testItem')[0]);
    //     }
    // });
}); 
