/// <reference path ="../typings/jquery/jquery.d.ts"/>
/// <reference path ="../typings/nunjucks/nunjucks.d.ts"/>
/// <reference path ="../typings/highcharts/index.d.ts"/>
/// <reference path ="./tests.ts"/>


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

    static loadTemplates() {
        this.testList = Globals.env.getTemplate("ci-hpc/templates/test-list.njk", true);
        this.lineTooltip = Globals.env.getTemplate("ci-hpc/templates/line-tooltip.njk", true);
        this.barTooltip = Globals.env.getTemplate("ci-hpc/templates/bar-tooltip.njk", true);
        this.chart = Globals.env.getTemplate("ci-hpc/templates/chart.njk", true);
    }
}

interface Window {
    showChart(testName: string, caseName: string, sender: HTMLElement);
    showChartDetail(uuids: string[], chartID: string);
}


$(document).ready(() => {
    Globals.initEnv();
    Templates.loadTemplates();


    var url_base = 'http://hybs.nti.tul.cz:5000/hello-world';


    var cntrlIsPressed: boolean = false;
    $(document).keydown((event: JQuery.Event) => {
        if (event.which == 17)
            cntrlIsPressed = true;
    });
    $(document).keyup((event: JQuery.Event) => {
        cntrlIsPressed = false;
    });



    var lineTooltip = function(event) {
        if (cntrlIsPressed)
            return false;

        var commit = null,
            date = null;
        for (var context of this.points) {
            if (!commit) {
                var index = context.point.index;
                commit = context.series.options.commits[index];
                date = context.point.name;
            }
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
            points: this.points
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
                opt.tooltip.formatter = function(event) {
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
                        points: this.points
                    });
                }
                $('#' + chartID).parent().removeClass('full-width');
                $('#' + chartID + '-detail').parent().removeClass('hidden');
                $('#' + chartID).highcharts().setSize(undefined, undefined);
                Highcharts.chart(chartID + '-detail', opt);
            },
        });
    };



    var showChart = function(testName: string, caseName: string, sender: HTMLElement) {
        if (sender) {
            var clss = 'mdl-color--green-200 mdl-color-text--black';
            $('.testItem').removeClass(clss);
            $(sender).addClass(clss);
        }
        $('#chartsHolder').empty();
        $.ajax({
            // url: 'http://127.0.0.1:5000/case-view/10_darcy/01_source',
            // url: 'http://127.0.0.1:5000/case-view/12_darcy_frac/11_exact_2d_nc_p0/failed',
            // url: 'http://127.0.0.1:5000/case-view/12_darcy_frac/04_bddc',
            url: url_base + '/case-view/' + testName + '/' + caseName + '/uniform=1,failed=0,smooth=0,separate=1,groupby=foo',

            success: function(opts) {
                $('#chartTitle').html(testName + ' / ' + caseName);
                if (!Array.isArray(opts)) {
                    // alert(opts.error);
                    var dialog: any = document.querySelector('dialog');
                    $(dialog).find('.mdl-dialog__title').html(opts.error);
                    $(dialog).find('.mdl-dialog__content').html(opts.description);
                    // if (!dialog.showModal) {
                    //     dialogPolyfill.registerDialog(dialog);
                    // }
                    dialog.querySelector('.close').addEventListener('click', function() {
                        dialog.close();
                    });
                    dialog.showModal();
                    return;
                }
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
                            var link = 'https://github.com/flow123d/flow123d/commit/' + commit;
                            return '<a href="' + link + '" target="_blank">' + this.value + '</a>';
                        },
                        events: {
                            click: function() {
                                // console.log(this);
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
                    // labels: {
                    //     formatter: function () {
                    //         return '<a href="' + categoryLinks[this.value] + '">' +
                    //             this.value + '</a>';
                    //     }
                    // }
                    Highcharts.chart(id, opt);
                }
            },
        });
    };


    // render tests list
    $('#testsRendered').html(
        Templates.testList.render({
            name: 'tests',
            tests: window.tests,
        })
    );


    window.showChart = showChart;
    window.showChartDetail = showChartDetail;

    showChart(window.tests[0].name, window.tests[0].cases[0], $('.testItem')[0]);
}); 