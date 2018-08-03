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
    static toggleOption: nunjucks.Template;

    static loadTemplates() {
        var compileNow: boolean = true;
        this.testList = Globals.env.getTemplate("templates/test-list.njk", compileNow);
        this.lineTooltip = Globals.env.getTemplate("templates/line-tooltip.njk", compileNow);
        this.barTooltip = Globals.env.getTemplate("templates/bar-tooltip.njk", compileNow);
        this.chart = Globals.env.getTemplate("templates/chart.njk", compileNow);
        this.emptyResults = Globals.env.getTemplate("templates/empty-results.njk", compileNow);
        this.toggleOption = Globals.env.getTemplate("templates/toggle-option.njk", compileNow);
    }
}

interface CIHPC {
    projectName: string;
    flaskApiUrl: string;
}

interface Window {
    showChart(testName: string, caseName: string, sender: HTMLElement);
    showChartDetail(uuids: string[], chartID: string);
    cihpc: CIHPC;
}


$(document).ready(() => {
    Globals.initEnv();
    Templates.loadTemplates();

    var cntrlIsPressed: boolean = false;
    $(document).keydown((event: JQuery.Event) => {
        if (event.which == 17)
            cntrlIsPressed = true;
    });
    $(document).keyup((event: JQuery.Event) => {
        cntrlIsPressed = false;
    });
    
    var grapOptions = function () {
        var options: string[] = [];
        var inputs = $('#options .cihpc-option');
        inputs.each(function (index, elem) {
            var $elem = $(elem);
            var optionValue: Number = $elem.attr('checked') == 'checked' ? 1 : 0;
            var optionName = $(elem).attr('cihpc-option-name');
            options.push(optionName + '=' + optionValue)
        });
        return options.join(',');
    };


    var url_base = window.cihpc.flaskApiUrl + '/' + window.cihpc.projectName;
    $.ajax({
        url: url_base + '/config',

        success: function(config) {
            document.title = config.name;

            if (config['test-view'].colorby) {
                $('#options').html(
                  Templates.toggleOption.render({
                    name: 'separate',
                    text: 'Show separately',
                  })
                );
                (<any> window).componentHandler.upgradeDom('MaterialCheckbox');
                $('#checkbox-separate').change(function (event) {
                    // TODO update chart
                })
            }


            var lineTooltip = function(event) {
                if (cntrlIsPressed)
                    return false;

                var commit = null,
                    date = null;
                for (var context of this.points) {
                      var index = context.point.index;
                      var commit = context.series.options.commits[index];
                      var date = context.point.name;
                      break;
                }

                // return html to be rendered
                return Templates.lineTooltip.render({
                    commit: commit,
                    date: date,
                    points: this.points
                });
            }


            var barTooltip = function(event) {
                if (cntrlIsPressed)
                    return false;

                var ys = [];
                var result = '';
                for (var context of this.points) {
                    var index = context.point.index;
                    var path = context.series.options.data[index].path;
                    var name = context.series.options.data[index].name;
                    break;
                }
                
                
                // return html to be rendered
                return Templates.barTooltip.render({
                    path: path.split('/').join('<br />'),
                    name: name,
                    points: this.points,
                    props: config['frame-view'].groupby,
                });
            }



            var showChartDetail = function(uuids: string[], chartID: string) {
                $.ajax({
                    url: url_base + '/case-view-detail/' + (uuids.join(',')) + '',
                    success: function(opt) {
                        opt['xAxis']['labels'] = {
                            formatter: function() {
                                return this.value.substring(0, 24)
                            }
                        }
                        opt.tooltip.formatter = barTooltip;
                        
                        $('#' + chartID).parent().removeClass('full-width');
                        $('#' + chartID + '-detail').parent().removeClass('hidden');
                        $('#' + chartID).highcharts().setSize(undefined, undefined);
                        Highcharts.chart(chartID + '-detail', opt);
                    },
                });
            };



            var showChart = function(testName: string, caseName: string, sender: HTMLElement) {
                if (sender) {
                    var clss = 'mdl-button--raised';
                    $('.testItem').removeClass(clss);
                    $(sender).addClass(clss);
                }
                $('#chartsHolder').empty();
                $('#loading').removeClass('hidden');
                // componentHandler.upgradeAllRegistered();
                
                
                var options = 'ff=test-name=' + testName + ',ff=case-name=' + caseName + ',' + grapOptions();
                $.ajax({
                    url: url_base + '/case-view/' + options,

                    success: function(opts) {
                      $('#loading').addClass('hidden');
                        $('#chartTitle').html(testName + ' / ' + caseName);
                        if (!Array.isArray(opts)) {
                            $('#warning-msg .fs-inner-container').html(
                                Templates.emptyResults.render(opts)
                            );
                            $('#warning-msg').removeClass('hidden');
                            $('#page-content').addClass('hidden');
                            return;
                        }
                        $('#warning-msg').addClass('hidden');
                        $('#page-content').removeClass('hidden');

                        for (var i in opts) {
                            var size = opts[i].size;
                            var opt = opts[i].data;
                            var id = 'chart-' + (Number(i) + 1);

                            $('#chartsHolder').append(
                                Templates.chart.render({ testName: testName, caseName: caseName, id: id })
                            );
                            opt.xAxis.labels = {
                                useHTML: true,
                                formatter: function() {
                                    var commit = this.axis.series[0].options.commits[this.pos];
                                    var link = config['git-url'] + '/commit/' + commit;
                                    return '<a href="' + link + '" target="_blank">' + this.value + '</a>';
                                },
                                events: {
                                    click: function() {
                                    },
                                }
                            }
                            for (var i in opt.series) {
                                if (!opt.series[i].point)
                                    continue;

                                opt.series[i].point.events = {
                                    select: function(event) {
                                        var chartID = this.series.chart.renderTo.getAttribute('id');
                                        var chart = $('#' + chartID).highcharts();
                                        var selectedPoints: any[] = chart.getSelectedPoints();
                                        selectedPoints.push(this);
                                        var uuids = [];
                                        for (var point of selectedPoints) {
                                            var index = point.index;
                                            var commit = point.series.userOptions.commits[index];
                                            var uuid = point.series.userOptions.uuids[index];
                                            uuids.push(uuid);
                                        }
                                        showChartDetail(uuids, chartID);
                                    },
                                }
                            }
                            opt.tooltip.formatter = lineTooltip;
                            Highcharts.chart(id, opt);
                        }
                    },
                });
            };


            // render tests list
            $('#testsRendered').html(
                Templates.testList.render({
                    title: config.name,
                    tests: config.tests,
                })
            );


            window.showChart = showChart;
            window.showChartDetail = showChartDetail;

            // showChart('*', '*', $('.testItem')[0]);
        }
    });
}); 
