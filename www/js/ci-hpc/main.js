var Globals = (function () {
    function Globals() {
    }
    Globals.initEnv = function () {
        this.env = nunjucks.configure({});
        this.env.addFilter('toFixed', function (num, digits) {
            return parseFloat(num).toFixed(digits || 2);
        });
        this.env.addFilter('cut', function (str, digits) {
            return str.substring(0, digits || 8);
        });
    };
    return Globals;
}());
var Templates = (function () {
    function Templates() {
    }
    Templates.loadTemplates = function () {
        var compileNow = true;
        this.testList = Globals.env.getTemplate("templates/test-list.njk", compileNow);
        this.lineTooltip = Globals.env.getTemplate("templates/line-tooltip.njk", compileNow);
        this.barTooltip = Globals.env.getTemplate("templates/bar-tooltip.njk", compileNow);
        this.chart = Globals.env.getTemplate("templates/chart.njk", compileNow);
        this.emptyResults = Globals.env.getTemplate("templates/empty-results.njk", compileNow);
    };
    return Templates;
}());
$(document).ready(function () {
    Globals.initEnv();
    Templates.loadTemplates();
    var cntrlIsPressed = false;
    $(document).keydown(function (event) {
        if (event.which == 17)
            cntrlIsPressed = true;
    });
    $(document).keyup(function (event) {
        cntrlIsPressed = false;
    });
    var url_base = 'http://hybs.nti.tul.cz:5000/hello-world';
    $.ajax({
        url: url_base + '/config',
        success: function (config) {
            document.title = config.name;
            var lineTooltip = function (event) {
                if (cntrlIsPressed)
                    return false;
                var commit = null, date = null;
                for (var _i = 0, _a = this.points; _i < _a.length; _i++) {
                    var context = _a[_i];
                    if (!commit) {
                        var index = context.point.index;
                        commit = context.series.options.commits[index];
                        date = context.point.name;
                    }
                }
                return Templates.lineTooltip.render({
                    commit: commit,
                    date: date,
                    points: this.points
                });
            };
            var barTooltip = function (event) {
                if (cntrlIsPressed)
                    return false;
                var ys = [];
                var result = '';
                for (var _i = 0, _a = this.points; _i < _a.length; _i++) {
                    var context = _a[_i];
                    var index = context.point.index;
                    var path = context.series.options.data[index].path;
                    var name = context.series.options.data[index].name;
                    break;
                }
                return Templates.barTooltip.render({
                    path: path.split('/').join('<br />'),
                    name: name,
                    points: this.points
                });
            };
            var showChartDetail = function (uuids, chartID) {
                $.ajax({
                    url: url_base + '/case-view-detail/' + (uuids.join(',')) + '',
                    success: function (opt) {
                        opt['xAxis']['labels'] = {
                            formatter: function () {
                                return this.value.substring(0, 24);
                            }
                        };
                        opt.tooltip.formatter = function (event) {
                            if (cntrlIsPressed)
                                return false;
                            var ys = [];
                            var result = '';
                            for (var _i = 0, _a = this.points; _i < _a.length; _i++) {
                                var context = _a[_i];
                                var index = context.point.index;
                                var path = context.series.options.data[index].path;
                                var name = context.series.options.data[index].name;
                                break;
                            }
                            return Templates.barTooltip.render({
                                path: path.split('/').join('<br />'),
                                name: name,
                                points: this.points
                            });
                        };
                        $('#' + chartID).parent().removeClass('full-width');
                        $('#' + chartID + '-detail').parent().removeClass('hidden');
                        $('#' + chartID).highcharts().setSize(undefined, undefined);
                        Highcharts.chart(chartID + '-detail', opt);
                    }
                });
            };
            var showChart = function (testName, caseName, sender) {
                if (sender) {
                    var clss = 'mdl-button--raised';
                    $('.testItem').removeClass(clss);
                    $(sender).addClass(clss);
                }
                $('#chartsHolder').empty();
                $.ajax({
                    url: url_base + '/case-view/' + testName + '/' + caseName + '/uniform=1,failed=0,smooth=0,separate=1,groupby=foo',
                    success: function (opts) {
                        $('#chartTitle').html(testName + ' / ' + caseName);
                        if (!Array.isArray(opts)) {
                            $('#warning-msg .fs-inner-container').html(Templates.emptyResults.render(opts));
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
                            $('#chartsHolder').append(Templates.chart.render({ testName: testName, caseName: caseName, id: id }));
                            opt.xAxis.labels = {
                                useHTML: true,
                                formatter: function () {
                                    var commit = this.axis.series[0].options.commits[this.pos];
                                    var link = config['git-url'] + '/commit/' + commit;
                                    return '<a href="' + link + '" target="_blank">' + this.value + '</a>';
                                },
                                events: {
                                    click: function () {
                                    }
                                }
                            };
                            for (var i in opt.series) {
                                if (!opt.series[i].point)
                                    continue;
                                opt.series[i].point.events = {
                                    select: function (event) {
                                        var chartID = this.series.chart.renderTo.getAttribute('id');
                                        var chart = $('#' + chartID).highcharts();
                                        var selectedPoints = chart.getSelectedPoints();
                                        selectedPoints.push(this);
                                        var uuids = [];
                                        for (var _i = 0, selectedPoints_1 = selectedPoints; _i < selectedPoints_1.length; _i++) {
                                            var point = selectedPoints_1[_i];
                                            var index = point.index;
                                            var commit = point.series.userOptions.commits[index];
                                            var uuid = point.series.userOptions.uuids[index];
                                            uuids.push(uuid);
                                        }
                                        showChartDetail(uuids, chartID);
                                    }
                                };
                            }
                            opt.tooltip.formatter = lineTooltip;
                            Highcharts.chart(id, opt);
                        }
                    }
                });
            };
            $('#testsRendered').html(Templates.testList.render({
                title: config.name,
                tests: config.tests
            }));
            window.showChart = showChart;
            window.showChartDetail = showChartDetail;
            showChart(config.tests[0].name, config.tests[0].tests[0].name, $('.testItem')[0]);
        }
    });
});
